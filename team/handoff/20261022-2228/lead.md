# LEAD-Plan 20261022-2228 (UTC)

## Aufgabe
**S-010 / F3 – Merkliste und Preisalarme als JSON sichern und wiederherstellen**

## Begründung
- Es gibt keinen unfertigen Team-Draft-PR: #36 (F1) und #39 (F2) sind laut Preflight vollständig, CHECK hat beide bestanden.
- S-010 ist in tasks.json (Stand #36) der nächste Eintrag mit Status `open`. Er entspricht F3.
- Die Änderung bleibt rein clientseitig (app.js, index.html, ein wenig CSS). Dafür braucht es kein Netz, keine Zugangsdaten und keine Server-Änderung. In etwa 20 Minuten ist das machbar.

## Branch
`agent/master/20261022-22`, neu von **origin/main (e134cd0)** abzweigen. Nicht auf #36 oder #39 aufbauen. `team/tasks.json` nicht ändern, weil S-010 nur in #36 steht und sonst ein Konflikt entsteht.

## Umsetzungshinweise
- **Ist-Stand in `app/schnapper/web/app.js`:**
  - Konstanten `MAX_MERK = 200` und `MAX_ALARME = 50` (Zeilen 7–8)
  - Objekt `speicher` mit `lesen` und `schreiben`, die Schlüssel lauten `localStorage["schnapper.merkliste"]` und `["schnapper.alarme"]`
  - Getter `merkliste()` liefert ein Objekt `{id: {titel, gesamtpreis, url, quelle, zustand, gemerkt_am}}`
  - Getter `alarme()` liefert ein Array `[{text, max_preis, min_rabatt, zustand, angelegt_am}]`
  - Die Anzeige läuft über `merklisteZeigen()`, `alarmePruefen()` und `zaehler()`
- **Neu in app.js (Abschnitt „Sichern & Wiederherstellen“):**
  - `const SICHERUNG_VERSION = 1;` und `const MAX_SICHERUNG = 1024 * 1024;` (Dateigröße in Bytes)
  - `sicherungErstellen()` baut das Objekt `{format:"schnapper-sicherung", version:1, erstellt_am:ISO, merkliste:{…}, alarme:[…]}`. Daraus entsteht `Blob([JSON.stringify(obj,null,2)],{type:"application/json"})`, dann `URL.createObjectURL` und ein temporäres `<a download="schnapper-sicherung-JJJJ-MM-TT.json">` mit `click()`. Anschließend `revokeObjectURL` aufrufen.
  - `sicherungPruefen(obj)` ist eine **reine Funktion** und liefert `{ok, merkliste, alarme, fehler:[…]}`. Sie prüft:
    - `format`, `version === 1`, `merkliste` als einfaches Objekt und `alarme` als Array
    - Anzahl der Merkliste ≤ MAX_MERK und Anzahl der Alarme ≤ MAX_ALARME. Wird eine Grenze überschritten, wird die **ganze Datei abgewiesen**.
    - **Merkeintrag:**
      - Schlüssel: nicht-leerer String mit höchstens 200 Zeichen
      - `titel`: String mit 1–500 Zeichen
      - `gesamtpreis`: endliche Zahl ≥ 0
      - `url`: String, der mit `https://` oder `http://` beginnt, oder leer
      - `quelle` und `zustand`: String
      - `gemerkt_am`: String, optional
    - **Alarm:**
      - `text`: nicht-leerer String mit höchstens 200 Zeichen
      - `max_preis` und `min_rabatt`: String, der leer ist oder nur aus Ziffern mit `,`/`.` besteht. Mindestens eines der beiden Felder ist gesetzt.
      - `zustand`: `""` oder ein Schlüssel aus `ZUSTAND`
    - Unbekannte Felder werden verworfen (Whitelist).
    - Ungültige Einträge kommen nicht in das Ergebnis. Stattdessen wird `fehler` ergänzt, z. B. „Merkliste: Eintrag ‚x‘ ungültig (gesamtpreis)“.
    - Dubletten bei Alarmen (gleicher `wunschText`) werden nur einmal übernommen.
  - `sicherungLaden(ev)`:
    - Datei > MAX_SICHERUNG: abweisen
    - `await file.text()` und dann `JSON.parse` in try/catch
    - Ist das Ergebnis nicht ok (kaputt, falsche Version oder Grenze überschritten): Hinweis in `#sicherung-status` anzeigen, **nichts schreiben**
    - Sonst: `speicher.schreiben("merkliste", …)` und `speicher.schreiben("alarme", …)`. Damit **wird der bisherige Stand ersetzt**, nicht gemischt.
    - Danach `zaehler()`, `merklisteZeigen()` und `alarmePruefen()` aufrufen. Die Meldung lautet „Wiederhergestellt: N gemerkt, M Alarme; K ungültige Einträge übersprungen“, die Fehlerliste wird darunter angezeigt.
    - Ausgabe nur per `textContent` bzw. `el()`, nie per innerHTML.
  - Beide Listener im `DOMContentLoaded`-Block registrieren.
- **`app/schnapper/web/index.html`:** In `#ansicht-alarme` oder in einem kleinen gemeinsamen Abschnitt nach `#ansicht-alarme` kommt ein Block `<section id="sicherung" aria-label="Sichern und wiederherstellen">` mit:
  - Knopf `#sicherung-export` („Merkliste & Alarme sichern“)
  - `<label>` mit `<input id="sicherung-datei" type="file" accept=".json,application/json">`
  - `<p id="sicherung-status" class="status" aria-live="polite">` und `<ul id="sicherung-fehler">`
  - Das vorhandene `#datei`-Upload-Feld nicht anfassen.
- **CSP (web.py `SICHERHEIT`) bleibt unverändert.** Ein Blob-Download per `a[download]` ist eine Navigation bzw. ein Download und keine Ressource, die durch `default-src`/`connect-src` erfasst wird. `file.text()` ist ebenfalls CSP-frei. Bricht der Download trotzdem, ist das als Blocker zu melden. Die CSP darf **nicht** gelockert werden.
- **`app/schnapper/web/app.css`:** höchstens etwa 10 Zeilen für `#sicherung`, Fehlerliste mobil bei 390 px.

## Akzeptanzkriterien
1. Der Export erzeugt eine `.json`-Datei mit `format:"schnapper-sicherung"`, `version:1`, `merkliste` und `alarme`. Der Browsertest liest den Download über `page.expect_download()` und prüft die Felder.
2. **Rundreise im Browser** (Playwright, 390x844):
   - Ablauf: 2 Angebote merken, 1 Preisalarm anlegen, sichern, `localStorage.clear()` und neu laden (Zähler leer), dann die Datei per `set_input_files` wiederherstellen.
   - Erwartung: `schnapper.merkliste` und `schnapper.alarme` sind als JSON-Objekt **gleich** wie vorher, und die Zähler bzw. Listen zeigen den Stand wieder.
3. Eine kaputte Datei (kein JSON) ändert nichts: localStorage ist byte-gleich wie vorher, `#sicherung-status` zeigt einen Hinweis. Das wird im Browser geprüft.
4. Falsche Version (`version:2`), falsches `format` und Dateien über 1 MiB werden mit Hinweis abgewiesen, der Stand bleibt unverändert.
5. 201 Merkeinträge oder 51 Alarme führen zur Abweisung mit einem Hinweis, der MAX_MERK bzw. MAX_ALARME nennt. Der Stand bleibt unverändert.
6. Gemischte Datei (gültige plus ungültige Einträge, z. B. `gesamtpreis:"x"` oder `url:"javascript:…"`): Nur die gültigen werden übernommen, jeder ungültige erscheint in `#sicherung-fehler`. Unbekannte Felder werden nicht gespeichert.
7. Ein Titel mit `<img src=x onerror=…>` wird nach dem Import nur als Text angezeigt: kein `<img>` im DOM und kein `pageerror`.
8. Keine Netzwerkanfrage außer an 127.0.0.1. Im Browsertest lässt `page.on("request")` nur die eigene Basis-URL und `blob:` zu.
9. app.js enthält weiterhin kein `innerHTML`, `MAX_MERK = 200` und `MAX_ALARME = 50` sind unverändert, und der CSP-String in web.py ist unverändert. Das prüft ein statischer Test.
10. Alle bisherigen Tests sind grün (190 + neue), Cloudflare 10/10. Es gibt keine Änderung an `.github/workflows`.

## Testbefehle
```
cd /home/claude/schnapper && python3 -m unittest discover -s tests
python3 -m unittest tests.test_app_sicherung_s010 -v
cd /home/claude/schnapper/cloudflare && node --test test/*.test.mjs
```
- Der Browsertest gehört in `tests/test_app_sicherung_s010.py` und nutzt dasselbe Muster wie `tests/test_app_erfassen_s009.py` auf `origin/agent/master/20261022-21`, nur zum Ansehen:
  - Server über `erstelle_server(BEISPIEL, port=0)` im Thread
  - `CHROMIUM = /opt/pw-browsers/chromium-1194/chrome-linux/chrome` mit `executable_path`
  - `skipUnless(playwright vorhanden)`
  - Viewport 390x844, `accept_downloads=True`
- **Kein `playwright install`**, kein pip-Download.

## Dateigrenzen
- **Erlaubt:**
  - `app/schnapper/web/app.js`
  - `app/schnapper/web/index.html`
  - `app/schnapper/web/app.css`
  - neu: `tests/test_app_sicherung_s010.py`
  - optional eine kurze Zeile in `README.md`
- **Verboten:**
  - `app/schnapper/web.py` (die CSP bleibt)
  - `.github/workflows/**` und `team/tasks.json`
  - **`team/handoff/**`**, das nie committet werden darf, also kein `git add -A`, sondern nur gezielt hinzufügen
  - Branches fremder PRs (#30/#28/#29 ändern ebenfalls den Preisalarm-Import; Hinweis im PR-Text)
  - alles von ZENTNA, JERRY AL und Beatmaster
- Budget 0 €, keine externen Preisquellen, keine Secrets.
