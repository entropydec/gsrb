"""定义枚举类 Criterion"""
from __future__ import annotations

import logging
from enum import Enum, auto
from functools import total_ordering
from xml.etree.ElementTree import Element

logger = logging.getLogger(__name__)


@total_ordering
class Criterion(Enum):
    """用于表示定位组件方式的枚举类，本质是一个谓词

    如 Criterion.ID 表示判断给定节点的 resource-id 属性是否与给定标识符相等
    """

    ID = auto()
    DESC = auto()
    CLASS = auto()
    TEXT = auto()

    @property
    def u2_name(self) -> str:
        match self:
            case Criterion.ID:
                return "resourceId"
            case Criterion.DESC:
                return "description"
            case Criterion.CLASS:
                return "className"
            case Criterion.TEXT:
                return "text"

    def __call__(self, node: Element, identifier: str) -> bool:
        """判断给定节点是否与 identifier 匹配

        >>> from xml.etree.ElementTree import fromstring
        >>> n = fromstring('<node text="Documents"/>')
        >>> criterion = Criterion.TEXT
        >>> criterion(n, "Documents")
        True

        Args:
            node (Element): 待判断节点
            identifier (str): 标识符

        Returns:
            bool: 返回匹配结果
        """

        match self:
            case Criterion.ID:
                return node.get("resource-id") == identifier
            case Criterion.DESC:
                return node.get("content-desc") == identifier
            case Criterion.CLASS:
                return node.get("class") == identifier
            case Criterion.TEXT:
                return node.get("text") == identifier

    @classmethod
    def from_parameter(cls, name: str) -> Criterion | None:
        match name:
            case "resourceId":
                return cls.ID
            case "description":
                return cls.DESC
            case "text":
                return cls.TEXT
            case "className":
                return cls.CLASS
            case _:
                return None

    def __repr__(self) -> str:
        return self.name

    def __lt__(self, other: object) -> bool:
        if isinstance(other, Criterion):
            return self.value < other.value
        return NotImplemented
