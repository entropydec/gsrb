from xml.etree.ElementTree import Element

import pytest

from gsrb.common.criterion import Criterion

node = Element("node")
node.attrib.update(
    {
        "resource-id": "com.veniosg.dir:id/primary_info",
        "content-desc": "Documents",
        "text": "Documents",
        "class": "android.widget.TextView",
    }
)


@pytest.mark.parametrize(
    ["criterion", "identifier"],
    [
        (Criterion.ID, "com.veniosg.dir:id/primary_info"),
        (Criterion.DESC, "Documents"),
        (Criterion.TEXT, "Documents"),
        (Criterion.CLASS, "android.widget.TextView"),
    ],
)
def test_match(criterion: Criterion, identifier: str) -> None:
    assert criterion(node, identifier)


@pytest.mark.parametrize(
    ["criterion", "identifier", "result"],
    [
        (
            Criterion.ID,
            "com.veniosg.dir:id/primary_info",
            {"resourceId": "com.veniosg.dir:id/primary_info"},
        ),
        (Criterion.DESC, "Documents", {"description": "Documents"}),
        (Criterion.TEXT, "Documents", {"text": "Documents"}),
        (
            Criterion.CLASS,
            "android.widget.TextView",
            {"className": "android.widget.TextView"},
        ),
    ],
)
def test_to_dict(criterion: Criterion, identifier: str, result: dict[str, str]) -> None:
    assert {criterion.u2_name: identifier} == result


@pytest.mark.parametrize(
    ["d", "result"],
    [
        (
            {
                "resourceId": "com.veniosg.dir:id/primary_info",
                "text": "Documents",
                "description": "Documents",
                "className": "android.widget.Text.View",
                "instance": 1,
                "scrollable": True,
            },
            {
                Criterion.ID: "com.veniosg.dir:id/primary_info",
                Criterion.TEXT: "Documents",
                Criterion.DESC: "Documents",
                Criterion.CLASS: "android.widget.Text.View",
            },
        )
    ],
)
def test_from_dict(
    d: dict[str, str | bool | int], result: dict[Criterion, str]
) -> None:
    assert {
        Criterion.from_parameter(k): v
        for k, v in d.items()
        if Criterion.from_parameter(k) is not None
    } == result
