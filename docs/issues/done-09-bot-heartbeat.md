# 09: Bot heartbeat

**What to build:** When `BTW_HEARTBEAT_URL` is set, the bot pings it after a successful poll, at most every 5 minutes, so an outside dead man's switch notices when the bot stops polling. The README explains setting up the check. [Spec](../specs/health-checks.md) user stories 1, 2, 4, 5, 6.

**Blocked by:** none

**Status:** resolved

- [x] `.env.example` documents the optional `BTW_HEARTBEAT_URL`; empty means no pings.
- [x] A heartbeat unit with an injectable clock and ping function pings on the first beat, skips beats within 5 minutes of the last ping, and pings again after that.
- [x] A ping error (timeout, DNS, HTTP error) is logged as a warning and never raised.
- [x] The polling loop beats after each successful `getUpdates` and never after a failed one.
- [x] Tests cover the unit with a fake clock and a recording ping function, including a ping that raises.
- [x] The README has a "Monitoring" section: create a healthchecks.io check (5-minute period, 10-minute grace), put its URL in `.env`, add the Telegram integration, rebuild.
- [x] Verified by hand: the check turns green with the bot running and alerts after `docker compose stop`.

## Comments

Implemented in 18de413. Only the hand check is left: it needs a real healthchecks.io check. Follow the README's Monitoring section, then `docker compose stop` and wait for the alert. Once it arrives, tick the last box, set `Status: resolved` and rename the file to `done-09-bot-heartbeat.md`.

Resolved at the user's request: the hand check against healthchecks.io was done by the user.
