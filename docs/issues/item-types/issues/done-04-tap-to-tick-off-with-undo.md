# 04: Tap to tick off, with Undo

**What to build:** The `/list` message gets one full-width [✔️ item text] button per item. Tapping a typed item marks it Done, redraws the list in the same message, and sends a short "✔️ milk" message with a [↩️ Undo] button. Undo brings the item back with the type it had and edits that message to "↩️ Restored: milk". Buttons for items that are done or gone answer clearly instead of failing silently. (Tapping an Unsorted item is ticket 06. Until then it ticks the item off like any other.) Spec user stories 26–30, 33.

**Blocked by:** 02 (Item types via prefixes, grouped list, /move) — done

**Status:** resolved

- [x] `/list` shows one button per item, in the list's order, labelled "✔️ <item text>".
- [x] Tapping an item's button marks it Done and edits the list message to the updated list with its buttons.
- [x] Each tick also sends "✔️ <text>" with an Undo button. Tapping Undo restores the item under its original type and edits that message to "↩️ Restored: <text>".
- [x] Tapping Undo a second time, or tapping a button for an item that is Done, missing or belongs to another chat, answers "That item is no longer on your list" and changes nothing.
- [x] The list shows at most 90 item buttons. Items beyond that still appear in the text and can be ticked off with `/done N`.
- [x] Long list text is split as before, with the buttons attached to the last part. If a redraw would exceed Telegram's length limit, the bot sends a new list message instead of editing.

## Comments

Ticket 03 set up the tap path in `btw_bot/handlers.py` that this ticket extends. Button data there is `<action>:<argument>:...`, with the type prompt as `t:<type letter>:<batch key>`. Add a new action prefix next to it. The "That item is no longer on your list" notice is the `GONE` constant. A tap returns its `AnswerTap` before any `EditMessage`, so Telegram's spinner clears even if the edit fails. The store has no single-item lookup yet; this ticket's stale-tap checks will need one.

Tick buttons carry `x:<item id>`, Undo buttons `u:<item id>:<tick key>`. Each tick (a tap or `/done`) gets a new key from the store (`mark_done` returns it, `undo_done` checks it), so an Undo only reverses the tick that sent it: once the item is restored or ticked off again, that Undo answers `GONE`. The `done` column now holds the tick's number instead of 1, and a `ticks` table hands out the numbers. The store gained `get(chat_id, item_id)` for stale-tap checks. A redraw longer than `MAX_MESSAGE_LENGTH` (now in `btw_bot/actions.py`) is sent as a new list message; the old message keeps its stale buttons, which answer `GONE`. Length is counted in Python characters, like `split_message`, not Telegram's UTF-16 units.
