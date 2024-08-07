"""定义枚举类 Action"""
import logging
from collections.abc import Mapping
from enum import Enum, auto

from uiautomator2 import Device, UiObject

logger = logging.getLogger(__name__)


class Action(Enum):
    """表示事件动作类型的枚举类

    如 Action.CLICK 表示点击操作。此处定义的动作仅仅为类型而非具体的动作
    """

    # 需要 locator 的动作
    CLICK = auto()
    """点击操作"""
    LONG_CLICK = auto()
    """长按操作"""
    SET_TEXT = auto()
    """设置文本"""
    EXIST = auto()
    """断言，判断节点是否存在"""
    NOT_EXIST = auto()
    """断言，判断节点是否不存在"""
    EQUAL = auto()
    """断言，判断属性是否相等"""
    NOT_EQUAL = auto()
    """断言，判断属性是否不相等"""

    # 不需要 locator 的动作
    BACK = auto()
    """BACK 操作"""
    SWIPE = auto()

    def perform(
        self,
        device: Device,
        ui_object: UiObject | None = None,
        *,
        parameter: Mapping[str, object],
    ) -> None:
        """在设备上执行当前动作

        Args:
            device (Device): 连接的设备
            locator (Locator | None): 与动作关联的定位符
            parameter (Mapping[str, Any]): 额外参数

        Raises:
            ValueError: 传入的 locator 与 action 不符
        """
        if ui_object is None:
            match self:
                case Action.BACK:
                    device.press("back")
                case Action.SWIPE:
                    device.swipe(
                        parameter["fx"],
                        parameter["fy"],
                        parameter["tx"],
                        parameter["ty"],
                    )
                case _:
                    raise ValueError(f"action {self.name} missing locator")
            return
        match self:
            case Action.CLICK:
                ui_object.click()
            case Action.LONG_CLICK:
                ui_object.long_click()
            case Action.SET_TEXT:
                ui_object.set_text(parameter["text"])
            case Action.EXIST:
                assert ui_object.exists
            case Action.NOT_EXIST:
                assert not ui_object.exists
            case Action.EQUAL:
                assert ui_object.info[parameter["attr"]] == parameter["oracle"]
            case Action.NOT_EQUAL:
                assert ui_object.info[parameter["attr"]] != parameter["oracle"]
            case _:
                raise ValueError(f"unexpected action {self.name}")

    def is_assertion(self) -> bool:
        """判断当前操作是否为断言

        >>> Action.EXIST.is_assertion()
        True
        >>> Action.CLICK.is_assertion()
        False

        Returns:
            bool: 是否为断言
        """
        match self:
            case Action.EXIST | Action.NOT_EXIST | Action.EQUAL | Action.NOT_EQUAL:
                return True
            case _:
                return False

    def __repr__(self) -> str:
        return self.name
