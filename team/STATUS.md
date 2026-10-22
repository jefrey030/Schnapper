# SCHNAPPER-KI-Team – Status

**Team-Status:** NICHT EINSATZBEREIT (Stand 21.10.2026, vor dem ersten echten Lauf)

| Bereich | Zustand | Beleg |
| --- | --- | --- |
| Vier Agenten LEAD/BRAIN/CHECK/COMMAND | Code fertig, je eigener Prozess + eigener KI-Aufruf | `team/agent.py`, Tests in `tests/test_agenten.py` |
| Echte KI-Laufzeit | GitHub Models (kostenlos) vorgesehen, **noch nie erfolgreich aufgerufen** | kein Actions-Lauf möglich |
| Stundenautomatik | Workflow vorhanden, **GitHub startet die Jobs nicht** | Annotation: „job was not started because recent account payments have failed or your spending limit needs to be increased“ |
| Kostenpflichtige APIs | entfernt, per Test ausgeschlossen | `test_kein_bezahlter_anbieter_im_code` |
| Externe Schnäppchen-Daten | nicht verbunden | – |

Dieser Status wird nach jedem tatsächlich gelaufenen Stundenlauf automatisch überschrieben.

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 10:30 UTC)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| S-000 bis S-003 | **review** (warten auf Freigabe durch Jefrey) | `team/konzept/`, Tests `tests/test_konzept_s000.py`, `test_bestandsaufnahme_s001.py`, `test_plan_s002.py`, `test_agenten.py` |
| S-004 Quellen-Register | **proposed** – T1/T2 auf main bereits erfüllt, Vorschlag: auf `done` setzen | `tests/test_abgleich_s004_s005.py` |
| S-005 Adapter | **proposed** – T4/T5 erfüllt; T3 (Mock-Adapter) in #13, Zeitfehler dort in #15 (2bba103) behoben | `team/tasks.json` |
| S-006 PR-Ordnung | **proposed** – offen: #2, #6, #7, #8, #12, #13, #14, #15, #16; #16 ist Geschwister von #15 (9 eigene Commits, 14 fehlende); 6 Branches ohne PR vollständig in main → Löschkandidaten (nur Jefrey) | `team/tasks.json`, `tests/test_branches_s006.py` |
| Sammel-PRs #15/#16 | **rot**: je 2 Fehlschläge im alten S-006-Test; Korrektur liegt in #6 (0b758dd) | Bericht `team/runs/20261022-1030-master.md` |
| Tests (Arbeitsbranch) | 92/92 bestanden | `python3 -m unittest discover -s tests` |
| Blocker | Actions starten nicht (Billing); 9 offene, sich überschneidende PRs; eBay-Produktivfreigabe fehlt | – |
| Nächster Schritt | Jefrey: #16 auf #15 aufsetzen und 0b758dd übernehmen | – |
