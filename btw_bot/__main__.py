"""Entry point: `python -m btw_bot`. Reads config and runs the long-polling loop."""

import logging
import os
import signal
import sys
import time

from .actions import Action, AnswerTap, EditMessage, SendMessage
from .db import TodoStore
from .handlers import COMMANDS, handle
from .heartbeat import Heartbeat
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


def run(
    client: TelegramClient,
    store: TodoStore,
    allowed_users: set[int],
    heartbeat: Heartbeat | None = None,
) -> None:
    offset = None
    while True:
        try:
            updates = client.get_updates(offset, POLL_TIMEOUT)
        except (OSError, ValueError, TelegramError) as e:
            log.warning("Polling failed, retrying in %ss: %s", RETRY_DELAY, e)
            time.sleep(RETRY_DELAY)
            continue
        if heartbeat:
            heartbeat.beat()

        for update in updates:
            offset = update["update_id"] + 1
            user_id = sender_id(update)
            if allowed_users and user_id not in allowed_users:
                log.info("Ignoring update from user %s (not in BTW_ALLOWED_USERS)", user_id)
                continue

            try:
                for action in handle(store, update):
                    execute(client, action)
            except Exception:
                log.exception("Failed to handle update %s", update["update_id"])


def sender_id(update: dict) -> int | None:
    """The user who sent a message or tapped a button."""
    event = update.get("message") or update.get("callback_query") or {}
    return event.get("from", {}).get("id")


def execute(client: TelegramClient, action: Action) -> None:
    if isinstance(action, SendMessage):
        client.send_message(action.chat_id, action.text, action.buttons)
    elif isinstance(action, EditMessage):
        client.edit_message(action.chat_id, action.message_id, action.text, action.buttons)
    elif isinstance(action, AnswerTap):
        client.answer_tap(action.tap_id, action.notice)
    else:
        raise TypeError(f"Unknown action: {action!r}")


def stop_on_sigterm(signum, frame) -> None:
    """`docker stop` sends SIGTERM, which PID 1 ignores without a handler: stop like Ctrl-C."""
    raise KeyboardInterrupt


def main() -> int:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    signal.signal(signal.SIGTERM, stop_on_sigterm)
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

    heartbeat_url = os.environ.get("BTW_HEARTBEAT_URL", "").strip()
    heartbeat = Heartbeat(heartbeat_url) if heartbeat_url else None

    store = TodoStore(db_path)
    client = TelegramClient(token)
    log.info("Bot started, database: %s", db_path)
    if heartbeat:
        log.info("Heartbeat on: pinging BTW_HEARTBEAT_URL while polling works.")
    try:
        client.set_commands(COMMANDS)
    except (OSError, ValueError, TelegramError) as e:
        log.warning("Could not register the command menu: %s", e)
    try:
        run(client, store, allowed_users, heartbeat)
    except KeyboardInterrupt:
        log.info("Stopping.")
    finally:
        store.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
