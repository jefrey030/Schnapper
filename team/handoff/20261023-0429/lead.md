# LEAD-Plan Lauf 20261023-0429 (UTC)

## Aufgabe
Den offenen Team-Draft-PR **#41 (F4 = S-011 „Barcode per Kamera scannen“)** fortsetzen:
1. Den Branch per **Merge von `origin/main` (6dbe114)** auf den aktuellen Stand bringen (kein Rebase, kein Force-Push).
2. In `tests/test_app_kamera_s011.py` den fest verdrahteten Chromium-Pfad (`/opt/pw-browsers/chromium-1194/chrome-linux/chrome`) durch eine **automatische Suche** nach der installierten Chromium-Version ersetzen. Sonst werden die Browsertests ohne `PLAYWRIGHT_BROWSERS_PATH` still übersprungen.

Begründung: F1–F6 haben alle offene Draft-PRs. #41 ist neben #36 der einzige PR, der hinter main liegt (4 Commits: #37, #34, #42, #43). Das hat der letzte Bericht als nächsten kleinsten Schritt empfohlen. Der Schritt ist klein und in ca. 30 Minuten erreichbar.

## Befund (geprüft von LEAD)
- `git log origin/main..origin/agent/master/20261022-2238` ergibt 1 Commit: 38a469e (F4). Umgekehrt fehlen dem Branch 4 Commits: bbbed04, 1926983, 6d91dfa, 6dbe114.
- `git merge-tree --write-tree origin/main origin/agent/master/20261022-2238` ergibt rc=0, Baum 56e74ac, **konfliktfrei**.
- Diff des Branches gegenüber main: `app.css`, `app.js`, `index.html`, `tests/test_app_kamera_s011.py` (+381). main hat seit e134cd0 keine dieser Dateien geändert.
- Die CSP in `app/schnapper/web.py` auf main ist identisch mit der Konstante `CSP` im F4-Test. `test_csp_unveraendert` bleibt also gültig.
- Installiert ist `/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`. **Achtung:** Der Unterordner heißt jetzt `chrome-linux64`, nicht mehr `chrome-linux`. `chromium-1194` existiert nicht.
- Der fest verdrahtete Pfad steht im Branch nur in `tests/test_app_kamera_s011.py` (Zeilen 18, 106, 112). Auf main gibt es keine Browsertests mit `chromium-1194`. Dieselbe Stelle in `test_app_sicherung_s010.py` (PR #40) ist **nicht** Teil dieses Laufs.

## Branch
`agent/master/20261022-2238` (Draft-PR #41) fortsetzen. Keinen neuen Branch anlegen.

## Genaue Schritte (BRAIN)
1. `git fetch origin` ausführen und `git checkout -B agent/master/20261022-2238 origin/agent/master/20261022-2238`. Prüfen, dass HEAD = 38a469e ist.
2. `git merge --no-ff origin/main -m "SCHNAPPER MASTER: main (#34, #37, #42, #43) in F4 übernommen (S-011)"`. Nichts von Hand auflösen. Wenn ein Konflikt auftritt: abbrechen (`git merge --abort`) und als Blocker melden.
3. Nach dem Merge die Tests ausführen (siehe unten). Erwartet wird „alles grün“.
4. In `tests/test_app_kamera_s011.py`:
   - Die Konstante `CHROMIUM = pathlib.Path(".../chromium-1194/...")` durch eine kleine Hilfsfunktion ersetzen, z. B. `_finde_chromium()`. Sie gibt einen `pathlib.Path` oder `None` zurück:
     - Basisordner: `os.environ.get("PLAYWRIGHT_BROWSERS_PATH")`, sonst `/opt/pw-browsers`
     - Kandidaten: `<basis>/chromium-*/chrome-linux*/chrome` (deckt `chrome-linux` und `chrome-linux64` ab), nur existierende Dateien
     - Auswahl: höchste Versionsnummer **numerisch** (int nach `chromium-`). Ordner wie `chromium_headless_shell-*` oder `chromium` ohne Nummer werden ignoriert.
   - `CHROMIUM = _finde_chromium()`
   - skipUnless-Bedingung: `sync_playwright is not None and (CHROMIUM is not None or os.environ.get("PLAYWRIGHT_BROWSERS_PATH"))`
   - In `setUpClass`: `kw = {"executable_path": str(CHROMIUM)} if CHROMIUM else {}`
   - Den Kommentar „Stand von main (e134cd0)“ bei `CSP` auf „Stand von main (6dbe114)“ ändern (optional, nur Text).
   - Einen kleinen statischen Test ergänzen (ohne Browser), z. B. `test_chromium_suche`. Er legt in einem `tempfile.TemporaryDirectory` die Ordner `chromium-999/chrome-linux/chrome`, `chromium-1243/chrome-linux64/chrome` und `chromium_headless_shell-2000/chrome-linux/chrome` an und erwartet, dass die Funktion (Basisordner als optionaler Parameter, z. B. `_finde_chromium(basis=None)`) den 1243-Pfad liefert. Für einen leeren Ordner erwartet er `None`.
5. Als **einen** Commit committen: „SCHNAPPER MASTER: F4 Browsertests finden installiertes Chromium automatisch (S-011)“.
6. Nicht pushen. Das macht COMMAND nach CHECK, per normalem Fast-Forward-Push.

## Akzeptanzkriterien
1. HEAD des Branches stammt von 38a469e ab (`git merge-base --is-ancestor 38a469e HEAD`), es gibt keinen Rebase und keine umgeschriebene Historie.
2. Es gibt genau einen Merge-Commit mit den Eltern 38a469e und 6dbe114. Sein Baum ist identisch mit `git merge-tree --write-tree origin/main 38a469e` (56e74ac), also wurde nichts von Hand aufgelöst.
3. `origin/main` ist Vorfahre von HEAD (`git merge-base --is-ancestor origin/main HEAD`).
4. Nach dem Merge gibt es genau einen weiteren Commit. Er ändert **nur** `tests/test_app_kamera_s011.py`.
5. `git diff origin/main HEAD --stat` zeigt nur die 4 F4-Dateien (`app.css`, `app.js`, `index.html`, `tests/test_app_kamera_s011.py`).
6. `git grep -n "chromium-1194" HEAD -- tests/test_app_kamera_s011.py` liefert keinen Treffer. Es gibt keinen fest verdrahteten Versionspfad mehr.
7. **Ohne** gesetztes `PLAYWRIGHT_BROWSERS_PATH` (`env -u PLAYWRIGHT_BROWSERS_PATH python3 -m unittest -v tests.test_app_kamera_s011`) laufen die Browsertests wirklich: 0 skipped, alle OK.
8. **Mit** `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` laufen dieselben Tests ebenfalls ohne Skip und OK.
9. Der neue statische Test für die Chromium-Suche besteht. Er wählt `chromium-1243` vor `chromium-999` (numerisch, nicht alphabetisch), ignoriert `chromium_headless_shell-*` und liefert für einen leeren Ordner `None`.
10. `python3 -m unittest discover -s tests` ergibt OK. Erwartet werden mindestens 216 (main) plus die F4-Tests plus 1 neuer, kein Fehler.
11. `cd cloudflare && node --test test/*.test.mjs` ergibt 10/10 pass.
12. Keine Änderung an `.github/workflows`, keine Secrets im Diff (Scan nach `sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`), keine Netzabrufe (Open Prices/eBay), kein `playwright install`.
13. Kein Push auf main, kein Merge des PRs, kein Force-Push. Der PR bleibt Draft.

## Testbefehle
```
cd /home/claude/schnapper
python3 -m unittest discover -s tests
env -u PLAYWRIGHT_BROWSERS_PATH python3 -m unittest -v tests.test_app_kamera_s011
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 -m unittest -v tests.test_app_kamera_s011
(cd cloudflare && node --test test/*.test.mjs)
git merge-tree --write-tree origin/main 38a469e   # mit Baum des Merge-Commits vergleichen: git rev-parse <merge>^{tree}
git diff origin/main HEAD --stat
```

## Erlaubte Pfade
- Merge-Commit: nur das, was `git merge origin/main` automatisch erzeugt (keine Handänderungen)
- Eigener Commit: **nur** `tests/test_app_kamera_s011.py`
- Übergabe: `/home/claude/handoff/20261023-0429/*`

Nicht erlaubt: `app/**` (inkl. `app.js`/`index.html`/`app.css`), `tests/test_app_sicherung_s010.py` und andere Testdateien, `team/**`, `.github/workflows/**`, `cloudflare/**`, alle anderen Team-Branches (#36, #39, #40, #44, #45), fremde PRs.

## Hinweise für COMMAND
- Push: `git push origin agent/master/20261022-2238` (Fast-Forward von 38a469e). Vorher prüfen, dass `origin/agent/master/20261022-2238` noch auf 38a469e steht.
- PR-Body von #41 per REST (`gh api -X PATCH repos/jefrey030/Schnapper/pulls/41`) um den Abschnitt „Update Lauf 20261023-0429“ ergänzen. GraphQL (`gh pr view`) ist gesperrt.
- Als Folgeschritt vormerken: dieselbe Chromium-Suche in `tests/test_app_sicherung_s010.py` (#40) und ggf. in den Browsertests von #39 übernehmen.
