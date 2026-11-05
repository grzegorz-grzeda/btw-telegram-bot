# 12: Private chats only

**What to build:** A message or button tap from any chat that isn't private gets "I only work in private chats" and changes nothing. [Spec](../specs/household-list.md) user story 9.

**Blocked by:** none

**Status:** ready-for-agent

- [ ] A message from a group or supergroup chat yields one reply with the notice, and nothing is stored.
- [ ] A button tap from a non-private chat yields exactly one answer-tap action with the notice, and nothing changes.
- [ ] The README says the bot works only in private chats.
- [ ] Tests feed group-chat updates and check the actions and that `/list` in a private chat is unchanged.
