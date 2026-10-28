# CHECK – Lauf 20261028-2328

**Urteil: bestanden**

Geprüft wurde der lokale Commit `6165af4` auf `agent/master/20261022-2238` (ungepusht, Fast-Forward auf origin `ca5420e`). Ich habe keinen Code geändert, nichts committet und nichts gepusht.

## 1. Tests (selbst ausgeführt, vorinstalliertes Chromium, kein `playwright install`)
- `python3 -m unittest tests.test_app_kamera_s011 -v`: **Ran 25, OK, 0 Skips**. Alle 4 neuen Tests sind grün.
- `python3 -m unittest discover -s tests`: **Ran 241, OK**, ohne Skips.
- `cd cloudflare && node --test test/*.test.mjs`: **10 Tests, 10 pass, 0 fail, 0 skipped**.

## 2. Diff und Grenzen
- `origin/agent/master/20261022-2238..agent/master/20261022-2238`: geändert sind nur `app/schnapper/web/app.js` (+2 Zeilen in `kameraStoppen()`, +1 Zeile in `kameraScannen()`) und `tests/test_app_kamera_s011.py` (2 Hilfsmethoden und 4 neue Tests). Beide Dateien sind erlaubt.
- `origin/main...branch`: Dateien `app.css`, `app.js`, `index.html` und `tests/test_app_kamera_s011.py`. `app.css` und `index.html` stammen aus früheren S-011-Commits, dieser Commit ändert sie nicht.
- Keine Änderung an `.github/workflows`, keine Tabu-Pfade (ZENTNA, JERRY AL, Beatmaster). Die Suche ergab keinen Treffer.
- `KAMERA_FORMATE`, `KAMERA_ZEITLIMIT`, die Treffer-Regex, die Zeitlimit-Logik und `kamera.lauf` sind unverändert.

## 3. Secret-Scan
Den Diff `origin/main...branch` habe ich nach `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token` durchsucht: **kein Treffer**.

## 4. Gegenprobe (selbst ausgeführt)
Ich habe `app.js` aus `ca5420e` eingesetzt und die neuen Tests laufen lassen. Ergebnis: **FAILED (failures=3)**.
- `test_tastatur_fokus_start_und_abbrechen`: Zeitüberschreitung beim Warten auf Fokus `kamera-abbrechen`.
- `test_fokus_waehrend_kamera_anfrage`: `'kamera-knopf' != 'kamera-abbrechen'`.
- `test_fokus_zurueck_nach_zeitlimit`: Zeitüberschreitung beim Warten auf Fokus `kamera-abbrechen`.
- `test_fokus_bleibt_im_feld` ist grün, wie erwartet.

Danach habe ich `git checkout -- .` ausgeführt. `git status` ist sauber, nur der eine Commit liegt vor origin.

Randbemerkung: In Chromium meldet `activeElement` beim alten Code den deaktivierten `kamera-knopf`, nicht `BODY`, wie lead.md vermutet hatte. Die Begründung ändert sich dadurch nicht: Ein deaktivierter Knopf ist nicht bedienbar, und Abbrechen hat keinen Fokus. Die Tests sind trotzdem rot.

## 5. Akzeptanzkriterien
| AK | Bewertung | Beleg |
|---|---|---|
| 1 Start-Fokus | erfüllt | `$("kamera-abbrechen").focus()` steht direkt nach `hidden = false` und vor `await getUserMedia`. Test 6 ist grün. |
| 2 Stoppen nur bei Fokus auf Abbrechen | erfüllt | `fokusZurueck` wird vor `hidden = true` ermittelt, `focus()` folgt nach `disabled = false`. Test 8 (Fokus bleibt im Barcode-Feld) ist grün. |
| 3 alle Stopp-Wege | erfüllt | Die Logik sitzt zentral in `kameraStoppen()`, und Abbrechen, Zeitlimit, Fehler, Treffer und visibilitychange/pagehide laufen alle darüber. Belegt durch Tests 5, 6 und 7. Für Fehler und Treffer gibt es keinen eigenen Fokus-Test, durch den zentralen Pfad sind sie aber abgedeckt. |
| 4 Treffer-Ablauf | erfüllt | Die Reihenfolge Feld → `kameraStoppen` → `requestSubmit` ist unverändert. `test_ak1_ak2_ak3_treffer_fuellt_feld` ist grün. |
| 5 Test Tastatur Start/Abbrechen | erfüllt | Vorhanden, nutzt `focus` und Enter, keinen Klick. Prüft Status, `alles_gestoppt()` und Fokus auf `kamera-knopf`. |
| 6 Test Fokus während Anfrage | erfüllt | Vorhanden mit `verzoegert=True` und `__gum === 1`. Zusätzlich bricht der Test per Enter ab und prüft die Fokus-Rückgabe. |
| 7 Test Zeitlimit | erfüllt | Vorhanden mit `uhr=True` und `run_for(21000)`. Prüft `alles_gestoppt()`, `ZEITLIMIT` und Fokus auf `kamera-knopf`. |
| 8 Test Fokus bleibt im Feld | erfüllt | Vorhanden, nutzt `verstecken()` und prüft Fokus auf `barcode`. |
| 9 Gegenprobe | erfüllt | 3 Fehlschläge (siehe Abschnitt 4). |
| 10 Alt-Tests grün, 0 Skips | erfüllt | 241 OK. `test_markup`, `test_app_js` und `test_csp_unveraendert` sind grün. 0 Skips. |
| 11 kein innerHTML/console, keine neue Abhängigkeit, CSP und index.html unverändert | erfüllt | Die hinzugefügten Zeilen enthalten kein `innerHTML` und kein `console.`. Der Commit berührt `index.html` nicht. |

## Code-Review
- **Fokus-Diebstahl:** Beim Stoppen wird der Fokus nur zurückgegeben, wenn er vorher auf Abbrechen lag. Das ist korrekt. Beim Start wird der Fokus immer auf Abbrechen gesetzt, auch bei einem Mausklick. Das ist gewollt und unbedenklich, weil der Start eine Nutzeraktion auf genau diesem Bedienelement ist.
- **Fehlendes Element:** Beide Elemente wurden schon vorher in denselben Funktionen ohne Null-Prüfung über `$()` angesprochen. Das Risiko ist also nicht neu, und `test_markup` sichert das Vorhandensein ab.
- **CSP:** Es gibt keine Inline-Handler und keine neuen Quellen. `test_csp_unveraendert` ist grün.
- **Reihenfolge:** `focus()` wird erst nach `disabled = false` aufgerufen, sonst würde der Aufruf wirkungslos bleiben. Der Fokus wird vor `hidden = true` gelesen, sonst wäre `activeElement` schon `body`. Beides ist richtig umgesetzt.

## Nachbesserungen
Keine sind nötig. Optional für später: ein eigener Fokus-Test für den Treffer- und den Fehler-Pfad. Der Code deckt beide Pfade bereits ab.
