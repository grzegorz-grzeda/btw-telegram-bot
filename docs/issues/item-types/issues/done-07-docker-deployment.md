# 07: Docker deployment

**What to build:** The bot runs in Docker, deployed the same way on the Raspberry Pi and the VPS: `git pull` then `docker compose up -d --build` in the repo checkout. The database lives in a bind-mounted `./data` folder next to the compose file, and configuration still comes from `.env`. The systemd deployment is removed. The docs describe deploying, updating and moving from the Pi to the VPS. Spec user stories 45–51.

**Blocked by:** None (can start immediately)

**Status:** resolved

- [x] The image is based on Python 3.14 slim, installs no dependencies, runs `python -m btw_bot` as a non-root user, and has unbuffered output.
- [x] The compose file defines one bot service with `restart: unless-stopped`, environment from `.env`, and `./data` bind-mounted as the data directory, with the database path pointing into it.
- [x] `docker compose up -d --build` starts the bot from a fresh checkout. The database file appears in `./data` on the host and survives a rebuild.
- [x] `docker compose logs -f` shows the bot's log lines as they happen.
- [x] The systemd unit is deleted.
- [x] The README covers: first deploy (including creating `./data` with ownership the container user can write), updating, reading logs, and moving to the VPS (stop the Pi, copy `./data` and `.env`, start the VPS, never run both at once).
- [x] CLAUDE.md drops the "compatible with the Pi's system Python" constraint and describes the Docker deployment instead.

## Comments

Verified by building and running the image with a fake token: the bot runs as UID 1000, the image holds only `btw_bot/`, `./data/btw.db` appears on the host and keeps its rows across `up -d --build --force-recreate`, logs stream live, and the restart policy is `unless-stopped`.

Beyond the checklist: the bot handles SIGTERM, raising `KeyboardInterrupt` in `btw_bot/__main__.py`. Python as PID 1 otherwise ignores SIGTERM, so every `docker compose down` or rebuild would wait 10 s for a SIGKILL. With the 3.10 floor gone, CI tests only Python 3.14, the version the image pins.
