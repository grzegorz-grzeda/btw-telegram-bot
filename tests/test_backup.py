import os
import tempfile
import unittest
from datetime import date

from btw_bot.backup import backup
from btw_bot.db import TodoStore


class BackupTest(unittest.TestCase):
    def setUp(self):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = tmp.name
        self.db_path = os.path.join(self.tmp, "btw.db")
        self.backup_dir = os.path.join(self.tmp, "backups")

    def store(self, path):
        store = TodoStore(path)
        self.addCleanup(store.close)
        return store

    def open_texts(self, path):
        return [item.text for item in self.store(path).open_items()]

    def test_snapshot_opens_with_the_same_items(self):
        live = self.store(self.db_path)
        live.add_batch([("milk", "food"), ("call mum", None)])

        snapshot = backup(self.db_path, self.backup_dir, date(2026, 11, 5))

        self.assertEqual(os.path.basename(snapshot), "btw-2026-11-05.db")
        self.assertEqual(os.path.dirname(snapshot), self.backup_dir)
        self.assertEqual(self.open_texts(snapshot), ["milk", "call mum"])

    def test_rerun_on_the_same_day_replaces_that_days_snapshot(self):
        live = self.store(self.db_path)
        live.add_batch([("milk", "food")])
        backup(self.db_path, self.backup_dir, date(2026, 11, 5))
        live.add_batch([("bread", "food")])

        snapshot = backup(self.db_path, self.backup_dir, date(2026, 11, 5))

        self.assertEqual(os.listdir(self.backup_dir), ["btw-2026-11-05.db"])
        self.assertEqual(self.open_texts(snapshot), ["milk", "bread"])

    def test_snapshots_older_than_14_days_are_deleted(self):
        self.store(self.db_path).add_batch([("milk", "food")])
        os.makedirs(self.backup_dir)
        for name in (
            "btw-2026-10-01.db",  # 35 days old
            "btw-2026-10-21.db",  # 15 days old
            "btw-2026-10-22.db",  # 14 days old
            "btw-2026-11-04.db",  # yesterday
            "notes.txt",  # not a snapshot
        ):
            open(os.path.join(self.backup_dir, name), "w").close()

        backup(self.db_path, self.backup_dir, date(2026, 11, 5))

        self.assertEqual(
            sorted(os.listdir(self.backup_dir)),
            ["btw-2026-10-22.db", "btw-2026-11-04.db", "btw-2026-11-05.db", "notes.txt"],
        )
