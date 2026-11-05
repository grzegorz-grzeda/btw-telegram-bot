# 07: Docker deployment

**What to build:** The bot runs in Docker, deployed the same way on the Raspberry Pi and the VPS: `git pull` then `docker compose up -d --build` in the repo checkout. The database lives in a bind-mounted `./data` folder next to the compose file, and configuration still comes from `.env`. The systemd deployment is removed. The docs describe deploying, updating and moving from the Pi to the VPS. Spec user stories 45–51.

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The image is based on Python 3.14 slim, installs no dependencies, runs `python -m btw_bot` as a non-root user, and has unbuffered output.
- [ ] The compose file defines one bot service with `restart: unless-stopped`, environment from `.env`, and `./data` bind-mounted as the data directory, with the database path pointing into it.
- [ ] `docker compose up -d --build` starts the bot from a fresh checkout. The database file appears in `./data` on the host and survives a rebuild.
- [ ] `docker compose logs -f` shows the bot's log lines as they happen.
- [ ] The systemd unit is deleted.
- [ ] The README covers: first deploy (including creating `./data` with ownership the container user can write), updating, reading logs, and moving to the VPS (stop the Pi, copy `./data` and `.env`, start the VPS, never run both at once).
- [ ] CLAUDE.md drops the "compatible with the Pi's system Python" constraint and describes the Docker deployment instead.
