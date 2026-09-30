# Media Downloader WebUI

一个轻量的媒体下载 Web 服务：粘贴 Twitter/X、Bluesky、YouTube 或图片链接，自动解析并下载媒体（图片/视频/GIF）到本机。

## ✨ 功能

- 🐦 **Twitter / X**：支持引用转推、多图、多视频，图片自动取高清
- 📘 **Bluesky**：图片 / 视频全解析
- 🎬 **YouTube**：yt-dlp 下载最高画质
- 🖼️ **GIF / 图片**：直接下载
- 🌐 **网页界面**：粘贴链接即用，支持预览 + 下载
- 🔌 **可配置代理**：适合需要科学上网的环境

## 🚀 快速开始

### Linux / macOS
```bash
chmod +x start.sh
./start.sh
```

### Windows
双击 `start.bat`

启动后访问：**http://localhost:8891**（局域网用 `http://<本机IP>:8891`）

> 首次启动会自动创建虚拟环境并安装依赖。

## ⚙️ 配置（环境变量）

| 变量 | 默认值 | 说明 |
|---|---|---|
| `MEDIA_PORT` | `8891` | 服务端口 |
| `MEDIA_HOST` | `0.0.0.0` | 监听地址 |
| `MEDIA_PROXY` | `http://127.0.0.1:7890` | 代理地址（访问外网媒体用；不需要可留空）|
| `MEDIA_DL_DIR` | `./downloads` | 下载文件保存目录 |
| `MEDIA_MAX_MB` | `200` | 单文件最大 MB |

示例：
```bash
MEDIA_PORT=9000 MEDIA_PROXY=http://127.0.0.1:7890 ./start.sh
```

## 📦 依赖

- Python 3.8+
- Python 包：`flask`, `aiohttp`（启动器自动安装）
- **可选**（增强功能）：
  - `ffmpeg` —— 视频转码为 QQ 兼容格式（可选）
  - `yt-dlp` —— YouTube 下载（可选）

## 📁 项目结构

```
media-webui/
├── app.py                 # Flask 后端（解析 + 下载）
├── templates/index.html   # 前端页面
├── requirements.txt
├── start.sh               # Linux/macOS 启动器
├── start.bat              # Windows 启动器
└── downloads/             # 下载文件（自动创建）
```

## 📖 说明

- 文件下载到服务器后，可通过页面预览或点击「下载」保存到本机
- 建议定期清理 `downloads/` 目录
- 视频转码依赖 `ffmpeg`（无音轨视频会尝试补静音轨）

## 📄 License

MIT
