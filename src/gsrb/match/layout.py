"""定义数据类 Layout 以及一些预处理方法"""
from __future__ import annotations

import io
import logging
from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from xml.etree.ElementTree import Element, fromstring

from PIL import Image, ImageDraw, ImageFont
from uiautomator2 import Device

from gsrb.match.predictors import is_child, is_cover, is_overlap, is_parent
from gsrb.match.preprocess import preprocess
from gsrb.utils.element import coordinates, digest

logger = logging.getLogger(__name__)


def get_valid_node(node: Element) -> set[Element]:
    """获取所有可有效交互的组件

    Args:
        node (Element): 根节点

    Returns:
        set[Element]: 所有有效节点的集合
    """
    result: set[Element] = set()
    for n in node.iter("node"):
        # 选取所有被 n 覆盖的组件并删去
        if is_child(n) and n.get("clickable") == "true":
            result -= {x for x in result if is_child(x) and is_cover(n, x)}
        if is_child(n) and n.get("clickable") == "false":
            # 如果当前节点不可点击且有可点击的叶节点覆盖当前节点，不加入该节点
            if (
                len(
                    [
                        m
                        for m in result
                        if is_child(m)
                        and m.get("clickable") == "true"
                        and is_cover(m, n)
                    ]
                )
                > 0
            ):
                continue
        result.add(n)
    return result


def get_children(node: Element) -> set[Element]:
    """获取当前界面的叶节点

    叶节点除了要满足 `is_child` 还要满足是有效节点

    Args:
        node (Element): 根节点

    Returns:
        set[Element]: 叶节点集合
    """
    return {x for x in get_valid_node(node) if is_child(x)}


def get_parents(node: Element) -> set[Element]:
    """获取当前界面的非叶节点

    Args:
        node (Element): 根节点

    Returns:
        set[Element]: 非叶节点集合
    """
    return {x for x in node.iter("node") if is_parent(x)}


def compress_parents(parents: set[Element]) -> set[Element]:
    need_remove = set()
    for a in parents:
        for b in parents:
            if a != b and len(b) == 1 and b[0] == a:
                need_remove.add(b)

    return parents - need_remove


def get_list_items(children: Iterable[Element]) -> list[list[Element]]:
    """根据 resource-id 寻找可能为列表项的组件

    列表项中的 resource-id 相等

    Args:
        children (Element): 子节点集合

    Returns:
        list[list[Element]]: 可能为列表项的子节点集
    """
    result: list[list[Element]] = []
    counter: defaultdict[str, list[Element]] = defaultdict(list)
    for child in children:
        counter[child.get("resource-id", "")].append(child)
    for k, v in counter.items():
        if k != "" and len(v) > 1:
            result.append(v)
    return result


def get_non_overlap(
    children: Iterable[Element], cp: Mapping[Element, Element]
) -> dict[Element, Element]:
    """寻找一组子节点的最大无重叠父节点

    最大无重叠即这组子节点的父节点间彼此不重叠

    Args:
        children (list[Element]): 子节点集合
        cp (dict[Element, Element]): 子节点与其父节点的映射

    Returns:
        dict[Element, Element]: 子节点与其最大无重叠父节点的映射
    """
    result: dict[Element, Element] = dict()
    # 初始化父节点为自身
    for child in children:
        result[child] = child

    update: bool = True
    while update:
        update = False
        for child in result.keys():
            current_parent = result[child]
            next_parent = cp.get(current_parent)
            if next_parent and next_parent.tag != "hierarchy":
                other_parents = [result[k] for k in result.keys() if k != child]
                if all(not is_overlap(next_parent, parent) for parent in other_parents):
                    result[child] = next_parent
                    update = True
    return result


