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

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 20:29 UTC)
| Punkt | Zustand |
| --- | --- |
| main | e134cd0, Tests **190/190 bestanden**, Cloudflare **10/10** |
| Aufgabe | F1 Aufräumen (freigegeben von Jefrey) |
| Ergebnis | **Draft-PR #36** in Prüfung: https://github.com/jefrey030/Schnapper/pull/36 (Branch `agent/master/20261022-20` @ 4d48068) |
| S-004, S-005, S-006 | im PR auf **done** gesetzt (S-006 überholt) – wirksam erst nach Merge durch Jefrey |
| S-009 bis S-013 | im PR als **open** angelegt (F2 Angebot erfassen, F3 JSON-Sicherung, F4 Barcode-Kamera, F5 Termux-Start, F6 eBay vorbereiten) |
| S-007, S-008 | nicht übernommen (ID-Kollision mit offenem PR #33); möglicher Textkonflikt am Ende von `team/tasks.json` mit #33 |
| Masterplan | Abschnitt B jetzt PR-Tabelle mit echtem GitHub-Stand (34 PRs), D.3 angepasst |
| Blocker | Actions starten nicht (Billing, laut früheren Berichten); eBay-Zugangsdaten fehlen; Merge-Entscheidung über PR #36 bei Jefrey |
| Nächster Schritt | S-009 (F2) im nächsten Lauf, sofern PR #36 bestehen bleibt |
| Bericht | `team/runs/20261022-2029-master.md` |

Hinweis: `team/tasks.json` wurde nicht separat geändert; die tasks.json-Änderung ist ausschließlich in PR #36 enthalten.

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 21:28 UTC, Lauf 20261022-2128)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F1 Aufräumen (tasks.json, Masterplan B) | **Draft-PR #36** (Branch `agent/master/20261022-20` @ 4d48068), wartet auf Jefrey | `team/runs/20261022-2029-master.md` |
| F2 = S-009 Angebot direkt in der App erfassen | **Draft-PR #39** (Branch `agent/master/20261022-21` @ 6dbeb82), CHECK bestanden, wartet auf Jefrey | https://github.com/jefrey030/Schnapper/pull/39, `tests/test_app_erfassen_s009.py` |
| tasks.json | auf main unverändert. S-009 bis S-013 existieren nur in #36, deshalb wurde der Status von S-009 bewusst nicht in #39 gepflegt (sonst Konflikt) | – |
| Tests (Branch F2) | 202/202 OK (davon 12 neu, inkl. Playwright-Browsertest), Cloudflare 10/10 | `team/runs/20261022-2128-master.md` |
| Blocker | Actions starten nicht (Billing). Merge von #36/#39 liegt bei Jefrey. Mögliche Konflikte mit fremden PRs #19/#37 (`app/schnapper/web*`). eBay ohne Zugangsdaten | – |
| Nächster Schritt | F3 = S-010 Merkliste/Preisalarme sichern & wiederherstellen | – |

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 22:28 UTC, Lauf 20261022-2228)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F1 Aufräumen (tasks.json, Masterplan B) | **Draft-PR #36** (Branch `agent/master/20261022-20` @ 4d48068), wartet auf Jefrey | `team/runs/20261022-2029-master.md` |
| F2 = S-009 Angebot direkt in der App erfassen | **Draft-PR #39** (Branch `agent/master/20261022-21` @ 6dbeb82), wartet auf Jefrey | `team/runs/20261022-2128-master.md` |
| F3 = S-010 Merkliste und Preisalarme sichern und wiederherstellen | **Draft-PR #40** (Branch `agent/master/20261022-22` @ 3ab36fa), CHECK bestanden (AK 1–10 erfüllt), wartet auf Jefrey | https://github.com/jefrey030/Schnapper/pull/40, `tests/test_app_sicherung_s010.py` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch ist S-010 als **review** mit Hinweis auf PR #40 eingetragen; der Eintrag stammt aus #36. Im Feature-Branch wurde tasks.json nicht geändert, damit kein Konflikt mit #36 entsteht | – |
| Tests (Branch F3) | 196/196 OK (davon 6 neu, darunter 3 Playwright-Browsertests mit 390x844), Cloudflare 10/10 | `team/runs/20261022-2228-master.md` |
| Blocker | Actions starten nicht (Billing). Die Merge-Entscheidung über #36, #39 und #40 liegt bei Jefrey. Mögliche Konflikte mit den fremden PRs #28, #29 und #30 (Preisalarm). Der `gh`-Token ist ungültig, deshalb wurde der PR über das GitHub-MCP angelegt. eBay hat keine Zugangsdaten | – |
| Nächster Schritt | F4 = S-011 Barcode per Kamera | – |
