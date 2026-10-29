# CHECK – Lauf 20261029-0829

- Start: 2026-10-29T08:36:38Z
- Ende: 2026-10-29T08:40Z
- Geprüft: lokaler Commit **778e998** auf `agent/master/20261022-21`, Elter a87a977 = `origin/agent/master/20261022-21`, noch nicht gepusht
- Prüfung unabhängig, ohne Codeänderung. Nur für die Gegen- und Mutationsproben wurde app.js kurz geändert und danach per `git checkout` zurückgesetzt. Der Arbeitsbaum ist sauber.

## Urteil: **bestanden**
Es gibt eine Empfehlung (kein Blocker): den Konsolenfilter in AK4/AK5 enger fassen, siehe AK 6.

## Git
- `git log --oneline -3`: 778e998 (neu), a87a977, fd16763
- `rev-list --count origin/agent/master/20261022-21..agent/master/20261022-21` = **1**. Der Remote-Kopf ist Vorfahre, also kein Force nötig.
- Diff a87a977..778e998: `app/schnapper/web/app.js` (+10), `tests/test_app_erfassen_s009.py` (+110). Das sind nur die erlaubten Dateien. In app.js ist nur `angebotSpeichern` geändert, dazu das Flag `angebotLaeuft` mit Kommentar direkt davor.
- `git diff origin/main...branch --stat`: 6 Dateien, die ganze S-009-Arbeit (einlesen.py, web.py, app.css, app.js, index.html, Test). Keine Workflows und keine Abhängigkeitsdateien.
- PR #39 per REST abgefragt: `draft: true`, `state: open`, Kopf weiter a87a977 (kein Push)

## Tests (selbst ausgeführt, Chromium aus /opt/pw-browsers, kein `playwright install`)
- `python3 -m unittest tests.test_app_erfassen_s009 -v`: **32/32 OK**, 0 Skips (27 alte + 5 neue `DoppeltAbsenden`)
- `python3 -m unittest discover -s tests`: **248 OK**
- `cd cloudflare && node --test test/*.test.mjs`: **10 pass / 0 fail / 0 skipped**

## Gegenprobe (AK 7)
- sha256 Fix: `9214c178d579d3dc5e14bde5288e210854d4bb81be4a856274aa6721dea2d5fd`
- Mit `git show a87a977:app/schnapper/web/app.js`: **FAILED (failures=3)** von 32. AK1 `2 != 1`, AK2 `2 != 1`, AK3 `False is not true`. AK4 und AK5 bestehen, weil der alte Code den Knopf gar nicht sperrt.
- Zurückgesetzt mit `git checkout --`. sha256 danach identisch, `git status` sauber.
- Zusätzliche Mutationsproben von CHECK:
  - Fix ohne `knopf.disabled = false` im finally: AK3, AK4 und AK5 schlagen fehl. Die Tests erkennen also, ob der Knopf in allen drei Ausgängen wieder frei wird.
  - Fix ohne `if (angebotLaeuft) return;`, also nur mit gesperrtem Knopf: AK2 schlägt fehl. Damit ist belegt, dass das Flag nötig ist.
  - Danach jeweils zurückgesetzt, sha256 identisch.

