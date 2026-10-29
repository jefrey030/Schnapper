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

## SCHNAPPER MASTER – letzter Lauf (22.10.2026, 22:38 UTC, Lauf 20261022-2238)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F1 Aufräumen (tasks.json, Masterplan B) | **Draft-PR #36** (Branch `agent/master/20261022-20` @ 4d48068), wartet auf Jefrey | `team/runs/20261022-2029-master.md` |
| F2 = S-009 Angebot direkt in der App erfassen | **Draft-PR #39** (Branch `agent/master/20261022-21` @ 6dbeb82), wartet auf Jefrey | `team/runs/20261022-2128-master.md` |
| F3 = S-010 Merkliste und Preisalarme sichern und wiederherstellen | **Draft-PR #40** (Branch `agent/master/20261022-22` @ 3ab36fa), wartet auf Jefrey | `team/runs/20261022-2228-master.md` |
| F4 = S-011 Barcode per Kamera scannen (BarcodeDetector) | **Draft-PR #41** (Branch `agent/master/20261022-2238` @ 38a469e), CHECK bestanden (AK 1–12 erfüllt), wartet auf Jefrey. Auf echtem Gerät ungetestet; Kamera nur im Secure Context (https/localhost) | https://github.com/jefrey030/Schnapper/pull/41, `tests/test_app_kamera_s011.py` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch ist S-011 als **review** mit Hinweis auf PR #41 eingetragen; der Eintrag stammt aus #36. Im Feature-Branch wurde tasks.json nicht geändert | – |
| Tests (Branch F4) | 200/200 OK (davon 10 neu, darunter 7 Playwright-Browsertests mit 390x844), Cloudflare 10/10. CSP unverändert | `team/runs/20261022-2238-master.md` |
| Blocker | PR-Check python-tests lief auf #40 grün (Actions-Billing-Blocker für PR-Checks überholt; Stundenlauf ungeprüft). Die Merge-Entscheidung über #36, #39, #40 und #41 liegt bei Jefrey. Mögliche Konflikte mit #28/#29/#30 sowie #36/#39/#40 (`app/schnapper/web*`). Der `gh`-Token ist ungültig, PR über GitHub-MCP angelegt. eBay-Sandbox-Schlüssel für F6 fehlt | – |
| Nächster Schritt | F5 = S-012 Ein-Befehl-Start unter Termux | – |

## SCHNAPPER MASTER – letzter Lauf (23.10.2026, 01:28 UTC, Lauf 20261023-0128)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F1 bis F4 | **Draft-PRs #36, #39, #40, #41**, warten auf Jefrey | frühere Laufberichte |
| F5 = S-012 Ein-Befehl-Start Termux | **Draft-PR #44** (Branch `agent/master/20261022-23` @ a584774), CHECK bestanden, auf echtem Gerät ungetestet. Wird hier nachgetragen, weil STATUS im Lauf 20261022-2328 nur im Übergabeordner lag | `team/runs/20261022-2328-master.md` |
| F6 = S-013 eBay vorbereiten (Browse-API-Adapter, Sandbox als Standard, gesperrt ohne Schalter und Schlüssel) | **Draft-PR #45** (Branch `agent/master/20261023-01` @ ecad218), CHECK bestanden (AK 1–23 erfüllt), wartet auf Jefrey. **Mit echten eBay-Sandbox-Schlüsseln ungetestet** | https://github.com/jefrey030/Schnapper/pull/45, `app/schnapper/ebay.py`, `tests/test_ebay.py`, `docs/EBAY.md` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch sind S-012 (PR #44) und S-013 (PR #45) als **review** eingetragen; die Einträge stammen aus #36. Im Feature-Branch wurde tasks.json nicht geändert | – |
| Tests (Branch F6) | 250/250 OK (216 main + 34 neu, 0 skipped), Cloudflare 10/10 | `team/runs/20261023-0128-master.md` |
| Blocker | Die Merge-Entscheidung über #36, #39, #40, #41, #44 und #45 liegt bei Jefrey. Es fehlen eBay-Sandbox-Client-ID und -Secret; Jefrey legt sie gemäß `docs/EBAY.md` als Umgebungsvariablen an, nie im Repo. Für die Produktivnutzung braucht es eine Genehmigung von eBay (Entscheidung Jefrey) | – |
| Nächster Schritt | Jefrey sichtet und mergt #36 (macht tasks.json auf main aktuell). Danach den Platzhalter `adapter.EbayAdapter` auf `ebay.EbayAdapter` umleiten (Folgepunkt aus #45) | – |

