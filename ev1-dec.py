import os
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

def dnd_file(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        file = file.strip('{}')

        if not file.lower().endswith('.ev1'):
            print(f"Ignore {file}")
            continue

        print(f"Convert {file}")

        with open(file, 'rb+') as f:
            raw = f.read(100)
            data = bytearray(raw)
            for i in range(len(data)):
                data[i] ^= 0xff
            f.seek(0)
            f.write(data)

        os.rename(file, file + '.flv')

    # 放下文件后恢复背景
    frame.config(bg=default_bg)

def on_drag_enter(event):
    frame.config(bg='#e6f2ff')  # 淡蓝色高亮

def on_drag_leave(event):
    frame.config(bg=default_bg)

root = TkinterDnD.Tk()
root.geometry('400x300')
root.title('DV1: EV1 Decoder')

# 整个窗口的容器
frame = tk.Frame(root)
frame.pack(fill='both', expand=True)

default_bg = frame.cget('bg')

label = tk.Label(
    frame,
    text='Drop *.ev1 anywhere in this window :)',
    font=('Arial', 14)
)
label.place(relx=0.5, rely=0.5, anchor='center')

# ⭐ 关键：给整个窗口注册拖拽
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_file)
root.dnd_bind('<<DragEnter>>', on_drag_enter)
root.dnd_bind('<<DragLeave>>', on_drag_leave)

root.mainloop()
