# Contributing to n8n-factory

## Setup
1. Clone repo
2. `pip install -e .`
3. `pip install -r requirements-dev.txt` (if exists, or `pytest rich ...`)

## Development
- **Code Style:** Follow PEP8. Use `black` or `ruff`.
- **Tests:** Run `pytest tests/`. Ensure 100% coverage for new features.
- **Templates:** Add new templates to `templates/`. Run `python scripts/generate_docs.py`.

## Pull Requests
- Create feature branch.
- Add tests.
- Update CHANGELOG.md.
