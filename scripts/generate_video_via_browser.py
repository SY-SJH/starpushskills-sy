#!/usr/bin/env python3
"""在独立 Playwright 后备浏览器中生成小云雀视频，并把视频挂回当前推广草稿。"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit

from account_utils import (
    canonical_platform,
    load_account,
    login_hint,
    requires_manual_login,
    session_path,
)


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def load_product_profile(root: Path) -> dict[str, Any]:
    """读取视频提示词使用的默认产品资料；文件缺失时保留可用的短兜底。"""

    path = root / "references" / "product-profile.json"
    if not path.exists():
        return {
            "name": "StarPush / STAR DREAM",
            "website": "https://starpush.show/",
            "one_liner": "私人梦境记录、整理与中性解读平台。",
        }
    payload = read_json(path)
    if not isinstance(payload, dict):
        raise SystemExit(f"product profile must be an object: {path}")
    return payload


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.strip().lower())
    return re.sub(r"-{2,}", "-", slug).strip("-") or "draft"


def login_page_detected(page: Any, login_url: str, selectors: dict[str, Any]) -> bool:
    """生成页被重定向到登录页时，立即停止，避免产生假成功草稿。"""

    login_indicator = selectors.get("login_indicator")
    if login_indicator and page.locator(login_indicator).count() > 0:
        return True
    login_path = urlsplit(login_url).path.rstrip("/")
    current_path = urlsplit(page.url).path.rstrip("/")
    return bool(login_path and current_path == login_path)


def update_manifest(bundle_dir: Path, video_name: str) -> None:
    manifest_path = bundle_dir / "manifest.json"
    if not manifest_path.exists():
        return
    manifest = read_json(manifest_path)
    for item in manifest.get("items", []):
        if canonical_platform(str(item.get("platform", ""))) == "douyin":
            item["media_path"] = video_name
            item["media_type"] = "video"
            break
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--topic", required=True)
    parser.add_argument("--direction", default="")
    parser.add_argument("--product", default="", help="覆盖默认产品的一句话描述")
    parser.add_argument("--name", required=True)
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--bundle-dir", help="把视频直接保存到已有推广草稿目录")
    parser.add_argument("--headful", action="store_true", help="打开可见浏览器")
    parser.add_argument("--timeout-seconds", type=int, default=1800, help="等待视频生成的最长时间")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    product_profile = load_product_profile(root)
    product = args.product.strip() or str(product_profile.get("one_liner", "私人梦境记录、整理与中性解读平台。"))
    drafts_root = root / "drafts"
    drafts_root.mkdir(parents=True, exist_ok=True)
    bundle_dir = Path(args.bundle_dir) if args.bundle_dir else None
    if bundle_dir is None:
        stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        bundle_dir = drafts_root / f"{stamp}-xiaoyunque-{slugify(args.topic)}"
        bundle_dir.mkdir(parents=True, exist_ok=False)
    else:
        bundle_dir.mkdir(parents=True, exist_ok=True)

    account = load_account(root, args.account_file, args.name, "xiaoyunque")
    login_url = account.get("login_url")
    generate_url = account.get("generate_url")
    storage = session_path(root, account)
    selectors = account.get("selectors", {})
    if not login_url or not generate_url:
        raise SystemExit("xiaoyunque requires login_url and generate_url")
    if requires_manual_login(account) and (storage is None or not storage.exists()):
        raise SystemExit(
            "本地 Playwright 后备模式没有找到小云雀登录态。这不代表当前 Chrome 或模型浏览器未登录；"
            "该脚本不能接管已有浏览器。请按 references/browser-session.md 使用已登录浏览器，"
            "或先执行一次人工登录命令：\n"
            + login_hint(root, args.account_file, args.name, "xiaoyunque")
        )

    direction = args.direction or "自主创作"
    prompt = (
        f"请为产品创作一条适合抖音的短视频。产品：{product}。"
        f"主题：{args.topic}。方向：{direction}。"
        "只使用已确认的产品能力，避免医疗、心理诊断和确定性预言表述。"
    )
    (bundle_dir / "request.json").write_text(
        json.dumps(
            {
                "product": product,
                "topic": args.topic,
                "direction": args.direction,
                "prompt": prompt,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        raise SystemExit("playwright is required for Xiaoyunque video generation") from exc

    video_name: str | None = None
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        context = browser.new_context(storage_state=str(storage))
        page = context.new_page()
        try:
            page.goto(generate_url, wait_until="domcontentloaded")
            page.wait_for_timeout(2000)
            if login_page_detected(page, login_url, selectors):
                raise SystemExit(
                    "小云雀登录态已失效，请重新执行人工登录命令：\n"
                    + login_hint(root, args.account_file, args.name, "xiaoyunque")
                )

            prompt_sel = selectors.get("prompt")
            generate_sel = selectors.get("generate_button")
            download_sel = selectors.get("download_button")
            if not prompt_sel or not generate_sel or not download_sel:
                raise SystemExit(
                    "xiaoyunque selectors must define prompt, generate_button and download_button"
                )

            page.fill(prompt_sel, prompt)
            style_sel = selectors.get("style")
            if style_sel:
                page.fill(style_sel, args.direction)
            page.screenshot(path=str(bundle_dir / "before-generate.png"), full_page=True)

            page.click(generate_sel)
            ready_sel = selectors.get("generation_ready") or download_sel
            try:
                page.wait_for_selector(ready_sel, state="visible", timeout=args.timeout_seconds * 1000)
            except PlaywrightTimeoutError as exc:
                page.screenshot(path=str(bundle_dir / "generation-timeout.png"), full_page=True)
                raise SystemExit("小云雀视频生成超时，请查看草稿目录中的 generation-timeout.png") from exc

            with page.expect_download(timeout=60000) as download_info:
                page.click(download_sel)
            download = download_info.value
            suggested = Path(download.suggested_filename or "video.mp4").name
            video_name = suggested if suggested else "video.mp4"
            download.save_as(str(bundle_dir / video_name))
            page.screenshot(path=str(bundle_dir / "after-generate.png"), full_page=True)
            update_manifest(bundle_dir, video_name)
            (bundle_dir / "video-result.json").write_text(
                json.dumps(
                    {
                        "topic": args.topic,
                        "product": product,
                        "direction": args.direction,
                        "status": "generated",
                        "platform": "xiaoyunque",
                        "media_path": video_name,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            context.storage_state(path=str(storage))
        finally:
            context.close()
            browser.close()

    print(str(bundle_dir))


if __name__ == "__main__":
    main()
