@echo off
chcp 65001 >nul
REM ============================================
REM   媒体下载器 WebUI - Windows 启动器
REM ============================================
cd /d "%~dp0"

echo ==^> 检查 Python...
where python >nul 2>nul
if errorlevel 1 (
    echo [X] 未找到 Python，请先安装 Python 3.8+ 并勾选 Add to PATH
    pause
    exit /b 1
)
python --version

echo ==^> 准备虚拟环境...
if not exist "venv" (
    python -m venv venv
    if errorlevel 1 ( echo [X] 创建 venv 失败 & pause & exit /b 1 )
)
call venv\Scripts\activate.bat

echo ==^> 安装依赖...
python -m pip install -q --upgrade pip
python -m pip install -q -r requirements.txt

where ffmpeg >nul 2>nul
if errorlevel 1 echo [!] 未检测到 ffmpeg（视频转码需要，可选）
where yt-dlp >nul 2>nul
if errorlevel 1 echo [!] 未检测到 yt-dlp（YouTube 下载需要，可选）

if "%MEDIA_PORT%"=="" set MEDIA_PORT=8891
echo.
echo ============================================
echo   启动中... 访问: http://localhost:%MEDIA_PORT%
echo   局域网: http://^<本机IP^>:%MEDIA_PORT%
echo   关闭本窗口即停止
echo ============================================
echo.
python app.py
pause
