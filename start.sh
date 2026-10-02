#!/usr/bin/env bash
# ============================================
#  媒体下载器 WebUI - Linux/macOS 启动器
# ============================================
set -e
cd "$(dirname "$0")"

echo "==> 检查 Python..."
if command -v python3 >/dev/null 2>&1; then PY=python3
elif command -v python >/dev/null 2>&1; then PY=python
else echo "❌ 未找到 Python，请先安装 Python 3.8+"; exit 1; fi
$PY --version

echo "==> 准备虚拟环境..."
if [ ! -d "venv" ]; then
  $PY -m venv venv || { echo "❌ 创建 venv 失败"; exit 1; }
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "==> 安装依赖..."
pip install -q --upgrade pip
pip install -q -r requirements.txt
pip install -q yt-dlp 2>/dev/null || echo "⚠️  yt-dlp 安装失败（YouTube功能不可用）"

# 可选依赖提示
command -v ffmpeg >/dev/null 2>&1 || echo "⚠️  未检测到 ffmpeg（视频转码需要，可选）"
command -v yt-dlp >/dev/null 2>&1 || echo "⚠️  未检测到 yt-dlp（YouTube 下载需要，可选）"

PORT="${MEDIA_PORT:-8891}"
echo ""
echo "============================================"
echo "  启动中... 访问: http://localhost:$PORT"
echo "  局域网: http://<本机IP>:$PORT"
echo "  Ctrl+C 停止"
echo "============================================"
echo ""
exec python app.py
