import os
import subprocess
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD


# ===== 全局统计 =====
stats = {
    "ok": 0,
    "fail": 0,
    "skip": 0,
}


# ===== 日志系统 =====
def log(msg: str, path: str | None = None):
    print(msg)
    log_box.config(state='normal')
    start = log_box.index('end-1c')
    log_box.insert('end', msg + '\n')
    end = log_box.index('end-1c')

    # 如果关联了文件路径，打 tag
    if path:
        tag = f"path_{start}"
        log_box.tag_add(tag, start, end)
        log_box.tag_bind(tag, "<Button-1>", lambda e, p=path: reveal_in_finder(p))
        log_box.tag_config(tag, foreground='#0066cc', underline=True)

    log_box.see('end')
    log_box.config(state='disabled')
    update_status()


def clear_log():
    log_box.config(state='normal')
    log_box.delete('1.0', 'end')
    log_box.config(state='disabled')
    stats["ok"] = stats["fail"] = stats["skip"] = 0
    update_status()
    log("Log cleared.")


# ===== Finder =====
def reveal_in_finder(path: str):
    subprocess.run(["open", "-R", path])


# ===== ffprobe 判断 =====
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
    with open(path, "rb+") as f:
        raw = f.read(100)
        data = bytearray(raw)
        for i in range(len(data)):
            data[i] ^= 0xff
        f.seek(0)
        f.write(data)


def convert_file(path: str):
    if is_valid_video(path):
        stats["skip"] += 1
        log(f"Skip (already valid): {path}", path)
        return

    log(f"Decode EV1 → FLV : {path}", path)
    decode_ev1_inplace(path)

    if is_valid_video(path):
        stats["ok"] += 1
        log(f"✓ Converted OK: {path}", path)
    else:
        stats["fail"] += 1
        log(f"✗ Failed to convert: {path}", path)


def handle_path(path: str):
    if os.path.isfile(path):
        convert_file(path)
    elif os.path.isdir(path):
        log(f"Scan folder: {path}")
        for root_dir, _, files in os.walk(path):
            for name in files:
                convert_file(os.path.join(root_dir, name))


# ===== 拖拽 =====
def dnd_file(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        handle_path(path.strip('{}'))

    frame.config(bg=default_bg)
    notify_done()


def on_drag_enter(event):
    frame.config(bg='#e6f2ff')


def on_drag_leave(event):
    frame.config(bg=default_bg)


# ===== 状态 & 通知 =====
def update_status():
    status_var.set(
        f"✓ {stats['ok']}   ✗ {stats['fail']}   → {stats['skip']}"
    )


def notify_done():
    if stats["ok"] + stats["fail"] + stats["skip"] == 0:
        return
    subprocess.run([
        "osascript",
        "-e",
        f'display notification "✓ {stats["ok"]}  ✗ {stats["fail"]}  → {stats["skip"]}" '
        f'with title "EV1 Decoder Finished"'
    ])


# ===== GUI =====
root = TkinterDnD.Tk()
root.geometry('700x480')
root.title('DV1: EV1 → FLV Decoder')

frame = tk.Frame(root)
frame.pack(fill='both', expand=True, padx=10, pady=8)

default_bg = frame.cget('bg')

label = tk.Label(
    frame,
    text='Drop videos or folders here\n',
    font=('Arial', 13),
    justify='center'
)
label.pack(pady=(0, 6))

# 日志区
log_box = tk.Text(
    frame,
    height=14,
    wrap='word',
    state='disabled',
    bg='#f8f8f8'
)
log_box.pack(fill='both', expand=True)

# 控制栏
ctrl = tk.Frame(frame)
ctrl.pack(fill='x', pady=6)

clear_btn = tk.Button(ctrl, text='Clear Log', command=clear_log)
clear_btn.pack(side='left')

status_var = tk.StringVar()
status_label = tk.Label(ctrl, textvariable=status_var, anchor='e')
status_label.pack(side='right')

# 拖拽绑定
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_file)
root.dnd_bind('<<DragEnter>>', on_drag_enter)
root.dnd_bind('<<DragLeave>>', on_drag_leave)

log("Ready. Drop files or folders to start.")
update_status()

root.mainloop()
