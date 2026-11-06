import unittest

from btw_bot.actions import AnswerTap, EditMessage, SendMessage
from btw_bot.db import TodoStore
from btw_bot.handlers import HELP, PRIVATE_ONLY, handle

CHAT = 100
OTHER_CHAT = 200
GROUP_CHAT = -300
USER = 7


def text_update(text, chat_id=CHAT, chat_type="private"):
    return {
        "update_id": 1,
        "message": {
            "message_id": 10,
            "from": {"id": USER},
            "chat": {"id": chat_id, "type": chat_type},
            "text": text,
        },
    }


def tap_update(data, chat_id=CHAT, tap_id="tap-1", chat_type="private"):
    return {
        "update_id": 2,
        "callback_query": {
            "id": tap_id,
            "from": {"id": USER},
            "message": {
                "message_id": 11,
                "chat": {"id": chat_id, "type": chat_type},
                "text": "old",
            },
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
        self.assertEqual(self.send("/list"), "The list is empty.")

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

    def test_group_message_gets_notice_and_changes_nothing(self):
        self.send("mine")
        for chat_type in ("group", "supergroup"):
            for text in ("buy milk", "/done 1", "/add eggs", "/move 1 f"):
                actions = handle(self.store, text_update(text, GROUP_CHAT, chat_type))
                self.assertEqual(actions, [SendMessage(GROUP_CHAT, PRIVATE_ONLY)])
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. mine")

    def test_group_tap_gets_notice_and_changes_nothing(self):
        self.send("mine")
        (reply,) = handle(self.store, text_update("/list"))
        (tick,) = [b.data for row in reply.buttons for b in row if b.label == "❓ mine"]
        for chat_type in ("group", "supergroup"):
            actions = handle(self.store, tap_update(tick, GROUP_CHAT, chat_type=chat_type))
            self.assertEqual(actions, [AnswerTap("tap-1", PRIVATE_ONLY)])
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. mine")

    def test_both_chats_see_and_change_the_one_list(self):
        self.send("mine")
        self.send("theirs", chat_id=OTHER_CHAT)
        both = "❓ Unsorted\n1. mine\n2. theirs"
        self.assertEqual(self.send("/list"), both)
        self.assertEqual(self.send("/list", chat_id=OTHER_CHAT), both)
        self.assertEqual(self.send("/done 1", chat_id=OTHER_CHAT), "Done: mine")
        self.assertEqual(self.send("/list"), "❓ Unsorted\n1. theirs")

    def test_command_with_bot_mention(self):
        self.send("a")
        self.assertEqual(self.send("/LIST@BtwBot"), "❓ Unsorted\n1. a")

    def test_help_and_unknown(self):
        self.assertEqual(self.send("/start"), HELP)
        self.assertEqual(self.send("/help"), HELP)
        for topic in ("f milk", "s bulbs", "d call dentist", "❓ Unsorted", "/move 3 s"):
            self.assertIn(topic, HELP)
        self.assertIn("shared by everyone allowed to use the bot", HELP)
        self.assertNotIn("your list", HELP.lower())
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


class TypePromptTest(unittest.TestCase):
    """The [🍎 Food] [🛒 Stuff] [✅ Do] prompt on replies to unprefixed items."""

    def setUp(self):
        self.store = TodoStore(":memory:")
        self.addCleanup(self.store.close)

    def send(self, text, chat_id=CHAT):
        """Send a text message; return the single reply."""
        (reply,) = handle(self.store, text_update(text, chat_id))
        self.assertIsInstance(reply, SendMessage)
        return reply

    def list_text(self):
        return self.send("/list").text

    def tap(self, reply, label, chat_id=CHAT, message_id=55):
        """Tap the button labelled `label` on `reply`; return the actions."""
        (data,) = [b.data for row in reply.buttons or [] for b in row if b.label == label]
        update = tap_update(data, chat_id=chat_id, tap_id="t1")
        update["callback_query"]["message"]["message_id"] = message_id
        actions = handle(self.store, update)
        answers = [a for a in actions if isinstance(a, AnswerTap)]
        self.assertEqual(len(answers), 1, actions)
        self.assertEqual(answers[0].tap_id, "t1")
        return actions

    def edit_text(self, reply, label):
        """Tap `label` on `reply`; return the text the reply is edited to."""
        (edit,) = [a for a in self.tap(reply, label) if isinstance(a, EditMessage)]
        return edit.text

    def labels(self, reply):
        return [[b.label for b in row] for row in reply.buttons or []]

    def test_unprefixed_item_gets_type_buttons_and_is_already_unsorted(self):
        reply = self.send("milk")
        self.assertEqual(reply.text, "Added to ❓ Unsorted: milk")
        self.assertEqual(self.labels(reply), [["🍎 Food", "🛒 Stuff", "✅ Do"]])
        self.assertEqual(self.list_text(), "❓ Unsorted\n1. milk")

    def test_prefixed_items_get_no_prompt(self):
        self.assertIsNone(self.send("f milk\ns bulbs").buttons)

    def test_tapping_a_type_files_the_item_and_edits_the_reply(self):
        reply = self.send("milk")
        actions = self.tap(reply, "🍎 Food", message_id=55)
        # The answer comes first, so the spinner clears even if the edit fails.
        self.assertEqual(
            actions, [AnswerTap("t1"), EditMessage(CHAT, 55, "Added to 🍎 Food: milk")]
        )
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk")

    def test_one_prompt_files_every_unprefixed_line_of_a_message(self):
        reply = self.send("bread\nbutter\njam")
        self.assertEqual(self.labels(reply), [["🍎 Food", "🛒 Stuff", "✅ Do"]])
        edit_text = self.edit_text(reply, "🍎 Food")
        self.assertEqual(edit_text, "Added to 🍎 Food: bread; butter; jam")
        self.assertEqual(self.list_text(), "🍎 Food\n1. bread\n2. butter\n3. jam")

    def test_mixed_message_files_prefixed_lines_now_and_prompts_for_the_rest(self):
        reply = self.send("s bulbs\nhammer\nd call mum\nnails")
        self.assertEqual(
            self.list_text(),
            "🛒 Stuff\n1. bulbs\n\n✅ Do\n2. call mum\n\n❓ Unsorted\n3. hammer\n4. nails",
        )
        edit_text = self.edit_text(reply, "🛒 Stuff")
        self.assertEqual(edit_text, "Added to 🛒 Stuff: hammer; nails")
        self.assertEqual(
            self.list_text(), "🛒 Stuff\n1. bulbs\n2. hammer\n3. nails\n\n✅ Do\n4. call mum"
        )

    def test_button_data_fits_telegram_limit_for_many_lines(self):
        reply = self.send("\n".join(f"item number {n}" for n in range(200)))
        for row in reply.buttons:
            for button in row:
                self.assertLessEqual(len(button.data.encode()), 64, button)
        self.tap(reply, "✅ Do")
        self.assertNotIn("Unsorted", self.list_text())

    def test_old_prompt_only_files_items_still_unsorted_and_not_done(self):
        reply = self.send("bread\nbatteries\nbin bags")
        self.send("/move 2 s")  # batteries
        self.send("/done 3")  # bin bags is number 3: Stuff first, then Unsorted bread, bin bags
        edit_text = self.edit_text(reply, "🍎 Food")
        self.assertEqual(edit_text, "Added to 🍎 Food: bread")
        self.assertEqual(self.list_text(), "🍎 Food\n1. bread\n\n🛒 Stuff\n2. batteries")

    def test_old_prompt_never_overwrites_a_later_choice(self):
        reply = self.send("milk")
        self.tap(reply, "🍎 Food")
        actions = self.tap(reply, "✅ Do")
        self.assertEqual(actions, [AnswerTap("t1", "That item is no longer on the list")])
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk")

    def test_prompt_for_items_all_gone_says_so_and_changes_nothing(self):
        reply = self.send("milk\neggs")
        self.send("/done 1 2")
        actions = self.tap(reply, "🍎 Food")
        self.assertEqual(actions, [AnswerTap("t1", "That item is no longer on the list")])
        self.assertEqual(self.list_text(), "The list is empty.")

    def test_prompt_for_items_the_other_chat_sorted_says_so(self):
        reply = self.send("milk")
        self.send("/move 1 s", chat_id=OTHER_CHAT)
        actions = self.tap(reply, "🍎 Food")
        self.assertEqual(actions, [AnswerTap("t1", "That item is no longer on the list")])
        self.assertEqual(self.list_text(), "🛒 Stuff\n1. milk")


class ListTestCase(unittest.TestCase):
    """Helpers for tests that read and tap the /list message."""

    def setUp(self):
        self.store = TodoStore(":memory:")
        self.addCleanup(self.store.close)

    def send(self, text, chat_id=CHAT):
        """Send a text message; return the single reply."""
        (reply,) = handle(self.store, text_update(text, chat_id))
        self.assertIsInstance(reply, SendMessage)
        return reply

    def list_text(self):
        return self.send("/list").text

    def labels(self, reply):
        return [[b.label for b in row] for row in reply.buttons or []]

    def tap(self, reply, label, chat_id=CHAT, message_id=55):
        """Tap the button labelled `label` on `reply`; return the actions after the one answer."""
        (data,) = [b.data for row in reply.buttons or [] for b in row if b.label == label]
        update = tap_update(data, chat_id=chat_id, tap_id="t1")
        update["callback_query"]["message"]["message_id"] = message_id
        actions = handle(self.store, update)
        answers = [a for a in actions if isinstance(a, AnswerTap)]
        self.assertEqual(len(answers), 1, actions)
        # The answer comes first, so the spinner clears even if a later action fails.
        self.assertEqual(actions[0], answers[0])
        self.assertEqual(answers[0].tap_id, "t1")
        return actions

    def item_labels(self, reply):
        """Labels of the item buttons, below the filter row."""
        return self.labels(reply)[1:]


FILTER_ROW = ["• All", "🍎", "🛒", "✅"]


class TickTest(ListTestCase):
    """One [✔️ item] button per item in /list; tapping it ticks the item off, with Undo."""

    def test_list_has_one_full_width_button_per_item_in_list_order(self):
        self.send("d call mum\nf milk\nhammer")
        reply = self.send("/list")
        self.assertEqual(
            self.labels(reply), [FILTER_ROW, ["✔️ milk"], ["✔️ call mum"], ["❓ hammer"]]
        )

    def test_empty_list_has_no_buttons(self):
        self.assertIsNone(self.send("/list").buttons)

    def test_tapping_an_item_ticks_it_off_and_redraws_the_list_in_place(self):
        self.send("f milk\nf eggs\nd call mum")
        actions = self.tap(self.send("/list"), "✔️ eggs", message_id=55)
        (edit,) = [a for a in actions if isinstance(a, EditMessage)]
        self.assertEqual((edit.chat_id, edit.message_id), (CHAT, 55))
        self.assertEqual(edit.text, "🍎 Food\n1. milk\n\n✅ Do\n2. call mum")
        self.assertEqual(self.item_labels(edit), [["✔️ milk"], ["✔️ call mum"]])
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk\n\n✅ Do\n2. call mum")

    def test_tick_sends_a_short_message_with_undo(self):
        self.send("f milk")
        actions = self.tap(self.send("/list"), "✔️ milk")
        (sent,) = [a for a in actions if isinstance(a, SendMessage)]
        self.assertEqual((sent.chat_id, sent.text), (CHAT, "✔️ milk"))
        self.assertEqual(self.labels(sent), [["↩️ Undo"]])

    def tick(self, label):
        """Tick `label` off a fresh /list; return the "✔️ ..." message sent."""
        actions = self.tap(self.send("/list"), label)
        (sent,) = [a for a in actions if isinstance(a, SendMessage)]
        return sent

    def test_undo_restores_the_item_with_its_type_and_edits_the_message(self):
        self.send("f milk\ns bulbs\nd call mum")
        undo = self.tick("✔️ bulbs")
        actions = self.tap(undo, "↩️ Undo", message_id=77)
        self.assertEqual(actions, [AnswerTap("t1"), EditMessage(CHAT, 77, "↩️ Restored: bulbs")])
        self.assertEqual(
            self.list_text(), "🍎 Food\n1. milk\n\n🛒 Stuff\n2. bulbs\n\n✅ Do\n3. call mum"
        )

    def assert_gone(self, actions):
        self.assertEqual(actions, [AnswerTap("t1", "That item is no longer on the list")])

    def test_undo_after_the_item_was_ticked_off_again_says_gone(self):
        self.send("f milk")
        undo = self.tick("✔️ milk")
        self.tap(undo, "↩️ Undo")
        self.send("/done 1")
        self.assert_gone(self.tap(undo, "↩️ Undo"))
        self.assertEqual(self.list_text(), "The list is empty.")

    def test_undo_after_the_item_was_restored_says_gone(self):
        self.send("f milk")
        undo = self.tick("✔️ milk")
        self.tap(undo, "↩️ Undo")
        self.assert_gone(self.tap(undo, "↩️ Undo"))
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk")

    def test_button_for_an_item_already_done_says_gone_and_changes_nothing(self):
        self.send("f milk\nf eggs")
        old_list = self.send("/list")
        self.send("/done 1")
        self.assert_gone(self.tap(old_list, "✔️ milk"))
        self.assertEqual(self.list_text(), "🍎 Food\n1. eggs")

    def test_other_chat_ticks_off_an_item_added_here(self):
        self.send("f milk\nf eggs")
        their_list = self.send("/list", chat_id=OTHER_CHAT)
        actions = self.tap(their_list, "✔️ milk", chat_id=OTHER_CHAT)
        (sent,) = [a for a in actions if isinstance(a, SendMessage)]
        self.assertEqual((sent.chat_id, sent.text), (OTHER_CHAT, "✔️ milk"))
        self.assertEqual(self.list_text(), "🍎 Food\n1. eggs")

    def test_undo_here_restores_an_item_added_from_the_other_chat(self):
        self.send("f milk", chat_id=OTHER_CHAT)
        undo = self.tick("✔️ milk")
        actions = self.tap(undo, "↩️ Undo", message_id=77)
        self.assertEqual(actions, [AnswerTap("t1"), EditMessage(CHAT, 77, "↩️ Restored: milk")])
        self.assertEqual(self.send("/list", chat_id=OTHER_CHAT).text, "🍎 Food\n1. milk")

    def test_stale_tap_after_the_other_chat_ticked_the_item_off_says_gone(self):
        self.send("f milk\nf eggs")
        my_list = self.send("/list")
        self.send("/done 1", chat_id=OTHER_CHAT)
        self.assert_gone(self.tap(my_list, "✔️ milk"))
        self.assertEqual(self.list_text(), "🍎 Food\n1. eggs")

    def test_list_shows_at_most_90_buttons_and_the_rest_with_done(self):
        self.send("\n".join(f"f item {n}" for n in range(1, 96)))
        reply = self.send("/list")
        self.assertIn("95. item 95", reply.text)
        labels = self.item_labels(reply)
        self.assertEqual(len(labels), 90)
        self.assertEqual(labels[-1], ["✔️ item 90"])
        self.assertEqual(self.send("/done 95").text, "Done: item 95")

    def test_redraw_too_long_to_edit_is_sent_as_a_new_list_message(self):
        long = "x" * 1000
        self.send("\n".join(f"f {long} {n}" for n in range(1, 7)))
        actions = self.tap(self.send("/list"), f"✔️ {long} 1", message_id=55)
        self.assertEqual([type(a) for a in actions], [AnswerTap, SendMessage, SendMessage])
        new_list, undo = actions[1:]
        self.assertEqual(new_list.text, self.list_text())
        self.assertEqual(len(self.item_labels(new_list)), 5)
        self.assertEqual(undo.text, f"✔️ {long} 1")

    def test_ticking_the_last_item_redraws_an_empty_list(self):
        self.send("f milk")
        actions = self.tap(self.send("/list"), "✔️ milk")
        (edit,) = [a for a in actions if isinstance(a, EditMessage)]
        self.assertEqual(edit.text, "The list is empty.")
        self.assertIsNone(edit.buttons)


class FilterTest(ListTestCase):
    """The [All] [🍎] [🛒] [✅] row on /list narrows it to one type, keeping item numbers."""

    def edit_after(self, actions):
        (edit,) = [a for a in actions if isinstance(a, EditMessage)]
        return edit

    def test_tapping_a_filter_shows_only_that_type_in_place_with_full_list_numbers(self):
        self.send("f milk\nf eggs\ns bulbs\nd call mum\nhammer")
        actions = self.tap(self.send("/list"), "🛒", message_id=55)
        self.assertEqual(len(actions), 2, actions)
        edit = self.edit_after(actions)
        self.assertEqual((edit.chat_id, edit.message_id), (CHAT, 55))
        self.assertEqual(edit.text, "🛒 Stuff\n3. bulbs")
        self.assertEqual(self.labels(edit), [["All", "🍎", "• 🛒", "✅"], ["✔️ bulbs"]])

    def test_all_shows_everything_again_including_unsorted(self):
        self.send("f milk\nhammer")
        food = self.edit_after(self.tap(self.send("/list"), "🍎"))
        self.assertEqual(food.text, "🍎 Food\n1. milk")
        everything = self.edit_after(self.tap(food, "All"))
        self.assertEqual(everything.text, "🍎 Food\n1. milk\n\n❓ Unsorted\n2. hammer")
        self.assertEqual(self.labels(everything)[0], FILTER_ROW)

    def test_ticking_in_a_filtered_view_keeps_the_filter(self):
        self.send("f milk\nf eggs\ns bulbs\nd call mum")
        food = self.edit_after(self.tap(self.send("/list"), "🍎"))
        redrawn = self.edit_after(self.tap(food, "✔️ milk"))
        self.assertEqual(redrawn.text, "🍎 Food\n1. eggs")
        self.assertEqual(self.labels(redrawn), [["All", "• 🍎", "🛒", "✅"], ["✔️ eggs"]])

    def test_filtered_view_with_no_items_says_so_and_keeps_the_filter_row(self):
        self.send("f milk")
        do = self.edit_after(self.tap(self.send("/list"), "✅"))
        self.assertEqual(do.text, "No Do items.")
        self.assertEqual(self.labels(do), [["All", "🍎", "🛒", "• ✅"]])

    def test_list_with_a_type_opens_filtered(self):
        self.send("f milk\ns bulbs\nd call mum")
        for args, text, active in [
            ("food", "🍎 Food\n1. milk", "• 🍎"),
            ("F", "🍎 Food\n1. milk", "• 🍎"),
            ("stuff", "🛒 Stuff\n2. bulbs", "• 🛒"),
            ("s", "🛒 Stuff\n2. bulbs", "• 🛒"),
            ("do", "✅ Do\n3. call mum", "• ✅"),
            ("d", "✅ Do\n3. call mum", "• ✅"),
        ]:
            with self.subTest(args):
                reply = self.send(f"/list {args}")
                self.assertEqual(reply.text, text)
                self.assertIn(active, self.labels(reply)[0])

    def test_list_with_anything_else_explains_usage(self):
        self.send("f milk")
        for args in ("x", "food stuff", "unsorted", "a"):
            with self.subTest(args):
                reply = self.send(f"/list {args}")
                self.assertEqual(
                    reply.text, "Usage: /list, or /list food (f), /list stuff (s), /list do (d)"
                )
                self.assertIsNone(reply.buttons)

    def test_ticking_the_last_item_of_a_filter_says_none_left(self):
        self.send("f milk\ns bulbs")
        food = self.edit_after(self.tap(self.send("/list"), "🍎"))
        redrawn = self.edit_after(self.tap(food, "✔️ milk"))
        self.assertEqual(redrawn.text, "No Food items.")
        self.assertEqual(self.labels(redrawn), [["All", "• 🍎", "🛒", "✅"]])


class SortTest(ListTestCase):
    """Tapping an Unsorted item in /list swaps the list for a type picker for that item."""

    def edit_after(self, actions):
        (edit,) = [a for a in actions if isinstance(a, EditMessage)]
        return edit

    def picker(self):
        """Open the picker for "hammer" from a fresh /list; return the edited message."""
        return self.edit_after(self.tap(self.send("/list"), "❓ hammer", message_id=55))

    def test_tapping_an_unsorted_item_shows_a_type_picker_in_place(self):
        self.send("f milk\nhammer")
        actions = self.tap(self.send("/list"), "❓ hammer", message_id=55)
        self.assertEqual(len(actions), 2, actions)
        edit = self.edit_after(actions)
        self.assertEqual((edit.chat_id, edit.message_id), (CHAT, 55))
        self.assertEqual(edit.text, "Which type is “hammer”?")
        self.assertEqual(self.labels(edit), [["🍎 Food", "🛒 Stuff", "✅ Do"], ["⬅️ Back"]])
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk\n\n❓ Unsorted\n2. hammer")

    def test_choosing_a_type_files_the_item_and_redraws_the_list(self):
        self.send("f milk\nhammer\nd call mum")
        actions = self.tap(self.picker(), "🛒 Stuff", message_id=55)
        self.assertEqual(len(actions), 2, actions)
        edit = self.edit_after(actions)
        self.assertEqual((edit.chat_id, edit.message_id), (CHAT, 55))
        self.assertEqual(edit.text, "🍎 Food\n1. milk\n\n🛒 Stuff\n2. hammer\n\n✅ Do\n3. call mum")
        self.assertEqual(
            self.labels(edit), [FILTER_ROW, ["✔️ milk"], ["✔️ hammer"], ["✔️ call mum"]]
        )
        self.assertEqual(self.list_text(), edit.text)

    def test_back_returns_to_the_list_unchanged(self):
        self.send("f milk\nhammer")
        before = self.send("/list")
        edit = self.edit_after(self.tap(self.picker(), "⬅️ Back", message_id=55))
        self.assertEqual((edit.chat_id, edit.message_id), (CHAT, 55))
        self.assertEqual((edit.text, self.labels(edit)), (before.text, self.labels(before)))
        self.assertEqual(self.list_text(), before.text)

    def test_choosing_a_type_for_an_item_done_since_says_gone_and_redraws(self):
        self.send("f milk\nhammer")
        picker = self.picker()
        self.send("/done 2")
        actions = self.tap(picker, "🍎 Food")
        self.assertEqual(actions[0], AnswerTap("t1", "That item is no longer on the list"))
        self.assertEqual(self.edit_after(actions).text, "🍎 Food\n1. milk")
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk")

    def test_choosing_a_type_for_an_item_moved_since_keeps_the_newer_type(self):
        self.send("f milk\nhammer")
        picker = self.picker()
        self.send("/move 2 s")
        actions = self.tap(picker, "🍎 Food")
        self.assertEqual(actions[0], AnswerTap("t1", "Already in 🛒 Stuff"))
        self.assertEqual(self.edit_after(actions).text, "🍎 Food\n1. milk\n\n🛒 Stuff\n2. hammer")

    def test_sorting_an_item_added_from_the_other_chat(self):
        self.send("f milk\nhammer", chat_id=OTHER_CHAT)
        actions = self.tap(self.picker(), "🛒 Stuff")
        self.assertEqual(actions[0], AnswerTap("t1"))
        self.assertEqual(
            self.send("/list", chat_id=OTHER_CHAT).text, "🍎 Food\n1. milk\n\n🛒 Stuff\n2. hammer"
        )

    def test_done_still_ticks_off_unsorted_items_directly(self):
        self.send("f milk\nhammer")
        self.assertEqual(self.send("/done 2").text, "Done: hammer")
        self.assertEqual(self.list_text(), "🍎 Food\n1. milk")


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


    def test_items_from_every_chat_already_stored_form_the_one_list(self):
        import os
        import sqlite3
        import tempfile

        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "btw.db")
            store = TodoStore(path)
            store.close()
            # Rows as they were stored when each chat had a List of its own.
            conn = sqlite3.connect(path)
            conn.executescript(
                """
                INSERT INTO items (chat_id, text, type) VALUES (100, 'milk', 'food');
                INSERT INTO items (chat_id, text) VALUES (300, 'hammer');
                INSERT INTO items (chat_id, text, done) VALUES (300, 'old done', 1);
                """
            )
            conn.commit()
            conn.close()

            store = TodoStore(path)
            self.addCleanup(store.close)
            for chat_id in (CHAT, OTHER_CHAT):
                (reply,) = handle(store, text_update("/list", chat_id))
                self.assertEqual(reply.text, "🍎 Food\n1. milk\n\n❓ Unsorted\n2. hammer")


if __name__ == "__main__":
    unittest.main()
