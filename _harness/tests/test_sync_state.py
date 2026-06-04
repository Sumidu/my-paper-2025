import sys
import json
from pathlib import Path
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.sync_state import (
    file_hash, load_state, save_state,
    update_section_state, get_section_state, detect_conflict
)


def test_file_hash_returns_string(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    h = file_hash(f)
    assert isinstance(h, str)
    assert len(h) == 12


def test_file_hash_missing_file_returns_none(tmp_path):
    assert file_hash(tmp_path / "missing.md") is None


def test_file_hash_changes_with_content(tmp_path):
    f = tmp_path / "test.md"
    f.write_text("hello")
    h1 = file_hash(f)
    f.write_text("world")
    h2 = file_hash(f)
    assert h1 != h2


def test_load_state_missing_file_returns_empty(tmp_path):
    state = load_state(tmp_path / "sync-state.json")
    assert state == {"sections": {}}


def test_save_and_load_roundtrip(tmp_path):
    path = tmp_path / "sync-state.json"
    state = {"sections": {"10_abstract": {"md_hash": "abc", "tex_hash": "def"}}}
    save_state(state, path)
    loaded = load_state(path)
    assert loaded["sections"]["10_abstract"]["md_hash"] == "abc"
    assert "last_sync" in loaded


def test_update_section_state(tmp_path):
    path = tmp_path / "sync-state.json"
    update_section_state("20_related_work", "aaa", "bbb", path)
    state = load_state(path)
    assert state["sections"]["20_related_work"]["md_hash"] == "aaa"
    assert state["sections"]["20_related_work"]["tex_hash"] == "bbb"
    assert "synced_at" in state["sections"]["20_related_work"]


def test_detect_conflict_both_changed(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"

    md.write_text("original md")
    tex.write_text("original tex")

    update_section_state("20_related_work", file_hash(md), file_hash(tex), state_path)

    md.write_text("updated md")
    tex.write_text("updated tex")

    assert detect_conflict("20_related_work", md, tex, state_path) is True


def test_detect_conflict_only_md_changed(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"

    md.write_text("original md")
    tex.write_text("original tex")
    update_section_state("20_related_work", file_hash(md), file_hash(tex), state_path)

    md.write_text("updated md")
    # tex unchanged

    assert detect_conflict("20_related_work", md, tex, state_path) is False


def test_detect_conflict_never_synced_returns_false(tmp_path):
    md = tmp_path / "section.md"
    tex = tmp_path / "section.tex"
    state_path = tmp_path / "sync-state.json"
    md.write_text("content")
    tex.write_text("content")

    assert detect_conflict("new_section", md, tex, state_path) is False
