#!/usr/bin/env python3
"""
媒体下载 WebUI - 解析 Twitter/Bluesky/YouTube 链接并下载媒体
复用 astrbot_plugin_media_bridge 的解析逻辑
"""
import os
import re
import uuid
import asyncio
import urllib.parse

import aiohttp
import time
import ipaddress
import socket
import hmac
from urllib.parse import urlparse
from flask import Flask, request, jsonify, send_file, render_template, session, redirect
from functools import wraps

app = Flask(__name__)

# ============ 安全加固 ============
ALLOW_PRIVATE = os.environ.get("MEDIA_ALLOW_PRIVATE", "0") == "1"
MAX_FAILS = 5
FAIL_WINDOW = 300
_fails = {}


def _is_safe_url(u):
    """SSRF 防护：只允许 http/https 且非内网/保留地址"""
    try:
        p = urlparse(u)
    except Exception:
        return False
    if p.scheme not in ("http", "https"):
        return False
    host = p.hostname
    if not host:
        return False
    if ALLOW_PRIVATE:
        return True
    try:
        infos = socket.getaddrinfo(host, None)
    except Exception:
        return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0])
        except Exception:
            continue
        if ip.is_private or ip.is_loopback or ip.is_link_local or ip.is_reserved or ip.is_multicast or ip.is_unspecified:
            return False
    return True


def _rate_ok(ip):
    now = time.time()
    arr = [t for t in _fails.get(ip, []) if now - t < FAIL_WINDOW]
    _fails[ip] = arr
    return len(arr) < MAX_FAILS


def _rate_fail(ip):
    _fails.setdefault(ip, []).append(time.time())



PROXY = os.environ.get("MEDIA_PROXY", "http://127.0.0.1:7890")
import shutil as _shutil
YTDLP = _shutil.which("yt-dlp") or "/home/debug/qqbot/qqbot/new-zaiens/astrbot/.venv/bin/yt-dlp"
DL_DIR = os.environ.get("MEDIA_DL_DIR", os.path.join(os.path.dirname(os.path.abspath(__file__)), "downloads"))
os.makedirs(DL_DIR, exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}
MAX_MB = int(os.environ.get("MEDIA_MAX_MB", "200"))


async def _download(session, url, type_hint=""):
    """下载到本地，返回文件名"""
    try:
        async with session.get(url, proxy=PROXY, headers=HEADERS) as resp:
            if resp.status != 200:
                return None
            data = await resp.read()
            if len(data) > MAX_MB * 1024 * 1024:
                return None
            ext = ""
            if type_hint.lower() in ("video", "gif"):
                ext = ".mp4"
            elif type_hint.lower() in ("photo", "image"):
                ext = ".jpg"
            if not ext:
                ct = resp.headers.get("Content-Type", "")
                if "mp4" in ct or "video" in ct:
                    ext = ".mp4"
                elif "gif" in ct:
                    ext = ".gif"
                elif "png" in ct:
                    ext = ".png"
                elif "webp" in ct:
                    ext = ".webp"
                elif "jpeg" in ct or "jpg" in ct:
                    ext = ".jpg"
                else:
                    ext = os.path.splitext(url.split("?")[0])[1] or ".bin"
            fname = f"{uuid.uuid4().hex}{ext}"
            with open(os.path.join(DL_DIR, fname), "wb") as f:
                f.write(data)
            return {"file": fname, "size": len(data), "type": "video" if ext in (".mp4", ".mov", ".webm", ".mkv") else "image"}
    except Exception as e:
        print(f"[download] {e}")
        return None


async def parse_twitter(session, url):
    m = re.search(r"(?:twitter\.com|x\.com)/([^/]+)/status/(\d+)", url)
    if not m:
        return []
    user, sid = m.group(1), m.group(2)
    async with session.get(f"https://api.fxtwitter.com/{user}/status/{sid}", proxy=PROXY, headers=HEADERS) as r:
        if r.status != 200:
            return []
        d = await r.json()
    t = d.get("tweet", {})
    medias = list(t.get("media", {}).get("all", []))
    q = t.get("quote")
    if isinstance(q, dict):
        medias += list((q.get("media", {}) or {}).get("all", []))
    results = []
    for mm in medias:
        mu = mm.get("url") or mm.get("media_url_https") or mm.get("thumbnail_url") or ""
        if not mu:
            continue
        for a, b in (("name=small", "name=large"), ("name=medium", "name=large"), ("name=orig", "name=large")):
            mu = mu.replace(a, b)
        info = await _download(session, mu, mm.get("type", ""))
        if info:
            info["source"] = mu
            results.append(info)
    return results


