# Spec: Item types, tap-friendly list, Docker deployment and backups

Status: ready-for-agent

## Problem Statement

My list mixes everything I jot down: groceries, things to buy elsewhere and things to do. In the supermarket I scroll past "call the dentist" looking for the milk, and at home I scroll past shopping to find what I need to do. Ticking items off means typing `/done 3`, which is clumsy on a phone, and a mistyped number ticks off the wrong item with no way back.

The bot also runs on my Raspberry Pi as a bare Python process under systemd, with the list in one SQLite file on the SD card. If the card dies, the list is gone. I may move the bot to my VPS later, and I want that to be a copy and a restart, not a reinstall.

## Solution

Every item gets a type: 🍎 **Food** (groceries to buy), 🛒 **Stuff** (non-food things to buy) or ✅ **Do** (anything that isn't buying). I set it with a one-letter prefix (`f milk`, `s bulbs`, `d call dentist`) or, if I don't, by tapping one of three buttons the bot offers. Until I choose, the item is **Unsorted**, so nothing I send is lost or filed wrongly.

There is still one **List** per chat. `/list` shows it grouped by type, with one running number, a row of filter buttons to narrow it to a single type, and one button per item. Tapping an item ticks it off, and the bot offers an Undo. Tapping an Unsorted item lets me give it a type. Typed commands (`/done 3`, `/move 3 s`) keep working, and the main commands appear in Telegram's "/" menu.

The bot runs in Docker on both the Pi and the VPS, with the database in a plain folder next to the compose file. A nightly backup writes a snapshot of the database and keeps two weeks of them, and a host cron job copies them to Google Drive. Moving machines means stopping the old container, copying the folder and starting the new one.

## User Stories

### Adding items

1. As the user, I want to send `f milk` and have "milk" added as Food, so that groceries are filed with no extra taps.
2. As the user, I want to send `s light bulbs` and have it added as Stuff, so that non-food shopping is kept apart from groceries.
3. As the user, I want to send `d call dentist` and have it added as Do, so that tasks are kept apart from shopping.
4. As the user, I want the prefix letter to work in either case (`F milk`), so that my phone's auto-capitalisation doesn't break it.
5. As the user, I want text that merely starts with a word like "do" or "food" ("do the dishes", "food for the dog") to be saved whole, so that my words are never chopped up by accident.
6. As the user, I want an item without a prefix to be saved straight away as Unsorted, so that nothing I send is lost if I put the phone away.
7. As the user, I want the bot to reply to an unprefixed item with [🍎 Food] [🛒 Stuff] [✅ Do] buttons, so that I can give it a type with one tap without remembering prefixes.
8. As the user, I want the reply to change to "Added to 🍎 Food: milk" once I tap a type, so that I can see where it went.
9. As the user, I want each line of a multi-line message to become its own item with its own optional prefix, so that I can dump several things at once.
10. As the user, I want all the unprefixed lines of one message to share a single type prompt, so that one tap files "bread, butter, jam" together.
11. As the user, I want the prefixed lines of a mixed message to be filed immediately and only the rest to wait for the prompt, so that I only answer for what I didn't specify.
12. As the user, I want a reply that says what was added and where, so that I can trust the bot understood me.
13. As the user, I want `/add text` to keep working the same way as plain text, prefixes included, so that the old command still does something sensible.
14. As the user, I want an empty message or a prefix with nothing after it to be rejected politely, so that I don't get blank items.

### Viewing the list

15. As the user, I want `/list` to show my items grouped under 🍎 Food, 🛒 Stuff, ✅ Do and ❓ Unsorted, in that order, so that I can scan one kind of thing at a time.
16. As the user, I want empty groups to be left out, so that the list stays short.
17. As the user, I want one running number across all the groups, so that `/done 3` always means one specific item.
18. As the user, I want items within a group to stay in the order I added them, so that the list feels stable.
19. As the user, I want a row of filter buttons [All] [🍎] [🛒] [✅] at the top of the list message, so that I can narrow the list to one type without typing.
20. As the user, I want tapping a filter to redraw the same message rather than send a new one, so that my chat doesn't fill up with copies of my list.
21. As the user, I want a filtered view to keep the same item numbers as the full list, so that a number I saw in one view still works in the other.
22. As the user, I want to see which filter is active, so that I know whether I'm looking at everything.
23. As the user, I want `/list food` (or `/list f`, and the same for stuff and do) to open the list already filtered, so that typing still works if I prefer it.
24. As the user, I want a filtered view with no items to say so ("No Food items."), so that an empty screen isn't confusing.
25. As the user, I want "Your list is empty." when there's nothing at all, so that I know the bot is working.

### Ticking items off

26. As the user, I want one full-width button per item in the list, showing the item's text, so that I tap the item itself rather than a number.
27. As the user, I want tapping a typed item to mark it Done and redraw the list in place, keeping the current filter, so that I can work through my shopping one tap at a time.
28. As the user, I want a short "✔️ milk" message with a [↩️ Undo] button after each tick, so that I can fix a mistaken tap.
29. As the user, I want Undo to bring the item back with the type it had, so that it returns to the right group.
30. As the user, I want the Undo message to change to "↩️ Restored: milk" after I tap it, so that I don't tap it twice.
31. As the user, I want `/done 3` and `/done 1 3` to keep working, so that I can still use commands.
32. As the user, I want `/done N` to work on Unsorted items too, so that I can tick off something without sorting it first.
33. As the user, I want a tap on a button for an item that's already done or gone to answer "That item is no longer on your list", so that stale buttons fail clearly instead of silently.

### Sorting and re-filing

34. As the user, I want tapping an Unsorted item in the list to show the type buttons for that item in place, so that I can sort leftovers later, long after the original prompt has scrolled away.
35. As the user, I want the list to come back, with the item in its new group, once I pick a type, so that I can carry on where I was.
36. As the user, I want a way to go back from that type picker without choosing, so that a mistaken tap doesn't trap me.
37. As the user, I want tapping the original prompt after I've already sorted those items elsewhere to do no harm, so that old buttons can't undo my later choices.
38. As the user, I want `/move 3 s` to change item 3's type, so that I can fix "batteries" filed under Food by mistake.
39. As the user, I want `/move` with a wrong number or type letter to explain the right usage, so that I can correct myself.
40. As the user, I want the items I had before this change to show up as Unsorted, so that nothing disappears and I can sort them with a tap.

### Commands and help

41. As the user, I want `/list`, `/move` and `/help` to appear in Telegram's "/" menu with short descriptions, so that I never have to remember command names.
42. As the user, I want `/help` to explain the prefixes, the types and the buttons in a few lines, so that I can learn the bot from inside Telegram.
43. As the user, I want commands addressed to the bot by name (`/list@MyBot`) to work, so that the bot also behaves in group chats.
44. As the owner, I want button taps from users outside the allowed list to be ignored, just like their messages, so that the allow-list can't be bypassed through buttons.

### Deployment

45. As the owner, I want to run the bot with one `docker compose up -d --build` from the repo checkout, so that the Pi and the VPS are deployed the same way.
46. As the owner, I want the image to need nothing beyond the Python standard library, so that it builds in seconds on the Pi.
47. As the owner, I want the database in a plain folder next to the compose file, so that backing up or moving it is copying a file.
48. As the owner, I want the container to restart by itself after a crash or reboot, so that the bot stays up without supervision.
49. As the owner, I want to read the bot's logs with `docker compose logs -f`, so that I can see why something failed.
50. As the owner, I want configuration to keep coming from the `.env` file, so that nothing about the token or allow-list changes.
51. As the owner, I want the README to describe deploying, updating (`git pull` then rebuild) and moving from the Pi to the VPS, so that I can do it months from now without remembering details.

### Backups

52. As the owner, I want a command inside the container that writes a consistent snapshot of the database while the bot runs, so that a backup never catches a half-written file.
53. As the owner, I want snapshots named by date, with one per day and a re-run on the same day replacing that day's copy, so that I can find the one I need.
54. As the owner, I want snapshots older than 14 days to be deleted automatically, so that the backup folder doesn't grow forever.
55. As the owner, I want the README to give the host cron line that runs the backup and syncs the folder to Google Drive with rclone, so that my backups live off the machine.
56. As the owner, I want the README to describe restoring from a snapshot, so that recovery is a few commands when I'm stressed.

## Implementation Decisions

### Domain and storage

- The vocabulary is the one in the glossary: List, Item, Type (Food, Stuff, Do), Unsorted, Done. Unsorted is the absence of a type, not a fourth type.
- Items gain a nullable type column, where an empty value means Unsorted. The schema is still created on startup, and a database without the column has it added on startup. Existing items therefore become Unsorted with no separate migration step.
- Items added by one message share a **batch** key stored with them. The type prompt for that message refers to the batch, so one tap can type all of them. This is needed because Telegram limits button data to 64 bytes, too small to list several item IDs.
- Applying a type from a batch prompt changes only the items in that batch that are still Unsorted and not Done. A later `/move` or in-list sort is therefore never overwritten by an old prompt (story 37).
- The store's interface treats item IDs as opaque strings everywhere outside the store, including button data. This keeps a future non-SQLite store possible without touching the handler.
- The store gains operations to:
  - list open items with their type
  - set the type of one item
  - set the type of the still-Unsorted items in a batch
  - mark items done
  - restore a done item
  - look up a single item, so stale taps can be detected
- Done items stay in the database (as today), which is what makes Undo possible.

### Handler (the main seam)

- The handler's input changes from (chat, text) to a raw Telegram update, either a text message or a button tap. It returns a list of **actions** instead of a reply string. It never calls Telegram itself.
- The actions are:
  - send a message (text plus an optional button layout)
  - edit an existing message (text plus an optional button layout)
  - answer a button tap (optional short notice)
- Every button tap yields exactly one "answer tap" action, so Telegram's loading spinner always clears.
- Button data is a compact, versionless string that encodes the action and its target (an item ID, a batch key, a filter or a type), and stays within 64 bytes. The handler both writes and parses it. Nothing else depends on its format.
- Every list button carries the filter it was drawn with, so a tap redraws the list with the same filter.
- Prefix rule: a line whose first character is f, s or d (any case), followed by a space and then non-empty text, gets that type, with the prefix removed. Everything else is saved whole as Unsorted.
- List layout:
  - groups in the order Food, Stuff, Do, Unsorted, with empty groups omitted
  - one running number in that order, computed from the full list, so filtered views show the same numbers
  - a filter row on top that marks the active filter
  - one item button per row
- `/done N` and `/move N <f|s|d>` resolve numbers against the full list, in the order shown. `/done` keeps resolving all numbers before marking any.
- `/list` accepts an optional filter argument: food, stuff or do, or the letters f, s, d.
- A tap on an Unsorted item edits the list message to show a type picker for that item, with a back button. Choosing a type sets it and redraws the list in the same message.
- A tap on a typed item marks it done, redraws the list in place and sends a separate "✔️ text" message with an Undo button. Undo restores the item and edits that message to say so. It does not redraw older list messages.
- A tap that refers to an item that is done, missing or belongs to another chat answers with "That item is no longer on your list" and changes nothing.
- The help text is rewritten to cover the prefixes, the types, the buttons and `/move`.

### Telegram client and polling loop

- The client gains:
  - message editing
  - answering button taps
  - registering the command menu
  - support for a button layout on sent and edited messages
- Polling asks for both messages and button taps.
- The polling loop's only new job is to execute the returned actions in order. The allow-list check covers the sender of button taps as well as messages.
- At startup the bot registers `/list`, `/move` and `/help` with short descriptions. A failure here is logged and doesn't stop the bot.
- Telegram limits inline keyboards to 100 buttons. The list shows at most 90 item buttons. Items beyond that still appear in the text and can be ticked off with `/done N`. Long list text is still split across messages, with the buttons attached to the last part. Edits can't be split, so an edit that would exceed the length limit is sent as a new list message instead.

### Deployment

- A container image based on Python 3.14 slim runs `python -m btw_bot`, with no dependencies to install. It runs as a non-root user and with unbuffered output, so logs appear immediately.
- A compose file defines one bot service:
  - restart unless stopped
  - environment from `.env`
  - a bind-mounted `./data` folder as the data directory
  - the database path set to the database file inside that folder
- The images are built on the device. There's no registry or CI.
- The systemd unit is deleted.
- CLAUDE.md drops the "compatible with the Pi's system Python" constraint, because the container pins Python, and describes the Docker deployment instead.
- Exactly one instance runs at a time, because Telegram allows one poller per bot token.

### Backups (the second seam)

- A backup module, runnable as a command inside the container, takes the database path, a backup folder and today's date. It writes a snapshot named with the date using SQLite's online backup API, so it's consistent while the bot writes. It then deletes snapshots older than 14 days, judged by the date in the name.
- By default the backup folder is a `backups` folder next to the database, so it lands in the bind-mounted data folder on the host.
- `rclone` and its Google Drive credentials live on the host, not in the image. The README documents:
  - the nightly cron line (run the backup in the container, then `rclone sync` the backups folder to `gdrive:btw-backups`)
  - restoring: stop the container, copy a snapshot over the database file, start the container again

## Testing Decisions

- A good test drives the bot only from outside, the way Telegram would. It feeds the handler fake updates (text messages and button taps) and checks the actions that come back: the texts, the button labels and which message is sent or edited. It must not inspect the database directly or depend on the format of button data. To tap a button, a test takes the data from a button in an earlier returned action and feeds it back as a tap. Any change to the data format then stays invisible to tests.
- **Handler tests** (main seam) use an in-memory store and cover every story in "Adding items" through "Commands and help" except the command menu registration. That includes:
  - prefixes and case
  - non-prefix words like "do the dishes"
  - multi-line batches and the shared prompt
  - grouped numbering and filters with stable numbers
  - tap to mark done, and Undo restoring the type
  - sorting Unsorted items in the list, with the back button
  - `/move`
  - stale buttons, including a batch prompt tapped after one of its items was re-filed
  - Unsorted items from a database created before the type column existed, built through a file-based store as in the existing persistence test
  - a tap always yielding exactly one answer action
- **Backup tests** (second seam) use a temporary folder and an injected date. They check that a snapshot is written and readable with the same items, that a same-day re-run replaces it, and that snapshots older than 14 days are removed while newer ones are kept.
- The existing message-splitting tests stay.
- The polling loop, the HTTP client, the command menu registration, Docker, compose and cron are not unit-tested. They're verified by building the image and running the bot against a real bot token.
- Prior art: the existing handler tests (in-memory store, a `send` helper, assertions on reply text) and the persistence test (temp-dir database reopened). Those handler tests get rewritten against the update-in, actions-out signature.

## Out of Scope

- Webhook mode. The bot keeps long polling on both the Pi and the VPS. The actions-returning handler keeps a later webhook entry point cheap.
- MongoDB or any other store. Durability comes from backups. The opaque string item IDs keep a later store change possible.
- Custom or user-defined types, and a combined "Buy" (Food + Stuff) filter.
- Building images in CI or pushing to a registry.
- A separate development bot or running more than one instance.
- Editing an item's text, reminders, due dates and sharing a List between chats.
- Redrawing older list messages after an Undo.

## Further Notes

- This spec replaces the systemd deployment described in the README and CLAUDE.md. Both need updating as part of the work.
- The bind-mounted data folder must be writable by the container's non-root user. The README should note matching ownership on the host, for example by creating `./data` before the first start.
- Moving from the Pi to the VPS: stop the container on the Pi, copy `./data` and `.env` to the VPS, then run `docker compose up -d --build` there. Never run both at once.
