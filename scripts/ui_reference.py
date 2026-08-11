#!/usr/bin/env python3
"""读取并选择 StarPush 的真实界面参考截图。"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_ui_reference_manifest(root: Path) -> dict[str, Any]:
    """读取界面素材清单，并检查最小结构。"""

    path = root / "references" / "ui-reference.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or not isinstance(payload.get("assets"), list):
        raise ValueError(f"界面素材清单格式错误：{path}")
    return payload


def select_ui_references(
    root: Path,
    *,
    mode: str,
    topic: str,
    direction: str,
    requested_ids: list[str] | None = None,
) -> list[dict[str, Any]]:
    """按显式 ID 或主题关键词选择需要上传的小云雀参考素材。"""

    manifest = load_ui_reference_manifest(root)
    assets = [item for item in manifest["assets"] if isinstance(item, dict)]
    by_id = {str(item.get("id")): item for item in assets if item.get("id")}

    requested = list(
        dict.fromkeys(item.strip() for item in (requested_ids or []) if item.strip())
    )
    if requested:
        unknown = [item for item in requested if item not in by_id]
        if unknown:
            choices = ", ".join(by_id)
            raise ValueError(f"未知界面参考素材：{', '.join(unknown)}；可选值：{choices}")
        selected = [by_id[item] for item in requested]
    else:
        corpus = f"{topic}\n{direction}".lower()
        product_demo_keywords = manifest.get("product_demo_keywords") or []
        should_auto_attach = mode == "product-demo" or (
            mode == "auto"
            and any(str(keyword).lower() in corpus for keyword in product_demo_keywords)
        )
        if not should_auto_attach:
            return []

        selected = []
        for item in assets:
            keywords = item.get("keywords") or []
            if any(str(keyword).lower() in corpus for keyword in keywords):
                selected.append(item)
        for item in assets:
            if item.get("default") and item not in selected:
                selected.append(item)
        limit = int(manifest.get("max_automatic_references") or 3)
        selected = selected[: max(1, limit)]

    resolved: list[dict[str, Any]] = []
    asset_root = root / "assets" / "ui-reference"
    for item in selected:
        file_name = Path(str(item.get("file") or "")).name
        path = asset_root / file_name
        if not file_name or not path.is_file():
            raise ValueError(f"界面参考素材不存在：{path}")
        resolved.append({**item, "path": path})
    return resolved
