# Contributing

Thanks for helping improve this open source project.

## Development setup

```bash
python -m pip install -e '.[dev]'
pytest
ruff check .
mypy src/manuscript_kit
```

## Good issues include

- A small input snippet that reproduces the problem.
- The expected output.
- The actual output.
- The command or API call you used.

Please avoid posting full copyrighted manuscripts. Minimal snippets are best.

## Pull request checklist

- Add or update tests for behavior changes.
- Keep deterministic behavior deterministic; do not add AI/provider calls to core cleanup.
- Update README examples if CLI behavior changes.
- Run `pytest`, `ruff check .`, and `mypy src/manuscript_kit` before opening a PR.
