# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Added
- GitHub Actions CI workflow (ruff, mypy, pytest, coverage baseline gate)
- CodeQL workflow for Python
- Dependabot configuration for pip and GitHub Actions
- `CONTRIBUTING.md`, `SECURITY.md`, `docs/OPERATIONS.md`
- Pull request and issue templates

### Changed
- Central config validation with fail-fast behavior for invalid providers/paths
- Secret key handling now supports `FLASK_SECRET_KEY` for stable sessions

