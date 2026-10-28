# BRAIN – Lauf 20261028-1629

## Branch
`agent/master/20261022-23` (PR #44), Worktree `/home/claude/brain-wt-1629`, Basis 779e8b7 (= origin-Kopf).
origin/main = 6dbe114, ist Vorfahre (merge-base --is-ancestor wahr), also kein Merge nötig.
**Commit: `41e801c3ca4f89e94e6d1766b42f4cbc53f5e233`**, lokal, NICHT gepusht (Push als Fast-Forward durch LEAD).

## Geänderte Dateien (2 Dateien, +24/−2)
- `start-schnapper.sh`: Die Prüfung verlangt jetzt die exakte Ausgabe `py-ok:42`. Der Wert wird im Python-Code als `6 * 7` berechnet und steht nicht wörtlich im `-c`-Code. Der Vergleich nutzt `!=` und `|| true` (wegen set -eu). Die Meldung lautet „Python ist zu alt oder kein Python ($PY). SCHNAPPER braucht Python 3.8 oder neuer.“ und nennt zusätzlich „pkg install python“. Im Kopfkommentar unter „Verhalten“ steht neu: „Kein echtes Python (z. B. SCHNAPPER_PYTHON=echo oder true) -> Exit 2.“
- `tests/test_start_skript_s012.py`: Neuer Test `test_falscher_interpreter_wird_abgelehnt`. Er prüft per subTest die Interpreter echo, /bin/echo (Ersatz: shutil.which) und true. Dabei kommen `ohne_schnapper_env(SCHNAPPER_PORT, SCHNAPPER_PYTHON)`, ein freier Port, timeout=15 und ein Temp-cwd zum Einsatz. Geprüft werden: Exit 2, stderr enthält „Python“ und „3.8“, stdout enthält kein „SCHNAPPER startet“ und am Port lauscht nichts.
- `docs/HANDY-START.md` ist unverändert (optional, nicht nötig).
- Unverändert sind außerdem: Shebang, `set -eu`, der BASH_VERSION-Wächter und der Modus 100755. Neue Hilfsprogramme gibt es nicht. Der Hinweis „auf echtem Gerät ungetestet“ steht weiter in Skript und Doku.

## Tests
- `python3 -m unittest discover -s tests`: **234 Tests OK** (skipped=1, schon vorher vorhanden)
- `python3 -m unittest -v tests.test_start_skript_s012`: **18 OK**. Darin grün sind der neue Test sowie test_start_ohne_argument_aus_fremdem_cwd, test_start_mit_datei_argument, test_relative_datei_zum_aufrufort, test_fehlendes_python, test_keine_externen_hilfsprogramme, test_keine_downloads_oder_installation und test_bash_n.
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**
- Manuell: echo, /bin/echo und true enden jeweils mit **exit=2** und der Meldung „Python ist zu alt oder kein Python (…) … 3.8 …“.
- `bash -n start-schnapper.sh`: OK

## Gegenprobe
Mit `git show 779e8b7:start-schnapper.sh > start-schnapper.sh` ergibt sich: 18 Tests, **FAILED (failures=3)**. Rot sind die subTests echo, /bin/echo und true:
- echo und /bin/echo: `AssertionError: 0 != 2 : -c import sys; sys.exit(sys.version_info < (3, 8))`
- true: `AssertionError: 0 != 2 : SCHNAPPER startet: http://127.0.0.1:38155 …`

Danach wurde der Fix-Stand wiederhergestellt (Modus 755). Ergebnis: 18 OK.

## Secret-Scan
Diff-Grep auf token, secret, passw und api key: leer.

## Offene Punkte
- Push (Fast-Forward) und Nachtrag „Update Lauf 20261028-1629“ im PR-#44-Body übernimmt der LEAD.
- team/STATUS.md und tasks.json werden nur auf agent/master/reports gepflegt. S-012 bleibt `review`.
- Auf echtem Android/Termux weiterhin ungetestet.
