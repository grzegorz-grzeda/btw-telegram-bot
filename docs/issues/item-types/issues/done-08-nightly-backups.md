# 08: Nightly backups

**What to build:** A backup command, runnable inside the bot's container, writes a consistent dated snapshot of the database while the bot keeps running. It keeps 14 days of snapshots in a `backups` folder next to the database, which lands in the host's `./data` folder. The README gives the host cron line that runs it nightly and syncs the folder to Google Drive with rclone, and explains how to restore. Spec user stories 52–56.

**Blocked by:** 07 (Docker deployment) — done

**Status:** resolved

- [x] The backup takes the database path, a backup folder (by default `backups` next to the database) and today's date, and writes a snapshot named with that date using SQLite's online backup API.
- [x] Running it twice on the same day replaces that day's snapshot.
- [x] Snapshots older than 14 days, judged by the date in the name, are deleted, and newer ones are kept.
- [x] It runs as a command inside the container through `docker compose exec`, needing nothing outside the standard library.
- [x] Tests use a temporary folder and an injected date. They check that the snapshot opens with the same items, the same-day replacement, and the 14-day pruning.
- [x] The README gives the nightly cron line (backup in the container, then `rclone sync` of the backups folder to `gdrive:btw-backups`) and notes that rclone and its Google Drive credentials stay on the host.
- [x] The README describes restoring: stop the container, copy a snapshot over the database file, start the container again.

## Comments

Ticket 07: inside the container the database is `/data/btw.db` (`BTW_DB_PATH` is set in `compose.yaml`, overriding `.env`), so `backups` next to it is `/data/backups`, which is host `./data/backups` (git-ignored with `/data/`). The container runs as UID 1000, and `docker compose exec bot ...` runs as that user too. `.dockerignore` copies only `btw_bot/` into the image, so the backup module must live there.

Ticket 08: `btw_bot/backup.py` holds `backup(db_path, backup_dir, today)`, which the tests drive, and `main()`, which the cron line runs with `docker compose exec -T bot python -m btw_bot.backup`. Snapshots are `btw-YYYY-MM-DD.db`, dated in UTC. Retention follows the wording "older than 14 days": a snapshot exactly 14 days old is kept, so the folder holds up to 15 files (today plus the 14 days before). Each snapshot is written to a `.partial` file and then renamed, so a failed re-run keeps that day's earlier snapshot. The command refuses to run when the database file is missing; otherwise SQLite would create an empty one, and the following `rclone sync` would wipe the Drive copies. Verified by running the command in the built image against a bind-mounted folder.

Implemented in 7cbcd33.
