# LEAD – Auftrag Lauf 20261022-2328 (UTC)

## Wahl
**Aufgabe: F5 = S-012 „Ein-Befehl-Start für Android/Termux (start-schnapper.sh, docs/HANDY-START.md)“**

Begründung nach Prioritätsregel:
1. Offene Team-Draft-PRs #36 (F1), #39 (F2), #40 (F3), #41 (F4): laut Preflight und Berichten vollständig und von CHECK „bestanden“. Dort ist nichts fortzusetzen; die Merge-Entscheidung liegt bei Jefrey.
2. `team/tasks.json` auf main enthält keinen Eintrag mit Status `open` (S-000–S-003 `review`, S-004–S-006 `proposed`). S-012 steht als `open` nur in PR #36 (Branch `agent/master/20261022-20`) und ist dort von Jefrey als F5 freigegeben.
3. Damit ist F5 der nächste offene Punkt. F6 (S-013, eBay) ist **nicht** Teil dieses Laufs.

Keine Abweichung von der Vorgabe.

## Branch
`agent/master/20261022-23`, **neu von `origin/main` @ 6dbe114** (existiert remote noch nicht). Nicht auf #36/#39/#40/#41 aufsetzen.

## Ausgangslage (geprüft)
- Start bisher: `PYTHONPATH=app python -m schnapper.web <datei>` aus dem Repo-Stamm.
- `web.py main()` (argparse): positional `datei`; `--host` (Standard `127.0.0.1`), `--port` (int, Standard 8765), `--quellen`, `--verlauf`. Gibt `SCHNAPPER läuft: http://<host>:<port>  (Beenden: Strg+C)` auf stdout aus. Bei Startfehler (`OSError` usw., z. B. fehlende Datei, Port belegt) `Start fehlgeschlagen: …` auf stderr und Exit 1. `KeyboardInterrupt` → sauberes Ende, Exit 0.
- Mit `--port 0` wäre die ausgegebene Adresse falsch (`:0`). Darum wählt der Test einen freien Port selbst und übergibt ihn.
- Standarddatei existiert: `app/vorlagen/meine-angebote.csv`. Beispiele: `app/beispiele/angebote.csv`.
- Die Tests in `tests/` nutzen `unittest`, `pathlib`, `urllib.request` und `tempfile` (siehe `tests/test_app_handy.py`). Server werden dort in-process per `erstelle_server(..., port=0)` gestartet. Für S-012 braucht es zusätzlich `subprocess` mit einem echten Prozess.
- In dieser Umgebung ist `shellcheck` **nicht** installiert. Python ist 3.13. Im App-Code gibt es keine 3.10+-Syntax (`match` oder `X | None`).

