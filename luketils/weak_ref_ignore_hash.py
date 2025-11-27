import weakref
from dataclasses import dataclass
from typing import Generic, TypeVar

K = TypeVar("K")
V = TypeVar("V")


@dataclass(frozen=True)
class WeakRefValue(Generic[V]):
    ref: weakref.ReferenceType
    value: V


class WeakKeyDictionaryThatIgnoresHash(Generic[K, V]):
    def __init__(self) -> None:
        self._data: dict[int, WeakRefValue] = {}

    def __setitem__(self, obj: K, value: V) -> None:
        obj_id = id(obj)

        if obj_id in self._data:
            raise ValueError(
                f"{obj_id} for object {obj} was already inside of the "
                "cache, but it was set again."
            )

        def remove(_):
            self._data.pop(obj_id, None)

        self._data[obj_id] = WeakRefValue(weakref.ref(obj, remove), value)

    def __getitem__(self, obj: K) -> V:
        obj_id = id(obj)
        entry = self._data[obj_id]
        if entry.ref() is None:
            raise KeyError(obj)
        return entry.value

    def __contains__(self, obj: K) -> bool:
        obj_id = id(obj)
        entry = self._data.get(obj_id)
        return entry is not None and entry.ref() is not None

    def pop(self, obj: K, default: V | None = None) -> V:
        obj_id = id(obj)
        entry = self._data.pop(obj_id, None)
        if entry is None or entry.ref() is None:
            if default is None:
                raise KeyError(obj)
            return default
        return entry.value
