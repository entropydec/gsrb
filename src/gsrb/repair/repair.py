import logging
import pprint
import time
import zipfile
from copy import deepcopy
from dataclasses import replace
from pathlib import Path
from typing import Literal, NoReturn

from uiautomator2 import Device, connect

from gsrb.common.action import Action
from gsrb.common.event import TEMPLATE_U2, Event
from gsrb.common.locator import Locator
from gsrb.common.step import Step, TestCase, Ui
from gsrb.match.layout import Layout
from gsrb.match.match import match_layout
from gsrb.match.predictors import (
    default_filter,
    default_key,
    optimize_filter_generator,
    optimize_key_generator,
    tree_equal,
)
from gsrb.utils.app import get_version, init_app
from gsrb.utils.logging import log_in_memory

logger = logging.getLogger(__name__)


class Repair:
    def __init__(
        self,
        testcase: TestCase,
        package: str,
        output: Path,
        device: str,
        *,
        pretest: str | None = None,
        template: Literal["u2"] = "u2",
        verbose_output: Path | None = None,
        optimize_explore: bool = True,
        remove_assertion: bool = False,
    ) -> None:
        # init device
        self.device: Device = connect(device)
        self.device.implicitly_wait(3.0)
        logger.info(f"init device: {device}")
        logger.info(
            f"device info:\n{pprint.pformat(self.device.info, indent=2, width=240, sort_dicts=False)}"  # noqa
        )

        # init package
        self.package: str = package
        if (version := get_version(device, self.package)) is None:
            logger.error(
                f"unable to get version of {self.package} "
                f"on device {device}, "
                "please check install state"
            )
            return
        logger.info(f"target apk: {self.package}")
        logger.info(f"target version: {version}")

        # init pretest
        if pretest is not None:
            logger.info("init pretest")
            pretest = pretest.replace(
                "u2.connect()", f'u2.connect("{device}")'
            ).replace(
                "uiautomator2.connect()",
                f'uiautomator2.connect("{device}")',
            )
            logger.info(f"pretest: \n{pretest}")
            self.pretest: str | None = pretest
        else:
            self.pretest = None

        if remove_assertion:
            testcase = [step for step in testcase if not step.event.is_assertion()]

        # init testcase
        self.testcase: TestCase = [
            step for step in testcase if not step.event.is_generated_assertion()
        ]
        self.generated_assertion: dict[Step, Step] = dict()
        for i in range(len(testcase) - 1):
            if testcase[i + 1].event.is_generated_assertion():
                self.generated_assertion[testcase[i]] = testcase[i + 1]

        # init result
        self.result: TestCase = []
        self.result_assertion: dict[Step, Step] = dict()

        # init output
        self.output = output
        if not (parent := self.output.parent).exists():
            parent.mkdir(parents=True)
        self.verbose_output = verbose_output

        self.optimize_explore = optimize_explore
        logger.info(f"optimize explore: {self.optimize_explore}")

        self.template = template
        logger.info(f"current output template: {self.template}")

        # 中间变量
        self.__current: int = 0
        self.start_time = time.time()
        self.end_time = time.time()
        self.explore_time = 0

    @property
    def current(self) -> int:
        return self.__current

    @current.setter
    def current(self, value: int) -> None:
        logger.debug(f"update current from {self.__current} to {value}")
        self.__current = value

    def repair(self) -> None:
        self.start_time = time.time()
        # 打印修复信息
        logger.info("repair start")
        init_app(self.device, self.package, self.pretest)

        for i, step in enumerate(self.testcase):
            logger.info(f"step {i:>02}: {step}")
            if step in self.generated_assertion:
                print(f"generate step: {self.generated_assertion[step]}")

        while self.current < len(self.testcase):
            self.check_generated_assertion()

            logger.info(f"repair step {self.testcase[self.current]}")

            # 逐步尝试
            if self.__match_current() or self.__match_next():
                continue

            # 尝试当前界面开始探索
            logger.info("try to explore...")
            if any(self.__explore(c) for c in self.__candidates()):
                logger.info("explore succeed")
                continue

            # 尝试前一步骤
            logger.info("try to explore with a step back")
            if len(self.result) == 0:
                logger.info("cannot back")
                self.__quit(False)
            if len(self.result) > 0 and self.result[-1].event.action == Action.SWIPE:
                # 特殊处理回退时是 swipe 的情况
                logger.info("pop swipe")
                self.result.pop()
            self.result.pop()
            logger.info("current result:")
            for i, step in enumerate(self.result):
                logger.info(f"step {i:0>2}: {step}")
            self.__recover()

            # 先尝试匹配
            if self.__match_current() or self.__match_next():
                continue

            # 再进行探索
            if any(self.__explore(c) for c in self.__candidates()):
                logger.info("explore succeed")
                continue

            logger.info("all explorations are failed")
            self.__quit(False)

        self.check_generated_assertion()
        self.__quit(True)

    def check_generated_assertion(self) -> None:
        if self.current < 1:
            return

        if (
            prev_step := self.testcase[self.current - 1]
        ) in self.generated_assertion and len(self.result) > 0:
            # 上一步之后有生成的断言
            assertion_step = self.generated_assertion[prev_step]
            cur_result = self.result[-1]
            logger.info(f"try to perform generated assertion {assertion_step}")

            if assertion_step.event.perform(self.device):
                logger.info("generated assertion succeeded")
                new_step = assertion_step
            else:
                logger.info("generated assertion failed")
                new_step = replace(
                    assertion_step,
                    event=assertion_step.event.with_parameter({"failed": True}),
                )

            self.result_assertion[cur_result] = new_step

    def __recover(self) -> None:
        """将应用状态恢复到当前保存的已执行步骤"""
        logger.info("recovering...")
        init_app(self.device, self.package, self.pretest)
        for step in self.result:
            logger.debug(f"perform step {step}")
            step.event.perform(self.device)

    def __capture(self) -> Layout:
        """捕获当前布局

        Returns:
            Layout: 布局信息
        """
        return Layout.from_device(self.device)

    def __quit(self, succeed: bool) -> NoReturn:
        """退出修复并输出结果

        Args:
            succeed (bool): 修复是否成功
        """
        logger.info(f"repair {'failed' if not succeed else 'succeeded'}, quitting...")
        self.end_time = time.time()
        self.__save(succeed)
        self.device.app_stop(self.package)
        exit(0 if succeed else -1)

    def __save(self, succeed: bool) -> None:
        if succeed:
            Path(str(self.output.resolve())).write_text(
                self.__generate(), encoding="utf-8"
            )
        if self.verbose_output is not None:
            with zipfile.ZipFile(self.verbose_output, "w") as zf:
                for i, step in enumerate(self.result):
                    if step.has_ui():
                        zf.writestr(f"ui/{i * 2}.png", step.ui_before.p)
                        zf.writestr(f"ui/{i * 2}.xml", step.ui_before.x)
                        zf.writestr(f"ui/{i * 2 + 1}.png", step.ui_after.p)
                        zf.writestr(f"ui/{i * 2 + 1}.xml", step.ui_after.x)

                content = "\n".join([step.event.to_json() for step in self.result])
                zf.writestr("record.txt", content)
                if self.pretest is not None:
                    zf.writestr("pretest.py", self.pretest)

                zf.writestr("gsrb.debug.log", log_in_memory.getvalue())

    def __generate(self) -> str:
        """根据当前修复配置的生成模板，生成对应目标代码"""
        if self.template == "u2":
            template = TEMPLATE_U2
            lines = []
            for step in self.result:
                lines.append(step.event.generate_u2("d"))
                if step in self.result_assertion:
                    lines.append(self.result_assertion[step].event.generate_u2("d"))
            content = "\n".join(f"    {line}" for line in lines)
            device_name = "d"
            device_serial = ""
            package = self.package
            script = template.substitute(
                content=content,
                device_name=device_name,
                device_serial=device_serial,
                package=package,
            )
            return f"# repair time: {self.end_time - self.start_time:.2f}s\n# explore time: {self.explore_time}\n{script}"  # noqa
        return ""

    def __candidates(self) -> list[Event]:
        """在当前界面获取探索的候选组件，按照一定规则排序后返回

        优先返回 id 唯一的组件，然后是列表项组件

        Returns:
            list[Event]: 候选组件序列
        """
        current_layout = self.__capture()

        # 筛选
        candidates_filter = (
            optimize_filter_generator(current_layout.non_overlap)
            if self.optimize_explore
            else default_filter
        )
        children = candidates_filter(current_layout.children)

        # 排序
        candidate_key = (
            optimize_key_generator(children) if self.optimize_explore else default_key
        )
        children.sort(key=candidate_key)

        candidates: list[Event] = []
        for child in children:
            locator = Locator.from_node(child)
            event = Event(Action.CLICK, locator)
            candidates.append(event)

        for candidate in candidates:
            logger.info(f"explore candidate: {candidate}")
        return candidates

    def __explore(self, event: Event) -> bool:
        """探索以修复当前步骤

        Args:
            event (Event): 前往下一个页面的动作

        Returns:
            bool: 是否修复成功
        """
        self.explore_time += 1
        logger.info(f"try to explore new step {event}")
        original: list[Step] = self.result.copy()

        layout_before = self.__capture()
        if not event.perform(self.device):
            logger.error(f"perform new step failed: {event}")
            return False

        layout_after = self.__capture()

        self.result.append(
            Step(
                event,
                Ui(layout_before.xml, layout_before.png),
                Ui(layout_after.xml, layout_after.png),
            )
        )

        # 剪枝，如果执行后界面无变更则提前返回
        if self.optimize_explore and tree_equal(layout_before.root, layout_after.root):
            logger.info("UI not change after exploration, return")
            self.result = original
            return False

        if self.__match_current() or self.__match_next():
            return True
        else:
            # 恢复现场
            logger.info("explore failed")
            self.result = original
            self.__recover()
            return False

    def __exec_assertion(self, next_step: bool = False) -> bool:
        """对断言进行修复

        如果当前操作不是断言，则直接返回 False 以进行后续修复，否则执行断言

        如果断言执行成功，则进行下一步，否则认为修复失败，直接退出

        Returns:
            bool: 是否修复成功
        """
        current_step = (
            self.testcase[self.current]
            if not next_step
            else self.testcase[self.current + 1]
        )
        current_event = deepcopy(current_step.event)
        if current_event.is_assertion():
            layout_before = self.__capture()
            if current_event.perform(self.device):
                # 断言成功
                self.result.append(
                    Step(
                        current_event,
                        Ui(layout_before.xml, layout_before.png),
                        Ui(layout_before.xml, layout_before.png),
                    )
                )
                self.current += 1 if not next_step else 2
                return True
            else:
                # 断言失败
                if next_step:
                    logger.info("next step assertion failed")
                    return False
                logger.error("assertion failed")
                self.__quit(False)
        else:
            return False

    def __match_current(self) -> bool:
        """尝试在当前界面匹配当前步骤

        Returns:
            bool: 是否修复成功
        """
        logger.info("try to match current step...")
        current_step = self.testcase[self.current]
        return self.__exec_assertion() or self.__match(current_step)

    def __match_next(self) -> bool:
        """尝试对下一步进行匹配

        Returns:
            bool: 是否修复成功
        """
        if self.current + 1 >= len(self.testcase):
            return False
        logger.info("try to match next step...")
        next_step = self.testcase[self.current + 1]
        return self.__exec_assertion(next_step=True) or self.__match(next_step, 2)

    def __try(self, step: Step, offset: int = 1) -> bool:
        """尝试直接执行步骤

        Args:
            step (Step): 待执行步骤
            offset (int, optional): 执行成功后当前指针增加的偏移量. Defaults to 1.

        Returns:
            bool: 是否执行成功
        """
        layout_before = self.__capture()
        if step.event.perform(self.device):
            layout_after = self.__capture()
            self.result.append(
                Step(
                    step.event,
                    Ui(layout_before.xml, layout_before.png),
                    Ui(layout_after.xml, layout_after.png),
                )
            )
            self.current += offset
            logger.info("Succeed")
            return True
        else:
            logger.info("Fail")
            return False

    def __match(self, step: Step, offset: int = 1) -> bool:
        """尝试匹配并执行步骤

        Args:
            step (Step): 待执行的步骤
            offset (int, optional): 执行成功后当前指针增加的偏移量. Defaults to 1.

        Returns:
            bool: 是否执行成功
        """
        if step.event.is_assertion():
            return False

        if (locator := step.event.locator) is None:
            # 没有 locator 的步骤不需要匹配修复
            logger.info("event without locator")
            return self.__try(step, offset)

        # capture and match
        layout_before = self.__capture()
        base_layout = Layout(*step.ui_before)
        result = match_layout(base_layout, layout_before)

        if (old_child := locator.find_in_layout(base_layout.root)) is None:
            logger.error("cannot find node in base layout")
            self.__quit(False)

        if old_child in result.matched:
            target = result.matched[old_child]
            locator = Locator.from_node(target)
            new_event = replace(step.event, locator=locator)
            logger.info(f"repair current step :{new_event}")

            if new_event.perform(self.device):
                layout_after = self.__capture()

                if tree_equal(layout_before.root, layout_after.root):
                    # 点击前后 ui 无变化，认为该步不产生影响，跳过
                    logger.info("Succeed, UI not change after repair, skip")
                    self.current += offset
                    return True

                self.result.append(
                    Step(
                        new_event,
                        Ui(layout_before.xml, layout_before.png),
                        Ui(layout_after.xml, layout_after.png),
                    )
                )
                self.current += offset
                logger.info("Succeed")
                return True
            else:
                logger.error(f"Perform new step failed {new_event}")
                self.__quit(False)
        else:
            logger.info("Fail")
            return False
