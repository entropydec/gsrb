import io
import json
import logging
import re
from typing import NamedTuple
from xml.etree.ElementTree import Element, fromstring

from PIL import Image, ImageDraw

from gsrb.common.locator import Locator

bound_pattern = (
    r"^\s*\[(?P<x0>\d+)\s*,\s*(?P<y0>\d+)]\[(?P<x1>\d+)\s*,\s*(?P<y1>\d+)]\s*$"  # noqa
)

logger = logging.getLogger(__name__)


class Coordinate(NamedTuple):
    x0: int = 0
    y0: int = 0
    x1: int = 0
    y1: int = 0


def coordinates(node: Element | str) -> Coordinate:
    """根据节点的 bounds 属性返回对应的坐标值

    如果解析失败，返回 0, 0, 0, 0

    >>> from xml.etree.ElementTree import fromstring
    >>> x = "<node bounds='[189,1174][404,1231]' />"
    >>> a = fromstring(x)
    >>> tuple(coordinates(a))
    (189, 1174, 404, 1231)
    >>> tuple(coordinates("[189,1174][404,1231]"))
    (189, 1174, 404, 1231)

    Args:
        node (Element | str): 节点或节点的 bounds 属性

    Returns:
        tuple[int, int, int, int]: 左上角和右下角的坐标
    """
    if isinstance(node, Element):
        bounds = node.get("bounds", "[0,0][0,0]")
    else:
        bounds = node
    if match := re.match(bound_pattern, bounds):
        return Coordinate(
            int(match.group("x0")),
            int(match.group("y0")),
            int(match.group("x1")),
            int(match.group("y1")),
        )
    return Coordinate()


def digest(node: Element) -> str:
    """将结点的关键属性转换成可读的字符串

    Args:
        node (Element): 节点

    Returns:
        str: 节点信息
    """
    result = dict()
    for name, attr in [
        ("c", "class"),
        ("t", "text"),
        ("d", "content-desc"),
        ("r", "resource-id"),
        ("b", "bounds"),
    ]:
        result[name] = node.get(attr, "")
    return json.dumps(result)


def draw_element(screen: bytes, layout: str, locator: Locator | None) -> bytes:
    if locator is None:
        return screen
    root = fromstring(layout)
    if (element := locator.find_in_layout(root)) is None:
        logger.warning(f"cannot find {layout} in root, return unchanged image")
        return screen
    with io.BytesIO(screen) as f, Image.open(f) as img:
        draw = ImageDraw.Draw(img)

        coord = coordinates(element)
        draw.rectangle(coord, width=5, outline="#FF0000")

        bio = io.BytesIO()
        img.save(bio, format="png")
        return bio.getvalue()
