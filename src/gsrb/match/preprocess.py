import logging
from collections import defaultdict
from typing import Callable
from xml.etree.ElementTree import Element

from gsrb.utils.element import coordinates

logger = logging.getLogger(__name__)


def preprocess(node: Element) -> None:
    """对根节点进行预处理

    主要步骤包括

    * 移除系统的 UI 组件
    * 标注 index 信息
    * 标注坐标信息

    Args:
        node (Element): 根节点
    """
    remove_node(
        node,
        lambda n: n.get("package") == "com.android.systemui",
    )
    denote_index(node)
    denote_bounds(node)


def remove_node(node: Element, predictor: Callable[[Element], bool]) -> None:
    """从根节点移除满足条件的子节点

    主要用于移除与当前包无关的组件

    Args:
        node (Element): 根节点
        predictor (Callable[[Element], bool]): 判断移除的谓词
    """
    if node.tag != "hierarchy":
        return

    remove_list = [child for child in node if predictor(child)]
    for child in remove_list:
        node.remove(child)


def denote_index(node: Element) -> None:
    """根据节点属性值在全文中出现的次序为其标记 index

    Args:
        node (Element): 根节点
    """
    counters: dict[str, defaultdict[str, int]] = {
        "class": defaultdict(int),
        "resource-id": defaultdict(int),
        "content-desc": defaultdict(int),
        "text": defaultdict(int),
    }

    for child in node.iter("node"):
        if child.get("resource-id", "").startswith("com.google.android"):
            continue
        for k, c in counters.items():
            if child.get(k, "") != "":
                child.set(f"{k}-index", str(c[child.get(k, "")]))
                c[child.get(k, "")] += 1
            else:
                # 不考虑空属性的 index，一律设置为 -1
                child.set(f"{k}-index", str(-1))


def denote_bounds(node: Element) -> None:
    """根据节点的 bounds 属性，为其标注左上角坐标与宽高

    Args:
        node (Element): 节点
    """
    for child in node.iter("node"):
        x0, y0, x1, y1 = coordinates(child)
        child.attrib.update(
            {"x": str(x0), "y": str(y0), "w": str(x1 - x0), "h": str(y1 - y0)}
        )
