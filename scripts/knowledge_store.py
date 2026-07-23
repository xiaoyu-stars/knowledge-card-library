#!/usr/bin/env python3
"""Initialize and update the persistent Markdown knowledge-card library."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_ROOT = Path(
    os.environ.get("KNOWLEDGE_BASE_ROOT", str(Path.home() / "KnowledgeBase"))
).expanduser()
VALID_STATUSES = {"new", "learning", "mastered", "needs_revision"}


def now_iso() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def atomic_json_write(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp_name = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            json.dump(value, handle, ensure_ascii=False, indent=2)
            handle.write("\n")
        os.replace(temp_name, path)
    except Exception:
        try:
            os.unlink(temp_name)
        except FileNotFoundError:
            pass
        raise


def empty_store() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "collection": "knowledge_cards",
        "updated_at": now_iso(),
        "cards": [],
    }


def safe_filename(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "-", value).strip().rstrip(".")
    cleaned = re.sub(r"\s+", "-", cleaned)
    if not cleaned:
        raise ValueError("Cannot derive a filename from an empty title")
    return cleaned + ".md" if not cleaned.lower().endswith(".md") else cleaned


def load_store(root: Path) -> dict[str, Any]:
    store_path = root / "data" / "store.json"
    if not store_path.exists():
        return empty_store()
    with store_path.open("r", encoding="utf-8-sig") as handle:
        store = json.load(handle)
    if not isinstance(store.get("cards"), list):
        raise ValueError(f"Invalid store: {store_path} must contain a cards array")
    return store


def render_index(store: dict[str, Any]) -> str:
    status_labels = {
        "new": "新建",
        "learning": "学习中",
        "mastered": "已掌握",
        "needs_revision": "需修订",
    }
    lines = [
        "# 知识卡片库",
        "",
        "这里保存用于主动回忆和长期复习的 Markdown 知识卡片。",
        "",
        "## 当前卡片",
        "",
    ]
    cards = sorted(store["cards"], key=lambda card: str(card.get("title", "")).casefold())
    if cards:
        lines.extend(["| 主题 | 类型 | 卡片数 | 状态 | 文件 |", "|---|---|---:|---|---|"])
        for card in cards:
            title = str(card.get("title", "")).replace("|", "\\|")
            content_type = str(card.get("content_type", "")).replace("|", "\\|")
            count = len(card.get("items", []))
            status = status_labels.get(card.get("status", "new"), str(card.get("status", "new")))
            filename = Path(str(card["markdown_file"])).name
            lines.append(f"| {title} | {content_type} | {count} | {status} | [打开卡片](./cards/{filename}) |")
    else:
        lines.append("尚未添加知识卡片。")
    lines.extend(
        [
            "",
            "## 状态说明",
            "",
            "- `新建`：尚未复习",
            "- `学习中`：正在建立记忆",
            "- `已掌握`：能够稳定主动回忆",
            "- `需修订`：内容需要核实或更新",
            "",
        ]
    )
    return "\n".join(lines)


def initialize(root: Path) -> None:
    (root / "cards").mkdir(parents=True, exist_ok=True)
    (root / "data").mkdir(parents=True, exist_ok=True)
    store_path = root / "data" / "store.json"
    if store_path.exists():
        store = load_store(root)
    else:
        store = empty_store()
        atomic_json_write(store_path, store)
    (root / "index.md").write_text(render_index(store), encoding="utf-8", newline="\n")


def validate_payload(payload: dict[str, Any]) -> None:
    for field in ("id", "title", "content_type", "source", "items"):
        if field not in payload:
            raise ValueError(f"Payload missing required field: {field}")
    if not isinstance(payload["id"], str) or not payload["id"].strip():
        raise ValueError("Payload id must be a non-empty string")
    if not isinstance(payload["source"], dict) or not isinstance(payload["source"].get("text"), str):
        raise ValueError("Payload source.text must be a string")
    if not isinstance(payload["items"], list) or not payload["items"]:
        raise ValueError("Payload items must be a non-empty array")
    seen_ids: set[str] = set()
    for item in payload["items"]:
        for field in ("id", "kind", "front", "back"):
            if not isinstance(item.get(field), str) or not item[field].strip():
                raise ValueError(f"Every item requires a non-empty string field: {field}")
        if item["id"] in seen_ids:
            raise ValueError(f"Duplicate item id: {item['id']}")
        seen_ids.add(item["id"])
    status = payload.get("status", "new")
    if status not in VALID_STATUSES:
        raise ValueError(f"Unsupported status: {status}")


def upsert(root: Path, payload_path: Path, markdown_path: Path) -> None:
    initialize(root)
    with payload_path.open("r", encoding="utf-8-sig") as handle:
        payload = json.load(handle)
    validate_payload(payload)
    if not markdown_path.is_file():
        raise FileNotFoundError(f"Markdown draft not found: {markdown_path}")

    store = load_store(root)
    existing_index = next(
        (index for index, card in enumerate(store["cards"]) if card.get("id") == payload["id"]),
        None,
    )
    timestamp = now_iso()
    filename = safe_filename(str(payload.get("markdown_filename") or payload["title"]))
    destination = root / "cards" / filename
    record = dict(payload)
    record.pop("markdown_filename", None)
    record["status"] = record.get("status", "new")
    record["updated_at"] = timestamp
    record["markdown_file"] = f"cards/{filename}"

    if existing_index is None:
        record["created_at"] = timestamp
        record["version"] = 1
        store["cards"].append(record)
    else:
        previous = store["cards"][existing_index]
        record["created_at"] = previous.get("created_at", timestamp)
        record["version"] = int(previous.get("version", 1)) + 1
        store["cards"][existing_index] = record

    shutil.copy2(markdown_path, destination)
    store["updated_at"] = timestamp
    atomic_json_write(root / "data" / "store.json", store)
    (root / "index.md").write_text(render_index(store), encoding="utf-8", newline="\n")
    print(json.dumps({"ok": True, "id": record["id"], "version": record["version"], "markdown": str(destination)}, ensure_ascii=False))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    init_parser = subparsers.add_parser("init", help="Initialize a knowledge library")
    init_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    upsert_parser = subparsers.add_parser("upsert", help="Add or revise one topic")
    upsert_parser.add_argument("--root", type=Path, default=DEFAULT_ROOT)
    upsert_parser.add_argument("--payload", type=Path, required=True)
    upsert_parser.add_argument("--markdown", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    root = args.root.resolve()
    if args.command == "init":
        initialize(root)
        print(json.dumps({"ok": True, "root": str(root)}, ensure_ascii=False))
    else:
        upsert(root, args.payload.resolve(), args.markdown.resolve())


if __name__ == "__main__":
    main()

