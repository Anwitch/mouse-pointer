import unittest

from mouse_pointer.devices import device_key, label, short_id

DONGLE = r"\?\HID#VID_3151&PID_3022&MI_01&Col01#7&2a3b&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}"
BLUETOOTH = (r"\?\HID#{00001124-0000-1000-8000-00805f9b34fb}_VID&0002046d_PID&b023&Col01"
             r"#9&1f&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}")
TOUCHPAD = r"\?\HID#ASUE1300&Col01#5&bf0715d&0&0000#{378de44c-56ef-11d1-bc8c-00a0c91405dd}"


class DeviceKeyTest(unittest.TestCase):
    def test_strips_interface_and_collection(self):
        self.assertEqual(device_key(DONGLE), "VID_3151&PID_3022")
        self.assertEqual(device_key(TOUCHPAD), "ASUE1300")

    def test_bluetooth(self):
        key = device_key(BLUETOOTH)
        self.assertIn(key.lower(), BLUETOOTH.lower())
        self.assertEqual(short_id(key), "046D:B023")

    def test_key_matches_its_own_path(self):
        # Engine mencocokkan mouse dengan "key in path" (tanpa huruf besar/kecil).
        for path in (DONGLE, BLUETOOTH, TOUCHPAD):
            self.assertIn(device_key(path).lower(), path.lower())


class LabelTest(unittest.TestCase):
    def test_uses_product_name(self):
        self.assertEqual(label("VID_3151&PID_3022", "2.4G Mouse"), "2.4G Mouse (3151:3022)")

    def test_generic_names(self):
        self.assertEqual(label("ASUE1300", "HIDI2C Device"), "Touchpad laptop (ASUE1300)")
        self.assertEqual(label("VID_3151&PID_3022", ""), "Mouse (3151:3022)")
