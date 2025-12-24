import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

def convert_ev1(file_path: str):
    if not file_path.lower().endswith('.ev1'):
        return

    print(f"Convert {file_path}")

    with open(file_path, 'rb+') as f:
        raw = f.read(100)
        data = bytearray(raw)
        for i in range(len(data)):
            data[i] ^= 0xff
        f.seek(0)
        f.write(data)

    os.rename(file_path, file_path + '.flv')


def handle_path(path: str):
    if os.path.isfile(path):
        convert_ev1(path)
    elif os.path.isdir(path):
        for root_dir, _, files in os.walk(path):
            for name in files:
                convert_ev1(os.path.join(root_dir, name))


def dnd_file(event):
    paths = root.tk.splitlist(event.data)
    for path in paths:
        handle_path(path.strip('{}'))

    # 放下后恢复背景
    frame.config(bg=default_bg)


def on_drag_enter(event):
    frame.config(bg='#e6f2ff')


def on_drag_leave(event):
    frame.config(bg=default_bg)


root = TkinterDnD.Tk()
root.geometry('400x300')
root.title('DV1: EV1 Decoder')

frame = tk.Frame(root)
frame.pack(fill='both', expand=True)

default_bg = frame.cget('bg')

label = tk.Label(
    frame,
    text='Drop *.ev1 files or folders anywhere :)',
    font=('Arial', 14)
)
label.place(relx=0.5, rely=0.5, anchor='center')

# 整个窗口接收拖拽
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_file)
root.dnd_bind('<<DragEnter>>', on_drag_enter)
root.dnd_bind('<<DragLeave>>', on_drag_leave)

root.mainloop()
