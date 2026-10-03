# 媒体下载项目 · 进度状态（暂停点）

> 更新时间：2026-10-03 17:00（APK 构建完成）

## 最新进展（2026-10-03）
- ✅ **Android App 本地构建成功**：`/home/debug/media-downloader-app/dist/media-downloader-app-debug.apk`（27K，`com.zaiens.mediadl`，minSdk21/target34）
- ✅ **App 交互＝8891 旧版**：多行批量粘贴 → 自动拆分链接 → 解析并直接下载到系统「下载」目录 → 卡片展示结果（非勾选模式）
- ✅ **下载走手机网络 + 本地代理**：HttpURLConnection 直连源站（不经服务器），新增显式读取系统代理（clash 的 host:port）并应用到连接，TUN/系统代理模式均生效
- ✅ 同步 GitHub：已推 `origin/main`；`build.yml` 因 token 缺 `workflow` scope 暂不入库
- 🛠 环境：Gradle 8.7（`/opt/gradle-8.7`）、Android SDK（platforms;android-34、build-tools;34.0.0、platform-tools）已装

## 一、项目概览
两个子项目：
1. **WebUI（服务端版）** — 已完成 ✅
2. **Android App（原生下载器）** — 代码完成，待构建 APK ⏳

---

## 二、WebUI（已完成）

- **目录**：`/home/debug/media-webui/`
- **GitHub**：https://github.com/Zaienscookie/media-downloader-webui
- **状态**：✅ 完成，systemd 服务运行中（开机自启）
- **访问**：`http://192.168.2.126:8891`（局域网）
- **管理**：`systemctl restart/stop media-webui`
- **文件**：`app.py`（Flask 后端，配置化）、`templates/index.html`、`start.sh`（Linux）、`start.bat`（Windows）、`requirements.txt`、`README.md`
- **配置**：环境变量 `MEDIA_PORT` / `MEDIA_PROXY` / `MEDIA_DL_DIR` / `MEDIA_MAX_MB`
- **能力**：Twitter/X（含引用转推、多图多视频）、Bluesky、YouTube(yt-dlp)、GIF/图片

---

## 三、Android App（待构建 APK）

- **目录**：`/home/debug/media-downloader-app/`
- **GitHub**：https://github.com/Zaienscookie/media-downloader-app（**已同步**；`.github/workflows/build.yml` 因 token 缺 `workflow` scope 未入库）
- **APK**：✅ **已构建** → `dist/media-downloader-app-debug.apk`（批量粘贴解析下载 + 手机本地代理）
- **界面**：8891 旧版交互（多行批量粘贴→拆分→直接下载→卡片结果）
- **设计**：**原生 App**（非 WebView 壳）— App 内直接请求 fxtwitter/Bluesky API，用**手机网络**下载到系统「下载」目录；手机开 clash 全局即走代理
- **文件**：
  - `app/src/main/java/com/zaiens/mediadl/MainActivity.java`（原生下载器，9.2KB）
  - `app/build.gradle`、`build.gradle`、`settings.gradle`、`gradle.properties`
  - `app/src/main/AndroidManifest.xml`
  - `.github/workflows/build.yml`（GitHub Actions 构建，因 token 缺 workflow scope 未推）

### 待办 · 方式 A：本地构建（推荐，避开 token 问题）
Android commandline-tools 已下载到 `/opt/android-sdk/cmdline-tools/`（147MB 已解压）。继续步骤：
```bash
cd /opt/android-sdk/cmdline-tools && mv cmdline-tools latest
export ANDROID_HOME=/opt/android-sdk
yes | /opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$ANDROID_HOME --licenses
/opt/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$ANDROID_HOME "platform-tools" "platforms;android-34" "build-tools;34.0.0"
cd /home/debug/media-downloader-app && gradle assembleDebug
# 产物：app/build/outputs/apk/debug/app-debug.apk
```

### 待办 · 方式 B：GitHub Actions
- 需 token 增加 `workflow` scope 才能推 workflow 文件；或网页手动创建

---

## 四、关键信息

- **服务器**：2.126（本机，4核7.5G，`192.168.2.126`）
- **clash 代理**：`http://127.0.0.1:7890`
- **已装**：ffmpeg、deno（`/usr/local/bin/deno`）、JDK17（`/usr/lib/jvm/java-17-openjdk-amd64`）
- **可用 python**：`/home/debug/qqbot/qqbot/new-zaiens/astrbot/.venv/bin/python`（含 flask + aiohttp）
- **yt-dlp**：astrbot venv 内
- **GitHub token**：`（token 已脱敏）`（scope: `repo`，**缺 `workflow`**）
- **提交邮箱**：`160210221+Zaienscookie@users.noreply.github.com`

---

## 五、相关

- AstrBot 插件 `astrbot_plugin_media_bridge`（v1.3.x，共用同一套解析逻辑）已推：https://github.com/Zaienscookie/astrbot_plugin_media_bridge

---

## 六、恢复入口

继续时对助手说：**「继续媒体下载项目，看 /home/debug/media-webui/PROJECT_STATUS.md」** 即可恢复上下文。