## Akzeptanzkriterien (nummeriert, alle Pflicht)
1. **Datei & Rechte:** Neue Datei `start-schnapper.sh` im Repo-Stamm, ausführbar (`chmod +x`). Im Git-Index steht der Modus `100755` (prüfbar mit `git ls-files -s start-schnapper.sh`). Der Test prüft das Ausführungsbit des Dateisystems (`os.access(..., os.X_OK)`).
2. **Shebang & Kompatibilität:** Erste Zeile `#!/usr/bin/env bash` (Termux hat kein `/bin/bash`, `env` wird dort umgebogen). Danach `set -eu` (kein `pipefail` nötig). Das Skript muss `bash -n start-schnapper.sh` fehlerfrei bestehen. Es nutzt nur bash-Builtins und `python`/`python3`, also **kein** `dirname`, `readlink -f`, `realpath`, `ss`, `curl` usw., damit es auch mit leerem PATH bis zur Python-Prüfung kommt.
3. **Arbeitsort unabhängig vom Aufrufort:** Das Skript ermittelt sein eigenes Verzeichnis über `${BASH_SOURCE[0]}` (Builtins: `${…%/*}`, `cd`, `pwd`) und arbeitet von dort aus. Es setzt `PYTHONPATH="<skriptverzeichnis>/app"` (einen vorhandenen PYTHONPATH darf es anhängen, muss es aber nicht) und startet `-m schnapper.web`. Der Aufruf aus einem fremden Arbeitsverzeichnis (z. B. `cd /tmp && /pfad/start-schnapper.sh`) funktioniert. Der Test prüft das mit `cwd=` ≠ Repo-Stamm.
4. **Python-Prüfung:** Gesucht wird zuerst `python3`, dann `python` (mit `command -v`). Optional kann `SCHNAPPER_PYTHON` einen expliziten Interpreter vorgeben. Fehlt Python, gibt das Skript auf stderr eine klare deutsche Meldung aus, die `Python` und den Termux-Befehl `pkg install python` enthält, und endet mit **Exit-Code ≠ 0** (empfohlen: 2). Zusätzlich prüft es die Mindestversion **3.8** per `"$PY" -c 'import sys; sys.exit(sys.version_info < (3, 8))'`. Bei zu alter Version kommt eine klare Meldung und Exit ≠ 0.
5. **Datei-Argument:** Ohne Argument wird `<skriptverzeichnis>/app/vorlagen/meine-angebote.csv` verwendet. Ein erstes Argument wird als Datei genommen, relativ zum **Aufruf**-Verzeichnis aufgelöst (vor dem `cd`) bzw. absolut übernommen. Existiert die Datei nicht oder ist sie keine reguläre Datei, gibt das Skript auf stderr eine klare Meldung mit Dateinamen aus (z. B. `Datei nicht gefunden: …`), startet **keinen** Server und endet mit Exit ≠ 0. Weitere Argumente nach der Datei sind nicht nötig. Werden welche übergeben, reicht eine klare Fehlermeldung mit Exit ≠ 0, oder sie werden ignoriert. Das Verhalten ist im Skriptkopf zu dokumentieren.
6. **Host/Port:** Der Server lauscht **immer nur auf 127.0.0.1** (Vorgabe aus S-012). Das Skript übergibt `--host 127.0.0.1` fest, und es gibt **keine** Möglichkeit, über das Skript `0.0.0.0` zu setzen. Der Port kommt aus der Umgebungsvariable `SCHNAPPER_PORT` (Standard 8765). Ist der Wert keine ganze Zahl von 1 bis 65535, folgt eine klare Meldung und Exit ≠ 0, ohne Start. Übergeben wird er als `--port "$PORT"`. Ein belegter Port wird über die bestehende Fehlermeldung von web.py gemeldet (Exit 1), es gibt dafür keine Extra-Logik.
7. **Adresse ausgeben:** Vor dem Start gibt das Skript eine Zeile mit der Adresse aus, z. B. `SCHNAPPER startet: http://127.0.0.1:<PORT> – in Chrome öffnen. Beenden: Strg+C`, dazu die verwendete Datei. Danach folgt die vorhandene Zeile `SCHNAPPER läuft: http://127.0.0.1:<PORT>` von web.py. Die Ausgabe auf stdout darf nicht dauerhaft gepuffert hängen: per `PYTHONUNBUFFERED=1` oder `-u` setzen, damit der Test die Zeile lesen kann.
8. **Prozessführung:** Python wird mit `exec` gestartet, damit SIGINT/SIGTERM direkt beim Server ankommen und kein verwaister Kindprozess zurückbleibt. Der Exit-Code von web.py wird durchgereicht.
9. **Keine Downloads, keine Installation, keine Geheimnisse:** Das Skript enthält kein `curl`, `wget`, `pip`, `pkg install` (außer als **Text** in der Hinweismeldung), `git clone/pull`, `apt` und keine Tokens oder Zugangsdaten. Der Test prüft das statisch: Er sucht nach `curl`, `wget`, `pip ` / `pip3`, `git `, `apt` und `npm` außerhalb von Kommentar- oder echo-Hinweiszeilen. Wenn das zu fehleranfällig ist, prüft er einfach, dass diese Wörter nur in Zeilen mit `echo`/`printf` oder `#` vorkommen. `pkg install python` darf nur in der Meldung stehen.
10. **Hinweis „ungetestet“:** Im Kopfkommentar von `start-schnapper.sh` **und** in `docs/HANDY-START.md` steht wörtlich `auf echtem Gerät ungetestet` (bzw. `auf einem echten Android-Gerät noch nicht getestet` **plus** die Formulierung `auf echtem Gerät ungetestet`). Der Test prüft die exakte Zeichenkette `auf echtem Gerät ungetestet` in beiden Dateien.
11. **Doku `docs/HANDY-START.md`:** Schritt 4 wird auf den Ein-Befehl-Start umgestellt (`cd ~/Schnapper-main` bzw. den entpackten Ordner, dann `bash start-schnapper.sh`, ggf. vorher `chmod +x start-schnapper.sh`, weil ZIP-Downloads das Ausführungsbit verlieren können. Daher als Hauptweg `bash start-schnapper.sh` empfehlen). Es wird beschrieben, wie man eine eigene Datei angibt (`bash start-schnapper.sh app/beispiele/angebote.csv`), wie man den Port per `SCHNAPPER_PORT=8800 bash start-schnapper.sh` ändert und wie man beendet (Strg+C bzw. Termux-Tastenleiste CTRL + C). Der bisherige manuelle Befehl `PYTHONPATH=app python -m schnapper.web …` bleibt als „Alternative ohne Skript“ erhalten. In `pkg install` ist `unzip` weiterhin nötig. Der Abschnitt zu PR #15 bleibt inhaltlich unverändert (nicht Gegenstand dieser Aufgabe), der Datumsstempel wird auf 22.10.2026 / F5 aktualisiert.
12. **Test `tests/test_start_skript_s012.py`** (nur Standardbibliothek, `unittest`):
    a. **Starttest (Pflicht):** Freien Port ermitteln (`socket.bind(("127.0.0.1", 0))`, Port merken, Socket schließen). Dann `subprocess.Popen(["bash", str(SKRIPT)], cwd=<tempdir>, env={**os.environ, "SCHNAPPER_PORT": str(port)}, stdout=PIPE, stderr=PIPE, text=True)`. Abwarten (Polling bis max. ~15 s) auf `GET http://127.0.0.1:<port>/` mit `urllib.request`, erwartet werden HTTP 200 und HTML mit `SCHNAPPER`. Danach `proc.terminate()` bzw. SIGINT, `wait(timeout=10)`, im `finally`/`addCleanup` notfalls `kill()`. Zusätzlich prüfen, dass stdout `http://127.0.0.1:<port>` enthält.
    b. Ohne Datei-Argument wird `meine-angebote.csv` verwendet (Ausgabe nennt den Dateinamen oder `/api/…`-Status zeigt ihn; Ausgabe genügt). Darf mit (a) kombiniert sein.
    c. **Datei-Argument:** Start mit `app/beispiele/angebote.csv` (absolut) liefert die Seite (darf mit (a) kombiniert sein).
    d. **Fehlende Datei:** `bash start-schnapper.sh /gibt/es/nicht.csv` endet schnell mit Exit ≠ 0, stderr enthält den Dateinamen, auf dem Port lauscht nichts.
    e. **Fehlendes Python:** Skript mit `/bin/bash` (bzw. `shutil.which("bash")`) aufrufen, mit `env={"PATH": <leeres tempdir>}` und ohne `SCHNAPPER_PYTHON`. Erwartet: Exit ≠ 0 und Meldung mit `Python` auf stderr.
    f. **Ungültiger Port:** `SCHNAPPER_PORT=abc` → Exit ≠ 0, klare Meldung, kein Start.
    g. **Statisch:** Shebang `#!/usr/bin/env bash`, `os.access(X_OK)`, `--host 127.0.0.1` vorhanden, `0.0.0.0` nicht als Startwert, Verbotswörter aus AK 9, `auf echtem Gerät ungetestet` in Skript und Doku, `bash -n` per subprocess mit Rückgabe 0.
    h. Tests, die `bash` brauchen, werden mit `skipUnless(shutil.which("bash"))` geschützt. In dieser Umgebung muss **0 skipped** herauskommen (CHECK misst das).
    i. Es entstehen keine Dateien im Repo und keine verwaisten Prozesse; temporäre Verzeichnisse laufen über `tempfile`.
