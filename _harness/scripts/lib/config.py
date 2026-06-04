from __future__ import annotations

import yaml
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class ZoteroConfig:
    collection: Optional[str] = None
    bibtex_export: Optional[str] = None


@dataclass
class PaperConfig:
    title: str
    target: str = "overleaf"
    overleaf_repo: Optional[str] = None
    csl: str = "apa.csl"
    citation_package: str = "natbib"
    language: str = "en"
    whisper_model: str = "large-v3-turbo"
    research_max_results: int = 200
    scholar_max_results: int = 20
    enrich_min_papers: int = 2
    exclude_sections: list = field(default_factory=list)
    zotero: ZoteroConfig = field(default_factory=ZoteroConfig)


_DEFAULTS = {
    "target": "overleaf",
    "csl": "apa.csl",
    "citation_package": "natbib",
    "language": "en",
    "whisper_model": "large-v3-turbo",
    "research_max_results": 200,
    "scholar_max_results": 20,
    "enrich_min_papers": 2,
    "exclude_sections": [],
}


def load_config(root: Path) -> PaperConfig:
    config_path = root / "paper.yaml"
    if not config_path.exists():
        raise FileNotFoundError(f"paper.yaml not found at {config_path}")

    data = yaml.safe_load(config_path.read_text()) or {}

    if "title" not in data:
        raise ValueError("paper.yaml must contain a 'title' field")

    zotero_data = data.pop("zotero", {}) or {}
    zotero = ZoteroConfig(**{k: v for k, v in zotero_data.items()
                             if k in ZoteroConfig.__dataclass_fields__})

    for key, default in _DEFAULTS.items():
        data.setdefault(key, default)

    known_fields = set(PaperConfig.__dataclass_fields__) - {"zotero"}
    filtered = {k: v for k, v in data.items() if k in known_fields}

    return PaperConfig(zotero=zotero, **filtered)
