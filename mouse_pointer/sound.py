"""Bunyi peringatan timer: nada sinus dibuat di memori, diputar lewat speaker biasa.

winsound.Beep memakai buzzer PC yang di banyak laptop modern tidak bersuara,
jadi bunyinya dibuat sendiri sebagai WAV.
"""
import io
import math
import struct
import threading
import wave
import winsound

RATE = 22050
FADE_MS = 8  # tanpa fade, awal/akhir nada terdengar "klik"
GAP_MS = 120


def tone(freq, ms, volume=0.6):
    n = RATE * ms // 1000
    fade = RATE * FADE_MS // 1000
    out = []
    for i in range(n):
        env = min(1.0, i / fade, (n - 1 - i) / fade)
        out.append(int(32767 * volume * env * math.sin(2 * math.pi * freq * i / RATE)))
    return out


def wav(pattern):
    """[(frekuensi Hz, durasi ms), ...] -> bytes WAV mono 16-bit, dengan jeda antar nada."""
    samples = []
    for freq, ms in pattern:
        samples += tone(freq, ms) + [0] * (RATE * GAP_MS // 1000)
    buf = io.BytesIO()
    with wave.open(buf, "wb") as f:
        f.setnchannels(1)
        f.setsampwidth(2)
        f.setframerate(RATE)
        f.writeframes(struct.pack(f"<{len(samples)}h", *samples))
    return buf.getvalue()


def play(data):
    # SND_MEMORY tidak bisa SND_ASYNC, jadi diputar di thread sendiri.
    threading.Thread(target=winsound.PlaySound, args=(data, winsound.SND_MEMORY),
                     daemon=True).start()
