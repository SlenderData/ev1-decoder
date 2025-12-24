import os
import subprocess
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD


# ===== 日志工具 =====
def log(msg: str):
    print(msg)
    log_box.config(state='normal')
    log_box.insert('end', msg + '\n')
    log_box.see('end')
    log_box.config(state='disabled')


# ===== ffmpeg 判断 =====
def is_valid_video(path: str) -> bool:
    try:
        result = subprocess.run(
            [
                "ffprobe",
                "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=codec_name",
                "-of", "default=noprint_wrappers=1:nokey=1",
                path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=3
        )
        return result.returncode == 0 and bool(result.stdout.strip())
    except Exception:
        return False


# ===== EV1 解码 =====
def decode_ev1_inplace(path: str):
    log(f"Decode EV1 → FLV : {path}")

    with open(path, "rb+") as f:
        raw = f.read(100)
        data = bytearray(raw)
        for i in range(len(data)):
            data[i] ^= 0xff
        f.seek(0)
        f.write(data)


def convert_file(path: str):
    if is_valid_video(path):
        log(f"Skip (already valid): {path}")
        return

    decode_ev1_inplace(path)

    if is_valid_video(path):
        log(f"✓ Converted OK: {path}")
    else:
        log(f"✗ Failed to convert: {path}")


def handle_path(path: str):
    if os.path.isfile(path):
        convert_file(path)
    elif os.path.isdir(path):
        log(f"Scan folder: {path}")
        for root_dir, _, files in os.walk(path):
            for name in files:
                convert_file(os.path.join(root_dir, name))


# ===== 拖拽回调 =====
def dnd_file(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        handle_path(path.strip('{}'))
    frame.config(bg=default_bg)


def on_drag_enter(event):
    frame.config(bg='#e6f2ff')


def on_drag_leave(event):
    frame.config(bg=default_bg)


# ===== GUI =====
root = TkinterDnD.Tk()
root.geometry('600x420')
root.title('DV1: EV1 → FLV Decoder')

frame = tk.Frame(root)
frame.pack(fill='both', expand=True, padx=8, pady=8)

default_bg = frame.cget('bg')

label = tk.Label(
    frame,
    text='Drop videos or folders here\n(EV1 disguised as *.mp4.flv supported)',
    font=('Arial', 13),
    justify='center'
)
label.pack(pady=(0, 8))

# 日志窗口
log_box = tk.Text(
    frame,
    height=12,
    wrap='word',
    state='disabled',
    bg='#f8f8f8'
)
log_box.pack(fill='both', expand=True)

# 拖拽绑定
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_file)
root.dnd_bind('<<DragEnter>>', on_drag_enter)
root.dnd_bind('<<DragLeave>>', on_drag_leave)

log("Ready. Drop files or folders to start.")

root.mainloop()