## SCHNAPPER MASTER – letzter Lauf (23.10.2026, 02:29 UTC, Lauf 20261023-0229)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F2 = S-009 auf main-Stand bringen | **Draft-PR #39** (Branch `agent/master/20261022-21` @ 1833417) per Merge von main @ 6dbe114 aktualisiert (Merge-Commit 2a3ae8e, kein Rebase/Force-Push). `Zustand.hinzufuegen` atomar unter `_import_lock` mit Verlauf-Rollback (OSError → 500 „Angebot nicht übernommen …“), 3 neue Tests. CHECK bestanden (AK 1–13), wartet auf Jefrey | https://github.com/jefrey030/Schnapper/pull/39, `team/runs/20261023-0229-master.md` |
| F1, F3–F6 | **Draft-PRs #36, #40, #41, #44, #45** unverändert, warten auf Jefrey. #36/#40/#41 liegen 4 Commits hinter main (konfliktfrei laut merge-tree) | `team/runs/20261023-0229-master.md` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch fehlte S-009 bisher; jetzt aus #36 übernommen und als **review** mit Hinweis auf PR #39 eingetragen | – |
| Tests (Branch F2) | 231/231 OK (216 main + 15 S-009, Browsertest ausgeführt), Cloudflare 10/10 | `team/runs/20261023-0229-master.md` |
| Blocker | Merge-Entscheidung über #36, #39, #40, #41, #44, #45 liegt bei Jefrey. #40/#41 ändern dieselben Stellen in `app.js`/`index.html` wie #39 (Folgekonflikte erwartet). eBay-Sandbox-Client-ID/-Secret fehlen | – |
| Nächster Schritt | #40 (F3) per Merge von main aktualisieren, danach #41 | – |

## SCHNAPPER MASTER – letzter Lauf (23.10.2026, 03:29 UTC, Lauf 20261023-0329)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F3 = S-010 auf main-Stand bringen | **Draft-PR #40** (Branch `agent/master/20261022-22` @ 1adad0c) per Merge von main @ 6dbe114 aktualisiert (Merge-Commit 2697c30, kein Rebase/Force-Push). Alarm-Prüfung in `sicherungPruefen` an die Server-Regeln angeglichen (`max_preis` > 0 und höchstens 2 Nachkommastellen, `min_rabatt` 0–100), 2 neue Tests. CHECK bestanden (AK 1–12), PR-Check python-tests grün, mergeable clean, wartet auf Jefrey | https://github.com/jefrey030/Schnapper/pull/40, `team/runs/20261023-0329-master.md` |
| F1, F2, F4–F6 | **Draft-PRs #36, #39, #41, #44, #45** unverändert, warten auf Jefrey. #36/#41 liegen 4 Commits hinter main (konfliktfrei laut merge-tree) | `team/runs/20261023-0329-master.md` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch bleibt S-010 **review**, Hinweis „PR #40 auf main 6dbe114 gebracht, Lauf 20261023-0329“ ergänzt | – |
| Tests (Branch F3) | 224/224 OK (216 main + 8 S-010, Browsertests ausgeführt), Cloudflare 10/10 | `team/runs/20261023-0329-master.md` |
| Blocker | Merge-Entscheidung über #36, #39, #40, #41, #44, #45 liegt bei Jefrey. #39/#40/#41 ändern dieselben Stellen in `app.js`/`index.html` (Folgekonflikte erwartet). Testdateien verweisen auf `chromium-1194` (installiert: 1243), Browsertests laufen nur mit `PLAYWRIGHT_BROWSERS_PATH`. eBay-Sandbox-Client-ID/-Secret fehlen | – |
| Nächster Schritt | #41 (F4) per Merge von main aktualisieren; danach Chromium-Pfad in den Testdateien robust machen | – |

## SCHNAPPER MASTER – letzter Lauf (23.10.2026, 04:29 UTC, Lauf 20261023-0429)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F4 = S-011 auf main-Stand bringen | **Draft-PR #41** (Branch `agent/master/20261022-2238` @ a3fcfab) per Merge von main @ 6dbe114 aktualisiert (Merge-Commit 9d3982e, kein Rebase/Force-Push). `tests/test_app_kamera_s011.py` findet das installierte Chromium jetzt automatisch (`_finde_chromium()`, statt fest `chromium-1194`), 1 neuer statischer Test. CHECK bestanden (AK 1–13), PR-Check python-tests grün, wartet auf Jefrey | https://github.com/jefrey030/Schnapper/pull/41, `team/runs/20261023-0429-master.md` |
| F1–F3, F5, F6 | **Draft-PRs #36, #39, #40, #44, #45** unverändert, warten auf Jefrey. #36 liegt 4 Commits hinter main (konfliktfrei laut merge-tree) | `team/runs/20261023-0429-master.md` |
| tasks.json | Auf main unverändert. Auf dem Report-Branch bleibt S-011 **review**, Hinweis „PR #41 auf main 6dbe114 gebracht, Lauf 20261023-0429“ ergänzt | – |
| Tests (Branch F4) | 227/227 OK (216 main + 11 S-011, 0 skipped; Browsertests mit und ohne `PLAYWRIGHT_BROWSERS_PATH` ausgeführt), Cloudflare 10/10 | `team/runs/20261023-0429-master.md` |
| Blocker | Merge-Entscheidung über #36, #39, #40, #41, #44, #45 liegt bei Jefrey. #39/#40/#41 ändern dieselben Stellen in `app.js`/`index.html` (Folgekonflikte erwartet). `tests/test_app_sicherung_s010.py` (#40) verweist weiter auf `chromium-1194`. eBay-Sandbox-Client-ID/-Secret fehlen | – |
| Nächster Schritt | Dieselbe Chromium-Suche in `tests/test_app_sicherung_s010.py` auf PR #40 übernehmen | – |

