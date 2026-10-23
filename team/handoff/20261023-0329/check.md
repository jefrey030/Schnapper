# CHECK – Lauf 20261023-0329

- Start: 2026-10-23T03:34:17Z (UTC)
- Ende: 2026-10-23T03:36Z (UTC)
- Prüfer: AGENT CHECK. Ich habe unabhängig geprüft und alles selbst belegt; brain.md diente nur zum Abgleich.
- Branch: `agent/master/20261022-22`, HEAD `1adad0c`, lokal und nicht gepusht. `team/handoff/` ist ungetrackt.
- Code wurde nicht geändert, nichts committet, nichts gepusht. Der temporäre Worktree für die Gegenprobe ist wieder entfernt (`git worktree list` zeigt nur das Hauptverzeichnis).

## Urteil: **bestanden**

## Belege

### Verlauf
`git log --oneline -5`:
```
1adad0c SCHNAPPER MASTER: F3 Alarm-Prüfung an Server-Regeln angeglichen (S-010)
2697c30 SCHNAPPER MASTER: main (#34, #37, #42, #43) in F3 übernommen (S-010)
6dbe114 security(SCHNAPPER): token only via HTTPS, block redirects (#43)
6d91dfa fix(SCHNAPPER): sicherer Preisimport URLs und Preisalarme (#42)
1926983 fix(SCHNAPPER): invalid maximum-price filters reject (#34)
```
- **Eltern von 2697c30:** `3ab36fa5519d…` (origin/agent/master/20261022-22) und `6dbe114271b3…` (origin/main).
- **Kein umgeschriebener Verlauf:** `merge-base --is-ancestor origin/main HEAD` ist ok, `--is-ancestor origin/agent/master/20261022-22 HEAD` ebenfalls.
- **Keine Konflikte von Hand aufgelöst:**
  - Der Baum von `git merge-tree --write-tree 3ab36fa 6dbe114` ist `0586d3af…`. Der Baum des Merge-Commits ist identisch (`0586d3af…`).
  - `git diff-tree --cc` zeigt keine kombinierten Hunks.

### Diff
- `git diff origin/main...HEAD --stat` und `git diff origin/main HEAD --stat` enthalten genau 4 Dateien mit +443:
  - `app/schnapper/web/app.css`
  - `app/schnapper/web/app.js`
  - `app/schnapper/web/index.html`
  - `tests/test_app_sicherung_s010.py`
- Der Anpassungs-Commit 1adad0c ändert nur zwei Dateien:
  - `app.js` (+9/−3): ausschließlich in `sicherungPruefen`. `zahlText` wird durch `zahlWert`, `maxPreisOk` und `minRabattOk` ersetzt.
  - `tests/test_app_sicherung_s010.py` (+56, 0 entfernte Zeilen): AK1–AK9 sind unverändert.
- Merklisten-Prüfung sowie die Prüfungen für Größe und MAX_MERK/MAX_ALARME sind unberührt. Die Meldetexte bleiben `Alarme: Eintrag N ungültig (max_preis|min_rabatt)`.
- Keine Dateien unter `.github/` und keine Pfade von ZENTNA, JERRY AL oder Beatmaster.
- Python unter `app/schnapper/` ist gegenüber origin/main unverändert (`git diff --quiet` ok).

### Secret-Scan
- Ich habe `git diff origin/main...HEAD` nach `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token` (ohne Groß-/Kleinschreibung) durchsucht: 0 Treffer.
- Im Diff stehen nur zwei URLs, beide in Tests: `https://beispiel.example/1` als Testdatum und `http://127.0.0.1` für den lokalen Testserver. Es gibt keine externen Preisquellen.

### Tests (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest discover -s tests` | **Ran 224 tests, OK** (kein `skipped`). `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` ist in der Umgebung gesetzt. |
| `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 -m unittest -v tests.test_app_sicherung_s010` | **8/8 OK**. Alle 4 `Browser.*`-Tests liefen mit „ok“, keiner mit „skipped“, darunter `test_alarmgrenzen_wie_server`. |
| `cd cloudflare && node --test test/*.test.mjs` | **tests 10, pass 10, fail 0, skipped 0** |

