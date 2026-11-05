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
