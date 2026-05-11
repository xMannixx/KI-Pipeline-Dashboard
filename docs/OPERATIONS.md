# Operations Runbook

## Datenstruktur

Laufzeitdaten liegen unter `data/`:

- `<run_id>.json` pro Run
- `audit.jsonl` + `audit.jsonl.1..10` (Rotation)
- `review_ergebnisse/`, `konsolidierungen/`, `token_reports/` (je nach Konfiguration)

## Backup

Regelmäßig sichern:

- `data/*.json`
- `data/audit.jsonl*`
- optionale Unterordner mit Reports
- `config.toml` (lokal, nicht versioniert)

Empfehlung:

- tägliches inkrementelles Backup
- mindestens 7 Tage Aufbewahrung

## Restore

1. App stoppen
2. `data/` und `config.toml` aus Backup wiederherstellen
3. App starten und Runs im Dashboard prüfen

## Audit-Log Handling

- Audit-Rotation ist aktiv (mehrere Backups)
- Logs regelmäßig archivieren
- Beim Teilen/Export personenbezogene Inhalte und Secrets entfernen

## Security-Betrieb

- `FLASK_SECRET_KEY` in der Laufzeitumgebung setzen, damit Sessions über Neustarts stabil bleiben
- Secret-Leaks umgehend rotieren (API-Keys neu erzeugen)
- Dependabot- und CodeQL-Alerts regelmäßig triagieren
