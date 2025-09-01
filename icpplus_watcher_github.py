#!/usr/bin/env python3
import os
import json
import time
import pathlib
import urllib.request
import urllib.error
import sys

# === CONFIG ===
URL = "https://icp.administracionelectronica.gob.es/icpplus/index.html"
TIMEOUT_SEC = 8
STATE_FILE = str(pathlib.Path.home() / ".icpplus_state.json")
# Secrets are read from environment variables set by GitHub Actions:
TELEGRAM_BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
TELEGRAM_CHAT_ID   = os.getenv("CHAT_ID", "").strip()
# =============

def is_up(url: str, timeout: int = 8) -> bool:
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            if resp.status < 400:
                _ = resp.read(256)
                return True
            return False
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError):
        return False

def load_state(path: str) -> dict:
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_state(path: str, data: dict) -> None:
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f)
    except Exception:
        pass

def send_telegram(token: str, chat_id: str, text: str) -> None:
    if not token or not chat_id:
        return
    api_url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = json.dumps({"chat_id": chat_id, "text": text, "disable_web_page_preview": True}).encode("utf-8")
    req = urllib.request.Request(api_url, data=payload, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=8) as resp:
            resp.read(64)
    except Exception:
        pass

def main():
    # Fail fast if secrets are missing
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Missing BOT_TOKEN or CHAT_ID environment variables.", file=sys.stderr)
        sys.exit(1)

    up = is_up(URL, TIMEOUT_SEC)
    state = load_state(STATE_FILE)
    last = state.get("up")

    # Notify only on transition from DOWN -> UP
    if up and (last is False or last is None):
        send_telegram(
            TELEGRAM_BOT_TOKEN,
            TELEGRAM_CHAT_ID,
            "✅ ICP+ is back online: https://icp.administracionelectronica.gob.es/icpplus/index.html"
        )

    state["up"] = bool(up)
    state["ts"] = int(time.time())
    save_state(STATE_FILE, state)

if __name__ == "__main__":
    main()
