"""最小长期记忆 Store（纯标准库，可本地跑）。

命名空间：memory:user:{user_id} — 勿与 RAG kb:tenant:* 混用。
"""

from __future__ import annotations

import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Literal

MemoryType = Literal["pref", "fact", "episode"]


@dataclass
class MemoryItem:
    id: str
    user_id: str
    type: MemoryType
    text: str
    source: str
    confidence: float
    created_at: float = field(default_factory=time.time)
    ttl_sec: float | None = None  # None = 不过期

    def expired(self, now: float | None = None) -> bool:
        if self.ttl_sec is None:
            return False
        return (now or time.time()) > self.created_at + self.ttl_sec


def should_write_long_term(item: dict) -> tuple[bool, str]:
    if item.get("source") in {"rag", "fetch_url", "user_raw"}:
        return False, "untrusted_source"
    if float(item.get("confidence", 0)) < 0.8:
        return False, "low_confidence"
    if item.get("type") not in {"pref", "fact"}:
        return False, "type_not_allowed"
    text = str(item.get("text", ""))
    if any(x in text.lower() for x in ("sk-", "password=", "忽略之前")):
        return False, "sensitive_or_injection"
    return True, "ok"


class MemoryStore:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path
        self._items: dict[str, MemoryItem] = {}
        if path and path.exists():
            self._load()

    def _load(self) -> None:
        assert self.path is not None
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        for row in raw:
            item = MemoryItem(**row)
            self._items[item.id] = item

    def save(self) -> None:
        if not self.path:
            return
        self.path.parent.mkdir(parents=True, exist_ok=True)
        data = [asdict(i) for i in self._items.values()]
        self.path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def add(self, *, user_id: str, type: MemoryType, text: str, source: str, confidence: float, ttl_sec: float | None = 86400 * 30) -> tuple[MemoryItem | None, str]:
        candidate = {
            "type": type,
            "text": text,
            "source": source,
            "confidence": confidence,
        }
        ok, reason = should_write_long_term(candidate)
        if not ok:
            return None, reason
        item = MemoryItem(
            id=str(uuid.uuid4()),
            user_id=user_id,
            type=type,
            text=text,
            source=source,
            confidence=confidence,
            ttl_sec=ttl_sec,
        )
        self._items[item.id] = item
        self.save()
        return item, "ok"

    def revoke(self, memory_id: str) -> bool:
        if memory_id in self._items:
            del self._items[memory_id]
            self.save()
            return True
        return False

    def retrieve(self, user_id: str, *, limit: int = 5, memory_type: MemoryType | None = None) -> list[MemoryItem]:
        now = time.time()
        rows = [
            i
            for i in self._items.values()
            if i.user_id == user_id and not i.expired(now) and (memory_type is None or i.type == memory_type)
        ]
        rows.sort(key=lambda i: i.created_at, reverse=True)
        return rows[:limit]

    def format_for_prompt(self, items: list[MemoryItem]) -> str:
        if not items:
            return ""
        lines = [f"- [{i.type}] {i.text}" for i in items]
        return "相关长期记忆：\n" + "\n".join(lines)
