# LEAD – Lauf 20261029-1130

## Aufgabe
- **F4 = S-011** (Barcode per Kamera), Draft-PR **#41**
- Branch zum Fortsetzen: `agent/master/20261022-2238`, Kopf `175d7b7070b69d72559afca3fcea0af18fea91db`
- Wahlgrund: Rotation laut INDEX.md. F4 lief zuletzt 20261029-0528 und ist damit der älteste F-Punkt. Der Preflight nennt ihn ebenfalls als nächsten.
- Mergebarkeit: `git merge-base --is-ancestor origin/main FETCH_HEAD` ergibt Exit 0, origin/main 6dbe114 ist also enthalten. `git merge-tree --write-tree origin/main FETCH_HEAD` ergibt Exit 0, es gibt keinen Konflikt.
- Ausgangsstand: `python3 -m unittest tests.test_app_kamera_s011` ergibt 28 OK (geprüft auf 175d7b7).

## Problem: Kamera fällt während des Scans weg, und die App merkt es nicht
Wenn der Video-Track endet, ohne dass die App ihn selbst stoppt, reagiert der Code nicht. Das passiert etwa, wenn Android die Berechtigung entzieht, eine andere App die Kamera übernimmt oder eine USB-Kamera abgezogen wird. In allen diesen Fällen feuert `MediaStreamTrack` das Ereignis `ended`.

Die Folgen:
- Der Scan läuft mit totem Bild bis zu 20 s weiter.
- Der Status zeigt weiter „Barcode vor die Kamera halten …“.
- Der Videobereich und „Abbrechen“ bleiben sichtbar, der Startknopf bleibt gesperrt.
- Erst das Zeitlimit beendet den Scan, und zwar mit einer falschen Meldung („Kein Barcode erkannt“).

Das verletzt die Kriterien „klare Meldung“ und „Kamera sofort stoppen bzw. Zustand sofort aufräumen“.

**Beleg (Code):**
- `app/schnapper/web/app.js:293` setzt `kamera.stream = stream;`. Danach registriert der Code an keiner Stelle einen Listener für `ended` oder `onended` (geprüft mit `git show FETCH_HEAD:app/schnapper/web/app.js | grep -n ended`: kein Treffer).
- `app/schnapper/web/app.js:304–321`: Das Zeitlimit und die `runde`-Schleife prüfen nur `kamera.stream !== stream`, nie `track.readyState`.
- Tests: Auch `tests/test_app_kamera_s011.py` enthält keinen Fall, in dem `ended` von außen ausgelöst wird.

**Beleg (lokale Probe, nur 127.0.0.1, Playwright mit dem vorinstallierten Chromium 1243):**
- Der Scan lief mit Detektor „leer“, dann folgte `window.__tracks[0].dispatchEvent(new Event('ended'))` und 1 s Warten.
- Ergebnis: `bereich hidden: False | status: Barcode vor die Kamera halten … | detect-Runden nach ended: 5 | abbrechen sichtbar: True`.
- Probeskript: `/tmp/claude-0/-home-claude-schnapper/61f8c763-b503-5a73-949a-b04b7a3690cc/scratchpad/probe.py`, nur Wegwerf-Werkzeug, nicht ins Repo übernehmen.

Früher behoben (laut INDEX.md) und hier nicht betroffen:
- Lauf-ID beim Neustart
- Abbruch während der Formatabfrage
- visibilitychange und pagehide
- Abbrechen-Knopf während des Starts
- Fokus
- Generationszähler in der Handsuche

Den Fall „Track endet von außen“ hat noch kein Lauf behandelt.

## Lösungsskizze
1. In `kameraScannen()` direkt nach `kamera.stream = stream;` (app.js:293) folgenden Code einfügen:
   ```js
   for (const t of stream.getVideoTracks()) {
     t.addEventListener("ended", () => {
       if (kamera.stream === stream) kameraStoppen("Kamera wurde getrennt – Barcode bitte eintippen.");
     }, { once: true });
   }
   ```
   Der Wächter `kamera.stream === stream` sorgt dafür, dass ein später feuerndes `ended` eines alten oder abgebrochenen Streams einen neueren Lauf nicht stört. Er greift auch, wenn der Track während der Formatabfrage oder während `video.play()` endet, denn `kamera.stream` ist dann schon gesetzt.
2. `kameraStoppen` bleibt unverändert. Es ruft auch für den schon beendeten Track `stop()` auf, das ist harmlos, räumt alles auf und gibt den Fokus zurück.
3. Keine Änderungen an CSP, HTML, CSS oder Server.

## Akzeptanzkriterien
1. Läuft der Scan (Videobereich sichtbar, `__detect > 0`) und endet der Track von außen (`window.__tracks[0].dispatchEvent(new Event('ended'))`), dann gilt innerhalb von höchstens 1 s ohne Uhr-Attrappe:
   - `alles_gestoppt()` ist erfüllt: alle Tracks gestoppt, `srcObject === null`, Bereich verborgen, Abbrechen unsichtbar, Startknopf frei.
   - Der Status lautet genau „Kamera wurde getrennt – Barcode bitte eintippen.“
