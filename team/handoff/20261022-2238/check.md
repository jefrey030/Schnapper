# CHECK – Lauf 20261022-2238 (F4 / S-011 Barcode per Kamera)

**Urteil: bestanden**

Geprüft wurde Branch `agent/master/20261022-2238`, Commit 38a469e, gegen origin/main e134cd0 (1 Commit voraus, nicht gepusht).

## Tests (selbst ausgeführt)
- `python3 -m unittest tests.test_app_kamera_s011 -v`: **10/10 OK**. Davon sind 7 Browsertests, die tatsächlich in Chromium /opt/pw-browsers gelaufen sind, 0 wurden übersprungen.
- `python3 -m unittest discover -s tests`: **200/200 OK** (190 bestehende plus 10 neue), kein „skipped“.
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**, 0 fail, 0 skipped.

## Diff und Dateigrenzen
- Geändert sind nur `app/schnapper/web/{index.html (+6), app.js (+90), app.css (+5)}` und die neue Datei `tests/test_app_kamera_s011.py`. Das sind 381 Zeilen, ausschließlich hinzugefügt.
- Nicht berührt: `web.py`, `team/`, `.github/workflows/`, `cloudflare/`, `tasks.json`, andere Tests, Service Worker und Manifest. Ein grep auf die Namensliste des Diffs fand nichts.
- Secret- und Tabu-Scan im Diff: Nach sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, ZENTNA, JERRY AL und Beatmaster wurde gesucht. Es gab **0 Treffer**.

## Kriterien
| AK | Ergebnis | Beleg |
|---|---|---|
| 1 Knopf, gUM erst auf Klick | erfüllt | index.html: `<button id="kamera-knopf" type="button" disabled>Mit Kamera scannen</button>`. getUserMedia wird nur in `kameraScannen()` aufgerufen, und die hängt nur am click-Listener. Der Test `starte()` prüft `__gum == 0` vor dem Klick. |
| 2 Treffer füllt Feld, lokale Suche | erfüllt | `test_ak1_ak2_ak3`: #barcode enthält „4008400402222“, es kommt genau ein POST /api/openprices mit `{"ean":"4008400402222"}`. Die Vorgabe `{video:{facingMode:"environment"},audio:false}` und die Formate werden geprüft. |
| Validierung vor Übernahme | erfüllt | `rawValue` wird per String/trim normalisiert und mit `/^[0-9]{8,14}$/` geprüft. Erst danach wird `$("barcode").value` gesetzt, ungültige Codes werden verworfen. |
| 3 Stopp nach Treffer | erfüllt | `kameraStoppen`: getTracks().forEach(stop), srcObject=null, hidden=true, beide Timer werden gelöscht. Der Test `alles_gestoppt()` prüft `__gestoppt == tracks.length`, dass alle Tracks `ended` sind, srcObject === null, den Bereich hidden und den Knopf wieder aktiv. |
| 4 Stopp nach Abbrechen | erfüllt | `test_ak4_abbrechen` deckt das ab, inklusive eines zweiten Starts mit erneutem sauberem Stopp (`__gum == 2`). |
| 5 Zeitlimit 20 s | erfüllt | `KAMERA_ZEITLIMIT = 20000` ist eine Konstante und nicht von außen überschreibbar. Im Test `page.clock`: nach 19 s läuft der Scan noch, nach 21 s ist er gestoppt und zeigt die Meldung „Kein Barcode erkannt – …“. |
| Stopp beim Verlassen | erfüllt (nur Code) | Es gibt Listener für `visibilitychange`→hidden und für `pagehide`, beide rufen `kameraStoppen` auf. Ein Browsertest dafür fehlt, der Plan verlangt aber keinen. |
| Kein Doppel-Scan | erfüllt | Ein `kamera.laeuft`-Guard plus `disabled` am Knopf während des Scans. Der Test prüft `disabled` im laufenden Scan. Nach einem Abbruch während getUserMedia stoppt die Prüfung `if (!kamera.laeuft)` den späten Stream. Beim Neustart wird der alte Erkennungslauf über `kamera.stream !== stream` beendet. |
| 6 Ohne API | erfüllt | `kameraVerfuegbar()` prüft BarcodeDetector, isSecureContext, mediaDevices.getUserMedia und die Formatschnittmenge. Zwei Tests: ohne Detector und ohne mediaDevices. Der Knopf bleibt dann disabled, der Hinweis ist sichtbar, es gibt keinen pageerror. Die Handeingabe sucht weiter (die Abfrage wird geprüft). |
| 7 NotAllowed/NotFound | erfüllt | `kameraFehler` liefert deutsche Meldungen. Tests: Meldung exakt, keine Tracks, srcObject null, Knopf wieder aktiv, Handeingabe funktioniert. Fehler werden abgefangen, es gibt kein console.error. |
| 8 Keine Fehler, 390 px | erfüllt | tearDown prüft für jeden Browsertest `meldungen == []` (console error und pageerror). Viewport 390x844, `scrollWidth <= 390` ist geprüft. |
| 9 Keine Fremd-Requests, keine Bilder | erfüllt | Route-Block für fremde URLs, `fremd == []` in jedem Test. Es gibt keine externe Bibliothek. Der statische Test schließt im Kamera-Abschnitt createObjectURL, toDataURL, toBlob, getImageData, localStorage, fetch( und console. aus. |
| 10 Kein innerHTML, textContent | erfüllt | `innerHTML` steht in app.js nur in einem Kommentar (Zeile 2). Alle Kamera-Texte werden per `textContent` gesetzt, die Template-String-Meldung ebenfalls über textContent. Die bisherigen Barcode-IDs sind unverändert, die Alt-Tests sind grün. |
| 11 CSP unverändert | erfüllt | `git diff origin/main -- app/schnapper/web.py` ist leer. `test_csp_unveraendert` vergleicht mit dem main-String und prüft, dass kein Permissions-Policy-Header existiert. |
| 12 Testzahlen | erfüllt | 200/200 (0 skipped) und 10/10, siehe oben. |

## Hinweise (keine Mängel, nicht blockierend)
- Theoretischer Race: Geht die Seite während eines offenen getUserMedia-Prompts auf hidden und wird der Knopf noch vor der Auflösung erneut geklickt, kann der erste Stream nicht gestoppt werden. Die Prüfung verwendet nur `laeuft`, keinen Generationszähler. Praktisch ist das kaum erreichbar, weil der Abbrechen-Knopf erst nach getUserMedia sichtbar wird. Härten ließe sich das mit einer Lauf-ID.
- Für visibilitychange und pagehide gibt es keinen Browsertest.
- Auf einem echten Gerät ist die Funktion ungetestet (Android Chrome). Unter iOS greift der Fallback.
