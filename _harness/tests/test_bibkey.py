import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from lib.bibkey import make_bibkey, resolve_collision


def test_basic_key():
    assert make_bibkey(["Smith J"], 2024, "Attention in Hybrid Work") == "smith2024attention"


def test_stop_words_skipped():
    # "The" is a stop word, "Role" is not
    assert make_bibkey(["Jones A"], 2023, "The Role of Notifications") == "jones2023role"


def test_unicode_normalized():
    assert make_bibkey(["Müller K"], 2022, "Über die Arbeit") == "muller2022uber"


def test_comma_separated_author():
    # "Smith, John" → last name is "Smith"
    assert make_bibkey(["Smith, John"], 2021, "Focus States") == "smith2021focus"


def test_no_authors_uses_unknown():
    key = make_bibkey([], 2020, "Some Paper")
    assert key.startswith("unknown2020")


def test_year_truncated_to_four_digits():
    key = make_bibkey(["Brown X"], "2024-01", "Deep Learning")
    assert "2024" in key
    assert "01" not in key


def test_collision_adds_suffix():
    existing = {"smith2024attention"}
    assert resolve_collision("smith2024attention", existing) == "smith2024attentiona"


def test_collision_chains():
    existing = {"smith2024attention", "smith2024attentiona"}
    assert resolve_collision("smith2024attention", existing) == "smith2024attentionb"
