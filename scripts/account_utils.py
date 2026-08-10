#!/usr/bin/env python3
"""账号配置、平台别名和本地登录态的公共处理逻辑。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


PLATFORM_ALIASES = {
    "知乎": "zhihu",
    "zhihu": "zhihu",
    "小红书": "xiaohongshu",
    "xiaohongshu": "xiaohongshu",
    "抖音": "douyin",
    "douyin": "douyin",
    "百度贴吧": "tieba",
    "贴吧": "tieba",
    "tieba": "tieba",
    "微博": "weibo",
    "weibo": "weibo",
    "小宇宙": "xiaoyuzhou",
    "xiaoyuzhou": "xiaoyuzhou",
    "小云雀": "xiaoyunque",
    "xiaoyunque": "xiaoyunque",
}

SENSITIVE_KEYS = {
    "password",
    "passcode",
    "secret",
    "token",
    "access_token",
    "refresh_token",
    "cookie",
    "cookies",
    "authorization",
}


def canonical_platform(value: str) -> str:
    """把用户常用的平台中文名转换为配置使用的稳定标识。"""

    normalized = value.strip().lower()
    return PLATFORM_ALIASES.get(normalized, normalized)


def resolve_account_path(root: Path, account_file: str) -> Path:
    """解析本地账号文件；真实运行禁止静默回退到示例账号。"""

    path = Path(account_file)
    if not path.is_absolute():
        path = root / path
    if not path.exists():
        example = root / "accounts.example.json"
        raise SystemExit(
            f"account file not found: {path}. Copy {example.name} to accounts.json and fill local values."
        )
    return path


def _profiles(payload: Any) -> list[dict[str, Any]]:
    """兼容旧的单账号格式以及新的 accounts 数组格式。"""

    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    if not isinstance(payload, dict):
        return []

    accounts = payload.get("accounts")
    if isinstance(accounts, list):
        return [item for item in accounts if isinstance(item, dict)]
    if isinstance(accounts, dict):
        return [dict(value, name=name) for name, value in accounts.items() if isinstance(value, dict)]
    if payload.get("name") and isinstance(payload.get("platforms"), dict):
        return [payload]
    return []


def load_account(root: Path, account_file: str, name: str, platform: str) -> dict[str, Any]:
    """读取指定同事的指定平台账号，返回原始配置供本地浏览器使用。"""

    path = resolve_account_path(root, account_file)
    payload = json.loads(path.read_text(encoding="utf-8"))
    target_platform = canonical_platform(platform)
    for profile in _profiles(payload):
        if profile.get("name") != name:
            continue
        platforms = profile.get("platforms", {})
        if not isinstance(platforms, dict):
            platforms = {}
        record = next(
            (
                value
                for platform_name, value in platforms.items()
                if canonical_platform(str(platform_name)) == target_platform
            ),
            None,
        )
        if not isinstance(record, dict):
            raise SystemExit(f"platform account not found: {target_platform} for {name}")
        return record
    raise SystemExit(f"account name not found: {name}")


def redact(value: Any, key: str | None = None) -> Any:
    """生成可写入草稿清单的脱敏副本，避免密码进入文件或终端输出。"""

    if key and key.lower() in SENSITIVE_KEYS:
        return "[redacted]"
    if isinstance(value, dict):
        # selector 里的 password 是网页定位器，不是账号密码，必须保留以便排查页面结构。
        selector_map = key == "selectors"
        return {
            item_key: redact(item_value, None if selector_map else item_key)
            for item_key, item_value in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


def session_path(root: Path, record: dict[str, Any]) -> Path | None:
    """把配置中的 storage_state 转换为本地路径。"""

    configured = record.get("storage_state")
    if not configured:
        return None
    path = Path(str(configured))
    return path if path.is_absolute() else root / path


def requires_manual_login(record: dict[str, Any]) -> bool:
    """判断是否必须通过可见浏览器人工完成短信或第三方授权。"""

    mode = str(record.get("auth_mode", "")).strip().lower()
    if mode in {"sms", "sms-or-douyin", "douyin-login", "manual", "qr", "qrcode"}:
        return True
    return not record.get("username") or not record.get("password")


def login_hint(root: Path, account_file: str, name: str, platform: str) -> str:
    """生成不包含凭据的人工登录命令提示。"""

    return (
        f"python3 {root / 'scripts' / 'bootstrap_browser_session.py'} "
        f"--platform {canonical_platform(platform)} --name {name} --account-file {account_file}"
    )
