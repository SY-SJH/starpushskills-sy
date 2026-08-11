#!/usr/bin/env python3
"""小云雀 API 的本地配置和 HTTP 通用处理。

Access Key 只从环境变量或 Git 忽略的本地文件读取，避免进入草稿、日志和提交记录。
"""

from __future__ import annotations

import json
import mimetypes
import os
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any


DEFAULT_BASE_URL = "https://xyq.jianying.com"
ACCESS_KEY_ENV = "XIAOYUNQUE_ACCESS_KEY"
ACCESS_KEY_FILE = "local/xiaoyunque-access-key.txt"


class XiaoyunqueApiError(RuntimeError):
    """小云雀 API 返回错误或响应格式不符合预期。"""


def load_access_key(root: Path, required: bool = True) -> str | None:
    """读取本机 Key；required=False 用于判断是否切换 API 模式。"""

    for env_name in (ACCESS_KEY_ENV, "XIAOYUNQUE_API_KEY"):
        value = os.environ.get(env_name, "").strip()
        if value:
            return value

    path = root / ACCESS_KEY_FILE
    if path.exists():
        value = path.read_text(encoding="utf-8").strip()
        if value:
            return value

    if required:
        raise XiaoyunqueApiError(
            "未找到小云雀 Access Key。请在 skill 目录的 "
            f"{ACCESS_KEY_FILE} 保存完整 Key，或设置环境变量 {ACCESS_KEY_ENV}。"
        )
    return None


def api_url(path: str, base_url: str = DEFAULT_BASE_URL) -> str:
    """拼接官方 API 地址，允许测试环境通过参数覆盖域名。"""

    return f"{base_url.rstrip('/')}/{path.lstrip('/')}"


def request_json(
    path: str,
    access_key: str,
    payload: dict[str, Any],
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = 60,
) -> dict[str, Any]:
    """发送 JSON 请求并隐藏认证信息，不把 Key 放进异常文本。"""

    body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(
        api_url(path, base_url),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise XiaoyunqueApiError(
            f"小云雀 API 请求失败（HTTP {exc.code}），请检查 Access Key 和账号额度。"
        ) from exc
    except urllib.error.URLError as exc:
        raise XiaoyunqueApiError(f"小云雀 API 网络请求失败：{exc.reason}") from exc

    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise XiaoyunqueApiError("小云雀 API 返回了无法解析的响应。") from exc
    if not isinstance(result, dict):
        raise XiaoyunqueApiError("小云雀 API 返回格式错误。")
    return result


def upload_file(
    path: Path,
    access_key: str,
    *,
    base_url: str = DEFAULT_BASE_URL,
    timeout_seconds: int = 120,
) -> dict[str, Any]:
    """按官方 multipart/form-data 接口上传单个素材文件。"""

    if not path.is_file():
        raise XiaoyunqueApiError(f"待上传素材不存在：{path}")
    try:
        file_data = path.read_bytes()
    except OSError as exc:
        raise XiaoyunqueApiError(f"无法读取待上传素材：{path.name}") from exc

    boundary = f"----starpush-{uuid.uuid4().hex}"
    file_name = path.name.replace('"', "_")
    content_type = mimetypes.guess_type(file_name)[0] or "application/octet-stream"
    prefix = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="{file_name}"\r\n'
        f"Content-Type: {content_type}\r\n\r\n"
    ).encode("utf-8")
    body = prefix + file_data + f"\r\n--{boundary}--\r\n".encode("ascii")
    request = urllib.request.Request(
        api_url("/api/biz/v1/skill/upload_file", base_url),
        data=body,
        method="POST",
        headers={
            "Authorization": f"Bearer {access_key}",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
            raw = response.read()
    except urllib.error.HTTPError as exc:
        raise XiaoyunqueApiError(
            f"小云雀素材上传失败（HTTP {exc.code}），请检查 Access Key、文件格式和账号额度。"
        ) from exc
    except urllib.error.URLError as exc:
        raise XiaoyunqueApiError(f"小云雀素材上传网络请求失败：{exc.reason}") from exc

    try:
        result = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise XiaoyunqueApiError("小云雀素材上传返回了无法解析的响应。") from exc
    if not isinstance(result, dict):
        raise XiaoyunqueApiError("小云雀素材上传返回格式错误。")
    return result


def ensure_success(result: dict[str, Any], operation: str) -> dict[str, Any]:
    """统一检查小云雀 ret，并返回 data 对象。"""

    if str(result.get("ret", "")) != "0":
        message = str(result.get("errmsg") or "未知错误")
        log_id = str(result.get("log_id") or "")
        suffix = f"（日志 ID: {log_id}）" if log_id else ""
        raise XiaoyunqueApiError(f"小云雀{operation}失败：{message}{suffix}")
    data = result.get("data") or {}
    if not isinstance(data, dict):
        raise XiaoyunqueApiError(f"小云雀{operation}返回格式错误。")
    return data