## SCHNAPPER MASTER – letzter Lauf (23.10.2026, 05:29 UTC, Lauf 20261023-0529)
| Aufgabe | Zustand | Beleg |
| --- | --- | --- |
| F1 auf main-Stand bringen und aktualisieren | **Draft-PR #36** (Branch `agent/master/20261022-20` @ 8d4e90b) per Merge von main @ 6dbe114 aktualisiert (Merge-Commit 2a43d86, kein Rebase/Force-Push; Push Fast-Forward 4d48068..8d4e90b). Abschnitt B im Masterplan auf Live-Stand 23.10. 05:30 UTC (Offen 15, Gemergt 19, Geschlossen 9; #4/#38 Issues). S-009–S-013 in `team/tasks.json` auf **review** statt open (offen benannte Abweichung von der Arbeitsliste: offene Draft-PRs existieren, verhindert Doppelvergabe durch `team/agent.py`). CHECK bestanden (AK 1–12; AK 13 durch COMMAND belegt: head.sha 8d4e90b, draft true), wartet auf Jefrey | https://github.com/jefrey030/schnapper/pull/36, `team/runs/20261023-0529-master.md` |
| F2–F6 | **Draft-PRs #39, #40, #41, #44, #45** unverändert, alle enthalten main 6dbe114, warten auf Jefrey | `team/runs/20261023-0529-master.md` |
| tasks.json | Auf main unverändert (S-009–S-013 existieren dort erst nach Merge von #36). In #36 jetzt S-009–S-013 **review** mit Hinweis auf PR #39/#40/#41/#44/#45 – deckungsgleich mit dem Report-Branch | – |
| Tests (Branch F1) | 216/216 OK, Cloudflare 10/10, JSON gültig, Secret-Scan ohne Treffer | `team/runs/20261023-0529-master.md` |
| Blocker | Merge-Entscheidung über #36, #39, #40, #41, #44, #45 liegt bei Jefrey. #39/#40/#41 ändern dieselben Stellen in `app.js`/`index.html` (Folgekonflikte erwartet). Titel von #36 nennt noch „S-009–S-013 open“ (bewusst nicht geändert). `tests/test_app_sicherung_s010.py` (#40) verweist weiter auf `chromium-1194`. eBay-Sandbox-Client-ID/-Secret fehlen | – |
| Nächster Schritt | Dieselbe Chromium-Suche (`_finde_chromium()`) in `tests/test_app_sicherung_s010.py` auf PR #40 übernehmen | – |

## Lauf 20261023-0629 (Bericht `team/runs/20261023-0629-master.md`)
- F3 / PR #40: Browsertest findet Chromium automatisch statt fest `chromium-1194` (Commit f0cc84c, Fast-Forward-Push, kein Force). Tests 226 OK, Modul 10/10 ohne Skip, Cloudflare 10/10. CHECK bestanden. #40 bleibt Draft, Kopf f0cc84c. `team/tasks.json` ist unverändert (S-010 bleibt `review`). Merge-Entscheidung bei Jefrey, eBay-Sandbox-Schlüssel fehlen weiter.

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 08:28 UTC)

- Lauf 20261028-0828: In PR #45 (F6 / S-013, eBay, Branch `agent/master/20261023-01`) Commit 31677d0 gepusht, als Fast-Forward ohne Force. `_anfrage()` meldet zu tief verschachteltes JSON und Zahlen mit mehr als 4300 Ziffern jetzt als `EbayFehler` statt als rohe Ausnahme.
- Tests: `tests.test_ebay` 35/35 OK, discover 251 OK, Cloudflare 10/10 pass, CI `python-tests` success.
- PR #45: Draft, Kopf 31677d0, mergeable_state clean. Die Merge-Entscheidung trifft Jefrey, ebenso für #36, #39, #40, #41 und #44.
- `team/tasks.json` ist unverändert, S-013 steht in #36 bereits auf `review`.
- Offen: Für #45 fehlen eBay-Sandbox-Schlüssel (Umgebungsvariablen laut `docs/EBAY.md`). Zu 2666d8b (#39) fehlt ein Bericht. #50 ist ausgeklammert.
- Bericht: `team/runs/20261028-0828-master.md` (auf `agent/master/reports`)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 14:33 UTC, Lauf 20261028-1433)

