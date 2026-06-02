# Manuscript Structure Kit

[![Python](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**Manuscript Structure Kit** is a small, dependency-light open source Python library and CLI for preparing long-form fiction manuscripts for conversion, publishing tools, NLP pipelines, and public-domain cleanup projects.

It detects chapter heading levels, normalizes heading hierarchy, strips generated table-of-contents artifacts, standardizes ornamental scene breaks, counts manuscript words while ignoring Markdown syntax, and extracts representative beginning/middle/later samples from long books.

```bash
pip install manuscript-structure-kit
manuscript-kit inspect novel.md
manuscript-kit normalize novel.md --out clean.md
manuscript-kit sample novel.epub --words 8000 --out sample.txt
manuscript-kit wordcount novel.docx
```

> This repository is intentionally focused on local, deterministic manuscript-structure utilities. It does not require a database, hosted service, AI provider, or external account.

---

## Why use it?

Publishing and authoring tools often need to answer simple but surprisingly messy questions:

- Which heading level is actually used for chapters?
- Are `## Chapter 1` sections nested under a title page and should they become H1?
- Did a generated EPUB/DOCX table of contents get converted into body text?
- Are ornamental breaks like `* * *`, `— — —`, or `❦` consistent?
- How many real words are in this Markdown manuscript?
- Can I sample a long novel without only reading the opening chapters?

Manuscript Structure Kit provides deterministic utilities for those jobs without requiring a database, web app, cloud service, or AI provider.

---

## Features

### Core library

- Detect likely chapter heading level from Markdown H1/H2/H3 headings.
- Detect chapter-like headings such as `Chapter 1`, `Part II`, `Prologue`, and `Epilogue`.
- Detect common frontmatter/backmatter headings.
- Promote chapter headings to H1 while preserving relative subheading hierarchy.
- Strip generated TOC blocks and page-number/link artifacts.
- Normalize ornamental scene breaks to a consistent `***` marker.
- Deduplicate repeated scene-break markers.
- Count manuscript words while ignoring common Markdown syntax.
- Extract representative text samples from beginning, middle, and later sections.
- Validate inputs safely and read `.md`, `.txt`, `.docx`, and `.epub` text with the Python standard library.

### CLI

- `inspect` — summarize structure, heading counts, detected chapter level, and word count.
- `normalize` — clean TOC artifacts, normalize headings, and normalize scene breaks.
- `sample` — write a representative sample for review or downstream analysis.
- `wordcount` — print a manuscript word count.
- `chapterize` — replace chapter-like headings with a numbered template.

---

## Installation

### From PyPI, after release

```bash
pip install manuscript-structure-kit
```

### From a local checkout

```bash
cd manuscript-structure-kit
python -m pip install -e .
```

### Development install

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src/manuscript_kit
```

---

## Quick start

### Inspect a manuscript

```bash
manuscript-kit inspect examples/novel.md
```

Example output:

```text
Path: examples/novel.md
Size: 184231 bytes
Words: 82411
Headings: 42
Detected chapter level: 2
H1: 1
H2: 40
H3: 1
```

### Normalize Markdown structure

```bash
manuscript-kit normalize novel.md --out build/novel.clean.md
```

Before:

```markdown
# The Moonlit Door

## Contents

Chapter 1 ........ 1
Chapter 2 ........ 18

## Chapter 1

Rain silvered the windows.

— — —

The letter arrived at midnight.
```

After:

```markdown
# The Moonlit Door

# Chapter 1

Rain silvered the windows.

***

The letter arrived at midnight.
```

### Extract a representative sample

```bash
manuscript-kit sample novel.epub --words 8000 --out review-sample.txt
```

The sample contains labeled sections from the beginning, middle, and later parts of the book so downstream review is not biased toward the opening alone.

### Count words

```bash
manuscript-kit wordcount novel.docx
```

---

## Python API

```python
from manuscript_kit import (
    clean_toc_artifacts,
    count_words,
    detect_chapter_heading_level,
    extract_book_sample,
    normalize_heading_hierarchy,
    normalize_scene_breaks,
)

raw = Path("novel.md").read_text(encoding="utf-8")

chapter_level = detect_chapter_heading_level(raw)
clean = clean_toc_artifacts(raw)
clean = normalize_heading_hierarchy(clean, chapter_level=chapter_level)
clean = normalize_scene_breaks(clean)

print("Detected chapter level:", chapter_level)
print("Words:", count_words(clean))

sample = extract_book_sample("novel.epub", total_words=8000)
```

---

## API reference

### Headings

```python
detect_chapter_heading_level(markdown_text: str) -> int | None
normalize_heading_hierarchy(markdown_text: str, chapter_level: int | None = None) -> str
find_markdown_headings(markdown_text: str) -> list[Heading]
is_chapterlike_heading(text: str) -> bool
is_frontmatter_heading(text: str) -> bool
clean_toc_artifacts(markdown_text: str) -> str
```

### Scene breaks

```python
is_scene_break(line: str) -> bool
normalize_scene_breaks(markdown_text: str, marker: str = "***") -> str
```

### Sampling and word counts

```python
count_words(text: str) -> int
extract_text_sample(text: str, total_words: int = 8000) -> str
extract_book_sample(path: str | Path, total_words: int = 8000) -> str
```

### Validation and text extraction

```python
validate_input_file(path: str | Path, max_bytes: int = 200 * 1024 * 1024) -> FileValidation
```

The built-in reader supports `.md`, `.markdown`, `.txt`, `.docx`, and `.epub`. ZIP-based formats are checked for unsafe member paths and oversized entries before extraction.

---

## Design principles

- **Deterministic first.** Heuristics should be explainable and regression-testable.
- **Markdown-first.** Markdown is the clean interchange format for manuscript structure.
- **Small dependency surface.** The core package uses only the Python standard library.
- **Safe file handling.** ZIP-based document formats are read with path and size checks.
- **Standalone by default.** No app routes, databases, cloud storage, or vendor SDKs.

---

## Roadmap

- Add richer EPUB spine-order extraction for more accurate sampling.
- Add optional DOCX heading-style detection when `python-docx` is installed.
- Add more multilingual chapter heading patterns.
- Add structured JSON output for `inspect`.
- Publish a small public-domain fixture pack.
- Split advanced cleanup recipes into separate opt-in modules.

---

## Contributing

Contributions are welcome. Please see [CONTRIBUTING.md](CONTRIBUTING.md) and open an issue with a minimal manuscript snippet that reproduces any formatting bug.

For privacy and copyright safety, do not upload entire copyrighted manuscripts to issues. Small excerpts that demonstrate a structural problem are usually enough.

---

## License

MIT. See [LICENSE](LICENSE).
