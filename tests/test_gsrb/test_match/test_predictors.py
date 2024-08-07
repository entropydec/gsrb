from xml.etree.ElementTree import Element

import pytest

from gsrb.match.predictors import attr_equal, attr_like

node1 = Element("node", {"resource-id": "android:id/id1", "text": "text1"})
node2 = Element("node", {"resource-id": "android:id/id1", "text": "text2"})
node3 = Element("node", {"resource-id": "android:id/bx1", "text": "text3"})


@pytest.mark.parametrize(
    ["a", "b", "attr", "result"],
    [(node1, node2, "resource-id", True), (node1, node2, "text", False)],
)
def test_attr_equal(a: Element, b: Element, attr: str, result: bool) -> None:
    assert attr_equal(a, b, attr) == result


@pytest.mark.parametrize(
    ["a", "b", "attr", "result"],
    [(node1, node2, "text", True), (node1, node3, "resource-id", False)],
)
def test_attr_like(a: Element, b: Element, attr: str, result: bool) -> None:
    assert attr_like(a, b, attr) == result
