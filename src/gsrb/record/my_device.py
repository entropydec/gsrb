from typing import Any

from uiautomator2 import Device, UiObject

from gsrb.common.action import Action
from gsrb.common.criterion import Criterion
from gsrb.common.event import Event
from gsrb.common.locator import Locator
from gsrb.record.manager import RecordManager
from gsrb.record.my_uiobject import MyUiObject


class MyDevice(Device):
    manager: RecordManager | None = None

    def press(self, key: int | str, meta: int | None = None) -> Any:
        event: Event | None = None
        match key:
            case "back":
                event = Event(Action.BACK)
            case _:
                pass
        if event is not None and self.manager is not None:
            self.manager.before()
            result = super().press(key, meta)
            self.manager.after(event)
            return result

        return super().press(key, meta)

    def swipe(self, fx: int, fy: int, tx: int, ty: int) -> Any:
        event = Event(Action.SWIPE, None, {"fx": fx, "fy": fy, "tx": tx, "ty": ty})
        if self.manager:
            self.manager.before()
            result = super().swipe(fx, fy, tx, ty)
            self.manager.after(event)
            return result

        return super().swipe(fx, fy, tx, ty)

    def __call__(self, **kwargs: object) -> UiObject:
        obj = super().__call__(**kwargs)
        obj.__class__ = MyUiObject
        criteria: dict[Criterion, str] = dict()
        for k, v in kwargs.items():
            if (c := Criterion.from_parameter(k)) is not None and isinstance(v, str):
                criteria[c] = v
        instance = kwargs.get("instance", 0)
        instance = 0 if not isinstance(instance, int) else instance
        locator = Locator(criteria, instance)
        obj.__setattr__("locator", locator)
        return obj
