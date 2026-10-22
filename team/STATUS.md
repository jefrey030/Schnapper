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

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 07:28 UTC)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| S-000 bis S-003 | **review** (warten auf Freigabe durch Jefrey) | `team/konzept/`, Tests `tests/test_konzept_s000.py`, `test_bestandsaufnahme_s001.py`, `test_plan_s002.py`, `test_agenten.py` |
| App-Kern + Quellen/Web | **auf main** (5343009, 7a0b83e aus PR #5/#10) | `app/schnapper/` |
| S-004 Quellen-Register | **proposed** – T1/T2 auf main bereits erfüllt, Vorschlag: auf `done` setzen | `tests/test_abgleich_s004_s005.py` |
| S-005 Adapter | **proposed** – T4/T5 erfüllt, **offen nur T3** (Mock-Adapter mit TEST-Daten) | `tests/test_abgleich_s004_s005.py` |
| S-006 PR-Ordnung | **proposed** – offen: #2, #6, #7, #8, #9; zusätzlich 4 Branches ohne PR vollständig in main → Löschkandidaten (nur Jefrey) | `team/tasks.json`, `tests/test_branches_s006.py` |
| Tests | 82/82 bestanden | `python3 -m unittest discover -s tests` |
| Blocker | Actions starten nicht (Billing) → kein echter Stundenlauf belegbar; 5 offene überlappende Draft-PRs; eBay-Produktivfreigabe fehlt; Kleinanzeigen ausgeschlossen | Bericht `team/runs/20261022-0728-master.md` |
| Nächster Schritt | Jefrey setzt S-005 auf `open` (nur T3 umsetzen) bzw. S-004 auf `done` | – |

## Nachtrag 22.10.2026 – Stand nach PR #15 (kein Stundenlauf)
- GitHub-Branch `integration/schnapper-gesamtstand-20261022` bündelt die Vorschläge.
- Preisadapter und lokale Barcode-Websuche erweitert. Tests im Branch angelegt,
  **nach den neuen Änderungen noch nicht ausgeführt**.
- **Nicht** verwechseln: Die PR-/Cloudflare-Simulationsläufe sind keine laufenden Agenten.
- Stundenautomatik: **weiterhin nicht einsatzbereit**, es liegen keine bestätigten
  echten Stundenberichte von LEAD/BRAIN/CHECK/COMMAND vor.
- Der PR darf bis zur Sichtung nicht gemergt werden. Kein Kostenrisiko eingehen.

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 16:29 UTC)
| Punkt | Zustand |
| --- | --- |
| main | a8898af, Tests **173/173 bestanden** |
| Offene Aufgaben | keine (`open` fehlt) |
| S-004, S-005 | auf main **vollständig erfüllt** (S-005/T3 via `tests/test_mock_adapter.py`) – Vorschlag: `done` |
| S-006 | überholt (PRs #2, #6–#9 geschlossen) |
| Neu vorgeschlagen | S-007 Entscheidungsvorlage PR #19/#20, S-008 Löschkandidaten-Liste (14 Branches vollständig in main) |
| Blocker | Actions starten nicht (Billing); eBay-Zugang fehlt; Freigabe einer Aufgabe durch Jefrey nötig |
| Bericht | `team/runs/20261022-1629-master.md` |
