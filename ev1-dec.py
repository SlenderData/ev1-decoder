import os
import json
import platform
import subprocess
import tkinter as tk
from tkinter.scrolledtext import ScrolledText
from tkinterdnd2 import TkinterDnD, DND_FILES

# ================= 配置 =================

VIDEO_EXTS = {
    ".mp4", ".mkv", ".avi", ".mov", ".flv", ".webm", ".wmv",
    ".m4v", ".mpg", ".mpeg", ".ts", ".mts", ".m2ts", ".ev1"
}

FORMAT_EXT_MAP = {
    "mp4": ".mp4",
    "mov": ".mov",
    "flv": ".flv",
    "matroska": ".mkv",
    "avi": ".avi",
    "mpegts": ".ts",
    "webm": ".webm",
}

XOR_HEAD_SIZE = 100

# ================= 统计 =================

stat_success = 0
stat_failed = 0
stat_skipped = 0


# ================= ffprobe =================

def get_ffprobe_path():
    base = os.path.dirname(os.path.abspath(__file__))
    arch = platform.machine().lower()
    sub = "arm64(Apple_Silicon)" if arch in ("arm64", "aarch64") else "x86_64(Intel)"
    path = os.path.join(
        base,
        "static_FFmpeg_8.0_binaries",
        sub,
        "ffprobe"
    )
    if not os.path.exists(path):
        raise RuntimeError("ffprobe not found")
    return path


FFPROBE = get_ffprobe_path()


# ================= GUI 工具 =================

def update_status():
    status_var.set(
        f"成功 {stat_success} / 失败 {stat_failed} / 跳过 {stat_skipped}"
    )
    root.update_idletasks()


def log(msg):
    text.insert(tk.END, msg + "\n\n")
    text.see(tk.END)
    root.update_idletasks()


def clear_log():
    global stat_success, stat_failed, stat_skipped
    text.delete("1.0", tk.END)
    stat_success = stat_failed = stat_skipped = 0
    update_status()
    log("日志已清空。")


def notify_done():
    try:
        subprocess.run([
            "osascript",
            "-e",
            'display notification "视频处理已完成" with title "Video Normalizer"'
        ])
    except Exception:
        pass


# ================= 核心逻辑 =================

def should_skip_file(path: str) -> bool:
    name = os.path.basename(path)
    return (
        name.startswith('.') or
        name.startswith('__') or
        name in {'.DS_Store', 'Thumbs.db', 'desktop.ini'}
    )


def is_video_file(path: str) -> bool:
    lower = path.lower()
    return any(lower.endswith(ext) for ext in VIDEO_EXTS)


def ffprobe_format(path: str):
    try:
        p = subprocess.run(
            [
                FFPROBE,
                "-v", "error",
                "-print_format", "json",
                "-show_format",
                path
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=5
        )
        if p.returncode != 0:
            return None
        info = json.loads(p.stdout)
        return info.get("format", {}).get("format_name")
    except Exception:
        return None


def format_to_ext(fmt: str) -> str:
    primary = fmt.split(",")[0]
    return FORMAT_EXT_MAP.get(primary, f".{primary}")


def ev1_decode_inplace(path: str):
    with open(path, "rb+") as f:
        raw = f.read(XOR_HEAD_SIZE)
        data = bytearray(raw)
        for i in range(len(data)):
            data[i] ^= 0xFF
        f.seek(0)
        f.write(data)
        f.flush()
        os.fsync(f.fileno())


def normalize_extension(path: str, fmt: str) -> str:
    new_ext = format_to_ext(fmt)

    base = path
    while True:
        name, ext = os.path.splitext(base)
        if ext.lower() in VIDEO_EXTS:
            base = name
        else:
            break

    new_path = base + new_ext

    if new_path == path:
        return path

    if os.path.exists(new_path):
        base_name, ext = os.path.splitext(new_path)
        counter = 1
        while os.path.exists(new_path):
            new_path = f"{base_name}_{counter}{ext}"
            counter += 1

    os.rename(path, new_path)
    return new_path


def process_file(path: str):
    global stat_success, stat_failed, stat_skipped

    if should_skip_file(path):
        return

    log(f"处理文件：{path}")

    if not is_video_file(path):
        log("跳过（非视频文件）")
        stat_skipped += 1
        update_status()
        return

    fmt = ffprobe_format(path)

    if not fmt:
        log("无法识别，疑似 EV1，开始解码")
        ev1_decode_inplace(path)
        fmt = ffprobe_format(path)

        if not fmt:
            log("❌ 解码后仍无法识别")
            stat_failed += 1
            update_status()
            return

    try:
        new_path = normalize_extension(path, fmt)
        log(f"✅ 完成 → {new_path}")
        stat_success += 1
    except Exception as e:
        log(f"❌ 重命名失败：{e}")
        stat_failed += 1

    update_status()


def process_path(path: str):
    if os.path.isdir(path):
        for root_dir, _, files in os.walk(path):
            for f in files:
                process_file(os.path.join(root_dir, f))
    else:
        process_file(path)


def on_drop(event):
    paths = root.tk.splitlist(event.data)
    for p in paths:
        process_path(p)
    notify_done()


# ================= GUI =================

root = TkinterDnD.Tk()
root.title("Video Normalizer 💅")
root.geometry("760x460")

label = tk.Label(
    root,
    text="拖入视频文件或文件夹\n程序将基于 ffprobe 校正真实视频格式",
    font=("Helvetica", 13)
)
label.pack(pady=8)

toolbar = tk.Frame(root)
toolbar.pack(fill=tk.X, padx=10)

clear_btn = tk.Button(toolbar, text="🧹 清空日志", command=clear_log)
clear_btn.pack(side=tk.LEFT)

text = ScrolledText(root, font=("Menlo", 11))
text.pack(expand=True, fill=tk.BOTH, padx=10, pady=8)

status_var = tk.StringVar()
status_bar = tk.Label(
    root,
    textvariable=status_var,
    anchor="w",
    relief=tk.SUNKEN
)
status_bar.pack(fill=tk.X)

root.drop_target_register(DND_FILES)
root.dnd_bind("<<Drop>>", on_drop)

update_status()
log("Video Normalizer Ready.")
log(f"ffprobe: {FFPROBE}")

root.mainloop()
