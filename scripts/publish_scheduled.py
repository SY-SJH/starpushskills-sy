#!/usr/bin/env python3
"""执行已经到时间的本地推广发布队列。"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import Any


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: dict[str, Any]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def is_due(value: str) -> bool:
    try:
        scheduled = datetime.fromisoformat(value)
    except ValueError as exc:
        raise SystemExit(f"invalid publish_at: {value}") from exc
    if scheduled.tzinfo is None:
        return datetime.now() >= scheduled
    return datetime.now(scheduled.tzinfo) >= scheduled


def process_bundle(root: Path, schedule_path: Path, override_headful: bool) -> str:
    schedule = read_json(schedule_path)
    if schedule.get("status") != "scheduled" or not is_due(str(schedule.get("publish_at", ""))):
        return "skipped"

    schedule["status"] = "running"
    schedule["started_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    write_json(schedule_path, schedule)
    bundle_dir = schedule_path.parent
    try:
        for platform in schedule.get("platforms", []):
            command = [
                sys.executable,
                str(root / "scripts" / "publish_via_browser.py"),
                "--bundle-dir",
                str(bundle_dir),
                "--platform",
                str(platform),
                "--name",
                str(schedule["name"]),
                "--account-file",
                str(schedule.get("account_file", "accounts.json")),
            ]
            if override_headful or schedule.get("headful"):
                command.append("--headful")
            subprocess.run(command, check=True)
    except subprocess.CalledProcessError as exc:
        schedule["status"] = "failed"
        schedule["error"] = f"platform publish exited with code {exc.returncode}"
        schedule["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
        write_json(schedule_path, schedule)
        return "failed"

    schedule["status"] = "completed"
    schedule["finished_at"] = datetime.now().astimezone().isoformat(timespec="seconds")
    write_json(schedule_path, schedule)
    return "completed"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--draft-root", default=None)
    parser.add_argument("--once", action="store_true", help="扫描一次到期草稿后退出")
    parser.add_argument("--headful", action="store_true", help="定时任务执行时打开可见浏览器")
    args = parser.parse_args()

    root = Path(__file__).resolve().parents[1]
    draft_root = Path(args.draft_root) if args.draft_root else root / "drafts"
    draft_root.mkdir(parents=True, exist_ok=True)
    counts = {"completed": 0, "failed": 0, "skipped": 0}
    for schedule_path in sorted(draft_root.glob("*/schedule.json")):
        result = process_bundle(root, schedule_path, args.headful)
        counts[result] += 1
    print(json.dumps(counts, ensure_ascii=False))


if __name__ == "__main__":
    main()
