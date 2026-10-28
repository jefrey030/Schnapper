# BRAIN – Lauf 20261028-1028

## Commit
- Branch: `agent/master/20261022-2238` (lokal, **nicht gepusht**)
- Basis-SHA: `a3fcfab` (= origin/agent/master/20261022-2238)
- Commit-SHA: `16e914b` – "SCHNAPPER MASTER: F4 Kamera – kein offener Stream bei Neustart während Berechtigungsdialog (S-011)", mit den beiden Attributionszeilen
- Genau ein Commit über a3fcfab.

## Geänderte Dateien (`git diff --numstat a3fcfab HEAD`)
| Datei | + | − |
|---|---|---|
| app/schnapper/web/app.js | 5 | 3 |
| tests/test_app_kamera_s011.py | 106 | 2 |

### app.js (nur im Kamera-Abschnitt)
- `kamera` hat jetzt das Feld `lauf: 0` (Generationszähler).
- `kameraStoppen()` führt `kamera.lauf++` aus.
- `kameraScannen()` setzt vor `getUserMedia` `const lauf = ++kamera.lauf;`.
  - `catch`: `kameraStoppen(...)` läuft nur noch, wenn `lauf === kamera.lauf` gilt.
  - Nach dem `await`: Bei `lauf !== kamera.lauf` werden die Tracks gestoppt und die Funktion endet (vorher stand dort `!kamera.laeuft`).
- Unverändert: `KAMERA_FORMATE`, `KAMERA_ZEITLIMIT`, Meldungstexte und die Zeile `getTracks().forEach((t) => t.stop())`. Es kam kein innerHTML, kein fetch( und kein console. hinzu.

### Tests
- Neue Konstante `MEDIEN_VERZOEGERT`: `getUserMedia` löst erst auf `__aufloesen(i)` auf bzw. lehnt erst auf `__ablehnen(i, name)` ab. Die Streams liegen in `__streams[i]`. `MEDIEN` und `DETEKTOR` sind unverändert.
- `oeffne()` hat den optionalen Parameter `verzoegert=False`. Das ist eine der 2 entfernten Zeilen, die andere ist die Auswahl der Medien-Zeile. Das Verhalten der alten Tests bleibt gleich.
- Neue Hilfen: `verstecken()` (visibilityState hidden + visibilitychange, danach wieder sichtbar), `kurz_warten()`, `neustart_waehrend_anfrage()`.
- 4 neue Tests in `Browser`:
  - `test_neustart_alter_stream_sofort_gestoppt` (AK1 + AK2): Ablauf Klick → hidden → Klick → `__aufloesen(0)`. Danach sind die Tracks von Stream 1 innerhalb von 3 s `ended`, `__gestoppt == 1`, der Bereich ist noch versteckt. Dann `__aufloesen(1)`: Bereich sichtbar, `srcObject === __streams[1]`, Stream live, Knopf deaktiviert. Nach „Abbrechen“ gilt gum 2, tracks 2, gestoppt 2 und `alles_gestoppt()`.
  - `test_neustart_alter_fehler_stoert_nicht` (AK3): Lauf 2 wird aufgelöst, danach Anfrage 1 mit `NotAllowedError` abgelehnt. Lauf 2 bleibt aktiv (Bereich sichtbar, srcObject = Stream 2, live, gestoppt 0, Knopf deaktiviert, Status ohne „Kamerazugriff verweigert“). Nach „Abbrechen“ ist `alles_gestoppt()` erfüllt.
  - `test_visibilitychange_beendet_scan` (AK4): Status „Kamera-Scan beendet.“ und `alles_gestoppt()`.
  - `test_pagehide_beendet_scan` (AK5): `alles_gestoppt()`.

## Eigene Testergebnisse
- `python3 -m unittest -v tests.test_app_kamera_s011`: **Ran 15 tests, OK**. Das sind 11 alte und 4 neue Tests, alle Browsertests liefen ohne Skip (jeder Test meldet „ok“).
- `python3 -m unittest discover -s tests`: **Ran 231 tests in 20.2s, OK**. Das sind 227 + 4. Die Ausgabe zeigt kein „skipped“, also 0 Skips.
- `cd cloudflare && node --test test/*.test.mjs`: **tests 10, pass 10, fail 0**.
- `git diff origin/main --stat -- app/schnapper/web.py`: leer, die CSP ist also unverändert.
- Im Diff gibt es keine Tabu-Begriffe und keine Secrets (grep nach zentna/jerry/beatmaster/secret/token: kein Treffer in +/−-Zeilen).

## Gegenprobe (AK6)
Vorgehen: eine Scratch-Kopie des Arbeitsbaums ohne .git. Darin habe ich `app/schnapper/web/app.js` durch `git show a3fcfab:app/schnapper/web/app.js` ersetzt (mit `cmp` als identisch geprüft). Die neuen Tests blieben drin.
Pfad: `/tmp/claude-0/-home-claude-schnapper/63d452f4-d5a4-50e3-b963-a8a41bff3de9/scratchpad/gegenprobe`, Log: `.../scratchpad/gegenprobe.log`.
```
test_neustart_alter_fehler_stoert_nicht ... FAIL
test_neustart_alter_stream_sofort_gestoppt ... FAIL
FAIL: test_neustart_alter_fehler_stoert_nicht
AssertionError: True is not false
FAIL: test_neustart_alter_stream_sofort_gestoppt
AssertionError: Zeitüberschreitung: window.__streams[0].getTracks().every((t) => t.readyState === 'ended')
Ran 15 tests in 13.507s
FAILED (failures=2)
```
Mit dem alten Code bleibt Stream 1 offen (AK1-Test schlägt fehl). Außerdem stoppt der veraltete NotAllowedError Lauf 2 (AK3-Test: der Bereich ist versteckt). Die Tests für visibilitychange und pagehide laufen auch mit dem alten Code grün. Das ist erwartet, denn sie sichern bestehendes Verhalten ab.

## Offene Punkte
- Kein Push. Das übernimmt laut lead.md COMMAND.
- Der PR-Body von #41 erwähnt noch „Für visibilitychange/pagehide gibt es keinen Browsertest“ und sollte angepasst werden. BRAIN hat ihn nicht geändert.
- Nicht umgesetzt (laut lead.md nicht blockierend): `upc_e` in `KAMERA_FORMATE`, #45 Nicht-String-URL, Bericht zu 2666d8b.
- `verstecken()` simuliert den Hintergrund per `Object.defineProperty(document, 'visibilityState', …)`. Einen echten Tab-Wechsel im Browser habe ich nicht getestet.
- Am Rande: LEAD nannte für discover „je 1 Skip“. In meinem Lauf gab es 0 Skips. Den Grund habe ich nicht untersucht, vermutlich ist hier Chromium bzw. die Umgebung vorhanden.
