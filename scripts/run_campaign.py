#!/usr/bin/env python3
"""
Run the end-to-end promo workflow.

This is the single entrypoint for:
1. generating per-platform drafts;
2. generating Xiaoyunque video when Douyin is included;
3. building publish plans;
4. optionally triggering browser publishing.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

from account_utils import canonical_platform


PLATFORM_LABELS = {
    "zhihu": "知乎",
    "xiaohongshu": "小红书",
    "douyin": "抖音",
    "tieba": "百度贴吧",
    "weibo": "微博",
    "xiaoyuzhou": "小宇宙",
}


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", help="发布或生成视频时使用的同事账号名；只生成文字草稿时可省略")
    parser.add_argument("--topic", required=True)
    parser.add_argument("--direction", default="", help="可选创作方向；留空时按主题自主创作")
    parser.add_argument("--platforms", required=True, help="Comma-separated platform list")
    parser.add_argument("--auto-publish", action="store_true")
    parser.add_argument("--publish-at", help="按本地时间或 ISO 8601 时间排队，例如 2026-08-10T18:00:00+08:00")
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--headful", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    platforms = []
    for item in args.platforms.split(","):
        platform = canonical_platform(item)
        if platform and platform not in platforms:
            platforms.append(platform)
    if not platforms:
        raise SystemExit("platforms cannot be empty")
    if ("douyin" in platforms or args.auto_publish or args.publish_at) and not args.name:
        raise SystemExit("抖音视频或自动发布需要 --name，以便读取对应同事的账号")
    if args.auto_publish and args.publish_at:
        raise SystemExit("--auto-publish 和 --publish-at 不能同时使用")
    if args.publish_at:
        try:
            datetime.fromisoformat(args.publish_at)
        except ValueError as exc:
            raise SystemExit("--publish-at 必须是 ISO 8601 时间，例如 2026-08-10T18:00:00+08:00") from exc

    payload = {
        "topic": args.topic,
        "direction": args.direction,
        "auto_publish": bool(args.auto_publish),
        "items": [],
    }

    for platform in platforms:
        label = PLATFORM_LABELS.get(platform, platform)
        direction = args.direction or "自主创作"
        if platform == "douyin":
            payload["items"].append(
                {
                    "platform": "douyin",
                    "title": f"{args.topic}｜短视频",
                    "body": f"围绕 {direction} 的视频文案",
                    "tags": ["#抖音", "#视频"],
                    "script": f"{args.topic}。{direction}",
                }
            )
        else:
            payload["items"].append(
                {
                    "platform": platform,
                    "title": f"{args.topic}｜{label}",
                    "body": f"围绕 {direction} 的{label}平台文案",
                    "tags": [f"#{label}", "#推广"],
                }
            )

    bundle_dir = subprocess.check_output(
        [
            sys.executable,
            str(root / "scripts" / "create_draft_bundle.py"),
        ],
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
    ).strip()

    if "douyin" in platforms:
        run(
            [
                sys.executable,
                str(root / "scripts" / "generate_video_via_browser.py"),
                "--topic",
                args.topic,
                "--direction",
                args.direction,
                "--name",
                args.name,
                "--account-file",
                args.account_file,
                "--bundle-dir",
                bundle_dir,
            ]
            + (["--headful"] if args.headful else [])
        )

    if args.name:
        for platform in platforms:
            run(
                [
                    sys.executable,
                    str(root / "scripts" / "build_publish_plan.py"),
                    "--bundle-dir",
                    bundle_dir,
                    "--platform",
                    platform,
                    "--name",
                    args.name,
                    "--account-file",
                    args.account_file,
                ]
            )

    if args.publish_at:
        schedule = {
            "created_at": datetime.now().astimezone().isoformat(timespec="seconds"),
            "publish_at": args.publish_at,
            "platforms": platforms,
            "name": args.name,
            "account_file": args.account_file,
            "headful": bool(args.headful),
            "status": "scheduled",
        }
        Path(bundle_dir, "schedule.json").write_text(
            json.dumps(schedule, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    if args.auto_publish:
        for platform in platforms:
            run(
                [
                    sys.executable,
                    str(root / "scripts" / "publish_via_browser.py"),
                    "--bundle-dir",
                    bundle_dir,
                    "--platform",
                    platform,
                    "--name",
                    args.name,
                    "--account-file",
                    args.account_file,
                ]
                + (["--headful"] if args.headful else [])
            )

    print(bundle_dir)


if __name__ == "__main__":
    main()
