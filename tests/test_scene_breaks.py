from pathlib import Path

from manuscript_kit import is_scene_break, normalize_scene_breaks

FIXTURES = Path(__file__).parent / "fixtures"


def test_recognizes_common_scene_breaks() -> None:
    assert is_scene_break("* * *")
    assert is_scene_break("— — —")
    assert is_scene_break("⁂")
    assert not is_scene_break("This is ***important*** text")


def test_normalizes_and_deduplicates_breaks() -> None:
    text = (FIXTURES / "ornamental_breaks.md").read_text(encoding="utf-8")

    normalized = normalize_scene_breaks(text)

    assert "— — —" not in normalized
    assert "* * *" not in normalized
    assert normalized.count("***") == 2
