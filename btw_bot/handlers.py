"""Turns an incoming message text into a reply. No Telegram I/O here."""

from .db import TodoStore

HELP = """\
Just send me a message and I'll add it to your list.
Each line of a multi-line message becomes a separate item.

/list - show your list
/done 2 - mark item 2 as done (several: /done 1 3)
/add text - add an item (same as sending plain text)
/help - show this help"""


def handle(store: TodoStore, chat_id: int, text: str) -> str:
    text = text.strip()
    if not text.startswith("/"):
        return _add(store, chat_id, text)

    parts = text.split(maxsplit=1)
    # In group chats commands arrive as "/list@MyBot".
    command = parts[0].split("@", 1)[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command in ("/start", "/help"):
        return HELP
    if command == "/add":
        return _add(store, chat_id, args)
    if command == "/list":
        return _list(store, chat_id)
    if command == "/done":
        return _done(store, chat_id, args)
    return "Unknown command. Send /help to see what I can do."


def _add(store: TodoStore, chat_id: int, text: str) -> str:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return "Nothing to add. Send me some text."
    for line in lines:
        store.add(chat_id, line)
    if len(lines) == 1:
        return f"Added: {lines[0]}"
    return f"Added {len(lines)} items."


def _list(store: TodoStore, chat_id: int) -> str:
    items = store.open_items(chat_id)
    if not items:
        return "Your list is empty."
    return "\n".join(f"{n}. {item.text}" for n, item in enumerate(items, start=1))


def _done(store: TodoStore, chat_id: int, args: str) -> str:
    tokens = args.replace(",", " ").split()
    if not tokens or not all(t.isdigit() for t in tokens):
        return "Usage: /done 2 (item numbers from /list)"

    items = store.open_items(chat_id)
    numbers = sorted({int(t) for t in tokens})
    invalid = [n for n in numbers if not 1 <= n <= len(items)]
    if invalid:
        return f"No item number {', '.join(map(str, invalid))}. Send /list to see your items."

    chosen = [items[n - 1] for n in numbers]
    store.mark_done([item.id for item in chosen])
    return "Done: " + "; ".join(item.text for item in chosen)
