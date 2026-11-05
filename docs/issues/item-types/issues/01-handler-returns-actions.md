# 01: Handler returns actions (prefactor)

**What to build:** Change the bot's core so the handler receives a raw Telegram update (a text message or a button tap) and returns a list of actions (send a message, edit a message, answer a tap) instead of a reply string. The polling loop executes those actions. Users see no change: every existing command behaves exactly as before. This is the seam that every later ticket tests through, and it keeps a future webhook entry point cheap. See the spec: Implementation Decisions, "Handler" and "Telegram client and polling loop".

**Blocked by:** None (can start immediately)

**Status:** ready-for-agent

- [ ] The handler takes a Telegram update and returns actions. It never calls Telegram itself.
- [ ] Actions cover sending a message, editing an existing message and answering a button tap, each with an optional button layout where Telegram allows one.
- [ ] Every button tap produces exactly one "answer tap" action (unknown taps included), so Telegram's spinner always clears.
- [ ] The Telegram client can send with a button layout, edit a message's text and buttons, and answer a tap. Polling asks for both messages and button taps.
- [ ] The polling loop executes the returned actions in order. The allow-list check applies to the sender of button taps as well as messages.
- [ ] Item IDs are opaque strings everywhere outside the store.
- [ ] The existing handler tests are rewritten to drive the handler with fake updates and assert on the returned actions. Adding, `/list`, `/done`, `/help` and persistence behave the same as before, and all tests pass.
