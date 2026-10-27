"""Overlay timer: kotak kecil selalu di atas layar, klik tembus, tidak merebut fokus.

Semua akses tkinter terjadi di thread utama; thread lain cukup memanggil post().
"""
import queue
import time
import tkinter as tk

from . import sound
from . import winapi as w
from .timer import END, IDLE, PAUSED, WARNING, CountdownTimer, fmt

GWL_EXSTYLE = -20
WS_EX_LAYERED, WS_EX_TRANSPARENT, WS_EX_TOOLWINDOW = 0x80000, 0x20, 0x80
WS_EX_TOPMOST, WS_EX_NOACTIVATE = 0x8, 0x08000000
HWND_TOPMOST = -1
SWP_NOSIZE, SWP_NOMOVE, SWP_NOACTIVATE = 0x1, 0x2, 0x10

ALPHA = 0.88
MARGIN = 16
# gaya -> (warna teks, warna latar)
STYLES = {"normal": ("#ffffff", "#1e1e1e"), "paused": ("#9a9a9a", "#1e1e1e"),
          "warning": ("#1e1e1e", "#ffb020"), "over": ("#ffffff", "#d93025")}
SOUNDS = {WARNING: sound.wav([(880, 180), (880, 180)]), END: sound.wav([(1047, 450)] * 3)}


class TimerOverlay:
    def __init__(self, minutes, warning_seconds, position, font_size, sound):
        self.timer = CountdownTimer(minutes * 60, warning_seconds)
        self.position = position
        self.sound = sound
        self._queue = queue.Queue()
        self._shown = False
        self._last_raise = 0.0
        self._geometry = None

        self.root = tk.Tk()
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        # Disembunyikan lewat alpha 0, bukan withdraw: memunculkan ulang
        # jendela bisa merebut fokus dari Canva (panah jadi tidak sampai).
        self.root.attributes("-alpha", 0.0)
        self.label = tk.Label(self.root, font=("Segoe UI", font_size, "bold"), padx=14, pady=2)
        self.label.pack()
        self.root.update_idletasks()
        self.hwnd = w.user32.GetParent(self.root.winfo_id())
        style = w.user32.GetWindowLongW(self.hwnd, GWL_EXSTYLE)
        w.user32.SetWindowLongW(self.hwnd, GWL_EXSTYLE, style | WS_EX_LAYERED | WS_EX_TRANSPARENT
                                | WS_EX_TOOLWINDOW | WS_EX_TOPMOST | WS_EX_NOACTIVATE)
        self.root.after(100, self._tick)

    def post(self, cmd, arg=None):
        """Aman dipanggil dari thread mana pun: toggle, reset, duration, quit."""
        self._queue.put((cmd, arg))

    def run(self):
        self.root.mainloop()

    def _tick(self):
        now = time.monotonic()
        while True:
            try:
                cmd, arg = self._queue.get_nowait()
            except queue.Empty:
                break
            if cmd == "quit":
                self.root.destroy()
                return
            if cmd == "toggle":
                self.timer.toggle(now)
            elif cmd == "reset":
                self.timer.reset()
            elif cmd == "duration":
                self.timer.set_duration(arg)
        for event in self.timer.events(now):
            if self.sound:
                sound.play(SOUNDS[event])
        self._render(now)
        self.root.after(100, self._tick)

    def _render(self, now):
        if self.timer.state == IDLE:
            if self._shown:
                self.root.attributes("-alpha", 0.0)
                self._shown = False
            return
        remaining = self.timer.remaining(now)
        text = fmt(remaining)
        if self.timer.state == PAUSED:
            style, text = "paused", "❚❚ " + text
        elif remaining <= 0:
            style = "over"
        elif remaining <= self.timer.warning:
            style = "warning"
        else:
            style = "normal"
        fg, bg = STYLES[style]
        self.label.config(text=text, fg=fg, bg=bg)
        self.root.config(bg=bg)
        self._place()
        if not self._shown:
            self.root.attributes("-alpha", ALPHA)
            self._shown = True
        if now - self._last_raise > 1.0:  # tetap di atas walau Canva baru fullscreen
            w.user32.SetWindowPos(self.hwnd, HWND_TOPMOST, 0, 0, 0, 0,
                                  SWP_NOMOVE | SWP_NOSIZE | SWP_NOACTIVATE)
            self._last_raise = now

    def _place(self):
        self.root.update_idletasks()
        width, height = self.root.winfo_reqwidth(), self.root.winfo_reqheight()
        x = MARGIN if "left" in self.position else self.root.winfo_screenwidth() - width - MARGIN
        y = MARGIN if "top" in self.position else self.root.winfo_screenheight() - height - MARGIN
        geometry = f"+{x}+{y}"
        if geometry != self._geometry:
            self.root.geometry(geometry)
            self._geometry = geometry
