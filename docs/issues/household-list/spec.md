# Spec: Household list

Status: ready-for-agent

## Problem Statement

I want to share my list with my wife. Today each chat with the bot has its own List, so if she starts using the bot she gets an empty list of her own, and my items stay private to my chat. A group chat would only half work: the bot wouldn't see plain text there without extra setup, every message in the group would become an item, and we'd each still keep a private List on the side. Once I share, I want everything to be common, with no private parts.

With two of us adding things, the same item will get added twice ("milk" and "Milk"), and item numbers will move under us: she adds `f eggs` while I'm reading the list, and my `/done 5` ticks off the wrong item with no way back.

## Solution

The bot holds one **List**, shared by the **Household**: everyone in `BTW_ALLOWED_USERS`. Each of us uses our own private chat with the bot and sees and changes the same items. Adding someone to the allow-list is the sharing; there's no share command. My existing items become the household List as they are. Group chats are not supported: the bot says it only works in private chats.

Adding an item whose text matches an open item, ignoring case and spacing, adds nothing: the bot says it's already on the list. Duplicates already in the database are cleaned up once. `/done` offers the same Undo that tapping an item does.

See `docs/adr/0001-one-list-per-household.md` and the glossary's Household, List and Duplicate.

## User Stories

### One List for the household

1. As the user, I want my wife to see and change the same List as me from her own private chat with the bot, so that we share one shopping and to-do list.
2. As the user, I want sharing to be nothing more than adding her user ID to `BTW_ALLOWED_USERS`, so that there is no share step to learn.
3. As the user, I want my existing items to become the household List unchanged, so that nothing has to be retyped.
4. As the user, I want items she adds to appear when I next open `/list`, without a message to me for each one, so that a shopping brain-dump doesn't ping me all day.
5. As the user, I want items to stay anonymous in the list, so that it looks the same as today.
6. As the user, I want tapping an item in an old list message that the other person already ticked off to say it's no longer on the list, so that stale messages never do harm.
7. As the user, I want an Undo button to work from my chat even if the item was added from hers, so that the List behaves the same whoever touched it.
8. As the user, I want the help text and README to say the list is shared by everyone allowed to use the bot, so that nobody expects private items.

### Private chats only

9. As the user, I want the bot to answer a message or button tap from a group chat with "I only work in private chats" and do nothing else, so that a group never becomes a second, confusing way in.

### Outsiders

10. As the user, I want a button tap from someone not in the household to be answered with "You're not on this bot's list", so that their spinner clears; their messages stay silently ignored.

### Duplicates

11. As the user, I want sending `milk` while `Milk` is open to add nothing and reply "Already on the list under 🍎 Food: Milk", so that two of us can't add the same thing twice.
12. As the user, I want the match to ignore case and extra spaces but nothing else, so that `egg` and `eggs`, or `milk` and `milk.`, are still separate items.
13. As the user, I want an item that's Done not to count, so that I can add `milk` again after buying it.
14. As the user, I want `f milk` to give an open Unsorted `milk` the Food type and reply "Moved to 🍎 Food: milk", so that a prefix fills in what was missing.
15. As the user, I want `s milk` to leave an open Food `milk` where it is and reply "Already on the list under 🍎 Food: milk", so that a duplicate never re-files an item; `/move` is there if I meant it.
16. As the user, I want an unprefixed duplicate of a typed item to get no type prompt, so that I'm not asked about something already filed.
17. As the user, I want duplicate lines within one message to be added once, with the reply noting the skipped lines, so that pasting a list with repeats is harmless.
18. As the user, I want duplicates already in the database to be merged once, keeping the oldest item, so that the household List starts clean.

### Undo for /done

19. As the user, I want `/done 2 5` to send an ↩️ Undo button for each item it ticked off, like tapping does, so that a number that moved under me, or a typo, can be put right.

## Implementation Decisions

### Store

- Items are no longer scoped by chat: every store operation drops its chat argument, and open items, lookups, batches and undo all work on the one List. Item IDs stay opaque strings.
- The `chat_id` column stays (dropping or re-defaulting a column in SQLite means rebuilding the table) but nothing reads it any more; new rows write 0 into it. Items from every chat already in the database therefore form the household List with no migration step.
- A **duplicate key** for a text: casefolded, with runs of whitespace collapsed to one space and the ends trimmed. It lives in one place in the store or handler, and both adding and the cleanup use it.
- Adding a batch skips lines whose key matches an open item or an earlier line of the same batch, and reports, for each skipped line, the open item that stands for it. When the open item is Unsorted and the line has a type, the open item takes that type.
- A one-time cleanup on startup merges open duplicates: in each group of open items with the same key, the oldest is kept, takes a type from the newest typed copy if it is Unsorted itself, and the other copies are deleted from the database. It's idempotent, so running it on every start is fine. Deleting is acceptable here: the rows are copies, and the nightly backups hold the previous state.

### Handler

- The handler still replies to the chat an update came from, but reads and writes the one List.
- Updates from a chat whose type isn't `private` get "I only work in private chats": a reply for a message, an answered tap with that notice for a button. Nothing is stored or changed.
- Add replies list what was added and, separately, each duplicate with where the existing item is ("Already on the list under 🍎 Food: Milk", "Moved to 🍎 Food: milk"). The type prompt appears only if at least one new Unsorted item was added, and covers only those.
- `/done` replies as today ("Done: ...") and additionally sends one "✔️ text" message with an ↩️ Undo button per item, the same messages and buttons a tap produces, all sharing that `/done`'s tick.
- Help text and wording move from "your list" to "the list".

### Polling loop

- The allow-list check stays in the loop, but turns a rejected update into actions through a small function: a button tap from an outsider yields one answer-tap action with "You're not on this bot's list"; a message yields nothing. Every tap still gets exactly one answer.

## Testing Decisions

- As before, tests drive the handler with fake updates and assert on returned actions, never on the database or button data format.
- Household tests send updates from two different private chats against one store: an item added in one shows up in the other's `/list`; a tap or Undo from one chat acts on an item added from the other; a stale tap after the other chat ticked the item off says it's no longer on the list.
- A group-chat message and a group-chat tap each yield only the private-chats notice, and the list is unchanged.
- Duplicate tests cover case and spacing, punctuation and plurals not matching, Done items not counting, the Unsorted-gets-the-type case, the different-type case, no prompt for an unprefixed duplicate, and repeats within one message.
- The cleanup is tested through a file-based store: create duplicates in a database (as the existing pre-type-column persistence test does), reopen it, and check `/list` shows each once, with the type kept.
- The outsider function is unit-tested: a tap yields exactly one answer-tap action with the notice, a message yields none.
- `/done` tests take an Undo button from its returned actions, tap it, and check the item is back.

## Out of Scope

- Several Lists on one instance, linked Lists, share codes, or a List per chat.
- Group chats in any form.
- Notifications about the other person's changes.
- Showing who added or ticked off an item.
- Fuzzy duplicate matching (plurals, punctuation, typos).
- Discarding items (the glossary has the term; the feature comes later).
- Stopping `/done` when the list changed since it was last shown.
