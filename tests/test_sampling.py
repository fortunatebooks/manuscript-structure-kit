from manuscript_kit import extract_text_sample


def test_short_text_returns_whole_text() -> None:
    text = "One short paragraph.\n\nAnother short paragraph."

    assert extract_text_sample(text, total_words=100) == text


def test_long_text_samples_distinct_sections() -> None:
    paragraphs = [f"Paragraph {i} has several useful manuscript words." for i in range(80)]
    text = "\n\n".join(paragraphs)

    sample = extract_text_sample(text, total_words=60)

    assert "EXTRACT 1" in sample
    assert "EXTRACT 2" in sample
    assert "EXTRACT 3" in sample
    assert "Paragraph 0" in sample
    assert "Paragraph 79" not in sample
