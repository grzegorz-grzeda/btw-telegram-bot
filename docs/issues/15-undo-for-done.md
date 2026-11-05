# 15: Undo for /done

**What to build:** `/done` sends an ↩️ Undo button for each item it ticked off, the same as tapping an item does, so a number that moved or a typo can be put right. [Spec](../specs/household-list.md) user story 19.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] `/done` still replies "Done: ..." and also sends one "✔️ text" message with an Undo button per item ticked off, all from the same tick.
- [ ] Tapping one of those Undo buttons reopens that item with its type and edits its message, exactly as for a tapped item.
- [ ] The README mentions the Undo for `/done`.
- [ ] Tests take Undo buttons from the returned actions, tap them and check the items are back in `/list`.
