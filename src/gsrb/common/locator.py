"""定义数据类 Locator"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from xml.etree.ElementTree import Element

from uiautomator2 import Device, UiObject

from gsrb.common.criterion import Criterion
from gsrb.common.mixin import JsonMixin

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Locator(JsonMixin):
    """用于定位控件的数据类

    用于在布局文件或实际界面上根据 Criterion 与标识符定位控件。

    Locator 可以关联一个或多个 Criterion。每个 Criterion 有各自的标识符，定位时需要全都满足。

    index 用于满足 criteria 的组件有多个时根据下标唯一确定控件
    """

    criteria: Mapping[Criterion, str]
    index: int = 0

    def find_in_layout(self, node: Element) -> Element | None:
        """在布局树中根据定位符寻找控件

        >>> from xml.etree.ElementTree import fromstring
        >>> from gsrb.common.criterion import Criterion
        >>> s = "<hierarchy><node text='a'><node text='b'/></node></hierarchy>"
        >>> n = fromstring(s)
        >>> locator = Locator({Criterion.TEXT: "b"}, 0)
        >>> locator.find_in_layout(n) is not None
        True

        Args:
            node (Element): 布局树的根节点

        Returns:
            Element | None: 返回找到的控件，或者空
        """
        matched: list[Element] = []
        for n in node.iter("node"):
            if all(k(n, v) for k, v in self.criteria.items()):
                matched.append(n)
        if len(matched) == 0 or self.index >= len(matched):
            return None

        return matched[self.index]

    def find_in_device(self, device: Device) -> UiObject:
        """使用 Device 在当前界面动态寻找控件

        Args:
            device (Device): 当前设备

        Returns:
            UiObject: 找到的控件

        Raises:
            UiObjectNotFoundError: 找不到控件
        """
        return device(**self.to_kwargs())[self.index]

    def to_kwargs(self) -> dict[str, str]:
        """获取用于 u2 定位的参数字典

        Returns:
            dict[str, str | bool]: 参数字典
        """
        return {k.u2_name: v for k, v in self.criteria.items()}

    def to_dict(self) -> dict[str, object]:
        """将自身序列化为字典

        Returns:
            dict[str, Any]: 序列化结果
        """
        d: dict[str, object] = dict()
        d["criteria"] = {k.name: v for k, v in self.criteria.items()}
        if self.index != 0:
            d["index"] = self.index
        return d

    @classmethod
    def from_dict(cls, d: Mapping[str, object]) -> Locator:
        """从字典中反序列化的工厂方法

        Args:
            d (dict[str, Any]): 输入字典

        Returns:
            Locator: 定位符
        """
        c: dict[Criterion, str] = dict()

        criteria = d["criteria"]
        index = d.get("index", 0)
        assert isinstance(index, int) and isinstance(criteria, Mapping)

        for k, v in criteria.items():
            try:
                criterion = Criterion[k]
            except KeyError:
                logger.warning(f"unknown criterion: {k}")
                continue
            c[criterion] = v

        return cls(c, index)

    @classmethod
    def from_node(cls, node: Element) -> Locator:
        """从节点中生成定位符

        Args:
            node (Element): 节点

        Returns:
            Locator: 定位符
        """
        for attr, criterion in (
            ("text", Criterion.TEXT),
            ("content-desc", Criterion.DESC),
            ("resource-id", Criterion.ID),
        ):
            if (identifier := node.get(attr, "")) != "":
                index = int(node.get(f"{attr}-index", "0"))
                return cls({criterion: identifier}, index)
        identifier = node.get("class", "")
        index = int(node.get("class-index", "0"))
        return cls({Criterion.CLASS: identifier}, index)

    def generate_u2(self) -> str:
        temp: list[str] = []
        for k, v in self.to_kwargs().items():
            temp.append(f"{k}={repr(v)}")
        if self.index != 0:
            temp.append(f"instance={repr(self.index)}")
        result = f"({', '.join(temp)})"
        return result

    def __repr__(self) -> str:
        return self.to_json()

    def __eq__(self, __value: object) -> bool:
        if isinstance(__value, Locator):
            return self.criteria == __value.criteria and self.index == __value.index
        return False

    def __hash__(self) -> int:
        criteria = tuple(sorted(self.criteria.items()))
        return hash((self.index, *criteria))
