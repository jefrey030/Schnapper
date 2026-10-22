## Aufgabe
**F5 = S-012 „Ein-Befehl-Start für Android/Termux“** (Lauf 20261022-2328, SCHNAPPER MASTER).

Statt `PYTHONPATH=app python -m schnapper.web …` genügt jetzt im entpackten Ordner:

```
bash start-schnapper.sh
```

## Änderungen
- **`start-schnapper.sh`** (neu, Modus 100755)
  - `#!/usr/bin/env bash` (Termux-tauglich), `set -eu`, nur bash-Builtins plus Python
  - Ermittelt das eigene Verzeichnis, funktioniert aus jedem Arbeitsverzeichnis, setzt `PYTHONPATH=<ordner>/app`
  - Python-Suche: `SCHNAPPER_PYTHON` → `python3` → `python`. Fehlt Python, kommt eine deutsche Meldung mit `pkg install python` (Exit 2). Mindestversion 3.8 wird geprüft.
  - Standarddatei `app/vorlagen/meine-angebote.csv`, optional eigene Datei als Argument (relativ zum Aufrufort). Bei fehlender Datei: „Datei nicht gefunden: …“, Exit 2, kein Start.
  - **Host fest `127.0.0.1`**, es gibt keine Möglichkeit, `0.0.0.0` zu setzen. Port über `SCHNAPPER_PORT` (Standard 8765, geprüft 1–65535).
  - Gibt die Adresse aus, startet per `exec` (Strg+C/SIGTERM kommen direkt beim Server an), ungepuffert
  - Keine Downloads, keine Installation, keine Geheimnisse
- **`docs/HANDY-START.md`:** Schritt 4 auf `bash start-schnapper.sh` umgestellt (inkl. Hinweis auf das Ausführungsbit bei ZIP-Downloads, eigene Datei, `SCHNAPPER_PORT=8800`, Beenden mit CTRL+C). Der manuelle Befehl bleibt als „Alternative ohne Skript“ erhalten, Stand 22.10.2026 (F5).
- **`README.md`:** eine Verweiszeile im Abschnitt „Web-Oberfläche“
- **`tests/test_start_skript_s012.py`** (neu, 16 Tests): echter Start per Subprocess aus fremdem cwd mit HTTP-Abruf, Datei-Argument (absolut/relativ), fehlende Datei, fehlendes Python (leerer PATH), ungültiger Port, zu viele Argumente sowie statische Prüfungen (Shebang, Ausführungsbit, `--host 127.0.0.1`, Verbotswörter, `bash -n`)

`app/` (inkl. `web.py`), `.github/`, `cloudflare/` und `team/` sind unverändert.

## Testergebnisse
- `python3 -m unittest discover -s tests`: **Ran 232 tests, OK** (216 auf main + 16 neu, 0 Fehler, 0 skipped)
- `python3 -m unittest tests.test_start_skript_s012 -v`: **16/16 OK, 0 skipped**
- `cd cloudflare && node --test test/*.test.mjs`: **tests 10, pass 10, fail 0, skipped 0**
- `bash -n start-schnapper.sh`: OK; `git ls-files -s start-schnapper.sh` → `100755`
- `shellcheck`: **nicht verfügbar** (in der Umgebung nicht installiert)
- CHECK manuell: Start aus fremdem cwd → HTTP 200; `exec` nachgewiesen (kein bash-Zwischenprozess); belegter Port → Meldung von web.py, Exit 1

## Hinweise
- **Auf echtem Gerät (Termux) ungetestet.** Geprüft wurde nur unter Linux.
- **Host fest 127.0.0.1:** Der Server ist nur auf dem Handy selbst erreichbar.
- **Abhängigkeit:** S-012 ist in **#36** als Aufgabe angelegt. Der `team/tasks.json`-Status von S-012 wird deshalb hier nicht geändert und muss nach dem Merge von #36 nachgezogen werden (→ `review`/`done`).
- **Mögliche Konflikte:** Mit #36 (docs) sind sie gering. `docs/HANDY-START.md` berührt eventuell den Abschnitt zu #15, der inhaltlich unverändert bleibt.
- Draft, nicht mergen ohne Jefreys Entscheidung.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_013twcAZiybH8Gm5Xd2oejzj
