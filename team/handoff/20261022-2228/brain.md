# BRAIN-Bericht 20261022-2228: S-010 / F3

## Branch / Commit
- Branch `agent/master/20261022-22`, abgezweigt von origin/main e134cd0 (nicht gepusht)
- Commit **3ab36fa**: „SCHNAPPER MASTER: F3 (S-010) Merkliste und Preisalarme als JSON sichern und wiederherstellen“

## Geänderte Dateien
- `app/schnapper/web/app.js` (+112): `SICHERUNG_VERSION = 1`, `MAX_SICHERUNG = 1024*1024`, `sicherungErstellen()` (Blob, `a[download]`, revokeObjectURL), reine Funktion `sicherungPruefen(obj)` mit Whitelist und Fehlerliste, `sicherungLaden(ev)`; beide Listener im DOMContentLoaded-Block
- `app/schnapper/web/index.html` (+10): `<section id="sicherung">` am Ende von `#ansicht-alarme` mit `#sicherung-export`, `#sicherung-datei`, `#sicherung-status`, `#sicherung-fehler`; `#datei` unverändert
- `app/schnapper/web/app.css` (+7)
- neu: `tests/test_app_sicherung_s010.py` (3 statische Tests, 3 Playwright-Tests mit 390x844)
- Nicht angefasst: web.py (die CSP gilt unverändert und wird per Test geprüft), .github/workflows, team/tasks.json, README

## Eigene Testergebnisse
- Python `python3 -m unittest discover -s tests`: **196/196 OK** (190 vorher + 6 neu)
- `tests.test_app_sicherung_s010`: 6/6 OK, davon **3/3 Browsertests** (Chromium unter /opt/pw-browsers)
  - AK1/2: Export per `expect_download`, Felder geprüft; Rundreise mit 2 gemerkten Angeboten und 1 Alarm, danach `localStorage.clear()` und reload; nach dem Restore ist der localStorage-Stand JSON-gleich, die Zähler und Listen sind wieder da, scrollWidth ≤ 390
  - AK3/4/5: Diese Dateien werden abgewiesen und der localStorage bleibt byte-gleich: kaputtes JSON, version 2, falsches format, Datei > 1 MiB, 201 Merkeinträge (Hinweis „max. 200“), 51 Alarme (Hinweis „max. 50“), Merkliste als Array
  - AK6/7: In einer gemischten Datei werden nur die gültigen Einträge übernommen und jeder ungültige erscheint in `#sicherung-fehler` (9 Stück). Unbekannte Felder werden verworfen. Der `<img onerror>`-Titel erscheint nur als Text: kein `<img>` im DOM und kein pageerror
  - AK8: `page.on("request")` lässt nur die Basis-URL und `blob:` zu. Alles andere wird per Route abgebrochen und in tearDown geprüft (leer)
  - AK9: statisch geprüft, dass kein innerHTML vorkommt, MAX_MERK/MAX_ALARME unverändert sind und der CSP-String exakt gleich ist
- Cloudflare `node --test test/*.test.mjs`: **10/10 OK**
- Der Blob-Download funktioniert unter der bestehenden CSP. Es gibt keinen Blocker.

## Abweichungen vom Plan
1. **gesamtpreis**: Der Plan sagt „endliche Zahl ≥ 0“. Der Server liefert `gesamtpreis` aber als Dezimal-String (`str(Decimal)`, z. B. "54.89"), und genau so speichert die Merkliste ihn. Wäre nur eine Zahl erlaubt, würde jeder echte Eintrag beim Restore abgewiesen. Das hat der Browsertest gezeigt (zuerst „0 gemerkt“). Deshalb wird jetzt auch ein String nach `^[0-9]+(\.[0-9]+)?$` (≤ 20 Zeichen) akzeptiert. Der Typ bleibt dabei erhalten, sodass die Rundreise identisch ist. "x" und -1 werden weiter abgewiesen.
2. Die Alarme übernehmen zusätzlich das optionale `angelegt_am` (String), denn es gehört zum bestehenden Datenschema. Die Merkliste übernimmt `gemerkt_am` wie im Plan.
3. Im Browsertest ersetzt die Hilfe `warte()` (Python-Polling über `evaluate`) `wait_for_function`, weil die CSP ohne `'unsafe-eval'` Playwrights String-Prädikate blockiert. Die CSP selbst wurde nicht gelockert und es gibt kein `bypass_csp`.

## Offene Punkte
- Der Hinweis für den PR-Text: #30/#28/#29 ändern ebenfalls den Preisalarm-Import, es kann also zu Konflikten kommen.
- README-Zeile weggelassen (optional).
- S-010 in team/tasks.json bleibt laut Plan unverändert. Den Status setzt erst der Merge von #36.
