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

There is no build step, linter config or virtualenv: the project uses only the standard library. CI (`.github/workflows/test.yml`) runs the tests on Python 3.10 and 3.14.

## Architecture

`btw_bot/handlers.py` turns one Telegram update into a list of actions (`btw_bot/actions.py`); `btw_bot/__main__.py` polls and executes them; `btw_bot/db.py` stores items; `btw_bot/telegram.py` is the Bot API client. Conventions the code won't tell you:

- The handler does no network I/O. It's the test seam: tests feed fake updates and assert on returned actions, never on the database or button data format.
- Every button tap yields exactly one answer-tap action, so Telegram's spinner always clears.
- Item IDs are opaque strings outside the store.
- Item numbers shown to users are positions in the open list, not IDs. `/done` resolves all numbers before marking any.
- Telegram error messages leave out the request URL: it contains the token.
- An exception while handling one update is logged and skipped, so the polling loop never dies.

Config is in `.env.example`.

## Constraints

- **No dependencies.** Keep it stdlib-only unless the user agrees otherwise. This is what keeps setup on the Pi to a `git clone`.
- **Python 3.10 compatibility.** The dev machine runs 3.14, but the Pi's system Python may be older (Raspberry Pi OS Bookworm ships 3.11). The code uses `X | None` annotations, so 3.10 is the floor.
- **Long polling, not webhooks.** The Pi has no public HTTPS endpoint.
- **Deployment** is the systemd unit in `deploy/btw-bot.service`, which runs `/usr/bin/python3 -m btw_bot` from the repo checkout.

## Git

- **Push when done.** Once a piece of work is committed and the tests pass, push it to `origin` straight away, without asking. CI runs on the push.

## Agent skills

### Issue tracker

Local markdown files under `docs/issues/<feature-slug>/`, committed with the code. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
