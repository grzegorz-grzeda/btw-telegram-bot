# 09: Bot heartbeat

**What to build:** When `BTW_HEARTBEAT_URL` is set, the bot pings it after a successful poll, at most every 5 minutes, so an outside dead man's switch notices when the bot stops polling. The README explains setting up the check. [Spec](../specs/health-checks.md) user stories 1, 2, 4, 5, 6.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] `.env.example` documents the optional `BTW_HEARTBEAT_URL`; empty means no pings.
- [ ] A heartbeat unit with an injectable clock and ping function pings on the first beat, skips beats within 5 minutes of the last ping, and pings again after that.
- [ ] A ping error (timeout, DNS, HTTP error) is logged as a warning and never raised.
- [ ] The polling loop beats after each successful `getUpdates` and never after a failed one.
- [ ] Tests cover the unit with a fake clock and a recording ping function, including a ping that raises.
- [ ] The README has a "Monitoring" section: create a healthchecks.io check (5-minute period, 10-minute grace), put its URL in `.env`, add the Telegram integration, rebuild.
- [ ] Verified by hand: the check turns green with the bot running and alerts after `docker compose stop`.
