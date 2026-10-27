"""Daftar mouse yang sedang terhubung, dengan nama yang bisa dibaca manusia."""
import ctypes
import re

from . import winapi as w

# Satu dongle bisa muncul sebagai beberapa koleksi/interface (&MI_01&Col01, ...).
_SUFFIX = re.compile(r"&(MI_[0-9A-F]+|COL[0-9A-F]+)", re.IGNORECASE)
_VID_PID = re.compile(r"VID[_&]([0-9A-F]+).*?PID[_&]([0-9A-F]+)", re.IGNORECASE)
_GENERIC = ("", "HIDI2C Device")


def device_key(path):
    r"""Path Raw Input -> ID perangkat tanpa nomor interface.

    \\?\HID#VID_3151&PID_3022&MI_01&Col01#7&...#{...} -> VID_3151&PID_3022
    """
    parts = path.split("#")
    if len(parts) < 2:
        return path
    return _SUFFIX.sub("", parts[1])


def label(key, product):
    if product not in _GENERIC:
        return f"{product} ({short_id(key)})"
    if product == "HIDI2C Device":
        return f"Touchpad laptop ({short_id(key)})"
    return f"Mouse ({short_id(key)})"


def short_id(key):
    m = _VID_PID.search(key)
    if m:
        return f"{m.group(1)[-4:].upper()}:{m.group(2)[-4:].upper()}"
    return key


def connected_mice():
    """[(key, label)] untuk setiap mouse fisik yang terhubung, tanpa duplikat."""
    found = {}
    for path in w.mouse_device_names():
        if not path or "RDP_MOU" in path.upper():  # mouse virtual Remote Desktop
            continue
        key = device_key(path)
        if key not in found:
            found[key] = label(key, w.hid_product(path))
    return sorted(found.items(), key=lambda kv: kv[1].lower())
