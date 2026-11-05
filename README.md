# btw-telegram-bot
A 'by the way...' telegram bot for keeping your to-do lists

Send the bot any text and it's added to your list. Pure Python standard library: no dependencies, data in a local SQLite file.

## Commands

- *any text*: adds an item (each line of a multi-line message is a separate item)
- `f milk`, `s bulbs`, `d call dentist`: adds an item as 🍎 Food, 🛒 Stuff or ✅ Do (the prefix letter and a space; any case). Without a prefix it goes to ❓ Unsorted
- `/list`: shows open items grouped Food, Stuff, Do, Unsorted, with one running number. Tap an item's button to tick it off; the bot offers an Undo. Tapping a ❓ Unsorted item instead shows [🍎 Food] [🛒 Stuff] [✅ Do] and [⬅️ Back] in place of the list, to give it a type. The [All] [🍎] [🛒] [✅] row on top filters the list to one type, keeping the item numbers
- `/list food` (or `f`, `stuff`/`s`, `do`/`d`): opens the list already filtered
- `/done 2`: marks item 2 done (several at once: `/done 1 3`)
- `/move 3 s`: changes item 3's type (`f`, `s` or `d`)
- `/add text`: same as sending plain text
- `/help`: shows the commands

## Setup

1. Create a bot with [@BotFather](https://t.me/BotFather) and copy its token.
2. Get your numeric user ID, for example from [@userinfobot](https://t.me/userinfobot).
3. `cp .env.example .env` and fill in `TELEGRAM_BOT_TOKEN` and `BTW_ALLOWED_USERS`.

To try it locally without Docker (Python 3.14), run `python3 -m btw_bot`. For a machine that keeps it running, use Docker as below.

## Deploying with Docker

The bot runs the same way on the Raspberry Pi and on a VPS: Docker with the Compose plugin, built on the machine itself. The Python base image has 64-bit and 32-bit ARMv7 builds, so a Pi 2 or newer works, but a Pi Zero or Pi 1 doesn't. The database is `./data/btw.db` next to `compose.yaml`; configuration comes from `.env`.

### First deploy

```bash
git clone https://github.com/grzegorz-grzeda/btw-telegram-bot.git
cd btw-telegram-bot
cp .env.example .env        # then fill in TELEGRAM_BOT_TOKEN and BTW_ALLOWED_USERS
mkdir data
sudo chown 1000:1000 data   # the container runs as UID 1000 and must be able to write here
docker compose up -d --build
```

Create `./data` yourself before the first start: if Docker creates it, it's owned by root and the bot can't write the database. If your login user is already UID 1000 (check with `id -u`; it usually is on the Pi), `mkdir data` alone is enough.

The container restarts by itself after a crash or a reboot (`restart: unless-stopped`), as long as the Docker service starts at boot.

### Updating

```bash
git pull
docker compose up -d --build
```

The database in `./data` is kept across rebuilds.

### Logs

```bash
docker compose logs -f
```

### Monitoring

An outside dead man's switch watches two checks and alerts you when either goes quiet. [healthchecks.io](https://healthchecks.io/) does this for free. Both are optional.

| Check | Pinged by | Alerts after | Silence means |
| --- | --- | --- | --- |
| `btw bot` | the bot, at most every 5 minutes, after Telegram answered a poll | about 15 minutes | the bot is down (the Pi lost power or network, the container crash-loops, the token was revoked, or a second instance is polling with the same token) |
| `btw backup` | the nightly cron line, only when both the backup and the `rclone sync` succeeded | about 25 hours | last night's backup or Drive copy failed, or cron didn't run |

#### Bot alive

1. Sign up and add a check named, for example, `btw bot`. Set its **Period** to 5 minutes and its **Grace Time** to 10 minutes: it alerts after about 15 minutes without a ping.
2. Copy the check's ping URL (`https://hc-ping.com/…`) into `.env` as `BTW_HEARTBEAT_URL=…`. Keep it private: anyone who has it can ping the check and hide an outage.
3. Under **Integrations**, add **Telegram** and follow its steps to link your Telegram account, so alerts reach you there. Make sure the integration is enabled for the check.
4. Rebuild so the bot picks up the setting: `docker compose up -d --build`. The log says `Heartbeat on`, and the check turns green within a minute.

To test the alert, `docker compose stop` and wait about 15 minutes; `docker compose start` turns the check green again. If a ping fails (healthchecks.io unreachable, say), the bot logs a warning and keeps working. Leave `BTW_HEARTBEAT_URL` empty to turn pings off.

#### Backup ran

1. Add a check named, for example, `btw backup` (sign up first if you skipped the bot check). Set its **Period** to 1 day and its **Grace Time** to 1 hour. Or, under **Schedule**, choose **Cron** and enter the same schedule as the crontab line (`30 3 * * *`) with the host's time zone (often UTC on a VPS), and keep the 1-hour Grace Time, so a late run is caught sooner.
2. Make sure the Telegram integration (step 3 of the bot check) is enabled for this check too.
3. Put the check's ping URL at the end of the nightly cron line (see [Backups](#backups)). The URL lives in the crontab, not in `.env`, because cron runs on the host. As with the bot's URL, keep it private. `curl` must be installed on the host (`sudo apt install curl` if `curl --version` fails).

To test it, run the cron line's command (everything after `30 3 * * *`) once in a shell; the check turns green.

### Backups

The bot can snapshot its database while it keeps running:

```bash
docker compose exec bot python -m btw_bot.backup
```

This writes `./data/backups/btw-YYYY-MM-DD.db` (dated in UTC). A second run on the same day replaces that day's snapshot, and snapshots more than 14 days old are deleted.

To run it nightly and copy the snapshots to Google Drive, install [rclone](https://rclone.org/) on the host and set up a Google Drive remote named `gdrive` (`rclone config`). rclone and its credentials stay on the host, never in the image. Then add a line like this with `crontab -e`, using the path of your checkout:

```cron
30 3 * * * cd /home/pi/btw-telegram-bot && docker compose exec -T bot python -m btw_bot.backup && rclone sync data/backups gdrive:btw-backups && curl -fsS -m 10 --retry 3 https://hc-ping.com/your-backup-check-uuid > /dev/null
```

`-T` is needed because cron has no terminal, and the crontab's user must be able to run `docker` (in the `docker` group). `rclone sync` makes `gdrive:btw-backups` match the local folder, so Drive also keeps only the last 14 days. The final `curl` pings the backup check from [Monitoring](#monitoring); the `&&` chain is what makes it skip the ping when anything before it failed. Replace the URL with your check's, or drop that part if you don't use the check.

### Restoring from a backup

```bash
docker compose stop
cp data/backups/btw-2026-11-05.db data/btw.db   # pick the snapshot you want
docker compose start
```

If a `data/btw.db-journal` file is still there after the stop, delete it before starting the bot, or SQLite will apply it to the restored file. If your login user isn't UID 1000, run `sudo chown 1000:1000 data/btw.db` after the copy. To restore on a fresh machine, download a snapshot from Drive (`rclone copy gdrive:btw-backups/btw-2026-11-05.db .`), copy it to `data/btw.db` and start the bot as in the first deploy.

### Moving from the Pi to a VPS

Telegram allows only one poller per bot token, so **never run both at once**.

1. On the Pi: `docker compose down`.
2. Copy `./data` and `.env` into the checkout on the VPS, for example `rsync -a data .env vps:btw-telegram-bot/`, then on the VPS give the folder back to the container user: `sudo chown -R 1000:1000 data`.
3. On the VPS: `docker compose up -d --build`.

Don't start the Pi again afterwards; to go back, do the same in reverse.

## Tests

```bash
python3 -m unittest
```
