# 03: Answer outsiders' taps

**What to build:** A button tap from someone not in `BTW_ALLOWED_USERS` is answered with "You're not on this bot's list", so their spinner clears. Their messages stay silently ignored. Spec user story 10.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] A small function turns a rejected update into actions: one answer-tap action with the notice for a tap, none for a message.
- [ ] The polling loop executes those actions instead of just skipping the update, and still logs the rejection.
- [ ] Unit tests cover the function for a tap and for a message.
