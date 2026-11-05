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
4. Run it (Python 3.10+):

   ```bash
   python3 -m btw_bot
   ```

## Running on a Raspberry Pi

Clone the repo on the Pi, create `.env` as above, then install the systemd unit (edit `User` and `WorkingDirectory` in it first if your user isn't `pi`):

```bash
sudo cp deploy/btw-bot.service /etc/systemd/system/
sudo systemctl enable --now btw-bot
journalctl -u btw-bot -f
```

## Tests

```bash
python3 -m unittest
```
