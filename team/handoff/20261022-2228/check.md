# CHECK 20261022-2228: S-010 / F3 (Sichern & Wiederherstellen)

**Urteil: bestanden**

Geprüft wurde Branch `agent/master/20261022-22` mit Commit 3ab36fa (1 Commit über origin/main e134cd0). Ich habe den Diff vollständig gelesen und alle Tests selbst ausgeführt.

## Diff / Dateigrenzen
- Geändert sind nur `app/schnapper/web/app.css` (+7), `app/schnapper/web/app.js` (+112), `app/schnapper/web/index.html` (+10) und neu `tests/test_app_sicherung_s010.py` (+252). Alle vier Pfade sind laut lead.md erlaubt.
- Folgende Pfade sind nicht berührt: `web.py`, `.github/workflows`, `team/tasks.json`, `team/handoff/`. `team/handoff/` ist nur untracked und nicht committet.
- Der Secret-Scan über den Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw, token) fand nichts.
- Tabu-Pfade (ZENTNA, JERRY AL, Beatmaster): kein Treffer.

## Testzahlen (selbst ausgeführt)
- `python3 -m unittest discover -s tests`: **196/196 OK**, 0 übersprungen (190 vorher + 6 neu)
- `python3 -m unittest tests.test_app_sicherung_s010 -v`: **6/6 OK**
  - davon 3 Browsertests (`Browser.test_ak1_ak2…`, `test_ak3_ak4_ak5…`, `test_ak6_ak7…`). Sie liefen tatsächlich mit „ok“, nicht mit „skipped“, Laufzeit 5,5 s.
- `cloudflare: node --test test/*.test.mjs`: **10/10 pass**, 0 fail, 0 skipped

## Kriterien

| AK | Ergebnis | Beleg |
|---|---|---|
| 1 Export-JSON | erfüllt | `test_ak1_ak2_export_und_rundreise`: `expect_download`, Dateiname-Regex, `format`/`version`/`merkliste`/`alarme` geprüft. Code: `sicherungErstellen()` (Blob, `a[download]`, `revokeObjectURL`) |
| 2 Rundreise 390x844 | erfüllt | gleicher Test. Ablauf: 2 merken, 1 Alarm, Export, `localStorage.clear()`, reload (Zähler hidden, beide Keys `None`), `set_input_files`. Danach `stand() == vorher`, Zähler „2“, Listen 2 bzw. 1, scrollWidth ≤ 390 |
| 3 Kaputte Datei | erfüllt | `test_ak3…` Fall „kaputt“: Meldung „kein gültiges JSON … Nichts geändert“, `roh()` byte-gleich. Code: `JSON.parse` in try/catch mit `return` vor jedem `speicher.schreiben` |
| 4 Version / Format / > 1 MiB | erfüllt | Fälle „version 2“, „format“, „zu gross“ (1 MiB + 8 Byte). `datei.size > MAX_SICHERUNG` wird vor dem Lesen geprüft. Der Stand bleibt byte-gleich |
| 5 201 Merk / 51 Alarme | erfüllt | Hinweise „max. 200“ / „max. 50“ (aus `MAX_MERK`/`MAX_ALARME`). Die ganze Datei wird abgewiesen, der Stand bleibt byte-gleich |
| 6 Gemischte Datei / Whitelist | erfüllt | `test_ak6_ak7…`: 9 Fehler in `#sicherung-fehler` (preis „x“, preis −1, `javascript:`-URL, leerer Schlüssel, leerer Titel, Dublette, beide Grenzen leer, „10€“, falscher zustand). Felder `geheim`/`extra` werden nicht gespeichert, Feldmenge exakt geprüft |
| 7 XSS-Titel | erfüllt | Titel `<img src=x onerror=…>` erscheint als Text in `.titel`. Weiter geprüft: `img`-Count 0, `window.__xss` undefined, kein pageerror (tearDown prüft `meldungen == []`) |
| 8 Nur 127.0.0.1 / blob: | erfüllt | `kontext.route` bricht fremde URLs ab, `page.on("request")` protokolliert sie, tearDown prüft `fremd == []` |
| 9 Statisch | erfüllt | `test_ak9_app_js` prüft: kein `innerHTML`, `MAX_MERK = 200` und `MAX_ALARME = 50` unverändert. `test_ak9_csp_unveraendert` vergleicht den CSP-String exakt. `web.py` ist nicht im Diff |
| 10 Regression | erfüllt | 196/196, Cloudflare 10/10, keine Workflow-Änderung |

## Sicherheit (eigene Prüfung)
- **innerHTML:** Im neuen Code gibt es kein innerHTML. Alle Ausgaben laufen über `textContent` bzw. `el("li", f)` mit `replaceChildren`.
- **Whitelist:** Merkeinträge und Alarme werden jeweils als neues Objekt aufgebaut. Es werden nur benannte Felder kopiert.
- **URL:**
  - Beim Import gilt `/^https?:\/\//` oder ein leerer String. `javascript:` und `HTTPS://` werden abgewiesen (eigener Versuch).
  - Beim Anzeigen setzt die bestehende Darstellung `href` nur bei `https://` (app.js Z. 107/298/345). Das ist eine zweite Schutzschicht.
- **zustand:** Die Prüfung `Object.hasOwn(ZUSTAND, …)` weist `"__proto__"` ab (eigener Versuch).
- **Kein Teil-Schreiben:** Bei `ok:false` oder einem Parse-/Größenfehler endet die Funktion per `return`, bevor `speicher.schreiben` aufgerufen wird.

## Abweichung gesamtpreis als Dezimal-String
Die Abweichung ist **berechtigt**. `merkliste()` übernimmt `t.gesamtpreis` unverändert vom Server (Z. 76), also als String. Ohne die Abweichung würde jede echte Sicherung beim Restore verworfen.

Die Prüfung ist trotzdem streng. Eigener Node-Versuch mit `preisOk`:
- **abgewiesen:** NaN, Infinity, 1e309 (wird zu Infinity), −0.01, "Infinity", "NaN", "-1", "1e5", " 1", "1.", "0x10" sowie Strings über 20 Zeichen
- **angenommen:** 0, "0", "54.89"

Die Anzeige rechnet über `Number(...)`, das ist für diese Formen unkritisch.

## Hinweis (kein Mangel)
Ein Merkliste-Schlüssel `"__proto__"` wird wegen `merk[id] = neu` still verworfen: Er landet weder im Ergebnis noch in `fehler`.
- Es gibt keine globale Prototype-Pollution, `({}).titel` bleibt undefined (eigener Versuch).
- Echte IDs dieser Form sind praktisch ausgeschlossen. Optional ließe sich das später mit `Object.create(null)` oder einem Fehlereintrag lösen.
