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
from xiaoyunque_api import load_access_key


PLATFORM_LABELS = {
    "zhihu": "知乎",
    "xiaohongshu": "小红书",
    "douyin": "抖音",
    "tieba": "百度贴吧",
    "weibo": "微博",
    "xiaoyuzhou": "小宇宙",
}

DEFAULT_PRODUCT_PROFILE = {
    "name": "StarPush / STAR DREAM",
    "website": "https://starpush.show/",
    "one_liner": "一个把醒来后的模糊片段记录下来、整理成私人梦境手记，并提供中性 AI 解读和平台认证真人解梦服务的梦境平台。",
}


def load_product_profile(root: Path) -> dict[str, object]:
    """读取随 skill 发布的产品资料，避免每次创作都重新询问产品定位。"""

    path = root / "references" / "product-profile.json"
    if not path.exists():
        return dict(DEFAULT_PRODUCT_PROFILE)
    try:
        profile = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"product profile is invalid: {path}") from exc
    if not isinstance(profile, dict):
        raise SystemExit(f"product profile must be an object: {path}")
    return profile


def run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--name",
        help="发布时使用的同事账号名；未配置小云雀 API Key 时也用于网页登录生成视频",
    )
    parser.add_argument("--topic", required=True)
    parser.add_argument("--direction", default="", help="可选创作方向；留空时按主题自主创作")
    parser.add_argument("--product", default="", help="覆盖默认产品的一句话描述；通常不需要填写")
    parser.add_argument(
        "--content-mode",
        choices=("auto", "product-demo", "dream-story", "virtual-character"),
        default="auto",
        help="抖音视频内容：自动判断、平台演示、梦境故事或虚拟人物",
    )
    parser.add_argument("--virtual-character", default="", help="可选的虚拟人物设定")
    parser.add_argument("--platforms", required=True, help="Comma-separated platform list")
    parser.add_argument("--auto-publish", action="store_true")
    parser.add_argument("--publish-at", help="按本地时间或 ISO 8601 时间排队，例如 2026-08-10T18:00:00+08:00")
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--headful", action="store_true")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    api_key = load_access_key(root, required=False)
    product_profile = load_product_profile(root)
    product = args.product.strip() or str(
        product_profile.get("one_liner") or DEFAULT_PRODUCT_PROFILE["one_liner"]
    )
    platforms = []
    for item in args.platforms.split(","):
        platform = canonical_platform(item)
        if platform and platform not in platforms:
            platforms.append(platform)
    if not platforms:
        raise SystemExit("platforms cannot be empty")
    if "douyin" in platforms and not args.name and not api_key:
        raise SystemExit(
            "抖音视频需要小云雀 API Key，或使用 --name 走网页登录流程。"
        )
    if (args.auto_publish or args.publish_at) and not args.name:
        raise SystemExit("发布或定时发布需要 --name，以便识别发布账号")
    if args.auto_publish and args.publish_at:
        raise SystemExit("--auto-publish 和 --publish-at 不能同时使用")
    if args.publish_at:
        try:
            datetime.fromisoformat(args.publish_at)
        except ValueError as exc:
            raise SystemExit("--publish-at 必须是 ISO 8601 时间，例如 2026-08-10T18:00:00+08:00") from exc

    payload = {
        "product": product,
        "product_profile": product_profile,
        "topic": args.topic,
        "direction": args.direction,
        "auto_publish": bool(args.auto_publish),
        "items": [],
    }

    for platform in platforms:
        label = PLATFORM_LABELS.get(platform, platform)
        direction = args.direction or "自主创作"
        generation_prompt = (
            f"产品：{product}\n"
            f"主题：{args.topic}\n"
            f"方向：{direction}\n"
            f"请按{label}平台习惯创作，不虚构产品能力。"
        )
        if platform == "douyin":
            payload["items"].append(
                {
                    "platform": "douyin",
                    "title": f"{args.topic}｜短视频",
                    "body": f"产品：{product}\n围绕 {direction} 的抖音短视频文案",
                    "tags": ["#抖音", "#视频"],
                    "script": generation_prompt,
                    "generation_prompt": generation_prompt,
                }
            )
        else:
            payload["items"].append(
                {
                    "platform": platform,
                    "title": f"{args.topic}｜{label}",
                    "body": f"产品：{product}\n围绕 {direction} 的{label}平台文案",
                    "tags": [f"#{label}", "#推广"],
                    "generation_prompt": generation_prompt,
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
        video_script = (
            "generate_video_via_api.py" if api_key else "generate_video_via_browser.py"
        )
        run(
            [
                sys.executable,
                str(root / "scripts" / video_script),
                "--topic",
                args.topic,
                "--direction",
                args.direction,
                "--product",
                product,
                "--content-mode",
                args.content_mode,
                "--virtual-character",
                args.virtual_character,
                "--bundle-dir",
                bundle_dir,
            ]
            + ([] if api_key else ["--name", args.name, "--account-file", args.account_file])
            + (["--headful"] if args.headful and not api_key else [])
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
