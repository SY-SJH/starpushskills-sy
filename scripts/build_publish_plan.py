#!/usr/bin/env python3
"""
Build a publish plan from a draft bundle and a selected account.

This does not post to external platforms. It only prepares the bundle that
automation or a human operator can use next.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

from account_utils import canonical_platform, load_account, redact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--bundle-dir", required=True)
    parser.add_argument("--platform", required=True)
    parser.add_argument("--name", required=True)
    parser.add_argument("--account-file", default="accounts.json")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    bundle_dir = Path(args.bundle_dir)
    manifest = json.loads((bundle_dir / "manifest.json").read_text(encoding="utf-8"))
    platform = canonical_platform(args.platform)
    account = {
        "name": args.name,
        "platform": platform,
        "account": redact(load_account(root, args.account_file, args.name, platform)),
    }

    plan = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "bundle_dir": str(bundle_dir),
        "platform": platform,
        "account": account,
        "draft": manifest,
        "status": "pending",
    }
    plan_path = bundle_dir / f"publish-plan-{platform}.json"
    plan_path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
    print(str(plan_path))


if __name__ == "__main__":
    main()
