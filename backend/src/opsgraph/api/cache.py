"""Small in-process TTL stores for the scale-to-zero demo profiles."""

from collections import OrderedDict
from dataclasses import dataclass
from time import monotonic
from typing import Generic, TypeVar

ValueT = TypeVar("ValueT")


@dataclass(frozen=True)
class CacheEntry(Generic[ValueT]):
    expires_at: float
    value: ValueT


class BoundedTtlCache(Generic[ValueT]):
    def __init__(self, *, max_items: int = 100, ttl_seconds: int = 300) -> None:
        self.max_items = max_items
        self.ttl_seconds = ttl_seconds
        self._entries: OrderedDict[str, CacheEntry[ValueT]] = OrderedDict()

    def get(self, key: str) -> ValueT | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        if entry.expires_at < monotonic():
            del self._entries[key]
            return None
        self._entries.move_to_end(key)
        return entry.value

    def set(self, key: str, value: ValueT) -> None:
        if self.ttl_seconds == 0:
            return
        self._entries[key] = CacheEntry(
            expires_at=monotonic() + self.ttl_seconds,
            value=value,
        )
        self._entries.move_to_end(key)
        while len(self._entries) > self.max_items:
            self._entries.popitem(last=False)


class BoundedRunStore(Generic[ValueT]):
    def __init__(self, max_items: int = 100) -> None:
        self.max_items = max_items
        self._entries: OrderedDict[str, ValueT] = OrderedDict()

    def get(self, run_id: str) -> ValueT | None:
        return self._entries.get(run_id)

    def set(self, run_id: str, value: ValueT) -> None:
        self._entries[run_id] = value
        self._entries.move_to_end(run_id)
        while len(self._entries) > self.max_items:
            self._entries.popitem(last=False)
