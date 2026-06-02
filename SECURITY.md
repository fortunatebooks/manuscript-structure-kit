# Security Policy

Please report security issues privately through GitHub Security Advisories. If advisories are unavailable, contact the maintainers privately before opening a public issue.

## File handling scope

The library reads Markdown, text, DOCX, and EPUB files. DOCX and EPUB are ZIP-based formats, so the reader checks archive member paths and member sizes before extraction. Please report any bypasses or denial-of-service cases.