### Eigene Gegenprobe (AK7)
- Aufbau: temporärer Worktree im Scratchpad auf HEAD, darin `app.js` von 2697c30 (alter Stand mit `zahlText`).
- Ergebnis von `tests.test_app_sicherung_s010`: **FAILED (failures=3)**.
  - `test_alarmgrenzen_wie_server` schlug zweimal fehl (Browser-Test und Subtests).
  - `test_alarmpruefung_wie_server` schlug ebenfalls fehl.
- Danach habe ich den Worktree entfernt.

### Inhaltlicher Abgleich mit den Server-Regeln (main)
Server-Regeln:
- `web.py` `filter_aus_query`:
  - `max_preis = geld(...)` und Wert > 0.
  - `min_rabatt = Decimal(x.replace(",", "."))`, endlich, Wert zwischen 0 und 100.
- `angebot.geld`:
  - Bei genau einem Trenner gilt `\d+[.,]\d{1,2}`, sonst Fehler.
  - Ganzzahl `\d+`.
  - € und Leerzeichen werden entfernt.

Fuzzing:
- 222.222 Kombinationen aus `0159,.-€ e` (Länge 0–5) plus Grenzwerte wie `999999999,99`, `100,00`, `100.01`, `0,01` und `0.00`.
- Jede Eingabe lief gegen die Client-Regel (gleiche Regex und Grenzen) und gegen das echte `filter_aus_query`.

Ergebnis:
- **0 Fälle, in denen der Client annimmt und der Server ablehnt.** AK6 ist also auch jenseits der Testwerte erfüllt.
- In 15.767 Fällen ist der Client strenger als der Server, z. B. `10€`, `-0`, `1e1` oder Leerzeichen. Das ist laut lead.md gewollt. Folge: Solche Einträge aus einer Sicherung werden gemeldet statt übernommen.

## Akzeptanzkriterien
| AK | Status | Beleg |
|---|---|---|
| 1 Merge-Eltern 3ab36fa + 6dbe114, beide is-ancestor, kein Rebase | bestanden | siehe Verlauf |
| 2 Keine manuelle Konfliktlösung, Diff nur 4 erlaubte Dateien | bestanden | Baum identisch mit merge-tree; Stat siehe oben |
| 3 Anpassung nur app.js (sicherungPruefen) und Testdatei | bestanden | `git show 1adad0c` |
| 4 Abweisung von 0, 1,234, 1.2345, 150, 100,5 mit Meldung samt Feldname | bestanden | Subtests in `test_alarmgrenzen_wie_server` grün, Fuzz-Abgleich |
| 5 Gültige Werte weiter übernommen, AK1–AK9 unverändert grün | bestanden | Subtests grün; Testdatei ohne entfernte Zeilen |
| 6 Übernommene Alarme vom Server akzeptiert, keine Karte zeigt „Eingabe ungültig“ | bestanden | Browsertest prüft die Karten und `/api/suche` mit Status 200; Fuzzing ohne Gegenbeispiel |
| 7 Gegenprobe dokumentiert | bestanden | brain.md und eigene Wiederholung: 3 Fehlschläge |
| 8 discover grün, ≥ 216 + F3 + neue Tests | bestanden | 224 OK |
| 9 S-010-Browser-Tests wirklich ausgeführt | bestanden | 8/8 ok, 0 skipped |
| 10 Cloudflare 10/10 | bestanden | 10 pass, 0 fail |
| 11 Secret-Scan 0, kein .github/workflows, keine externen Preisquellen | bestanden | siehe oben |
| 12 index.html/CSP gegenüber 3ab36fa unverändert | bestanden | `git diff 3ab36fa HEAD -- index.html` leer; `test_ak9_csp_unveraendert` ok |

## Hinweise (nicht blockierend)
- In `tests/test_app_sicherung_s010.py` steht noch der Pfad `CHROMIUM = …/chromium-1194/…`. Installiert ist aber nur `chromium-1243`.
  - Die Browser-Tests laufen trotzdem, weil `skipUnless` als Ersatz auf die gesetzte Variable `PLAYWRIGHT_BROWSERS_PATH` zurückfällt.
  - Ohne diese Variable würden sie still übersprungen. Das ist ein Kandidat für einen Folgeschritt.
- Der Client ist in Randfällen strenger als der Server (siehe oben). Das ist laut Plan gewollt und hat keine Folgen für AK6.
- Der Push steht noch aus und ist Sache von COMMAND.
