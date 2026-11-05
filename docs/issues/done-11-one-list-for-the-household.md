# 11: One List for the household

**What to build:** Every allowed user sees and changes the same List from their own private chat. The store stops scoping items by chat, existing items from every chat form the household List, and help text and README describe the List as shared. [Spec](../specs/household-list.md) user stories 1–8.

**Blocked by:** none

**Status:** resolved

- [x] Store operations no longer take a chat; open items, lookups, batch typing and undo work on the one List. New rows write 0 into the unused `chat_id` column.
- [x] Items already in the database, from any chat, appear in every chat's `/list`.
- [x] An item added in one chat shows up in another chat's `/list`; a tap, a sort or an Undo from one chat acts on an item added from the other.
- [x] A tap on an item the other chat already ticked off answers "That item is no longer on the list" and changes nothing.
- [x] Help text and replies say "the list", not "your list".
- [x] The README explains sharing: add the other person's user ID to `BTW_ALLOWED_USERS`, rebuild, and they see the same List in their own chat; nothing is private once shared.
- [x] The `db.py` module docstring no longer says "one list per Telegram chat".
- [x] Tests use two private chats against one store.

## Comments

Implemented in aa6d162. Store operations take no chat; replies still go to the chat the update came from. The `idx_items_chat_done` index is left in place though no query uses `chat_id` any more.
