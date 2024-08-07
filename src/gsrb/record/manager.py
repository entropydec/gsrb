import logging
import re
import time
import zipfile
from dataclasses import replace
from pathlib import Path
from typing import Callable
from xml.etree.ElementTree import fromstring

from uiautomator2 import Device

from gsrb.common.criterion import Criterion
from gsrb.common.event import Event
from gsrb.common.locator import Locator
from gsrb.common.step import Step, Ui
from gsrb.match.layout import Layout
from gsrb.match.preprocess import preprocess as xml_preprocess
from gsrb.record.assertion import (
    get_target_indices,
    retry_ask,
    select_candidate,
    to_assertion,
)
from gsrb.utils.app import init_app
from gsrb.utils.element import draw_element
from gsrb.utils.logging import log_in_memory

logger = logging.getLogger(__name__)

pattern = r"^(?P<intent>\s*?)(?P<device>[a-zA-Z_]\w*?)\s*?=\s*?(?:uiautomator2|u2)\.connect\(\)\s*?$"  # noqa
assertion_pattern = (
    r"^(?P<intent>\s*?)assert\s+?(?P<not>not\s+?)?(?P<statement>.*?)\.exists$"
)
extend_assertion_pattern = r'^(?P<intent>\s*?)assert\s+?(?P<statement>.*?)\.info\["(?P<attr>.*?)"\]\s*(?:(?P<eq>==)|(?P<ne>!=))\s*"(?P<oracle>.*?)"'  # noqa

record_interval = 0.5

PostProcessor = Callable[[list[Step]], None]


class RecordManager:
    def __init__(self, *args: PostProcessor) -> None:
        """初始化录制处理器"""
        self.post_processors: list[PostProcessor] = list(args)
        self.device: Device | None = None
        self.steps: list[Step] = []
        self.current_ui: Ui = Ui()

    def dump(self) -> tuple[str, bytes]:
        """获取当前设备的界面信息

        Args:
            device (Device): 设备

        Returns:
            tuple[str, bytes]: 界面布局信息与截屏信息
        """
        time.sleep(record_interval)
        if self.device is None:
            return "", bytes()
        layout = self.device.dump_hierarchy()
        screenshot = self.device.screenshot(format="raw")
        assert isinstance(screenshot, bytes)
        return layout, screenshot

    def before(self) -> None:
        if self.device is not None:
            self.current_ui = Ui(*self.dump())

    def after(self, event: Event) -> None:
        if self.device is not None:
            logger.debug(f"record {event=}")
            new_ui = Ui(*self.dump())
            step = Step(event, self.current_ui, new_ui)
            self.steps.append(step)

    def post_process(self) -> None:
        for processor in self.post_processors:
            processor(self.steps)


def save_to_zip(target: Path, pretest: str | None, draw: bool) -> PostProcessor:
    def func(steps: list[Step]) -> None:
        with zipfile.ZipFile(target, "w") as zf:
            for i, step in enumerate(steps):
                if not draw:
                    zf.writestr(f"ui/{i * 2}.png", step.ui_before.p)
                else:
                    zf.writestr(
                        f"ui/{i * 2}.png",
                        draw_element(
                            step.ui_before.p, step.ui_before.x, step.event.locator
                        ),
                    )
                zf.writestr(f"ui/{i * 2}.xml", step.ui_before.x)
                zf.writestr(f"ui/{i * 2 + 1}.png", step.ui_after.p)
                zf.writestr(f"ui/{i * 2 + 1}.xml", step.ui_after.x)

            content = "\n".join([x.event.to_json() for x in steps])
            zf.writestr("record.txt", content)
            if pretest is not None:
                zf.writestr("pretest.py", pretest)

            zf.writestr("gsrb.debug.log", log_in_memory.getvalue())

    return func


def generate_assertion(target: Path) -> PostProcessor:
    def func(steps: list[Step]) -> None:
        target_indices = get_target_indices(steps)
        new_events: list[Event] = []
        for i, step in enumerate(steps):
            new_events.append(step.event)
            if i in target_indices:
                layout = Layout(step.ui_after.x, step.ui_after.p)
                candidates = retry_ask(layout)
                event = to_assertion(select_candidate(candidates))
                if event is None:
                    continue
                new_events.append(event)

        with zipfile.ZipFile(target, "a") as zf:
            zf.writestr(
                "record_with_assertion.txt",
                "\n".join([e.to_json() for e in new_events]),
            )

    return func


