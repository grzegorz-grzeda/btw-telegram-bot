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
        self.assertEqual(self.send("buy milk"), "Added to ❓ Unsorted: buy milk")
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. buy milk")

    def test_multiline_message_adds_each_line(self):
        self.assertEqual(
            self.send("eggs\n\n  bread  \ncheese"),
            "Added 3 items:\n❓ Unsorted: eggs; bread; cheese",
        )
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. eggs\n2. bread\n3. cheese")

    def test_add_command(self):
        self.assertEqual(self.send("/add call mom"), "Added to ❓ Unsorted: call mom")
        self.assertEqual(self.send("/add f milk"), "Added to 🍎 Food: milk")
        self.assertEqual(self.send("/add"), "Nothing to add. Send me some text, e.g. f milk")

    def test_empty_list(self):
        self.assertEqual(self.send("/list"), "Your list is empty.")

    def test_done_removes_item_and_renumbers(self):
        self.send("a\nb\nc")
        self.assertEqual(self.send("/done 2"), "Done: b")
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. a\n2. c")

    def test_done_several_items_uses_numbers_from_before(self):
        self.send("a\nb\nc\nd")
        self.assertEqual(self.send("/done 3, 1"), "Done: a; c")
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. b\n2. d")

    def test_done_invalid_input_changes_nothing(self):
        self.send("a\nb")
        self.assertIn("No item number 5", self.send("/done 1 5"))
        self.assertIn("Usage", self.send("/done"))
        self.assertIn("Usage", self.send("/done x"))
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. a\n2. b")

    def test_chats_have_separate_lists(self):
        self.send("mine")
        self.send("theirs", chat_id=OTHER_CHAT)
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. mine")
        self.assertEqual(self.send("/list", chat_id=OTHER_CHAT), "❓ Unsorted\n1. theirs")

    def test_command_with_bot_mention(self):
        self.send("a")
        self.assertEqual(self.send("/LIST@BtwBot"), "❓ Unsorted\n1. a")

    def test_help_and_unknown(self):
        self.assertEqual(self.send("/start"), HELP)
        self.assertEqual(self.send("/help"), HELP)
        for topic in ("f milk", "s bulbs", "d call dentist", "❓ Unsorted", "/move 3 s"):
            self.assertIn(topic, HELP)
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
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. a")


    def test_prefix_files_item_under_type(self):
        self.assertEqual(self.send("f milk"), "Added to 🍎 Food: milk")
        self.assertEqual(self.send("S bulbs"), "Added to 🛒 Stuff: bulbs")
        self.assertEqual(self.send("d call dentist"), "Added to ✅ Do: call dentist")
        self.assertEqual(
            self.send("/list"),
            "🍎 Food\n1. milk\n\n🛒 Stuff\n2. bulbs\n\n✅ Do\n3. call dentist",
        )


    def test_words_that_look_like_prefixes_are_saved_whole(self):
        self.assertEqual(self.send("do the dishes"), "Added to ❓ Unsorted: do the dishes")
        self.assertEqual(self.send("food for the dog"), "Added to ❓ Unsorted: food for the dog")
        self.assertEqual(self.send("f"), "Added to ❓ Unsorted: f")
        self.assertEqual(
            self.send("/list"), "❓ Unsorted\n1. do the dishes\n2. food for the dog\n3. f"
        )

    def test_list_groups_by_type_keeping_added_order_and_one_running_number(self):
        for text in ("loose end", "d walk dog", "f milk", "s bulbs", "f eggs", "d pay rent"):
            self.send(text)
        self.assertEqual(
            self.send("/list"),
            "🍎 Food\n1. milk\n2. eggs\n\n"
            "🛒 Stuff\n3. bulbs\n\n"
            "✅ Do\n4. walk dog\n5. pay rent\n\n"
            "❓ Unsorted\n6. loose end",
        )

    def test_done_uses_grouped_numbers_including_unsorted(self):
        for text in ("loose end", "d walk dog", "f milk"):
            self.send(text)
        self.assertEqual(self.send("/done 1 3"), "Done: milk; loose end")
        self.assertEqual(self.send("/list"), "✅ Do\n1. walk dog")

    def test_multiline_lines_have_their_own_prefixes_and_reply_says_where(self):
        self.assertEqual(
            self.send("f milk\nbread\nS bulbs\nF eggs\nd call mum"),
            "Added 5 items:\n🍎 Food: milk; eggs\n🛒 Stuff: bulbs\n✅ Do: call mum\n❓ Unsorted: bread",
        )

    def test_prefix_with_nothing_after_it_is_rejected(self):
        self.assertEqual(self.send("f   "), "Nothing to add. Send me some text, e.g. f milk")
        self.assertEqual(self.send("/add d "), "Nothing to add. Send me some text, e.g. f milk")
        self.assertEqual(self.send("s \nf milk"), "Added to 🍎 Food: milk")
        self.assertEqual(self.send("/list"), "🍎 Food\n1. milk")

    def test_move_changes_an_items_type(self):
        self.send("f milk\nf batteries\nloose end")
        self.assertEqual(self.send("/move 2 s"), "Moved to 🛒 Stuff: batteries")
        self.assertEqual(self.send("/move 3 D"), "Moved to ✅ Do: loose end")
        self.assertEqual(
            self.send("/list"), "🍎 Food\n1. milk\n\n🛒 Stuff\n2. batteries\n\n✅ Do\n3. loose end"
        )

    def test_move_with_wrong_number_or_type_explains_usage_and_changes_nothing(self):
        self.send("f milk")
        for bad in ("/move", "/move 1", "/move 2 s", "/move 0 s", "/move x s", "/move 1 x", "/move 1 s d"):
            self.assertIn("Usage: /move 3 s", self.send(bad), bad)
        self.assertEqual(self.send("/list"), "🍎 Food\n1. milk")

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
            self.assertEqual(reply.text, "❓ Unsorted\n1. persist me")

    def test_database_from_before_types_opens_with_items_unsorted(self):
        import os
        import sqlite3
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "btw.db")
            # The schema as it was before item types existed.
            conn = sqlite3.connect(path)
            conn.executescript(
                """
                CREATE TABLE items (
                    id         INTEGER PRIMARY KEY,
                    chat_id    INTEGER NOT NULL,
                    text       TEXT    NOT NULL,
                    done       INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT    NOT NULL DEFAULT (datetime('now'))
                );
                INSERT INTO items (chat_id, text) VALUES (100, 'old item');
                INSERT INTO items (chat_id, text, done) VALUES (100, 'old done', 1);
                """
            )
            conn.commit()
            conn.close()

            store = TodoStore(path)
            self.addCleanup(store.close)
            handle(store, text_update("f milk"))
            (reply,) = handle(store, text_update("/list"))
            self.assertEqual(reply.text, "🍎 Food\n1. milk\n\n❓ Unsorted\n2. old item")


if __name__ == "__main__":
    unittest.main()
