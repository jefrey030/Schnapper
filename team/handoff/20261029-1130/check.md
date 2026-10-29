# CHECK – Lauf 20261029-1130 (F4 = S-011, PR #41)

## Urteil: **bestanden**

Geprüft wurde der Commit `6fd9ffd94e9dd7ca714d017ec419826727860954` auf `agent/master/20261022-2238`. Sein Elternteil ist `175d7b7` (= `origin/agent/master/20261022-2238`), es ist also ein reiner Fast-Forward. `origin/main` 6dbe114 ist enthalten (`merge-base --is-ancestor`: Exit 0). Grundlage waren nur lead.md, brain.md und eigene Prüfungen.

## Diff
- `git diff origin/agent/master/20261022-2238..HEAD` betrifft 2 Dateien mit +43/−0:
  - `app/schnapper/web/app.js`: +5, nur in `kameraScannen()` direkt nach `kamera.stream = stream;`
  - `tests/test_app_kamera_s011.py`: +38, zwei neue Methoden in `Browser`
- `git diff origin/main...HEAD` (der ganze PR) betrifft app.css, app.js, index.html und test_app_kamera_s011.py. Die Änderungen an app.css und index.html stammen aus früheren Läufen, der neue Commit berührt sie nicht.
- Der Code entspricht der Lösungsskizze aus lead.md: ein `ended`-Listener mit `{ once: true }` pro Video-Track und der Wächter `kamera.stream === stream`.

## Akzeptanzkriterien
| # | Kriterium | erfüllt | Beleg |
|---|---|---|---|
| 1 | Nach `ended` innerhalb von ≤1 s `alles_gestoppt()` und Status genau „Kamera wurde getrennt – Barcode bitte eintippen.“ | ja | `test_track_ended_von_aussen`: `warte(...hidden, sekunden=1)`, dann `alles_gestoppt()` (Tracks gestoppt, srcObject null, Bereich verborgen, Abbrechen unsichtbar, Knopf frei) und `assertEqual(status, …)`. Grün. Mutation M3 (andere Meldung) führt zu FAIL. |
| 2 | Keine weiteren detect-Aufrufe nach 500 ms, `abfragen == []`, Barcode-Feld leer | ja | Gleicher Test: `__detect` vor und nach 500 ms gleich, `assertEqual(self.abfragen, [])`, `input_value("#barcode") == ""` |
| 3 | Neustart ergibt `__gum == 2` und einen sichtbaren Bereich, Abbrechen stoppt sauber | ja | Gleicher Test, letzter Block: Klick, `warte(!hidden)`, `__gum == 2`, Abbrechen, `alles_gestoppt()` |
| 4 | Ein veraltetes `ended` stört Lauf 2 nicht | ja | `test_veraltetes_track_ended_stoert_nicht`: Bereich bleibt sichtbar, Status ist nicht die Trenn-Meldung, `__tracks[1].readyState == 'live'`, danach Abbrechen und `alles_gestoppt()`. Grün. Mutation M2 führt zu FAIL. |
| 5 | Fokus wandert von Abbrechen zu `#kamera-knopf` | ja | Gleicher Test wie AK1: `fokus() == "kamera-abbrechen"` vorher, `"kamera-knopf"` nachher |
| 6 | `test_app_js` grün, kein innerHTML, `fetch(`, `console.` oder URL | ja | `test_app_js ... ok`. Ein grep über die +-Zeilen des neuen Commits findet keinen Treffer. |
| 7 | CSP unverändert | ja | `test_csp_unveraendert ... ok`. `web.py` steht nicht im Diff. |
| 8 | Neue Tests stehen in `Browser`, nutzen die vorhandenen Hilfen, Fixtures unverändert, tearDown greift | ja | Beide Methoden stehen in `class Browser` und nutzen `oeffne`, `starte`, `warte`, `alles_gestoppt` und `kurz_warten`. Der Diff besteht nur aus Zusätzen ab Zeile 684, MEDIEN (Z. 50) und MEDIEN_VERZOEGERT (Z. 109) sind unberührt. `tearDown` prüft `fremd == []` und `meldungen == []`. |
| 9 | Gegenprobe: beide Pflicht-Mutationen ergeben FAIL, danach Rücksetzung mit gleicher sha256 | ja | Selbst nachvollzogen, siehe unten (M1, M2) |
| 10 | Kamera-Modul ≥30 OK ohne Skips, Python gesamt Ausgangszahl +2, Cloudflare 10/10 | ja | Kamera 30 OK und 0 Skips, Python 246 OK (BRAIN: vorher 244), Cloudflare 10/10 |
| 11 | Ein Commit, nur Fast-Forward, PR-Beschreibung ergänzt, PR bleibt Draft | ja (Teil von CHECK) / offen (COMMAND) | Es gibt genau einen Commit, Elternteil 175d7b7, die Nachricht hat Trailer. Push und Ergänzung der PR-Beschreibung von #41 sind laut lead.md Aufgabe von COMMAND nach „bestanden“ und stehen noch aus. |

