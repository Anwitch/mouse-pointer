"""Deklarasi ctypes untuk Win32 API yang dipakai."""
import ctypes
from ctypes import wintypes as wt

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
hid = ctypes.WinDLL("hid")

LRESULT = ctypes.c_ssize_t
ULONG_PTR = ctypes.c_size_t

WH_MOUSE_LL = 14
LLMHF_INJECTED = 0x1
WM_INPUT_DEVICE_CHANGE = 0x00FE
WM_INPUT = 0x00FF
WM_TIMER = 0x0113
WM_HOTKEY = 0x0312
WM_APP = 0x8000
RID_INPUT = 0x10000003
RIDI_DEVICENAME = 0x20000007
RIM_TYPEMOUSE = 0
RIDEV_INPUTSINK, RIDEV_DEVNOTIFY = 0x100, 0x2000
HWND_MESSAGE = -3
MOD_ALT, MOD_CONTROL, MOD_NOREPEAT = 0x1, 0x2, 0x4000
INPUT_MOUSE, INPUT_KEYBOARD = 0, 1
KEYEVENTF_EXTENDEDKEY, KEYEVENTF_KEYUP = 0x1, 0x2
VK_LEFT, VK_RIGHT = 0x25, 0x27
ERROR_ALREADY_EXISTS = 183
MB_ICONWARNING = 0x30
FILE_SHARE_READ_WRITE = 0x3
OPEN_EXISTING = 3
INVALID_HANDLE_VALUE = wt.HANDLE(-1).value


class MSLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [("pt", wt.POINT), ("mouseData", wt.DWORD), ("flags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class RAWINPUTDEVICE(ctypes.Structure):
    _fields_ = [("usUsagePage", wt.USHORT), ("usUsage", wt.USHORT),
                ("dwFlags", wt.DWORD), ("hwndTarget", wt.HWND)]


class RAWINPUTDEVICELIST(ctypes.Structure):
    _fields_ = [("hDevice", wt.HANDLE), ("dwType", wt.DWORD)]


class RAWINPUTHEADER(ctypes.Structure):
    _fields_ = [("dwType", wt.DWORD), ("dwSize", wt.DWORD),
                ("hDevice", wt.HANDLE), ("wParam", wt.WPARAM)]


class _BTN(ctypes.Structure):
    _fields_ = [("usButtonFlags", wt.USHORT), ("usButtonData", wt.USHORT)]


class _BTNU(ctypes.Union):
    _fields_ = [("ulButtons", wt.ULONG), ("s", _BTN)]


class RAWMOUSE(ctypes.Structure):
    _fields_ = [("usFlags", wt.USHORT), ("u", _BTNU), ("ulRawButtons", wt.ULONG),
                ("lLastX", wt.LONG), ("lLastY", wt.LONG), ("ulExtraInformation", wt.ULONG)]


class RAWINPUT(ctypes.Structure):
    _fields_ = [("header", RAWINPUTHEADER), ("mouse", RAWMOUSE)]


class MOUSEINPUT(ctypes.Structure):
    _fields_ = [("dx", wt.LONG), ("dy", wt.LONG), ("mouseData", wt.DWORD),
                ("dwFlags", wt.DWORD), ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [("wVk", wt.WORD), ("wScan", wt.WORD), ("dwFlags", wt.DWORD),
                ("time", wt.DWORD), ("dwExtraInfo", ULONG_PTR)]


class _INPUTU(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wt.DWORD), ("u", _INPUTU)]


HOOKPROC = ctypes.WINFUNCTYPE(LRESULT, ctypes.c_int, wt.WPARAM, wt.LPARAM)
WNDPROC = ctypes.WINFUNCTYPE(LRESULT, wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM)


class WNDCLASSW(ctypes.Structure):
    _fields_ = [("style", wt.UINT), ("lpfnWndProc", WNDPROC), ("cbClsExtra", ctypes.c_int),
                ("cbWndExtra", ctypes.c_int), ("hInstance", wt.HINSTANCE), ("hIcon", wt.HICON),
                ("hCursor", wt.HANDLE), ("hbrBackground", wt.HBRUSH),
                ("lpszMenuName", wt.LPCWSTR), ("lpszClassName", wt.LPCWSTR)]


def _sig(fn, argtypes, restype=wt.BOOL):
    fn.argtypes, fn.restype = argtypes, restype


_sig(user32.DefWindowProcW, [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM], LRESULT)
_sig(user32.CallNextHookEx, [wt.HHOOK, ctypes.c_int, wt.WPARAM, wt.LPARAM], LRESULT)
_sig(user32.SetWindowsHookExW, [ctypes.c_int, HOOKPROC, wt.HINSTANCE, wt.DWORD], wt.HHOOK)
_sig(user32.UnhookWindowsHookEx, [wt.HHOOK])
_sig(user32.GetRawInputData, [wt.HANDLE, wt.UINT, ctypes.c_void_p,
                              ctypes.POINTER(wt.UINT), wt.UINT], wt.UINT)
_sig(user32.GetRawInputDeviceInfoW, [wt.HANDLE, wt.UINT, ctypes.c_void_p,
                                     ctypes.POINTER(wt.UINT)], wt.UINT)
_sig(user32.GetRawInputDeviceList, [ctypes.c_void_p, ctypes.POINTER(wt.UINT), wt.UINT], wt.UINT)
_sig(user32.RegisterRawInputDevices, [ctypes.POINTER(RAWINPUTDEVICE), wt.UINT, wt.UINT])
_sig(user32.RegisterClassW, [ctypes.POINTER(WNDCLASSW)], wt.ATOM)
_sig(user32.CreateWindowExW, [wt.DWORD, wt.LPCWSTR, wt.LPCWSTR, wt.DWORD, ctypes.c_int,
                              ctypes.c_int, ctypes.c_int, ctypes.c_int, wt.HWND, wt.HMENU,
                              wt.HINSTANCE, wt.LPVOID], wt.HWND)
_sig(user32.DestroyWindow, [wt.HWND])
_sig(user32.SendInput, [wt.UINT, ctypes.POINTER(INPUT), ctypes.c_int], wt.UINT)
_sig(user32.SetTimer, [wt.HWND, ULONG_PTR, wt.UINT, ctypes.c_void_p], ULONG_PTR)
_sig(user32.RegisterHotKey, [wt.HWND, ctypes.c_int, wt.UINT, wt.UINT])
_sig(user32.UnregisterHotKey, [wt.HWND, ctypes.c_int])
_sig(user32.PostMessageW, [wt.HWND, wt.UINT, wt.WPARAM, wt.LPARAM])
_sig(user32.GetMessageW, [ctypes.POINTER(wt.MSG), wt.HWND, wt.UINT, wt.UINT])
_sig(user32.TranslateMessage, [ctypes.POINTER(wt.MSG)])
_sig(user32.DispatchMessageW, [ctypes.POINTER(wt.MSG)], LRESULT)
_sig(user32.PostQuitMessage, [ctypes.c_int], None)
_sig(user32.MessageBoxW, [wt.HWND, wt.LPCWSTR, wt.LPCWSTR, wt.UINT], ctypes.c_int)
_sig(user32.GetParent, [wt.HWND], wt.HWND)
_sig(user32.GetWindowLongW, [wt.HWND, ctypes.c_int], wt.LONG)
_sig(user32.SetWindowLongW, [wt.HWND, ctypes.c_int, wt.LONG], wt.LONG)
_sig(user32.SetWindowPos, [wt.HWND, wt.HWND, ctypes.c_int, ctypes.c_int, ctypes.c_int,
                           ctypes.c_int, wt.UINT])
_sig(kernel32.GetModuleHandleW, [wt.LPCWSTR], wt.HMODULE)
_sig(kernel32.CreateMutexW, [ctypes.c_void_p, wt.BOOL, wt.LPCWSTR], wt.HANDLE)
_sig(kernel32.CreateFileW, [wt.LPCWSTR, wt.DWORD, wt.DWORD, ctypes.c_void_p, wt.DWORD,
                            wt.DWORD, wt.HANDLE], wt.HANDLE)
_sig(kernel32.CloseHandle, [wt.HANDLE])
_sig(hid.HidD_GetProductString, [wt.HANDLE, ctypes.c_void_p, wt.ULONG], wt.BOOLEAN)


def device_name(handle):
    if not handle:
        return ""
    n = wt.UINT(0)
    user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, None, ctypes.byref(n))
    buf = ctypes.create_unicode_buffer(n.value + 1)
    user32.GetRawInputDeviceInfoW(handle, RIDI_DEVICENAME, buf, ctypes.byref(n))
    return buf.value


def mouse_device_names():
    n = wt.UINT(0)
    size = ctypes.sizeof(RAWINPUTDEVICELIST)
    user32.GetRawInputDeviceList(None, ctypes.byref(n), size)
    arr = (RAWINPUTDEVICELIST * n.value)()
    user32.GetRawInputDeviceList(arr, ctypes.byref(n), size)
    return [device_name(d.hDevice) for d in arr[:n.value] if d.dwType == RIM_TYPEMOUSE]


def hid_product(path):
    """Nama produk HID (mis. "2.4G Mouse"), atau "" kalau tidak tersedia."""
    # Akses 0: cukup untuk membaca atribut walau mouse dibuka eksklusif oleh Windows.
    handle = kernel32.CreateFileW(path, 0, FILE_SHARE_READ_WRITE, None, OPEN_EXISTING, 0, None)
    if not handle or handle == INVALID_HANDLE_VALUE:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(127)
        if not hid.HidD_GetProductString(handle, buf, ctypes.sizeof(buf)):
            return ""
        return buf.value.strip()
    finally:
        kernel32.CloseHandle(handle)


def read_raw_mouse(l_param):
    """Return (hDevice, usButtonFlags) dari pesan WM_INPUT, atau None."""
    size = wt.UINT(0)
    hdr = ctypes.sizeof(RAWINPUTHEADER)
    user32.GetRawInputData(l_param, RID_INPUT, None, ctypes.byref(size), hdr)
    buf = ctypes.create_string_buffer(max(size.value, ctypes.sizeof(RAWINPUT)))
    if user32.GetRawInputData(l_param, RID_INPUT, buf, ctypes.byref(size), hdr) == 0xFFFFFFFF:
        return None
    ri = RAWINPUT.from_buffer(buf)
    if ri.header.dwType != RIM_TYPEMOUSE:
        return None
    return ri.header.hDevice, ri.mouse.u.s.usButtonFlags


def send_key(vk, tag):
    arr = (INPUT * 2)()
    for i, up in enumerate((0, KEYEVENTF_KEYUP)):
        arr[i].type = INPUT_KEYBOARD
        arr[i].u.ki = KEYBDINPUT(vk, 0, KEYEVENTF_EXTENDEDKEY | up, 0, tag)
    user32.SendInput(2, arr, ctypes.sizeof(INPUT))


def send_mouse(event_flags, mouse_data, tag):
    inp = INPUT(type=INPUT_MOUSE)
    inp.u.mi = MOUSEINPUT(0, 0, mouse_data & 0xFFFFFFFF, event_flags, 0, tag)
    user32.SendInput(1, ctypes.byref(inp), ctypes.sizeof(INPUT))
