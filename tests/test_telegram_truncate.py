import unittest


from notifiers.telegram_notifier import TelegramNotifier


class TestTelegramTruncate(unittest.TestCase):
    def test_truncate_message_len_4096(self):
        txt = "a" * 5000
        out = TelegramNotifier._truncate(txt, TelegramNotifier.MAX_MESSAGE_LEN)
        self.assertLessEqual(len(out), TelegramNotifier.MAX_MESSAGE_LEN)

    def test_truncate_caption_len_1024(self):
        txt = "b" * 5000
        out = TelegramNotifier._truncate(txt, TelegramNotifier.MAX_CAPTION_LEN)
        self.assertLessEqual(len(out), TelegramNotifier.MAX_CAPTION_LEN)


if __name__ == "__main__":
    unittest.main()

