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

## SCHNAPPER MASTER – letzter Lauf (21.10.2026, 21:31 UTC)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| S-000 MVP-Konzept | **review** (wartet auf Freigabe durch Jefrey) | `team/konzept/S-000-mvp-konzept.md`, `tests/test_konzept_s000.py` |
| S-001 Bestandsaufnahme | **review** | `team/konzept/S-001-bestandsaufnahme.md`, `tests/test_bestandsaufnahme_s001.py` |
| Tests | 28/28 bestanden | `python3 -m unittest discover -s tests` |
| Blocker | Actions starten nicht (Billing), Marktplatz-Nutzungsrechte offen | Bericht `team/runs/20261021-2131-master.md` |
| Nächster Schritt | M1 Inserat-Datenmodell als Python-Modul mit Tests | – |
