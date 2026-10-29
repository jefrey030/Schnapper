# LEAD – Lauf 20261029-0928

## Aufgabe
F1 / PR #36: In `tests/test_tasks_f1_review.py` wird die Nachbildung `test_c_lead_liste_enthaelt_keine_review_aufgabe` durch einen echten Aufruf von `team/agent.py:lead()` ersetzt bzw. ergänzt. Dabei kommen eine Attrappe für die KI und eine Kopie der Aufgaben zum Einsatz, kein Netz. So ist belegt, dass LEAD Aufgaben im Status „review“ (S-009–S-013) weder angeboten bekommt noch annimmt.

**Wahlgrund:**
- Faire Rotation nach `team/runs/INDEX.md`: F1/#36 wurde zuletzt um 20261029-0328 bearbeitet und ist damit am längsten unberührt. Danach folgt F6 um 0428. Der letzte Bericht empfiehlt F1 ebenfalls.
- Ein Merge ist nicht nötig. `git merge-base --is-ancestor origin/main origin/agent/master/20261022-20` ergibt Exit 0, origin/main 6dbe114 ist also enthalten, es gibt keinen Konflikt.
- Der Fund ist belegt (siehe unten): Der bestehende Test sichert die Akzeptanz „keine Doppelvergabe über LEAD“ nicht ab.
- Die INDEX-Einträge zu F1 betreffen andere Dinge: 0529 Merge und PR-Tabelle, 1729 Masterplan-Zahlen, 0328 Regressionstest mit Nachbildung. Die Nachbildung durch einen echten Aufruf zu ersetzen, wurde noch nicht gemacht.

## PR / Branch
- PR: **#36** (Draft)
- Branch (wird fortgesetzt, kein Force-Push): `agent/master/20261022-20`
- Ausgangs-SHA: `397d0e2b96e65e3a6420baf120f037f3fbd09d4b`
- origin/main: `6dbe114` (bereits enthalten)

## Betroffene Dateien
- `tests/test_tasks_f1_review.py` (einzige erlaubte Änderung)
- Nicht ändern: `team/agent.py`, `team/runner.py`, `team/tasks.json`, `.github/workflows/*`

## Fehlerbeschreibung mit Fundstelle
Fundstelle ist `tests/test_tasks_f1_review.py` auf dem Branch, in `test_c_lead_liste_enthaelt_keine_review_aufgabe` (ca. Zeilen 53–56):
```python
# Nachbildung der Auswahl in team/agent.py lead(): nur status == "open".
offen = [t for t in self.tasks if t.get("status") == "open"]
self.assertFalse({t["id"] for t in offen} & set(ERWARTET))
```
- Der Test baut den Filter selbst nach und ruft `team/agent.py` gar nicht auf. Der echte Filter steht in `team/agent.py:148` (`offen = [t for t in aufgaben if t.get("status") == "open"]`), die Prüfung der KI-Wahl in `agent.py:161-165` (`gueltig = {t["id"]: t for t in offen}` und `status="FEHLER"`).
- Wenn `agent.py` geändert wird, bleibt der Test trotzdem grün.

**Reproduktion (von LEAD ausgeführt, in einer Kopie per `git archive` unter `scratchpad/lead36`):**
- Zeile 148 in `team/agent.py` wurde mutiert zu `t.get("status") in ("open", "review")`.
- `python3 -m unittest tests.test_tasks_f1_review` meldet danach **OK** (4/4). Die Mutation bleibt also unentdeckt.
- Das Skript `scratchpad/repro36.py` zeigt, dass `agent` ohne Netz importierbar ist. `agent.lead(None, Fake)` mit `Fake.frage()` → `{"text": json.dumps({"aufgabe_id": ...})}` funktioniert. Mit den echten Aufgaben ergibt das `status="KEINE AUFGABE"` und `werkzeug.offene_aufgaben=[]`.
- Ausgangsstand ungemutiert: Suite `python3 -m unittest discover -s tests` meldet OK (1 Skip).

