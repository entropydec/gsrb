import logging
import re
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from typing import Callable, NamedTuple
from xml.etree.ElementTree import Element, canonicalize, tostring

import cv2
from Levenshtein import ratio

from gsrb.utils.element import coordinates

logger = logging.getLogger(__name__)

id_pattern = r"^(?:[A-Za-z][A-Za-z\d_]*)(?:\.[A-Za-z][A-Za-z\d_]*)*:id/(?P<content>.*)$"

threshold = 0.70


def attr_equal(a: Element, b: Element, name1: str, name2: str | None = None) -> bool:
    """判定两个节点的某属性是否相等

    如果有其中一个节点属性为空，则认为不相等

    Args:
        a (Element): 组件 A
        b (Element): 组件 B
        attr (str): 属性名

    Returns:
        bool: 是否相等
    """
    attr_a = a.get(name1, "").strip().lower()
    if name2 is None:
        attr_b = b.get(name1, "").strip().lower()
    else:
        attr_b = b.get(name2, "").strip().lower()
    if attr_a == "" or attr_b == "":
        return False
    attr_a = re.sub(r"\s+", " ", attr_a).strip()
    attr_b = re.sub(r"\s+", " ", attr_b).strip()

    return attr_a == attr_b


def attr_like(a: Element, b: Element, name1: str, name2: str | None = None) -> bool:
    """判定两个节点的某属性是否相似

    相似判断：相似度是否大于阈值

    Args:
        a (Element): 组件 A
        b (Element): 组件 B
        name1 (str): 属性名
        name2 (str | None): 另一个属性名，如果不为空则用组件 A 的 name1 属性与组件 B 的 name2 属性比较

    Returns:
        bool: 是否相似
    """

    def process_id(s: str) -> str:
        if len(s) == 0:
            return s
        else:
            if match := re.match(id_pattern, s):
                return match.group("content")
            else:
                logger.warning(f"resource-id not match pattern: {s}")
                return s

    attr_a = a.get(name1, "").strip().lower()
    if name1 == "resource-id":
        attr_a = process_id(attr_a)
    attr_b = (
        b.get(name1, "").strip().lower()
        if name2 is None
        else b.get(name2, "").strip().lower()
    )
    if (name2 is None and name1 == "resource-id") or (
        name2 is not None and name2 == "resource-id"
    ):
        attr_b = process_id(attr_b)

    if attr_a == "" or attr_b == "":
        return False

    attr_a = re.sub(r"\s+", " ", attr_a).strip().lower()
    attr_b = re.sub(r"\s+", " ", attr_b).strip().lower()

    similarity = ratio(attr_a, attr_b)
    return similarity >= threshold


def is_list(node: Element) -> bool:
    """判断给定节点是否是列表组件

    Args:
        node (Element): 节点

    Returns:
        bool: 是否为列表组件
    """
    return node.get("class") in {
        "android.view.ViewGroup",
        "android.widget.GridView",
        "android.widget.ListView",
        "android.widget.FrameLayout",
        "android.widget.GridLayout",
        "android.widget.LinearLayout",
        "android.widget.RelativeLayout",
        "androidx.recyclerview.widget.RecyclerView",
    }


def is_child(node: Element) -> bool:
    """判断一个组件是否是可参与匹配的叶节点

    判断标准：

    * 本身为叶节点
    * 面积不为零
    * 不是列表组件
    * text 不为空，或是尺寸不小于 15 x 15
    * text/resource-id/content-desc 至少有一个属性不为空

    Args:
        node (Element): 待判断节点

    Returns:
        bool: 判断结果
    """
    if len(node) != 0:
        return False

    if node.get("resource-id", "").startswith("com.google.android.inputmethod"):
        # 输入法
        return False

    if node.get("w") == "0" or node.get("h") == "0":
        return False

    if int(node.get("w", "0")) * int(node.get("h", "0")) >= 1080 * 1920 * 0.6:
        # too big
        return False

    not_list = not is_list(node)
    has_text = node.get("text") != ""
    not_empty = (
        has_text or node.get("content-desc") != "" or node.get("resource-id") != ""
    )
    big_enough = int(node.get("w", "0")) >= 15 and int(node.get("h", "0")) >= 15

    return not_list and (not_empty or big_enough)


def is_parent(node: Element) -> bool:
    """判断组件是否为父节点

    标准：

    * id 与 desc 至少有一个不为空
    * 是列表类组件，或子节点数不为零

    Args:
        node (Element): 节点

    Returns:
        bool: 是否为父节点
    """
    if node.get("w") == "0" or node.get("h") == "0":
        return False

    not_empty = node.get("resource-id", "") != "" or node.get("content-desc", "") != ""

    return not_empty and (len(node) > 0 or is_list(node))


