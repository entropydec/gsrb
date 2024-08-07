from xml.etree.ElementTree import Element, SubElement

from gsrb.match.preprocess import denote_bounds, denote_index, remove_node


def test_remove_node() -> None:
    root = Element("hierarchy")
    SubElement(root, "node", {"package": "a"})
    SubElement(root, "node", {"package": "b"})
    SubElement(root, "node", {"package": "a"})

    remove_node(root, lambda x: x.get("package") == "a")

    assert len(root) == 1


def test_denote_index() -> None:
    root = Element("hierarchy")
    a = SubElement(root, "node", {"text": "a"})
    b = SubElement(root, "node", {"text": "b"})
    SubElement(root, "node", {"text": "a"})
    SubElement(a, "node", {"text": "b"})

    denote_index(root)

    assert a.get("text-index") == "0"
    assert b.get("text-index") == "1"


def test_denote_bounds() -> None:
    root = Element("node", {"bounds": "[100,100][200,250]"})
    denote_bounds(root)

    assert root.get("x") == "100"
    assert root.get("w") == "100"
