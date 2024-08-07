import json
from collections.abc import Mapping
from typing import Protocol, Self, TypeVar


class Jsonable(Protocol):
    def to_dict(self) -> dict[str, object]:
        ...

    @classmethod
    def from_dict(cls, d: Mapping[str, object]) -> Self:
        ...


T = TypeVar("T", bound=Jsonable)


class JsonMixin:
    def to_json(self: Jsonable) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False)

    @classmethod
    def from_json(cls: type[T], s: str) -> T:
        return cls.from_dict(json.loads(s))
