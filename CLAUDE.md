# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**btw-telegram-bot**: a "by the way..." Telegram bot that keeps a to-do list per chat. It's meant to stay small and simple, and runs as a proof of concept on a Raspberry Pi. See `README.md` for user-facing commands and setup.

## Commands

```bash
python3 -m btw_bot                                    # run the bot (reads .env from the cwd)
python3 -m unittest                                   # all tests
python3 -m unittest tests.test_handlers.HandleTest.test_add_command   # one test
```

There is no build step, linter config or virtualenv: the project uses only the standard library.

## Architecture

- `btw_bot/handlers.py`: `handle(store, chat_id, text) -> str`. All command logic, with no network I/O, so tests call it directly against an in-memory `TodoStore(":memory:")`.
- `btw_bot/db.py`: `TodoStore`, a thin wrapper over stdlib `sqlite3`. The schema is created on startup (`CREATE TABLE IF NOT EXISTS`), with no migrations. Completed items are flagged `done = 1`, not deleted.
- `btw_bot/telegram.py`: a minimal Bot API client over `urllib` (`getUpdates` long polling, `sendMessage` with splitting past 4096 chars). Error messages deliberately leave out the request URL because it contains the token.
- `btw_bot/__main__.py`: config (env vars plus a tiny `.env` loader where already-set variables win), the user allow-list check and the polling loop. Network errors back off and retry; an exception while handling one update is logged and skipped, so the loop never dies.

Item numbers shown to users are positions in the current open list (not DB ids), so they shift after `/done`. `/done` resolves every number against the list as it was before any are marked.

Config: `TELEGRAM_BOT_TOKEN` (required), `BTW_ALLOWED_USERS` (comma-separated user IDs; empty allows everyone), `BTW_DB_PATH` (default `btw.db`). See `.env.example`.

## Constraints

- **No dependencies.** Keep it stdlib-only unless the user agrees otherwise. This is what keeps setup on the Pi to a `git clone`.
- **Python 3.10 compatibility.** The dev machine runs 3.14, but the Pi's system Python may be older (Raspberry Pi OS Bookworm ships 3.11). The code uses `X | None` annotations, so 3.10 is the floor.
- **Long polling, not webhooks.** The Pi has no public HTTPS endpoint.
- **Deployment** is the systemd unit in `deploy/btw-bot.service`, which runs `/usr/bin/python3 -m btw_bot` from the repo checkout.
