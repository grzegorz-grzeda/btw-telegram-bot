# 05: Filter row and /list food

**What to build:** The top of the `/list` message gets a row of filter buttons, [All] [🍎] [🛒] [✅], with the active one marked. Tapping a filter redraws the same message showing only that type. Item numbers stay the same as in the full list. Ticking an item off in a filtered view keeps the filter. `/list food` (or `f`, and likewise for stuff and do) opens the list already filtered. Spec user stories 19–24.

**Blocked by:** 04 (Tap to tick off, with Undo) — done

**Status:** resolved

- [x] The list message has a filter row above the item buttons, and the active filter is visibly marked.
- [x] Tapping a filter edits the same message to show only that type's items and buttons.
- [x] Items keep the numbers they have in the full list, so a filtered Stuff view of "1. milk, 2. eggs, 3. bulbs" shows "3. bulbs".
- [x] Ticking an item off in a filtered view redraws the list with the same filter.
- [x] `/list food`, `/list f`, `/list stuff`, `/list s`, `/list do` and `/list d` open the list filtered. Any other argument replies with the usage.
- [x] A filtered view with no items says so (for example "No Food items."), and the filter row is still there.

## Comments

Ticket 04: tick buttons in `/list` carry `x:<item id>` with no filter yet (`TICK` in `btw_bot/handlers.py`). This ticket needs to add the filter to that data so a tick redraws with the same filter. `_list` now returns `(text, buttons)` and caps item buttons at `MAX_ITEM_BUTTONS = 90`.

Ticket 05: list buttons now carry the filter. Filter buttons are `l:<filter letter>`, ticks `x:<filter letter>:<item id>`, with `a` for All and f/s/d for the types (`FILTER_LETTERS` in `btw_bot/handlers.py`). `_list(store, chat_id, only)` draws a filtered view (Unsorted shows only under All), and `_redraw` handles any in-place redraw, sending a new message when it's too long to edit. Tick buttons from before this change (`x:<item id>`) answer `GONE`. A list with nothing open at all still says "Your list is empty." with no filter row, per story 25. `TelegramClient.edit_message` ignores Telegram's "message is not modified" error, so tapping the active filter isn't logged as a failure.