2. Danach gibt es keine weiteren `detect`-Aufrufe (`__detect` bleibt nach weiteren 500 ms gleich), keine `/api/openprices`-Abfrage (`self.abfragen == []`), und das Barcode-Feld bleibt leer.
3. Ein Neustart nach dem Wegfall funktioniert: Ein Klick auf „Mit Kamera scannen“ ergibt `__gum == 2` und einen sichtbaren Bereich. Abbrechen stoppt wieder sauber (`alles_gestoppt()`).
4. Ein veraltetes `ended` stört nicht:
   - Ablauf: Lauf 1 starten, abbrechen, Lauf 2 starten (Bereich sichtbar), dann `ended` auf dem Track von Lauf 1 auslösen (`window.__tracks[0]`).
   - Erwartung: Lauf 2 läuft weiter, der Bereich bleibt sichtbar, der Status ist nicht die Trenn-Meldung, und der Track von Lauf 2 ist nicht gestoppt (`window.__tracks[1].readyState === 'live'`).
   - Danach wird abgebrochen, und es folgt `alles_gestoppt()`.
5. Fokus: Lag der Fokus beim Wegfall auf „Abbrechen“, liegt er danach auf `#kamera-knopf`. Das ist bestehendes Verhalten von `kameraStoppen` und wird im Test aus AK1 mitgeprüft.
6. Der statische Test `test_app_js` bleibt grün: kein `innerHTML`, `fetch(` oder `console.` im Kamera-Block, keine URL.
7. Die CSP bleibt unverändert (`test_csp_unveraendert` grün).
8. Neue Tests stehen in `tests/test_app_kamera_s011.py` in der Klasse `Browser`: mindestens `test_track_ended_von_aussen` (AK1–3, 5) und `test_veraltetes_track_ended_stoert_nicht` (AK4). Sie nutzen die vorhandenen Hilfen (`oeffne`, `starte`, `warte`, `alles_gestoppt`, `kurz_warten`). Die Fixtures MEDIEN und MEDIEN_VERZOEGERT bleiben unverändert, und die tearDown-Prüfungen (keine Fremdanfragen, keine Konsolenfehler) greifen.
9. **Gegenprobe/Mutation (Pflicht):**
   - Den neuen `ended`-Listener in app.js vorübergehend auskommentieren. Dann muss `test_track_ended_von_aussen` **FAIL** melden.
   - Zweite Mutation: Den Wächter `kamera.stream === stream` durch `true` ersetzen. Dann muss `test_veraltetes_track_ended_stoert_nicht` **FAIL** melden.
   - Danach alles zurücksetzen und die sha256 von app.js mit dem Commit-Stand vergleichen.
10. Gesamtsuiten grün, 0 Skips im Kamera-Modul:
    - Kamera-Modul: 28 → mindestens 30 OK
    - Python-Suite: Ausgangszahl auf dem Branch selbst ermitteln, plus die neuen Tests
    - Cloudflare: 10/10
11. Ein Commit auf `agent/master/20261022-2238`, nur Fast-Forward, kein Force-Push (Push durch COMMAND nach „bestanden“). Den Abschnitt „Update Lauf 20261029-1130“ per REST an die PR-Beschreibung von #41 anhängen. Der PR bleibt Draft.

## Testbefehle
```
cd /home/claude/schnapper   # auf Branch agent/master/20261022-2238 (175d7b7)
python3 -m unittest tests.test_app_kamera_s011 -v
python3 -m unittest tests.test_app_kamera_s011.Browser.test_track_ended_von_aussen tests.test_app_kamera_s011.Browser.test_veraltetes_track_ended_stoert_nicht -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
- Playwright nutzt das vorinstallierte Chromium. `_finde_chromium()` findet `/opt/pw-browsers/chromium-1243` automatisch. **Kein `playwright install`.**
- Kein Live-Netz. Die Tests blockieren Fremd-URLs und fangen `/api/openprices` ab.

## Grenzen
- Ändern dürfen BRAIN und CHECK **nur** diese beiden Dateien:
  - `app/schnapper/web/app.js` (nur in `kameraScannen()`, wenige Zeilen)
  - `tests/test_app_kamera_s011.py` (nur neue Tests, ggf. ein kleiner Helfer)
- Tabu:
  - `index.html`, `app.css`, `web.py`/CSP und `.github/workflows`
  - andere PRs und Branches
  - Secrets
  - alles von ZENTNA, JERRY AL und Beatmaster
- 0 € Budget, keine neuen Abhängigkeiten.
- Keinen Code aus dem Probeskript im Scratchpad übernehmen, es ist nur ein Beleg.
