from uiautomator2 import UiObject

from gsrb.common.action import Action
from gsrb.common.event import Event
from gsrb.record.manager import RecordManager


class MyUiObject(UiObject):
    manager: RecordManager | None = None

    def click(
        self, timeout: float | None = None, offset: tuple[float, float] | None = None
    ) -> None:
        if self.manager:
            event = Event(Action.CLICK, self.__dict__.get("locator", None))
            self.manager.before()
            super().click(timeout, offset)
            self.manager.after(event)

    def long_click(self, duration: float = 0.5, timeout: float | None = None) -> object:
        if self.manager:
            event = Event(Action.LONG_CLICK, self.__dict__.get("locator", None))
            self.manager.before()
            result = super().long_click(duration, timeout)
            self.manager.after(event)
            return result
        return super().long_click(duration, timeout)

    def set_text(self, text: str, timeout: float | None = None) -> object:
        if self.manager:
            event = Event(
                Action.SET_TEXT, self.__dict__.get("locator", None), {"text": text}
            )
            self.manager.before()
            result = super().set_text(text, timeout)
            self.manager.after(event)
            return result
        return super().set_text(text, timeout)

    def assert_exists(self) -> None:
        if self.manager:
            event = Event(Action.EXIST, self.__dict__.get("locator", None))
            self.manager.before()
            self.manager.after(event)

    def assert_not_exists(self) -> None:
        if self.manager:
            event = Event(Action.NOT_EXIST, self.__dict__.get("locator", None))
            self.manager.before()
            self.manager.after(event)

    def assert_equals(self, attr: str, oracle: str) -> None:
        if self.manager:
            event = Event(
                Action.EQUAL,
                self.__dict__.get("locator", None),
                {"attr": attr, "oracle": oracle},
            )
            self.manager.before()
            self.manager.after(event)

    def assert_not_equals(self, attr: str, oracle: str) -> None:
        if self.manager:
            event = Event(
                Action.NOT_EQUAL,
                self.__dict__.get("locator", None),
                {"attr": attr, "oracle": oracle},
            )
            self.manager.before()
            self.manager.after(event)
