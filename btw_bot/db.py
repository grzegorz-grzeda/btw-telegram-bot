"""SQLite storage for to-do items, one list per Telegram chat."""

import sqlite3
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY,
    chat_id    INTEGER NOT NULL,
    text       TEXT    NOT NULL,
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_items_chat_done ON items (chat_id, done);
"""


@dataclass(frozen=True)
class Item:
    id: str  # opaque outside the store
    text: str


class TodoStore:
    """Item IDs are opaque strings to callers; only the store knows they're SQLite rowids."""

    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)

    def add(self, chat_id: int, text: str) -> str:
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO items (chat_id, text) VALUES (?, ?)", (chat_id, text)
            )
        return str(cur.lastrowid)

    def open_items(self, chat_id: int) -> list[Item]:
        """Not-done items in the order they were added."""
        rows = self._conn.execute(
            "SELECT id, text FROM items WHERE chat_id = ? AND done = 0 ORDER BY id",
            (chat_id,),
        )
        return [Item(id=str(row[0]), text=row[1]) for row in rows]

    def mark_done(self, item_ids: list[str]) -> None:
        with self._conn:
            self._conn.executemany(
                "UPDATE items SET done = 1 WHERE id = ?", [(_rowid(i),) for i in item_ids]
            )

    def close(self) -> None:
        self._conn.close()


def _rowid(item_id: str) -> int:
    """Turn an opaque item ID back into a rowid. A malformed ID matches no row."""
    try:
        return int(item_id)
    except ValueError:
        return -1
