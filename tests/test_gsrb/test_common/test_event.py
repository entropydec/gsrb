from pytest_mock import MockerFixture

from gsrb.common.action import Action
from gsrb.common.criterion import Criterion
from gsrb.common.event import Event
from gsrb.common.locator import Locator


def test_convert() -> None:
    locator = Locator({Criterion.TEXT: "Documents"}, 3)
    event = Event(Action.CLICK, locator, {})
    assert event == Event.from_json(event.to_json())


def test_perform(mocker: MockerFixture) -> None:
    locator = Locator({Criterion.TEXT: "Documents"}, 0)
    event = Event(Action.CLICK, locator, {})

    mock_device = mocker.stub("mock_device")
    mock_object = mocker.stub("mock_object")
    mock_click = mocker.stub("mock_click")

    mock_object.__setattr__("click", mock_click)
    mock_device.return_value = [mock_object]
    event.perform(mock_device)
    mock_click.assert_called_once()
    mock_device.assert_called_once_with(text="Documents")