## Akzeptanzkriterien
1. **erfüllt:** `test_ak1_doppelklick_ein_angebot` mit `dblclick()` prüft: POST-Zähler = 1, CSV hat 1 Datenzeile, Status genau „Gespeichert. Deine Liste hat jetzt 1 Angebot.“, Meldungen leer. Die 300 ms Nachlaufzeit fangen eine verspätete zweite Anfrage ab. Mit altem Code: 2.
2. **erfüllt:** `test_ak2_…` mit 2× `requestSubmit()` in einem `evaluate` ergibt 1 POST und 1 Zeile. Die Mutation ohne Flag schlägt fehl, also wirkt das Flag.
3. **erfüllt:** `test_ak3_…` hält die Route in einer Liste fest (kein sleep), prüft dabei `is_disabled()`, ruft dann `continue_()` auf und prüft `is_enabled()`. CSV hat 1 Zeile.
4. **erfüllt:** `test_ak4_…` schickt einen `http://`-Link und bekommt 422. Die Meldung ist weder „Gespeichert“ noch „Server nicht erreichbar“, der Knopf ist wieder aktiv. Danach wird mit https gespeichert, CSV hat 1 Zeile. Der Status wird beim 422 nicht wörtlich geprüft, nur ausgeschlossen. Das reicht.
5. **erfüllt:** `test_ak5_…` mit `route.abort()` ergibt „Server nicht erreichbar. Läuft SCHNAPPER noch?“, der Knopf ist aktiv.
6. **erfüllt, mit Einschränkung:** Alle Anfragen außer an `self.basis` werden per Kontext-Route (Regex mit negativem Lookahead) abgebrochen. AK1 bis AK3 prüfen eine leere Meldungsliste inklusive `pageerror`. In AK4/AK5 hat CHECK die tatsächlichen Meldungen protokolliert. Es ist jeweils genau eine:
   - AK4: `Failed to load resource: the server responded with a status of 422 (Unprocessable Content)`
   - AK5: `Failed to load resource: net::ERR_FAILED`

   **Bewertung des Filters:** Die Ausnahme ist sachlich gerechtfertigt, weil Chromium diese Netzfehler selbst loggt. Der Filter ist aber breiter, als brain.md behauptet („nur diese eine Meldung“):
   - Es wird jede Meldung verworfen, die die Teilzeichenkette `422` bzw. `ERR_FAILED` enthält.
   - Die Zahl der Meldungen wird nicht geprüft.

   CHECK-Probe: Ein injiziertes `console.error('TypeError: x 422')` wurde vom AK4-Filter verdeckt (gefilterte Liste leer). In der Praxis ist das Risiko gering, weil `pageerror` meist kein „422“ enthält und AK1 bis AK3 streng bleiben.
   **Empfehlung** für den nächsten F2-Lauf: auf genau eine Meldung prüfen, z. B. `assertEqual(len(m), 1)` und `startswith("Failed to load resource")` plus 422 bzw. ERR_FAILED.
7. **erfüllt:** siehe Gegenprobe oben (3 Fehlschläge, sha256 gleich).
8. **erfüllt:** 32/32, die 27 alten grün, 0 Skips. `CHROMIUM = _finde_chromium()` findet chromium-1243 unter /opt/pw-browsers.
9. **erfüllt:** Gesamtsuite 248 OK, Cloudflare 10/10. Im Diff gibt es keine neuen Abhängigkeiten, kein `playwright install` und als URLs nur `x.example` als Testdaten (wird abgebrochen bzw. nur als Feldwert genutzt).
10. **erfüllt:** genau 1 Commit, nur die erlaubten Dateien, kein Push oder Force, PR #39 Draft. Die Commit-Nachricht enthält die Attributionszeilen.

## Weitere Befunde (kein Blocker)
- Codequalität: Der Fix entspricht genau der Vorgabe. Ein `finally` deckt Erfolg, das frühe `return` bei `!antwort.ok` und `catch` ab. Header `X-Schnapper: 1` ist unverändert, kein `innerHTML`, die Meldungen sind gleich geblieben. Ein gesperrter zweiter Submit kehrt still zurück, ohne den Status zu ändern.
- Flag und Knopf bleiben auch während `await suchen()` gesperrt. Das ist sinnvoll und hängt nicht. Wirft `suchen()`, gibt `finally` beides trotzdem frei.
- Altlast, nicht durch diesen Commit verursacht: Wirft `suchen()` nach erfolgreichem Speichern, überschreibt `catch` den Erfolgsstatus mit „Server nicht erreichbar“.

## Secret- und Tabu-Scan
- Diff a87a977..778e998 nach `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token` durchsucht: **0 Treffer**
- Pfade `ZENTNA|JERRY|Beatmaster|.github/workflows`: **0 Treffer**, weder im neuen Commit noch im ganzen Branch-Diff gegen main
