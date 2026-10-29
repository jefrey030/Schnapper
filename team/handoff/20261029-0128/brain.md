# BRAIN – Lauf 20261029-0128

- Start (UTC): Thu Oct 29 01:32:08 UTC 2026
- Ende (UTC): Thu Oct 29 01:32:55 UTC 2026 (laut `date -u`)
- Worktree: `/home/claude/wt-brain`, Branch `agent/master/20261022-23`
- Commit: **`b03b9868af91ab96707bec95473a38bb8f658aab`**, Parent `41e801c3ca4f89e94e6d1766b42f4cbc53f5e233` (direkt auf dem Ausgangskopf). **Nicht gepusht.**

## Geänderte Dateien (`git diff --stat 41e801c..HEAD`)
| Datei | + | − |
|---|---|---|
| `start-schnapper.sh` | 7 | 0 |
| `tests/test_start_skript_s012.py` | 27 | 5 |
| gesamt | 34 | 5 |

`docs/HANDY-START.md` nicht geändert. Modus `start-schnapper.sh` bleibt 100755.

## Umsetzung
- `start-schnapper.sh`: nach der Python-Suche und vor der Versionsprüfung
  `case "$PY" in /*) ;; *) PY=$AUFRUF_DIR/$PY ;; esac` (nur Builtins). Danach wird `PY` nicht mehr verändert, die `py-ok:42`-Prüfung prüft also genau den Pfad, den `exec` startet.
- Kopfkommentar: neue Zeile „Relativer SCHNAPPER_PYTHON (z. B. bin/python) gilt relativ zum Aufrufort.“
- Test: `starte()` hat jetzt die optionalen Parameter `cwd=None, env_extra=None` (bestehende Aufrufe unverändert). Neuer Test `test_relativer_python_pfad_zum_aufrufort` mit Subtests `bin/python` und `./bin/python` (Symlink auf `sys.executable` im temporären Aufrufverzeichnis ≠ Repo): `/` → 200 mit „SCHNAPPER“, Exit 0 nach SIGINT, „SCHNAPPER läuft“ in der Ausgabe, Port danach frei. `import sys` ergänzt.

## Testergebnisse
- `python3 -m unittest tests.test_start_skript_s012 -v` → **19 Tests OK** (18 bisherige + 1 neuer)
- `python3 -m unittest discover -s tests` → **235 Tests OK**
- `cd cloudflare && node --test test/*.test.mjs` → **10/10 bestanden**, 0 fehlgeschlagen
- `bash -n start-schnapper.sh` → ohne Fehler
- Secret-Scan über den Diff (token/secret/passw/api-key/private key) → keine Treffer

## Gegenprobe
`git show 41e801c:start-schnapper.sh > start-schnapper.sh`, dann Modultest:
**FAILED (failures=2, errors=0)**, beide Subtests des neuen Tests (`bin/python`, `./bin/python`) rot, die übrigen 18 grün. Danach wurde die neue Datei wiederhergestellt (Modus 755) und der Modultest war wieder OK.
