# CHECK – Lauf 20261028-1829

- Start CHECK: 2026-10-28 18:35:48 UTC
- Ende CHECK: 2026-10-28 18:38:30 UTC
- Geprüft: Branch `agent/master/20261022-21`, Kopf `fd16763e43bfa1370039b85b3d7d5625aba6a993` (PR #39)

## Urteil: **bestanden**

## Git-Stand
- `git status`: Arbeitsbaum sauber, auf `agent/master/20261022-21`. Kopf `fd16763…` entspricht dem SHA in brain.md.
- `git merge-base --is-ancestor origin/agent/master/20261022-21 HEAD` → ja (origin-Kopf `2666d8b`). Genau 1 Commit darüber, Push als Fast-Forward ohne Force möglich.
- `git merge-base --is-ancestor origin/main HEAD` → ja (origin/main `6dbe114`).
- Commit-Trailer `Co-Authored-By: Claude Opus 5.5 …` und `Claude-Session: …` sind vorhanden.

## Diff und Secret-Scan
- `git diff --stat 2666d8b HEAD`: nur `app/schnapper/web.py` (+23) und `tests/test_app_erfassen_s009.py` (+43). Beide Dateien sind erlaubt.
- `git diff --stat origin/main...HEAD`: web.py, app.css, app.js, index.html und die Testdatei. Diese Dateien gehören zum bisherigen PR-Inhalt, keine davon ist neu in diesem Lauf.
- Unverändert gegenüber 2666d8b (`git diff --quiet`): `angebot.py`, `einlesen.py`, `app/schnapper/web/`, `.github`, `team`, `cloudflare`.
- Tabu-Pfade (ZENTNA, JERRY AL/Jerry-AL, Beatmaster, .github, team/, cloudflare/) kommen in den Dateinamen des Diffs gegen main nicht vor.
- Secret-Scan des Diffs gegen main (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, password/passwort=) ergibt keine Treffer.

## Tests (selbst ausgeführt)
- `python3 -m unittest discover -s tests` ergibt **Ran 237, OK**, ohne Skip in meinem Lauf. Auf dem alten Stand 2666d8b im Worktree: **Ran 233, OK**. Das macht +4 neue Tests und keine zusätzlichen Skips.
- `python3 -m unittest tests.test_app_erfassen_s009 -v` ergibt **Ran 21, OK**. `test_ak8_erfassen_und_csv_im_browser ... ok` lief also tatsächlich, mit dem vorinstallierten Chromium und ohne Skip. Den Browser habe ich nicht nachinstalliert.
- `cd cloudflare && node --test test/*.test.mjs` ergibt **tests 10, pass 10, fail 0, skipped 0**.

## Gegenprobe (selbst gemacht)
Dazu habe ich `git worktree add --detach <scratch>/wt-alt 2666d8b` angelegt, die neue Testdatei aus HEAD hineinkopiert und `python3 -m unittest tests.test_app_erfassen_s009` gestartet. Ergebnis: **FAILED (failures=17, errors=1)**.
- dict-Titel: `FAIL … (feld='titel', wert={'a': 1})` mit `201 != 422`. Ebenso schlagen list-, bool- und int-Titel, list-url, dict-zustand sowie dict-, bool- und int-kategorie fehl, außerdem versand False/[].
- `test_kategorie_laenge` meldet ERROR mit ImportError `MAX_KATEGORIE`. Mein Randfallskript auf dem alten Stand zeigt zusätzlich, dass eine kategorie mit 101 Zeichen dort **201** liefert, mit 3000 Zeichen ebenfalls **201**.

Der Worktree ist danach entfernt (`git worktree list` zeigt nur noch den Klon).

## Randfälle (eigenes Skript gegen echten Server auf 127.0.0.1, neuer Stand)
Für jeden Fall habe ich `/api/suche` und die Dateien im Datenverzeichnis vor und nach der Anfrage verglichen. Bei jeder Ablehnung blieben beide unverändert.

| Fall | Status | Fehlertext / Bemerkung |
|---|---|---|
| titel dict / list / bool / int | 422 | `Feld 'titel' muss Text sein` |
| titel null, titel "  " | 422 | `Feld 'titel' fehlt` |
| zustand list, url dict, kategorie dict | 422 | Feldname im Text |
| zustand null, kategorie null, versand null | 201 | null gilt bei optionalen Feldern als leer (in brain.md begründet, nach AK 1 erlaubt) |
| preis true/false/list/dict, versand true, referenzpreis list | 422 | `Feld '<name>' muss Text oder Zahl sein` |
| preis null | 422 | `Feld 'preis' fehlt` |
| preis 450 / 19.9 | 201 | |
| kategorie 100 / 100 mit Leerzeichen außen / 100× „ä“ | 201 | |
| kategorie 101 / 3000 | 422 | `Feld 'kategorie' ist länger als 100 Zeichen` |
| GUELTIG; GUELTIG + quelle/id/erfasst_am/waehrung | 201 | fremde Felder werden ignoriert (dazu ist `test_ak4` grün) |
| ohne X-Schnapper | 403 | unverändert |
| kaputtes JSON / Liste statt Objekt | 400 | unverändert |
| preis NaN | 422 | „Preis ist keine endliche Zahl“, wie auf dem alten Stand |
| Body > 4096 | 413 | unverändert |

## Akzeptanzkriterien
1. **erfüllt.** Textfelder mit Nicht-`str` ergeben 422 und `fehler` mit dem Feldnamen (Tabelle oben, `test_textfelder_nur_text`). null ist nur bei optionalen Feldern erlaubt; die Ausnahme ist in brain.md begründet.
2. **erfüllt.** `bool` ist explizit ausgeschlossen (`isinstance(wert, bool) or not isinstance(wert, (str, int, float))` in `typfehler`), 450 und 19.9 ergeben 201.
3. **erfüllt.** 101 Zeichen ergeben 422, genau 100 Zeichen (auch nach strip) ergeben 201. Die Konstante `MAX_KATEGORIE = 100` steht in web.py und entspricht `maxlength="100"` in index.html, Z. 99. Ein Test prüft die Gleichheit.
4. **erfüllt.** Bei Ablehnung bleiben `/api/suche` und die Dateien unverändert (Skript und `pruefe_422`). Die Prüfung läuft vor `aus_dict` und `zustand.hinzufuegen`.
5. **erfüllt.** GUELTIG ergibt 201, die Whitelist greift weiter, 400/403/413 sind unverändert. 411 steht unverändert im Code (Diff berührt den Pfad nicht), und die bestehenden Tests sind grün.
6. **erfüllt.** Klasse `ErfassenTypen` mit 4 Tests und subTests: titel dict/list/bool/int, kategorie dict, preis bool/list/dict, kategorie 101 gegen 100, preis 450 ergibt 201.
7. **erfüllt.** Die Gegenprobe habe ich selbst wiederholt: 17 failures und 1 error, darunter dict-Titel. Die 101-Zeichen-Kategorie liefert auf dem alten Stand 201 (Skript).
8. **erfüllt.** Die Prüfung steckt nur in `typfehler()` und `_angebot_erfassen` in web.py. angebot.py und einlesen.py sind unverändert.
9. **erfüllt.** 237 Tests OK (233 + 4), keine zusätzlichen Skips, der Browsertest lief.
10. **erfüllt.** 10 pass, 0 fail.
11. **erfüllt.** Der Diff berührt nur erlaubte Dateien, der Secret-Scan ist leer.
12. **teilweise prüfbar, soweit CHECK zuständig erfüllt.** Der Commit ist ein Fast-Forward-Nachfolger von 2666d8b und trägt beide Trailer. Push, Draft-Status und PR-Body-Abschnitt sind Aufgabe von COMMAND und noch offen.

## Hinweise (kein Mangel)
- In meinem Lauf meldete discover keinen Skip, brain.md nennt `skipped=1`. Das liegt vermutlich an der Umgebung; die Bedingung „Skips höchstens wie vorher“ ist erfüllt.
- Die CSV-Formel-Injection bleibt nach LEAD bewusst offen.
- Ich habe nichts geändert, committet oder gepusht. Der Klon steht auf dem Branch, der Arbeitsbaum ist sauber.
