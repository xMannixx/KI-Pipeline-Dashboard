# Contributing

Danke fürs Mitwirken am KI Pipeline Dashboard.

## Setup

```bash
python -m pip install -r requirements.txt
python -m pip install -r requirements-dev.txt
```

Lokale Konfiguration:

1. `config.example.toml` nach `config.toml` kopieren
2. `.env.example` nach `.env` kopieren und API-Keys setzen

## Lokale Quality Gates

Vor jedem PR bitte ausführen:

```bash
python -m ruff check app.py pipeline tests
python -m mypy app.py pipeline
python -m pytest --cov=app --cov=pipeline --cov-report=term --cov-fail-under=25
```

## Pull Requests

- Kleine, fokussierte PRs mit klarer Beschreibung.
- Mindestens 1 Review.
- CI muss grün sein.
- Bei Security-relevanten Änderungen bitte zusätzlich einen Hinweis im PR-Text geben.

## Branch-Schutz (Repository Settings)

Empfohlen in GitHub Settings:

- Require a pull request before merging
- Require at least 1 approving review
- Dismiss stale pull request approvals when new commits are pushed
- Require status checks to pass before merging (`CI`, `CodeQL`)

## Changelog

- Nutzerrelevante Änderungen im Abschnitt `Unreleased` in `CHANGELOG.md` erfassen.
