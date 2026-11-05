# 05: Filter row and /list food

**What to build:** The top of the `/list` message gets a row of filter buttons, [All] [🍎] [🛒] [✅], with the active one marked. Tapping a filter redraws the same message showing only that type. Item numbers stay the same as in the full list. Ticking an item off in a filtered view keeps the filter. `/list food` (or `f`, and likewise for stuff and do) opens the list already filtered. Spec user stories 19–24.

**Blocked by:** 04 (Tap to tick off, with Undo) — done

**Status:** ready-for-agent

- [ ] The list message has a filter row above the item buttons, and the active filter is visibly marked.
- [ ] Tapping a filter edits the same message to show only that type's items and buttons.
- [ ] Items keep the numbers they have in the full list, so a filtered Stuff view of "1. milk, 2. eggs, 3. bulbs" shows "3. bulbs".
- [ ] Ticking an item off in a filtered view redraws the list with the same filter.
- [ ] `/list food`, `/list f`, `/list stuff`, `/list s`, `/list do` and `/list d` open the list filtered. Any other argument replies with the usage.
- [ ] A filtered view with no items says so (for example "No Food items."), and the filter row is still there.

## Comments

Ticket 04: tick buttons in `/list` carry `x:<item id>` with no filter yet (`TICK` in `btw_bot/handlers.py`). This ticket needs to add the filter to that data so a tick redraws with the same filter. `_list` now returns `(text, buttons)` and caps item buttons at `MAX_ITEM_BUTTONS = 90`.
