# LEAD – Lauf 20261029-0029

## Aufgabe
F3 / S-010 „Merkliste/Preisalarme sichern und wiederherstellen“, Draft-PR #40.
Schritt: Ein Preisalarm darf nur dann angelegt werden, wenn er die Prüfung beim Wiederherstellen bestehen würde. Dafür gibt es eine gemeinsame Prüfregel für Anlegen und Wiederherstellen. Bisher legt die App Alarme an, die ihre eigene Wiederherstellung später als „ungültig“ verwirft. Die Rundreise Sichern → Wiederherstellen verliert so Daten, und das verletzt das Akzeptanzkriterium von S-010.

## Begründung (mit Beleg)
- `alarmAnlegen()` (app.js Z. 250–262 auf Branch-Kopf 33a9487) übernimmt den Wunsch aus `aktuellerWunsch()` (Z. 229–234) ungeprüft, sobald `/api/suche` mit 200 antwortet (`liste.push({ ...w, … })`, Z. 259). Der Server ist aber großzügiger. `filter_aus_query` (web.py Z. 87–101) nimmt `max_preis` „1.299,99“ und „10€“ über `geld()` an, `min_rabatt` „12.345“ über `Decimal` und einen Suchtext mit 250 Zeichen, den er still auf 200 kürzt (`eins("text")[:200]`, Z. 101). Gegenprobe vom LEAD lesend mit `filter_aus_query`: alle vier Werte OK.
- `sicherungPruefen()` lehnt genau diese gespeicherten Alarme ab. Grund sind `maxPreisOk`/`minRabattOk` (Z. 420–424, Regex `^[0-9]{1,9}(?:[.,][0-9]{1,2})?$` bzw. `^[0-9]{1,3}(?:[.,][0-9]{1,2})?$`) und `w.text.length > 200` (Z. 430). Ein deutscher Nutzer mit „Bis € 1.299,99“ sichert also seinen Alarm und verliert ihn beim Wiederherstellen („Eintrag 1 ungültig (max_preis)“).
- #40 wurde zuletzt am 28.10. um 16:35 bearbeitet (33a9487) und ist damit unter den Team-PRs mit belegbarem Mangel am längsten unberührt. Frühere Läufe haben nur die Wiederherstellungsseite an den Server angeglichen (1adad0c). Die Anlegeseite war bisher nie Thema, der Schritt wiederholt also keine Politur.

