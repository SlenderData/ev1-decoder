import os
import locale
import tkinter as tk
from tkinterdnd2 import DND_FILES, TkinterDnD

def dnd_file(event):
    files = root.tk.splitlist(event.data)
    for file in files:
        file = file.strip('{}')  # mac 拖拽路径可能带 {}

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

# 编码（mac 这里基本用不到 decode 了）
sys_enc = locale.getpreferredencoding()

root = TkinterDnD.Tk()
root.geometry('400x300')
root.title('DV1: EV1 Decoder (mac)')

label = tk.Label(root, text='Drop *.ev1 on me :)', font=('Arial', 14))
label.pack(expand=True)

label.drop_target_register(DND_FILES)
label.dnd_bind('<<Drop>>', dnd_file)

root.mainloop()
