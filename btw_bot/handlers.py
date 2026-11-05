"""Turns a Telegram update into a list of actions. No Telegram I/O here."""

from .actions import Action, AnswerTap, SendMessage
from .db import Item, TodoStore

# Types in list order. Unsorted (None) is not a type; it's listed last.
TYPES = ("food", "stuff", "do")
PREFIXES = {"f": "food", "s": "stuff", "d": "do"}
GROUP_NAMES = {"food": "🍎 Food", "stuff": "🛒 Stuff", "do": "✅ Do", None: "❓ Unsorted"}

HELP = """\
Just send me a message and I'll add it to your list.
Each line of a multi-line message becomes a separate item.

Start a line with a letter and a space to give it a type:
f milk - 🍎 Food to buy
s bulbs - 🛒 Stuff to buy that isn't food
d call dentist - ✅ Do (anything that isn't buying)
Without a prefix, the item goes to ❓ Unsorted.

/list - show your list, grouped by type
/done 2 - mark item 2 as done (several: /done 1 3)
/move 3 s - give item 3 another type (f, s or d)
/add text - add an item (same as sending plain text)
/help - show this help"""

# The "/" menu Telegram shows; registered at startup.
COMMANDS = [
    ("list", "Show your list"),
    ("move", "Change an item's type: /move 3 s"),
    ("help", "How to use the bot"),
]


def handle(store: TodoStore, update: dict) -> list[Action]:
    """Handle one raw Telegram update (a text message or a button tap)."""
    tap = update.get("callback_query")
    if tap:
        return [AnswerTap(tap["id"])]
    message = update.get("message")
    if not message or "text" not in message:
        return []
    chat_id = message["chat"]["id"]
    return [SendMessage(chat_id, _reply(store, chat_id, message["text"]))]


def _reply(store: TodoStore, chat_id: int, text: str) -> str:
    # Not stripped on the right: "f " is a prefix with nothing after it, not the item "f".
    if not text.lstrip().startswith("/"):
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
    if command == "/move":
        return _move(store, chat_id, args)
    return "Unknown command. Send /help to see what I can do."


def _parse_line(line: str) -> tuple[str, str | None] | None:
    """Split off a type prefix ("f milk" -> "milk", Food). Anything else is Unsorted, whole.
    A prefix with nothing after it ("f ") gives None: there's no item."""
    letter, space, rest = line.partition(" ")
    item_type = PREFIXES.get(letter.lower())
    if not (item_type and space):
        return line.strip(), None
    if not rest.strip():
        return None
    return rest.strip(), item_type


def _add(store: TodoStore, chat_id: int, text: str) -> str:
    parsed = [_parse_line(line.lstrip()) for line in text.splitlines() if line.strip()]
    added = [p for p in parsed if p is not None]
    if not added:
        return "Nothing to add. Send me some text, e.g. f milk"
    for item_text, item_type in added:
        store.add(chat_id, item_text, item_type)
    if len(added) == 1:
        item_text, item_type = added[0]
        return f"Added to {GROUP_NAMES[item_type]}: {item_text}"
    lines = [f"Added {len(added)} items:"]
    for item_type in (*TYPES, None):
        texts = [text for text, its_type in added if its_type == item_type]
        if texts:
            lines.append(f"{GROUP_NAMES[item_type]}: " + "; ".join(texts))
    return "\n".join(lines)


def _grouped(store: TodoStore, chat_id: int) -> list[Item]:
    """Open items in list order: Food, Stuff, Do, then Unsorted, each in the order added.
    Item numbers are positions in this list."""
    items = store.open_items(chat_id)
    return sorted(items, key=lambda item: _group_rank(item.type))


def _group_rank(item_type: str | None) -> int:
    return TYPES.index(item_type) if item_type in TYPES else len(TYPES)


def _list(store: TodoStore, chat_id: int) -> str:
    items = _grouped(store, chat_id)
    if not items:
        return "Your list is empty."
    sections = []
    for n, item in enumerate(items, start=1):
        if n == 1 or item.type != items[n - 2].type:
            sections.append([GROUP_NAMES[item.type]])
        sections[-1].append(f"{n}. {item.text}")
    return "\n\n".join("\n".join(section) for section in sections)


def _done(store: TodoStore, chat_id: int, args: str) -> str:
    tokens = args.replace(",", " ").split()
    if not tokens or not all(t.isdigit() for t in tokens):
        return "Usage: /done 2 (item numbers from /list)"

    items = _grouped(store, chat_id)
    numbers = sorted({int(t) for t in tokens})
    invalid = [n for n in numbers if not 1 <= n <= len(items)]
    if invalid:
        return f"No item number {', '.join(map(str, invalid))}. Send /list to see your items."

    chosen = [items[n - 1] for n in numbers]
    store.mark_done([item.id for item in chosen])
    return "Done: " + "; ".join(item.text for item in chosen)


MOVE_USAGE = "Usage: /move 3 s (item number from /list, then f = Food, s = Stuff, d = Do)"


def _move(store: TodoStore, chat_id: int, args: str) -> str:
    tokens = args.split()
    item_type = PREFIXES.get(tokens[1].lower()) if len(tokens) == 2 else None
    if not item_type or not tokens[0].isdigit():
        return MOVE_USAGE
    items = _grouped(store, chat_id)
    number = int(tokens[0])
    if not 1 <= number <= len(items):
        return MOVE_USAGE
    item = items[number - 1]
    store.set_type(item.id, item_type)
    return f"Moved to {GROUP_NAMES[item_type]}: {item.text}"
