# 10: Backup check

**What to build:** The README's nightly cron line pings a second check only when the backup and the rclone sync both succeeded, and explains setting that check up. No code changes. [Spec](../specs/health-checks.md) user stories 3, 6.

**Blocked by:** none

**Status:** ready-for-human

- [x] The cron line in the README ends with `&& curl -fsS -m 10 --retry 3 <backup check URL> > /dev/null`, after `rclone sync`.
- [x] The README notes the backup check's settings (1-day period and 1-hour grace, or a cron schedule matching the crontab line) and that `curl` must be installed on the host.
- [x] The "Monitoring" section (added by ticket 09, or created here if it's not there yet) lists both checks and what silence on each means.
- [ ] Verified by hand: running the cron line once turns the check green.

## Comments

Implemented in e32a3b8. Only the hand check is left: it needs a real healthchecks.io check. Follow the README's "Backup ran" steps, then run the cron line's command once in a shell and watch the check turn green. Once it does, tick the last box, set `Status: resolved` and rename the file to `done-10-backup-check.md`.
