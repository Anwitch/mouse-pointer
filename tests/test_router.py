import unittest

from mouse_pointer.router import (
    BACK_DOWN, FWD_DOWN, L_DOWN, L_UP, M_DOWN, M_UP, NEXT, PREV, R_DOWN, WHEEL, Router,
    hook_flag, wheel_delta)

WHEEL_DOWN = (-120 & 0xFFFF) << 16
WHEEL_UP = 120 << 16


class HookFlagTest(unittest.TestCase):
    def test_maps_buttons(self):
        self.assertEqual(hook_flag(0x201, 0), L_DOWN)
        self.assertEqual(hook_flag(0x204, 0), R_DOWN)
        self.assertEqual(hook_flag(0x20B, 1 << 16), BACK_DOWN)
        self.assertEqual(hook_flag(0x20B, 2 << 16), FWD_DOWN)
        self.assertEqual(hook_flag(0x207, 0), M_DOWN)
        self.assertIsNone(hook_flag(0x200, 0))  # gerakan

    def test_wheel_delta_is_signed(self):
        self.assertEqual(wheel_delta(WHEEL_DOWN), -120)
        self.assertEqual(wheel_delta(WHEEL_UP), 120)


class RouterTest(unittest.TestCase):
    def setUp(self):
        self.r = Router()

    def test_target_click_hook_first(self):
        self.assertEqual(self.r.on_hook(L_DOWN, 0, 0.0), (True, []))
        self.assertEqual(self.r.on_raw(L_DOWN, True, 0.001), [("key", NEXT)])
        self.assertEqual(self.r.pending, [])

    def test_target_click_raw_first(self):
        self.assertEqual(self.r.on_raw(R_DOWN, True, 0.0), [])
        self.assertEqual(self.r.on_hook(R_DOWN, 0, 0.001), (True, [("key", PREV)]))

    def test_target_button_release_is_swallowed(self):
        self.r.on_hook(L_UP, 0, 0.0)
        self.assertEqual(self.r.on_raw(L_UP, True, 0.001), [])

    def test_other_device_hook_first_is_reinjected(self):
        self.r.on_hook(L_DOWN, 0, 0.0)
        self.assertEqual(self.r.on_raw(L_DOWN, False, 0.001), [("mouse", L_DOWN, 0)])

    def test_other_device_raw_first_passes_through(self):
        self.r.on_raw(R_DOWN, False, 0.0)
        self.assertEqual(self.r.on_hook(R_DOWN, 0, 0.001), (False, []))

    def test_side_buttons(self):
        self.r.on_hook(FWD_DOWN, 2 << 16, 0.0)
        self.assertEqual(self.r.on_raw(FWD_DOWN, True, 0.0), [("key", NEXT)])
        self.r.on_hook(BACK_DOWN, 1 << 16, 1.0)
        self.assertEqual(self.r.on_raw(BACK_DOWN, True, 1.0), [("key", PREV)])

    def test_target_middle_click_toggles_timer(self):
        self.r.on_hook(M_DOWN, 0, 0.0)
        self.assertEqual(self.r.on_raw(M_DOWN, True, 0.0), [("timer", "toggle")])
        self.r.on_hook(M_UP, 0, 0.1)
        self.assertEqual(self.r.on_raw(M_UP, True, 0.1), [])

    def test_other_device_middle_click_is_reinjected(self):
        self.r.on_hook(M_DOWN, 0, 0.0)
        self.assertEqual(self.r.on_raw(M_DOWN, False, 0.0), [("mouse", M_DOWN, 0)])

    def test_missing_raw_input_times_out_and_reinjects(self):
        self.r.on_hook(L_DOWN, 0, 0.0)
        self.assertEqual(self.r.tick(0.03), [])
        self.assertEqual(self.r.tick(0.1), [("mouse", L_DOWN, 0)])
        self.assertEqual(self.r.pending, [])

    def test_wheel_direction_and_throttle(self):
        self.r.on_hook(WHEEL, WHEEL_DOWN, 0.0)
        self.assertEqual(self.r.on_raw(WHEEL, True, 0.0), [("key", NEXT)])
        self.r.on_hook(WHEEL, WHEEL_DOWN, 0.1)
        self.assertEqual(self.r.on_raw(WHEEL, True, 0.1), [])  # terlalu cepat
        self.r.on_hook(WHEEL, WHEEL_UP, 0.4)
        self.assertEqual(self.r.on_raw(WHEEL, True, 0.4), [("key", PREV)])

    def test_inactive_passes_everything(self):
        self.r.set_active(False)
        self.assertEqual(self.r.on_hook(L_DOWN, 0, 0.0), (False, []))
        self.assertEqual(self.r.on_raw(L_DOWN, True, 0.0), [])

    def test_deactivate_flushes_pending_clicks(self):
        self.r.on_hook(L_DOWN, 0, 0.0)
        self.assertEqual(self.r.set_active(False), [("mouse", L_DOWN, 0)])


if __name__ == "__main__":
    unittest.main()