13. **Regression:** Die gesamte Suite ist grün (vorher 216/216 auf main, danach 216 + neue Tests, 0 Fehler) und Cloudflare 10/10.
14. **Optional README.md:** Im Abschnitt „Web-Oberfläche“ darf **eine** kurze Zeile auf `bash start-schnapper.sh` (Handy/Termux, siehe `docs/HANDY-START.md`) verweisen. Sonst bleibt README unverändert.

## Dateien
**Erlaubt (nur diese):**
- `start-schnapper.sh` (neu, Modus 100755)
- `docs/HANDY-START.md`
- `tests/test_start_skript_s012.py` (neu)
- `README.md`: nur Startabschnitt „Web-Oberfläche“, max. ein kurzer Verweis

**Verboten:**
- `team/tasks.json`, `team/STATUS.md`, `team/handoff/`, `team/runs/`, `team/agent.py`
- `.github/` (insbesondere `.github/workflows/`)
- `cloudflare/`
- `app/schnapper/web.py` und der gesamte übrige App-Code. Eine Änderung an web.py ist nur zulässig, wenn ohne sie ein AK **nachweislich** nicht erfüllbar ist. Das muss im Commit und in der Übergabe begründet werden. Nach Analyse ist das **nicht** nötig: Alle Parameter (`datei`, `--host`, `--port`) existieren bereits.
- Alles, was ZENTNA, JERRY AL oder Beatmaster betrifft (tabu)
- Keine Secrets, keine neuen Abhängigkeiten, kein `pip install`, Budget 0 €

