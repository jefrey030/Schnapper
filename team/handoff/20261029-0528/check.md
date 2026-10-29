# CHECK – Lauf 20261029-0528

Start: Thu Oct 29 05:35:17 UTC 2026 · Ende: Thu Oct 29 05:38:04 UTC 2026

## Urteil: bestanden

Geprüft: Branch `agent/master/20261022-2238`, HEAD `175d7b7` (lokal, 1 Commit vor origin `6165af4`), origin/main `6dbe114`.

## Testzahlen (selbst ausgeführt)
- `python3 -m unittest tests.test_app_kamera_s011`: 28 Tests, OK, 0 Skips (Playwright mit vorinstalliertem Chromium, kein `playwright install`)
- `python3 -m unittest discover -s tests`: 244 Tests, OK, 0 Skips
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0, skipped 0

## Diff / Tabu / Secrets
- `git diff origin/agent/master/20261022-2238..HEAD`: nur `app/schnapper/web/app.js` (+9/−2) und `tests/test_app_kamera_s011.py` (+76). Beide Dateien sind erlaubt.
- `git diff origin/main...HEAD`: app.css, app.js, index.html und test_app_kamera_s011.py, alles aus dem bisherigen PR #41. Nichts unter `.github/`, kein ZENTNA, JERRY AL oder Beatmaster (grep, Exit 1). `web.py` ist nicht im Diff, die CSP ist also unverändert.
- Secret-Scan über den gesamten Diff gegen origin/main (`sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw(or)?d[=:]`): keine Treffer. Die einzigen grep-Treffer betrafen `innerHTML` in Test-Assertions (`assertNotIn`).
- Die Änderung in app.js liegt nur im neuen Modulzähler und in `barcodeSuchen()`. Kamera-Code, HTML, CSS und CSP sind unberührt.

## Akzeptanzkriterien
1. **Generationszähler: erfüllt.**
   - `let barcodeAbfrage = 0;` steht auf Modulebene, `const nr = ++barcodeAbfrage;` direkt nach `preventDefault()`.
   - `if (nr !== barcodeAbfrage) return;` steht nach `await fetch` und nach `await antwort.json()`. Danach läuft der Code bis zum Ende synchron, es gibt also kein weiteres Überholfenster.
   - Der `catch` schreibt nur bei `nr === barcodeAbfrage`. Damit sind veralteter Erfolg, HTTP-Fehler, Netzfehler und JSON-Fehler abgedeckt.
2. **Knopf: erfüllt.**
   - Im `finally` steht `if (nr === barcodeAbfrage) knopf.disabled = false;`. Ein `return` aus `try` läuft durch `finally`, gibt den Knopf aber bei einer veralteten Abfrage nicht frei.
   - T2 belegt, dass der Knopf nach der Antwort von A deaktiviert bleibt.
3. **T1 grün:** `test_kamera_treffer_waehrend_handsuche_neue_antwort_zuerst` prüft Lizenz B, B-Status, 0 Treffer, Knopf aktiv und Feld 4008400402222, und zwar sowohl nach B als auch nach A.
4. **T2 grün:** `..._alte_antwort_zuerst` prüft nach A: Lizenz leer, Status „Frage Ladenpreise ab …“, Knopf deaktiviert. Nach B wird B angezeigt.
5. **Gegenprobe: selbst ausgeführt.**
   - Die alte app.js (`git show origin/agent/master/20261022-2238:app/schnapper/web/app.js`) wurde eingespielt. Ergebnis: 28 Tests, FAILED (failures=4). Rot waren T1, T2 und T3 (T3 zweimal, Test und tearDown). Die übrigen 25 Tests blieben grün.
   - Danach `git checkout -- app/schnapper/web/app.js` ausgeführt. Der sha256-Vergleich mit der Fassung vorher war OK, `git status` ist sauber.
