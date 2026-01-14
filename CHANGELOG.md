# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Python package structure (`src/markpact/`)
- CLI entry point `markpact`
- Makefile for development automation

## [0.1.0] - 2026-01-14

### Added
- Initial release
- `markpact:bootstrap` – embedded Python runtime in README
- `markpact:file` – file creation in sandbox
- `markpact:deps python` – Python dependency management with venv
- `markpact:run` – command execution in sandbox
- Environment variables:
  - `MARKPACT_SANDBOX` – custom sandbox directory
  - `MARKPACT_NO_VENV` – disable venv creation
  - `MARKPACT_PORT` – configurable port for examples
- Safe `sed` extraction command (handles ``` in regex)
- FastAPI example application

### Fixed
- Bootstrap extraction with `sed` no longer breaks on ``` inside code

[Unreleased]: https://github.com/wronai/markpact/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/wronai/markpact/releases/tag/v0.1.0
