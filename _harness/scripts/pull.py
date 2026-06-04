from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config
from lib.sync_state import (
    detect_conflict, update_section_state,
    file_hash, get_section_state,
)

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def _git_pull(repo_path: Path) -> bool:
    try:
        result = subprocess.run(
            ["git", "pull"], cwd=repo_path,
            capture_output=True, text=True, check=True,
        )
        print(result.stdout.strip() or "Already up to date.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"git pull failed: {e.stderr.strip()}")
        return False


def _tex_to_md(tex_path: Path) -> str:
    result = subprocess.run(
        [
            "pandoc", "--from", "latex", "--to", "markdown",
            "--wrap=none", "--atx-headers",
            str(tex_path),
        ],
        capture_output=True, text=True, check=True,
    )
    return result.stdout


def _tex_changed_since_sync(stem: str, tex_path: Path, state_path: Path) -> bool:
    prev = get_section_state(stem, state_path)
    if not prev:
        return True
    return file_hash(tex_path) != prev.get("tex_hash")


def run(root: Path = _HARNESS_ROOT) -> dict:
    config = load_config(root)
    if not config.overleaf_repo:
        print("overleaf_repo not set in paper.yaml.")
        return {}

    overleaf = Path(config.overleaf_repo).expanduser().resolve()
    if not overleaf.exists():
        print(f"Overleaf repo not found at: {overleaf}")
        return {}

    if not _git_pull(overleaf):
        return {}

    article_dir = root / "article"
    state_path = article_dir / "sync-state.json"
    tex_dir = overleaf / "sections"

    if not tex_dir.exists():
        print("No sections/ directory in Overleaf repo. Nothing to pull.")
        return {"pulled": 0, "conflicts": [], "skipped": 0}

    pulled: list[str] = []
    conflicts: list[str] = []
    skipped: list[str] = []

    for tex_path in sorted(tex_dir.glob("*.tex")):
        stem = tex_path.stem
        md_path = article_dir / "sections" / f"{stem}.md"

        if not _tex_changed_since_sync(stem, tex_path, state_path):
            skipped.append(stem)
            continue

        if detect_conflict(stem, md_path, tex_path, state_path):
            print(
                f"  CONFLICT {stem}: both .md and .tex changed since last sync — "
                "resolve manually, then re-run /paper:pull"
            )
            conflicts.append(stem)
            continue

        try:
            md_content = _tex_to_md(tex_path)
            md_path.parent.mkdir(parents=True, exist_ok=True)
            md_path.write_text(md_content)
            update_section_state(stem, file_hash(md_path), file_hash(tex_path), state_path)
            pulled.append(stem)
            print(f"  pulled: {stem}.md")
        except subprocess.CalledProcessError as e:
            print(f"  ERROR converting {stem}: {e.stderr[:200]}")

    return {"pulled": len(pulled), "conflicts": conflicts, "skipped": len(skipped)}


if __name__ == "__main__":
    result = run()
    if not result:
        sys.exit(1)
