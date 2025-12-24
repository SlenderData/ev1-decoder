import os
import sys
import json
import platform
import subprocess
import time
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
    text.insert(tk.END, msg + "\n")
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
            'display notification "EV1 转换已完成" with title "EV1 Decoder"'
        ])
    except Exception:
        pass


# ================= 核心逻辑 =================

def is_video_file(path: str) -> bool:
    name = path.lower()
    return any(name.endswith(ext) for ext in VIDEO_EXTS)


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


def process_file(path: str):
    global stat_success, stat_failed, stat_skipped

    if not is_video_file(path):
        stat_skipped += 1
        update_status()
        return

    fmt = ffprobe_format(path)
    print(fmt)
    if fmt:
        log(f"跳过（正常视频 {fmt}）：{path}")
        stat_skipped += 1
        update_status()
        time.sleep(1)
        return

    log(f"疑似 EV1，解码中：{path}")
    ev1_decode_inplace(path)

    fmt_after = ffprobe_format(path)
    if not fmt_after:
        log(f"❌ 解码失败：{path}")
        stat_failed += 1
        update_status()
        return

    new_ext = format_to_ext(fmt_after)
    base = path
    removed_exts = []
    while True:
        name, ext = os.path.splitext(base)
        if ext.lower() in VIDEO_EXTS:
            removed_exts.append(ext)
            base = name
        else:
            break
    new_path = base + new_ext

    # 安全重命名
    if new_path != path:
        if os.path.exists(new_path):
            # 生成唯一文件名
            base_name, ext = os.path.splitext(new_path)
            counter = 1
            while os.path.exists(new_path):
                new_path = f"{base_name}_{counter}{ext}"
                counter += 1
            log(f"⚠️ 目标文件已存在,重命名为：{new_path}")

        try:
            os.rename(path, new_path)
        except Exception as e:
            log(f"❌ 重命名失败 ({e})：{path}")
            stat_failed += 1
            update_status()
            return

    log(f"✅ 完成 → {new_path}")
    stat_success += 1
    update_status()


def process_path(path: str):
    if os.path.isdir(path):
        for root_dir, _, files in os.walk(path):
            for f in files:
                # 跳过 macOS 隐藏文件
                if f.startswith('._') or f.startswith('.'):
                    continue
                process_file(os.path.join(root_dir, f))
    else:
        # 单文件也要检查
        if not os.path.basename(path).startswith('.'):
            process_file(path)


def on_drop(event):
    paths = root.tk.splitlist(event.data)
    for p in paths:
        process_path(p)
    notify_done()


# ================= GUI =================

root = TkinterDnD.Tk()
root.title("EV1 Decoder 💅")
root.geometry("760x460")

label = tk.Label(
    root,
    text="拖入文件或文件夹\n程序将自动识别 EV1 并恢复为真实视频格式",
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
log("EV1 Decoder Ready.")
log(f"ffprobe: {FFPROBE}")

root.mainloop()
