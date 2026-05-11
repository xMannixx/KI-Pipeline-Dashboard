# Aethos Pipeline Dashboard

Lokales Web-Dashboard für den vollständigen Aethos Review- und Build-Zyklus.  
Ersetzt manuelle Dateioperationen durch eine strukturierte **5-Phasen-Pipeline** mit KI-gestützten Reviews und menschlichen Manni-Gates (Freigabe durch den Dirigenten).

---

## Inhaltsverzeichnis

1. [Rollen](#rollen)
2. [Der vollständige Workflow](#der-vollständige-workflow)
3. [Die 5 Phasen im Detail](#die-5-phasen-im-detail)
4. [Setup & Starten](#setup--starten)
5. [Konfiguration](#konfiguration-configtoml)
6. [Features & Neuerungen](#features--neuerungen)
7. [Projektstruktur](#projektstruktur)
8. [Datenpersistenz](#datenpersistenz)
9. [Transport: HTTP und HTTPS](#transport-http-und-https)
10. [Sicherheitsregel](#sicherheitsregel)
11. [Änderungsprotokoll](#änderungsprotokoll)

---

## Rollen

| Rolle | Modell | Aufgabe |
|---|---|---|
| **Dirigent (Manni)** | — | Entscheidet alles. Gibt frei, lehnt ab, steuert den gesamten Zyklus. |
| **Teamleiter** | wählbar (s. u.) | Koordiniert, schreibt Aufträge, konsolidiert Reviews, erstellt Cursor-Aufträge. Baut keinen Code. |
| **Code-Builder** | Cursor (Opus 4.6 + Sonnet 4.6) | Baut Code nach Spezifikation. Einziger der den echten Code anfasst und pytest ausführt. |
| **GPT 5.2 Thinking** | OpenAI o3 | Bug Hunter — beste Semantik-Analyse, findet logische Fehler und Grenzfälle. |
| **GPT 5.4 Thinking** | OpenAI o4-mini | Bug Hunter sekundär — schnelle, scharfe zweite Meinung. |
| **Sonnet 4.6 (Reviewer)** | Claude Sonnet 4.6 | Security, PII, Architektur — kennt den Aethos-Kontext. |
| **Gemini 3.1 Pro** | Gemini 3.1 Pro | Edge Cases / Unique Findings — findet Dinge die andere übersehen. |
| **DeepSeek R1** | DeepSeek R1 | Architektur-Trade-offs — günstig, stark bei Design-Entscheidungen. |

### Teamleiter-Modelle (wählbar pro Phase)

| Label | Modell | Anmerkung |
|---|---|---|
| Sonnet 4.6 (Anthropic) | `claude-sonnet-4-6` | Standard, schnell, Cache-fähig |
| **Opus 4.6 (Anthropic)** | `claude-opus-4-6` | Stärkste Analyse, Cache-fähig, Extended Thinking |
| GPT 5.2 / o3 (OpenAI) | `o3` | Sehr starkes Reasoning |
| GPT 5.4 / o4-mini (OpenAI) | `o4-mini` | Schnell + günstig |
| Gemini 3.1 Pro (Google) | `gemini-3.1-pro-preview` | Große Kontextfenster |
| DeepSeek R1 | `deepseek-reasoner` | KV-Cache, günstiger Preis |

---

## Der vollständige Workflow

```
┌─────────────────────────────────────────────────────────────────────────┐
│  DIRIGENT (Manni) startet einen neuen Run                               │
│  · Beschreibung der Aufgabe                                             │
│  · Optional: Code-Dateien aus Workspace-Browser laden                  │
│  · Optional: Teamleiter-Systemprompt wählen                            │
│  · Optional: Current State Sheet für alle Reviewer wählen              │
│  · Optional: Fertigen Review-Auftrag einfügen (Phase 1 überspringen)   │
└────────────────────────┬────────────────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 1 — Review-Auftrag erstellen                                     │
│  Teamleiter → strukturiertes YAML                                       │
│  Manni: prüfen → Freigeben / Ablehnen / Editieren                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ approved
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 2 — Parallel Review                                              │
│  Alle ausgewählten Reviewer starten gleichzeitig                        │
│  Jeder mit eigenem Fokus-Systemprompt + Current State Sheet             │
│  Manni: Ergebnisse prüfen → Freigeben / Ablehnen                        │
│  Optional: Ergebnisse als .md speichern / herunterladen                 │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ approved
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 3 — Konsolidierung                                               │
│  Teamleiter wertet alle Reviews aus:                                    │
│  · Konsens-Findings (alle Reviewer einig)                               │
│  · Einzigartige Findings (nur ein Reviewer)                             │
│  · Priorisierte Maßnahmen                                               │
│  Manni: prüfen → Freigeben / Ablehnen / Editieren                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ approved
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 4 — Cursor-Auftrag generieren                                    │
│  Teamleiter → strukturiertes YAML:                                      │
│  titel, aufgaben (Problem + Lösung + Dateien),                          │
│  akzeptanzkriterien, hinweise, anti-mogel-regeln                        │
│  Manni: prüfen → Freigeben / Ablehnen / Editieren                       │
└────────────────────────┬────────────────────────────────────────────────┘
                         │ approved
                         ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  PHASE 5 — Cursor-Brücke (Build)                                        │
│  Schreibt CURSOR_AUFTRAG_…yaml in den Workspace-Ordner                  │
│  Dirigent öffnet Cursor: @CURSOR_AUFTRAG_…yaml → "Implement this"       │
│  Code-Builder (Cursor) baut nach Spezifikation                          │
│  Manni: Done                                                            │
└─────────────────────────────────────────────────────────────────────────┘
```

### Manni-Gates (pro Phase)

Jede Phase endet im Status **„Warte auf Manni"** bevor die nächste starten kann:

| Aktion | Wirkung |
|---|---|
| **Freigeben** | Phase → `approved`, nächste Phase freischaltbar |
| **Ablehnen** | Phase → `rejected`, Teamleiter-Ergebnis verworfen |
| **Nochmal** | Phase wird neu gestartet (nach Ablehnung) |
| **Änderungen speichern** | Manni kann das Teamleiter-Ergebnis direkt editieren und speichern |
| **Abbrechen** | Laufende Phase sofort stoppen (wartet auf API-Response) |

**Freigabe / Speichern und Metadaten:** Wenn ein bearbeitbares Textfeld sichtbar ist (Phase 1, 3, 4), sendet der Browser nur den geänderten Text (`yaml_text`, `consolidation_text`, `task_yaml`). Das Backend **merged** diese Felder in das bestehende Phasen-Ergebnis (`app.py`: `phase_approve`, `phase_update`) — Werte wie `km_model`, `duration`, `cache_read_tokens`, `thinking_budget` gehen dabei **nicht** verloren (wichtig für Statistik und Nachvollziehbarkeit).

---

## Die 5 Phasen im Detail

### Phase 1 — Review-Auftrag erstellen

Der Teamleiter analysiert die Eingabe (Beschreibung + Code) und erstellt ein strukturiertes Review-YAML mit:
- `title`, `description`, `context`
- `acceptance_criteria`, `affected_components`
- `review_steps` (explizite Prüfpunkte für die Reviewer)
- `priority`, `due_date`

**Skip-Option:** Wenn bereits ein fertiger Review-Auftrag vorliegt (z. B. aus einem vorherigen Zyklus), kann Phase 1 übersprungen werden. Den fertigen YAML-Text einfügen und die Checkbox „Phase 1 überspringen" aktivieren — Phase 1 wird automatisch freigegeben.

### Phase 2 — Parallel Review

Alle ausgewählten Reviewer starten gleichzeitig (parallel Threads). Jeder Reviewer erhält:
- Den Review-Auftrag aus Phase 1
- Seinen spezifischen Fokus-Systemprompt
- Das **Current State Sheet** (Halluzinationskontrolle)

Vor dem Start wählbar: **Reviewer Thinking** (Effort-Stufen) und **Reviewer Temperatur** (Slider/Presets) — gelten für alle ausgewählten Reviewer; Details unter **Features & Neuerungen** (*Extended Thinking* und *Temperatur*).

Live-Fortschritt: Das Dashboard zeigt in Echtzeit welche Reviewer fertig sind.

**Ergebnisse sichern:**
- **Download (.md)** — alle Review-Ergebnisse als Markdown-Datei herunterladen
- **Auto-Save** nach `review_ergebnisse/` (fail-soft mit `auto_save_error`)
- **In Ordner speichern** — manuelles Speichern nach `review_ergebnisse/`

### Phase 3 — Konsolidierung

Der Teamleiter analysiert alle Reviewer-Ergebnisse und erstellt:
- **Konsens-Findings** — Punkte auf die sich mehrere Reviewer geeinigt haben
- **Einzigartige Findings** — Punkte die nur ein Reviewer gefunden hat
- **Priorisierte Maßnahmenliste** — nach Kritikalität sortiert

Manni kann das Ergebnis direkt im Textfeld editieren bevor er freigibt.
Die Konsolidierung wird automatisch nach `konsolidierungen/` geschrieben (optional auch manuell per Button).

### Phase 4 — Cursor-Auftrag generieren

Der Teamleiter erstellt aus der Konsolidierung einen konkreten, umsetzbaren Cursor-Auftrag als **strukturiertes YAML** mit:
- `titel`
- `aufgaben[]` — je mit `problem`, `loesung`, `betroffene_dateien`
- `akzeptanzkriterien[]`
- `hinweise`
- eingebettete **Anti-Mogel-Regeln**

### Phase 5 — Cursor-Brücke

Schreibt die YAML-Datei als `CURSOR_AUFTRAG_<titel>_<datum>.yaml` in den konfigurierten Workspace-Ordner. Danach in Cursor:

```
@CURSOR_AUFTRAG_<name>.yaml
Implement this.
```

---

## Setup & Starten

### Voraussetzungen

- **Python 3.11 oder höher** (Projekt nutzt moderne Syntax; Entwicklung u. a. mit Python 3.14)
- API Keys für: Anthropic, OpenAI, Google (Gemini), DeepSeek

### Installation

```powershell
cd <pfad-zum-repo>
copy config.example.toml config.toml
pip install -r requirements.txt
```

### Entwicklungsstandard (Quality Gates)

Standard-Tooling im Projekt:

- `ruff` (Linting)
- `mypy` (Typprüfung)
- `pytest` (Tests)
- `pydantic` (validierte Daten-/Settings-Modelle)

Installation der Dev-Tools:

```powershell
pip install -r requirements-dev.txt
```

Empfohlene Standard-Checks vor Releases:

```powershell
python -m ruff check app.py pipeline
python -m mypy app.py pipeline
python -m pytest
```

### API Keys

`.env`-Datei im Projektordner (Vorlage: `.env.example`):

```env
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-...
GOOGLE_API_KEY=...
DEEPSEEK_API_KEY=sk-...
```

Das Dashboard lädt `.env` automatisch beim Start (Datei im Projektroot).

### Session Secret (empfohlen)

Für stabile Sessions über App-Neustarts hinweg sollte zusätzlich ein fester Secret-Key gesetzt werden:

```env
FLASK_SECRET_KEY=<zufaelliger-langer-wert>
```

Ohne gesetzten `FLASK_SECRET_KEY` nutzt die App einen temporären Schlüssel pro Start (Sessions werden beim Neustart ungültig).

### Starten

**Option A** — Batch-Datei im Repo (Windows):

```
Pipeline_Dashboard_Starten.bat
```

**Option B** — Direkt:
```powershell
python app.py
```

Der Browser öffnet sich automatisch auf `http://localhost:5000`.

### Flask neu starten

Im schwarzen Konsolenfenster: `Ctrl+C` → dann `.bat` oder Desktop-Link erneut starten.  
Nach Code-Änderungen immer neu starten + Browser Hard-Refresh (`Ctrl+Shift+R`).

---

## Konfiguration (`config.toml`)

Leg bei Bedarf eine eigene `config.toml` an — Vorlage ist [`config.example.toml`](config.example.toml) (ohne eigene `config.toml` wird die Vorlage gelesen). Pfade können relativ zum Repository-Stamm oder absolut sein.

### Teamleiter (Default in `config.toml`)

```toml
[teamleiter]
provider    = "anthropic"
model       = "claude-sonnet-4-6"
temperature = 0.3
max_tokens  = 8192
system_prompt = """..."""

# Anti-Mogel-Regeln — werden IMMER angehängt (auch bei eigenem Systemprompt)
anti_mogel = """
WICHTIG — Anti-Mogel-Regeln für alle generierten Cursor-Aufträge:
- Keine hardcodierten Werte oder Lösungen die nur für spezifische Test-Inputs funktionieren
- Keine Umgehung von Tests — echte Probleme lösen, nicht Tests manipulieren
- Falls Tests falsch sind: informiere den Dirigenten statt daran vorbeizuarbeiten
- Fail-Closed-Prinzip: bei Unsicherheit ablehnen, nicht raten"""
```

Hinweis: Primaer wird jetzt **`[teamleiter]`** verwendet. Aus Kompatibilitaetsgruenden werden
**`[konzertmeister]`** und **`[[konzertmeister_choices]]`** weiterhin als Fallback gelesen.
Wenn beide vorhanden sind, gewinnt immer `teamleiter`.

Wenn du im Dashboard in Phase 1, 3 oder 4 ein anderes Modell/Provider auswaehlst, wird dieser Default
fuer den jeweiligen Start **ueberschrieben**. Nur wenn du **nichts** auswaehlst, greift der Wert aus
`config.toml`.

### Teamleiter-Modell-Auswahl

```toml
[[teamleiter_choices]]
label          = "Sonnet 4.6 (Anthropic)"
provider       = "anthropic"
model          = "claude-sonnet-4-6"
thinking_effort = "none"

[[teamleiter_choices]]
label          = "Opus 4.6 (Anthropic)"
provider       = "anthropic"
model          = "claude-opus-4-6"
thinking_effort = "none"
```

### Reviewer

```toml
[reviewer.deepseek]
provider = "deepseek"
model    = "deepseek-reasoner"
name     = "DeepSeek R1"
role     = "Architektur-Trade-offs"
system_prompt = "..."
```

### Workspace-Browser

```toml
[[workspace_roots]]
label = "Dieses Repository"
path  = "."

# Weitere Wurzeln: absolute Pfade oder relative Pfade zum Repo-Stamm, z. B.:
# path  = "../mein-anderes-projekt"

[workspace_browser]
extensions = [".py", ".md", ".yaml", ".yml", ".txt", ".ts", ".js", ".json", ".toml"]
```

### Dokumente-Ordner

```toml
[docs_dir]
path = "data/systemprompts"
```

### Anthropic Prompt-Cache (TTL)

Steuert die Lebensdauer von `cache_control: ephemeral` in [`pipeline/api_clients.py`](pipeline/api_clients.py):

```toml
[anthropic]
prompt_cache_ttl = "5m"   # "5m" | "1h"
```

- `"5m"` (Standard): typischer Write-Multiplikator ~1,25× Basis-Input.
- `"1h"`: Write ~2× Basis, Cache bleibt eine Stunde — sinnvoll bei gleichen langen Präfixen mit Pause **> 5 Minuten** zwischen Anthropic-Calls (siehe [Prompt Caching](#prompt-caching)).

---

## Features & Neuerungen

### Teamleiter-Modell pro Phase wählbar

Für jede Teamleiter-Phase (1, 3, 4) kann das Modell individuell ausgewählt werden — direkt im Phasen-Block vor dem Start. Verfügbare Modelle werden aus `config.toml` geladen.

### Extended Thinking und Effort (Teamleiter + Reviewer)

#### Teamleiter (Phasen 1, 3, 4)

Die **Thinking**-Zeile erscheint, wenn ein **Anthropic**- oder **Google (Gemini)**-Modell als Teamleiter gewählt ist. Stufen: **Kein Thinking**, **Low**, **Medium**, **High**, **Max**.

**Claude Opus 4.6** (`claude-opus-4-6`): Empfohlener API-Modus **adaptives Thinking** — `thinking.type = "adaptive"`, die Tiefe steuert der **Effort** (`low` / `medium` / `high` / `max`). Es wird kein festes `budget_tokens` mehr gesetzt (Legacy-Modus). Implementierung: [`pipeline/api_clients.py`](pipeline/api_clients.py) (`_call_anthropic`).

**Claude Sonnet 4.6** (`claude-sonnet-4-6`): Weiterhin **Extended Thinking** mit **`budget_tokens`** (Legacy), gemappt aus dem Effort:

| Effort | Budget-Tokens (ca.) | Einsatz |
|---|---|---|
| **Kein Thinking** | 0 | Standard, schnell, günstig |
| **Low** | 1.024 | Leichte Analyse |
| **Medium** | 8.000 | Ausgewogene Tiefe |
| **High** | 16.000 | Tiefe Analyse |
| **Max** | 32.000 | Maximales Budget (Sonnet) |

**Gemini (z. B. `gemini-3.1-pro-preview`):** Thinking wird über `thinkingConfig.thinkingBudget` gesteuert. **`thinkingBudget = 0` ist für Gemini 3.1 Pro ungültig** („Budget 0 is invalid“). **Kein Thinking** bedeutet hier: es wird **kein** `thinkingConfig` gesendet — das Modell nutzt sein **eigenes Minimum** (Thinking bleibt aktiv, Kosten variieren). Für begrenztes Thinking **Low/Medium/High/Max** wählen.

Bei aktivem Anthropic-Thinking wird `temperature` auf **1** gesetzt (API-Vorgabe).

#### Phase 2 — Reviewer Thinking

Vor **„Alle Reviewer starten“** gibt es eine eigene Zeile **Reviewer Thinking** mit denselben Stufen (inkl. **Max**). Der gewählte Effekt gilt für **alle** gestarteten Reviewer; Provider ohne steuerbares Thinking ignorieren den Parameter.

Verbrauchte **Thought-/Thinking-Tokens** (z. B. Gemini `thoughtsTokenCount`) werden pro Reviewer als Badge angezeigt; die **Statistik** summiert Thinking aus **Teamleiter-Phasen** und **Reviewer-Ergebnissen** (`thinking_budget`).

### Temperatur (UI)

Für **Teamleiter** (jede TL-Phase) und **Reviewer** (Phase 2) gibt es einen **Slider** (0,0–1,5, Schritt 0,1) und Presets **0,0** / **0,2** / **0,5** / **1,0**:

- **0,0** — empfohlen für Programmierung/Mathematik (u. a. DeepSeek-Dokumentation).
- **0,2** — Standard für strukturierte Reviews.
- Höhere Werte — eher für Analyse, Brainstorming, kreativere Formulierung.

Der Wert wird mit dem Phasen-Start an das Backend übergeben und überschreibt die jeweilige `temperature` aus `config.toml` für diesen Lauf.

**Hinweis:** OpenAI-**Reasoning**-Modelle (`o3`, `o4-mini`, …) akzeptieren oft **kein** `temperature` — das Backend lässt den Parameter dann weg (unverändertes API-Verhalten).

### Prompt Caching

Automatisch aktiv für alle unterstützten Provider:

| Provider | Caching-Methode | Ersparnis |
|---|---|---|
| **Anthropic** | `cache_control: ephemeral` (System + User-Block) | Cache-Read ~10 % des Basis-Input-Preises |
| **OpenAI** | Automatisch (server-side) | automatisch |
| **DeepSeek** | KV-Cache (Cache-Hit ~0,028 $/MTok vs. Miss ~0,28 $/MTok) | automatisch |
| **Google** | Implizites Prefix-Caching (modellabhängig) | — |

**Anthropic — TTL (5 Min vs. 1 Std):** In `config.toml` unter `[anthropic]`:

- `prompt_cache_ttl = "5m"` (Standard): Schreib ~1,25× Basis-Input — typisch für parallele Reviewer, die innerhalb weniger Minuten dieselben Präfixe nutzen.
- `prompt_cache_ttl = "1h"`: Schreib ~2× Basis, Cache bleibt eine Stunde — sinnvoll, wenn **dieselben** statischen Präfixe (z. B. Teamleiter-Systemprompt + State Sheet) mit **Pause > 5 Minuten** erneut an Anthropic gehen (z. B. Phase 1 und später Phase 3 mit demselben Modell).

Mindestlänge zum Cachen: u. a. ~1024 Tokens (Sonnet 4.6), ~4096 Tokens (Opus 4.6). **Tool-Definitionen** oder **Thinking-Parameter** zwischen Calls ändern → Messages-Cache kann invalidiert werden; stabile Systemprompte + gleiche Reviewer-Einstellungen helfen.

Cache-Read und Cache-Write Tokens werden pro Phase als Badge angezeigt; die Statistik aggregiert sie über alle Runs.

### Anti-Mogel-Regeln (unveränderlich)

Die Anti-Mogel-Regeln sind in `config.toml` unter `anti_mogel` definiert und werden **immer** an den Teamleiter-Systemprompt angehängt — unabhängig davon ob ein eigener Systemprompt geladen wurde. Sie sind nicht überschreibbar.

**Inhalt:**
- Keine hardcodierten Werte die nur für spezifische Test-Inputs funktionieren
- Keine Umgehung von Tests — echte Probleme lösen
- Bei falschen Tests: Dirigenten informieren statt drumherum arbeiten
- Fail-Closed: bei Unsicherheit ablehnen, nicht raten

### XML-strukturierte Prompts

Alle Teamleiter-Prompt-Templates nutzen XML-Tags für bessere Strukturierung:

```xml
<instructions>...</instructions>
<context>...</context>
<code>...</code>
```

Verbessert die Qualität der Teamleiter-Ausgaben und reduziert Halluzinationen.

### Workspace-Browser

Code-Dateien aus dem Aethos-Projekt direkt in den Run-Auftrag laden — ohne manuelles Kopieren:

1. Im „Neuer Run"-Dialog: **„Code aus Workspace laden"** klicken
2. Workspace-Root wählen (Aethos Module, Pipeline Dashboard, weitere V4-Ordner, etc.)
3. Dateien auswählen (Checkboxen), mehrstufige Ordner-Navigation
4. **„Auswahl laden"** — Inhalt wird automatisch in das Eingabefeld eingefügt

Unterstützte Dateitypen: `.py`, `.md`, `.yaml`, `.yml`, `.txt`, `.ts`, `.js`, `.json`, `.toml`

### Eigener Teamleiter-Systemprompt

Pro Run kann ein eigener Systemprompt für den Teamleiter geladen werden:
- Direkt eingeben oder aus dem `systemprompts`-Ordner per Datei-Picker laden
- Ersetzt den Standard-Systemprompt aus `config.toml`
- Die **Anti-Mogel-Regeln werden trotzdem immer angehängt**

### Current State Sheet (alle Reviewer)

Ein „Current State Sheet" kann pro Run als Kontext für alle Reviewer mitgegeben werden:
- Halluzinationskontrolle: aktueller Projektzustand, Architektur-Übersicht
- Aus dem `current_state_sheet`-Ordner per Datei-Picker laden
- Wird jedem Reviewer-Prompt vorangestellt

### Phase 1 überspringen

Wenn ein fertiger Review-Auftrag vorliegt:
1. Checkbox **„Review-Auftrag bereits fertig → Phase 1 überspringen"** aktivieren
2. YAML-Inhalt in das Eingabefeld einfügen
3. Run starten — Phase 1 wird automatisch mit `[Auto-approved: Phase 1 übersprungen]` freigegeben
4. Direkt mit Phase 2 weitermachen

### Phase-Reihenfolge erzwungen

Eine Phase kann nur gestartet werden wenn **alle vorherigen Phasen freigegeben** (`approved`) sind. Sowohl Frontend (sofortige Toast-Meldung) als auch Backend (400-Fehler) prüfen dies.

### Phase 2 — Ergebnisse sichern

Review-Ergebnisse aus Phase 2 werden automatisch gesichert:
- **Auto-Save** nach `review_ergebnisse/` sobald Phase 2 auf `review` geht
- Fehler beim Auto-Save brechen die Phase nicht ab; sie werden als `auto_save_error` im Ergebnis vermerkt

Zusätzlich manuell:
- **Download (.md)** — direkt als Datei herunterladen
- **In Ordner speichern** — schreibt nach `review_ergebnisse/<run_title>_<run_id>_<datum>.md`

### Phase 3 — Konsolidierung sichern

Die Konsolidierung aus Phase 3 wird ebenfalls automatisch gesichert:
- **Auto-Save** nach `konsolidierungen/`
- Optionaler manueller Save-Button im Run-View

### Token-Report (.yaml)

Für Token-/Cache-Transparenz wird ein YAML-Report erzeugt:
- **Automatisch** beim Abschluss eines Runs (nach finaler Freigabe)
- **Manuell** über den Button in Phase 5 (falls du einen Report erneut schreiben willst)
- Zielordner: `token_reports/`

### YAML-Ausgabe für Cursor-Aufträge (Phase 4 + 5)

Phase 4 generiert und Phase 5 speichert den Cursor-Auftrag als **strukturiertes YAML** (`.yaml`) statt Markdown:
- Maschinenlesbar und strukturiert
- Markdown-Code-Fences werden automatisch entfernt
- Dateiname: `CURSOR_AUFTRAG_<titel>_<datum>.yaml`

### Run-Verwaltung

- **Stoppen** — laufende Phasen abbrechen, Run bleibt erhalten
- **Löschen** — Run dauerhaft entfernen (inkl. Sync-Konflikt-Kopien)
- Gelöschte / gestoppte Runs verschwinden aus der Dashboard-Liste

### Statistik-Panel (Hauptseite)

Kompakte Übersichtsleiste immer sichtbar, aufklappbare Details:

**Kompakt-Leiste:**
- Runs gesamt / Abgeschlossen / Cache-Hits / Thinking-Tokens / Ø Run-Dauer

**Thinking-Tokens (Gesamt):** Summe aus **Teamleiter-Phasen** (1, 3, 4; Feld `thinking_budget` im Phasen-Ergebnis) **und** **Phase-2-Reviewer** (pro Reviewer gespeichertes `thinking_budget`, z. B. Gemini *thought* tokens). Ohne Anthropic/Gemini-Thinking kann der Wert **0** sein.

**Detail-Ansicht (aufklappbar):**

| Sektion | Inhalt |
|---|---|
| Cache-Nutzung pro KI | Read-Tokens, Write-Tokens, Aufrufe, Ersparnis-Schätzung (in $) |
| Token-Übersicht | Cache-Read/Write gesamt, Thinking gesamt (Teamleiter + Reviewer) |
| Teamleiter-Modell-Nutzung | Balkendiagramm: welches Modell wie oft verwendet |
| Reviewer-Nutzung | Balkendiagramm: welcher Reviewer wie oft aufgerufen |
| Phasen-Qualität | Approve/Reject-Zahl, Approve-Rate (farbig), Ø Dauer pro Phase |
| Run-Übersicht | Gesamt / Abgeschlossen / Laufend / In Review / Abgebrochen / Ø Dauer |

Aktualisiert sich automatisch alle 30 Sekunden.

### Sicherheits-Header

Das Dashboard setzt HTTP-Header die Browser-Plugins (Wappalyzer, MaxAI, etc.) daran hindern, Inhalte zu scannen oder zu injizieren:

```
X-Content-Type-Options: nosniff
X-Frame-Options: SAMEORIGIN
Permissions-Policy: interest-cohort=()
X-Robots-Tag: noindex, nofollow
Cache-Control: no-store  (für alle /api/-Routen)
```

### Adaptives Polling

Das Dashboard pollt den Server für Live-Updates:
- **2 Sekunden** — wenn eine Phase aktiv läuft
- **8 Sekunden** — wenn kein Run aktiv ist (spart Ressourcen und reduziert Extension-Aktivität)

---

## Projektstruktur

```
pipeline-dashboard/
├── app.py                      # Flask-App, Routes, /api/stats, Auto-Save (P2/P3), Token-Reports (.yaml)
├── config.example.toml         # Vorlage (versioniert); ohne config.toml wird diese geladen
├── config.toml                 # optional: lokale Überschreibung (nicht versioniert)
├── requirements.txt
├── .env                        # API Keys (nicht im Repo)
├── .env.example                # Vorlage
├── Pipeline_Dashboard_Starten.bat
│
├── pipeline/
│   ├── api_clients.py          # LLM-Dispatcher: Google, Anthropic, OpenAI, DeepSeek
│   │                           # Anthropic: Opus adaptive / Sonnet budget_tokens, Cache-TTL
│   ├── konzertmeister.py       # Teamleiter-Logik Phase 1, 3, 4 — XML-Prompts, Anti-Mogel, _fmt helper
│   ├── reviewer.py             # Phase 2 — parallele Threads, Current State Sheet
│   ├── cursor_bridge.py        # Phase 5 — YAML-Datei schreiben
│   ├── state_machine.py        # FSM, JSON-Persistenz, Audit-Log, load_run_file
│   └── models.py               # PipelineRun / Phase Datenklassen
│
├── templates/
│   ├── base.html
│   ├── index.html              # Dashboard: Run-Liste + Statistik-Panel
│   ├── run.html                # Einzelner Run: Phasen, Reviewer-Thinking, Reviewer-Temp
│   └── _km_selector.html       # Teamleiter: Modell, Thinking, Temperatur-Slider (Partial)
│
├── static/
│   ├── app.js                  # Polling, Manni-Gates, Stats, Phase-Validierung
│   └── style.css               # Dark Theme
│
└── data/                       # Laufzeit-Daten (nicht im Repo)
    ├── <run_id>.json           # Ein JSON pro Run
    ├── audit.jsonl             # Aktives Audit-Log
    └── audit.jsonl.1..10       # Rotierte Audit-Logs (10 x 10 MB)
```

---

## Datenpersistenz

Jeder Run wird als einzelne JSON-Datei unter `data/<run_id>.json` gespeichert.  
Alle Phasen-Ergebnisse, Status-Übergänge und Metadaten (Tokens, Dauer, Modell) sind darin enthalten.

Ein Audit-Log in `data/audit.jsonl` protokolliert alle Aktionen (Run erstellt, Phase gestartet, freigegeben, abgelehnt, etc.) mit Zeitstempel.
Ab 10 MB rotiert die Datei automatisch unter demselben Lock nach `audit.jsonl.1` bis `audit.jsonl.10`.

OneDrive/Nextcloud-Sync-Konflikte werden automatisch erkannt und bereinigt.

---

## Transport: HTTP und HTTPS

| Verbindung | Protokoll | Kurz erklärt |
|---|---|---|
| **Browser → Flask** (`http://localhost:5000`) | **HTTP** (ohne TLS) | Nur auf deinem Rechner (Loopback). Typisch für lokale Entwicklung. |
| **Flask → KI-Anbieter** | **HTTPS** | `api.anthropic.com`, `api.openai.com`, `generativelanguage.googleapis.com`, `api.deepseek.com` — API-Keys und Payloads gehen verschlüsselt übers Internet. |

Wenn du die **Weboberfläche** selbst per TLS erreichbar machen willst (z. B. Zugriff von anderen Geräten im LAN), brauchst du einen Reverse-Proxy mit Zertifikat oder Flask mit SSL — für reines `localhost` ist das optional.

---

## Sicherheitsregel

> Passe in deiner lokalen `config.toml` an, welche Verzeichnisse das **Original** (z. B. für Cursor) und welche die **Arbeitskopie** für Reviews sind — und halte getrennte Pfade ein, falls du so arbeitest.

Weitere Leitfäden:

- [`CONTRIBUTING.md`](CONTRIBUTING.md)
- [`SECURITY.md`](SECURITY.md)
- [`docs/OPERATIONS.md`](docs/OPERATIONS.md)

---

## Änderungsprotokoll

**Stand 2026-05-11** (öffentliches Repo — Vorbereitung):

- **`config.example.toml`:** Neutrale Pfad-Vorlage; relative Pfade zum Repo-Stamm.
- **`config.toml`:** Für lokale Overrides vorgesehen, per `.gitignore` vom Commit ausgeschlossen.
- **Pfad-Auflösung:** `pipeline/config_alias.py` — `dashboard_config_path()`, `resolve_project_path()`; keine Benutzer-Pfade mehr im Quelltext.
- **`.env`:** Nur noch die `.env` im Projektroot wird automatisch geladen.

**Stand 2026-03-29**:

- **DH-1 Alias-Migration:** Primär-Keys `[teamleiter]` + `[[teamleiter_choices]]`; Legacy-Keys `[konzertmeister]` + `[[konzertmeister_choices]]` bleiben als Fallback. Wenn beide vorhanden sind, gewinnt `teamleiter`.
- **Deprecation-Warnung:** Bei Legacy-only Config wird einmal pro App-Start eine Warnung geloggt.
- **API-Kompatibilität:** Modell-Endpoint ist unter `/api/konzertmeister_models` **und** `/api/teamleiter_models` erreichbar.
- **DH-2 Audit-Rotation:** `data/audit.jsonl` rotiert größenbasiert mit Lock (`10 x 10 MB`), atomare Rename-Reihenfolge, Doku und `.gitignore` angepasst.
- **Auto-Save Phase 2:** Ergebnisse werden automatisch nach `review_ergebnisse/` geschrieben; Fehler sind fail-soft als `auto_save_error`.
- **Auto-Save Phase 3:** Konsolidierung wird automatisch nach `konsolidierungen/` geschrieben; ebenfalls fail-soft.
- **Token-Report YAML:** Wird bei Run-Abschluss automatisch erzeugt und kann zusätzlich manuell via `/api/run/<run_id>/token_report` erstellt werden. Zielordner: `token_reports/`.
- **Requirements:** `pyyaml` zu Runtime- und Dev-Dependencies ergänzt.
- **Tests erweitert:** Zusätzliche Tests für Alias-/Rotation und Reporting/Auto-Save.

**Stand 2026-03-21** (Auszug — Dokumentation und zugehörige Funktionen):

- **Claude Opus 4.6:** Adaptives Thinking (`type: "adaptive"`) + Effort `low`–`max`; Sonnet 4.6 weiterhin `budget_tokens` inkl. Stufe **Max** (~32k).
- **Thinking-UI:** Teamleiter für Anthropic und Gemini; Phase 2 **Reviewer Thinking**; Statistik summiert Thinking aus TL + Reviewern.
- **Gemini 3.1 Pro:** Kein `thinkingBudget: 0`; „Kein Thinking“ = kein `thinkingConfig` (Modell-Minimum).
- **Temperatur:** Slider + Presets für Teamleiter und Reviewer; überschreibt `config.toml` pro Start.
- **Anthropic Cache:** `[anthropic] prompt_cache_ttl = "5m" | "1h"` in `config.toml`.
- **Freigabe:** Merge von editiertem Text mit bestehendem Phasen-Ergebnis — Metadaten (`km_model`, Cache, Dauer, …) bleiben erhalten.
- **README:** Transport (HTTP vs. HTTPS), Preis-/Caching-Hinweise, Projektstruktur und ToC aktualisiert.
