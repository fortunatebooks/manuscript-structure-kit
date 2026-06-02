"""Input-file validation and safe text extraction for manuscript utilities."""

from __future__ import annotations

import xml.etree.ElementTree as ET
import zipfile
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path

SUPPORTED_EXTENSIONS = {".md", ".markdown", ".txt", ".docx", ".epub"}
DEFAULT_MAX_BYTES = 200 * 1024 * 1024
DEFAULT_MAX_ZIP_MEMBER_BYTES = 50 * 1024 * 1024


@dataclass(frozen=True)
class FileValidation:
    """Result returned by :func:`validate_input_file`."""

    path: Path
    ok: bool
    extension: str
    size_bytes: int
    message: str = ""


def validate_input_file(path: str | Path, max_bytes: int = DEFAULT_MAX_BYTES) -> FileValidation:
    """Validate that a manuscript path is readable, bounded, and supported."""
    resolved = Path(path)
    if not resolved.exists():
        return FileValidation(resolved, False, resolved.suffix.lower(), 0, "file does not exist")
    if not resolved.is_file():
        return FileValidation(resolved, False, resolved.suffix.lower(), 0, "path is not a file")
    size = resolved.stat().st_size
    extension = resolved.suffix.lower()
    if size == 0:
        return FileValidation(resolved, False, extension, size, "file is empty")
    if size > max_bytes:
        return FileValidation(resolved, False, extension, size, "file exceeds maximum allowed size")
    if extension not in SUPPORTED_EXTENSIONS:
        return FileValidation(resolved, False, extension, size, "unsupported file extension")
    return FileValidation(resolved, True, extension, size)


def read_text(path: str | Path) -> str:
    """Read text from TXT/Markdown, DOCX, or EPUB using only the standard library."""
    validation = validate_input_file(path)
    if not validation.ok:
        raise ValueError(validation.message)
    extension = validation.extension
    if extension in {".txt", ".md", ".markdown"}:
        return validation.path.read_text(encoding="utf-8", errors="replace")
    if extension == ".docx":
        return _read_docx_text(validation.path)
    if extension == ".epub":
        return _read_epub_text(validation.path)
    raise ValueError(f"unsupported file extension: {extension}")


def _safe_zip_members(path: Path) -> list[zipfile.ZipInfo]:
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as exc:
        raise ValueError(f"invalid zip-based file: {path}") from exc

    with archive:
        members = archive.infolist()
        for member in members:
            name = member.filename.replace("\\", "/")
            if name.startswith("/") or "../" in name or name == "..":
                raise ValueError(f"unsafe zip member path: {member.filename}")
            if member.file_size > DEFAULT_MAX_ZIP_MEMBER_BYTES:
                raise ValueError(f"zip member is too large: {member.filename}")
        return members


def _read_zip_member(path: Path, member_name: str) -> bytes:
    _safe_zip_members(path)
    with zipfile.ZipFile(path) as archive:
        return archive.read(member_name)


def _read_docx_text(path: Path) -> str:
    data = _read_zip_member(path, "word/document.xml")
    try:
        root = ET.fromstring(data)
    except ET.ParseError as exc:
        raise ValueError("DOCX document.xml is malformed") from exc

    namespace = "{http://schemas.openxmlformats.org/wordprocessingml/2006/main}"
    paragraphs: list[str] = []
    for para in root.iter(f"{namespace}p"):
        chunks = [node.text or "" for node in para.iter(f"{namespace}t")]
        text = "".join(chunks).strip()
        if text:
            paragraphs.append(text)
    return "\n\n".join(paragraphs)


def _read_epub_text(path: Path) -> str:
    _safe_zip_members(path)
    documents: list[tuple[str, str]] = []
    with zipfile.ZipFile(path) as archive:
        for member in archive.infolist():
            name = member.filename.lower()
            if name.endswith((".xhtml", ".html", ".htm")):
                raw = archive.read(member.filename).decode("utf-8", errors="replace")
                documents.append((member.filename, _html_to_text(raw)))
    documents.sort(key=lambda item: item[0])
    return "\n\n".join(text for _, text in documents if text.strip())


class _HTMLTextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self.parts: list[str] = []

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag.lower() in {"p", "br", "div", "section", "article", "h1", "h2", "h3", "h4", "li"}:
            self.parts.append("\n")

    def handle_data(self, data: str) -> None:
        if data.strip():
            self.parts.append(data)

    def handle_endtag(self, tag: str) -> None:
        if tag.lower() in {"p", "div", "section", "article", "h1", "h2", "h3", "h4", "li"}:
            self.parts.append("\n")


def _html_to_text(html: str) -> str:
    parser = _HTMLTextExtractor()
    parser.feed(html)
    lines = [line.strip() for line in "".join(parser.parts).splitlines()]
    paragraphs = [line for line in lines if line]
    return "\n\n".join(paragraphs)
