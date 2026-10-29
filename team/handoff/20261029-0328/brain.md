# BRAIN – Lauf 20261029-0328

## Branch / Commit
- Branch `agent/master/20261022-20` (Basis origin c4ac5c5), lokal ausgecheckt, **nicht gepusht**
- Commit `397d0e2b96e65e3a6420baf120f037f3fbd09d4b`
  "SCHNAPPER MASTER: F1 Review-Status S-009–S-013 per Test absichern, S-006-Testname (#36)"

## Geänderte Dateien (`git diff --stat origin/agent/master/20261022-20`)
- `tests/test_tasks_f1_review.py` (neu, 70 Zeilen): ERWARTET-Zuordnung, Tests A–D
- `tests/test_branches_s006.py` (1 −/1 +): `test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten` → `test_s006_erledigt_und_nennt_alle_kandidaten`, Testkörper unverändert
- `team/tasks.json` und `docs/SCHNAPPER-MASTERPLAN.md` sind unverändert.

## Eigene Testergebnisse
- `python3 -m unittest tests.test_tasks_f1_review -v`: 4 Tests (A, B, C, D), alle OK, 0 Skips
- `tests.test_branches_s006 tests.test_runner tests.test_vorschlaege`: 16/16 OK
- `python3 -m unittest discover -s tests`: **220/220 OK** (216 + 4)
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0
- `json.tool team/tasks.json`: json-ok
- Alter Testname kommt 0-mal vor, der neue 1-mal.
- Secret-Scan über den Diff: kein-secret. Unter `.github/` ist nichts geändert.

## Gegenproben (jeweils mit `git checkout -- team/tasks.json` zurückgesetzt)
1. S-012 auf "open": rot. A failt (subTest S-012), dazu B (alle 13 previous_id) und C, insgesamt failures=15
2. "#44" aus dem Hinweis von S-012 entfernt: rot, A failt (S-012), failures=1
3. S-009 auf "open": rot. A (S-009), B (13 previous_id) und C failen, failures=15
- Danach ist `git status --porcelain team/tasks.json` leer. Test D arbeitet nur auf einer deepcopy und prüft zusätzlich, dass `load_tasks()` danach gleich bleibt.

## Hinweise / offene Punkte
- In der echten tasks.json steht derzeit **keine** Aufgabe auf "open". `choose_task` liefert deshalb immer None, und Test B allein wäre trivial grün. Test D belegt, dass das Testgerüst greift.
- Für PR-Nummer und Branch prüft Test A auf Wortgrenzen (Regex), damit z. B. `#4` nicht auf `#44` passt.
- Widerspruch in den Vorgaben: lead.md verlangt am Ende `git checkout -q main`, der Auftrag an BRAIN sagt "Branch ausgecheckt lassen". Der Auftrag hat Vorrang, der Branch bleibt ausgecheckt. Den Wechsel auf main macht COMMAND.
- Offen für COMMAND: K1 im PR-Body von #36 als erledigt markieren. Push als Fast-Forward durch COMMAND. PR #36 bleibt Draft.
