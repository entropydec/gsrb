from xml.etree.ElementTree import Element, SubElement

from gsrb.common.criterion import Criterion
from gsrb.common.locator import Locator

root = Element("hierarchy")
SubElement(root, "node", {"text": "Documents"})


def test_find_in_tree() -> None:
    locator = Locator({Criterion.TEXT: "Documents"})
    assert locator.find_in_layout(root) is not None


def test_get_param() -> None:
    locator = Locator({Criterion.TEXT: "Documents"})
    assert locator.to_kwargs() == {"text": "Documents"}


def test_convert() -> None:
    locator = Locator({Criterion.TEXT: "Documents"}, 3)
    assert locator == Locator.from_json(locator.to_json())


def test_exception() -> None:
    locator = Locator.from_json('{"criteria": {"TEXT": "Documents", "NAME": "bla"}}')
    assert locator.to_dict() == {"criteria": {"TEXT": "Documents"}}
