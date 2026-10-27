import io
import unittest
import wave

from mouse_pointer.sound import GAP_MS, RATE, tone, wav


class SoundTest(unittest.TestCase):
    def test_wav_length_includes_gaps(self):
        with wave.open(io.BytesIO(wav([(880, 200), (880, 100)]))) as f:
            self.assertEqual((f.getnchannels(), f.getsampwidth(), f.getframerate()), (1, 2, RATE))
            self.assertEqual(f.getnframes(), RATE * (200 + 100 + 2 * GAP_MS) // 1000)

    def test_tone_fades_in_and_out(self):
        samples = tone(1000, 100)
        self.assertEqual(samples[0], 0)
        self.assertEqual(samples[-1], 0)
        self.assertGreater(max(samples), 15000)
