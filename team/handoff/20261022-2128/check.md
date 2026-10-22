# CHECK 20261022-2128 – Runde 1

**Urteil: bestanden**

Geprüft: Branch `agent/master/20261022-21`, Commit `6dbeb82` („SCHNAPPER MASTER: F2 Angebot in der App erfassen (S-009)“, Attribution-Zeilen vorhanden), Basis origin/main. Diff vollständig gelesen (5 Dateien, +359/−2).

## Testzahlen (selbst ausgeführt)
- `python3 -m unittest discover -s tests`: **Ran 202 tests, OK** (0 skipped; vorher 190 + 12 neu)
- `python3 -m unittest tests.test_app_erfassen_s009 -v`: **12/12 ok**, `Browser.test_ak8_erfassen_und_csv_im_browser ... ok` (lief, nicht skipped)
- `cd cloudflare && node --test test/*.test.mjs`: **10 pass, 0 fail, 0 skipped**

## Sicherheits-/Regelprüfung
- Secret-Scan des Diffs (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw): **keine Treffer**.
- Tabu: geänderte Dateien nur `app/schnapper/web.py`, `app/schnapper/web/{app.css,app.js,index.html}`, `tests/test_app_erfassen_s009.py`. Keine Änderung an .github/workflows, team/handoff, team/tasks.json. Keine Treffer für ZENTNA / Jerry / Beatmaster.
- `git status` nach Prüfung sauber (nur untracked `team/handoff/`).

## Akzeptanzkriterien
| # | Kriterium | erfüllt | Beleg |
|---|-----------|---------|-------|
| 1 | POST /api/angebot → 201, Suche findet Treffer mit quelle „eigene“ | ja | web.py `_angebot_erfassen` (→ 201 `{"id","anzahl"}`); Test `test_ak1_erfassen_und_finden` (test_app_erfassen_s009.py:68) |
| 2 | ohne Header 403 / >4096 → 413 / kaputtes JSON → 400 | ja | Tests :78, :83, :87; eigener Probelauf: X-Schnapper fehlt/„0“ → 403, 5000 Byte → 413, CL=0/−5 → 413, ohne Content-Length → 411, ungültiges UTF‑8 → 400, JSON-Liste/-String → 400 |
| 3 | Ungültig → 422, Liste unverändert (Preis 0/abc, http-URL, unbek. Zustand) | ja | Test :92 (subTests inkl. leerer Titel, Vergleich Suche vorher/nachher); Probe: preis `[1]`/null/inf, versand −1, `javascript:` → 422 |
| 4 | Client-quelle/id/erfasst_am ignoriert | ja | Whitelist `ERFASSEN_FELDER`, Server setzt id `e-`+token_hex, quelle „eigene“, erfasst_am UTC; Test :102; Probe mit `quelle:"ebay"` → CSV zeigt `eigene` |
| 5 | Beispielliste wird verworfen, nur neues Angebot | ja | `Zustand.hinzufuegen` (unter `_lock`, keine In-place-Änderung); Test :112 (+ zweites Angebot hängt an) |
| 6 | CSV-Kopfzeile = Vorlage; Roundtrip mit lies_text ohne Fehler | ja | Kopf `id;titel;preis;versand;referenzpreis;zustand;quelle;kategorie;url;erfasst_am` identisch mit app/vorlagen/meine-angebote.csv Z.1; Tests :125 (aus Datei gelesen), :134 (inkl. `;` und `"` im Titel, leerer Referenzpreis) |
| 7 | app.js: /api/angebot + X-Schnapper, kein innerHTML im neuen Code | ja | `angebotSpeichern` nur `textContent`; einziges „innerHTML“ in app.js ist der bestehende Kommentar Z.2. Abweichung vom wörtlichen Test (`"innerHTML" not in js` wäre wegen Kommentar falsch) begründet; Test :153 prüft Funktion + Code ohne Kommentare |
| 8 | Playwright-Browsertest 390x844, Karte, CSV-Download, keine console-/pageerror | ja | Test :176 lief (ok); Chromium /opt/pw-browsers/chromium-1194; Fremd-Requests per `route` abgebrochen; `meldungen == []`; scrollWidth ≤ 390 |
| 9 | Bestehende Tests grün, Cloudflare 10/10, kein externer Netzzugriff | ja | 202 OK, 10/10; Server bindet 127.0.0.1 (`erstelle_server` Default, Probe `bind ('127.0.0.1', …)`, Test `test_lokal`); Tests mit `ProxyHandler({})` |

Zusätzlich geprüft:
- CSV-Antwort mit allen SICHERHEIT-Köpfen (CSP, nosniff) + `Content-Disposition`; HEAD liefert 200 ohne Body.
- Thread-Sicherheit: 50 parallele POSTs → 52 Angebote, 52 eindeutige IDs, Rückimport fehlerfrei.
- Register-Prüfung `pruefe("eigene")` eingebaut; OSError → 500 analog /api/import.
- CSP unverändert; Formular per fetch (form-action 'none' kein Problem).

## Pflichtkorrekturen
keine

## Optionale Hinweise (kein Blocker)
1. **CSV-Formel-Injection:** Zellen, die mit `= + - @` beginnen, werden unverändert exportiert (Probe: Titel `=HYPERLINK(...)`, Kategorie `+cmd`). Relevanz gering: lokale Einzelnutzer-App, Daten stammen vom Nutzer selbst bzw. aus von ihm importierten Listen. Ein Präfix `'` würde den Roundtrip (AK 6) verändern – daher eher als Folgeaufgabe abwägen (z. B. nur beim Export Präfix + beim Import wieder entfernen).
2. Nicht-String-Werte werden per `str()` angenommen (Probe: `titel: {"a":1}` → 201, Titel „{'a': 1}“). Harmlos, aber eine Typprüfung (nur str/Zahl) wäre sauberer.
3. `kategorie` maxlength 100 nur im HTML, serverseitig nur durch 4096-Byte-Limit begrenzt.
4. Wie von BRAIN vermerkt: gleiche URL wird in der Suche als Dublette ausgeblendet (bleibt in CSV) – ggf. UI-Hinweis.
