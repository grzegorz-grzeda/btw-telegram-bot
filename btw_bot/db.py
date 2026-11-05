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
    id: int
    text: str


class TodoStore:
    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)

    def add(self, chat_id: int, text: str) -> int:
        with self._conn:
            cur = self._conn.execute(
                "INSERT INTO items (chat_id, text) VALUES (?, ?)", (chat_id, text)
            )
        return cur.lastrowid

    def open_items(self, chat_id: int) -> list[Item]:
        """Not-done items in the order they were added."""
        rows = self._conn.execute(
            "SELECT id, text FROM items WHERE chat_id = ? AND done = 0 ORDER BY id",
            (chat_id,),
        )
        return [Item(id=row[0], text=row[1]) for row in rows]

    def mark_done(self, item_ids: list[int]) -> None:
        with self._conn:
            self._conn.executemany(
                "UPDATE items SET done = 1 WHERE id = ?", [(i,) for i in item_ids]
            )

    def close(self) -> None:
        self._conn.close()
