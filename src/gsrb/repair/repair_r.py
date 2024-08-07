import logging
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Callable

from uiautomator2 import Device, connect

from gsrb.common.step import Step, TestCase, Ui
from gsrb.match.layout import Layout
from gsrb.utils.app import get_version, init_app

logger = logging.getLogger(__name__)


class Code(Enum):
    NEXT_LOOP = auto()
    CONTINUE = auto()
    ABORT = auto()


@dataclass
class RepairSession:
    # 修复输入
    testcase: TestCase
    package: str
    pretest: str | None

    # 设备信息
    device_serial: str
    device: Device = field(init=False)

    # 修复输出
    result: TestCase = field(init=False, default_factory=list)

    # 修复中间变量
    _current: int = field(init=False, default=0)
    flag: bool = field(init=False, default=True)
    generated_assertion: dict[Step, Step] = field(init=False, default_factory=dict)
    result_assertion: dict[Step, Step] = field(init=False, default_factory=dict)

    @property
    def current(self) -> int:
        return self._current

    @current.setter
    def current(self, value: int) -> None:
        logger.debug(f"update current: {self._current} -> {value}")
        self._current = value

    def __post_init__(self) -> None:
        # init device
        self.device = connect(self.device_serial)
        self.device.implicitly_wait(3.0)

        logger.info(f"init device {self.device_serial}")

        # init pretest
        if self.pretest is not None:
            logger.info("init pretest")
            self.pretest = self.pretest.replace(
                "u2.connect()", f'u2.connect("{self.device_serial}")'
            ).replace(
                "uiautomator2.connect()",
                f'uiautomator2.connect("{self.device_serial}")',
            )
            logger.info(f"pretest: \n{self.pretest}")

        # init generated_assertion
        temp: list[Step] = [
            step for step in self.testcase if not step.event.is_generated_assertion()
        ]

        for i in range(len(self.testcase) - 1):
            if self.testcase[i + 1].event.is_generated_assertion():
                self.generated_assertion[self.testcase[i]] = self.testcase[i + 1]
        self.testcase = temp

    def run(self) -> bool:
        if not self.setup():
            logger.error("setup failed")
            return False

        return self.repair()

    def setup(self) -> bool:
        logger.info("repair setup")

        # get apk info
        if (version := get_version(self.device_serial, self.package)) is None:
            logger.error(
                f"unable to get version of {self.package} "
                f"on device {self.device_serial}, "
                "please check install state"
            )
            return False

        logger.info(f"target apk: {self.package}")
        logger.info(f"target version: {version}")

        # get step info
        for i, step in enumerate(self.testcase):
            logger.info(f"step {i:0>2}: {step}")
            if step in self.generated_assertion:
                logger.info(f"generated assertion: {self.generated_assertion[step]}")

        return True

    def repair(self) -> bool:
        logger.info("repair start")
        logger.info("init app")

        init_app(self.device, self.package, self.pretest)

        while self.flag and self.current < len(self.testcase):
            logger.info(f"repair step {self.testcase[self.current]}")

            methods: list[Callable[[], Code]] = [self.execute_current_assertion]

            for method in methods:
                code = method()
                logger.info(code.name)
                match code:
                    case Code.NEXT_LOOP:
                        break
                    case Code.CONTINUE:
                        continue
                    case Code.ABORT:
                        self.flag = False
                        break

        return True

    def execute_assertion(self, step: Step, next_step: bool = False) -> Code:
        if not step.event.is_assertion():
            logger.info("current step is not an assertion")
            return Code.CONTINUE
        layout_before = Layout.from_device(self.device)
        new_step = Step(
            step.event,
            Ui(*layout_before.ui),
            Ui(*layout_before.ui),
        )
        if step.event.perform(self.device):
            self.result.append(new_step)
            self.current += 1 if not next_step else 2
            logger.info("assertion passed")
            return Code.NEXT_LOOP
        else:
            logger.info("assertion failed")
            return Code.ABORT if not next_step else Code.CONTINUE

    # def match_step(self, * , next_step: bool = False) -> Code:

    def execute_current_assertion(self) -> Code:
        logger.info("execute current step as assertion")
        return self.execute_assertion(self.testcase[self.current])

    # def execute_next_assertion(self) -> Code:
    #     logger.info("execute next step as assertion")
    #     return
