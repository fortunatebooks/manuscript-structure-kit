from pathlib import Path

from manuscript_kit import count_words, validate_input_file
from manuscript_kit.cli import main


def test_count_words_ignores_markdown_markup() -> None:
    assert count_words("# Chapter 1\n\nThis is **bold** and [linked text](https://example.com).") == 8


def test_validate_input_file_rejects_missing_file(tmp_path: Path) -> None:
    result = validate_input_file(tmp_path / "missing.md")

    assert not result.ok
    assert "does not exist" in result.message


def test_cli_wordcount(tmp_path: Path, capsys) -> None:  # type: ignore[no-untyped-def]
    manuscript = tmp_path / "book.md"
    manuscript.write_text("# Chapter 1\n\nThree simple words.", encoding="utf-8")

    exit_code = main(["wordcount", str(manuscript)])

    assert exit_code == 0
    assert capsys.readouterr().out.strip() == "5"


def test_cli_sample_creates_output_parent_directory(tmp_path: Path) -> None:
    manuscript = tmp_path / "book.md"
    output = tmp_path / "samples" / "review.txt"
    manuscript.write_text("One short paragraph.\n\nAnother short paragraph.", encoding="utf-8")

    exit_code = main(["sample", str(manuscript), "--words", "10", "--out", str(output)])

    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == "One short paragraph.\n\nAnother short paragraph.\n"


def test_cli_chapterize_only_rewrites_chapterlike_headings(tmp_path: Path) -> None:
    manuscript = tmp_path / "book.md"
    output = tmp_path / "chapterized.md"
    manuscript.write_text(
        "# My Novel\n\n"
        "## Copyright\n\n"
        "All rights reserved.\n\n"
        "## Chapter 1\n\n"
        "First scene.\n\n"
        "## Chapter Two\n\n"
        "Second scene.\n",
        encoding="utf-8",
    )

    exit_code = main(["chapterize", str(manuscript), "--out", str(output)])

    assert exit_code == 0
    assert output.read_text(encoding="utf-8") == (
        "# My Novel\n\n"
        "## Copyright\n\n"
        "All rights reserved.\n\n"
        "## Chapter 1\n\n"
        "First scene.\n\n"
        "## Chapter 2\n\n"
        "Second scene.\n"
    )