- F3 / S-010 / PR #40 (Branch `agent/master/20261022-22`): Ein Merkschlüssel `"__proto__"` wird beim Wiederherstellen jetzt als ungültig gemeldet (`Merkliste: Eintrag „__proto__“ ungültig (Schlüssel)`) statt still verworfen. Das Ergebnisobjekt in `sicherungPruefen` ist prototypfrei (`Object.create(null)`). Neuer Browsertest `test_proto_schluessel_wird_gemeldet`. Gegenprobe mit app.js aus f0cc84c: rot.
- Commit 4274324, Push f0cc84c..4274324 als Fast-Forward ohne Force.
- Tests: discover 227 OK, `tests.test_app_sicherung_s010` 11/11 OK (Browsertests ausgeführt), Cloudflare 10/10 pass, CI `python-tests` success. CHECK bestanden.
- PR #40: Draft, Kopf 4274324, Body um Nachtrag „Lauf 20261028-1433“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #41, #44, #45).
- `team/tasks.json`: S-010 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin. Hinweis: Im flachen Klon (depth 50) ist `tests/test_branches_s006.py` rot, nach `git fetch --unshallow` grün.
- Bericht: `team/runs/20261028-1433-master.md` (auf `agent/master/reports`)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 15:32 UTC, Lauf 20261028-1532)

- F5 / S-012 / PR #44 (Branch `agent/master/20261022-23`): `sh start-schnapper.sh` (sh → dash) bricht jetzt verständlich mit „Bitte mit bash starten: bash start-schnapper.sh“ und Exit 2 ab statt mit „Bad substitution“. POSIX-Wächter vor `set -eu`, Hinweis in `docs/HANDY-START.md` Schritt 4, neuer Test `test_start_mit_sh_meldet_bash`. Gegenprobe mit dem Skript aus a584774: rot.
- Commit 779e8b7, Push a584774..779e8b7 als Fast-Forward ohne Force. Ein Merge von main war nicht nötig, main 6dbe114 steckt schon im Branch (INDEX-Vermerk überholt).
- Tests: discover 233 OK (vorher 232), `tests.test_start_skript_s012` 17/17 OK, 0 skipped, Cloudflare 10/10 pass, CI `python-tests` success. CHECK bestanden (AK 1–12).
- PR #44: Draft, Kopf 779e8b7, Body um Nachtrag „Update Lauf 20261028-1532“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #41, #45). Auf echtem Gerät (Termux) weiterhin ungetestet.
- `team/tasks.json`: S-012 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin. Nächster kleiner Schritt in #44: `SCHNAPPER_PYTHON=echo` besteht die Versionsprüfung im Startskript (nur Exit-Code geprüft).
- Bericht: `team/runs/20261028-1532-master.md` (auf `agent/master/reports`)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 16:29 UTC, Lauf 20261028-1629)

- F5 / S-012 / PR #44 (Branch `agent/master/20261022-23`): Die Python-Versionsprüfung im Startskript verlangt jetzt die exakte Ausgabe `py-ok:42` (berechnet als `6 * 7`, nicht wörtlich im `-c`-Code) statt nur den Exit-Code. `SCHNAPPER_PYTHON=echo`, `/bin/echo` und `true` enden mit Exit 2 und der Meldung „Python ist zu alt oder kein Python (…)“, ohne Server. Neuer Test `test_falscher_interpreter_wird_abgelehnt`. Gegenprobe mit dem Skript aus 779e8b7: rot (failures=3).
- Commit 41e801c, Push 779e8b7..41e801c als Fast-Forward ohne Force.
- Tests: discover 234 OK (vorher 233), `tests.test_start_skript_s012` 18/18 OK, Cloudflare 10/10 pass, CI `python-tests` success. CHECK bestanden (AK 1–12).
- PR #44: Draft, Kopf 41e801c, Body um Nachtrag „Update Lauf 20261028-1629“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #41, #45). Auf echtem Gerät (Termux) weiterhin ungetestet.
- `team/tasks.json`: S-012 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261028-1629-master.md` (auf `agent/master/reports`)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 17:29 UTC, Lauf 20261028-1729)

- F1 / PR #36 (Branch `agent/master/20261022-20`): Abschnitt B in `docs/SCHNAPPER-MASTERPLAN.md` auf den Live-Stand vom 28.10.2026 ca. 17:30 UTC gebracht (Basis `main` @ 6dbe114, per GitHub-REST). `### Offen (15)` → `### Offen (56)` mit allen 56 offenen PRs, `### Gemergt (19)` unverändert. Hinweis nennt die Team-PRs #36, #39, #40, #41, #44, #45 und #50 (S-014). Nur diese Datei, nur Abschnitt B (44+/3−).
- Commit c4ac5c5, Push 8d4e90b..c4ac5c5 als Fast-Forward ohne Force.
- Tests: discover 216 OK, Cloudflare 10/10 pass, Prüfskript Tabelle gegen REST OK 56, CI `python-tests` success. CHECK bestanden (AK 1–12; AK 13 durch COMMAND).
- PR #36: Draft, Kopf c4ac5c5, Body um Nachtrag „Update Lauf 20261028-1729“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #39, #40, #41, #44, #45). Alle Team-PRs laut LEAD `mergeable_state` clean.
- `team/tasks.json`: S-004–S-006 bleiben `proposed` (in #36 `done`, wirksam erst nach Merge), Laufvermerk bei S-006 ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin; Produktion braucht eBay-Genehmigung.
- Bericht: `team/runs/20261028-1729-master.md` (im Hauptbaum, nicht committet)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 18:29 UTC, Lauf 20261028-1829)

