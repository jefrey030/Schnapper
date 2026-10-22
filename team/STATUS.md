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

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 01:28 UTC)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| S-000 MVP-Konzept | **review** (wartet auf Freigabe durch Jefrey) | `team/konzept/S-000-mvp-konzept.md`, `tests/test_konzept_s000.py` |
| S-001 Bestandsaufnahme | **review** | `team/konzept/S-001-bestandsaufnahme.md`, `tests/test_bestandsaufnahme_s001.py` |
| S-002 Datenquellen-Plan | **review** | `team/konzept/S-002-datenquellen-plan.md`, `tests/test_plan_s002.py` |
| S-003 Stundenlauf validieren | **review** – Bericht nennt fehlende KI-Anbindung jetzt als Blocker (Commit 0888b9a) | `team/agent.py` `blocker_ermitteln`, `tests/test_agenten.py` `test_s003_…` |
| App-Kern | in **PR #5** (nicht gemergt) | `app/schnapper` auf `feature/schnapper-angebotskern-20261021` |
| Vorschläge S-004–S-006 | **proposed** – warten auf Freigabe durch Jefrey (Quellen-Register, Adapter-Schnittstelle, PR-Entscheidungsvorlage; S-006 jetzt inkl. neuer Draft-PRs #8, #9) | `team/tasks.json`, `tests/test_vorschlaege.py` |
| Tests | 39/39 bestanden | `python3 -m unittest discover -s tests` |
| Blocker | Actions starten nicht (Billing) → kein echter Stundenlauf belegbar; S-004/S-005 brauchen Merge von PR #5; 6 offene überlappende PRs; eBay-Produktivfreigabe fehlt; Kleinanzeigen ausgeschlossen | Bericht `team/runs/20261022-0128-master.md` |
| Nächster Schritt | Jefrey gibt S-004–S-006 frei (`proposed` → `open`) bzw. prüft S-000–S-003 und PR #5 | – |
