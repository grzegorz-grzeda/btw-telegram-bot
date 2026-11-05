# 06: Sort Unsorted items from the list

**What to build:** In the `/list` message, tapping an Unsorted item opens a type picker for that item instead of ticking it off. The list message is replaced in place by [🍎 Food] [🛒 Stuff] [✅ Do] plus a back button. Choosing a type files the item and redraws the list with the item in its new group. Back returns to the list unchanged. Spec user stories 34–36, 40.

**Blocked by:** 04 (Tap to tick off, with Undo)

**Status:** ready-for-agent

- [ ] Tapping an Unsorted item's button edits the list message into a type picker for that item. Nothing is ticked off.
- [ ] Choosing a type sets it and edits the message back to the list, with the item under that type and the numbers updated.
- [ ] The back button returns the message to the list without changing anything.
- [ ] If the item was ticked off or moved elsewhere in the meantime, choosing a type answers "That item is no longer on your list" (or leaves the newer type alone) and redraws the current list.
- [ ] If ticket 05 has landed, the picker and the redrawn list keep the filter the list was showing.
- [ ] `/done N` still ticks off Unsorted items directly.
