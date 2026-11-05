"""SQLite storage for to-do items, one list per Telegram chat."""

import sqlite3
from dataclasses import dataclass

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY,
    chat_id    INTEGER NOT NULL,
    text       TEXT    NOT NULL,
    type       TEXT,   -- 'food', 'stuff', 'do', or NULL for Unsorted
    batch      INTEGER, -- items added by one message share it; NULL before batches existed
    done       INTEGER NOT NULL DEFAULT 0,
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_items_chat_done ON items (chat_id, done);
"""


@dataclass(frozen=True)
class Item:
    id: str  # opaque outside the store
    text: str
    type: str | None = None  # None means Unsorted


class TodoStore:
    """Item IDs are opaque strings to callers; only the store knows they're SQLite rowids."""

    def __init__(self, path: str):
        self._conn = sqlite3.connect(path)
        self._conn.executescript(SCHEMA)
        # Older databases lack later columns: items without a type are Unsorted,
        # items without a batch belong to no prompt.
        columns = {row[1] for row in self._conn.execute("PRAGMA table_info(items)")}
        with self._conn:
            for column, sql_type in (("type", "TEXT"), ("batch", "INTEGER")):
                if column not in columns:
                    self._conn.execute(f"ALTER TABLE items ADD COLUMN {column} {sql_type}")

    def add_batch(self, chat_id: int, items: list[tuple[str, str | None]]) -> str:
        """Add (text, type) items as one batch, in order; return the batch key (opaque)."""
        with self._conn:
            ids = [
                self._conn.execute(
                    "INSERT INTO items (chat_id, text, type) VALUES (?, ?, ?)",
                    (chat_id, text, item_type),
                ).lastrowid
                for text, item_type in items
            ]
            # The first item's rowid is unique, so it serves as the batch key.
            self._conn.executemany(
                "UPDATE items SET batch = ? WHERE id = ?", [(ids[0], i) for i in ids]
            )
        return str(ids[0])

    def type_batch(self, chat_id: int, batch: str, item_type: str) -> list[Item]:
        """Give a type to the batch's items that are still Unsorted and not done.
        Return those items, now typed; items sorted or ticked off since are left alone."""
        where = "chat_id = ? AND batch = ? AND type IS NULL AND done = 0"
        params = (chat_id, _rowid(batch))
        with self._conn:
            rows = self._conn.execute(
                f"SELECT id, text FROM items WHERE {where} ORDER BY id", params
            ).fetchall()
            self._conn.execute(f"UPDATE items SET type = ? WHERE {where}", (item_type, *params))
        return [Item(id=str(row[0]), text=row[1], type=item_type) for row in rows]

    def open_items(self, chat_id: int) -> list[Item]:
        """Not-done items in the order they were added."""
        rows = self._conn.execute(
            "SELECT id, text, type FROM items WHERE chat_id = ? AND done = 0 ORDER BY id",
            (chat_id,),
        )
        return [Item(id=str(row[0]), text=row[1], type=row[2]) for row in rows]

    def set_type(self, item_id: str, item_type: str | None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE items SET type = ? WHERE id = ?", (item_type, _rowid(item_id))
            )

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
