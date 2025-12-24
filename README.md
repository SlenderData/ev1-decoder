# VideoNormalizer 💅

**基于 ffprobe 的视频文件真实性校正器**

校正视频文件的真实格式，无论是 EV1 混淆文件还是后缀错误的视频，都能自动识别并重命名。**注意：本项目暂时仅支持 macOS。**

---

## ⚠️ 系统与依赖要求

* **操作系统**：macOS

  * 测试环境：macOS 26
* **Python**：3.14
* **ffmpeg / ffprobe**：8.0
* **CPU 架构**：

  * ARM64 (Apple Silicon) ✅ 已测试运行通过
  * x86_64 (Intel) ⚠️ 未测试，但理论上可运行

---

## 🚀 快速使用

1. 克隆或下载项目
2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 启动 GUI：

```bash
python VideoNormalizer.py
```

4. 拖入视频文件或文件夹，程序会自动：

* 判断是否为视频文件
* 检测文件真实格式
* 对 EV1 文件进行解码
* 规范化文件后缀
* 在日志窗口显示处理信息
* 处理完成后发送 macOS 原生通知

![VideoNormalizer Screenshot](example.gif)

---

## ⚡ 特性

* 支持常见视频格式：`.mp4`, `.mov`, `.flv`, `.mkv`, `.avi`, `.ts` 等
* 自动处理 EV1 混淆文件
* 拖拽文件夹可批量处理
* GUI 显示日志和底部状态栏
* 安全机制：解码失败自动回滚，避免文件损坏
* 内置 ffprobe，无需额外安装

---

## 🛠 打包

生成 macOS `.app`：

```bash
pip install pyinstaller
pyinstaller \
    --name "VideoNormalizer" \
    --windowed \
    --add-data "static_FFmpeg_8.0_binaries:static_FFmpeg_8.0_binaries" \
    VideoNormalizer.py
```

* 打包完成后 `.app` 位于 `dist/VideoNormalizer.app`
* 内置 ffprobe，直接拖入文件即可使用

---

## 📌 使用建议

* 拖拽整个文件夹可批量处理
* GUI 会实时显示处理日志与状态
* 处理完成后会发送 macOS 原生通知