- F2 / S-009 / PR #39 (Branch `agent/master/20261022-21`): `POST /api/angebot` prüft Typen und Längen jetzt serverseitig in `typfehler()` in `app/schnapper/web.py`, vor `Angebot.aus_dict`.
  - Textfelder `titel`, `zustand`, `url` und `kategorie` müssen `str` sein.
  - Geldfelder `preis`, `versand` und `referenzpreis` müssen `str`, `int` oder `float` sein, `bool` ist ausgeschlossen.
  - `kategorie` darf höchstens 100 Zeichen haben (`MAX_KATEGORIE` = `maxlength` im Formular).
  - Sonst gibt es 422 mit dem Feldnamen, Liste und Verlauf bleiben unverändert. `null` gilt bei optionalen Feldern als leer.
  - Bisher wurden z. B. `{"titel": {"a":1}}` und eine Kategorie mit 3000 Zeichen mit 201 übernommen. `angebot.py` und `einlesen.py` sind unverändert.
  - Neue Testklasse `ErfassenTypen` (4 Tests mit subTests). Gegenprobe gegen 2666d8b: rot (17 failures, 1 error).
- Commit fd16763, Push 2666d8b..fd16763 als Fast-Forward ohne Force.
- Tests: discover 237 OK (vorher 233), `tests.test_app_erfassen_s009` 21/21 OK (Browsertest ausgeführt), Cloudflare 10/10 pass, CI `python-tests` success. CHECK bestanden (AK 1–12).
- PR #39: Draft, Kopf fd16763, Body um Nachtrag „Update Lauf 20261028-1829“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #40, #41, #44, #45).
- `team/tasks.json`: S-009 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: CSV-Formel-Injection in #39 (CHECK-Hinweis 1) bewusst zurückgestellt. eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261028-1829-master.md` (auf `agent/master/reports`)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 19:29 UTC, Lauf 20261028-1929)

- F6 / S-013 / PR #45 (Branch `agent/master/20261023-01`): Neue Kommandozeilen-Option `python -m schnapper --ebay SUCHBEGRIFF` für den Sandbox-Test (lazy Import, genau eine Quelle, Sperren/Fehler mit Exit 3 und `eBay: …` auf stderr, Sandbox standardmäßig mit Präfix `SANDBOX `). Neue Tests `tests/test_ebay_cli.py` (10, ohne Netz), Abschnitt „Sandbox-Test per Kommandozeile“ in `docs/EBAY.md`. Nachbesserung: `--openprices ""` wieder Exit 2 statt Traceback.
- Commits c09c9dc + d1a9eef, Push 31b52d4..d1a9eef als Fast-Forward ohne Force.
- Tests: discover 262 OK (vorher 252), ohne Netz 73 OK, Cloudflare 10/10 pass. CHECK Runde 1 nachbessern, Runde 2 bestanden.
- PR #45: Draft, Kopf d1a9eef, Body um Nachtrag „Lauf 20261028-1929“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #41, #44).
- `team/tasks.json`: S-013 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: echter Sandbox-Test braucht Jefreys eBay-Sandbox-Schlüssel (`PYTHONPATH=app python -m schnapper --ebay "fahrrad"`). Weboberfläche für eBay weiterhin Folgepunkt.
- Bericht: `team/runs/20261028-1929-master.md` (im Hauptbaum, nicht committet)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 20:28 UTC, Lauf 20261028-2028)

