from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

# Allow running directly or as module
sys.path.insert(0, str(Path(__file__).parent))
from lib.config import load_config

_HARNESS_ROOT = Path(__file__).parent.parent.parent


def load_whisper_model(model_name: str):
    """Thin wrapper — exists so tests can patch it."""
    import whisper
    return whisper.load_model(model_name)


def _find_new_recordings(recordings_dir: Path, transcripts_dir: Path) -> list[Path]:
    today = date.today().isoformat()
    existing = {p.stem for p in transcripts_dir.glob("*.md")}
    new = []
    for mp3 in sorted(recordings_dir.glob("*.mp3")):
        if f"{today}_{mp3.stem}" not in existing:
            new.append(mp3)
    return new


def _transcribe_file(
    model,
    mp3_path: Path,
    output_path: Path,
    language: str,
    task: str = "transcribe",
) -> None:
    result = model.transcribe(str(mp3_path), language=language, task=task)
    text = result["text"].strip()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    label = "Translation" if task == "translate" else "Transcript"
    output_path.write_text(f"# {label}: {mp3_path.name}\n\n{text}\n")


def run(root: Path = _HARNESS_ROOT) -> list[str]:
    """Transcribe new MP3s. Returns list of created file paths."""
    config = load_config(root)
    recordings_dir = root / "ideas" / "recordings"
    transcripts_dir = root / "ideas" / "transcripts"
    translated_dir = transcripts_dir / "translated"

    recordings_dir.mkdir(parents=True, exist_ok=True)
    transcripts_dir.mkdir(parents=True, exist_ok=True)

    new = _find_new_recordings(recordings_dir, transcripts_dir)
    if not new:
        return []

    model = load_whisper_model(config.whisper_model)
    today = date.today().isoformat()
    created = []

    for mp3 in new:
        stem = f"{today}_{mp3.stem}"
        transcript_path = transcripts_dir / f"{stem}.md"
        _transcribe_file(model, mp3, transcript_path, config.language)
        created.append(str(transcript_path))

        if config.language != "en":
            translated_path = translated_dir / f"{stem}.md"
            _transcribe_file(model, mp3, translated_path, config.language, task="translate")
            created.append(str(translated_path))

    return created


if __name__ == "__main__":
    created = run()
    if created:
        print(f"Transcribed {len(created)} file(s):")
        for path in created:
            print(f"  {path}")
    else:
        print("No new recordings found in ideas/recordings/")
