"""SQLite storage for to-do items: the household's one List."""

import sqlite3
from dataclasses import dataclass, replace

SCHEMA = """
CREATE TABLE IF NOT EXISTS items (
    id         INTEGER PRIMARY KEY,
    chat_id    INTEGER NOT NULL, -- unused since the List became shared; new rows write 0
    text       TEXT    NOT NULL,
    type       TEXT,   -- 'food', 'stuff', 'do', or NULL for Unsorted
    batch      INTEGER, -- items added by one message share it; NULL before batches existed
    done       INTEGER NOT NULL DEFAULT 0, -- 0 open, else the number of the tick that closed it
    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_items_chat_done ON items (chat_id, done);
-- Numbers ticks. AUTOINCREMENT never reuses a number, so only the latest row is kept.
CREATE TABLE IF NOT EXISTS ticks (id INTEGER PRIMARY KEY AUTOINCREMENT);
"""


@dataclass(frozen=True)
class Item:
    id: str  # opaque outside the store
    text: str
    type: str | None = None  # None means Unsorted
    done: bool = False


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

    def add_batch(self, items: list[tuple[str, str | None]]) -> str:
        """Add (text, type) items as one batch, in order; return the batch key (opaque)."""
        with self._conn:
            ids = [
                self._conn.execute(
                    "INSERT INTO items (chat_id, text, type) VALUES (0, ?, ?)",
                    (text, item_type),
                ).lastrowid
                for text, item_type in items
            ]
            # The first item's rowid is unique, so it serves as the batch key.
            self._conn.executemany(
                "UPDATE items SET batch = ? WHERE id = ?", [(ids[0], i) for i in ids]
            )
        return str(ids[0])

    def type_batch(self, batch: str, item_type: str) -> list[Item]:
        """Give a type to the batch's items that are still Unsorted and not done.
        Return those items, now typed; items sorted or ticked off since are left alone."""
        where = "batch = ? AND type IS NULL AND done = 0"
        params = (_rowid(batch),)
        with self._conn:
            rows = self._conn.execute(
                f"SELECT id, text FROM items WHERE {where} ORDER BY id", params
            ).fetchall()
            self._conn.execute(f"UPDATE items SET type = ? WHERE {where}", (item_type, *params))
        return [Item(id=str(row[0]), text=row[1], type=item_type) for row in rows]

    def open_items(self) -> list[Item]:
        """Not-done items in the order they were added."""
        rows = self._conn.execute("SELECT id, text, type FROM items WHERE done = 0 ORDER BY id")
        return [Item(id=str(row[0]), text=row[1], type=row[2]) for row in rows]

    def get(self, item_id: str) -> Item | None:
        """The item with this ID, done or not; None if there's none."""
        row = self._conn.execute(
            "SELECT id, text, type, done FROM items WHERE id = ?", (_rowid(item_id),)
        ).fetchone()
        if row is None:
            return None
        return Item(id=str(row[0]), text=row[1], type=row[2], done=bool(row[3]))

    def set_type(self, item_id: str, item_type: str | None) -> None:
        with self._conn:
            self._conn.execute(
                "UPDATE items SET type = ? WHERE id = ?", (item_type, _rowid(item_id))
            )

    def mark_done(self, item_ids: list[str]) -> str:
        """Mark items done; return a key for this tick (opaque), which undo_done needs.
        Each tick gets a new key, so an Undo from an earlier tick can't reopen an item."""
        with self._conn:
            self._conn.execute("DELETE FROM ticks")
            tick = self._conn.execute("INSERT INTO ticks DEFAULT VALUES").lastrowid
            self._conn.executemany(
                "UPDATE items SET done = ? WHERE id = ?", [(tick, _rowid(i)) for i in item_ids]
            )
        return str(tick)

    def undo_done(self, item_id: str, tick: str) -> Item | None:
        """Reopen the item if it's still done from that tick; return it, else None.
        The item keeps the type it had."""
        item = self.get(item_id)
        if item is None:
            return None
        with self._conn:
            reopened = self._conn.execute(
                "UPDATE items SET done = 0 WHERE id = ? AND done = ? AND done != 0",
                (_rowid(item.id), _rowid(tick)),
            ).rowcount
        return replace(item, done=False) if reopened else None

    def close(self) -> None:
        self._conn.close()


def _rowid(item_id: str) -> int:
    """Turn an opaque item ID back into a rowid. A malformed ID matches no row."""
    try:
        return int(item_id)
    except ValueError:
        return -1
