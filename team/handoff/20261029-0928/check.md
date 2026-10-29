# CHECK – Lauf 20261029-0928 (F1 / PR #36)

## Urteil: bestanden

## Stand
- Branch `agent/master/20261022-20`, HEAD `85a047fd8055ca2fa2011b49a8a91ab85da2080f`. Das stimmt mit brain.md überein. Elternteil ist `397d0e2` (= origin/agent/master/20261022-20, Ausgangs-SHA aus lead.md). Der Branch liegt 1 Commit vor origin und ist nicht gepusht.
- `git diff origin/agent/master/20261022-20..HEAD --stat`: nur `tests/test_tasks_f1_review.py` (+65/−5).
- `git diff origin/main...HEAD --stat`: docs/SCHNAPPER-MASTERPLAN.md, team/tasks.json, tests/test_branches_s006.py, tests/test_tasks_f1_review.py. Diese Dateien gehören zu früheren Läufen des PR #36, dieser Commit hat nichts davon angefasst. origin/main ist enthalten (merge-base --is-ancestor: Exit 0).

## Eigene Testergebnisse
- `python3 -m unittest tests.test_tasks_f1_review -v`: 6 Tests, OK, 0 Skips.
- `python3 -m unittest discover -s tests`: 222 Tests, OK.
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0, skipped 0.
- Ohne Netz: `unshare -rn python3 -m unittest tests.test_tasks_f1_review` meldet OK. Dasselbe gilt mit entfernten Token- und Proxy-Variablen.
- sha256 von team/tasks.json vor und nach der Suite ist gleich (d86ce4f6…03c2). Die Zahl der Dateien in team/runs ist vorher und nachher 9. `git status` ist sauber.

## Gegenprobe (selbst wiederholt)
- agent.py vorher: sha256 9864393e…fd00.
- Mutation in Zeile 148 auf `t.get("status") in ("open", "review")`. Ergebnis: **FAILED (failures=1, errors=1)**.
  - FAIL in test_c (Fall A).
  - ERROR in test_c3 (Fall C). Ursache ist ein TypeError, weil `vorschlag` None ist. Die Mutation ist damit entdeckt, allerdings über einen Absturz statt über eine Assertion. Das ist ein Schönheitsfehler, kein Mangel.
- Wiederhergestellt mit `git checkout -- team/agent.py`. sha256 danach identisch, `git diff --exit-code team/agent.py` leer, `git status` sauber.

## Akzeptanzkriterien
1. **Erfüllt.** `_lead()` ruft `agent.lead(None, fake)` echt auf.
   - `previous_task_id` ist gepatcht, also wird team/runs nicht gelesen. Geschrieben wird nur in `bericht()`, und das wird nicht aufgerufen.
   - `FakeKI` ersetzt die KI. Der Lauf unter unshare -rn ist OK. Der Test liest keine Umgebungsvariablen. Beim Import von agent wird nur `SCHNAPPER_KI_BACKEND` gelesen, und das ist harmlos.
2. **Erfüllt.** Fall A prüft `status == "FEHLER"` und „ungültige Aufgabe“. Außerdem `werkzeug.offene_aufgaben == ["S-011"]` und, dass von ERWARTET in der Liste an die KI nur S-011 steht.
3. **Erfüllt.** Fall B prüft `status == "OK"` und `plan["aufgabe_id"] == "S-011"`.
4. **Erfüllt.** Fall C prüft `KEINE AUFGABE`, `offene_aufgaben == []` und `fake.aufrufe == 0`.
5. **Erfüllt.** Kopie gegen Deepcopy vorher und `load_tasks() == self.tasks` werden in allen drei Tests geprüft. Der sha256 von tasks.json bleibt unverändert.
6. **Erfüllt.** Siehe Gegenprobe: FAILED, danach wiederhergestellt, sha256 gleich.
7. **Erfüllt.** Modul 6/6 OK mit 0 Skips, Gesamtsuite 222 OK, Cloudflare 10/10.
8. **Erfüllt.**
   - Der Diff zu 397d0e2 umfasst nur die Testdatei.
   - Secret-Scan über `git diff origin/main...HEAD` (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw/Passwort): 0 Treffer.
   - Tabu-Pfade (.github/workflows, ZENTNA, Jerry, Beatmaster): 0 Treffer.
9. **Offen, kein Mangel.** Der Commit ist vorhanden, der Push steht noch aus, weil das Aufgabe von COMMAND ist. Er muss ohne Force erfolgen, und PR #36 muss Draft bleiben.

## Hinweise (nicht blockierend)
- Fall C würde bei der Mutation besser mit einer Assertion scheitern als mit einem TypeError. Das ist optional für einen späteren Lauf.
