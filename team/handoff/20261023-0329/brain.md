# BRAIN – Lauf 20261023-0329

- Start: 2026-10-23T03:31:15Z (UTC)
- Ende: 2026-10-23T03:34Z (UTC)
- Branch: `agent/master/20261022-22` (PR #40, F3/S-010), lokal von `origin/agent/master/20261022-22` (3ab36fa) ausgecheckt. **Nicht gepusht.**

## Commits (lokal)
| Art | SHA | Nachricht |
|---|---|---|
| Merge | `2697c30182440fbd3d6ae9e1ab8036c9ae069ad7` | SCHNAPPER MASTER: main (#34, #37, #42, #43) in F3 übernommen (S-010) |
| Anpassung | `1adad0ccf0b0f44be3715a170c440f9e9f6d3996` | SCHNAPPER MASTER: F3 Alarm-Prüfung an Server-Regeln angeglichen (S-010) |

- Eltern des Merge-Commits: 3ab36fa + 6dbe114. Die Zusammenführung lief ohne Konflikte (ort), es wurde nichts von Hand aufgelöst.
- `git merge-base --is-ancestor origin/main HEAD` und `... origin/agent/master/20261022-22 HEAD`: beide ok. Es gab keinen Rebase.

## Geänderte Dateien
- Anpassungs-Commit: `app/schnapper/web/app.js` (+9/−3, nur in `sicherungPruefen`) und `tests/test_app_sicherung_s010.py` (+56).
- `git diff origin/main HEAD --stat`: genau `app.css`, `app.js`, `index.html`, `tests/test_app_sicherung_s010.py` (4 Dateien, +443).
- `index.html` ist gegenüber 3ab36fa unverändert (Diff 0 Zeilen), die CSP ebenfalls.

## Umsetzung
`zahlText` wurde durch zwei Prüfungen ersetzt. Komma gilt jeweils als Dezimaltrenner:
- `maxPreisOk`: `""` oder `/^[0-9]{1,9}(?:[.,][0-9]{1,2})?$/` und Wert > 0.
- `minRabattOk`: `""` oder `/^[0-9]{1,3}(?:[.,][0-9]{1,2})?$/` und Wert zwischen 0 und 100.

Die Meldetexte sind unverändert: `Alarme: Eintrag N ungültig (max_preis|min_rabatt)`.

## Neue Tests
- `Browser.test_alarmgrenzen_wie_server`: stellt eine Sicherung mit 5 Alarmen wieder her.
  - Gültig: `max_preis` 12,50 und `min_rabatt` 100.
  - Ungültig: `max_preis` 0, `max_preis` 1,234 und `min_rabatt` 150.
  - Geprüft wird:
    - Die Meldung lautet „2 Alarme; 3 ungültige“.
    - Es gibt 3 Fehlerzeilen, jede mit Feldname.
    - Im localStorage stehen genau „Rad“ und „Bohrer“.
    - Keine der beiden Alarmkarten zeigt „Eingabe ungültig“.
  - Zusätzlich gibt es Subtests direkt gegen `sicherungPruefen`:
    - Abgewiesen werden 0, 0,00, 1,234, 1.2345, 10€ und −5 bei `max_preis` sowie 150 und 100,5 bei `min_rabatt`.
    - Angenommen werden 100, 12,50, 99.9 und 12.50 bei `max_preis` sowie 0, 20,5 und 100 bei `min_rabatt`.
  - Für jeden gültigen Wert wurde gegengeprüft, dass `/api/suche` (lokaler Testserver) mit HTTP 200 antwortet.
- `Statisch.test_alarmpruefung_wie_server`: prüft, dass `zahlText` entfernt ist und beide neuen Muster vorhanden sind.
- Die bestehenden Tests AK1–AK9 sind unverändert.

## Testergebnisse
| Zeitpunkt / Prüfung | Ergebnis |
|---|---|
| Reiner Merge-Stand: `unittest discover` | 222 Tests OK |
| Reiner Merge-Stand: S-010 | 6/6 OK, Browser-Klasse ausgeführt |
| Reiner Merge-Stand: Cloudflare | 10/10 pass |
| Nach Anpassung: `python3 -m unittest discover -s tests` | **224 Tests OK**, 0 Fehler |
| Nach Anpassung: `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 -m unittest -v tests.test_app_sicherung_s010` | **8/8 OK**, alle 4 Browser-Tests ausgeführt, nicht übersprungen |
| Nach Anpassung: `cd cloudflare && node --test test/*.test.mjs` | **10/10 pass**, 0 fail |
| Secret-Scan `origin/main...HEAD` (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY) | 0 Treffer |
| Änderungen unter `.github/` | keine |
| Netzabrufe | keine; Playwright blockiert fremde Hosts, `fremd == []` |

**Gegenprobe:** Im temporären Worktree (Scratchpad) liefen die neuen Tests gegen das alte `app.js` mit `zahlText`. Ergebnis: FAILED (3 Fehlschläge). Danach wurde der Worktree verworfen.
- Der Browsertest scheiterte mit „Wiederhergestellt: 0 gemerkt, 5 Alarme; 0 ungültige Einträge übersprungen“ statt „2 Alarme; 3 ungültige“.
- Zusätzlich gab es Konsolenfehler mit 400er-Antworten vom Server.
- Der statische Test scheiterte ebenfalls.

## Offene Punkte
- Der Push des Branches steht noch aus. Er ist laut Plan Sache von COMMAND nach CHECK.
- `CHROMIUM` in der Testdatei verweist auf `chromium-1194`. Diese Version ist nicht installiert (vorhanden ist `chromium-1243`). Die Browsertests laufen über `PLAYWRIGHT_BROWSERS_PATH`. Ohne die Variable würden sie übersprungen. Den Pfad habe ich nicht geändert, weil das außerhalb des Auftrags liegt; möglicher Folgeschritt.
- Der Client ist bei `max_preis="10€"` strenger als der Server: `geld()` entfernt das €-Zeichen. Das ist gewollt laut Plan.
- `min_rabatt` beim Server: `Decimal` akzeptiert z. B. `"1e1"`, der Client weist das ab. Auch hier ist der Client nur strenger, ohne Folgen für AK6.
