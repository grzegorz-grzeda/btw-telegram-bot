import unittest

from btw_bot.telegram import split_message


class SplitMessageTest(unittest.TestCase):
    def test_short_text_is_one_chunk(self):
        self.assertEqual(split_message("hello", limit=10), ["hello"])

    def test_splits_at_newlines(self):
        self.assertEqual(split_message("aaaa\nbbbb\ncccc", limit=10), ["aaaa\nbbbb", "cccc"])

    def test_hard_splits_long_line(self):
        self.assertEqual(split_message("x" * 25, limit=10), ["x" * 10, "x" * 10, "x" * 5])


if __name__ == "__main__":
    unittest.main()
