# BRAIN – Lauf 20261029-0928 (F1 / PR #36)

## Branch / Commit
- Branch: `agent/master/20261022-20`, Ausgangs-SHA `397d0e2b96e65e3a6420baf120f037f3fbd09d4b` (abgeglichen)
- Neuer Commit: `85a047fd8055ca2fa2011b49a8a91ab85da2080f` ("SCHNAPPER MASTER: F1-Test ruft lead() echt auf statt Nachbildung (#36)"), **nicht gepusht**
- `git diff --stat 397d0e2 HEAD`: nur `tests/test_tasks_f1_review.py` (65 Einfügungen, 5 Löschungen)

## Geänderte Dateien
- `tests/test_tasks_f1_review.py` (einzige Änderung)

## Beschreibung der Änderung
- Neu sind `import agent`, `json` und `unittest.mock` sowie die Klasse `FakeKI`. Sie zählt `aufrufe`, speichert `nutzer` als JSON und gibt `{"text": json.dumps({"aufgabe_id": wahl})}` zurück.
- Der Helfer `_lead(wahl, aufgaben=None)` patcht `agent.previous_task_id` auf `None`, damit `team/runs` nicht gelesen wird. Wird `aufgaben` mitgegeben, patcht er zusätzlich `agent.load_tasks`. Danach ruft er `agent.lead(None, fake)` echt auf.
- Die Nachbildung `test_c_lead_liste_enthaelt_keine_review_aufgabe` wurde entfernt und durch drei Tests ersetzt:
  - `test_c_lead_bietet_review_nicht_an_und_lehnt_review_wahl_ab` (Fall A): In der Kopie ist S-011 offen, die KI wählt S-009. Erwartet werden `FEHLER`, „ungültige Aufgabe“ im Fehlertext und `offene_aufgaben == ["S-011"]`. In der Liste, die die KI bekommt, steht von ERWARTET nur S-011. Kopie und `load_tasks()` bleiben unverändert.
  - `test_c2_selbstpruefung_lead_nimmt_offene_kopie_an` (Fall B): Die KI wählt S-011. Erwartet werden `OK` und `plan["aufgabe_id"] == "S-011"`. Kopie und Original bleiben unverändert.
  - `test_c3_lead_mit_echten_aufgaben_ohne_ki_frage` (Fall C): Mit dem echten tasks.json kommt `KEINE AUFGABE` zurück, `offene_aufgaben == []`, und es gibt `fake.aufrufe == 0`. `load_tasks()` bleibt unverändert.
- Der Docstring des Moduls wurde ergänzt. Kein Netz, keine Umgebungsvariablen, kein Schreiben in `team/runs`.

## Gegenprobe
```
sha256sum team/agent.py   # 9864393e559748f0c7c06641779162e4d1636e96c6caf413640468353c04fd00
sed -i '148s/t.get("status") == "open"/t.get("status") in ("open", "review")/' team/agent.py
python3 -m unittest tests.test_tasks_f1_review
```
Ergebnis: **FAILED (failures=1, errors=1)** bei 6 Tests.
- Fall A schlägt fehl (FAIL), weil S-009 jetzt angeboten und angenommen wird.
- Fall C bricht mit einem ERROR ab: `offen` ist nicht leer, `choose_task` gibt aber `None` zurück, und `vorschlag["id"]` löst dann einen TypeError aus. Auch damit ist die Mutation entdeckt.

Wiederherstellung mit `git checkout -- team/agent.py`. Der sha256 danach ist identisch (9864393e…fd00), und `git diff --exit-code team/agent.py` ist leer.

## Eigene Testergebnisse (nach Wiederherstellung)
- `python3 -m unittest tests.test_tasks_f1_review -v`: 6 Tests OK, 0 Skips
- `python3 -m unittest discover -s tests`: 222 Tests OK
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0
- `git status` nach dem Commit: sauber