def get_non_unique(children: Iterable[Element]) -> set[Element]:
    """获取组件集合中不唯一的组件

    不唯一的标准：三元组 id desc text 完全相同

    Args:
        children (Iterable[Element]): 组件集合

    Returns:
        set[Element]: 不唯一的组件
    """
    result: set[Element] = set()

    def node_hash(node: Element) -> tuple[str, str, str]:
        return (
            node.get("resource-id", ""),
            node.get("content-desc", ""),
            node.get("text", ""),
        )

    counter = Counter([node_hash(child) for child in children])

    for k, v in counter.items():
        if v > 1:
            result.update(child for child in children if node_hash(child) == k)

    return result


def get_unique_children(children: Iterable[Element]) -> set[Element]:
    result: set[Element] = set()
    s = set()
    for child in children:
        if (class_name := child.get("class", "")) not in s:
            s.add(class_name)
            result.add(child)
        else:
            result = {x for x in result if x.get("class", "") != class_name}
    return result


@dataclass
class Layout:
    """代表界面信息的数据类

    存储了当前界面原始的截屏与布局，并且将布局解析后生成额外信息
    """

    xml: str
    png: bytes
    root: Element = field(init=False)
    children: set[Element] = field(init=False)
    """参与匹配的子节点集"""
    parents: set[Element] = field(init=False)
    """参与匹配的父节点集"""
    cp: dict[Element, Element] = field(init=False, default_factory=dict)
    """子节点到自身父节点的映射"""
    non_overlap: dict[Element, Element] = field(init=False, default_factory=dict)
    """列表项与自身最大无重叠父节点的映射"""
    non_unique: set[Element] = field(init=False, default_factory=set)
    """非唯一的列表项集合"""
    unique_children: set[Element] = field(init=False, default_factory=set)

    @property
    def digest(self) -> str:
        n = "\n"
        return f"```{n.join(map(digest, (c for c in self.children if not c.get('resource-id', '').startswith('com.google.android'))))}```"  # noqa

    @property
    def ui(self) -> tuple[str, bytes]:
        return self.xml, self.png

    def __post_init__(self) -> None:
        """在初始化后做后续信息处理

        包括：

        * 预处理布局树
        * 获取匹配用的子节点
        * 构造子节点与父节点的映射关系
        * 获取列表项与最大无重叠父节点的映射关系
        """
        self.root = fromstring(self.xml)
        preprocess(self.root)
        self.children = get_children(self.root)
        self.parents = get_parents(self.root)
        self.parents = compress_parents(self.parents)
        self.cp = {c: p for p in self.root.iter("node") for c in p}
        self.unique_children = get_unique_children(self.children)

        for children in get_list_items(self.children):
            self.non_overlap.update(get_non_overlap(children, self.cp))
            self.non_unique.update(get_non_unique(children))

    def draw(self, nodes: Iterable[Element], with_index: bool = False) -> None:
        """将节点轮廓画在截屏上，用于 debug 或展示

        Args:
            nodes (Iterable[Element]): 需要绘制的节点集合
        """
        if len(self.png) == 0:
            logger.error("missing screenshot data")
            return
        font = ImageFont.load_default(size=36)
        with io.BytesIO(self.png) as f, Image.open(f) as img:
            draw = ImageDraw.Draw(img)

            for i, node in enumerate(nodes):
                coord = coordinates(node)
                draw.rectangle(coord, width=5, outline="#00FF00")
                if with_index:
                    draw.text(
                        (coord.x0 + 5, coord.y0 + 5), str(i), font=font, fill="#FF0000"
                    )

            img.show()

    def draw_bounds(self, bounds: Iterable[str]) -> None:
        if len(self.png) == 0:
            logger.error("missing screenshot data")
            return

        with io.BytesIO(self.png) as f, Image.open(f) as img:
            draw = ImageDraw.Draw(img)
            for bound in bounds:
                draw.rectangle(coordinates(bound), width=5, outline="#FF0000")

            img.show()

    @staticmethod
    def from_device(device: Device) -> Layout:
        """使用 u2.Device 动态创建 Layout 对象

        Args:
            device (Device): device 实例

        Returns:
            Layout: 基于当前布局产生的 Layout 对象
        """
        xml = device.dump_hierarchy()
        png = device.screenshot(format="raw")
        assert isinstance(png, bytes)
        return Layout(xml, png)
