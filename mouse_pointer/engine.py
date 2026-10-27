"""Thread Win32: low-level mouse hook + Raw Input + hotkey, menjalankan Router."""
import ctypes
import logging
import threading
import time
from ctypes import wintypes as wt

from . import router as r
from . import winapi as w

log = logging.getLogger(__name__)

WM_APP_TOGGLE = w.WM_APP + 1
WM_APP_QUIT = w.WM_APP + 2
WM_APP_DEVICE = w.WM_APP + 3
HOTKEY_TOGGLE, HOTKEY_QUIT, HOTKEY_TIMER, HOTKEY_TIMER_RESET = 1, 2, 3, 4
HOTKEYS = {HOTKEY_TOGGLE: "P", HOTKEY_QUIT: "Q", HOTKEY_TIMER: "T", HOTKEY_TIMER_RESET: "R"}
TAG = 0x5EED5EED  # dwExtraInfo untuk input yang kita kirim sendiri

KEYS = {r.NEXT: w.VK_RIGHT, r.PREV: w.VK_LEFT}
# flag -> (MOUSEEVENTF_*, mouseData tetap; None = pakai data asli)
MOUSE_EVENTS = {r.L_DOWN: (0x2, 0), r.L_UP: (0x4, 0), r.R_DOWN: (0x8, 0), r.R_UP: (0x10, 0),
                r.M_DOWN: (0x20, 0), r.M_UP: (0x40, 0), r.BACK_DOWN: (0x80, 1), r.BACK_UP: (0x100, 1),
                r.FWD_DOWN: (0x80, 2), r.FWD_UP: (0x100, 2), r.WHEEL: (0x800, None)}


