# LEAD – Lauf 20261029-0328

## Aufgabe
- **F1 Aufräumen**, S-004–S-006 / S-009–S-013, Draft-PR **#36**
- Branch: `agent/master/20261022-20` (Team-Branch), Kopf `c4ac5c5`
- Lokal: `git checkout -B agent/master/20261022-20 origin/agent/master/20261022-20`

## Lagebild (geprüft von LEAD)
- Alle sechs Team-Branches #36/#39/#40/#41/#44/#45 enthalten origin/main 6dbe114 (behind=0). `git merge-tree --write-tree origin/main <branch>` ist bei allen konfliktfrei. Ein Merge von main ist also nirgends nötig.
- Probe in einem temporären Worktree auf c4ac5c5: `python3 -m unittest discover -s tests` ergibt 216/216 OK. Der Worktree ist wieder entfernt.
- Faire Rotation: F1 wurde zuletzt am 20261028-1729 bearbeitet und ist damit der am längsten unberührte F-Punkt (F6 1929, F4 2328, F3 0029, F5 0128, F2 0229).
- Belegte Lücke in #36:
  1. Lauf 0529 hat S-009–S-013 bewusst auf `"review"` gesetzt, damit `team/agent.py` (`lead()`: `status == "open"`) und `team/runner.py:choose_task()` sie nicht doppelt vergeben. **Kein Test sichert das ab.** `tests/test_vorschlaege.py` prüft nur, ob der Status erlaubt ist. Setzt jemand den Status versehentlich auf `"open"` zurück, bleibt die Suite grün.
  2. Der Testname `test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten` in `tests/test_branches_s006.py` ist sachlich falsch, weil S-006 jetzt `done` ist. Das steht als offene Abweichung K1 im PR-Body.

## Genaue Beschreibung
1. **Neue Testdatei** `tests/test_tasks_f1_review.py`. Sie nutzt nur die Standardbibliothek und lädt `team/runner.py` wie die bestehenden Tests (Muster aus `tests/test_runner.py` übernehmen). Inhalt:
   - Zuordnung `ERWARTET = {"S-009": ("#39", "agent/master/20261022-21"), "S-010": ("#40", "agent/master/20261022-22"), "S-011": ("#41", "agent/master/20261022-2238"), "S-012": ("#44", "agent/master/20261022-23"), "S-013": ("#45", "agent/master/20261023-01")}`
   - Test A: `load_tasks()` (echte `team/tasks.json`) enthält alle fünf IDs. Jede hat `status == "review"`, und ihr `hinweis` enthält PR-Nummer und Branch-Namen aus `ERWARTET`.
   - Test B: `choose_task(tasks, previous_id=X)` liefert für `X` in `None` und allen Aufgaben-IDs nie eine der fünf IDs.
   - Test C: Die Liste, die `team/agent.py` an LEAD gibt, wird nachgebildet: `[t for t in tasks if t.get("status") == "open"]` enthält keine der fünf IDs. Eine reine Nachbildung reicht. agent.py nicht importieren, wenn das Netz oder KI-Clients braucht.
   - Test D (Selbstprüfung): In einer **Kopie** der Aufgabenliste (`copy.deepcopy`) wird S-011 auf `"open"` gesetzt. Dann muss `choose_task` S-011 auswählen können. Damit ist belegt, dass Test B nicht leer durchläuft. `team/tasks.json` wird dabei nicht verändert.
2. **Umbenennen** in `tests/test_branches_s006.py`: `test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten` wird zu `test_s006_erledigt_und_nennt_alle_kandidaten`. Der Testkörper bleibt Zeichen für Zeichen gleich.
3. `team/tasks.json` und `docs/SCHNAPPER-MASTERPLAN.md` bleiben **unverändert**.
4. Ein Commit auf dem Team-Branch, z. B. `SCHNAPPER MASTER: F1 Review-Status S-009–S-013 per Test absichern, S-006-Testname (#36)`.

## Akzeptanzkriterien
1. Es gibt die neue Datei `tests/test_tasks_f1_review.py`. Geändert sind nur diese Datei und `tests/test_branches_s006.py` (Prüfung mit `git diff --stat origin/agent/master/20261022-20`).
2. `python3 -m unittest tests.test_tasks_f1_review -v` zeigt mindestens 4 Tests (A–D), alle OK, 0 Skips.
3. Test A schlägt fehl, wenn in einer Arbeitskopie von `team/tasks.json` S-012 auf `"open"` steht oder `#44` aus dem Hinweis fehlt. Gegenprobe: Datei temporär ändern, Test laufen lassen (rot), danach mit `git checkout -- team/tasks.json` zurücksetzen. Im Bericht festhalten.
4. Test B schlägt fehl, wenn S-009 temporär auf `"open"` steht (gleiche Gegenprobe, danach zurücksetzen).
5. Test D verändert `team/tasks.json` nicht. Nach dem Lauf ist `git status --porcelain team/tasks.json` leer.
6. In `tests/test_branches_s006.py` hat sich nur der Methodenname geändert (`git diff` zeigt genau 1 −/1 + Zeile). Der neue Name kommt vor, der alte nicht mehr.
7. `python3 -m unittest discover -s tests` ist grün: 216 + neue Tests, 0 Fehler.
8. `cd cloudflare && node --test test/*.test.mjs` ergibt 10/10 pass.
9. Der Secret-Scan über den Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY) findet nichts, und unter `.github/` ist nichts geändert.

## Testbefehle
```
cd /home/claude/schnapper
git checkout -B agent/master/20261022-20 origin/agent/master/20261022-20
python3 -m unittest tests.test_tasks_f1_review -v
python3 -m unittest tests.test_branches_s006 tests.test_runner tests.test_vorschlaege -v
python3 -m unittest discover -s tests
(cd cloudflare && node --test test/*.test.mjs)
python3 -m json.tool team/tasks.json >/dev/null && echo json-ok
git diff --stat origin/agent/master/20261022-20
git diff origin/agent/master/20261022-20 | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY' || echo kein-secret
```
Playwright wird nicht gebraucht, weil es keine Änderung an der Oberfläche gibt.

## Sperren
- Kein Push durch BRAIN oder CHECK. Push nur durch COMMAND, ohne Force, als Fast-Forward.
- Keine Änderungen unter `.github/workflows` oder sonst unter `.github/`.
- Keine Secrets, keine Tokens in Dateien oder Commits.
- Keine Live-Netzabrufe (Open Prices, eBay, sonstige). Die Tests laufen offline.
- Keine fremden Branches anfassen, kein Rebase, kein Force-Push. `team/tasks.json` und den Masterplan in diesem Schritt nicht ändern.
- PR #36 bleibt Draft, kein Merge.
- Am Ende `git checkout -q main`.