- F4 / S-011 / PR #41 (Branch `agent/master/20261022-2238`): `#kamera-abbrechen` liegt nicht mehr im verborgenen `#kamera-bereich` und ist ab Klick auf „Mit Kamera scannen“ sichtbar, also auch bei offenem Berechtigungsdialog (`getUserMedia`) und offener Formatabfrage. Ein echter Klick bricht ab, gibt den Kamera-Knopf frei, ein später Stream wird sofort gestoppt. Video erst nach erfolgreichem Start. 2 neue Browsertests, JS-Direktklick durch echten Klick ersetzt. Gegenprobe mit app.js/index.html aus 662cf81: rot (failures=4).
- Commit ca5420e, Push 662cf81..ca5420e als Fast-Forward ohne Force.
- Tests: discover 237 OK, `tests.test_app_kamera_s011` 21/21 OK (0 Skips, Chromium gefunden), Cloudflare 10/10 pass. CHECK bestanden (AK 1–11).
- PR #41: Draft, Kopf ca5420e, Body um Nachtrag „Lauf 20261028-2028“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #44, #45).
- `team/tasks.json`: S-011 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: Fokus-Management beim Kamerastart (nicht gefordert), `upc_e` fehlt in `KAMERA_FORMATE`, echtes Gerät ungetestet. eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261028-2028-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (28.10.2026, 23:28 UTC, Lauf 20261028-2328)

- F4 / S-011 / PR #41 (Branch `agent/master/20261022-2238`): Tastaturfokus beim Kamera-Scan. Beim Start erhält `#kamera-abbrechen` sofort den Fokus (vor `getUserMedia`, also auch bei offenem Berechtigungsdialog). Beim Stoppen geht der Fokus nur dann zurück auf „Mit Kamera scannen“, wenn er auf Abbrechen lag; sonst bleibt er, wo er ist (z. B. im Barcode-Feld). Gilt zentral für alle Stopp-Wege. 4 neue Browsertests (Start per Tastatur, kein Klick). Gegenprobe mit app.js aus ca5420e: rot (failures=3).
- Commit 6165af4, Push ca5420e..6165af4 als Fast-Forward ohne Force.
- Tests: discover 241 OK, `tests.test_app_kamera_s011` 25/25 OK (0 Skips, Chromium gefunden), Cloudflare 10/10 pass. CHECK bestanden (AK 1–11), Secret-Scan leer.
- PR #41: Draft, Kopf 6165af4, Body um Nachtrag „Lauf 20261028-2328“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #44, #45).
- `team/tasks.json`: S-011 bleibt `review` (in Arbeit in PR #41), Laufvermerk im Hinweis ergänzt.
- Offen: `upc_e` fehlt in `KAMERA_FORMATE` (braucht Normalisierung auf UPC-A/EAN-13), eigener Fokus-Test für Treffer-/Fehler-Pfad, echtes Gerät ungetestet. eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261028-2328-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 00:29 UTC, Lauf 20261029-0029)