class Engine(threading.Thread):
    def __init__(self, router, device_id, on_change, on_exit, on_timer, on_devices):
        super().__init__(name="mouse-engine", daemon=True)
        self.router = router
        self.device_id = device_id.lower()
        self.on_change = on_change
        self.on_exit = on_exit
        self.on_timer = on_timer  # dipanggil dengan "toggle" atau "reset"
        self.on_devices = on_devices  # mouse dicolok/dicabut
        self._next_device = self.device_id
        self.ready = threading.Event()
        self.error = None
        self.hotkeys_ok = True
        self.hwnd = None
        self._targets = {}  # hDevice -> apakah mouse target

    def toggle(self):
        self._post(WM_APP_TOGGLE)

    def stop(self):
        self._post(WM_APP_QUIT)

    def set_device(self, device_id):
        self._next_device = device_id.lower()
        self._post(WM_APP_DEVICE)

    def _post(self, msg):
        if self.hwnd:
            w.user32.PostMessageW(self.hwnd, msg, 0, 0)

    def _is_target(self, handle):
        if handle not in self._targets:
            # device_id kosong = belum ada mouse yang dipilih ("" ada di string apa pun).
            self._targets[handle] = bool(self.device_id) and                 self.device_id in w.device_name(handle).lower()
        return self._targets[handle]

    def _run_actions(self, actions):
        for action in actions:
            if action[0] == "key":
                w.send_key(KEYS[action[1]], TAG)
            elif action[0] == "timer":
                self.on_timer(action[1])
            else:
                _, flag, data = action
                event, fixed = MOUSE_EVENTS[flag]
                w.send_mouse(event, r.wheel_delta(data) if fixed is None else fixed, TAG)

    def _set_active(self, active):
        self._run_actions(self.router.set_active(active))
        self.on_change(active)

    def _on_hook(self, n_code, w_param, l_param):
        try:
            if n_code == 0 and self.router.active:
                info = ctypes.cast(l_param, ctypes.POINTER(w.MSLLHOOKSTRUCT)).contents
                flag = r.hook_flag(w_param, info.mouseData)
                if flag and not info.flags & w.LLMHF_INJECTED:
                    swallow, actions = self.router.on_hook(
                        flag, info.mouseData, time.perf_counter())
                    self._run_actions(actions)
                    if swallow:
                        return 1
        except Exception:
            log.exception("hook error")
        return w.user32.CallNextHookEx(None, n_code, w_param, l_param)

    def _on_message(self, hwnd, msg, wp, lp):
        try:
            if msg == w.WM_INPUT and self.router.active:
                raw = w.read_raw_mouse(lp)
                if raw and raw[1]:
                    handle, buttons = raw
                    self._run_actions(self.router.on_raw(
                        buttons, self._is_target(handle), time.perf_counter()))
            elif msg == w.WM_INPUT_DEVICE_CHANGE:
                self._targets.clear()  # handle bisa dipakai ulang oleh perangkat lain
                self.on_devices()
            elif msg == WM_APP_DEVICE:
                self.device_id = self._next_device
                self._targets.clear()
            elif msg == w.WM_TIMER:
                self._run_actions(self.router.tick(time.perf_counter()))
            elif msg == WM_APP_TOGGLE or (msg == w.WM_HOTKEY and wp == HOTKEY_TOGGLE):
                self._set_active(not self.router.active)
            elif msg == WM_APP_QUIT or (msg == w.WM_HOTKEY and wp == HOTKEY_QUIT):
                w.user32.PostQuitMessage(0)
            elif msg == w.WM_HOTKEY and wp == HOTKEY_TIMER:
                self.on_timer("toggle")
            elif msg == w.WM_HOTKEY and wp == HOTKEY_TIMER_RESET:
                self.on_timer("reset")
        except Exception:
            log.exception("message error")
        return w.user32.DefWindowProcW(hwnd, msg, wp, lp)

    def run(self):
        hook = None
        try:
            hinst = w.kernel32.GetModuleHandleW(None)
            self._wndproc = w.WNDPROC(self._on_message)
            self._hookproc = w.HOOKPROC(self._on_hook)
            wc = w.WNDCLASSW(lpfnWndProc=self._wndproc, hInstance=hinst,
                             lpszClassName="MousePointerEngine")
            w.user32.RegisterClassW(ctypes.byref(wc))
            self.hwnd = w.user32.CreateWindowExW(0, wc.lpszClassName, "Mouse Pointer", 0,
                                                 0, 0, 0, 0, wt.HWND(w.HWND_MESSAGE),
                                                 None, hinst, None)
            rid = w.RAWINPUTDEVICE(0x01, 0x02, w.RIDEV_INPUTSINK | w.RIDEV_DEVNOTIFY,
                                   self.hwnd)
            if not w.user32.RegisterRawInputDevices(ctypes.byref(rid), 1, ctypes.sizeof(rid)):
                raise OSError(f"RegisterRawInputDevices gagal ({ctypes.get_last_error()})")
            mods = w.MOD_CONTROL | w.MOD_ALT | w.MOD_NOREPEAT
            self.hotkeys_ok = all([w.user32.RegisterHotKey(self.hwnd, hk_id, mods, ord(key))
                                   for hk_id, key in HOTKEYS.items()])
            w.user32.SetTimer(self.hwnd, 1, 10, None)
            hook = w.user32.SetWindowsHookExW(w.WH_MOUSE_LL, self._hookproc, hinst, 0)
            if not hook:
                raise OSError(f"SetWindowsHookEx gagal ({ctypes.get_last_error()})")
        except Exception as e:
            log.exception("engine start failed")
            self.error = e
            self.ready.set()
            return

        self.ready.set()
        msg = wt.MSG()
        try:
            while w.user32.GetMessageW(ctypes.byref(msg), None, 0, 0) > 0:
                w.user32.TranslateMessage(ctypes.byref(msg))
                w.user32.DispatchMessageW(ctypes.byref(msg))
        finally:
            w.user32.UnhookWindowsHookEx(hook)
            self._run_actions(self.router.set_active(False))
            for hk_id in HOTKEYS:
                w.user32.UnregisterHotKey(self.hwnd, hk_id)
            w.user32.DestroyWindow(self.hwnd)
            self.hwnd = None
            self.on_exit()
