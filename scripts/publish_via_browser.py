#!/usr/bin/env python3
"""通过平台网页完成登录、填充内容、上传媒体和发布。"""

from __future__ import annotations

import argparse
import json
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


def pick_platform_item(bundle: dict[str, Any], platform: str) -> dict[str, Any]:
    target = canonical_platform(platform)
    for item in bundle.get("items", []):
        if canonical_platform(str(item.get("platform", ""))) == target:
            return item
    raise SystemExit(f"no content found for platform: {target}")


def login_page_detected(page: Any, login_url: str, selectors: dict[str, Any]) -> bool:
    login_indicator = selectors.get("login_indicator")
    if login_indicator and page.locator(login_indicator).count() > 0:
        return True
    login_path = urlsplit(login_url).path.rstrip("/")
    current_path = urlsplit(page.url).path.rstrip("/")
    return bool(login_path and current_path == login_path)


def wait_for_network(page: Any, timeout: int = 15000) -> None:
    """平台页面常有长连接，网络不完全 idle 不能作为成功条件。"""

    try:
        page.wait_for_load_state("networkidle", timeout=timeout)
    except Exception:
        page.wait_for_timeout(1000)


def read_bundle(bundle_dir: Path, platform: str) -> dict[str, Any]:
    plan_path = bundle_dir / f"publish-plan-{canonical_platform(platform)}.json"
    if not plan_path.exists():
        legacy_path = bundle_dir / "publish-plan.json"
        plan_path = legacy_path if legacy_path.exists() else plan_path
    if not plan_path.exists():
        raise SystemExit(f"publish plan not found: {plan_path}")
    plan = json.loads(plan_path.read_text(encoding="utf-8"))
    manifest_path = bundle_dir / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8")) if manifest_path.exists() else plan.get("draft", {})
    return {"plan": plan, "manifest": manifest}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--headful", action="store_true", help="打开可见浏览器")
    parser.add_argument("--dry-run", action="store_true", help="只填充并截图，不点击发布")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    bundle_dir = Path(args.bundle_dir)
    platform = canonical_platform(args.platform)
    bundle_data = read_bundle(bundle_dir, platform)
    content = pick_platform_item(bundle_data["manifest"], platform)
    account = load_account(root, args.account_file, args.name, platform)

    login_url = account.get("login_url")
    publish_url = account.get("publish_url")
    selectors = account.get("selectors", {})
    storage = session_path(root, account)
    if not login_url or not publish_url:
        raise SystemExit(f"missing login_url or publish_url for {platform}")
    if requires_manual_login(account) and (storage is None or not storage.exists()):
        raise SystemExit(
            f"{platform} 本地 Playwright 后备模式没有登录态。这不代表当前 Chrome 或模型浏览器未登录；"
            "该脚本不能接管已有浏览器。请按 references/browser-session.md 使用已登录浏览器，"
            "或先执行人工登录命令：\n"
            + login_hint(root, args.account_file, args.name, platform)
        )

    try:
        from playwright.sync_api import TimeoutError as PlaywrightTimeoutError
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        raise SystemExit("playwright is required for browser publishing; install it before running this script") from exc

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=not args.headful)
        context_kwargs = {"storage_state": str(storage)} if storage and storage.exists() else {}
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        status = "dry-run" if args.dry_run else "clicked-unverified"
        title = str(content.get("title", ""))
        body = str(content.get("body") or content.get("script") or "")
        tags = content.get("tags", [])
        try:
            page.goto(publish_url, wait_until="domcontentloaded")
            page.wait_for_timeout(1500)

            if login_page_detected(page, login_url, selectors):
                if requires_manual_login(account):
                    raise SystemExit(
                        f"{platform} 登录态缺失或已失效，请先执行人工登录命令：\n"
                        + login_hint(root, args.account_file, args.name, platform)
                    )
                username_sel = selectors.get("username")
                password_sel = selectors.get("password")
                login_btn_sel = selectors.get("login_button")
                if not username_sel or not password_sel or not login_btn_sel:
                    raise SystemExit(f"{platform} password auth requires username, password and login_button selectors")
                page.goto(login_url, wait_until="domcontentloaded")
                page.fill(username_sel, str(account.get("username", "")))
                page.fill(password_sel, str(account.get("password", "")))
                page.click(login_btn_sel)
                wait_for_network(page)
                page.goto(publish_url, wait_until="domcontentloaded")
                page.wait_for_timeout(1500)
                if login_page_detected(page, login_url, selectors):
                    raise SystemExit(f"{platform} 登录未完成，请检查账号、密码或平台验证页面")

            title_sel = selectors.get("title")
            body_sel = selectors.get("body")
            tags_sel = selectors.get("tags")
            publish_btn_sel = selectors.get("publish_button")
            if title_sel:
                page.fill(title_sel, title)
            if body_sel:
                page.fill(body_sel, body)
            if tags_sel and tags:
                page.fill(tags_sel, " ".join(str(tag) for tag in tags))

            media_path = content.get("media_path")
            if media_path:
                media = Path(str(media_path))
                if not media.is_absolute():
                    media = bundle_dir / media
                media_input = selectors.get("media_input")
                if not media.exists():
                    raise SystemExit(f"media file not found: {media}")
                if not media_input:
                    raise SystemExit(f"{platform} content has media_path but selectors.media_input is missing")
                page.locator(media_input).set_input_files(str(media))
                upload_ready = selectors.get("upload_complete")
                if upload_ready:
                    try:
                        page.wait_for_selector(upload_ready, state="visible", timeout=120000)
                    except PlaywrightTimeoutError as exc:
                        raise SystemExit(f"{platform} media upload did not complete") from exc

            page.screenshot(path=str(bundle_dir / f"{platform}-before-publish.png"), full_page=True)
            if not args.dry_run:
                if not publish_btn_sel:
                    raise SystemExit(f"{platform} selectors.publish_button is missing")
                page.click(publish_btn_sel)
                wait_for_network(page)
                publish_success = selectors.get("publish_success")
                if publish_success:
                    try:
                        page.wait_for_selector(publish_success, state="visible", timeout=30000)
                    except PlaywrightTimeoutError as exc:
                        raise SystemExit(
                            f"{platform} 已点击发布，但未检测到成功标记；请人工确认页面状态"
                        ) from exc
                    status = "submitted"

            page.screenshot(path=str(bundle_dir / f"{platform}-after-publish.png"), full_page=True)
            if storage:
                storage.parent.mkdir(parents=True, exist_ok=True)
                context.storage_state(path=str(storage))
            (bundle_dir / f"{platform}-publish-result.json").write_text(
                json.dumps(
                    {
                        "platform": platform,
                        "title": title,
                        "status": status,
                        "login_url": login_url,
                        "publish_url": publish_url,
                        "media_path": content.get("media_path"),
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
        finally:
            context.close()
            browser.close()


if __name__ == "__main__":
    main()