def is_cover(a: Element, b: Element) -> bool:
    """判断组件 A 是否覆盖组件 B

    默认 A 位于 B 组件之上，覆盖的判断条件为：组件 B 的中心位于组件 A 内部

    这种情况下交互组件 B 实际上交互的是组件 A

    >>> from xml.etree.ElementTree import fromstring
    >>> a_str = "<node bounds='[100, 100][400, 400]' />"
    >>> a = fromstring(a_str)
    >>> b_str = "<node bounds='[0,0][500,250]' />"
    >>> b = fromstring(b_str)
    >>> is_cover(a, b)
    True

    Args:
        a (Element): 组件 A
        b (Element): 组件 B

    Returns:
        bool: 是否覆盖
    """
    ax0, ay0, ax1, ay1 = coordinates(a)
    bx0, by0, bx1, by1 = coordinates(b)
    center_x, center_y = (bx0 + bx1) / 2, (by0 + by1) / 2

    h_cover = ax0 <= center_x <= ax1
    v_cover = ay0 <= center_y <= ay1

    return h_cover and v_cover


def is_overlap(a: Element, b: Element) -> bool:
    """判断两个组件是否有重叠

    >>> from xml.etree.ElementTree import fromstring
    >>> a_str = "<node bounds='[100, 100][300, 300]' />"
    >>> a = fromstring(a_str)
    >>> b_str = "<node bounds='[200, 200][400, 400]' />"
    >>> b = fromstring(b_str)
    >>> is_overlap(a, b)
    True

    Args:
        a (Element): 组件 A
        b (Element): 组件 B

    Returns:
        bool: 是否重叠
    """
    ax0, ay0, ax1, ay1 = coordinates(a)
    bx0, by0, bx1, by1 = coordinates(b)

    xmin, xmax = min(ax1, ax1), max(ax0, bx0)
    h_overlap = xmin > xmax
    ymin, ymax = min(ay1, by1), max(ay0, by0)
    v_overlap = ymin > ymax
    return h_overlap and v_overlap


def is_match(a: Element, b: Element, *, strict: bool = True) -> bool:
    """判断两个组件是否匹配

    默认为严格匹配，需要以下三个属性至少有两个相等

    * resource-id
    * content-desc
    * text

    非严格匹配则只需要三个属性有一个相等

    Args:
        a (Element): 组件 A
        b (Element): 组件 B
        strict (bool, optional): 是否严格匹配. Defaults to True.

    Returns:
        bool: 匹配结果
    """
    results = [
        attr_equal(a, b, "resource-id"),
        attr_equal(a, b, "content-desc"),
        attr_equal(a, b, "text"),
    ]

    equal_num = sum([1 if x else 0 for x in results])

    if strict:
        return equal_num >= 2
    else:
        return equal_num >= 1


def is_like(a: Element, b: Element, strict: bool = True) -> bool:
    """判断两个组件是否模糊匹配

    模糊匹配不判断属性是否相等，而判断是否相似度超过阈值。严格匹配的定义同上

    Args:
        a (Element): 组件 A
        b (Element): 组件 B

    Returns:
        bool: 匹配结果
    """
    if (
        a.get("text", "") == ""
        and b.get("text", "") == ""
        and a.get("content-desc", "") == ""
        and b.get("content-desc", "") == ""
        and attr_like(a, b, "resource-id")
        and a.get("class", "") == b.get("class", "")
        and a.get("class") in {"android.widget.EditText"}
    ):
        return True

    if (attr_like(a, b, "resource-id") or not strict) and (
        attr_like(a, b, "text")
        or attr_like(a, b, "content-desc")
        or attr_like(a, b, "text", "content-desc")
        or attr_like(a, b, "content-desc", "text")
    ):
        return True

    if (
        (
            attr_equal(a, b, "text", "content-desc")
            or attr_equal(a, b, "content-desc", "text")
        )
        and a.get("class") not in {"android.widget.RadioButton"}
        and b.get("class") not in {"android.widget.RadioButton"}
    ):
        return True

    return False


