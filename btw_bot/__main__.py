"""Entry point: `python -m btw_bot`. Reads config and runs the long-polling loop."""

import logging
import os
import sys
import time

from .db import TodoStore
from .handlers import handle
from .telegram import TelegramClient, TelegramError

POLL_TIMEOUT = 50
RETRY_DELAY = 5

log = logging.getLogger("btw_bot")


def load_dotenv(path: str = ".env") -> None:
    """Load KEY=value lines into os.environ. Variables already set take precedence."""
    try:
        with open(path, encoding="utf-8") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip("'\""))


def parse_user_ids(raw: str) -> set[int]:
    return {int(part) for part in raw.replace(",", " ").split()}


def run(client: TelegramClient, store: TodoStore, allowed_users: set[int]) -> None:
    offset = None
    while True:
        try:
            updates = client.get_updates(offset, POLL_TIMEOUT)
        except (OSError, ValueError, TelegramError) as e:
            log.warning("Polling failed, retrying in %ss: %s", RETRY_DELAY, e)
            time.sleep(RETRY_DELAY)
            continue

        for update in updates:
            offset = update["update_id"] + 1
            message = update.get("message")
            if not message or "text" not in message:
                continue
            user_id = message.get("from", {}).get("id")
            if allowed_users and user_id not in allowed_users:
                log.info("Ignoring message from user %s (not in BTW_ALLOWED_USERS)", user_id)
                continue

            chat_id = message["chat"]["id"]
            try:
                reply = handle(store, chat_id, message["text"])
                client.send_message(chat_id, reply)
            except Exception:
                log.exception("Failed to handle update %s", update["update_id"])


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    load_dotenv()

    token = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
    if not token:
        log.error("TELEGRAM_BOT_TOKEN is not set (put it in .env or the environment).")
        return 1
    db_path = os.environ.get("BTW_DB_PATH", "btw.db")
    try:
        allowed_users = parse_user_ids(os.environ.get("BTW_ALLOWED_USERS", ""))
    except ValueError:
        log.error("BTW_ALLOWED_USERS must be a comma-separated list of numeric user IDs.")
        return 1
    if not allowed_users:
        log.warning("BTW_ALLOWED_USERS is empty: anyone who finds the bot can use it.")

    store = TodoStore(db_path)
    log.info("Bot started, database: %s", db_path)
    try:
        run(TelegramClient(token), store, allowed_users)
    except KeyboardInterrupt:
        log.info("Stopping.")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
