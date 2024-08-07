import io
import logging
from dataclasses import dataclass, field
from functools import reduce
from typing import Callable, Iterable
from xml.etree.ElementTree import Element

import cv2
import numpy as np
from PIL import Image

from gsrb.match.layout import Layout
from gsrb.match.predictors import attr_equal, is_in_bound, is_like, is_match
from gsrb.utils.element import digest

logger = logging.getLogger(__name__)

threshold = 0.8


@dataclass
class Result:
    """代表匹配结果的数据类"""

    score: float = 0.0
    is_match = False
    """界面是否匹配"""
    matched: dict[Element, Element] = field(init=False, default_factory=dict)
    """确定匹配的组件对"""
    possible: dict[Element, set[Element]] = field(init=False, default_factory=dict)
    """可能匹配的组件，每个旧版本组件对应新版本的一个组件集"""
    old_not_matched: set[Element] = field(init=False, default_factory=set)
    """旧版本未匹配组件"""
    new_not_matched: set[Element] = field(init=False, default_factory=set)
    """新版本未匹配组件"""


@dataclass
class MatchInfo:
    old: Layout
    new: Layout

    matched: set[Element] = field(init=False, default_factory=set)
    """已经被匹配的节点，不会参与后续匹配"""
    matched_parents: dict[Element, Element] = field(init=False, default_factory=dict)
    """在 sibling match 中被匹配的父节点对，用于后续优化匹配"""
    matched_points: dict[cv2.KeyPoint, cv2.KeyPoint] = field(
        init=False, default_factory=dict
    )

    def __post_init__(self) -> None:
        if len(self.old.png) == 0 or len(self.new.png) == 0:
            return

        img_old = cv2.imdecode(
            np.frombuffer(self.old.png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE
        )
        img_new = cv2.imdecode(
            np.frombuffer(self.new.png, dtype=np.uint8), cv2.IMREAD_GRAYSCALE
        )
        sift = cv2.SIFT.create()
        kp_old, desc_old = sift.detectAndCompute(
            img_old, np.full(img_old.shape, 255, np.uint8)
        )
        kp_new, desc_new = sift.detectAndCompute(
            img_new, np.full(img_new.shape, 255, np.uint8)
        )

        matcher = cv2.DescriptorMatcher.create(cv2.DescriptorMatcher_BRUTEFORCE)
        matches = matcher.knnMatch(desc_old, desc_new, 2)

        for match_pair in matches:
            m, n = match_pair[0], match_pair[1]
            if m.distance < n.distance * 0.8:
                self.matched_points[kp_old[m.queryIdx]] = kp_new[m.trainIdx]


def draw_matches(
    png_old: bytes, png_new: bytes, matches: dict[cv2.KeyPoint, cv2.KeyPoint]
) -> None:
    with io.BytesIO(png_old) as f1, io.BytesIO(png_new) as f2, Image.open(
        f1
    ) as img1, Image.open(f2) as img2:
        # 将 PIL.Image 对象转换为 numpy 数组
        i1 = np.array(img1)
        i2 = np.array(img2)
        # 获取两个图像的宽度和高度
        h1, w1 = i1.shape[:2]
        h2, w2 = i2.shape[:2]
        # 创建一个空白的图像，用于横向拼接两个图像
        img3 = np.zeros((max(h1, h2), w1 + w2, 3), dtype=np.uint8)
        # 将两个图像拷贝到空白图像上
        img3[:h1, :w1] = i1
        img3[:h2, w1:] = i2
        # 遍历匹配点字典，绘制匹配点和连线
        for kp1, kp2 in matches.items():
            # 获取匹配点的坐标
            x1, y1 = kp1.pt
            x2, y2 = kp2.pt
            # 将第二幅图像中的坐标加上第一幅图像的宽度，以便在拼接图像上显示
            x2 += w1
            # 绘制匹配点，使用圆形，颜色为蓝色，半径为 5，填充为实心
            cv2.circle(img3, (int(x1), int(y1)), 5, (0, 0, 255), -1)
            cv2.circle(img3, (int(x2), int(y2)), 5, (0, 0, 255), -1)
            # 绘制连线，使用直线，颜色为绿色，粗细为 3
            cv2.line(img3, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 1)
        # 将 numpy 数组转换为 PIL.Image 对象，并直接展示
        Image.fromarray(img3).show()


def match_sure(
    info: MatchInfo, result: Result, predictor: Callable[[Element, Element], bool]
) -> None:
    """进行确定匹配

    流程：

    * 选择新旧版本中的未匹配组件对
    * 如果满足匹配标准的有且仅有一个，则认为匹配成功
    * 如果是列表项，匹配兄弟节点

    Args:
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
        predictor (Callable[[Element, Element], bool]): 具体匹配的标准
    """
    logger.debug("start match sure")
    # 不能在这一步匹配不唯一的列表项
    old_candidates = info.old.children - info.old.non_unique
    new_candidates = info.new.children - info.new.non_unique
    update: bool = True
    while update:
        update = False
        for old_child in (n for n in old_candidates if n not in info.matched):
            candidates: list[Element] = []
            for new_child in (n for n in new_candidates if n not in info.matched):
                if predictor(old_child, new_child):
                    candidates.append(new_child)

            if len(candidates) == 1:
                update = True
                # 唯一候选
                candidate = candidates[0]
                result.matched[old_child] = candidate
                logger.debug(f"matched {digest(old_child)} {digest(candidate)}")
                info.matched.update([old_child, candidate])
                match_sibling(old_child, candidate, info, result)


def match_sibling(old: Element, new: Element, info: MatchInfo, result: Result) -> None:
    """匹配列表项的兄弟节点

    兄弟节点：即拥有同一个最大不重叠父节点的列表项

    Args:
        old (Element): 旧版本组件
        new (Element): 新版本组件
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
    """
    if old not in info.old.non_overlap or new not in info.new.non_overlap:
        # 双方都是列表项才可继续匹配
        return
    logger.debug("start match siblings")
    old_parent = info.old.non_overlap[old]
    new_parent = info.new.non_overlap[new]
    info.matched_parents[old_parent] = new_parent

    old_siblings = [
        k for k, v in info.old.non_overlap.items() if v == old_parent and k != old
    ]
    new_siblings = [
        k for k, v in info.new.non_overlap.items() if v == new_parent and k != new
    ]

    for old_sibling in (n for n in old_siblings if n not in info.matched):
        candidates: list[Element] = []
        for new_sibling in (
            n
            for n in new_siblings
            if n not in info.matched and is_match(old_sibling, n, strict=False)
        ):
            candidates.append(new_sibling)

        if len(candidates) == 1:
            candidate = candidates[0]
            result.matched[old_sibling] = candidate
            logger.debug(f"sibling matched {digest(old_sibling)} {digest(candidate)}")
            info.matched.update([old_sibling, candidate])


def match_possible(
    info: MatchInfo, result: Result, predictor: Callable[[Element, Element], bool]
) -> None:
    """进行可能匹配

    与确定匹配类似，基于匹配标准进行匹配，区别在于

    * 不考虑匹配数量，只要有一个及以上的组件满足标准，即加入匹配结果
    * 多个新界面组件可以重复参与匹配

    Args:
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
        predictor (Callable[[Element, Element], bool]): 匹配标准
    """
    logger.debug("start match possible")

    def get_unique_possible(
        attr: str, old: Element, candidates: Iterable[Element]
    ) -> Element | None:
        if (old_attr := old.get(attr, "").lower()) != "" and len(
            (
                attr_candidates := [
                    candidate
                    for candidate in candidates
                    if candidate.get(attr, "").lower() == old_attr
                    and candidate.get("class", "") == old.get("class", "")
                ]
            )
        ) == 1:
            return attr_candidates[0]
        return None

    for old_child in (n for n in info.old.children if n not in info.matched):
        candidates: set[Element] = set()
        for new_child in (n for n in info.new.children if n not in info.matched):
            if predictor(old_child, new_child):
                candidates.add(new_child)

        if len(candidates) > 0:
            # 寻找有没有唯一相等的
            if (
                (candidate := get_unique_possible("text", old_child, candidates))
                is not None
                or (
                    candidate := get_unique_possible(
                        "content-desc", old_child, candidates
                    )
                )
                is not None
                or (
                    (
                        candidate := get_unique_possible(
                            "resource-id", old_child, candidates
                        )
                    )
                    is not None
                    and old_child not in info.old.non_overlap
                )
            ):
                result.matched[old_child] = candidate
                logger.debug(
                    f"unique possible matched "
                    f"{digest(old_child)} {digest(candidate)}"
                )
                info.matched.update([old_child, candidate])
            else:
                result.possible[old_child] = candidates
                for candidate in candidates:
                    logger.debug(f"possible {digest(old_child)} {digest(candidate)}")


def match_parents(
    info: MatchInfo, predictor: Callable[[Element, Element], bool]
) -> None:
    """对参与匹配的父节点进行匹配

    满足匹配标准且唯一的组件对会被更新至 `info.matched_parents` 内，用于后续的优化

    Args:
        info (MatchInfo): 匹配信息
        predictor (Callable[[Element, Element], bool]): 匹配标准
    """
    logger.debug("start match parents")
    matched_parents: set[Element] = set()
    for old_parent in (n for n in info.old.parents if n not in matched_parents):
        candidates: list[Element] = []
        for new_parent in (n for n in info.new.parents if n not in matched_parents):
            if predictor(old_parent, new_parent):
                candidates.append(new_parent)

        if len(candidates) == 1:
            candidate = candidates[0]
            logger.debug(f"parents matched {digest(old_parent)} {digest(candidate)}")
            info.matched_parents[old_parent] = candidate
            matched_parents.update([old_parent, candidate])


def optimize_match(
    info: MatchInfo, result: Result, predictor: Callable[[Element, Element], bool]
) -> None:
    """根据父节点匹配的结果进行优化匹配

    在属于一对匹配父节点的子节点集合中两两进行匹配

    Args:
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
        predictor (Callable[[Element, Element], bool]): 匹配标准
    """
    logger.debug("start optimize match")
    for old_parent, new_parent in info.matched_parents.items():
        old_children = [n for n in old_parent.iter("node") if n in info.old.children]
        new_children = [n for n in new_parent.iter("node") if n in info.new.children]

        for old_child in (n for n in old_children if n not in info.matched):
            candidates: list[Element] = []
            for new_child in (n for n in new_children if n not in info.matched):
                if predictor(old_child, new_child):
                    candidates.append(new_child)

            if len(candidates) == 1:
                candidate = candidates[0]
                logger.debug(
                    f"optimize matched {digest(old_child)} {digest(candidate)}"
                )
                result.matched[old_child] = candidate
                info.matched.update([old_child, candidate])


def unique_match(info: MatchInfo, result: Result) -> None:
    logger.debug("start unique match")
    for old_child in (n for n in info.old.unique_children if n not in info.matched):
        candidates: list[Element] = []
        for new_child in (n for n in info.new.unique_children if n not in info.matched):
            if attr_equal(old_child, new_child, "class") and old_child.get(
                "class", ""
            ) in {"android.widget.EditText"}:
                candidates.append(new_child)

        if len(candidates) == 1:
            candidate = candidates[0]
            result.matched[old_child] = candidate
            logger.debug(f"unique matched {digest(old_child)} {digest(candidate)}")
            info.matched.update([old_child, candidate])


def sift_match(info: MatchInfo, result: Result) -> None:
    logger.debug("start sift match")
    update: bool = True
    exclude_set = {
        "android.widget.CheckBox",
        "android.widget.EditText",
        "android.widget.Switch",
    }
    while update:
        update = False
        for old_child in (
            n
            for n in info.old.children
            if n not in info.matched
            and n.get("text", "") == ""
            and n.get("class") not in exclude_set
        ):
            old_points = [
                point
                for point in info.matched_points.keys()
                if is_in_bound(point, old_child)
            ]
            if len(old_points) < 1:
                continue
            old_matches = [info.matched_points[point] for point in old_points]
            candidates: list[Element] = list()
            for new_child in (
                n
                for n in info.new.children
                if n not in info.matched and n.get("text", "") == ""
                # and n.get("class", "") == old_child.get("class", "")
                and n.get("class") not in exclude_set
            ):
                new_match_num = len(
                    [point for point in old_matches if is_in_bound(point, new_child)]
                )
                if (new_match_num / len(old_points)) >= 0.6:
                    candidates.append(new_child)

            if len(candidates) == 1:
                update = True
                candidate = candidates[0]
                logger.debug(f"sift matched {digest(old_child)} {digest(candidate)}")
                result.matched[old_child] = candidate
                info.matched.update([old_child, candidate])


def set_not_match(info: MatchInfo, result: Result) -> None:
    """在匹配结果中设置未匹配的组件

    Args:
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
    """
    new_possible: set[Element] = reduce(
        lambda x, y: x | y, result.possible.values(), set()
    )
    result.old_not_matched = {
        x
        for x in info.old.children
        if x not in result.matched and x not in result.possible
    }
    result.new_not_matched = {
        x
        for x in info.new.children
        if x not in result.matched.values() and x not in new_possible
    }


def set_match_score(result: Result) -> None:
    """设置匹配分数，并根据分数设置是否匹配成功

    如果匹配分数大于等于阈值，认为两个界面匹配

    Args:
        info (MatchInfo): 匹配信息
        result (Result): 匹配结果
    """
    matched_num = len(result.matched)
    possible_num = len(result.possible)
    not_match = len(result.old_not_matched)
    total = matched_num + possible_num + not_match
    result.score = ((matched_num + possible_num) / total) if total != 0 else 0
    result.is_match = result.score >= threshold


def match_layout(old: Layout, new: Layout) -> Result:
    """对布局进行匹配，返回匹配的结果

    Args:
        old (Layout): 旧版本布局
        new (Layout): 新版本布局

    Returns:
        Result: 匹配结果
    """
    result = Result()
    info = MatchInfo(old, new)

    match_sure(info, result, lambda x, y: is_match(x, y))  # 根据属性确定匹配，优先级最高
    match_sure(info, result, lambda x, y: is_like(x, y))  # 根据属性模糊匹配

    sift_match(info, result)
    match_parents(info, lambda x, y: is_match(x, y, strict=False))
    optimize_match(info, result, lambda x, y: is_like(x, y, strict=False))
    unique_match(info, result)
    # draw_matches(info.old.png, info.new.png, info.matched_points)
    # 至此确定匹配结束

    match_possible(info, result, lambda x, y: is_match(x, y, strict=False))

    set_not_match(info, result)
    set_match_score(result)

    return result
