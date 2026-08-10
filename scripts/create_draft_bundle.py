#!/usr/bin/env python3
"""
Create a local draft bundle for platform-specific promo content.

Input can come from a JSON file or stdin.
The script only handles filesystem packaging; content generation itself is done by the model.
"""

from __future__ import annotations

import argparse
import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any


def slugify(value: str) -> str:
    text = value.strip().lower()
    slug = re.sub(r"[^a-z0-9]+", "-", text)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "draft"


def load_payload(path: str | None) -> dict[str, Any]:
    if path:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    import sys

    return json.loads(sys.stdin.read())


def render_markdown(payload: dict[str, Any]) -> str:
    lines: list[str] = []
    lines.append(f"# {payload.get('topic', '推广草稿')}")
    lines.append("")
    lines.append(f"- 主题: {payload.get('topic', '')}")
    lines.append(f"- 方向: {payload.get('direction', '')}")
    lines.append(f"- 自动发布: {str(bool(payload.get('auto_publish'))).lower()}")
    lines.append("")
    for item in payload.get("items", []):
        platform = item.get("platform", "")
        lines.append(f"## {platform}")
        lines.append(f"- 标题: {item.get('title', '')}")
        lines.append(f"- 正文: {item.get('body', '')}")
        tags = item.get("tags", [])
        if tags:
            lines.append(f"- 标签: {' '.join(tags)}")
        script = item.get("script")
        if script:
            lines.append(f"- 脚本: {script}")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", help="JSON file path")
    parser.add_argument("--draft-root", default=None)
    args = parser.parse_args()

    payload = load_payload(args.input)
    root = Path(args.draft_root) if args.draft_root else Path(__file__).resolve().parents[1] / "drafts"
    root.mkdir(parents=True, exist_ok=True)

    topic = payload.get("topic", "draft")
    stamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    bundle_dir = root / f"{stamp}-{slugify(str(topic))}"
    bundle_dir.mkdir(parents=True, exist_ok=False)

    (bundle_dir / "manifest.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    (bundle_dir / "content.md").write_text(render_markdown(payload), encoding="utf-8")
    print(str(bundle_dir))


if __name__ == "__main__":
    main()
