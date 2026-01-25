# Changelog

## [Unreleased]
- Added `login` command to setup `.env`.
- Added `stats` command for workflow metrics.
- Added `--env` flag to load environment-specific configurations.
- Added HTML report generation for simulation (`--export-html`).
- Added support for `notes`, `disabled`, and `retry` in Recipe steps.
- Added `read_file` helper for Jinja2 templates.
- Added external mock data support (`mock: "file:..."`).
- Improved Auto-Layout engine (Y-axis centering).
- Added `execute_workflow`, `split_in_batches`, `filter`, `s3` templates.
- Implemented secret masking in build logs.

## [1.2.0]
- Added Auto-Layout engine.
- Added `publish`, `diff`, `validate` commands.
- Added `globals` and `imports` to Recipe.
- Added `slack`, `gmail`, `google_sheets` templates.

## [1.1.0]
- Added `init`, `visualize`, `watch`, `inspect` commands.
- Added cycle and orphan node detection.
- Added Rich logging and interactive wizard.

## [1.0.0]
- Initial release.
- Core assembler, optimizer, simulator.
- Basic templates: webhook, code, http_request, set.
