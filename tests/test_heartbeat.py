import socket
import unittest
import urllib.error

from btw_bot.heartbeat import Heartbeat

URL = "https://hc-ping.com/secret-check-id"


class FakeClock:
    def __init__(self):
        self.now = 1000.0

    def __call__(self):
        return self.now


class HeartbeatTest(unittest.TestCase):
    def setUp(self):
        self.clock = FakeClock()
        self.pings = []
        self.heartbeat = Heartbeat(URL, clock=self.clock, ping=self.pings.append)

    def test_first_beat_pings(self):
        self.heartbeat.beat()

        self.assertEqual(self.pings, [URL])

    def test_beats_within_5_minutes_of_the_last_ping_are_skipped(self):
        self.heartbeat.beat()
        self.clock.now += 50
        self.heartbeat.beat()
        self.clock.now += 249  # 4 min 59 s after the ping
        self.heartbeat.beat()

        self.assertEqual(self.pings, [URL])

    def test_a_beat_5_minutes_after_the_last_ping_pings_again(self):
        self.heartbeat.beat()
        self.clock.now += 300
        self.heartbeat.beat()
        self.clock.now += 200
        self.heartbeat.beat()  # skipped: 200 s after the second ping
        self.clock.now += 100
        self.heartbeat.beat()

        self.assertEqual(self.pings, [URL, URL, URL])

    def test_a_failing_ping_is_logged_without_the_url_and_not_raised(self):
        for error in (
            TimeoutError("timed out"),
            urllib.error.URLError(socket.gaierror(-2, "Name or service not known")),
            urllib.error.HTTPError(URL, 503, "Service Unavailable", {}, None),
            ValueError(f"unknown url type: {URL!r}"),
        ):
            with self.subTest(error=error):
                heartbeat = Heartbeat(URL, clock=self.clock, ping=raising(error))

                with self.assertLogs("btw_bot", "WARNING") as logs:
                    heartbeat.beat()

                self.assertEqual(len(logs.output), 1)
                self.assertNotIn("secret-check-id", logs.output[0])


def raising(error):
    def ping(url):
        raise error

    return ping
