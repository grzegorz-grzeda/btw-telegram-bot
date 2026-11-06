"""Turns a Telegram update into a list of actions. No Telegram I/O here."""

from .actions import (
    MAX_MESSAGE_LENGTH,
    Action,
    AnswerTap,
    Button,
    Buttons,
    EditMessage,
    SendMessage,
)
from .db import Item, TodoStore

# Types in list order. Unsorted (None) is not a type; it's listed last.
TYPES = ("food", "stuff", "do")
PREFIXES = {"f": "food", "s": "stuff", "d": "do"}
GROUP_NAMES = {"food": "🍎 Food", "stuff": "🛒 Stuff", "do": "✅ Do", None: "❓ Unsorted"}
GONE = "That item is no longer on the list"
PRIVATE_ONLY = "I only work in private chats"
# The filter row on /list: None shows everything. Only All shows Unsorted.
FILTERS = (None, *TYPES)
FILTER_LABELS = {None: "All", "food": "🍎", "stuff": "🛒", "do": "✅"}
# How a filter is written in button data and typed after /list: a = All, then the prefixes.
FILTER_LETTERS = {"a": None, **PREFIXES}
# Telegram allows 100 buttons per message; the rest of the list is ticked off with /done N.
MAX_ITEM_BUTTONS = 90

HELP = """\
Just send me a message and I'll add it to the list.
The list is shared by everyone allowed to use the bot.
Each line of a multi-line message becomes a separate item.

Start a line with a letter and a space to give it a type:
f milk - 🍎 Food to buy
s bulbs - 🛒 Stuff to buy that isn't food
d call dentist - ✅ Do (anything that isn't buying)
Without a prefix, the item goes to ❓ Unsorted.

/list - show the list, grouped by type (tap an item to tick it off,
  or a ❓ Unsorted one to give it a type)
/list f - show only Food (or s, d); the buttons on top filter too
/done 2 - mark item 2 as done (several: /done 1 3)
/move 3 s - give item 3 another type (f, s or d)
/add text - add an item (same as sending plain text)
/help - show this help"""

# The "/" menu Telegram shows; registered at startup.
COMMANDS = [
    ("list", "Show the list (/list f for only Food)"),
    ("move", "Change an item's type: /move 3 s"),
    ("help", "How to use the bot"),
]


def handle(store: TodoStore, update: dict) -> list[Action]:
    """Handle one raw Telegram update (a text message or a button tap)."""
    tap = update.get("callback_query")
    if tap:
        return _tap(store, tap)
    message = update.get("message")
    if not message or "text" not in message:
        return []
    chat_id = message["chat"]["id"]
    if not _is_private(message):
        return [SendMessage(chat_id, PRIVATE_ONLY)]
    reply = _reply(store, message["text"])
    text, buttons = (reply, None) if isinstance(reply, str) else reply
    return [SendMessage(chat_id, text, buttons)]


def _is_private(message: dict) -> bool:
    """A group would be a second way in to the one list."""
    return message["chat"].get("type") == "private"


# Button data is "<action>:<argument>:...", written and parsed only in this module.
TYPE_PROMPT = "t"  # "t:<type letter>:<batch key>"
FILTER = "l"  # "l:<filter letter>", on the filter row of /list
TICK = "x"  # "x:<filter letter>:<item id>", on each item in /list (Unsorted ones open the picker)
SORT = "s"  # "s:<filter letter>:<type letter>:<item id>", on the type picker
UNDO = "u"  # "u:<item id>:<tick key>", on the message sent after a tick


def _tap(store: TodoStore, tap: dict) -> list[Action]:
    """Every tap yields exactly one AnswerTap, so Telegram's spinner always clears."""
    message = tap.get("message")
    if message and not _is_private(message):
        return [AnswerTap(tap["id"], PRIVATE_ONLY)]
    action, _, rest = (tap.get("data") or "").partition(":")
    if not message or not rest:
        return [AnswerTap(tap["id"])]
    if action == TYPE_PROMPT:
        return _type_tap(store, tap, rest)
    if action == FILTER:
        return _filter_tap(store, tap, rest)
    if action == TICK:
        return _tick_tap(store, tap, rest)
    if action == UNDO:
        return _undo_tap(store, tap, rest)
    if action == SORT:
        return _sort_tap(store, tap, rest)
    return [AnswerTap(tap["id"])]


def _filter_tap(store: TodoStore, tap: dict, letter: str) -> list[Action]:
    if letter not in FILTER_LETTERS:
        return [AnswerTap(tap["id"])]
    return [AnswerTap(tap["id"]), _redraw(store, tap["message"], FILTER_LETTERS[letter])]


