# 03: Type prompt for unprefixed items

**What to build:** When a message adds items without a prefix, the bot's reply carries [🍎 Food] [🛒 Stuff] [✅ Do] buttons. One prompt covers every unprefixed line of that message. Tapping a type files those items and edits the reply to say where they went ("Added to 🍎 Food: milk"). Prefixed lines in the same message are filed immediately, without the prompt. An old prompt can never overwrite a type chosen later. Spec user stories 7, 8, 10, 11, 33, 37.

**Blocked by:** 02 (Item types via prefixes, grouped list, /move)

**Status:** ready-for-agent

- [ ] Sending "milk" returns a reply with three type buttons, and the item is already saved as Unsorted.
- [ ] Tapping a type in that reply files the item and edits the reply to "Added to <type>: milk".
- [ ] A message with several unprefixed lines gets one prompt, and one tap files all of them.
- [ ] In a mixed message, prefixed lines are filed straight away and only the unprefixed ones wait for the prompt.
- [ ] Items added by one message share a key that the prompt's buttons refer to, so the button data stays within Telegram's 64-byte limit for any number of lines.
- [ ] Tapping a prompt after some of its items were moved with `/move` or ticked off changes only the items that are still Unsorted and not Done.
- [ ] Tapping a prompt whose items are all gone or already sorted answers "That item is no longer on your list" and changes nothing.
- [ ] Tests tap buttons by feeding back the button data from earlier returned actions, never by building it themselves.
