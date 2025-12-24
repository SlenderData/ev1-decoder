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

root = TkinterDnD.Tk()
root.geometry('400x300')
root.title('DV1: EV1 Decoder')

# 一个铺满窗口的容器（关键）
frame = tk.Frame(root)
frame.pack(fill='both', expand=True)

label = tk.Label(
    frame,
    text='Drop *.ev1 anywhere in this window :)',
    font=('Arial', 14)
)
label.place(relx=0.5, rely=0.5, anchor='center')

# ⭐ 重点：给 root 注册拖拽
root.drop_target_register(DND_FILES)
root.dnd_bind('<<Drop>>', dnd_file)

root.mainloop()
