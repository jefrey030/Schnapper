# S-001 – Bestandsaufnahme: vorhandene Bausteine und fehlende Schnittstellen

Stand: 21.10.2026, 21:31 UTC · Autor: SCHNAPPER MASTER · Status: zur Prüfung (review)
Grundlage: Branch `agent/master/20261021-21` (basiert auf `main` @ `108509e`).
Jede Zeile `datei: funktion` unten wird von `tests/test_bestandsaufnahme_s001.py` gegen den Code geprüft.

## Vorhandene Dateien und Funktionen (belegt)

### Agenten-Infrastruktur (kein App-Code für Schnäppchen)
- `team/runner.py: load_tasks` – lädt und validiert `team/tasks.json`
- `team/runner.py: choose_task` – wählt offene Aufgabe nach Priorität, rotiert zwischen Läufen
- `team/runner.py: previous_task_id` – liest die zuletzt bearbeitete Aufgabe aus `team/runs/*.json`
- `team/agent.py: lead` – LEAD-Rolle (KI-Aufruf, Aufgabenwahl)
- `team/agent.py: brain` – BRAIN-Rolle (Vorschlag nach `team/proposals/`)
- `team/agent.py: check` – CHECK-Rolle (Unit-Tests + Geheimnis-Scan schlagen KI-Urteil)
- `team/agent.py: command` – COMMAND-Rolle (Freigabe/Nicht-Freigabe)
- `team/agent.py: bericht` – Stundenbericht, überschreibt `team/STATUS.md`
- `team/agent.py: geheimnis_scan` – Mustersuche nach API-Schlüsseln/Private Keys
- `team/agent.py: tests_ausfuehren` – führt `unittest` aus
- `team/ki.py: KI` – Zugriff auf GitHub Models mit Kostenbremsen
- `team/ki.py: waehle_modell` – wählt ein erlaubtes Open-Weight-Modell
- `team/ki.py: _pruefe_url` – erlaubt nur den Host `models.github.ai`

### Konzepte
- `team/konzept/S-000-mvp-konzept.md` – MVP-Konzept (3 Funktionen, Inserat-Schema, Fehlerszenarien F1–F4)

### Automatisierung (nur gelesen, nicht geändert)
- `.github/workflows/tests.yml` – Unit-Tests
- `.github/workflows/schnapper-hourly.yml` – Stundenlauf der vier Agenten, nur bei öffentlichem Repo

### Abhängigkeiten
Nur Python-Standardbibliothek (`json`, `pathlib`, `re`, `subprocess`, `sys`, `datetime`, `os`, `urllib`).
Keine `requirements.txt`, keine Fremdpakete.

## Fehlende Bausteine und Schnittstellen

| # | Fehlt | Art | Benötigt für | Blockiert durch |
| --- | --- | --- | --- | --- |
| M1 | Inserat-Datenmodell (Schema aus S-000) als Code | App-Code | MVP-Funktion 2/3 | nichts – umsetzbar |
| M2 | Suchanfrage-Validierung | App-Code | MVP-Funktion 1 | nichts – umsetzbar |
| M3 | Quellen-Adapter-Schnittstelle + Mock-Adapter | App-Code | MVP-Funktion 2 | nichts – umsetzbar mit Testdaten |
| M4 | Filter/Entdoppeln/Veraltet-Markierung | App-Code | MVP-Funktion 3 | nichts – umsetzbar |
| M5 | Echte Marktplatz-Quelle (z. B. eBay) | externe Schnittstelle | echte Treffer | ungeklärte Nutzungsrechte, keine Zugangsdaten |
| M6 | Benutzeroberfläche (CLI oder Web) | App-Code | Bedienung | Entscheidung durch Jefrey |
| M7 | Lauffähige GitHub Actions | Betrieb | Stundenlauf, CI | Kontosperre/Billing („job was not started …“) |
| M8 | Erfolgreicher Aufruf von GitHub Models | Betrieb | echte KI-Agenten | hängt an M7 |

## Ergebnis
- Auf `main` gibt es **keinen** App-Code für Schnäppchen-Suche oder Preisvergleich; vorhanden ist nur die Agenten-Infrastruktur.
- Nachtrag 21:36 UTC: **PR #5** (`app/schnapper`, offen, nicht gemergt) deckt M1–M4 weitgehend ab.
- M1–M4 sind ohne Zugangsdaten und ohne Kosten umsetzbar.
- M5 und M7 sind externe Blocker und werden nicht durch Code gelöst.