def is_diff(
    a: Element, b: Element, *, diff_dict: dict[str, tuple[str, str]] | None = None
) -> bool:
    """根据属性集合判断两个节点是否存在差异

    Args:
        a (Element): 节点 A
        b (Element): 节点 B
        diff_dict (dict[str, tuple[str, str]] | None, optional): 属性名与值对应的字典，
        如果该参数非空，则会在比较过程中设置该字典. Defaults to None.

    Returns:
        bool: 是否存在差异
    """
    attr_list: list[str] = [
        "resource-id",
        "text",
        "content-desc",
        "class",
        "resource-id-index",
        "text-index",
        "content-desc-index",
        "class-index",
    ]
    result = False
    for attr in attr_list:
        attr_a = a.attrib.get(attr, "")
        attr_b = b.attrib.get(attr, "")
        if diff_dict is not None:
            diff_dict[attr] = (attr_a, attr_b)
        if attr_a != attr_b:
            result = True
    return result


def tree_equal(a: Element, b: Element) -> bool:
    """判断两颗 xml 树是否完全相等

    >>> from xml.etree.ElementTree import fromstring
    >>> a = "<node><node a='a' b='b' /></node>"
    >>> b = "<node><node b='b' a='a' /></node>"
    >>> tree_equal(fromstring(a), fromstring(b))
    True

    Args:
        a (Element): 根节点 A
        b (Element): 根节点 B

    Returns:
        bool: 是否完全相等
    """
    data_a = tostring(a, encoding="unicode")
    data_b = tostring(b, encoding="unicode")

    return canonicalize(data_a) == canonicalize(data_b)


def is_in_bound(point: cv2.KeyPoint, node: Element) -> bool:
    x, y = int(node.get("x", "0")), int(node.get("y", "0"))
    w, h = int(node.get("w", "0")), int(node.get("h", "0"))

    px, py = point.pt
    assert isinstance(px, float) and isinstance(py, float)

    return x < px < x + w and y < py < y + h


def default_filter(candidates: Iterable[Element]) -> list[Element]:
    return [c for c in candidates]


def default_key(candidate: Element) -> tuple[int, int]:
    coord = coordinates(candidate)
    return (coord.y0, coord.x0)


def optimize_filter_generator(
    non_overlap: Mapping[Element, Element]
) -> Callable[[Iterable[Element]], list[Element]]:
    def key(e: Element) -> tuple[int, ...]:
        coord = coordinates(e)
        return (
            0 if e.get("class", "") == "android.widget.TextView" else 1,
            coord.y0,
            coord.x0,
            len(e.get("text", "")),
            len(e.get("content-desc", "")),
        )

    def func(candidates: Iterable[Element]) -> list[Element]:
        result: list[Element] = []

        # 先过滤掉不能点击交互的控件
        candidates = filter(
            lambda x: x.get("class", "")
            not in {
                "android.widget.CheckBox",
                "android.widget.EditText",
                "android.widget.Switch",
            },
            candidates,
        )
        temp: dict[Element, list[Element]] = defaultdict(list)
        for candidate in candidates:
            if candidate not in non_overlap:
                result.append(candidate)
            else:
                temp[non_overlap[candidate]].append(candidate)

        for siblings in temp.values():
            if len(siblings) == 1:
                result.append(siblings[0])
            else:
                result.append(sorted(siblings, key=key)[0])

        return result

    return func


class CustomKey(NamedTuple):
    id_unique: int
    text_unique: int
    desc_unique: int
    id_empty: int
    text_empty: int
    desc_empty: int
    id_num: int
    text_num: int
    desc_num: int
    y0: int
    x0: int


def optimize_key_generator(
    candidates: Iterable[Element],
) -> Callable[[Element], tuple[float, ...]]:
    id_counter = Counter([candidate.get("resource-id", "") for candidate in candidates])
    text_counter = Counter([candidate.get("text", "") for candidate in candidates])
    desc_counter = Counter(
        [candidate.get("content-desc", "") for candidate in candidates]
    )

    def func(candidate: Element) -> tuple[float, ...]:
        resource_id = candidate.get("resource-id", "")
        text = candidate.get("text", "")
        content_desc = candidate.get("content-desc", "")
        coord = coordinates(candidate)
        return tuple(
            CustomKey(
                0 if resource_id != "" and id_counter[resource_id] == 1 else 1,
                0 if text != "" and text_counter[text] == 1 else 1,
                0 if content_desc != "" and desc_counter[content_desc] == 1 else 1,
                0 if resource_id == "" else 1,
                0 if text == "" else 1,
                0 if content_desc == "" else 1,
                id_counter[resource_id],
                text_counter[text],
                desc_counter[content_desc],
                coord.y0,
                coord.x0,
            )
        )

    return func
