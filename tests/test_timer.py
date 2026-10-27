import unittest

from mouse_pointer.timer import END, IDLE, PAUSED, RUNNING, WARNING, CountdownTimer, fmt


class FmtTest(unittest.TestCase):
    def test_format(self):
        self.assertEqual(fmt(600), "10:00")
        self.assertEqual(fmt(599.2), "10:00")
        self.assertEqual(fmt(59), "00:59")
        self.assertEqual(fmt(0), "00:00")
        self.assertEqual(fmt(-12.7), "+00:12")
        self.assertEqual(fmt(-75), "+01:15")


class CountdownTimerTest(unittest.TestCase):
    def setUp(self):
        self.t = CountdownTimer(300, warning=60)

    def test_starts_idle_with_full_time(self):
        self.assertEqual(self.t.state, IDLE)
        self.assertEqual(self.t.remaining(100), 300)

    def test_counts_down_while_running(self):
        self.t.toggle(10)
        self.assertEqual(self.t.state, RUNNING)
        self.assertEqual(self.t.remaining(40), 270)

    def test_pause_freezes_and_resume_continues(self):
        self.t.toggle(0)
        self.t.toggle(30)
        self.assertEqual(self.t.state, PAUSED)
        self.assertEqual(self.t.remaining(1000), 270)
        self.t.toggle(1000)
        self.assertEqual(self.t.remaining(1010), 260)

    def test_reset(self):
        self.t.toggle(0)
        self.t.reset()
        self.assertEqual(self.t.state, IDLE)
        self.assertEqual(self.t.remaining(50), 300)

    def test_goes_negative_after_limit(self):
        self.t.toggle(0)
        self.assertEqual(self.t.remaining(310), -10)

    def test_warning_then_end_fire_once(self):
        self.t.toggle(0)
        self.assertEqual(self.t.events(100), [])
        self.assertEqual(self.t.events(240), [WARNING])
        self.assertEqual(self.t.events(241), [])
        self.assertEqual(self.t.events(300), [END])
        self.assertEqual(self.t.events(400), [])

    def test_skipped_warning_only_fires_end(self):
        self.t.toggle(0)
        self.assertEqual(self.t.events(305), [END])

    def test_no_warning_when_duration_shorter_than_warning(self):
        t = CountdownTimer(30, warning=60)
        t.toggle(0)
        self.assertEqual(t.events(1), [])
        self.assertEqual(t.events(30), [END])

    def test_reset_rearms_events(self):
        self.t.toggle(0)
        self.t.events(300)
        self.t.reset()
        self.t.toggle(0)
        self.assertEqual(self.t.events(240), [WARNING])

    def test_set_duration_resets(self):
        self.t.toggle(0)
        self.t.set_duration(600)
        self.assertEqual(self.t.state, IDLE)
        self.assertEqual(self.t.remaining(10), 600)


if __name__ == "__main__":
    unittest.main()
