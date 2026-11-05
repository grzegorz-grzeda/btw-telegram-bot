"""Snapshot the database while the bot runs: `python -m btw_bot.backup`."""

import os
import re
import sqlite3
import sys
from datetime import date, datetime, timedelta, timezone

from .__main__ import load_dotenv

KEEP_DAYS = 14
SNAPSHOT_NAME = re.compile(r"btw-(\d{4}-\d{2}-\d{2})\.db")


def snapshot_name(day: date) -> str:
    """The file name of a day's snapshot; SNAPSHOT_NAME must match it."""
    return f"btw-{day.isoformat()}.db"


def backup(db_path: str, backup_dir: str, today: date) -> str:
    """Write today's snapshot of the database into backup_dir, replacing any from earlier
    today, then delete snapshots older than KEEP_DAYS by the date in their name.
    Return the snapshot's path."""
    os.makedirs(backup_dir, exist_ok=True)
    snapshot = os.path.join(backup_dir, snapshot_name(today))
    # Write beside it and rename, so a failed re-run leaves the day's earlier snapshot intact.
    partial = snapshot + ".partial"
    # SQLite's online backup API copies a consistent state while the bot keeps writing.
    source = sqlite3.connect(db_path)
    target = sqlite3.connect(partial)
    try:
        source.backup(target)
    finally:
        target.close()
        source.close()
    os.replace(partial, snapshot)
    _prune(backup_dir, today - timedelta(days=KEEP_DAYS))
    return snapshot


def _prune(backup_dir: str, oldest_kept: date) -> None:
    """Delete snapshots dated before oldest_kept. Other files are left alone."""
    for name in os.listdir(backup_dir):
        match = SNAPSHOT_NAME.fullmatch(name)
        if not match:
            continue
        try:
            taken = date.fromisoformat(match[1])
        except ValueError:
            continue
        if taken < oldest_kept:
            os.remove(os.path.join(backup_dir, name))


def main() -> int:
    """Back up BTW_DB_PATH into `backups` next to it, dated today in UTC."""
    load_dotenv()
    db_path = os.environ.get("BTW_DB_PATH", "btw.db")
    # Connecting would create an empty database; a backup of nothing hides the mistake.
    if not os.path.isfile(db_path):
        print(f"No database at {db_path} (set BTW_DB_PATH).", file=sys.stderr)
        return 1
    backup_dir = os.path.join(os.path.dirname(db_path), "backups")
    today = datetime.now(timezone.utc).date()
    print(f"Wrote {backup(db_path, backup_dir, today)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
