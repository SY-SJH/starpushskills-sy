#!/usr/bin/env python3
"""通过小云雀营销视频 API 生成视频并保存到 StarPush 草稿目录。"""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import unquote, urlsplit
from urllib.request import Request, urlopen

from xiaoyunque_api import (
    DEFAULT_BASE_URL,
    XiaoyunqueApiError,
    ensure_success,
    load_access_key,
    request_json,
    upload_file,
)
from ui_reference import select_ui_references
from video_prompt import build_video_prompt


def load_product_profile(root: Path) -> dict[str, Any]:
    """读取默认产品资料，保证 API 提示词和文字推广口径一致。"""

    path = root / "references" / "product-profile.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise XiaoyunqueApiError(f"产品资料格式错误：{path}")
    return payload


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return re.sub(r"-{2,}", "-", slug).strip("-") or "draft"


def update_manifest(bundle_dir: Path, video_name: str) -> None:
    """把生成媒体挂回抖音草稿，供后续发布流程直接读取。"""

    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    for item in manifest.get("items", []):
        if str(item.get("platform", "")).lower() in {"douyin", "抖音"}:
            item["media_path"] = video_name
            item["media_type"] = "video"
            break
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )


def create_bundle(root: Path, topic: str, bundle_dir: str | None) -> Path:
    """复用已有草稿目录，否则创建一个新的视频草稿目录。"""

    if bundle_dir:
        target = Path(bundle_dir)
        target.mkdir(parents=True, exist_ok=True)
        return target
    drafts_root = root / "drafts"
    drafts_root.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    target = drafts_root / f"{stamp}-xiaoyunque-{slugify(topic)}"
    target.mkdir(parents=True, exist_ok=False)
    return target


def download_video(url: str, destination: Path, timeout_seconds: int = 120) -> None:
    """下载 API 返回的成品链接，不记录 URL 或认证信息。"""

    request = Request(url, headers={"Accept": "video/*"})
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            with destination.open("wb") as output:
                while chunk := response.read(1024 * 1024):
                    output.write(chunk)
    except (urllib.error.HTTPError, urllib.error.URLError) as exc:
        raise XiaoyunqueApiError("视频下载失败，请稍后从小云雀任务结果重试。") from exc


