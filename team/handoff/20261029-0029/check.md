# CHECK – Lauf 20261029-0029

**Urteil: bestanden**

Ich habe unabhängig geprüft, Branch `agent/master/20261022-22`, lokaler Commit `87eebba` (Basis `33a9487`, origin/main `6dbe114`). Es wurde kein Code geändert. Der Arbeitsbaum ist nach der Gegenprobe wieder clean (`git status`: „nothing to commit, working tree clean“).

## Tests
- `python3 -m unittest discover -s tests`: 234 Tests, OK, keine Skips.
- `python3 -m unittest tests.test_app_sicherung_s010 -v`: 18 Tests, OK, 0 Skips (Chromium gefunden). Die vier neuen Tests sind grün.
- `cd cloudflare && node --test test/*.test.mjs`: 10 Tests, 10 bestanden, 0 fehlgeschlagen, 0 übersprungen.

## Diff und Sperren
- `git diff origin/agent/master/20261022-22..agent/master/20261022-22` betrifft nur `app/schnapper/web/app.js` (+29/−13) und `tests/test_app_sicherung_s010.py` (+72).
- `git diff origin/main...agent/master/20261022-22` betrifft app.css, app.js, index.html und die Testdatei. Das ist der bisherige Stand von PR #40, in diesem Lauf kommt nichts dazu. Es gibt keine Änderung an `.github/workflows`, ZENTNA, JERRY AL oder Beatmaster (grep ohne Treffer).
- Secret-Scan über die `+`-Zeilen des Gesamtdiffs (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, secret, token): keine Treffer.

## Gegenprobe
`git show 33a9487:app/schnapper/web/app.js > app/schnapper/web/app.js` und danach das Testmodul: **FAILED (failures=5)** bei 18 Tests.
- 4 Subtests von `test_alarm_anlegen_nur_wenn_wiederherstellbar` (1.299,99 / 10€ / 12.345 / 201 Zeichen)
- `test_alarm_anlegen_nutzt_gemeinsame_pruefung`

Danach mit `git checkout -- .` zurückgesetzt. Das deckt sich mit dem Bericht von BRAIN.

## Akzeptanzkriterien
1. ✔ Es gibt genau eine `function alarmFehler(` (Z. 258). Sie wird in `alarmAnlegen` (Z. 278) und in `sicherungPruefen` (Z. 450) aufgerufen. Beide Regex-Ausdrücke sind wortgleich, und `test_alarmpruefung_wie_server` ist grün.
2. ✔ Die Prüfung läuft direkt nach `aktuellerWunsch()` und kehrt vor `speicher.schreiben` zurück. Der Browsertest prüft für alle vier Werte, dass `schnapper.alarme` dann `null` bzw. `[]` ist.
3. ✔ Im Code steht `alarmFehler` vor `fetch(`, das prüfen sowohl der statische Test als auch das Lesen des Codes. Der Browsertest stellt fest, dass die exakte alarmQuery-URL nicht abgerufen wurde. `#status` beginnt mit „Preisalarm nicht angelegt“ und nennt das Feld („Bis €“ / „Ab % billiger“ / „Suchbegriff höchstens 200 Zeichen“).
4. ✔ `test_gueltige_alarme_weiter_anlegbar` (80, 12,50, 1299,99, Rabatt 20,5) ist grün, `test_ak1_ak2_export_und_rundreise` ebenfalls. `aktuellerWunsch()` trimmt die Eingaben wie bisher, gültige Eingaben kommen also unverändert durch.
5. ✔ `test_alarm_rundreise_1299_99` ist grün und liefert „Wiederhergestellt: 0 gemerkt, 1 Alarme; 0 ungültige Einträge übersprungen“. Der Stand ist danach identisch.
6. ✔ Die Reihenfolge in `sicherungPruefen` ist gleich geblieben: kein Objekt, dann text, max_preis, min_rabatt, max_preis/min_rabatt, zustand und zuletzt angelegt_am. `angelegt_am` wird nur geprüft, wenn vorher alles fehlerfrei war, wie zuvor bei der else-if-Kette. Die Meldungstexte sind unverändert, und die bestehenden Tests laufen grün, ohne dass ich sie geändert habe.
7. ✔ Neue Meldungen werden nur über `textContent` gesetzt, ein `innerHTML` kommt nur im Kommentar in Z. 2 vor. Die Prüfungen `self.fremd == []` und auf Konsolenfehler greifen in allen Browsertests, `test_ak9_csp_unveraendert` ist grün. index.html und web.py sind in diesem Lauf nicht verändert.
8. ✔ Siehe „Diff und Sperren“: nur die zwei erlaubten Dateien, keine Secrets.
9. ✔ Die Gegenprobe ergibt 5 Fehlschläge. Dabei sind der Browsertest zu AK 2/3 und der statische Test rot.
10. ✔ Python 234 OK, das Modul ohne Skips, Cloudflare 10/10.

## Code-Review (Anmerkungen, kein Mangel)
- Durch das Herausziehen liegen `zahlWert`, `maxPreisOk` und `minRabattOk` jetzt global. Die Namen gibt es nur einmal, es kommt nicht zu einer Redeklaration, und die Konsole bleibt fehlerfrei.
- Der Fall `max_preis/min_rabatt` kann in der UI nicht auftreten, weil `aktuellerWunsch()` ihn vorher abfängt. Er ist trotzdem harmlos mit einem eigenen Text abgedeckt.
- Der Request-Nachweis im Browsertest vergleicht nur die exakte alarmQuery-URL. Er ist damit schwächer als „gar kein /api/suche“, weil die Filtersuche die API legitim selbst aufruft. Zusammen mit dem statischen Index-Test reicht das aus.
- Optional für später: ein `maxlength` am Suchfeld. Laut Plan ist es wegen #39/#41 bewusst nicht umgesetzt.
- Noch offen: Push bzw. PR-Update außerhalb von CHECK.
