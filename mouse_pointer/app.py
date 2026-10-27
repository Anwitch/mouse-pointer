"""Ikon tray + konfigurasi. Titik masuk aplikasi."""
import ctypes
import json
import logging
import sys
import threading
from pathlib import Path

import pystray
from PIL import Image, ImageDraw

from . import sound
from . import winapi as w
from .devices import connected_mice, short_id
from .engine import Engine
from .overlay import SOUNDS, TimerOverlay
from .router import Router
from .timer import RUNNING, WARNING

# Versi .exe (PyInstaller) membongkar kode ke folder sementara; config dan log
# disimpan di samping .exe-nya.
ROOT = (Path(sys.executable).parent if getattr(sys, "frozen", False)
        else Path(__file__).resolve().parent.parent)
CONFIG_FILE = ROOT / "config.json"
LOG_FILE = ROOT / "mouse_pointer.log"
DEFAULTS = {"device": "", "wheel_interval": 0.25, "start_active": True,
            "timer_minutes": 10, "timer_warning_seconds": 60, "timer_position": "top-left",
            "timer_font_size": 26, "timer_sound": True}
DURATIONS = (3, 5, 7, 10, 15, 20, 30)
APP_NAME = "Mouse Pointer"


def load_config():
    cfg = dict(DEFAULTS)
    try:
        cfg.update(json.loads(CONFIG_FILE.read_text(encoding="utf-8")))
    except FileNotFoundError:
        pass
    return cfg


def save_config(cfg):
    CONFIG_FILE.write_text(json.dumps(cfg, indent=2) + "\n", encoding="utf-8")


def make_icon(active):
    img = Image.new("RGBA", (64, 64), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    d.ellipse((2, 2, 62, 62), fill=(34, 160, 90) if active else (128, 128, 128))
    d.polygon([(24, 16), (24, 48), (50, 32)], fill="white")
    return img


def message_box(text):
    w.user32.MessageBoxW(None, text, APP_NAME, w.MB_ICONWARNING)


def main():
    logging.basicConfig(filename=LOG_FILE, level=logging.WARNING,
                        format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    try:
        ctypes.windll.shcore.SetProcessDpiAwareness(1)  # teks timer tajam di layar HiDPI
    except OSError:
        pass

    # Cegah dua instance: dua hook akan menelan klik dua kali.
    _mutex = w.kernel32.CreateMutexW(None, False, "Local\\MousePointerPresenter")
    if ctypes.get_last_error() == w.ERROR_ALREADY_EXISTS:
        message_box("Mouse Pointer sudah berjalan. Lihat ikonnya di system tray.")
        return

    cfg = load_config()
    router = Router(active=cfg["start_active"], wheel_interval=cfg["wheel_interval"])
    overlay = TimerOverlay(cfg["timer_minutes"], cfg["timer_warning_seconds"],
                           cfg["timer_position"], cfg["timer_font_size"], cfg["timer_sound"])
    icon = pystray.Icon(APP_NAME)

    def refresh(active):
        icon.icon = make_icon(active)
        icon.title = (f"{APP_NAME}: {'MODE PRESENTASI' if active else 'mouse normal'}"
                      " (Ctrl+Alt+P)")
        icon.update_menu()

    def on_exit():
        icon.stop()
        overlay.post("quit")

    def set_minutes(minutes):
        cfg["timer_minutes"] = minutes
        save_config(cfg)
        overlay.post("duration", minutes * 60)

    def duration_item(minutes):
        return pystray.MenuItem(f"{minutes} menit", lambda: set_minutes(minutes),
                                checked=lambda _: cfg["timer_minutes"] == minutes, radio=True)

    mice = connected_mice()

    def set_device(key, name):
        cfg["device"] = key
        save_config(cfg)
        engine.set_device(key)
        icon.update_menu()
        icon.notify(f"Mouse presentasi: {name}", APP_NAME)

    def device_item(key, name):
        # "&" di menu Win32 berarti huruf pintas; "&&" menampilkan "&".
        return pystray.MenuItem(name.replace("&", "&&"), lambda: set_device(key, name),
                                checked=lambda _: cfg["device"].lower() == key.lower(), radio=True)

    def device_items():
        items = [device_item(key, name) for key, name in mice]
        if cfg["device"] and not any(cfg["device"].lower() in k.lower() for k, _ in mice):
            items.append(pystray.MenuItem(f"{short_id(cfg['device'])} (tidak terhubung)", None,
                                          checked=lambda _: True, radio=True, enabled=False))
        return items or [pystray.MenuItem("Tidak ada mouse terdeteksi", None, enabled=False)]

    devices_lock = threading.Lock()  # satu colokan bisa memicu beberapa notifikasi sekaligus

    def refresh_devices():
        with devices_lock:
            mice[:] = connected_mice()
            icon.update_menu()

    engine = Engine(router, cfg["device"], on_change=refresh, on_exit=on_exit,
                    on_timer=overlay.post,
                    # Jangan kerja di thread engine: thread itu juga melayani hook mouse.
                    on_devices=lambda: threading.Thread(target=refresh_devices,
                                                        daemon=True).start())
    icon.menu = pystray.Menu(
        pystray.MenuItem(
            lambda _: "Matikan mode presentasi" if router.active else "Aktifkan mode presentasi",
            lambda: engine.toggle(), default=True),
        pystray.MenuItem("Pilih mouse", pystray.Menu(device_items)),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem(
            lambda _: ("Jeda timer" if overlay.timer.state == RUNNING else "Mulai timer")
            + "  (Ctrl+Alt+T / klik tengah)",
            lambda: overlay.post("toggle")),
        pystray.MenuItem("Reset timer  (Ctrl+Alt+R)", lambda: overlay.post("reset")),
        pystray.MenuItem("Durasi timer", pystray.Menu(*map(duration_item, DURATIONS))),
        pystray.MenuItem("Tes bunyi peringatan", lambda: sound.play(SOUNDS[WARNING])),
        pystray.Menu.SEPARATOR,
        pystray.MenuItem("Keluar  (Ctrl+Alt+Q)", lambda: engine.stop()))

    engine.start()
    engine.ready.wait()
    if engine.error:
        message_box(f"Gagal memulai: {engine.error}")
        return
    refresh(router.active)

    def setup(ic):
        ic.visible = True
        found = any(cfg["device"].lower() in k.lower() for k, _ in mice)
        if not engine.hotkeys_ok:
            ic.notify("Sebagian shortcut Ctrl+Alt dipakai aplikasi lain. "
                      "Pakai menu ikon tray.", APP_NAME)
        elif not cfg["device"]:
            ic.notify("Pilih mouse untuk presentasi: klik kanan ikon tray > Pilih mouse.",
                      APP_NAME)
        elif not found:
            ic.notify("Mouse presentasi belum terdeteksi. Colokkan dongle-nya; "
                      "akan langsung dikenali.", APP_NAME)
        else:
            ic.notify("Mode presentasi " + ("AKTIF" if router.active else "mati")
                      + ". Klik tengah mouse = mulai/jeda timer.", APP_NAME)

    # Di Windows pystray boleh jalan di thread lain; thread utama untuk tkinter.
    threading.Thread(target=icon.run, args=(setup,), name="tray", daemon=True).start()
    overlay.run()
