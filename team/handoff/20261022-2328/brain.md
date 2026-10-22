# BRAIN – Lauf 20261022-2328: F5 (S-012) Ein-Befehl-Start

## Branch / Commit
- Branch `agent/master/20261022-23`, neu von `origin/main` @ 6dbe114 (nicht gepusht, kein PR)
- Commit (genau einer): `a58477494f87ef513879c13734e72dc92a659b9d`
  Nachricht: `SCHNAPPER MASTER: F5 (S-012) Ein-Befehl-Start für Android/Termux (start-schnapper.sh)` plus Co-Authored-By/Claude-Session-Zeilen

## Geänderte Dateien (git diff --numstat origin/main)
| Datei | + | - | Zeilen gesamt |
|---|---|---|---|
| start-schnapper.sh (neu, Index-Modus 100755) | 99 | 0 | 99 |
| tests/test_start_skript_s012.py (neu) | 207 | 0 | 207 |
| docs/HANDY-START.md | 22 | 5 | 61 |
| README.md (eine Zeile in „Web-Oberfläche“) | 1 | 0 | 149 |

`git diff origin/main -- app/ .github/ cloudflare/ team/` ist leer. web.py ist unverändert.

## Testergebnisse (eigene Läufe)
- `bash -n start-schnapper.sh`: OK (Exit 0)
- `git ls-files -s start-schnapper.sh`: `100755 09f98f2b… 0 start-schnapper.sh`
- `python3 -m unittest tests.test_start_skript_s012 -v`: **16 Tests, OK, 0 skipped**
- `python3 -m unittest discover -s tests`: **232 Tests, OK** (216 vorher + 16 neu, 0 Fehler, 0 skipped)
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass, 0 fail**
- `shellcheck`: nicht verfügbar (nicht installiert)
- Manuell: `cd /tmp && SCHNAPPER_PORT=8799 /home/claude/schnapper/start-schnapper.sh` → Ausgabe „SCHNAPPER startet: http://127.0.0.1:8799 …“, „Datei: …/app/vorlagen/meine-angebote.csv“, „SCHNAPPER läuft: http://127.0.0.1:8799“; `curl` auf localhost lieferte `<!doctype html>`. Danach beendet, kein Restprozess.
  Hinweis: `kill -INT` auf einen Hintergrundjob einer nicht-interaktiven Shell wirkt nicht (die Shell ignoriert SIGINT für `&`-Jobs). Das ist ein Verhalten der Test-Shell und kein Skriptfehler. Im Unittest mit Popen kommt SIGINT an (Exit 0).

## Umsetzung der AK (Kurz)
1. Datei ausführbar, Modus 100755. 2. Shebang `#!/usr/bin/env bash`, `set -eu`, nur Builtins plus Python. 3. Verzeichnis über `${BASH_SOURCE[0]%/*}` + `cd`/`pwd`, PYTHONPATH=<dir>/app (vorhandener wird angehängt). 4. `SCHNAPPER_PYTHON` → `python3` → `python`; Meldung mit „Python“ und „pkg install python“, Exit 2; Prüfung auf Version 3.8. 5. Standarddatei meine-angebote.csv, Argument relativ zum Aufrufort, `-f`-Prüfung „Datei nicht gefunden: …“, Exit 2; mehr als ein Argument führt zu „Zu viele Argumente“ und Exit 2 (im Kopf dokumentiert). 6. `--host 127.0.0.1` fest, SCHNAPPER_PORT 1–65535 (nur Ziffern, max. 5 Stellen, `10#`-Normierung), sonst Exit 2. 7. Startzeile mit Adresse + Datei, `PYTHONUNBUFFERED=1` und `-u`. 8. `exec`. 9. Keine Downloads usw. (statisch getestet). 10. „auf echtem Gerät ungetestet“ steht in Skript und Doku. 11. Doku Schritt 4 umgestellt, PR-#15-Abschnitt unverändert, Stand 22.10.2026 (F5). 12. Tests a–i abgedeckt. Zusätzlich gibt es Tests für einen relativen Pfad zum Aufrufort und für zu viele Argumente. 13. Regression grün. 14. Ein README-Verweis.

## Abweichungen von lead.md (begründet)
- Exit-Code bei allen Skript-Fehlern ist 2 (laut Empfehlung). Bei zu vielen Argumenten gibt es eine Fehlermeldung statt Ignorieren (beides ist erlaubt).
- Der Starttest beendet per SIGINT (ein erlaubter Weg). Fallback ist terminate, im Cleanup kill.
- Der Test entfernt `SCHNAPPER_PORT`/`SCHNAPPER_PYTHON` aus der geerbten Umgebung, damit er nicht von außen beeinflusst wird.
- In der Doku wurde der Satz „Für deine eigene Liste statt der Beispieldaten in Schritt 4 …“ angepasst. Der Grund: Schritt 4 startet jetzt standardmäßig mit meine-angebote.csv. Sonst gibt es keine Abweichungen.
- Ein Draft-PR wurde nicht erstellt (der Auftrag verlangt ausdrücklich „NICHT pushen“).