6. **Bestehende Tests grün:** 25 alte und 3 neue, also 28/28 ohne Skip. Die gesamte Suite hat 244 Tests (OK), Cloudflare 10/10.
7. **Handsuche unverändert:** Die Barcode-Bestandstests sind grün, die tearDown-Prüfungen (Konsole, Fremd-Requests) sind grün.
   - In T3 ist die erwartete Browsermeldung zum 429 gezielt geprüft und dann entfernt. Das ist sauber gelöst: Die Meldung wird exakt geprüft und nicht pauschal unterdrückt.
8. **Kein `innerHTML`: erfüllt.**
   - In app.js steht `innerHTML` nur im Kommentar in Zeile 2, unverändert gegenüber main.
   - `test_csp_unveraendert` ist grün, und es gibt keine neuen Abhängigkeiten.
9. **Nur erlaubte Dateien, nichts unter `.github/`, Secret-Scan leer: erfüllt** (siehe oben).
10. **Push: offen, nicht Aufgabe von BRAIN oder CHECK.** Der Commit ist lokal und ein reiner Fast-Forward auf origin `6165af4`, weil HEAD~1 = 6165af4 ist. COMMAND pusht ohne Force. PR #41 bleibt Draft.

## Planabweichung `knopf.disabled = false;` bei ungültiger Eingabe
**Bewertung: korrekt, harmlos und sinnvoll. Kein Fehler.**
- Ohne diese Zeile würde eine ungültige neue Eingabe den Zähler erhöhen und die laufende Abfrage A verfallen lassen. Das `finally` von A gibt den Knopf dann nicht mehr frei, und der Knopf bliebe dauerhaft gesperrt.
- Im Normalfall ist der Knopf dort ohnehin aktiv, die Zeile ändert also nichts.
- Praktisch erreichbar ist der Fall kaum:
  - Die Kamera schickt nur Codes ab, die `/^[0-9]{8,14}$/` erfüllen (app.js:310).
  - Enter wird bei deaktiviertem Standardknopf von HTML blockiert.
  - Erreichbar bleibt der Fall nur über ein fremdes `requestSubmit()` oder `submit`-Ereignis.
- Als Absicherung ist die Zeile trotzdem richtig. Sie passt zur Vorgabe in lead.md Punkt 2: Die neue Eingabe gilt.
- Hinweis: Kein Test deckt die Zeile ab. Das ist nicht blockierend.

## Logikprüfung des Zählers
- **Veraltete Antwort schreibt etwas?** Nein. Alle drei Schreibstellen (Erfolg, `!antwort.ok`, `catch`) liegen hinter einer Zählerprüfung ohne `await` dazwischen. Das Leeren von Treffern und Lizenz am Funktionsanfang macht nur die neue Abfrage selbst.
- **Kann der Knopf dauerhaft gesperrt bleiben?** Die jeweils neueste Abfrage erreicht immer ihr `finally` und gibt den Knopf frei, ebenso der Zweig mit ungültiger Eingabe. Gesperrt bliebe er nur, wenn `fetch` nie zurückkommt. Das gab es schon vorher, denn es gibt kein Zeitlimit. Das ist nicht Teil dieses Laufs.
- **Fehlerpfade:**
  - 429 auf die neueste Abfrage: Der Status zeigt `daten.fehler`, der Knopf wird frei.
  - Netzfehler oder JSON-Fehler auf die neueste Abfrage: Status „Server oder Preisquelle nicht erreichbar.“, der Knopf wird frei.
  - Dasselbe auf eine veraltete Abfrage: wird stumm verworfen (T3 belegt das für 429).
- **Restverhalten, kein Mangel:** Antwortet der Server auf B mit 429, weil A noch den Lock hält, sieht der Nutzer bei Feld B die 429-Meldung, und A wird verworfen. Das ist ehrlich, denn es ist der Status der angezeigten Abfrage, und der Nutzer kann erneut suchen.

## Mängel
Keine.
