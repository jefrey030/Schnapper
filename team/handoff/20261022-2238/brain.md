# BRAIN – Lauf 20261022-2238 (F4 / S-011 Barcode per Kamera)

**Branch:** `agent/master/20261022-2238` (von origin/main e134cd0), nicht gepusht.
**Commit:** `38a469e` – SCHNAPPER MASTER: F4 (S-011) Barcode per Kamera scannen (BarcodeDetector)

## Geänderte Dateien
- `app/schnapper/web/index.html` (+6): #kamera-knopf (disabled), #kamera-bereich (hidden) mit #kamera-bild und #kamera-abbrechen, #kamera-status (aria-live)
- `app/schnapper/web/app.js` (+90): KAMERA_FORMATE, KAMERA_ZEITLIMIT = 20000, kameraFormate, kameraVerfuegbar, kameraStoppen (idempotent), kameraFehler, kameraScannen, Listener in DOMContentLoaded (Klick, Abbrechen, visibilitychange, pagehide)
- `app/schnapper/web/app.css` (+5): Knopf- und Videolayout (`width:100%; max-height:40vh; object-fit:cover`)
- neu `tests/test_app_kamera_s011.py`: 3 statische und 7 Browsertests (Chromium /opt/pw-browsers, 390x844, simulierte Kamera und simulierter Detector per add_init_script, fremde URLs geblockt, /api/openprices per page.route lokal beantwortet)

## Testergebnisse
- `python3 -m unittest tests.test_app_kamera_s011 -v`: 10/10 OK (Browsertests laufen wirklich, 0 übersprungen)
- `python3 -m unittest discover -s tests`: **200/200 OK** (190 + 10 neu), 0 skipped
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**, 0 fail

## CSP
**Nicht geändert.** Beleg: `git diff origin/main -- app/schnapper/web.py` ist leer. Der Test `test_csp_unveraendert` vergleicht die CSP mit dem main-Stand und prüft, dass kein Permissions-Policy-Header existiert. Unter der echten CSP (`default-src 'none'`, kein media-src) spielt das Video mit `srcObject = MediaStream` ab: `video.play()` löst auf, detect läuft. Dabei gibt es keine Konsolenfehler und keine pageerrors, denn tearDown prüft `meldungen == []`.

## Abdeckung der Akzeptanzkriterien
- AK1: Knopftext geprüft, `__gum == 0` vor dem Klick
- AK2: Treffer „4008400402222“ in #barcode, POST /api/openprices mit `{"ean": "4008400402222"}`, getUserMedia-Vorgabe `{video:{facingMode:"environment"}, audio:false}`, Formate `["ean_13","ean_8","upc_a"]`
- AK3/4/5: `__gestoppt == Anzahl Tracks`, alle `readyState == "ended"`, `srcObject === null`, Bereich hidden, Knopf wieder aktiv. Das gilt nach Treffer, nach Abbrechen (inklusive zweitem Start) und nach dem Zeitlimit. Beim Zeitlimit: Nach 19 s läuft der Scan noch, nach 21 s ist er beendet (page.clock) und zeigt die Meldung „Kein Barcode erkannt …“.
- AK6: ohne BarcodeDetector bzw. ohne mediaDevices ist der Knopf disabled und der Hinweis sichtbar. Die Handeingabe sucht weiter.
- AK7: NotAllowedError und NotFoundError zeigen die deutschen Meldungen. Es wird kein Track erzeugt, der Knopf ist wieder aktiv, die Handeingabe funktioniert.
- AK8/9: in allen Browsertests sind Konsolenfehler, pageerrors und `fremd` leer, `scrollWidth <= 390`
- AK10: Kein innerHTML. Der Kamera-Abschnitt enthält kein createObjectURL, toDataURL, toBlob, getImageData, localStorage, fetch und console. Bestehende Barcode-Tests sind grün.

## Abweichungen vom Plan
- Erkennung per `setTimeout(…, 200)` statt rAF (laut Plan erlaubt).
- Zusätzlich gemappt: `SecurityError` wird wie NotAllowedError behandelt, `OverconstrainedError` wie NotFoundError. Alle übrigen Fehler erhalten die allgemeine Meldung „Kamera konnte nicht gestartet werden – Barcode bitte eintippen.“
- `kameraVerfuegbar()` ist async, weil `getSupportedFormats()` ein Promise liefert. Ist die Schnittmenge leer, gilt der Scan als „nicht unterstützt“.
- Bei Treffer lautet die Statusmeldung „Barcode erkannt: <code>“. Bei Abbrechen lautet sie „Kamera-Scan abgebrochen.“, bei visibilitychange „Kamera-Scan beendet.“
- `/api/openprices` wird im Browsertest per page.route beantwortet (200, leere Treffer), damit der lokale Server nicht nach außen fragt.

## Offene Punkte
- Auf einem echten Gerät ungetestet (Android Chrome mit nativem BarcodeDetector, echte Kamera, Erkennungsqualität, Rückkamera-Auswahl). iOS Safari hat keinen BarcodeDetector, dort greift der Fallback mit deaktiviertem Knopf.
- Der Kamerazugriff braucht einen Secure Context. Über eine LAN-IP per http erscheint deshalb „nicht unterstützt“, localhost und https funktionieren.
- PR noch nicht angelegt (kein Push laut Sperre). Konflikt-Hinweis für den PR: #28/#29/#30 sowie #36/#39/#40 ändern ebenfalls `app/schnapper/web*`.