def _redraw(store: TodoStore, message: dict, only: str | None) -> Action:
    """Redraw the list in the tapped message, filtered by `only`."""
    chat_id = message["chat"]["id"]
    text, buttons = _list(store, only)
    # An edit can't be split like a sent message, so a list that's too long is sent anew.
    if len(text) > MAX_MESSAGE_LENGTH:
        return SendMessage(chat_id, text, buttons)
    return EditMessage(chat_id, message["message_id"], text, buttons)


def _tick_tap(store: TodoStore, tap: dict, rest: str) -> list[Action]:
    message = tap["message"]
    chat_id = message["chat"]["id"]
    letter, _, item_id = rest.partition(":")
    # Lists sent before filters existed carry "x:<item id>": treat those buttons as stale.
    if letter not in FILTER_LETTERS or not item_id:
        return [AnswerTap(tap["id"], GONE)]
    item = store.get(item_id)
    if item is None or item.done:
        return [AnswerTap(tap["id"], GONE)]
    if item.type is None:
        text = f"Which type is “{item.text}”?"
        picker = EditMessage(chat_id, message["message_id"], text, _picker(letter, item))
        return [AnswerTap(tap["id"]), picker]
    tick = store.mark_done([item.id])
    return [
        AnswerTap(tap["id"]),
        _redraw(store, message, FILTER_LETTERS[letter]),
        SendMessage(chat_id, f"✔️ {item.text}", [[Button("↩️ Undo", f"{UNDO}:{item.id}:{tick}")]]),
    ]


def _picker(letter: str, item: Item) -> Buttons:
    """Type buttons for one Unsorted item, and Back to the list it was opened from."""
    back = Button("⬅️ Back", f"{FILTER}:{letter}")
    return [_type_row(f"{SORT}:{letter}:{{}}:{item.id}"), [back]]


def _sort_tap(store: TodoStore, tap: dict, rest: str) -> list[Action]:
    message = tap["message"]
    letter, _, rest = rest.partition(":")
    type_letter, _, item_id = rest.partition(":")
    if letter not in FILTER_LETTERS or type_letter not in PREFIXES or not item_id:
        return [AnswerTap(tap["id"])]
    item = store.get(item_id)
    # Ticked off or sorted since the picker opened: leave it be, show the list as it is now.
    if item is None or item.done:
        answer = AnswerTap(tap["id"], GONE)
    elif item.type is not None:
        answer = AnswerTap(tap["id"], f"Already in {GROUP_NAMES[item.type]}")
    else:
        store.set_type(item.id, PREFIXES[type_letter])
        answer = AnswerTap(tap["id"])
    return [answer, _redraw(store, message, FILTER_LETTERS[letter])]


def _undo_tap(store: TodoStore, tap: dict, rest: str) -> list[Action]:
    message = tap["message"]
    chat_id = message["chat"]["id"]
    item_id, _, tick = rest.partition(":")
    item = store.undo_done(item_id, tick)
    if item is None:
        return [AnswerTap(tap["id"], GONE)]
    text = f"↩️ Restored: {item.text}"
    return [AnswerTap(tap["id"]), EditMessage(chat_id, message["message_id"], text)]


def _type_tap(store: TodoStore, tap: dict, rest: str) -> list[Action]:
    message = tap["message"]
    letter, _, batch = rest.partition(":")
    if letter not in PREFIXES or not batch:
        return [AnswerTap(tap["id"])]
    chat_id = message["chat"]["id"]
    item_type = PREFIXES[letter]
    typed = store.type_batch(batch, item_type)
    if not typed:
        return [AnswerTap(tap["id"], GONE)]
    text = _added_to(item_type, [item.text for item in typed])
    # Answer first: if the edit fails, the spinner must still clear.
    return [AnswerTap(tap["id"]), EditMessage(chat_id, message["message_id"], text)]


def _added_to(item_type: str | None, texts: list[str]) -> str:
    return f"Added to {GROUP_NAMES[item_type]}: " + "; ".join(texts)


def _type_prompt(batch: str) -> Buttons:
    return [_type_row(f"{TYPE_PROMPT}:{{}}:{batch}")]


def _type_row(data: str) -> list[Button]:
    """[🍎 Food] [🛒 Stuff] [✅ Do]; `data` has a {} where each type's letter goes."""
    return [Button(GROUP_NAMES[t], data.format(letter)) for letter, t in PREFIXES.items()]


def _reply(store: TodoStore, text: str) -> str | tuple[str, Buttons | None]:
    # Not stripped on the right: "f " is a prefix with nothing after it, not the item "f".
    if not text.lstrip().startswith("/"):
        return _add(store, text)

    parts = text.split(maxsplit=1)
    # A command may carry the bot's name: "/list@MyBot".
    command = parts[0].split("@", 1)[0].lower()
    args = parts[1] if len(parts) > 1 else ""

    if command in ("/start", "/help"):
        return HELP
    if command == "/add":
        return _add(store, args)
    if command == "/list":
        return _list_command(store, args)
    if command == "/done":
        return _done(store, args)
    if command == "/move":
        return _move(store, args)
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


