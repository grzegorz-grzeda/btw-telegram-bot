# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

**btw-telegram-bot**: a "by the way..." Telegram bot that keeps one to-do list, shared by everyone in `BTW_ALLOWED_USERS`. It's meant to stay small and simple, and runs as a proof of concept on a Raspberry Pi. See `README.md` for user-facing commands and setup.

## Commands

```bash
python3 -m btw_bot                                    # run the bot locally (reads .env from the cwd)
docker compose up -d --build                          # run it as deployed (database in ./data)
python3 -m unittest                                   # all tests
python3 -m unittest tests.test_handlers.HandleTest.test_add_command   # one test
```

There is no build step, linter config or virtualenv: the project uses only the standard library. CI (`.github/workflows/test.yml`) runs the tests on Python 3.14, the version the Docker image pins.

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

- **No dependencies.** Keep it stdlib-only unless the user agrees otherwise. This keeps the image free of any install step, so it builds in seconds on the Pi.
- **Long polling, not webhooks.** The Pi has no public HTTPS endpoint.
- **Deployment** is Docker, the same on the Pi and the VPS: `git pull` then `docker compose up -d --build` in the repo checkout. The `Dockerfile` pins Python, so that's the only version to support. Images are built on the device, with no registry. The database lives in the bind-mounted `./data`; `compose.yaml` sets its path, overriding `.env`. The bot runs as PID 1, so it handles SIGTERM itself to stop promptly.
- **One instance at a time.** Telegram allows one poller per bot token, so the Pi and the VPS never run together.

## Git

- **Stage by path, never in bulk.** The user edits files (including `.env`) in nano alongside you, so the tree can hold their lock files and half-done edits. Run `git add <path>` for each file you changed, never `git add -A`, `git add .` or `git commit -a`. Before committing, check `git status --short` for files you didn't touch and leave them out; ask if one looks like it belongs.
- **Push when done.** Once a piece of work is committed and the tests pass, push it to `origin` straight away, without asking. CI runs on the push.

## Agent skills

### Issue tracker

Local markdown files, committed with the code: tickets in `docs/issues/` with one running number, specs in `docs/specs/`. See `docs/agents/issue-tracker.md`.

### Triage labels

The five default roles (`needs-triage`, `needs-info`, `ready-for-agent`, `ready-for-human`, `wontfix`), recorded as a `Status:` line in each issue file. See `docs/agents/triage-labels.md`.

### Domain docs

Single-context: `GLOSSARY.md` and `docs/adr/` at the repo root. See `docs/agents/domain.md`.
