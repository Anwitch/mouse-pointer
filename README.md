# Mouse Pointer

Mengubah mouse biasa (wireless atau kabel) jadi pointer presentasi untuk Canva,
PowerPoint, PDF, dan apa pun yang pindah slide dengan tombol panah. Hanya mouse
yang dipilih yang berubah; touchpad dan mouse lain tetap normal, jadi laptop
tetap bisa dipakai seperti biasa.

Dibuat karena aku tidak punya pointer presentasi, tapi punya mouse wireless.

Khusus Windows 10/11.

## Fitur

| Tombol mouse presentasi | Jadi |
|---|---|
| Klik kiri, tombol samping depan, scroll ke bawah | Slide berikutnya (panah kanan) |
| Klik kanan, tombol samping belakang, scroll ke atas | Slide sebelumnya (panah kiri) |
| Klik tengah (tekan roda) | Mulai / jeda timer |
| Gerakan | Normal |

- **Timer presentasi** di pojok layar, selalu di atas slide, klik tembus.
  Putih = berjalan, abu-abu = dijeda, kuning + bip = sisa 1 menit,
  merah + 3 bip panjang = waktu habis, lalu menghitung kelebihan (`+00:12`).
- **Pilih mouse dari menu tray.** Mouse yang terhubung terdeteksi otomatis,
  termasuk saat dongle dicolok atau dicabut.
- Ikon di system tray: hijau = mode presentasi, abu-abu = mouse normal.

## Instal

Butuh [Python 3.10+](https://www.python.org/downloads/).

```
git clone https://github.com/Anwitch/mouse-pointer.git
cd mouse-pointer
pip install -r requirements.txt
```

Jalankan dengan klik dua kali `mouse_pointer.pyw`. Supaya gampang, buat
shortcut ke file itu di Desktop (klik kanan > Kirim ke > Desktop) dan ganti
ikonnya dengan `mouse_pointer.ico`.

## Pakai

1. Buka aplikasinya. Ikon bulat muncul di system tray.
2. Klik kanan ikon > **Pilih mouse**, lalu pilih mouse yang mau dipakai untuk
   presentasi. Pilihan ini tersimpan.
3. Buka slide dalam mode presentasi, lalu klik untuk pindah slide.

| Shortcut | Fungsi |
|---|---|
| `Ctrl+Alt+P` atau klik ikon tray | Mode presentasi on/off |
| `Ctrl+Alt+T` | Mulai / jeda timer |
| `Ctrl+Alt+R` | Reset timer (timer disembunyikan) |
| `Ctrl+Alt+Q` atau menu tray > Keluar | Tutup aplikasi, semua kembali normal |

Durasi timer diatur dari menu tray > **Durasi timer**. Menu **Tes bunyi
peringatan** memutar bunyi sisa-satu-menit untuk mengecek volume sebelum tampil.

## Setting (`config.json`)

Dibuat otomatis saat memilih mouse atau durasi. Pengaturan lain bisa diubah
manual; tutup lalu buka lagi aplikasinya setelah mengubah.

| Kunci | Default | Arti |
|---|---|---|
| `device` | `""` | ID mouse presentasi (diisi lewat menu Pilih mouse) |
| `start_active` | `true` | Langsung mode presentasi saat dibuka |
| `wheel_interval` | `0.25` | Jeda minimal antar slide saat scroll (detik) |
| `timer_minutes` | `10` | Durasi timer |
| `timer_warning_seconds` | `60` | Kapan peringatan berbunyi |
| `timer_position` | `top-left` | `top-left`, `top-right`, `bottom-left`, `bottom-right` |
| `timer_font_size` | `26` | Ukuran teks timer |
| `timer_sound` | `true` | Bunyi peringatan |

## Cara kerja

Windows tidak memberi tahu dari mouse mana sebuah klik berasal kalau hanya
memakai hook biasa. Aplikasi ini memakai dua jalur sekaligus:

- **Low-level mouse hook** untuk menahan atau meneruskan klik.
- **Raw Input** untuk tahu perangkat asal klik itu.

Keduanya melaporkan klik yang sama secara terpisah dan urutannya bisa terbalik,
jadi klik ditahan sebentar (paling lama 60 ms) sampai asalnya diketahui. Klik dari
mouse presentasi diubah jadi tombol panah, klik dari perangkat lain diteruskan
apa adanya. Logika ini ada di `mouse_pointer/router.py` dan diuji tanpa Win32.

Bunyi timer dibuat sebagai WAV di memori (`mouse_pointer/sound.py`), bukan
`winsound.Beep`, karena buzzer bawaan PC tidak bersuara di banyak laptop.

## Keterbatasan

- Hanya Windows.
- Tombol panah tidak sampai ke aplikasi yang berjalan sebagai Administrator,
  kecuali Mouse Pointer juga dijalankan sebagai Administrator.
- Dua mouse dengan model yang sama (ID sama) dianggap satu perangkat.

## Pengembangan

```
pip install -r requirements.txt
python -m unittest discover -s tests -t .
```

Error dicatat di `mouse_pointer.log`.

## Lisensi

[MIT](LICENSE)
