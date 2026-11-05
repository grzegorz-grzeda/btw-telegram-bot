import unittest

from btw_bot.actions import AnswerTap, SendMessage
from btw_bot.db import TodoStore
from btw_bot.handlers import HELP, handle

CHAT = 100
OTHER_CHAT = 200
USER = 7


def text_update(text, chat_id=CHAT):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "from": {"id": USER},
            "chat": {"id": chat_id},
            "text": text,
        },
    }


def tap_update(data, chat_id=CHAT, tap_id="tap-1"):
    return {
        "update_id": 2,
        "callback_query": {
            "id": tap_id,
            "from": {"id": USER},
            "message": {"message_id": 11, "chat": {"id": chat_id}, "text": "old"},
            "data": data,
        },
    }


class HandleTest(unittest.TestCase):
    def setUp(self):
        self.store = TodoStore(":memory:")
        self.addCleanup(self.store.close)

    def send(self, text, chat_id=CHAT):
        """Send a text message; expect exactly one reply to that chat and return its text."""
        actions = handle(self.store, text_update(text, chat_id))
        self.assertEqual(len(actions), 1, actions)
        (action,) = actions
        self.assertIsInstance(action, SendMessage)
        self.assertEqual(action.chat_id, chat_id)
        return action.text

    def test_plain_text_adds_item(self):
        self.assertEqual(self.send("buy milk"), "Added: buy milk")
        self.assertEqual(self.send("/list"), "1. buy milk")

    def test_multiline_message_adds_each_line(self):
        self.assertEqual(self.send("eggs\n\n  bread  \ncheese"), "Added 3 items.")
        self.assertEqual(self.send("/list"), "1. eggs\n2. bread\n3. cheese")

    def test_add_command(self):
        self.assertEqual(self.send("/add call mom"), "Added: call mom")
        self.assertEqual(self.send("/add"), "Nothing to add. Send me some text.")

    def test_empty_list(self):
        self.assertEqual(self.send("/list"), "Your list is empty.")

    def test_done_removes_item_and_renumbers(self):
        self.send("a\nb\nc")
        self.assertEqual(self.send("/done 2"), "Done: b")
        self.assertEqual(self.send("/list"), "1. a\n2. c")

    def test_done_several_items_uses_numbers_from_before(self):
        self.send("a\nb\nc\nd")
        self.assertEqual(self.send("/done 3, 1"), "Done: a; c")
        self.assertEqual(self.send("/list"), "1. b\n2. d")

    def test_done_invalid_input_changes_nothing(self):
        self.send("a\nb")
        self.assertIn("No item number 5", self.send("/done 1 5"))
        self.assertIn("Usage", self.send("/done"))
        self.assertIn("Usage", self.send("/done x"))
        self.assertEqual(self.send("/list"), "1. a\n2. b")

    def test_chats_have_separate_lists(self):
        self.send("mine")
        self.send("theirs", chat_id=OTHER_CHAT)
        self.assertEqual(self.send("/list"), "1. mine")
        self.assertEqual(self.send("/list", chat_id=OTHER_CHAT), "1. theirs")

    def test_command_with_bot_mention(self):
        self.send("a")
        self.assertEqual(self.send("/LIST@BtwBot"), "1. a")

    def test_help_and_unknown(self):
        self.assertEqual(self.send("/start"), HELP)
        self.assertEqual(self.send("/help"), HELP)
        self.assertIn("Unknown command", self.send("/nope"))

    def test_non_text_message_gets_no_reply(self):
        update = text_update("ignored")
        del update["message"]["text"]
        self.assertEqual(handle(self.store, update), [])

    def test_unknown_tap_is_answered_exactly_once_and_changes_nothing(self):
        self.send("a")
        for data in ("", "garbage", "x" * 64):
            actions = handle(self.store, tap_update(data, tap_id="t42"))
            answers = [a for a in actions if isinstance(a, AnswerTap)]
            self.assertEqual(len(answers), 1, actions)
            self.assertEqual(answers[0].tap_id, "t42")
            self.assertEqual(len(actions), 1, actions)
        self.assertEqual(self.send("/list"), "1. a")


class PersistenceTest(unittest.TestCase):
    def test_items_survive_reopen(self):
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "btw.db")
            store = TodoStore(path)
            handle(store, text_update("persist me"))
            store.close()

            store = TodoStore(path)
            self.addCleanup(store.close)
            (reply,) = handle(store, text_update("/list"))
            self.assertEqual(reply.text, "1. persist me")


if __name__ == "__main__":
    unittest.main()
