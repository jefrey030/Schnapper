# CHECK – Lauf 20261022-2328: F5 (S-012) Ein-Befehl-Start

## Urteil: **bestanden**

Branch `agent/master/20261022-23`, genau 1 Commit `a584774` („SCHNAPPER MASTER: F5 (S-012) Ein-Befehl-Start für Android/Termux (start-schnapper.sh)“) auf origin/main. Nicht gepusht, also kein PR.

## Diff
`git diff --stat origin/main...`: README.md +1, docs/HANDY-START.md +22/-5, start-schnapper.sh +99 (neu), tests/test_start_skript_s012.py +207 (neu). Das sind nur erlaubte Dateien.
`git diff origin/main -- app/ .github/ cloudflare/ team/ | wc -c` → `0`. web.py ist unverändert.

## Tests (selbst ausgeführt)
- `python3 -m unittest discover -s tests` → `Ran 232 tests … OK` (0 Fehler, 0 skipped). Basis main per Worktree: `Ran 216 tests … OK`, also 216 + 16.
- `python3 -m unittest tests.test_start_skript_s012 -v` → `Ran 16 tests … OK`, 0 skipped
- `cd cloudflare && node --test test/*.test.mjs` → tests 10, pass 10, fail 0, skipped 0
- `bash -n start-schnapper.sh` → Exit 0
- `git ls-files -s start-schnapper.sh` → `100755 09f98f2b… 0 start-schnapper.sh`
- shellcheck: nicht verfügbar

## Manuelle Prüfung
- Aus fremdem cwd (scratchpad/fremd) mit `SCHNAPPER_PORT=8817 /home/claude/schnapper/start-schnapper.sh`: curl → `HTTP 200`, HTML enthält `SCHNAPPER`. Ausgabe:
  `SCHNAPPER startet: http://127.0.0.1:8817 – in Chrome öffnen. Beenden: Strg+C` / `Datei: …/app/vorlagen/meine-angebote.csv` / `SCHNAPPER läuft: http://127.0.0.1:8817  (Beenden: Strg+C)`
- `exec` ist nachgewiesen: Der Prozess ist `python3 -u -m schnapper.web … --host 127.0.0.1 --port 8817`, dessen PPID ist die aufrufende Shell (kein bash-Zwischenprozess). Nach `kill -TERM` ist kein python- und kein bash-Rest mehr vorhanden.
- `/gibt/es/nicht.csv` → `Datei nicht gefunden: /gibt/es/nicht.csv`, exit=2
- Verzeichnis `/tmp` als Datei → `Datei nicht gefunden: /tmp`, exit=2
- `SCHNAPPER_PORT=abc` / `70000` → `Ungültiger Port in SCHNAPPER_PORT: …`, exit=2
- `env -i PATH= /bin/bash start-schnapper.sh` → `Python wurde nicht gefunden … pkg install python`, exit=2 (ebenso mit PATH auf ein leeres Verzeichnis)
- Simuliertes altes Python (python3, das mit 1 endet) → `Python ist zu alt …`, exit=2
- `SCHNAPPER_PYTHON=/nope` → klare Meldung, exit=2
- Zwei Argumente → `Zu viele Argumente…`, exit=2
- Port belegt → `Start fehlgeschlagen: [Errno 98] Address already in use`, exit=1 (Meldung von web.py)

## Sicherheit / Tabu
- Secret-Scan auf dem Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, token, secret): Der einzige Treffer ist eine unveränderte README-Kontextzeile („ohne Passwort“). Es gibt keine Secrets.
- ZENTNA/JERRY AL/Beatmaster: keine Treffer. Im Skript gibt es kein curl/wget/pip/apt/npm/git, und `pkg install python` steht nur in printf-Meldungen.
- „auf echtem Gerät ungetestet“ steht in Skriptkopf (Z. 4) und in docs/HANDY-START.md (Z. 3).

## Akzeptanzkriterien
1. erfüllt: 100755 im Index, Test os.access X_OK
2. erfüllt: `#!/usr/bin/env bash`, `set -eu`, bash -n ok, nur Builtins (Lauf mit `PATH=` erreicht die Python-Prüfung)
3. erfüllt: `${BASH_SOURCE[0]%/*}` + `cd`/`pwd`, PYTHONPATH=<dir>/app (vorhandener PYTHONPATH wird angehängt), Start aus fremdem cwd belegt
4. erfüllt: SCHNAPPER_PYTHON → python3 → python per `command -v`, Meldung mit „Python“ + „pkg install python“, Exit 2, Prüfung auf 3.8 (simuliert)
5. erfüllt: Standarddatei, relativ zum Aufrufort (Test + Code `$AUFRUF_DIR/$1`), `-f`-Prüfung, Exit 2, zu viele Argumente → Fehler, im Kopf dokumentiert
6. erfüllt: `--host 127.0.0.1` fest, kein 0.0.0.0 im Skript, Port 1–65535 geprüft, belegter Port über web.py (Exit 1)
7. erfüllt: Startzeile + Datei, PYTHONUNBUFFERED=1 und `-u`
8. erfüllt: `exec`, Exit-Code durchgereicht (1 bei belegtem Port, 0 bei SIGINT im Test)
9. erfüllt (statischer Test + grep)
10. erfüllt
11. erfüllt: Schritt 4 auf `bash start-schnapper.sh` umgestellt, chmod-Hinweis, eigene Datei, SCHNAPPER_PORT=8800, CTRL+C, Alternative ohne Skript erhalten, `pkg install python unzip` unverändert, Abschnitt „Grenzen“/PR #15 unberührt, Stand 22.10.2026 (F5)
12. erfüllt: a–i abgedeckt (Starttest mit freiem Port, cwd=tempdir, HTTP-Polling 15 s, SIGINT → terminate → kill im Cleanup, stdout mit Adresse; b/c/d/e/f/g vorhanden; skipUnless(bash); 0 skipped; nur tempfile, keine Restprozesse, Arbeitsbaum danach sauber)
13. erfüllt: 232/232, Cloudflare 10/10
14. erfüllt: genau eine README-Zeile im Abschnitt Web-Oberfläche

## BRAINs Abweichungen
Alle Abweichungen liegen im erlaubten Rahmen: Exit 2 wurde empfohlen, die Fehlermeldung bei Zusatzargumenten ist erlaubt, Beenden per SIGINT ist erlaubt, und das Entfernen von SCHNAPPER_* aus der Test-Umgebung macht die Tests robuster. Die Doku-Satzanpassung ist sachlich nötig. Dass kein Draft-PR existiert, ist laut BRAIN gewollt, weil der Auftrag „nicht pushen“ verlangt. Der Draft-PR muss deshalb beim Push nachgeholt werden, mit den PR-Inhalten aus lead.md. BRAINs Aussage, SIGINT an einen &-Job einer nicht-interaktiven Shell werde ignoriert, ist plausibel. Ich habe stattdessen mit SIGTERM beendet, und es blieb kein Rest.

## Anmerkungen (kein Mangel)
- Die Meldung bei ungültigem SCHNAPPER_PYTHON nennt kein `pkg install python`. Das ist zulässig, weil es ein expliziter Benutzerwunsch ist.
- Das Verhalten auf einem echten Android-/Termux-Gerät ist weiterhin ungetestet, wie dokumentiert.
