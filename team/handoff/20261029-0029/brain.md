# BRAIN – Lauf 20261029-0029

## Branch / Commit
- Branch: `agent/master/20261022-22` (PR #40), ausgecheckt mit `git checkout -B … origin/…`, Basis 33a9487
- origin/main = 6dbe114 (unverändert), deshalb kein Merge
- Commit: `87eebba8e310777d1dbc4b169eea62f009464393`. „SCHNAPPER MASTER: F3 Preisalarm nur anlegen, wenn er wiederherstellbar ist (S-010)“
- Nicht gepusht.

## Geänderte Dateien
| Datei | + | - |
|---|---|---|
| app/schnapper/web/app.js | 29 | 13 |
| tests/test_app_sicherung_s010.py | 72 | 0 |

## Umsetzung
- `zahlWert`, `maxPreisOk`, `minRabattOk` und die neue `function alarmFehler(w)` liegen jetzt auf oberster Ebene. Die Regex-Zeichenketten sind wortgleich geblieben. Rückgabe: `null` oder `"text"`, `"max_preis"`, `"min_rabatt"`, `"max_preis/min_rabatt"`, `"zustand"`.
- `sicherungPruefen()`: erst `kein Objekt`, dann `alarmFehler(w)`, danach `angelegt_am`. Reihenfolge und Meldungen sind unverändert.
- `alarmAnlegen()`: `alarmFehler(w)` läuft direkt nach `aktuellerWunsch()`, also vor der Dublettenprüfung und vor `fetch`. Bei einem Fehler kommt „Preisalarm nicht angelegt: …“ (Texte laut Plan, über `textContent`) in `#status`. Es gibt dann keinen Request und keinen Speichervorgang.
- Neue Tests:
  - `Statisch.test_alarm_anlegen_nutzt_gemeinsame_pruefung`: `function alarmFehler(` kommt genau einmal vor, steht in `alarmAnlegen` vor `fetch(` und wird in `sicherungPruefen` verwendet.
  - `Browser.test_alarm_anlegen_nur_wenn_wiederherstellbar`: prüft 1.299,99 / 10€ / Rabatt 12.345 / 201 Zeichen. Erwartet: kein Alarm gespeichert, Meldung nennt das Feld, kein Request mit exakt der alarmQuery-URL. Der Test wartet vorher die verzögerte Filtersuche ab.
  - `Browser.test_alarm_rundreise_1299_99`: Anlegen, Download, `localStorage.clear()`, Reload, Wiederherstellen. Ergebnis „0 gemerkt, 1 Alarme; 0 ungültige …“, Stand identisch.
  - `Browser.test_gueltige_alarme_weiter_anlegbar`: 80, 12,50, 1299,99 und Rabatt 20,5 werden angelegt.

## Testergebnisse
- `python3 -m unittest tests.test_app_sicherung_s010 -v`: 18 Tests OK, 0 Skips (Chromium gefunden)
- `python3 -m unittest discover -s tests`: 234 Tests OK
- `cd cloudflare && node --test test/*.test.mjs`: 10/10 pass, 0 fail, 0 skipped

## Gegenprobe (app.js aus 33a9487, danach zurückgesetzt)
- 18 Tests, FAILED (failures=5):
  - 4 Subtests von `test_alarm_anlegen_nur_wenn_wiederherstellbar` (1.299,99 / 10€ / 12.345 / 201 Zeichen)
  - `test_alarm_anlegen_nutzt_gemeinsame_pruefung`
- Die Positivtests (Rundreise 1299,99, gültige Werte) sind auch auf dem alten Stand grün. Das ist so gewollt, sie sichern ab, dass sich am gültigen Verhalten nichts ändert.

## Sperren eingehalten
Nur app.js und die Testdatei geändert. index.html, web.py, CSP und .github/workflows sind unberührt. Kein Push, kein Merge, keine Secrets, kein `playwright install`, keine externen Abrufe.

## Offene Punkte
- Für den Fall `max_preis/min_rabatt` habe ich zusätzlich den Text „„Bis €“ oder „Ab % billiger“ angeben.“ hinterlegt. In der UI kann er praktisch nicht auftreten, weil `aktuellerWunsch()` diesen Fall schon abfängt.
- Ein `maxlength` am Suchfeld wäre UX-seitig sinnvoll, ist aber wegen möglicher Konflikte mit #39/#41 bewusst nicht umgesetzt.
- Es muss noch jemand pushen bzw. den PR aktualisieren (außerhalb von BRAIN).
