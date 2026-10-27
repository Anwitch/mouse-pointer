"""Logika inti (tanpa Win32): memutuskan nasib setiap klik mouse.

Low-level hook dan Raw Input melaporkan klik yang sama secara terpisah, dan
urutannya bisa terbalik. Klik ditahan sampai Raw Input memberi tahu asal
perangkatnya: dari mouse target -> jadi tombol panah, selain itu -> diteruskan.
"""

NEXT, PREV = "next", "prev"

# Raw Input button flags (RI_MOUSE_*)
L_DOWN, L_UP, R_DOWN, R_UP = 0x1, 0x2, 0x4, 0x8
M_DOWN, M_UP = 0x10, 0x20
BACK_DOWN, BACK_UP, FWD_DOWN, FWD_UP = 0x40, 0x80, 0x100, 0x200
WHEEL = 0x400
INTERCEPT = (L_DOWN, L_UP, R_DOWN, R_UP, M_DOWN, M_UP,
             BACK_DOWN, BACK_UP, FWD_DOWN, FWD_UP, WHEEL)

DOWN_KEYS = {L_DOWN: NEXT, FWD_DOWN: NEXT, R_DOWN: PREV, BACK_DOWN: PREV}

_MSG_TO_FLAG = {0x201: L_DOWN, 0x202: L_UP, 0x204: R_DOWN, 0x205: R_UP,
                0x207: M_DOWN, 0x208: M_UP, 0x20A: WHEEL}
WM_XBUTTONDOWN, WM_XBUTTONUP = 0x20B, 0x20C


def hook_flag(msg, mouse_data):
    """Pesan low-level hook -> Raw Input flag, atau None kalau tidak diurus."""
    xbutton = (mouse_data >> 16) & 0xFFFF
    if msg == WM_XBUTTONDOWN:
        return BACK_DOWN if xbutton == 1 else FWD_DOWN
    if msg == WM_XBUTTONUP:
        return BACK_UP if xbutton == 1 else FWD_UP
    return _MSG_TO_FLAG.get(msg)


def wheel_delta(mouse_data):
    delta = (mouse_data >> 16) & 0xFFFF
    return delta - 0x10000 if delta & 0x8000 else delta


class Router:
    """Aksi: ("key", NEXT|PREV), ("timer", "toggle") atau ("mouse", flag, mouse_data)."""

    def __init__(self, active=True, wheel_interval=0.25, timeout=0.06):
        self.active = active
        self.wheel_interval = wheel_interval
        self.timeout = timeout
        self.pending = []   # (t, flag, data): klik ditahan, menunggu Raw Input
        self.raw_seen = []  # (t, flag, is_target): Raw Input yang datang lebih dulu
        self._last_wheel = float("-inf")

    def on_hook(self, flag, data, now):
        """Return (swallow, actions)."""
        if not self.active or flag not in INTERCEPT:
            return False, []
        for i, (_, f, is_target) in enumerate(self.raw_seen):
            if f == flag:
                del self.raw_seen[i]
                if is_target:
                    return True, self._target_actions(flag, data, now)
                return False, []
        self.pending.append((now, flag, data))
        return True, []

    def on_raw(self, button_flags, is_target, now):
        actions = []
        if not self.active:
            return actions
        for flag in INTERCEPT:
            if not button_flags & flag:
                continue
            match = next((p for p in self.pending if p[1] == flag), None)
            if match is None:
                self.raw_seen.append((now, flag, is_target))
                continue
            self.pending.remove(match)
            if is_target:
                actions += self._target_actions(flag, match[2], now)
            else:
                actions.append(("mouse", flag, match[2]))
        return actions

    def tick(self, now):
        """Klik yang Raw Input-nya tak kunjung datang diteruskan apa adanya."""
        expired = [p for p in self.pending if now - p[0] > self.timeout]
        for p in expired:
            self.pending.remove(p)
        self.raw_seen = [r for r in self.raw_seen if now - r[0] < 0.3]
        return [("mouse", flag, data) for _, flag, data in expired]

    def set_active(self, active):
        self.active = active
        if active:
            return []
        actions = [("mouse", flag, data) for _, flag, data in self.pending]
        self.pending.clear()
        self.raw_seen.clear()
        return actions

    def _target_actions(self, flag, data, now):
        if flag in DOWN_KEYS:
            return [("key", DOWN_KEYS[flag])]
        if flag == M_DOWN:
            return [("timer", "toggle")]
        if flag == WHEEL:
            if now - self._last_wheel < self.wheel_interval:
                return []
            self._last_wheel = now
            return [("key", NEXT if wheel_delta(data) < 0 else PREV)]
        return []  # lepas tombol: cukup ditelan
