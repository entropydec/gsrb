"""定义数据类 Event"""
from __future__ import annotations

import logging
import time
from collections.abc import Mapping
from dataclasses import dataclass, field
from importlib.resources import files
from string import Template

from uiautomator2 import Device, UiObjectNotFoundError

from gsrb.common.action import Action
from gsrb.common.locator import Locator
from gsrb.common.mixin import JsonMixin

logger = logging.getLogger(__name__)

PERFORM_INTERVAL = 1

TEMPLATE_U2: Template = Template(
    files("gsrb.common")
    .joinpath("templates")
    .joinpath("u2.txt")
    .read_text(encoding="utf-8")
)


@dataclass(frozen=True)
class Event(JsonMixin):
    """表示一个具体事件的数据类

    事件的定义是一个三元组 (a, l, p)

    * a 为事件的类型，如点击/滑动/长按等
    * l 为事件所关联的控件的定位符，可以根据该定位符在界面上找到控件，再根据事件类型与控件将事件复现
    * p 为复现事件所需的额外参数

    事件一般关联一个定位符，根据事件类型的不同也可能不关联定位符（如 BACK 事件）
    """

    action: Action
    locator: Locator | None = None
    parameter: Mapping[str, object] = field(default_factory=dict)

    def perform(self, device: Device) -> bool:
        """在设备上执行当前 event

        Args:
            device (Device): 连接的设备

        Returns:
            bool: 是否执行成功
        """
        try:
            if self.locator is None:
                self.action.perform(device, parameter=self.parameter)
            else:
                ui_object = self.locator.find_in_device(device)
                self.action.perform(device, ui_object, parameter=self.parameter)
            time.sleep(PERFORM_INTERVAL)
        except (AssertionError, ValueError, UiObjectNotFoundError):
            return False
        return True

    def is_assertion(self) -> bool:
        """返回当前步骤的事件是否为断言操作

        Returns:
            bool: 是否为断言
        """
        return self.action.is_assertion()

    def is_generated_assertion(self) -> bool:
        return self.is_assertion() and "generated" in self.parameter

    def to_dict(self) -> dict[str, object]:
        """将自身序列化为字典

        Returns:
            dict[str, Any]: 序列化结果
        """
        d: dict[str, object] = dict()
        d["action"] = self.action.name
        if self.locator is not None:
            d["locator"] = self.locator.to_dict()
        if len(self.parameter) > 0:
            d["parameter"] = self.parameter
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, object]) -> Event:
        """从字典中反序列化的工厂方法

        Args:
            d (Mapping[str, Any]): 输入字典

        Returns:
            Event: 事件
        """
        assert isinstance(action_name := d["action"], str)
        action = Action[action_name]
        locator = None
        if "locator" in d and isinstance(locator_dict := d["locator"], dict):
            locator = Locator.from_dict(locator_dict)
        parameter = d.get("parameter", dict())
        assert isinstance(parameter, dict)
        return cls(action, locator, parameter)

    def with_parameter(self, param: Mapping[str, object]) -> Event:
        p: dict[str, object] = dict()
        p.update(self.parameter)
        p.update(param)
        return Event(self.action, self.locator, p)

    def generate_u2(self, device_part: str) -> str:
        locator_part = "" if self.locator is None else self.locator.generate_u2()
        prefix = f"{device_part}{locator_part}"
        suffix = ""

        if "generated" in self.parameter or "repaired" in self.parameter:
            suffix = "  # "
            if "generated" in self.parameter:
                suffix = f"{suffix}generated"
            if "repaired" in self.parameter:
                suffix = f"{suffix}repaired"

        match self.action:
            case Action.CLICK:
                return f"{prefix}.click(){suffix}"
            case Action.LONG_CLICK:
                return f"{prefix}.long_click(){suffix}"
            case Action.SET_TEXT:
                return (
                    f"{prefix}.set_text(\"{self.parameter.get('text', '')}\"){suffix}"
                )
            case Action.EXIST:
                if "failed" in self.parameter:
                    return f"# assert {prefix}.exists{suffix}"
                else:
                    return f"assert {prefix}.exists{suffix}"
            case Action.NOT_EXIST:
                return f"assert not {prefix}.exists{suffix}"
            case Action.BACK:
                return f'{prefix}.press("back"){suffix}'
            case Action.EQUAL:
                return f"assert {prefix}.info[\"{self.parameter['attr']}\"] == \"{self.parameter['oracle']}\"{suffix}"  # noqa
            case Action.NOT_EQUAL:
                return f"assert {prefix}.info[\"{self.parameter['attr']}\"] != \"{self.parameter['oracle']}\"{suffix}"  # noqa
            case Action.SWIPE:
                return f"{prefix}.swipe({self.parameter['fx']}, {self.parameter['fy']}, {self.parameter['tx']}, {self.parameter['ty']}){suffix}"  # noqa

    def __repr__(self) -> str:
        return self.to_json()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Event):
            return (
                self.action == __value.action
                and self.locator == __value.locator
                and self.parameter == __value.parameter
            )
        return False

    def __hash__(self) -> int:
        parameter = tuple(sorted(self.parameter.items()))
        return hash((self.action, self.locator, *parameter))
