# BRAIN – Lauf 20261022-2029 (Gesamtstand nach Nachbesserungsrunde 1)

**Aufgabe:** F1 Aufräumen (tasks.json + Masterplan Abschnitt B), gemäß lead.md; Nachbesserung gemäß check-1.md.
**Branch:** `agent/master/20261022-20` (lokal, Basis `origin/main` = e134cd0c98a19bb779ee0a610dd7d1e58d29ec27; `merge-base --is-ancestor` → Exit 0)
**Commits (2, kein amend):**
1. `c37283c3e11f6727a9b4314840ae2f108063826f` – SCHNAPPER MASTER: F1 Aufräumen – tasks.json und Masterplan Abschnitt B
2. `4d48068d55746f60673388db51d51303150b978f` – SCHNAPPER MASTER: F1 Nachbesserung Runde 1 – Akzeptanzkriterien S-009–S-013 präzisiert
Nicht gepusht, kein PR, nichts gemergt, keine Branches gelöscht, keine Workflows angefasst, keine Secrets. Danach `main` ausgecheckt.

## Geänderte Dateien (`git diff --name-only origin/main...HEAD`)
1. `team/tasks.json`
   - S-004/S-005/S-006 → `done`, bisherige Hinweise vollständig behalten, Erledigt-Text angehängt (S-006: „überholt“, 4 Kandidaten-Branches, „Agenten löschen keine Branches“).
   - Neu S-009…S-013 (F2…F6), `open`, priority 9–13 (int). Kriterienzahl jetzt 7/5/4/4/5.
   - S-000–S-003 unverändert; kein S-007/S-008. Format (indent 2, ensure_ascii=False) erhalten; `load_tasks()` → 12 Aufgaben, IDs eindeutig.
2. `docs/SCHNAPPER-MASTERPLAN.md`
   - Abschnitt B ersetzt: 34 PRs (12 offen, 15 gemergt, 7 geschlossen), per REST geprüft, 0 Abweichungen.
   - Runde 1: D.3 korrigiert (verwies auf nicht mehr existierende „Reihenfolge aus Abschnitt B“) → „offene PRs siehe Abschnitt B (keine feste Reihenfolge mehr; überschneidende PRs zu Preisformaten und Preisalarm zuerst gegeneinander abwägen)“. Sonst A, C, E, Nachträge, Kopfzeile unverändert.
3. `tests/test_branches_s006.py` – nur Zeile 64 (gegenüber main): jetzt `self.assertEqual(s006["status"], "done")` (Runde 0: `assertIn(..., ("proposed","done"))`, in Runde 1 laut Check-Option 5 verschärft). Übrige Prüfungen und Testname unverändert.

## In Runde 1 nachgebessert (check-1.md)
1. S-009 (F2): neues Kriterium „Erfasste Angebote werden in der Oberfläche nur per textContent angezeigt (kein innerHTML); Test/Prüfung belegt“.
2. S-010 (F3): Strukturprüfung je Eintrag, „ungültige Einträge werden gemeldet statt übernommen“; neues Kriterium MAX_MERK (200) / MAX_ALARME (50) – Werte geprüft in app/schnapper/web/app.js:7-8.
3. S-012 (F5): „Solange nicht auf echtem Android/Termux-Gerät geprüft, steht in start-schnapper.sh und docs/HANDY-START.md deutlich der Hinweis ‚auf echtem Gerät ungetestet‘“.
4. S-013 (F6): Zugangsdaten nur aus SCHNAPPER_EBAY_CLIENT_ID / SCHNAPPER_EBAY_CLIENT_SECRET; Sandbox Standard; Produktion nur mit „zusätzlichem Schalter (Name wird in S-013 festgelegt)“ (kein Produktions-Schalter existiert im Code); Quelle „ebay“ gesperrt bis Freigabe-Schalter (bestehend: `SCHNAPPER_EBAY_FREIGABE`, belegt in app/schnapper/adapter.py:94) gesetzt und Zugangsdaten vorhanden.
5. Optional umgesetzt: Testzeile 64 streng auf "done".
6. Optional umgesetzt: Masterplan D.3 korrigiert (s. o.).

## Abweichungen
- **K1:** `tests/test_branches_s006.py` außerhalb team/docs, eine Zeile (64), weil S-006 laut Freigabe `done` wird. Testname `..._bleibt_vorschlag_...` ist sachlich veraltet, bewusst nicht umbenannt (Minimal-Diff). Im PR-Text unter „Abweichung“ nennen.
- **K2:** S-007/S-008 nicht übernommen (ID-Kollision mit offenem PR #33). #33 und dieser Branch ändern beide das Ende von tasks.json → textueller Merge-Konflikt möglich; im PR-Text erwähnen.

## Tests (auf 4d48068)
- `python3 -m unittest discover -s tests` → **Ran 190 tests, OK**
- `cd cloudflare && node --test test/*.test.mjs` → **tests 10, pass 10, fail 0**
- `git diff --name-only origin/main...HEAD` → genau `docs/SCHNAPPER-MASTERPLAN.md`, `team/tasks.json`, `tests/test_branches_s006.py`
- Secret-Scan (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY) → keine Treffer