def _add(store: TodoStore, text: str) -> str | tuple[str, Buttons | None]:
    """Add each line as an item. Unsorted ones get one type prompt for the whole message."""
    parsed = [_parse_line(line.lstrip()) for line in text.splitlines() if line.strip()]
    added = [p for p in parsed if p is not None]
    if not added:
        return "Nothing to add. Send me some text, e.g. f milk"
    batch = store.add_batch(added)
    has_unsorted = any(item_type is None for _, item_type in added)
    buttons = _type_prompt(batch) if has_unsorted else None
    if len(added) == 1:
        item_text, item_type = added[0]
        return _added_to(item_type, [item_text]), buttons
    lines = [f"Added {len(added)} items:"]
    for item_type in (*TYPES, None):
        texts = [text for text, its_type in added if its_type == item_type]
        if texts:
            lines.append(f"{GROUP_NAMES[item_type]}: " + "; ".join(texts))
    return "\n".join(lines), buttons


def _grouped(store: TodoStore) -> list[Item]:
    """Open items in list order: Food, Stuff, Do, then Unsorted, each in the order added.
    Item numbers are positions in this list."""
    items = store.open_items()
    return sorted(items, key=lambda item: _group_rank(item.type))


def _group_rank(item_type: str | None) -> int:
    return TYPES.index(item_type) if item_type in TYPES else len(TYPES)


def _list(store: TodoStore, only: str | None = None) -> tuple[str, Buttons | None]:
    """The list text, a filter row, and one full-width tick button per item shown.
    `only` is a type to filter by; numbers are still those of the full list."""
    items = _grouped(store)
    if not items:
        return "The list is empty.", None
    numbered = [(n, item) for n, item in enumerate(items, start=1) if only in (None, item.type)]
    sections = []
    for i, (n, item) in enumerate(numbered):
        if i == 0 or item.type != numbered[i - 1][1].type:
            sections.append([GROUP_NAMES[item.type]])
        sections[-1].append(f"{n}. {item.text}")
    text = "\n\n".join("\n".join(section) for section in sections)
    if not numbered:
        text = f"No {only.capitalize()} items."
    shown = [item for _, item in numbered[:MAX_ITEM_BUTTONS]]
    letter = _filter_letter(only)
    buttons = [_filter_row(only)]
    buttons += [
        [Button(f"{_tap_icon(item)} {item.text}", f"{TICK}:{letter}:{item.id}")] for item in shown
    ]
    return text, buttons


def _tap_icon(item: Item) -> str:
    """What tapping the item does: tick it off, or (Unsorted) pick a type."""
    return "❓" if item.type is None else "✔️"


LIST_USAGE = "Usage: /list, or /list food (f), /list stuff (s), /list do (d)"


def _list_command(store: TodoStore, args: str) -> str | tuple[str, Buttons | None]:
    """/list, or /list with a type (food, stuff, do) or its letter to open it filtered."""
    arg = args.strip().lower()
    if not arg:
        return _list(store)
    only = PREFIXES.get(arg, arg)
    if only not in TYPES:
        return LIST_USAGE
    return _list(store, only)


def _filter_row(active: str | None) -> list[Button]:
    def label(f: str | None) -> str:
        return f"• {FILTER_LABELS[f]}" if f == active else FILTER_LABELS[f]

    return [Button(label(f), f"{FILTER}:{_filter_letter(f)}") for f in FILTERS]


def _filter_letter(only: str | None) -> str:
    return next(letter for letter, t in FILTER_LETTERS.items() if t == only)


def _done(store: TodoStore, args: str) -> str:
    tokens = args.replace(",", " ").split()
    if not tokens or not all(t.isdigit() for t in tokens):
        return "Usage: /done 2 (item numbers from /list)"

    items = _grouped(store)
    numbers = sorted({int(t) for t in tokens})
    invalid = [n for n in numbers if not 1 <= n <= len(items)]
    if invalid:
        return f"No item number {', '.join(map(str, invalid))}. Send /list to see the items."

    chosen = [items[n - 1] for n in numbers]
    store.mark_done([item.id for item in chosen])
    return "Done: " + "; ".join(item.text for item in chosen)


MOVE_USAGE = "Usage: /move 3 s (item number from /list, then f = Food, s = Stuff, d = Do)"


def _move(store: TodoStore, args: str) -> str:
    tokens = args.split()
    item_type = PREFIXES.get(tokens[1].lower()) if len(tokens) == 2 else None
    if not item_type or not tokens[0].isdigit():
        return MOVE_USAGE
    items = _grouped(store)
    number = int(tokens[0])
    if not 1 <= number <= len(items):
        return MOVE_USAGE
    item = items[number - 1]
    store.set_type(item.id, item_type)
    return f"Moved to {GROUP_NAMES[item_type]}: {item.text}"
