# LEAD – Lauf 20261029-0829

## Aufgabe
- **F2 = S-009** „Angebot direkt in der App erfassen (Formular, POST-Endpunkt, CSV-Download)“, **Draft-PR #39**
- Branch: `agent/master/20261022-21` (bestehender Team-Branch), Ausgangskopf `a87a977`
- Wahlgrund: faire Rotation laut `team/runs/INDEX.md`. F2 lief zuletzt 20261029-0229 und ist damit am längsten unberührt (F1 0328, F6 0428, F4 0528, F3 0629, F5 0729). Dazu empfiehlt der letzte Bericht ausdrücklich F2/#39.
- Integration: `git merge-base --is-ancestor origin/main origin/agent/master/20261022-21` ergibt Exit 0. main 6dbe114 (#42, #43) ist schon enthalten, ein Merge ist **nicht** nötig. Ausgangsstand grün: `python3 -m unittest tests.test_app_erfassen_s009` ergibt 27/27 OK.

## Gefundener Mangel: Doppelklick legt das Angebot doppelt an
`app/schnapper/web/app.js:364-382` (`angebotSpeichern`) sperrt den Knopf `#angebot-knopf` während des Speicherns nicht und hat auch keine Sperre gegen ein zweites Absenden. Jedes `submit` schickt deshalb sofort einen eigenen `POST /api/angebot`. Die Formularfelder sind dabei noch gefüllt, weil `form.reset()` erst nach der Antwort läuft. Der Server vergibt jedes Mal eine neue Zufalls-ID (`web.py`, `_angebot_erfassen`, `"e-" + secrets.token_hex(4)`) und hängt das Angebot an (`Zustand.hinzufuegen`).

Zum Vergleich: `barcodeSuchen()` im selben File (`app.js:196` und `:222-223`) setzt `knopf.disabled = true` und gibt den Knopf im `finally` wieder frei. Beim Erfassen fehlt das.

**Reproduktion** (Playwright mit vorinstalliertem Chromium, Server `erstelle_server(BEISPIEL, port=0)`, nur 127.0.0.1):
1. Seite laden. Titel „Doppelt Rad“, Preis „10“ und Link „https://x.example/1“ eintragen.
2. `seite.locator('#angebot-form button[type=submit]').dblclick()`. Dasselbe passiert mit `form.requestSubmit(); form.requestSubmit();` in `evaluate`.
3. Ergebnis auf a87a977:
   - `#angebot-status`: „Gespeichert. Deine Liste hat jetzt **2** Angebote.“
   - `GET /api/angebote.csv` liefert Kopfzeile + **2 identische Zeilen** (`e-f1ecdd7a;Doppelt Rad;10.00;…` und `e-0ce8a0ec;Doppelt Rad;10.00;…`)
   - Die Trefferliste zeigt nur 1 Eintrag, weil die Suche Dubletten ausblendet. Der Nutzer sieht den Fehler also nicht, er steht aber im Export und im Preisverlauf.
   - Knopf direkt nach dem Klick: `disabled == False`

Das verletzt das AK „Erfasste Angebote als CSV … herunterladbar“: der Export enthält ein Angebot, das nie zweimal erfasst wurde, und die angezeigte Anzahl ist falsch. Auf dem Handy passiert das leicht durch doppeltes Tippen oder eine langsame Antwort.

## Umsetzungsvorgabe (klein, nur Client)
In `app/schnapper/web/app.js`, Funktion `angebotSpeichern`:
1. Ein Modul-Flag (z. B. `let angebotLaeuft = false;`) direkt vor der Funktion. Nach `ev.preventDefault()` gilt: Ist das Flag gesetzt, sofort `return`, ohne `fetch` und ohne den Status zu ändern. Ein deaktivierter Knopf allein reicht nicht, denn `requestSubmit()` und Enter im Feld lösen trotzdem `submit` aus.
2. Vor dem `fetch` das Flag setzen und `$("angebot-knopf").disabled = true` (Muster wie `barcodeSuchen`).
3. Ein `finally` setzt das Flag zurück und gibt den Knopf wieder frei, und zwar in **allen** Ausgängen: Erfolg, Fehlerantwort (`!antwort.ok`, frühes `return`) und `catch` (Server nicht erreichbar).
4. Sonst bleibt alles gleich: kein `innerHTML`, Header `X-Schnapper: 1`, gleiche Meldungen. Der Server bleibt unverändert, also kein serverseitiges Dubletten-Verbot (das wäre ein eigener Punkt).

## Akzeptanzkriterien
1. Ein Doppelklick (`dblclick()`) auf „Angebot hinzufügen“ mit gültigen Daten erzeugt genau **einen** `POST /api/angebot`. Danach enthält `GET /api/angebote.csv` genau Kopfzeile + 1 Datenzeile, und `#angebot-status` meldet „… jetzt 1 Angebot.“
2. Zwei direkt aufeinanderfolgende `form.requestSubmit()` in einem `evaluate` erzeugen ebenfalls genau ein Angebot (CSV: 1 Datenzeile). So ist belegt, dass das Flag wirkt und nicht nur der deaktivierte Knopf.
3. Während die Anfrage läuft, ist `#angebot-knopf` `disabled`. Der Test hält die Antwort dafür per `kontext.route`/`seite.route` zurück und lässt sie danach mit `route.continue_()` weiter. Nach der Antwort ist der Knopf wieder aktiv.
4. Nach einer Fehlerantwort (z. B. 422 bei Link `http://…` ohne https) ist der Knopf wieder aktiv, und ein danach korrigiertes Absenden wird gespeichert (CSV: 1 Datenzeile).
5. Nach „Server nicht erreichbar“ (Route mit `route.abort()`) erscheint die Meldung „Server nicht erreichbar …“, und der Knopf ist wieder aktiv.
6. Die Browsertests laufen ohne Konsolenfehler und `pageerror`, wie im bestehenden `test_ak8_…` (Meldungsliste leer), und blockieren alle Anfragen außer an den lokalen Server.
7. **Gegenprobe Pflicht:** Mit der alten `app/schnapper/web/app.js` aus `a87a977` (`git show a87a977:app/schnapper/web/app.js > app/schnapper/web/app.js`) schlagen mindestens die Tests zu AK 1 und 2 fehl (2 Datenzeilen bzw. „2 Angebote“). Danach wird die Datei zurückgesetzt und der sha256 gegen den Fix-Stand geprüft.
8. Alle bisherigen Tests in `tests/test_app_erfassen_s009.py` bleiben grün (vorher 27), und die neuen Browsertests werden **nicht** übersprungen (0 Skips, Chromium aus `/opt/pw-browsers` via `_finde_chromium`).
9. Die Gesamtsuite und die Cloudflare-Tests sind grün. Es gibt keinen Netzzugriff nach außen, kein `playwright install` und keine neuen Abhängigkeiten.
10. Genau ein Commit auf `agent/master/20261022-21`, nur die erlaubten Dateien, kein Force-Push, PR #39 bleibt Draft.

## Testbefehle
```
cd /home/claude/schnapper   # bzw. Worktree auf agent/master/20261022-21
python3 -m unittest tests.test_app_erfassen_s009 -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Gegenprobe (AK 7):
```
cp app/schnapper/web/app.js /tmp/…/app.js.fix && sha256sum app/schnapper/web/app.js
git show a87a977:app/schnapper/web/app.js > app/schnapper/web/app.js
python3 -m unittest tests.test_app_erfassen_s009   # muss FAILED zeigen
git checkout -- app/schnapper/web/app.js  (bzw. Fix-Kopie zurück) && sha256sum app/schnapper/web/app.js
```

## Erlaubte Dateien
- `app/schnapper/web/app.js` (nur `angebotSpeichern` + ein Flag direkt davor)
- `tests/test_app_erfassen_s009.py` (neue Testklasse/-methoden im bestehenden `Browser`-Muster)

Nicht anfassen: `web.py`, `index.html`, `app.css`, `.github/workflows`, `team/tasks.json`, fremde Branches.

## Hinweise für BRAIN/CHECK
- Playwright im Sync-Modus: Ein `time.sleep` im Route-Handler blockiert die Ereignisschleife. Für AK 3 die Route deshalb in einer Liste speichern, den Zustand des Knopfs prüfen und erst danach `route.continue_()` aufrufen.
- Der Server startet mit der Beispielliste. Das erste eigene Angebot verwirft sie, also ist „1 Datenzeile“ eindeutig.
