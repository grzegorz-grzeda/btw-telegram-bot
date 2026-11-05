# 01: One List for the household

**What to build:** Every allowed user sees and changes the same List from their own private chat. The store stops scoping items by chat, existing items from every chat form the household List, and help text and README describe the List as shared. Spec user stories 1–8.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] Store operations no longer take a chat; open items, lookups, batch typing and undo work on the one List. New rows write 0 into the unused `chat_id` column.
- [ ] Items already in the database, from any chat, appear in every chat's `/list`.
- [ ] An item added in one chat shows up in another chat's `/list`; a tap, a sort or an Undo from one chat acts on an item added from the other.
- [ ] A tap on an item the other chat already ticked off answers "That item is no longer on the list" and changes nothing.
- [ ] Help text and replies say "the list", not "your list".
- [ ] The README explains sharing: add the other person's user ID to `BTW_ALLOWED_USERS`, rebuild, and they see the same List in their own chat; nothing is private once shared.
- [ ] The `db.py` module docstring no longer says "one list per Telegram chat".
- [ ] Tests use two private chats against one store.
