# CHECK – Lauf 20261022-2029 (Runde 2)

**Urteil: bestanden**

Geprüft wurde der lokale Branch `agent/master/20261022-20` @ 4d48068. Er hat 2 Commits auf origin/main e134cd0c98a19bb779ee0a610dd7d1e58d29ec27 (c37283c, 4d48068) und liegt im Klon /home/claude/schnapper. Ich habe nichts geändert, nichts committet oder gepusht und keinen PR angelegt. Danach habe ich `main` wieder ausgecheckt.

## 1. Tests (selbst ausgeführt)
- `python3 -m unittest discover -s tests`: **Ran 190 tests, OK**
- `cd cloudflare && node --test test/*.test.mjs`: **tests 10, pass 10, fail 0**

## 2. Diff und Pfade
`git diff --name-only origin/main...agent/master/20261022-20`:
- docs/SCHNAPPER-MASTERPLAN.md
- team/tasks.json
- tests/test_branches_s006.py

Umfang: 3 Dateien, +133/−23.

**Abweichung tests/:** Die Änderung betrifft genau eine Zeile (64). Aus `assertEqual(s006["status"], "proposed")` wird `assertEqual(s006["status"], "done")`. Die Prüfungen auf die 4 Kandidaten-Branches und auf „Agenten löschen keine Branches“ bleiben unverändert. Der Test wird damit nicht geschwächt. Er ist jetzt sogar strenger als die Runde-0-Variante `assertIn(..., ("proposed","done"))`, denn er erzwingt genau den von Jefrey freigegebenen Status. Die Änderung ist in lead.md (K1) entschieden und in brain.md offengelegt. Ein Rest bleibt: Der Testname `..._bleibt_vorschlag_...` ist sachlich veraltet, wurde aber für einen minimalen Diff bewusst belassen.

## 3. Secret- und Tabu-Scan auf dem Diff
- `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|password`: keine Treffer
- `ZENTNA|JERRY.?AL|Beatmaster|.github/workflows`: keine Treffer; keine Workflow-Datei geändert

## 4. Akzeptanzkriterien aus lead.md
| # | Kriterium | Ergebnis | Beleg |
|---|---|---|---|
| 1 | Basis origin/main | erfüllt | `git merge-base --is-ancestor origin/main HEAD` gibt Exit 0 |
| 2 | JSON gültig, load_tasks, IDs eindeutig | erfüllt | `load_tasks()` liefert 12 Aufgaben: S-000…S-006, S-009…S-013, keine Duplikate. Format (indent 2, ensure_ascii=False) ist byte-identisch mit json.dumps |
| 3 | S-004/5/6 done, Hinweise nur angehängt, „überholt“ | erfüllt | Alle drei `"status": "done"`. Der neue Hinweis beginnt jeweils mit dem alten Hinweis von main (startswith = True). Die übrigen Felder sind gleich. S-006: „…\| Erledigt 22.10.2026 (Freigabe Jefrey, Lauf 20261022-2029): überholt – PRs #2, #6, #7, #8, #9 sind geschlossen bzw. gemergt…“ |
| 4 | S-009…S-013 open, prio 9–13 int, Titel F2…F6, ≥ 2 Kriterien | erfüllt | Status open, Priorität int 9–13, Titel „F2 …“ bis „F6 …“, Kriterien 7/5/4/4/5 |
| 5 | Kein S-007/S-008; S-000–S-003 unverändert | erfüllt | S-007/S-008 fehlen. Der Objektvergleich von S-000–S-003 mit origin/main ergibt Gleichheit |
| 6 | Abschnitt B: 34 PRs korrekt, alte Empfehlung entfernt, Rest unverändert | erfüllt mit dokumentierter Abweichung | Ein Skript hat alle 34 Zeilen gegen `gh api 'repos/jefrey030/schnapper/pulls?state=all&per_page=100'` geprüft: REST 34, Tabelle 34, **0 Abweichungen** bei Titel, Branch, Status mit Merge-Zeit (UTC) und Draft. Es fehlt nichts und es gibt nichts zusätzlich; 12 offen, 15 gemergt, 7 geschlossen. „#6 → #12 → #7 → #8“ steht nur noch im Satz „ist überholt“. **Abweichung:** D.3 wurde geändert, obwohl lead.md „D Punkt 3 bleibt unverändert“ vorsah. Neuer Text: „offene PRs siehe Abschnitt B (keine feste Reihenfolge mehr; …)“. Anlass war Hinweis 6 aus check-1, denn der alte Verweis zeigte auf eine Reihenfolge, die es nicht mehr gibt. Die Änderung liegt im erlaubten Pfad docs/, ist inhaltlich richtig und in brain.md offengelegt. Ich bewerte sie als vertretbar. A, C, E und die Nachträge sind unverändert (nur 2 Hunks: B und D.3) |
| 7 | 190 Tests OK | erfüllt | siehe 1 |
| 8 | 10/10 Cloudflare | erfüllt | siehe 1 |
| 9 | genau 3 Dateien | erfüllt | siehe 2 |
| 10 | Secret-Scan leer | erfüllt | siehe 3 |
| 11 | Draft-PR mit Text (F1, K1, K2) | offen (Aufgabe von COMMAND) | Gehört nicht zu dieser Prüfung |