def video_filename(url: str) -> str:
    candidate = Path(unquote(urlsplit(url).path)).name
    if not re.fullmatch(r"[A-Za-z0-9._-]+", candidate or ""):
        return "xiaoyunque-video.mp4"
    return candidate if Path(candidate).suffix else f"{candidate}.mp4"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--direction", default="")
    parser.add_argument("--product", default="")
    parser.add_argument(
        "--content-mode",
        choices=("auto", "product-demo", "dream-story", "virtual-character"),
        default="auto",
        help="视频内容：自动判断、平台演示、梦境故事或虚拟人物",
    )
    parser.add_argument("--virtual-character", default="", help="可选的虚拟人物设定")
    parser.add_argument(
        "--ui-reference",
        action="append",
        default=[],
        help="显式指定真实界面素材 ID，可重复使用；未指定时平台演示模式会自动选择",
    )
    parser.add_argument("--bundle-dir")
    parser.add_argument("--base-url", default=DEFAULT_BASE_URL)
    parser.add_argument("--ratio", type=int, default=3, help="画幅：3=9:16")
    parser.add_argument("--duration-start", type=int, default=15)
    parser.add_argument("--duration-end", type=int, default=20)
    parser.add_argument("--video-resolution", default="720p")
    parser.add_argument("--video-model", default="")
    parser.add_argument("--show-subtitle", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--poll-interval-seconds", type=int, default=10)
    parser.add_argument("--timeout-seconds", type=int, default=1800)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    access_key = load_access_key(root)
    product_profile = load_product_profile(root)
    product = args.product.strip() or str(
        product_profile.get("one_liner") or "私人梦境记录、整理与中性解读平台。"
    )
    direction = args.direction.strip() or "自主创作"
    bundle_dir = create_bundle(root, args.topic, args.bundle_dir)
    try:
        ui_references = select_ui_references(
            root,
            mode=args.content_mode,
            topic=args.topic,
            direction=direction,
            requested_ids=args.ui_reference,
        )
    except ValueError as exc:
        raise XiaoyunqueApiError(str(exc)) from exc

    asset_ids: list[str] = []
    for reference in ui_references:
        uploaded = upload_file(reference["path"], access_key, base_url=args.base_url)
        uploaded_data = ensure_success(uploaded, f"界面素材上传（{reference['label']}）")
        asset_id = str(uploaded_data.get("pippit_asset_id") or "")
        if not asset_id:
            raise XiaoyunqueApiError(
                f"小云雀界面素材上传响应缺少 pippit_asset_id：{reference['label']}"
            )
        asset_ids.append(asset_id)

    prompt = build_video_prompt(
        topic=args.topic,
        direction=direction,
        product=product,
        website=str(product_profile.get("website") or "https://starpush.show/"),
        mode=args.content_mode,
        virtual_character=args.virtual_character,
        ui_references=[str(item["label"]) for item in ui_references],
    )
    settings: dict[str, Any] = {
        "ratio": args.ratio,
        "duration_start": args.duration_start,
        "duration_end": args.duration_end,
        "show_subtitle": args.show_subtitle,
        "video_resolution": args.video_resolution,
    }
    if args.video_model.strip():
        settings["video_model"] = args.video_model.strip()
    request_payload: dict[str, Any] = {
        "message": prompt,
        "general_agent_settings": settings,
    }
    if asset_ids:
        request_payload["asset_ids"] = asset_ids
    request_record = {
        **request_payload,
        "reference_files": [str(item["path"].relative_to(root)) for item in ui_references],
    }
    (bundle_dir / "request.json").write_text(
        json.dumps(request_record, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    submitted = request_json(
        "/api/biz/v1/agent/submit_marketing_run",
        access_key,
        request_payload,
        base_url=args.base_url,
    )
    submitted_data = ensure_success(submitted, "视频任务提交")
    run_info = submitted_data.get("run") or {}
    if not isinstance(run_info, dict):
        raise XiaoyunqueApiError("小云雀视频任务提交响应缺少 run 信息。")
    run_id = str(run_info.get("run_id") or "")
    thread_id = str(run_info.get("thread_id") or "")
    if not run_id or not thread_id:
        raise XiaoyunqueApiError("小云雀视频任务提交响应缺少 run_id 或 thread_id。")

    deadline = time.monotonic() + args.timeout_seconds
    while time.monotonic() < deadline:
        result = request_json(
            "/api/biz/v1/agent/query_generate_video_result",
            access_key,
            {"thread_id": thread_id, "run_id": run_id},
            base_url=args.base_url,
        )
        data = ensure_success(result, "视频任务查询")
        state = str(data.get("run_state") or "")
        video_urls = data.get("video_urls") or []
        if state == "3" and isinstance(video_urls, list) and video_urls:
            video_url = next((item for item in video_urls if isinstance(item, str) and item), "")
            if not video_url:
                raise XiaoyunqueApiError("小云雀任务成功，但没有返回可下载的视频链接。")
            video_name = video_filename(video_url)
            destination = bundle_dir / video_name
            download_video(video_url, destination)
            update_manifest(bundle_dir, video_name)
            (bundle_dir / "video-result.json").write_text(
                json.dumps(
                    {
                        "status": "generated",
                        "platform": "xiaoyunque-api",
                        "content_mode": args.content_mode,
                        "virtual_character": args.virtual_character,
                        "ui_references": [str(item["label"]) for item in ui_references],
                        "run_id": run_id,
                        "thread_id": thread_id,
                        "media_path": video_name,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            print(str(bundle_dir))
            return
        if state in {"4", "5"}:
            reason = data.get("fail_reason") or "任务失败或已取消"
            raise XiaoyunqueApiError(f"小云雀视频任务未完成：{reason}")
        time.sleep(max(1, args.poll_interval_seconds))

    raise XiaoyunqueApiError("小云雀视频生成超时，请稍后在小云雀任务记录中查看。")


if __name__ == "__main__":
    try:
        main()
    except XiaoyunqueApiError as exc:
        raise SystemExit(str(exc)) from exc
