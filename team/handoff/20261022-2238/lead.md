# LEAD – Plan Lauf 20261022-2238 (UTC)

**Aufgabe:** F4 = S-011 „Barcode per Kamera scannen (BarcodeDetector)“. Quelle: tasks.json aus `origin/agent/master/20261022-20` (PR #36), Status open, von Jefrey freigegeben.
**Begründung:** F1–F3 liegen als Draft-PRs #36/#39/#40 vor, main e134cd0 ist grün (190/190, 10/10). F4 ist der nächste freigegebene Punkt. Er läuft rein clientseitig und braucht keine Zugangsdaten. F5 (S-012) folgt danach, F6 ist durch den fehlenden eBay-Schlüssel blockiert.
**Branch:** `agent/master/20261022-2238`, neu von `origin/main` (e134cd0). Nicht auf #36/#39/#40 aufbauen.

## Umsetzung (BRAIN)
1. `index.html`, in `#barcode-form` unter `.barcode-zeile`:
   - `<button id="kamera-knopf" type="button" disabled>Mit Kamera scannen</button>`
   - `<div id="kamera-bereich" hidden>` mit `<video id="kamera-bild" muted playsinline></video>`
   - `<button id="kamera-abbrechen" type="button">Abbrechen</button>`
   - `<p id="kamera-status" class="status" aria-live="polite"></p>`
2. `app.js`:
   - Neue Konstanten: `const KAMERA_FORMATE = ["ean_13", "ean_8", "upc_a"];` und `const KAMERA_ZEITLIMIT = 20000;`.
   - Neue Funktion `kameraVerfuegbar()`. Sie prüft `"BarcodeDetector" in window`, `navigator.mediaDevices?.getUserMedia` und `window.isSecureContext`. Optional kommt `BarcodeDetector.getSupportedFormats()` dazu, mit Schnittmenge zu KAMERA_FORMATE.
     - Beim DOMContentLoaded: Ist die Prüfung erfolgreich, wird `disabled` entfernt.
     - Sonst bleibt der Knopf `disabled` und `kamera-status` zeigt: „Kamera-Scan wird von diesem Browser nicht unterstützt – bitte Barcode eintippen.“
   - Neue Funktion `async kameraScannen()`:
     - `getUserMedia({video:{facingMode:"environment"}, audio:false})` wird erst auf Knopfdruck aufgerufen.
     - Danach `video.srcObject = stream` und `await video.play()`.
     - Erkennung mit `new BarcodeDetector({formats})`. Schleife per `requestAnimationFrame` oder `setTimeout(…, 200)` mit `detector.detect(video)`.
     - Der erste Treffer, dessen `rawValue` auf `/^[0-9]{8,14}$/` passt, wird übernommen: `$("barcode").value = code`, dann `kameraStoppen()`, dann `$("barcode-form").requestSubmit()`. Die Suche läuft nur gegen den lokalen Server.
   - Neue Funktion `kameraStoppen(meldung)`. Sie muss idempotent sein:
     - `stream.getTracks().forEach(t => t.stop())`
     - `video.srcObject = null`, Timer bzw. rAF löschen
     - `kamera-bereich` wird `hidden`, `stream = null`
     - Statusmeldung per `textContent` setzen
   - `kameraStoppen` wird aufgerufen bei Treffer, Abbrechen-Klick und Zeitlimit von 20 s („Kein Barcode erkannt – bitte erneut versuchen oder eintippen.“). Zusätzlich bei `visibilitychange` auf hidden und `pagehide`.
   - Fehler bei getUserMedia, nach `err.name`:
     - `NotAllowedError`: „Kamerazugriff verweigert – Barcode bitte eintippen.“
     - `NotFoundError`: „Keine Kamera gefunden – Barcode bitte eintippen.“
     - Sonst gibt es eine allgemeine Meldung.
     - Kein `console.error` und keine unbehandelte Promise-Ablehnung.
   - Während eines laufenden Scans ist der Knopf deaktiviert, damit kein Doppelstart möglich ist.
   - Es werden keine Frames gespeichert: kein Canvas-Export, kein fetch mit Bilddaten, kein `localStorage` für Bilder.
3. `app.css`: wenige Zeilen für `#kamera-bild`, etwa `width:100%; max-height:40vh; object-fit:cover`. Der Inhalt muss bei 390 px ohne horizontales Scrollen passen.
4. **CSP:** Voraussichtlich ist **keine Änderung** nötig.
   - `srcObject = MediaStream` löst keinen Fetch aus und unterliegt damit nicht `media-src`. Es gibt keine blob:-URL, weil `URL.createObjectURL(stream)` verboten ist.
   - Einen Permissions-Policy-Header gibt es in web.py nicht (SICHERHEIT hat nur CSP, nosniff, Referrer, Cache). Der Default erlaubt die Kamera für die eigene Herkunft, also wird **kein** neuer Header ergänzt.
   - Nur falls der Browsertest unter der echten CSP nachweislich ein Abspielen blockiert, ist diese Änderung in `app/schnapper/web.py` erlaubt: in SICHERHEIT `"img-src 'self' data:; "` → `"img-src 'self' data:; media-src 'self' mediastream:; "`. Die Änderung muss im PR mit Konsolen-Beleg begründet werden. Der CSP-Test der Datei ist dann anzupassen.
5. Neuer Test: `tests/test_app_kamera_s011.py`, aufgebaut wie `test_app_sicherung_s010.py` auf `origin/agent/master/20261022-22` (Server port=0, 390x844, Route-Block für fremde URLs, `warte()` mit Python-Polling statt wait_for_function, weil die CSP eval blockiert).
   - **Simulation per `add_init_script`:**
     - `window.BarcodeDetector`: Klasse mit `getSupportedFormats()`. `detect()` liefert beim 2. Aufruf `[{rawValue:"4008400402222", format:"ean_13"}]`.
     - `navigator.mediaDevices.getUserMedia`: liefert `canvas.captureStream()`. `track.stop` wird umwickelt und zählt in `window.__gestoppt`, Aufrufe zählen in `window.__gum`.
   - **Varianten:**
     - (a) Treffer füllt das Feld.
     - (b) Abbrechen.
     - (c) Zeitlimit: `detect` liefert immer `[]`. Im Test vor `goto` `page.clock.install()` aufrufen, nach dem Klick `page.clock.run_for(21000)`. KAMERA_ZEITLIMIT wird nicht von außen überschreibbar gemacht.
     - (d) Kein BarcodeDetector: Knopf disabled plus Meldung.
     - (e) getUserMedia wirft `NotAllowedError`: Meldung, Handeingabe weiter möglich.

## Akzeptanzkriterien (CHECK prüft jedes einzeln)
1. Der Knopf `#kamera-knopf` mit dem Text „Mit Kamera scannen“ ist vorhanden. getUserMedia wird erst nach Klick aufgerufen: Nach dem Laden gilt `__gum == 0`.
2. Mit simuliertem Detector und simuliertem Stream steht nach dem Klick „4008400402222“ in `#barcode`, die lokale Barcode-Suche startet.
3. Nach einem Treffer sind alle Tracks gestoppt (`__gestoppt == Anzahl Tracks`, `readyState == "ended"`), `video.srcObject === null` und `#kamera-bereich` ist hidden.
4. Gleiches gilt nach Klick auf „Abbrechen“.
5. Gleiches gilt nach dem Zeitlimit von 20 s, zusätzlich erscheint die Meldung „Kein Barcode erkannt …“.
6. Ohne `BarcodeDetector` (oder ohne mediaDevices): Der Knopf ist `disabled`, der Hinweistext ist sichtbar, kein pageerror. `#barcode` bleibt eintippbar und die Suche funktioniert.
7. Bei `NotAllowedError` und `NotFoundError` erscheint eine klare deutsche Meldung, es bleibt kein Stream offen und der Knopf ist wieder aktiv.
8. In allen Browsertests gibt es keine Konsolenfehler und keine pageerrors. Viewport 390x844, kein horizontales Scrollen (`scrollWidth <= 390`).
9. Es gibt keine externen Requests (`fremd == []`), keine externe Bibliothek, kein Upload oder Speichern von Bildern.
10. In app.js gibt es kein `innerHTML`, alle Texte werden über `textContent` gesetzt. Die bisherigen Barcode-IDs und Handeingabe-Tests bleiben unverändert grün.
11. Die CSP ist unverändert. Der statische Test vergleicht sie mit main. Ausnahme ist nur die unter Punkt 4 genannte Zeile, und nur mit Beleg.
12. Tests:
    - `python3 -m unittest discover -s tests`: alle OK (190 + neue), die Browsertests laufen tatsächlich und werden nicht übersprungen.
    - `cd cloudflare && node --test test/*.test.mjs`: 10/10.

## Testbefehle
- `python3 -m unittest discover -s tests`
- `python3 -m unittest tests.test_app_kamera_s011 -v`
- `cd cloudflare && node --test test/*.test.mjs`
- Chromium: `/opt/pw-browsers/chromium-1194/chrome-linux/chrome`. **Kein** `playwright install` und kein Download.

## Dateigrenzen
- **Erlaubt:**
  - `app/schnapper/web/index.html`
  - `app/schnapper/web/app.js`
  - `app/schnapper/web/app.css`
  - neu `tests/test_app_kamera_s011.py`
- **Nur mit Beleg:** `app/schnapper/web.py`, ausschließlich die CSP-Zeile aus Punkt 4.
- **Verboten:**
  - `team/tasks.json`, `team/handoff/` (nie committen), `.github/workflows/`, `cloudflare/`
  - andere Tests
  - Service-Worker- oder Manifest-Änderungen
- Kein Commit von Secrets, kein Force-Push. Der PR wird als Draft angelegt und nennt den Konflikt-Hinweis zu #28/#29/#30 sowie #36/#39/#40 (alle ändern `app/schnapper/web*`).