- F3 / S-010 / PR #40 (Branch `agent/master/20261022-22`): Ein Preisalarm wird nur noch angelegt, wenn er die Prüfung beim Wiederherstellen bestehen würde. Gemeinsame Prüfregel `alarmFehler(w)` (Regex wortgleich) für `alarmAnlegen()` und `sicherungPruefen()`; Prüfung läuft vor `fetch`. Bisher wurden z. B. „Bis €“ 1.299,99 / 10€, Rabatt 12.345 oder Suchtext > 200 Zeichen angelegt und beim Wiederherstellen verworfen. 4 neue Tests (3 Browser, 1 statisch). Gegenprobe mit app.js aus 33a9487: rot (failures=5).
- Commit 87eebba, Push 33a9487..87eebba als Fast-Forward ohne Force.
- Tests: discover 234 OK, `tests.test_app_sicherung_s010` 18/18 OK (0 Skips, Chromium gefunden), Cloudflare 10/10 pass. CHECK bestanden (AK 1–10), Secret-Scan leer.
- PR #40: Draft, Kopf 87eebba, Body um Nachtrag „Lauf 20261029-0029“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #41, #44, #45, #50).
- `team/tasks.json`: S-010 bleibt `review` (in Arbeit in PR #40), Laufvermerk im Hinweis ergänzt.
- Offen: `maxlength` am Suchfeld (wegen Konflikten mit #39/#41 bewusst nicht umgesetzt). eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261029-0029-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 01:28 UTC, Lauf 20261029-0128)

- F5 / S-012 / PR #44 (Branch `agent/master/20261022-23`): Ein relativer `SCHNAPPER_PYTHON` (z. B. `bin/python`, `./bin/python`) oder ein relativer PATH-Eintrag wird jetzt vor der Versionsprüfung gegen den Aufrufort absolut gemacht (`case "$PY" in /*) ;; *) PY=$AUFRUF_DIR/$PY ;; esac`, nur Builtins). Bisher prüfte das Skript den Interpreter im Aufrufort, wechselte dann per `cd` in den Skriptordner und startete per `exec` einen anderen Pfad (Exit 127 nach der Startmeldung oder ungeprüfter Interpreter). Neuer Test `test_relativer_python_pfad_zum_aufrufort` (Subtests `bin/python`, `./bin/python`). Gegenprobe mit dem Skript aus 41e801c: rot (failures=2).
- Commit b03b986, Push 41e801c..b03b986 als Fast-Forward ohne Force.
- Tests: discover 235 OK (vorher 234), `tests.test_start_skript_s012` 19/19 OK, Cloudflare 10/10 pass, `bash -n` OK. CHECK bestanden (AK 1–10), Secret-Scan leer. Rückfrage zu `SCHNAPPER_PYTHON=python3`: keine Regression (alt und neu 200/rc 0).
- PR #44: Draft, Kopf b03b986, Body um Nachtrag „Lauf 20261029-0128“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #41, #45, #50). Auf echtem Gerät (Termux) weiterhin ungetestet.
- `team/tasks.json`: S-012 bleibt `review` (in Arbeit in PR #44), Laufvermerk im Hinweis ergänzt.
- Offen: kosmetische Fehlermeldung bei `SCHNAPPER_PYTHON=echo`/`true` (künstlicher Pfad im Text, Exit 2 bleibt richtig). eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261029-0128-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 02:29 UTC, Lauf 20261029-0229)

- F2 / S-009 / PR #39 (Branch `agent/master/20261022-21`): Der CSV-Export `/api/angebote.csv` ist gegen Formel-Injektion abgesichert (CWE-1236). Textzellen (id, titel, zustand, quelle, kategorie, url), die mit `=`, `+`, `-`, `@`, Tab oder CR beginnen, bekommen ein führendes `'`. Der CSV-Import (`_zeilen_csv`) entfernt dieses `'` nur vor genau diesen Zeichen (`'Normal` bleibt). Die Konstante `CSV_FORMEL_START` ist nur in `einlesen.py` definiert, der JSON-Import ist unverändert. Bisher wurde z. B. `=HYPERLINK(...)` ungeschützt exportiert. 6 neue Tests (`CsvFormelSchutz`, `CsvImportApostroph`). Gegenprobe mit dem App-Code aus fd16763: rot (failures=3).
- Commit a87a977, Push fd16763..a87a977 als Fast-Forward ohne Force.
- Tests: discover 243 OK (vorher 237), `tests.test_app_erfassen_s009` 27/27 OK (Browsertest ohne Skip), weitere Nutzer von `lies_text` 64 OK, Cloudflare 10/10 pass. CHECK bestanden (AK 1–7, AK 8 durch COMMAND), Secret-Scan leer.
- PR #39: Draft, Kopf a87a977, Body um Nachtrag „Lauf 20261029-0229“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #40, #41, #44, #45, #50).
- `team/tasks.json`: S-009 bleibt `review` (in Arbeit in PR #39), Laufvermerk im Hinweis ergänzt.
- Offen: Randfall `'=x` als Originalwert kommt als `=x` zurück (nicht blockierend; Lösung wäre symmetrisches Escaping). eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261029-0229-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 03:28 UTC, Lauf 20261029-0328)

- F1 / PR #36 (Branch `agent/master/20261022-20`): Neuer Test `tests/test_tasks_f1_review.py` (+70, offline). Er sichert ab, dass S-009–S-013 auf `review` bleiben (Hinweis nennt PR und Branch) und weder `choose_task` noch die LEAD-Liste aus `team/agent.py` sie doppelt vergibt. Dazu kommt eine Selbstprüfung auf einer `deepcopy`. Testname in `tests/test_branches_s006.py` auf `test_s006_erledigt_und_nennt_alle_kandidaten` korrigiert (1 −/1 +), damit ist K1 erledigt. `team/tasks.json` und der Masterplan sind im PR unverändert.
- Commit 397d0e2, Push c4ac5c5..397d0e2 als Fast-Forward ohne Force.
- Tests: discover 220 OK (vorher 216, +4), `tests.test_tasks_f1_review` 4/4 OK, Cloudflare 10/10 pass. Gegenproben rot (S-012 open → failures=15, ohne #44 → 1, S-009 open → 15). CHECK bestanden (AK 1–9), Secret-Scan leer.
- PR #36: Draft, Kopf 397d0e2, Body um Nachtrag „Update Lauf 20261029-0328“ ergänzt (K1 erledigt, Vermerk zu tests/ als reiner Testergänzung). Merge-Entscheidung bei Jefrey (ebenso #39, #40, #41, #44, #45, #50).
- `team/tasks.json`: S-004–S-006 bleiben `proposed` (in #36 `done`, wirksam erst nach Merge), Laufvermerk bei S-006 ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261029-0328-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 04:28 UTC, Lauf 20261029-0428)

- F6 / S-013 / PR #45 (Branch `agent/master/20261023-01`): Ein eBay-`access_token` mit Steuerzeichen konnte über einen rohen `ValueError` aus `http.client.putheader` samt Wert auf stderr landen (`--ebay`). Behoben: `_token()` nimmt nur noch druckbares ASCII ohne Leerzeichen an (`[\x21-\x7e]+`), sonst kommt „Token-Antwort unbrauchbar“ ohne Wert. `_anfrage()` meldet einen `ValueError` als `EbayFehler("Anfrage an eBay ungültig (Kopfzeile)")` ohne Ausnahmetext. Neue Tests A (5 subTests), A2, B (echter http.client, Socket gesperrt) und C (CLI). Gegenproben rot (failures=5 bzw. errors=1).
- Commit 9cde1ee, Push d1a9eef..9cde1ee als Fast-Forward ohne Force.
- Tests: discover 265 OK (vorher 262), `tests.test_ebay tests.test_ebay_cli` 49 OK, Cloudflare 10/10 pass. CHECK bestanden (AK 1–9), Secret-Scan leer.
- PR #45: Draft, Kopf 9cde1ee, Body um Nachtrag „Update Lauf 20261029-0428“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #41, #44, #50).
- `team/tasks.json`: S-013 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: eBay-Sandbox-Schlüssel für #45 fehlen weiterhin (nur Jefrey, nur als Umgebungsvariablen).
- Bericht: `team/runs/20261029-0428-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 05:28 UTC, Lauf 20261029-0528)

- F4 / S-011 / PR #41 (Branch `agent/master/20261022-2238`): Ein Kamera-Treffer während einer laufenden Handsuche löste per `requestSubmit()` trotz deaktiviertem `#barcode-knopf` eine zweite Barcode-Abfrage aus. Die zuletzt eintreffende Antwort gewann, sodass Preise und Lizenz von A unter dem Feld mit B stehen konnten, und der Knopf wurde zu früh freigegeben. Behoben mit dem Generationszähler `barcodeAbfrage` in `barcodeSuchen()`: Nur die zuletzt gestartete Abfrage schreibt Treffer, Lizenz und Status und gibt den Knopf frei. Veraltete Antworten (Erfolg, HTTP-Fehler, Netzfehler) werden verworfen. Neue Browsertests T1, T2 und T3. Gegenprobe rot (failures=4).
- Commit 175d7b7, Push 6165af4..175d7b7 als Fast-Forward ohne Force. CI `python-tests` success.
- Tests: discover 244 OK (0 Skips), S-011-Modul 28/28 OK (vorher 25), Cloudflare 10/10 pass. CHECK bestanden (AK 1–9, AK 10 Push durch COMMAND), Secret-Scan leer.
- PR #41: Draft, Kopf 175d7b7, Body um Abschnitt „Lauf 20261029-0528“ ergänzt. Merge-Entscheidung bei Jefrey (ebenso #36, #39, #40, #44, #45, #50).
- `team/tasks.json`: S-011 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: Test von #41 auf einem echten Gerät. eBay-Sandbox-Schlüssel für #45 (F6) fehlen weiterhin.
- Bericht: `team/runs/20261029-0528-master.md` (Übergabe an Orchestrator)

## SCHNAPPER MASTER – letzter Lauf (29.10.2026, 06:29 UTC, Lauf 20261029-0629)

- F3 / S-010 / PR #40 (Branch `agent/master/20261022-22`): Gemerkte Angebote mit groß geschriebenem URL-Schema (`HTTPS://…`, vom Server angenommen) gingen beim Wiederherstellen als „ungültig (url)“ verloren. Behoben in `sicherungPruefen` (`/^https?:\/\//i`); `JAVASCRIPT:`, `data:`, `FTP://` bleiben abgelehnt, `href` weiter nur bei `https://`. 3 neue Tests, Gegenprobe rot (failures=2).
- Commit e1532c9, Push 87eebba..e1532c9 als Fast-Forward ohne Force. CI `python-tests` success.
- Tests: discover 237 OK, S-010-Modul 21/21 OK (0 Skips), Cloudflare 10/10. CHECK bestanden (AK 1–10), Secret-Scan leer.
- `team/tasks.json`: S-010 bleibt `review`, Laufvermerk im Hinweis ergänzt.
- Offen: Merge-Entscheidung #36, #39, #40, #41, #44, #45, #50 bei Jefrey; eBay-Sandbox-Schlüssel für #45 fehlen weiterhin. Späterer F3-Kandidat: Angebots-`id` > 200 Zeichen geht beim Wiederherstellen verloren.
- Bericht: `team/runs/20261029-0629-master.md`