## Testbefehle (im Repo-Stamm)
```
bash -n start-schnapper.sh
git ls-files -s start-schnapper.sh          # erwartet 100755 (nach git add)
python3 -m unittest tests.test_start_skript_s012 -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
command -v shellcheck && shellcheck start-schnapper.sh   # hier nicht installiert → als „nicht verfügbar“ vermerken
```
Manuell zusätzlich: `SCHNAPPER_PORT=8799 ./start-schnapper.sh` im Hintergrund starten, `curl -s http://127.0.0.1:8799/ | head`, dann beenden. Aus fremdem cwd wiederholen.

## Commit
- Genau ein Commit auf `agent/master/20261022-23`, Nachricht beginnt mit **`SCHNAPPER MASTER:`**, z. B.
  `SCHNAPPER MASTER: F5 (S-012) Ein-Befehl-Start für Android/Termux (start-schnapper.sh)`
- Ausführbarkeit sicherstellen: `chmod +x start-schnapper.sh` vor `git add`. Ggf. `git update-index --chmod=+x start-schnapper.sh`.
- Kein Force-Push, kein Merge. PR nur als **Draft**. PR-Text nennt: „auf echtem Gerät ungetestet“, Host fest 127.0.0.1, dass S-012 in tasks.json erst nach Merge von #36 nachzuziehen ist, und mögliche Überschneidung von `docs/HANDY-START.md` mit #36/#15.

## Hinweise für BRAIN/CHECK
- Fallstrick ZIP-Download: Das Ausführungsbit kann verloren gehen. Darum `bash start-schnapper.sh` als dokumentierten Hauptweg verwenden.
- Fallstrick Puffer: Ohne `PYTHONUNBUFFERED=1` sieht der Test die Ausgabe von web.py eventuell nicht. Der Test soll ohnehin primär per HTTP-Polling warten, nicht per stdout.
- Termux: `python` und `python3` existieren dort beide. Die Suche nach `python3` zuerst ist korrekt.
- CHECK misst selbst: Testanzahl, 0 skipped im neuen Modul, Modus 100755, Diff nur auf erlaubten Dateien, Secret-Scan, `git diff origin/main -- app/ .github/ cloudflare/ team/` leer.
