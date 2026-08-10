#!/usr/bin/env python3
"""通过可见浏览器完成一次人工登录并保存本地登录态。"""

from __future__ import annotations

import argparse
from pathlib import Path

from account_utils import canonical_platform, load_account, session_path


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--platform", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--wait-seconds", type=int, default=120, help="无法交互确认时的最长等待时间")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    platform = canonical_platform(args.platform)
    platform_cfg = load_account(root, args.account_file, args.name, platform)

    login_url = platform_cfg.get("login_url")
    storage_path = session_path(root, platform_cfg)
    if not login_url or not storage_path:
        raise SystemExit(f"missing login_url or storage_state for {args.platform}")

    try:
        from playwright.sync_api import sync_playwright
    except Exception as exc:  # pragma: no cover
        raise SystemExit("playwright is required for session bootstrap") from exc

    storage_path.parent.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context_kwargs = {"storage_state": str(storage_path)} if storage_path.exists() else {}
        context = browser.new_context(**context_kwargs)
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        print(f"请在打开的浏览器里完成 {platform} 登录。短信验证码或抖音授权必须由你本人操作。")
        try:
            input("登录成功后回到终端按回车保存登录态：")
        except EOFError:
            page.wait_for_timeout(args.wait_seconds * 1000)

        auth_success_selector = platform_cfg.get("selectors", {}).get("auth_success")
        if auth_success_selector:
            try:
                page.wait_for_selector(auth_success_selector, state="visible", timeout=5000)
            except Exception:
                context.close()
                browser.close()
                raise SystemExit(
                    f"未检测到登录成功标记 {auth_success_selector}，未保存登录态；请检查 selectors.auth_success"
                )

        context.storage_state(path=str(storage_path))
        context.close()
        browser.close()
        print(str(storage_path))


if __name__ == "__main__":
    main()
