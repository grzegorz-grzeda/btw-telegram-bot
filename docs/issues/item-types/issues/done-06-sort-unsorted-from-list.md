# 06: Sort Unsorted items from the list

**What to build:** In the `/list` message, tapping an Unsorted item opens a type picker for that item instead of ticking it off. The list message is replaced in place by [🍎 Food] [🛒 Stuff] [✅ Do] plus a back button. Choosing a type files the item and redraws the list with the item in its new group. Back returns to the list unchanged. Spec user stories 34–36, 40.

**Blocked by:** 04 (Tap to tick off, with Undo) — done

**Status:** resolved

- [x] Tapping an Unsorted item's button edits the list message into a type picker for that item. Nothing is ticked off.
- [x] Choosing a type sets it and edits the message back to the list, with the item under that type and the numbers updated.
- [x] The back button returns the message to the list without changing anything.
- [x] If the item was ticked off or moved elsewhere in the meantime, choosing a type answers "That item is no longer on your list" (or leaves the newer type alone) and redraws the current list.
- [x] If ticket 05 has landed, the picker and the redrawn list keep the filter the list was showing.
- [x] `/done N` still ticks off Unsorted items directly.

## Comments

Ticket 04: tapping any item, Unsorted included, currently ticks it off in `_tick_tap` (`btw_bot/handlers.py`). This ticket branches there for Unsorted items. The store now has `get(chat_id, item_id)` for single-item lookup.

Ticket 05 (not a blocker, but it changed the list): tick buttons are now `x:<filter letter>:<item id>`, and any list redraw should go through `_redraw(store, message, only)` in `btw_bot/handlers.py` so it keeps the filter. Unsorted items appear only under the All filter.

Ticket 06: tapping an Unsorted item's `x:` button now edits the list into a picker (`_picker` in `btw_bot/handlers.py`); old lists' Unsorted buttons do the same. Picker buttons are `s:<filter letter>:<type letter>:<item id>`; Back reuses the filter button `l:<filter letter>`. Choosing a type for an item done since answers `GONE`, for one sorted since answers "Already in <type>" and keeps that type; both redraw the list. Unsorted items' list buttons now read "❓ text" instead of "✔️ text", since tapping them no longer ticks off. `_type_row` builds the [🍎 Food] [🛒 Stuff] [✅ Do] row for both the add prompt and the picker.

Implemented in e010e28.