## Testzahlen (selbst ausgeführt, vorinstalliertes Chromium, kein `playwright install`)
| Suite | Ergebnis |
|---|---|
| `python3 -m unittest tests.test_app_kamera_s011 -v` | Ran 30, OK, 0 Skips |
| Einzeltests `test_track_ended_von_aussen` und `test_veraltetes_track_ended_stoert_nicht` | Ran 2, OK |
| `python3 -m unittest discover -s tests` | Ran 246, OK |
| `cd cloudflare && node --test test/*.test.mjs` | 10 tests, 10 pass, 0 fail, 0 skipped |

## Gegenprobe (eigene Mutationen, danach `git checkout -- .`)
| Mutation | betroffener Test | Ergebnis |
|---|---|---|
| M1: Listener abgeschaltet (`if (0) t.addEventListener(...)`) | `test_track_ended_von_aussen` | **FAIL** „Zeitüberschreitung: …kamera-bereich').hidden“ |
| M2: Wächter durch `true` ersetzt | `test_veraltetes_track_ended_stoert_nicht` | **FAIL** „True is not false“ |
| M3 (eigene): Meldung ersetzt durch „Kein Barcode erkannt.“ | `test_track_ended_von_aussen` | **FAIL** (Statusvergleich) |
| M4 (eigene): `getVideoTracks()` ersetzt durch `getAudioTracks()` | `test_track_ended_von_aussen` | **FAIL** |

Nach der Rücksetzung hat app.js die sha256 `cdaa3a4011c652cd6b42ca649413333d76ff88b1489509b208d432a495cd4d18`. Das ist derselbe Wert wie vor den Mutationen und wie bei `git show HEAD:app/schnapper/web/app.js`. `git status --short` ist leer.

## Secret- und Pfad-Scan
- **Secrets:** Ich habe sowohl `origin/main...HEAD` als auch den neuen Commit nach `sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY` und `passw`/`password` durchsucht (beim neuen Commit zusätzlich nach `secret` und `token`). Es gibt **keinen Treffer**.
- **Tabu-Pfade:** `.github/workflows`, ZENTNA, JERRY AL und Beatmaster kommen in den geänderten Pfaden **nicht** vor.
- **Erlaubte Dateien:** Der neue Commit ändert nur `app/schnapper/web/app.js` (nur in `kameraScannen()`) und `tests/test_app_kamera_s011.py` (nur neue Tests). index.html, app.css und web.py bleiben im neuen Commit unberührt. Es gibt keine neuen Abhängigkeiten.

## Hinweis für COMMAND
Aus Sicht von CHECK spricht nichts gegen den Push als Fast-Forward von 175d7b7 auf 6fd9ffd. Danach den Abschnitt „Update Lauf 20261029-1130“ an die PR-Beschreibung von #41 anhängen. Der PR bleibt Draft.

Arbeitsbaum am Ende sauber, kein Code geändert, nichts committet oder gepusht.