## Vorgabe für den Test (Skizze)
- `import agent` mit `sys.path` auf `team/` (das ist dort schon gesetzt).
- Die Attrappe `class FakeKI: def frage(self, system, nutzer): self.nutzer = json.loads(nutzer); return {"text": json.dumps({"aufgabe_id": self.wahl})}`.
- `unittest.mock.patch.object(agent, "load_tasks", return_value=kopie)` mit einer Deepcopy der Aufgaben, in der S-011 auf `"open"` steht. Zusätzlich `patch.object(agent, "previous_task_id", return_value=None)`, damit `team/runs` nicht gelesen wird.
- Fall A: Die KI wählt `"S-009"` (Status review). Erwartet werden `status == "FEHLER"` und `"ungültige Aufgabe"` in `fehler`. `werkzeug["offene_aufgaben"] == ["S-011"]`, und in `fake.nutzer["offene_aufgaben"]` steht keine ID aus ERWARTET außer S-011.
- Fall B: Die KI wählt `"S-011"`. Erwartet werden `status == "OK"` und `plan["aufgabe_id"] == "S-011"` (Selbstprobe, damit der Test nicht nur „immer FEHLER“ prüft).
- Fall C: Mit den echten Aufgaben, ohne Patch von `load_tasks`, erwartet: `status == "KEINE AUFGABE"`, und `FakeKI.frage` wird nicht aufgerufen.
- Den Kommentar „Nachbildung …“ entfernen oder `test_c` durch den echten Aufruf ersetzen.

## Akzeptanzkriterien
1. `tests/test_tasks_f1_review.py` ruft `team/agent.py:lead()` echt auf, mit KI-Attrappe, ohne Netz, ohne Umgebungsvariablen und ohne Schreiben in `team/runs`.
2. Fall A: Wählt die KI eine review-Aufgabe (S-009), gibt `lead()` `status == "FEHLER"` zurück, und die an die KI übergebene Liste `offene_aufgaben` enthält keine review-Aufgabe.
3. Fall B: Ist S-011 in der Kopie `open` und wählt die KI S-011, ist das Ergebnis `status == "OK"` und `plan["aufgabe_id"] == "S-011"`.
4. Fall C: Mit dem echten `team/tasks.json` liefert `lead()` `"KEINE AUFGABE"`, und die KI wird nicht befragt.
5. Das echte `team/tasks.json` und die Kopie der Aufgaben bleiben unverändert (Vergleich mit `load_tasks()` vorher/nachher).
6. **Gegenprobe (Pflicht):** Mit der Mutation `team/agent.py:148` → `t.get("status") in ("open", "review")` schlägt mindestens ein neuer Test fehl, nicht OK. Danach wird `agent.py` wiederhergestellt, `git diff team/agent.py` ist leer, sha256 vorher/nachher gleich.
7. Modul `tests.test_tasks_f1_review`: alle Tests OK, 0 Skips. Gesamtsuite OK, Cloudflare 10/10.
8. Der Diff zum Ausgangs-SHA 397d0e2 umfasst nur `tests/test_tasks_f1_review.py`. Es gibt keine Secrets und keine Änderung an Workflows.
9. Neuer Commit auf `agent/master/20261022-20`, Push ohne Force, PR #36 bleibt Draft.

## Testbefehle
```
cd /home/claude/schnapper   # Branch agent/master/20261022-20 auschecken (Kopf 397d0e2)
python3 -m unittest tests.test_tasks_f1_review -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
# Gegenprobe:
sha256sum team/agent.py
sed -i '148s/t.get("status") == "open"/t.get("status") in ("open", "review")/' team/agent.py
python3 -m unittest tests.test_tasks_f1_review   # muss FAILED zeigen
git checkout -- team/agent.py && sha256sum team/agent.py && git diff --exit-code team/agent.py
```
Browsertests sind nicht nötig, das ist eine reine Python-Änderung. Falls doch welche laufen: Playwright mit dem vorinstallierten Chromium, kein `playwright install`.
