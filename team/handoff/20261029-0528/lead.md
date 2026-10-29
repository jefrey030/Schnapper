# LEAD – Lauf 20261029-0528

## Aufgabe
F4 = S-011 „Barcode per Kamera scannen“, Draft-PR #41.

## Branch
`agent/master/20261022-2238` (bestehender Team-Branch von #41, Kopf `6165af4`).
Dieser Branch enthält origin/main 6dbe114 schon (`git merge-base --is-ancestor origin/main origin/agent/master/20261022-2238` ergibt Exit 0). Ein Merge ist nicht nötig. Kein rebase, kein force-push.

## Begründung der Wahl
- Faire Rotation laut INDEX.md: F4 war zuletzt um 20261028-2328 dran und ist damit am längsten unberührt.
- Ich habe einen echten, belegbaren Fehler im Kamera-Pfad gefunden, keine Kosmetik.
  - Bei einem Treffer ruft `kameraScannen()` `$("barcode-form").requestSubmit()` auf (app.js:307 auf dem Branch).
  - `requestSubmit()` ohne Submitter ignoriert, dass `#barcode-knopf` deaktiviert ist. Dieser Knopf ist in `barcodeSuchen()` (app.js:196) während einer laufenden Abfrage deaktiviert.
  - Vor S-011 gab es keinen zweiten Weg, eine Abfrage abzuschicken, solange eine lief: Bei deaktiviertem Standardknopf blockiert HTML die implizite Übermittlung per Enter. Der Fehler kommt also erst mit #41.
- Konkreter Ablauf des Fehlers:
  1. Der Nutzer tippt EAN A und klickt „Ladenpreise suchen“. Die Abfrage A läuft.
  2. Er scannt währenddessen per Kamera EAN B. Das Feld zeigt B, und eine zweite Abfrage startet.
  3. Der Server antwortet auf B mit 429 („Es läuft bereits eine Barcode-Abfrage“, `_openprices_lock`, web.py:201-203), oder die Antworten kommen in beliebiger Reihenfolge zurück.
  4. Die zuletzt eintreffende Antwort gewinnt. Kommt A später, stehen die Preise und die Lizenz von A unter dem Feld mit B: falsche Daten zum angezeigten Barcode.
  5. Zusätzlich setzt das `finally` der zuerst fertigen Abfrage den Knopf wieder auf aktiv, obwohl noch eine Abfrage läuft (app.js:223).

## Änderung (genau)
Datei `app/schnapper/web/app.js`, nur in `barcodeSuchen()` und einem neuen Modulzähler:
1. Neuer Zähler auf Modulebene, z. B. `let barcodeAbfrage = 0;` mit kurzem Kommentar. Er ist der Generationszähler für Barcode-Abfragen.
2. In `barcodeSuchen()` direkt nach `ev.preventDefault()`: `const nr = ++barcodeAbfrage;`. Damit verfällt auch eine noch laufende ältere Abfrage, wenn die neue Eingabe ungültig ist (die neue Eingabe gilt).
3. Nach `await fetch(...)` und nach `await antwort.json()` gilt: Ist `nr !== barcodeAbfrage`, wird sofort `return`ed. Es gibt dann keine Änderung an `#barcode-treffer`, `#barcode-lizenz` oder `#barcode-status`. Dasselbe gilt im `catch`: Eine veraltete Abfrage schreibt keinen Fehlerstatus.
4. Im `finally` gilt: `knopf.disabled = false` nur, wenn `nr === barcodeAbfrage`.
5. Sonst bleibt alles unverändert. Kein `innerHTML`, Ausgaben weiter per `textContent`/`replaceChildren`, Header `X-Schnapper` bleibt. Kamera-Code, CSP, HTML und CSS werden nicht angefasst.

Datei `tests/test_app_kamera_s011.py`: neue Browsertests in der bestehenden Playwright-Klasse (gleiches `setUp`/`oeffne`).
- Die Route `/api/openprices` darf für diese Tests mit einem eigenen Handler überschrieben werden: `self.seite.route(...)` vor `goto`, oder `unroute`+`route`. Der Handler legt die Route-Objekte zurück und erfüllt sie erst später aus dem Test (`route.fulfill(...)`). So lässt sich die Reihenfolge der Antworten steuern.
- Die Antworten werden über unterschiedliche `lizenz`-Texte unterschieden („LIZENZ-A“, „LIZENZ-B“) und über `treffer: []` gegenüber Status-Text.

**Test T1 „Kamera-Treffer während laufender Handsuche, neue Antwort zuerst“:**
1. `oeffne("treffer")`, Feld auf `12345678`, „Ladenpreise suchen“ klicken. Abfrage A hängt.
2. Kamera starten. Der Detektor liefert `4008400402222`, und die zweite Abfrage B hängt (`warte` auf 2 gespeicherte Routen).
3. Prüfen: Die Abfragen sind `[{"ean":"12345678"},{"ean":"4008400402222"}]`.
4. B erfüllen (Lizenz „LIZENZ-B“, 0 Treffer). Dann A erfüllen (Lizenz „LIZENZ-A“, Status 200).
5. Danach: `#barcode-lizenz` = „LIZENZ-B“, `#barcode-status` = „Keine passenden gemeldeten Preise gefunden.“, `#barcode-treffer` leer, `#barcode-knopf` aktiv, Feld = `4008400402222`.

**Test T2 „alte Antwort zuerst“:**
- Gleicher Aufbau, aber A zuerst erfüllen.
- Danach ist `#barcode-knopf` weiter deaktiviert, `#barcode-lizenz` leer, und der Status ist nicht von A überschrieben (weiter „Frage Ladenpreise ab …“).
- Dann B erfüllen. Danach Lizenz „LIZENZ-B“ und Knopf aktiv.

**Test T3 (optional, klein) „veraltete Abfrage mit Fehler“:**
- A wird mit `route.abort()` oder Status 429 und `{"fehler": "..."}` beantwortet, nachdem B schon beantwortet ist.
- Der Status von B bleibt stehen.

Gegenprobe (Pflicht für CHECK): Mit dem alten `barcodeSuchen()` (ohne Zähler) müssen T1 und T2 rot sein. Danach zurücksetzen.

## Akzeptanzkriterien
1. Ein Generationszähler sorgt dafür, dass nur die zuletzt gestartete Barcode-Abfrage `#barcode-treffer`, `#barcode-lizenz` und `#barcode-status` schreibt. Ältere Antworten (Erfolg, HTTP-Fehler, Netzfehler) werden verworfen.
2. `#barcode-knopf` wird nur von der zuletzt gestarteten Abfrage wieder aktiviert. Solange die neueste Abfrage läuft, bleibt er deaktiviert.
3. T1 ist grün: Erst kommt B, dann A. Angezeigt werden B-Lizenz und B-Status, Knopf aktiv, Feld = gescannter Code.
4. T2 ist grün: Erst kommt A, dann B. Nach A ist nichts von A sichtbar und der Knopf bleibt deaktiviert. Nach B wird B angezeigt und der Knopf ist aktiv.
5. Gegenprobe: Ohne die Änderung in app.js schlagen T1 und T2 fehl (vom CHECK selbst ausgeführt und danach zurückgesetzt).
6. Alle bestehenden Tests in `tests/test_app_kamera_s011.py` bleiben grün (bisher 25/25), ohne Skip, wenn Playwright und Chromium vorhanden sind. Die gesamte Python-Suite ist grün, die Cloudflare-Tests 10/10.
7. Die normale Handsuche (eine Abfrage) verhält sich unverändert, das deckt `test_ak1_ak2_ak3_treffer_fuellt_feld` und andere Barcode-Tests ab. Keine Konsolenfehler, keine Fremd-Requests (tearDown-Prüfungen).
8. Kein `innerHTML`. Die CSP in `web.py` bleibt unverändert (`test_csp_unveraendert` grün). Keine neuen Abhängigkeiten.
9. Der Diff berührt nur die erlaubten Dateien, nichts unter `.github/`. Secret-Scan im neuen Commit ohne Treffer.
10. Push als normaler Fast-Forward auf `agent/master/20261022-2238` (kein Force). PR #41 bleibt Draft.

## Testbefehle
```
cd /home/claude/schnapper
git checkout agent/master/20261022-2238 && git pull --ff-only origin agent/master/20261022-2238
python3 -m unittest tests.test_app_kamera_s011 -v      # Browsertests: Playwright + vorinstalliertes Chromium (_finde_chromium), KEIN `playwright install`
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Gegenprobe: `git stash push app/schnapper/web/app.js` (oder die alte Fassung per `git show HEAD:app/schnapper/web/app.js > …` einspielen), dann den Kamera-Test laufen lassen. T1/T2 müssen rot sein. Danach `git stash pop` und `git status` prüfen.
Secret-Scan: `git show HEAD | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|password='` muss leer sein.

## Erlaubte Dateien
- `app/schnapper/web/app.js` (nur `barcodeSuchen()` und ein neuer Zähler auf Modulebene)
- `tests/test_app_kamera_s011.py`

Alles andere ist tabu, ebenso STATUS.md und tasks.json. Diese pflegt COMMAND im Berichts-Worktree.

## Hinweis (nicht Teil dieses Laufs)
- Ein Kamera-Track mit `ended` (Kamera getrennt oder Berechtigung entzogen) wird nicht behandelt. Der Scan läuft bis zum 20-s-Zeitlimit mit totem Bild weiter. Das ist ein Kandidat für einen späteren F4-Lauf.