## Branch
`agent/master/20261022-22` (PR #40, Kopf `33a9487`). Auf diesem Branch fortsetzen, nicht neu erstellen, kein Force-Push, kein Rebase. Wenn origin/main inzwischen weiter ist als 6dbe114, per Merge übernehmen (laut Preflight unverändert, also voraussichtlich nicht nötig).

## Umsetzungshinweise
1. In `app/schnapper/web/app.js` die Alarmregeln aus `sicherungPruefen()` als Funktion auf oberster Ebene herausziehen, z. B. `function alarmFehler(w)`. Sie gibt `null` oder den Feldnamen zurück (`"text"`, `"max_preis"`, `"min_rabatt"`, `"max_preis/min_rabatt"`, `"zustand"`). Dabei `zahlWert`, `maxPreisOk` und `minRabattOk` mitnehmen und die Regex-Ausdrücke **wortgleich** lassen, denn `test_alarmpruefung_wie_server` prüft die Zeichenketten.
2. `sicherungPruefen()` nutzt `alarmFehler(w)` für die Felder. Die Prüfungen `kein Objekt` und `angelegt_am` bleiben dort. Fehlertexte und Reihenfolge der Meldungen ändern sich nicht, die bestehenden Tests müssen unverändert grün bleiben.
3. `alarmAnlegen()`: Direkt nach `const w = aktuellerWunsch(); if (!w) return;` wird `alarmFehler(w)` aufgerufen, vor Dublettenprüfung und `fetch`. Bei einem Fehler kommt eine verständliche Meldung in `#status`, und es gibt **keinen** `fetch` und keinen Speichervorgang, zum Beispiel:
   - text: „Preisalarm nicht angelegt: Suchbegriff höchstens 200 Zeichen.“
   - max_preis: „Preisalarm nicht angelegt: „Bis €“ als Zahl größer 0 mit höchstens 2 Nachkommastellen, ohne Tausenderpunkt und ohne €, z. B. 1299,99.“
   - min_rabatt: „Preisalarm nicht angelegt: „Ab % billiger“ zwischen 0 und 100, höchstens 2 Nachkommastellen.“
   - zustand: „Preisalarm nicht angelegt: Zustand unbekannt.“
   Die Texte gehen mit `textContent` in `#status`, nicht mit `innerHTML`.
4. Keine Änderung an `index.html` (kein `maxlength`), weil #39 und #41 dort dieselben Stellen ändern und Konflikte drohen. Auch an `web.py`, CSP und `.github/workflows` nichts ändern.
5. Tests nur in `tests/test_app_sicherung_s010.py` ergänzen:
   - Browsertest `test_alarm_anlegen_nur_wenn_wiederherstellbar`. Für die Werte `max_preis` „1.299,99“, „10€“, `min_rabatt` „12.345“ (mit leerem max_preis) und einen Text mit 201 Zeichen (max_preis „5“) jeweils `#text` und Feld füllen, auf `!alarm-anlegen.disabled` warten und klicken. Danach prüfen: `schnapper.alarme` bleibt leer bzw. `null`, `#status` beginnt mit „Preisalarm nicht angelegt“, und es gab keinen Request auf `/api/suche` mit diesem Wunsch (über `self.seite.on("request")` mitzählen, oder vor dem Klick `self.kontext.route` auf `**/api/suche*` zählen).
   - Positivfall im selben oder einem zweiten Test: „1299,99“ wird angelegt, gesichert (Download) und nach `localStorage.clear()` + Reload wiederhergestellt, Meldung „Wiederhergestellt: 0 gemerkt, 1 Alarme; 0 ungültige Einträge übersprungen“. Das ist die Rundreise.
   - Statischer Test: `function alarmFehler(` kommt in app.js vor, und `alarmAnlegen` ruft `alarmFehler(` **vor** `fetch(` auf (Index-Vergleich im Funktionsrumpf wie in `test_ak9_app_js`).
6. Commit-Nachricht nach Schema „SCHNAPPER MASTER: F3 Preisalarm nur anlegen, wenn er wiederherstellbar ist (S-010)“, mit der Attribution aus dem System-Hinweis.

## Akzeptanzkriterien
1. In app.js gibt es genau eine Alarmprüfung (`alarmFehler`), die `sicherungPruefen()` und `alarmAnlegen()` beide verwenden. Die Regex-Zeichenketten aus `test_alarmpruefung_wie_server` bleiben unverändert vorhanden.
2. `alarmAnlegen()` legt keinen Alarm an, wenn `max_preis` „1.299,99“ oder „10€“ ist, wenn `min_rabatt` „12.345“ ist oder wenn der Suchtext länger als 200 Zeichen ist. `localStorage['schnapper.alarme']` bleibt dann unverändert.
3. In diesen Fällen geht kein Request an `/api/suche` für den Alarm (die Prüfung läuft vor `fetch`), und `#status` zeigt eine Meldung, die mit „Preisalarm nicht angelegt“ beginnt und das betroffene Feld nennt.
4. Gültige Alarme („80“, „12,50“, „1299,99“, Rabatt „20,5“) werden wie bisher angelegt. Der bestehende `test_ak1_ak2_export_und_rundreise` bleibt grün.
5. Rundreise: Ein in der App angelegter Alarm mit „1299,99“ wird nach Sichern, Leeren und Wiederherstellen mit 0 übersprungenen Einträgen zurückgeholt.
6. Meldungen und Verhalten von `sicherungPruefen()` bleiben gleich, alle bestehenden Tests in `test_app_sicherung_s010.py` sind grün, ohne dass man sie ändert.
7. Kein `innerHTML`, keine neuen externen Requests (die Prüfung `self.fremd == []` greift), keine Konsolenfehler, CSP unverändert (`test_ak9_csp_unveraendert`).
8. Der Diff betrifft nur `app/schnapper/web/app.js` und `tests/test_app_sicherung_s010.py`. Kein Secret im Diff.
9. Gegenprobe: Die neuen Tests laufen gegen `app.js` aus 33a9487 (`git show 33a9487:app/schnapper/web/app.js > app/schnapper/web/app.js`, danach zurücksetzen) und **müssen fehlschlagen**. Mindestens der Browsertest aus AK 2/3 und der statische Test sind dann rot. Die Zahl der Fehlschläge wird festgehalten.
10. Python-Gesamtlauf grün mit 0 Skips im Modul (Chromium wird gefunden), Cloudflare 10/10.

## Testbefehle
```
cd /home/claude/schnapper
python3 -m unittest discover -s tests
python3 -m unittest tests.test_app_sicherung_s010 -v
cd cloudflare && node --test test/*.test.mjs
```
Playwright nutzt das vorinstallierte Chromium (`/opt/pw-browsers/chromium-*`, gefunden über `_finde_chromium()`). **Kein** `playwright install` und kein Netzwerkzugriff. Nur Mock- und Lokaltests, keine Live-Abrufe externer Preisquellen.