## 5. Nachbesserungspunkte aus check-1.md
| # | Punkt | Erledigt | Beleg (tasks.json bzw. Diff) |
|---|---|---|---|
| 1 | S-009 textContent | ja | „Erfasste Angebote werden in der Oberfläche nur per textContent angezeigt (kein innerHTML); Test/Prüfung belegt“ |
| 2 | S-010 MAX_MERK/MAX_ALARME | ja | „Import beachtet die Obergrenzen MAX_MERK (200) und MAX_ALARME (50) aus app/schnapper/web/app.js; Überschreitung wird mit Hinweis abgewiesen, Test belegt“. Gegen den Code geprüft: `app/schnapper/web/app.js:7 const MAX_MERK = 200;`, `:8 const MAX_ALARME = 50;` |
| 3 | S-012 „ungetestet“ | ja | „Solange nicht auf echtem Android/Termux-Gerät geprüft, steht in start-schnapper.sh und docs/HANDY-START.md deutlich der Hinweis „auf echtem Gerät ungetestet““ |
| 4 | S-013 Env-Namen und Freigabe-Schalter | ja | „Zugangsdaten nur aus den Umgebungsvariablen SCHNAPPER_EBAY_CLIENT_ID und SCHNAPPER_EBAY_CLIENT_SECRET, nie im Repo; …“ sowie „Quelle „ebay“ bleibt im Quellen-Register gesperrt, bis der Freigabe-Schalter (bestehend: SCHNAPPER_EBAY_FREIGABE in app/schnapper/adapter.py) gesetzt ist …“. Gegen den Code geprüft: `app/schnapper/adapter.py:94 FREIGABE_VARIABLE = "SCHNAPPER_EBAY_FREIGABE"`. Die CLIENT_ID/SECRET-Namen gibt es im Code noch nicht; das ist korrekt, denn sie sind Vorgabe für S-013 |
| 5 | optional: Test streng auf "done" | ja | `self.assertEqual(s006["status"], "done")` |
| 6 | optional: D.3 im PR-Text erwähnen | ja, über das Verlangte hinaus | D.3 wurde direkt korrigiert statt nur erwähnt (siehe Kriterium 6) |

## Hinweise für COMMAND (keine Blocker)
- Im PR-Text unter „Abweichung“ nennen: (a) tests/test_branches_s006.py Zeile 64 (K1, jetzt strikt "done"), (b) Masterplan D.3 angepasst, obwohl lead.md es unverändert lassen wollte.
- K2 nennen: S-007/S-008 nicht übernommen (ID-Kollision mit PR #33); möglicher Textkonflikt am Ende von tasks.json mit #33.
- Kleinigkeit zu S-013: Laut `app/schnapper/quellen.py:42` sperrt im heutigen Code zuerst der Register-Status SPAETER die Quelle „ebay“, erst danach greift SCHNAPPER_EBAY_FREIGABE. Das Kriterium widerspricht dem nicht. Bei der Umsetzung von S-013 muss das Register aber mitbedacht werden.