async def parse_bluesky(session, url):
    m = re.search(r"/profile/([^/]+)/post/(\w+)", url)
    if not m:
        return []
    handle, rkey = m.group(1), m.group(2)
    if handle.startswith("did:"):
        did = handle
    else:
        async with session.get(f"https://public.api.bsky.app/xrpc/com.atproto.identity.resolveHandle?handle={handle}",
                               proxy=PROXY, headers=HEADERS) as r:
            if r.status != 200:
                return []
            did = (await r.json()).get("did", "")
    if not did:
        return []
    uri = f"at://{did}/app.bsky.feed.post/{rkey}"
    async with session.get(f"https://public.api.bsky.app/xrpc/app.bsky.feed.getPosts?uris={urllib.parse.quote(uri)}",
                           proxy=PROXY, headers=HEADERS) as r:
        if r.status != 200:
            return []
        posts = (await r.json()).get("posts", [])
    if not posts:
        return []
    rec = posts[0].get("record", {})
    embed = rec.get("embed", {}) or {}
    et = embed.get("$type", "")
    media = []

    def _add_images(emb):
        for img in emb.get("images", []):
            blob = img.get("image", {})
            cid = blob.get("ref", {}).get("$link", "")
            ex = blob.get("mimeType", "image/jpeg").split("/")[-1]
            if cid:
                media.append((f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@{ex}", "image"))

    def _add_video(emb):
        blob = emb.get("video", {})
        cid = blob.get("ref", {}).get("$link", "")
        if cid:
            media.append((f"https://video.bsky.app/watch/{did}/{cid}/playlist.m3u8", "video"))

    if et == "app.bsky.embed.images":
        _add_images(embed)
    elif et == "app.bsky.embed.video":
        _add_video(embed)
    elif et == "app.bsky.embed.recordWithMedia":
        m2 = embed.get("media", {}) or {}
        if m2.get("$type") == "app.bsky.embed.images":
            _add_images(m2)
        elif m2.get("$type") == "app.bsky.embed.video":
            _add_video(m2)
    elif et == "app.bsky.embed.external":
        ext = embed.get("external", {}) or {}
        thumb = ext.get("thumb", {})
        cid = thumb.get("ref", {}).get("$link", "")
        if cid:
            media.append((f"https://cdn.bsky.app/img/feed_fullsize/plain/{did}/{cid}@jpeg", "image"))
    results = []
    for mu, th in media:
        if th == "video" and mu.endswith(".m3u8"):
            info = await _ytdlp_media(mu)
        else:
            info = await _download(session, mu, th)
        if info:
            info["source"] = mu
            results.append(info)
    return results


async def _ytdlp_media(url):
    """用 yt-dlp 下载 m3u8（Bluesky 视频）"""
    out_tmpl = os.path.join(DL_DIR, f"dl_{uuid.uuid4().hex}.%(ext)s")
    cmd = [YTDLP, "--proxy", PROXY, "--referer", "https://bsky.app/",
           "--add-header", "Origin:https://bsky.app",
           "-o", out_tmpl, "--no-playlist", url]
    try:
        proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
        await asyncio.wait_for(proc.communicate(), timeout=300)
    except Exception as e:
        print("[ytdlp_media]", e)
        return None
    for f in os.listdir(DL_DIR):
        if f.startswith("dl_"):
            p = os.path.join(DL_DIR, f)
            if os.path.getsize(p) > 0:
                return {"file": f, "size": os.path.getsize(p), "type": "video"}
    return None


async def parse_youtube(session, url):
    # 用 yt-dlp 下载
    out_tmpl = os.path.join(DL_DIR, f"yt_{uuid.uuid4().hex}.%(ext)s")
    cmd = [YTDLP, "-f", "bv*+ba/b", "--merge-output-format", "mp4", "-o", out_tmpl,
           "--no-playlist", "--max-filesize", f"{MAX_MB}M", "--proxy", PROXY, url]
    proc = await asyncio.create_subprocess_exec(*cmd, stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.PIPE)
    await asyncio.wait_for(proc.communicate(), timeout=600)
    for f in os.listdir(DL_DIR):
        if f.startswith("yt_"):
            p = os.path.join(DL_DIR, f)
            return [{"file": f, "size": os.path.getsize(p), "type": "video", "source": url}]
    return []


async def parse_all(url):
    async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=600)) as s:
        if re.search(r"(?:twitter\.com|x\.com)/", url):
            return await parse_twitter(s, url)
        if re.search(r"(?:bsky\.app|bsky\.social)/", url):
            return await parse_bluesky(s, url)
        if re.search(r"(?:youtube\.com|youtu\.be)/", url):
            return await parse_youtube(s, url)
        # 通用图片/GIF（按扩展名）
        if re.search(r"\.(?:gif|jpe?g|png|webp|bmp|avif)(?:\?|$)", url, re.I):
            info = await _download(s, url)
            if info:
                info["source"] = url
                return [info]
        # 兜底：按 Content-Type 判断可直接下载的媒体
        try:
            async with s.head(url, proxy=PROXY, headers=HEADERS, allow_redirects=True) as r:
                ct = r.headers.get("Content-Type", "")
            if ct.startswith("image/") or ct.startswith("video/"):
                info = await _download(s, url)
                if info:
                    info["source"] = url
                    return [info]
        except Exception:
            pass
        return []


