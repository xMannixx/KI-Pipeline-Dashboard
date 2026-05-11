# Security Policy

## Supported Versions

Aktiv gepflegt wird jeweils der aktuelle `main`-Stand.

## Reporting a Vulnerability

Bitte **keine öffentlichen Issues** für potenzielle Sicherheitslücken erstellen.

Melde Sicherheitsprobleme vertraulich an den Maintainer über GitHub Security Advisories oder einen privaten Kontaktkanal.

Bitte mitliefern:

- betroffene Datei/Komponente
- reproduzierbare Schritte
- erwartetes vs. beobachtetes Verhalten
- mögliche Auswirkung (Datenverlust, RCE, Secret Leak, etc.)

## Expected Response

- Eingangsbestätigung: innerhalb von 3 Werktagen
- Erste technische Einschätzung: innerhalb von 7 Werktagen
- Fix- oder Mitigations-Plan: sobald reproduzierbar bewertet

## Repository Security Baseline (Settings)

Diese Schutzmechanismen sollten in den Repository-Einstellungen aktiv sein:

- Secret Scanning
- Push Protection
- Dependabot Alerts
- Dependency Graph
- Code Scanning (CodeQL)
- Branch Protection mit Required Status Checks
