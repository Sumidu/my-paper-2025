import sys
from datetime import date
from pathlib import Path
from unittest.mock import patch, MagicMock, call
import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

import transcribe  # top-level import so patch("transcribe.load_whisper_model") works


@pytest.fixture
def paper_root(tmp_path):
    """Minimal paper project root with paper.yaml and recordings dir."""
    (tmp_path / "paper.yaml").write_text("title: Test Paper\n")
    (tmp_path / "ideas" / "recordings").mkdir(parents=True)
    (tmp_path / "ideas" / "transcripts" / "translated").mkdir(parents=True)
    return tmp_path


def make_mp3(root, name="test_recording.mp3"):
    path = root / "ideas" / "recordings" / name
    path.write_bytes(b"fake mp3 content")
    return path


def test_no_recordings_returns_empty(paper_root):
    result = transcribe.run(paper_root)
    assert result == []


def test_new_recording_is_transcribed(paper_root):
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Hello world"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert len(result) == 1
    assert "transcripts" in result[0]
    assert result[0].endswith(".md")


def test_transcript_file_contains_text(paper_root):
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "My research idea"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        transcribe.run(paper_root)

    transcripts = list((paper_root / "ideas" / "transcripts").glob("*.md"))
    assert len(transcripts) == 1
    assert "My research idea" in transcripts[0].read_text()


def test_already_transcribed_file_skipped(paper_root):
    mp3 = make_mp3(paper_root)
    stem = f"{date.today().isoformat()}_{mp3.stem}"
    (paper_root / "ideas" / "transcripts" / f"{stem}.md").write_text("existing")

    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "should not run"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert result == []
    mock_model.transcribe.assert_not_called()


def test_non_english_produces_translation(paper_root):
    (paper_root / "paper.yaml").write_text("title: Test\nlanguage: de\n")
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "Meine Forschungsidee"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        result = transcribe.run(paper_root)

    assert len(result) == 2
    assert any("translated" in r for r in result)


def test_translation_calls_whisper_with_translate_task(paper_root):
    (paper_root / "paper.yaml").write_text("title: Test\nlanguage: de\n")
    make_mp3(paper_root)
    mock_model = MagicMock()
    mock_model.transcribe.return_value = {"text": "some text"}

    with patch("transcribe.load_whisper_model", return_value=mock_model):
        transcribe.run(paper_root)

    tasks = [c.kwargs.get("task") for c in mock_model.transcribe.call_args_list]
    assert "translate" in tasks
