"""Timer hitung mundur presentasi (tanpa UI, waktu diberikan dari luar)."""
import math

IDLE, RUNNING, PAUSED = "idle", "running", "paused"
WARNING, END = "warning", "end"


def fmt(remaining):
    """10:00, 00:01, 00:00, lalu +00:05 saat lewat batas."""
    if remaining < 0:
        secs, sign = int(-remaining), "+"
    else:
        secs, sign = math.ceil(remaining), ""
    return f"{sign}{secs // 60:02d}:{secs % 60:02d}"


class CountdownTimer:
    def __init__(self, duration, warning=60):
        self.duration = duration
        self.warning = warning
        self.reset()

    def reset(self):
        self.state = IDLE
        self._elapsed = 0.0
        self._started = None
        self._fired = set()

    def set_duration(self, duration):
        self.duration = duration
        self.reset()

    def toggle(self, now):
        if self.state == RUNNING:
            self._elapsed += now - self._started
            self.state = PAUSED
        else:
            self._started = now
            self.state = RUNNING

    def elapsed(self, now):
        if self.state == RUNNING:
            return self._elapsed + now - self._started
        return self._elapsed

    def remaining(self, now):
        return self.duration - self.elapsed(now)

    def events(self, now):
        """Peringatan yang baru saja terlewati; masing-masing hanya sekali."""
        remaining = self.remaining(now)
        new = []
        if self.duration > self.warning and remaining <= self.warning:
            new.append(WARNING)
        if remaining <= 0:
            new.append(END)
        new = [e for e in new if e not in self._fired]
        if END in new:
            new = [END]  # langsung habis: cukup bunyi akhir
            self._fired.add(WARNING)
        self._fired.update(new)
        return new
