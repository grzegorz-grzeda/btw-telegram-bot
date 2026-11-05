# One List per household, not per chat

A bot instance holds exactly one List, shared by everyone in `BTW_ALLOWED_USERS` (the household), each working from their own private chat with the bot. Adding someone to the allow-list *is* sharing: once shared, nothing is private. The bot answers only in private chats.

## Considered Options

- **One List per chat, shared through a group chat.** Rejected: plain text only reaches a bot in a group with privacy mode turned off, every message in the group becomes an item, and each person still keeps a separate private List, which is exactly the "private part" we didn't want.
- **Lists linked between chats** (for example `/share` handing out a join code). Rejected: it only pays off when one instance holds several unrelated Lists, and the bot is for one household.

## Consequences

- A friend can't keep a List of their own on this instance; they run their own bot. Going back to several Lists would mean scoping items again and deciding who belongs to which List.
- Item numbers can shift while two people use the List at once, so `/done` offers an Undo like a tap does.
