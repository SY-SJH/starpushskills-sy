#!/usr/bin/env python3
"""读取同事账号，并以脱敏结果输出给操作者。"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from account_utils import canonical_platform, load_account, redact


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--account-file", default="accounts.json")
    parser.add_argument("--platform", required=True)
    parser.add_argument("--name", required=True)
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    platform = canonical_platform(args.platform)
    account = load_account(root, args.account_file, args.name, platform)
    print(
        json.dumps(
            {"name": args.name, "platform": platform, "account": redact(account)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