_SECRET_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".secret")
if os.environ.get("MEDIA_SECRET"):
    app.secret_key = os.environ["MEDIA_SECRET"]
else:
    try:
        app.secret_key = open(_SECRET_FILE).read().strip()
    except Exception:
        _s = os.urandom(32).hex()
        try:
            open(_SECRET_FILE, "w").write(_s)
        except Exception:
            pass
        app.secret_key = _s
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("MEDIA_COOKIE_SECURE", "0") == "1",
    PERMANENT_SESSION_LIFETIME=3600 * 24,
    MAX_CONTENT_LENGTH=2 * 1024 * 1024,
)
AUTH_USER = os.environ.get("MEDIA_USER", "debug")
AUTH_PASS = os.environ.get("MEDIA_PASS", "Admin@123")


def login_required(f):
    @wraps(f)
    def _w(*a, **kw):
        if not session.get("logged_in"):
            if request.path.startswith("/api/"):
                return jsonify({"ok": False, "error": "未登录", "need_login": True}), 401
            return redirect("/login")
        return f(*a, **kw)
    return _w


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        ip = request.headers.get("X-Forwarded-For", request.remote_addr or "").split(",")[0].strip()
        if not _rate_ok(ip):
            return render_template("login.html", error="尝试次数过多，请 5 分钟后再试"), 429
        u = request.form.get("username", "")
        p = request.form.get("password", "")
        ok = hmac.compare_digest(u, AUTH_USER) and hmac.compare_digest(p, AUTH_PASS)
        if ok:
            session["logged_in"] = True
            session.permanent = True
            session["_ip"] = ip
            return redirect("/")
        _rate_fail(ip)
        return render_template("login.html", error="用户名或密码错误")
    return render_template("login.html", error="")


@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")


@app.route("/")
@login_required
def index():
    return render_template("index.html")




def _cleanup_old():
    """惰性清理：删除超过 KEEP_HOURS 的下载文件"""
    hours = float(os.environ.get("MEDIA_KEEP_HOURS", "24"))
    now = time.time()
    for f in os.listdir(DL_DIR):
        p = os.path.join(DL_DIR, f)
        try:
            if os.path.isfile(p) and now - os.path.getmtime(p) > hours * 3600:
                os.remove(p)
        except Exception:
            pass


def _fmt(media):
    out = []
    for m in media:
        out.append({
            "file": m["file"],
            "type": m["type"],
            "size": m["size"],
            "view": f"/media/{m['file']}",
            "download": f"/media/{m['file']}?dl=1",
        })
    return out


@app.route("/api/parse", methods=["POST"])
@login_required
def api_parse():
    data = request.get_json(silent=True) or {}
    raw = (data.get("urls") or data.get("url") or "").strip()
    if not raw:
        return jsonify({"ok": False, "error": "请输入链接"})
    _cleanup_old()
    urls = re.findall(r"https?://[^\s,，、]+", raw)
    seen = set(); uniq = []
    for u in urls:
        if u not in seen:
            seen.add(u); uniq.append(u)
    if not uniq:
        return jsonify({"ok": False, "error": "未识别到有效链接"})
    all_media = []
    errors = []
    safe = []
    for u in uniq:
        if _is_safe_url(u):
            safe.append(u)
        else:
            errors.append({"url": u, "error": "已拦截：内网/非法地址"})
    uniq = safe
    for u in uniq:
        try:
            media = asyncio.run(parse_all(u))
        except Exception as e:
            errors.append({"url": u, "error": str(e)[:100]}); continue
        if media:
            all_media.extend(_fmt(media))
        else:
            errors.append({"url": u, "error": "未解析到媒体"})
    if not all_media and errors:
        return jsonify({"ok": False, "error": "全部解析失败", "errors": errors, "total": len(uniq)})
    return jsonify({"ok": True, "count": len(all_media), "media": all_media,
                    "total_urls": len(uniq), "errors": errors})


@app.after_request
def _sec_headers(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Referrer-Policy"] = "no-referrer"
    resp.headers["Content-Security-Policy"] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' data: blob:"
    try:
        del resp.headers["Server"]
    except Exception:
        pass
    return resp


@app.route("/media/<path:filename>")
@login_required
def media(filename):
    safe = os.path.basename(filename)
    path = os.path.join(DL_DIR, safe)
    if not os.path.abspath(path).startswith(os.path.abspath(DL_DIR)):
        return "forbidden", 403
    if not os.path.exists(path):
        return "not found", 404
    as_attachment = request.args.get("dl") == "1"
    return send_file(path, as_attachment=as_attachment)


if __name__ == "__main__":
    app.run(host=os.environ.get("MEDIA_HOST", "0.0.0.0"), port=int(os.environ.get("MEDIA_PORT", "8891")), threaded=True)
