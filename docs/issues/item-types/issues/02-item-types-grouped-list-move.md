# 02: Item types via prefixes, grouped list, /move

**What to build:** Items get a Type (Food, Stuff or Do) or are Unsorted. A line starting with `f `, `s ` or `d ` (any case) is filed under that type, with the prefix removed. Anything else is saved whole as Unsorted. There's no type prompt yet. `/list` shows the List grouped Food → Stuff → Do → Unsorted, with one running number across the groups. `/move N <f|s|d>` changes an item's type. The help text explains types and prefixes, and `/list`, `/move` and `/help` appear in Telegram's "/" menu. Items that existed before this change show up as Unsorted. Spec user stories 1–6, 9, 11–18, 25, 31, 32, 38–43.

**Blocked by:** 01 (Handler returns actions)

**Status:** ready-for-agent

- [ ] `f milk`, `S bulbs` and `d call dentist` are filed as Food, Stuff and Do, with the prefix removed from the text.
- [ ] "do the dishes", "food for the dog" and a bare `f` are saved whole as Unsorted.
- [ ] A multi-line message makes one item per line, each with its own optional prefix. The reply says what was added and where.
- [ ] `/add` follows the same rules as plain text, and empty input or a prefix with no text is politely rejected.
- [ ] `/list` groups items in the order Food, Stuff, Do, Unsorted, omits empty groups, keeps the order items were added within each group, and numbers items 1…N across the groups.
- [ ] `/done N` resolves numbers against that grouped order and works on Unsorted items too.
- [ ] `/move 3 s` changes item 3's type. A wrong number or type letter replies with the correct usage.
- [ ] A database created before types existed opens without error, and its items appear as Unsorted (tested with a file-based store).
- [ ] At startup the bot registers `/list`, `/move` and `/help` with short descriptions. A failure is logged and doesn't stop the bot.
- [ ] The help text covers types, prefixes and `/move`.
