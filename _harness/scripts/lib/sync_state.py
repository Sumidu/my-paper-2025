from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional


def file_hash(path: Path) -> Optional[str]:
    """SHA-256 of file contents, truncated to 12 chars. None if file missing."""
    if not path.exists():
        return None
    return hashlib.sha256(path.read_bytes()).hexdigest()[:12]


def load_state(path: Path) -> dict:
    if not path.exists():
        return {"sections": {}}
    return json.loads(path.read_text())


def save_state(state: dict, path: Path) -> None:
    state["last_sync"] = datetime.now(timezone.utc).isoformat()
    path.write_text(json.dumps(state, indent=2))


def get_section_state(name: str, path: Path) -> dict:
    return load_state(path).get("sections", {}).get(name, {})


def update_section_state(
    name: str, md_hash: str, tex_hash: str, path: Path
) -> None:
    state = load_state(path)
    state.setdefault("sections", {})[name] = {
        "md_hash": md_hash,
        "tex_hash": tex_hash,
        "synced_at": datetime.now(timezone.utc).isoformat(),
    }
    save_state(state, path)


def detect_conflict(name: str, md_path: Path, tex_path: Path, path: Path) -> bool:
    """True only when both .md and .tex changed since last sync."""
    prev = get_section_state(name, path)
    if not prev:
        return False
    md_changed = file_hash(md_path) != prev.get("md_hash")
    tex_changed = file_hash(tex_path) != prev.get("tex_hash")
    return md_changed and tex_changed
