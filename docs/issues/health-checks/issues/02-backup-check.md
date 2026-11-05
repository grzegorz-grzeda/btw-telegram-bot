# 02: Backup check

**What to build:** The README's nightly cron line pings a second check only when the backup and the rclone sync both succeeded, and explains setting that check up. No code changes. Spec user stories 3, 6.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] The cron line in the README ends with `&& curl -fsS -m 10 --retry 3 <backup check URL> > /dev/null`, after `rclone sync`.
- [ ] The README notes the backup check's settings (1-day period and 1-hour grace, or a cron schedule matching the crontab line) and that `curl` must be installed on the host.
- [ ] The "Monitoring" section (added by ticket 01, or created here if it's not there yet) lists both checks and what silence on each means.
- [ ] Verified by hand: running the cron line once turns the check green.