def rewrite_script(target: Path) -> PostProcessor:
    def func(steps: list[Step]) -> None:
        lines: list[str] = []
        lines.extend(
            [
                "import uiautomator2 as u2",
                "",
                'if __name__ == "__main__":',
                "    d = u2.connect()",
                "",
            ]
        )
        for step in steps:
            if step.event.locator is None:
                lines.append(f"    {step.event.generate_u2('d')}")
                continue
            root = fromstring(step.ui_before.x)
            locator = step.event.locator
            xml_preprocess(root)
            node = locator.find_in_layout(root)
            if node is None:
                logger.error(f"cannot find node for locator: {locator}")
                exit(-1)
            new_locator = Locator(
                {Criterion.CLASS: node.attrib["class"]}, int(node.attrib["class-index"])
            )
            new_event = replace(step.event, locator=new_locator)
            lines.append(f"    {new_event.generate_u2('d')}")
        target.write_text("\n".join(lines), encoding="utf-8")

    return func


def preprocess(script: str, package: str, addr: str, *, record: bool = True) -> str:
    """对脚本进行预处理

    Args:
        script (str): 脚本内容
        package (str): 包名
        addr (str): 设备序列号
        record (bool): 是否录制. Defaults to True.

    Returns:
        str: 预处理后的脚本
    """
    lines = [x for x in script.split("\n") if x.strip() != ""]
    if record:
        lines.insert(0, "from gsrb.record.my_device import MyDevice")
    for i in range(len(lines)):
        if match := re.match(pattern, lines[i]):
            # 主要工作是添加运行脚本的设备序列号
            intent: str = "" if not match.group("intent") else match.group("intent")
            device_name: str = match.group("device")
            lines[i] = lines[i].replace(".connect()", f'.connect("{addr}")')
            if record:
                # 增加录制逻辑
                lines[i] += f"\n{intent}{device_name}.__class__ = MyDevice"
                lines[i] += f"\n{intent}{device_name}.manager.device = {device_name}"
                lines[i] += f'\n{intent}init_app({device_name}, "{package}", pretest)'
        # 处理断言
        if record:
            if (match := re.match(assertion_pattern, lines[i])) is not None:
                intent = "" if not match.group("intent") else match.group("intent")
                not_exists = match.group("not") is not None
                statement: str = match.group("statement")
                lines[
                    i
                ] = f"{intent}{statement}.assert_{'not_' if not_exists else ''}exists()"
            if (match := re.match(extend_assertion_pattern, lines[i])) is not None:
                intent = "" if not match.group("intent") else match.group("intent")
                eq = match.group("eq") is not None
                statement = match.group("statement")
                attr: str = match.group("attr")
                oracle: str = match.group("oracle")
                lines[
                    i
                ] = f"{intent}{statement}.assert_{'not_' if not eq else ''}equals(\"{attr}\", \"{oracle}\")"  # noqa

    return "\n".join(lines)


def record(
    package: str,
    script: str,
    output: Path,
    device: str,
    pretest: str | None = None,
    rewrite: Path | None = None,
    # generate: bool = False,
    draw: bool = False,
) -> None:
    script = preprocess(script, package, device)

    if pretest is not None:
        new_pretest = preprocess(pretest, package, device, record=False)
    else:
        new_pretest = None
    manager = RecordManager(save_to_zip(output, pretest, draw))
    if rewrite is not None:
        manager.post_processors.append(rewrite_script(rewrite))
    # if generate:
    #     manager.post_processors.append(generate_assertion(output))

    from gsrb.record.my_device import MyDevice
    from gsrb.record.my_uiobject import MyUiObject

    MyDevice.manager = manager
    MyUiObject.manager = manager

    g = globals()
    g["__name__"] = "__main__"
    g["init_app"] = init_app
    g["pretest"] = new_pretest
    exec(script, g)
    manager.post_process()
    g["d"].app_stop(package)
