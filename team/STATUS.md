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

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 09:30 UTC)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| S-000 bis S-003 | **review** (warten auf Freigabe durch Jefrey) | `team/konzept/`, Tests `tests/test_konzept_s000.py`, `test_bestandsaufnahme_s001.py`, `test_plan_s002.py`, `test_agenten.py` |
| Arbeitsbranch | main 4bc37e7 (PR #9) übernommen, Konflikt in `team/agent.py` aufgelöst (beide Seiten erhalten) | Commit 0a953c6 |
| S-004 Quellen-Register | **proposed** – T1/T2 auf main bereits erfüllt, Vorschlag: auf `done` setzen | `tests/test_abgleich_s004_s005.py` |
| S-005 Adapter | **proposed** – T4/T5 erfüllt; T3 (Mock-Adapter) in Draft-PR #13 vorbereitet, **nicht verifiziert**: dort 2/58 Tests vor 09:05 UTC rot (fester Testzeitpunkt 09:00 UTC vs. echte Uhrzeit in `angebot.py`) | `team/tasks.json` |
| S-006 PR-Ordnung | **proposed** – offen: #2, #6, #7, #8, #12, #13, #14, #15; #15 enthält #6 vollständig, #12 ebenso; 6 Branches ohne PR vollständig in main → Löschkandidaten (nur Jefrey) | `team/tasks.json`, `tests/test_branches_s006.py` |
| Tests | 91/91 bestanden | `python3 -m unittest discover -s tests` |
| Blocker | Actions starten nicht (Billing) → kein echter Stundenlauf belegbar; 8 offene, sich überschneidende PRs; eBay-Produktivfreigabe fehlt; Kleinanzeigen ausgeschlossen | Bericht `team/runs/20261022-0930-master.md` |
| Nächster Schritt | Jefrey entscheidet über Sammel-PR #15 (macht #6/#12 überflüssig) | – |
