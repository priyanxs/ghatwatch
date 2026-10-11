"""Post the weekly captions to social channels. Off by default; nothing is sent unless it is configured.

Channels are enabled purely by environment variables (never put keys in code):
    TELEGRAM_BOT_TOKEN + TELEGRAM_CHAT_ID        a Telegram channel or group
    MASTODON_BASE_URL + MASTODON_ACCESS_TOKEN    a Mastodon account
    SOCIAL_WEBHOOK_URL                           any https webhook (Zapier / Make / IFTTT reach X, Facebook,
                                                 LinkedIn, Instagram ...); receives {"text", "text_en", "text_hi"}
    POST_ENABLED=true                            master switch; without it every run is a dry run
Demo data is never posted, whatever the settings.
"""
from __future__ import annotations

import json
import os
import urllib.parse
import urllib.request


def _env(name: str) -> str:
    return os.environ.get(name, "").strip()


def configured_channels() -> list[str]:
    """Names of channels whose settings are complete (never their secrets)."""
    out = []
    if _env("TELEGRAM_BOT_TOKEN") and _env("TELEGRAM_CHAT_ID"):
        out.append("telegram")
    if _env("MASTODON_BASE_URL").startswith("https://") and _env("MASTODON_ACCESS_TOKEN"):
        out.append("mastodon")
    if _env("SOCIAL_WEBHOOK_URL").startswith("https://"):
        out.append("webhook")
    return out


def enabled() -> bool:
    return _env("POST_ENABLED").lower() == "true"


def _send(req: urllib.request.Request) -> tuple[bool, str]:
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            return 200 <= resp.status < 300, f"HTTP {resp.status}"
    except Exception as exc:  # report the failure; never include the request (it holds the secret)
        return False, type(exc).__name__


def _json_post(url: str, payload: dict, headers: dict | None = None) -> urllib.request.Request:
    return urllib.request.Request(url, json.dumps(payload).encode(), {"Content-Type": "application/json", **(headers or {})})


def publish(report: dict) -> list[dict]:
    """Send both captions to every configured channel. Returns one result per channel and language."""
    results = []
    for channel in configured_channels():
        for lang in ("en", "hi"):
            text = report[f"caption_{lang}"]
            if channel == "telegram":
                url = f"https://api.telegram.org/bot{_env('TELEGRAM_BOT_TOKEN')}/sendMessage"
                req = _json_post(url, {"chat_id": _env("TELEGRAM_CHAT_ID"), "text": text, "disable_web_page_preview": True})
            elif channel == "mastodon":
                req = urllib.request.Request(
                    _env("MASTODON_BASE_URL").rstrip("/") + "/api/v1/statuses", urllib.parse.urlencode({"status": text}).encode(),
                    {"Authorization": f"Bearer {_env('MASTODON_ACCESS_TOKEN')}", "Idempotency-Key": f"ghatwatch-{report['date']}-{lang}"})
            else:
                req = _json_post(_env("SOCIAL_WEBHOOK_URL"), {"text": text, "text_en": report["caption_en"], "text_hi": report["caption_hi"], "lang": lang})
            ok, detail = _send(req)
            results.append({"channel": channel, "lang": lang, "ok": ok, "detail": detail})
            if channel == "webhook":
                break  # one call carries both languages
    return results
