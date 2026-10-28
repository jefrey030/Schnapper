# CHECK – Lauf 20261028-1629

**Urteil: BESTANDEN**

Geprüft wurde Commit `41e801c3ca4f89e94e6d1766b42f4cbc53f5e233` im Worktree /home/claude/brain-wt-1629. Die Gegenprobe lief in einem eigenen Worktree, der danach wieder entfernt wurde. Code wurde nicht geändert, gepusht wurde nichts.

## Grunddaten
- HEAD ist 41e801c…, der Worktree ist sauber. Remote-Kopf `agent/master/20261022-23` ist weiterhin 779e8b7, der Commit ist also noch nicht gepusht. HEAD ist ein direkter Nachfahre von 779e8b7, damit ist ein Fast-Forward möglich.
- origin/main ist 6dbe114 und Vorfahre von HEAD (`merge-base --is-ancestor` liefert OK). Nach `git fetch` gibt es keinen neueren main-Stand.
- `git diff origin/agent/master/20261022-23..HEAD`: 2 Dateien, +24/−2. Es sind `start-schnapper.sh` und `tests/test_start_skript_s012.py`, genau die erwarteten Dateien.
- `git diff origin/main...HEAD`: README.md, docs/HANDY-START.md, start-schnapper.sh, tests/test_start_skript_s012.py. Das ist der bisherige PR-#44-Umfang. Es gibt keine Änderungen unter `.github/`, `team/`, `app/` oder `cloudflare/`.
- Tabu-Pfade (ZENTNA, JERRY AL, Beatmaster): keine Treffer.
- Secret-Scan des gesamten Diffs (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, token, secret): leer.
- Der Commit trägt die Trailer Co-Authored-By und Claude-Session.

## Akzeptanzkriterien
| AK | Ergebnis | Beleg |
|---|---|---|
| 1 echo | ok | Manuell: exit=2, stdout leer, stderr „Python ist zu alt oder kein Python (echo). SCHNAPPER braucht Python 3.8 oder neuer.“ + „pkg install python“. Der subTest prüft `lauscht(port)` als False. |
| 2 /bin/echo | ok | Manuell: exit=2, Ausgabe wie bei echo. Der Test greift auf `shutil.which` zurück, `shutil` ist importiert. |
| 3 true | ok | Manuell: exit=2, Ausgabe wie bei echo. Zusätzlich geprüft: `false`, ein nicht existierender Pfad und ein Fake-Skript ohne Ausgabe enden mit exit=2. Ein Fake-Skript, das „py-alt“ ausgibt, endet mit exit=2 und der Meldung. |
| 4 Normalstart | ok | Die 3 genannten Tests sind grün. Manuell: echtes python3 (3.13) startet, „SCHNAPPER startet“ erscheint, der Port lauscht, Ende erst durch timeout (124). Mit `SCHNAPPER_PYTHON=python3.11` startet es ebenfalls. |
| 5 Python fehlt | ok | `test_fehlendes_python` ist grün. Dieser Zweig steht vor der geänderten Stelle und ist unverändert. |
| 6 exakter Vergleich | ok | Es wird `[ "$PY_OK" != "py-ok:42" ]` verwendet. Der `-c`-Code enthält nur `"py-ok:%d" % (6 * 7)`, der Text „py-ok:42“ kommt darin nicht vor. |
| 7 neuer Test | ok | `test_falscher_interpreter_wird_abgelehnt`: subTest über echo, /bin/echo und true. Er nutzt `ohne_schnapper_env(SCHNAPPER_PORT=…, SCHNAPPER_PYTHON=…)`, `freier_port()`, `timeout=15` und als cwd ein TemporaryDirectory. |
| 8 Gegenprobe | ok | Eigener Worktree mit dem Skript aus 779e8b7: 18 Tests, **FAILED (failures=3)**. echo und /bin/echo: `0 != 2 : -c import sys; …`. true: `0 != 2 : SCHNAPPER startet: http://127.0.0.1:55551 …`. Nach dem Zurücksetzen auf den Fix-Stand: OK. |
| 9 Struktur | ok | `bash -n` liefert 0. Der Shebang ist `#!/usr/bin/env bash`, `set -eu` und der `BASH_VERSION`-Wächter sind im Diff unberührt. Der Modus ist 100755. `test_keine_externen_hilfsprogramme` und `test_keine_downloads_oder_installation` sind grün. Mit `sh` erscheint weiterhin „Bitte mit bash starten“. |
| 10 Hinweis ungetestet | ok | Der Hinweis steht in start-schnapper.sh Z. 4 und in docs/HANDY-START.md Z. 3. |
| 11 Testzahlen | ok | Gesamtsuite: **234 Tests OK**. s012: **18 OK**. Cloudflare: **10/10 pass**. |
| 12 Secrets/Trailer/Push | ok, Push offen | Secret-Scan leer, Trailer vorhanden. Der Push ist noch offen (Aufgabe des LEAD) und als Fast-Forward möglich. |

## Regressionen
- stderr-Rauschen des Interpreters: Lauf mit `PYTHONVERBOSE=1` startet normal. stderr wird bei der Prüfung mit `2>/dev/null` verworfen, es zählt nur stdout.
- Ein Python ohne Ausgabe (stumm) wird mit exit=2 abgelehnt. Das ist so gewollt.
- Verbleibendes Restrisiko, kein Mangel: Eine sitecustomize-Datei oder ein Wrapper, der zusätzlich etwas auf stdout schreibt, würde den exakten Vergleich scheitern lassen. In Termux ist das unüblich. Auf echtem Gerät weiterhin ungetestet.
- Kleine Abweichung im BRAIN-Bericht: Dort steht „skipped=1“, bei mir lief die Suite ohne Skip-Angabe („OK“). Das hat keinen Einfluss auf das Urteil.
