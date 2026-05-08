import asyncio
from collections import defaultdict


class ConversationHistory:
    def __init__(self, max_pairs: int = 20) -> None:
        self._max_messages = max_pairs * 2
        self._history: dict[str, list[dict]] = defaultdict(list)
        self._lock = asyncio.Lock()

    async def get(self, key: str) -> list[dict]:
        async with self._lock:
            return list(self._history[key])

    async def append(self, key: str, role: str, content: str) -> None:
        async with self._lock:
            self._history[key].append({"role": role, "content": content})
            if len(self._history[key]) > self._max_messages:
                self._history[key] = self._history[key][-self._max_messages:]

    async def clear(self, key: str) -> None:
        async with self._lock:
            self._history.pop(key, None)
