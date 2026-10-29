# CHECK – Lauf 20261029-0128

- Start (UTC): 2026-10-29T01:33:27Z
- Ende (UTC): 2026-10-29T01:35:21Z (Nachtrag zur Rückfrage)
- Geprüft: Worktree `/home/claude/wt-brain`, Branch `agent/master/20261022-23`, HEAD `b03b9868af91ab96707bec95473a38bb8f658aab`, Parent `41e801c3ca4f89e94e6d1766b42f4cbc53f5e233` (= `origin/agent/master/20261022-23`). Nicht gepusht.

## Urteil: **bestanden**

## Testzahlen (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest discover -s tests` | Ran 235, OK |
| `python3 -m unittest tests.test_start_skript_s012 -v` | Ran 19, OK (18 alt + `test_relativer_python_pfad_zum_aufrufort`) |
| `cd cloudflare && node --test test/*.test.mjs` | tests 10, pass 10, fail 0 |
| `bash -n start-schnapper.sh` | ohne Fehler |
| Gegenprobe (altes Skript aus `origin/agent/master/20261022-23`) | Ran 19, **FAILED (failures=2, errors=0)**: beide Subtests `bin/python` und `./bin/python` rot |

Nach der Gegenprobe `git checkout -- start-schnapper.sh`: `git status --short` leer, Modus 100755 (Index und Datei).

## Kriterien
1. **Commit/Dateien** – erfüllt. `git diff --stat origin/agent/master/20261022-23..HEAD`: nur `start-schnapper.sh` (+7) und `tests/test_start_skript_s012.py` (+27/−5). Parent ist genau 41e801c. Gegen `origin/main...HEAD` zusätzlich nur `README.md` und `docs/HANDY-START.md` aus früheren Branch-Commits, nicht aus diesem Commit. Keine `.github/workflows`, keine Tabu-Pfade (ZENTNA/JERRY AL/Jerry-AL/Beatmaster: grep ohne Treffer).
2. **Relativer `SCHNAPPER_PYTHON`** – erfüllt. Durch den neuen Test belegt (200, „SCHNAPPER“ im HTML, Exit 0 nach SIGINT, Port frei) und von mir per Hand nachgestellt: `bin/python` in einem Aufrufordner mit Leerzeichen im Pfad → http 200, rc 0; aus `cwd=/` mit `SCHNAPPER_PYTHON=usr/bin/python3` → 200, rc 0.
3. **Geprüfter = gestarteter Interpreter** – erfüllt. Z. 93–96 macht `PY` absolut (`$AUFRUF_DIR/$PY`), danach gibt es keine Zuweisung an `PY` mehr (Z. 99 Prüfung, Z. 117 `exec "$PY"`). `AUFRUF_DIR=$PWD` wird in Z. 37 vor jedem `cd` gesetzt.
4. **Absolut/Standardsuche unverändert** – erfüllt. Absoluter Pfad (mit Leerzeichen) → 200/rc 0; `SCHNAPPER_PYTHON=python3` (Name ohne Schrägstrich aus PATH) → 200/rc 0. Alle 18 alten Tests grün. Zusätzlich jetzt auch richtig: relative PATH-Einträge `PATH=bin:…`, `PATH=.` und leerer Eintrag `PATH=:…` → jeweils 200/rc 0.
5. **Fehlerfälle** – erfüllt. `/nix/python` und `~/nix/python` (Tilde wird bewusst nicht erweitert) → rc 2 „Python nicht gefunden“; `echo`/`true` → rc 2 (Test `test_falscher_interpreter_wird_abgelehnt` grün); `PATH=` → rc 2 mit „pkg install python“.
6. **Nur Builtins** – erfüllt. Die Änderung ist ein `case`. `grep -E 'realpath|readlink|dirname'` im Skript: kein Treffer. `test_keine_externen_hilfsprogramme` grün.
7. **Hinweis/Syntax/Modus** – erfüllt. „auf echtem Gerät ungetestet“ steht in Skript Z. 4 und in `docs/HANDY-START.md` Z. 3; `test_hinweis_ungetestet` grün; `bash -n` ok; Modus 100755. Der dash/sh-Wächter wirkt weiter: `dash start-schnapper.sh` und `sh start-schnapper.sh` → „Bitte mit bash starten“, rc 2.
8. **Gegenprobe** – erfüllt (siehe oben: failures=2, errors=0).
9. **Gesamtsuite/Cloudflare/Secrets** – erfüllt. 235 OK, Cloudflare 10/10. Secret-Scan des Diffs (`sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|token|secret`) über `origin/agent/master/20261022-23..HEAD` und `origin/main...HEAD`: keine Treffer.
10. **Kein Push** – erfüllt. HEAD liegt nur lokal, `origin/agent/master/20261022-23` steht noch auf 41e801c; ein Fast-Forward ist möglich.

## Hinweis (nicht blockierend, kein Nachbesserungsgrund)
- Bei `SCHNAPPER_PYTHON=echo` oder `true` gibt `command -v` den Builtin-Namen zurück. Die Fehlermeldung nennt deshalb jetzt einen künstlichen Pfad, z. B. „kein Python (/…/aufrufort/echo)“. Exit 2 und Ablehnung bleiben richtig. Das ist nur kosmetisch und kann bei Bedarf später verbessert werden.
- **Rückfrage ORCHESTRATOR (01:35:21Z): Ist `SCHNAPPER_PYTHON=python3` eine Regression? Nein.** Gezielter Vergleich, Aufrufordner ≠ Skriptordner, normales PATH:

  | Stand | Ergebnis |
  |---|---|
  | neu (b03b986), `SCHNAPPER_PYTHON=python3` | http 200, rc 0 |
  | neu (b03b986), `SCHNAPPER_PYTHON=python` | http 200, rc 0 |
  | alt (41e801c), `SCHNAPPER_PYTHON=python3` | http 200, rc 0 |
  | alt (41e801c), `SCHNAPPER_PYTHON=python` | http 200, rc 0 |

  Warum das so ist: Für ein Programm aus PATH gibt `command -v python3` den Pfad aus dem PATH-Eintrag zurück, hier `/usr/local/bin/python3`, also absolut. Der neue `case` ändert daran nichts. Einen bloßen Namen liefert `command -v` nur bei Builtins, Funktionen und Aliasen (`echo`, `true`). Die werden ohnehin abgelehnt, und für sie gilt nur die kosmetische Notiz oben. Bei einem relativen PATH-Eintrag wird der Pfad richtig gegen den Aufrufort aufgelöst (siehe Kriterium 4). Nach dem Vergleich ist das Skript wiederhergestellt, `git status` ist leer und der Modus ist 755. **Das Urteil bleibt „bestanden“.**
- Der Test ist echt: Der Symlink im Aufrufordner (≠ Repo, per `assertNotEqual` abgesichert) gibt es unter dem Skriptordner nicht. Deshalb fällt der alte Stand deterministisch durch.
