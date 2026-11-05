# 14: Block duplicates

**What to build:** Adding an item whose text matches an open item, ignoring case and spacing, adds nothing and says where the existing item is; a prefix fills in a missing type. Duplicates already in the database are merged on startup, keeping the oldest. [Spec](../specs/household-list.md) user stories 11–18.

**Blocked by:** 11 (One List for the household)

**Status:** ready-for-agent

- [ ] One duplicate key: casefolded, whitespace runs collapsed to one space, ends trimmed. Adding and the cleanup both use it.
- [ ] A line matching an open item adds nothing; the reply says "Already on the list under <group>: <existing text>".
- [ ] A typed line matching an open Unsorted item gives that item the type; the reply says "Moved to <group>: <text>".
- [ ] A line matching an open typed item never changes its type, whatever its prefix.
- [ ] Done items don't count as matches.
- [ ] Repeats within one message are added once, with the skipped lines noted in the reply.
- [ ] The type prompt appears only when at least one new Unsorted item was added, and covers only the new ones.
- [ ] On startup, open duplicates are merged: the oldest is kept, takes the newest copy's type if it is Unsorted itself, and the other copies are deleted. Running it again changes nothing.
- [ ] Tests cover case and spacing, punctuation and plurals not matching, Done items, the Unsorted-gets-the-type and different-type cases, no prompt for an unprefixed duplicate, repeats in one message, and the startup cleanup through a file-based store.
