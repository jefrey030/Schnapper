# BRAIN – Lauf 20261029-1130 (F4 = S-011, PR #41)

## Stand
- Branch: `agent/master/20261022-2238`, Basis `175d7b7070b69d72559afca3fcea0af18fea91db`
- Commit: **`6fd9ffd94e9dd7ca714d017ec419826727860954`** (Fast-Forward auf 175d7b7, Elternteil geprüft). Nicht gepusht.
- Nachricht: „SCHNAPPER MASTER: S-011 Kamera-Scan beendet sich bei Track-Ende von außen“, mit Trailern.

## Geänderte Dateien (2 Dateien, +43 Zeilen, keine Löschungen)
- `app/schnapper/web/app.js` (+5, nur in `kameraScannen()` direkt nach `kamera.stream = stream;`): Für jeden Video-Track gibt es jetzt einen `ended`-Listener mit `{ once: true }`. Er ruft `kameraStoppen("Kamera wurde getrennt – Barcode bitte eintippen.")` auf, aber nur wenn `kamera.stream === stream` gilt. Ein veraltetes `ended` stört so keinen neueren Lauf. `kameraStoppen` ist unverändert. Keine Änderungen an CSP, HTML, CSS oder Server.
- `tests/test_app_kamera_s011.py` (+38, Klasse `Browser`), zwei neue Tests:
  - `test_track_ended_von_aussen` deckt AK1–3 und AK5 ab:
    - Nach `ended` ist der Bereich innerhalb von 1 s verborgen, und `alles_gestoppt()` ist erfüllt.
    - Der Status ist genau die Trenn-Meldung.
    - Der Fokus wandert von `kamera-abbrechen` zu `kamera-knopf`.
    - `__detect` bleibt nach 500 ms gleich, `abfragen == []`, das Barcode-Feld ist leer.
    - Ein Neustart ergibt `__gum == 2`. Danach Abbrechen und erneut `alles_gestoppt()`.
  - `test_veraltetes_track_ended_stoert_nicht` deckt AK4 ab:
    - Ablauf: Lauf 1 starten, abbrechen, Lauf 2 starten, dann `ended` auf `__tracks[0]` auslösen.
    - Erwartung: Der Bereich bleibt sichtbar, der Status ist nicht die Trenn-Meldung, und `__tracks[1].readyState === 'live'`.
    - Danach Abbrechen und `alles_gestoppt()`.
  - Die Fixtures MEDIEN und MEDIEN_VERZOEGERT sind unverändert. Die tearDown-Prüfungen greifen.

## Eigene Testergebnisse (vorinstalliertes Chromium, kein `playwright install`, kein Live-Netz)
| Suite | Ergebnis |
|---|---|
| Python gesamt `unittest discover -s tests` | vorher 244 OK, nachher **246 OK** (+2), 0 Fehler |
| Kamera-Modul `tests.test_app_kamera_s011 -v` | **30 OK** (vorher 28), 0 Skips |
| Einzeltests (die 2 neuen) | **2 OK** |
| Cloudflare `node --test test/*.test.mjs` | **10/10 pass**, 0 fail, 0 skipped |

`test_app_js` und `test_csp_unveraendert` sind grün (Teil der 30).

## Gegenprobe (Mutation führt zu Rot)
1. Den Listener abschalten (`if (0) t.addEventListener(...)`): `test_track_ended_von_aussen` ergibt **FAIL** („Zeitüberschreitung: … kamera-bereich').hidden“).
2. Den Wächter `kamera.stream === stream` durch `true` ersetzen: `test_veraltetes_track_ended_stoert_nicht` ergibt **FAIL** („True is not false“, der Bereich wurde verborgen).
3. Danach wiederhergestellt. Die sha256 von app.js stimmen überein:
   - Arbeitskopie: `cdaa3a4011c652cd6b42ca649413333d76ff88b1489509b208d432a495cd4d18`
   - `git show HEAD:app/schnapper/web/app.js`: derselbe Wert

## Offen für COMMAND
- Push (Fast-Forward) steht noch aus.
- Der Abschnitt „Update Lauf 20261029-1130“ in der PR-Beschreibung von #41 fehlt noch. BRAIN hat ihn nicht geschrieben, weil der Auftrag keinen Push und keine Netzaktionen erlaubt.
- Der PR bleibt Draft.
