# SCHNAPPER MASTER P2 – KI-Fehlerstopp, Rollen-Freigaben und Beweisqualität

**Datum:** 25.10.2026 · **Branch:** `integration/schnapper-p0-mainbased-20261025` · **Review:** [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55) · **Budget:** 0 € Zusatzkosten · **Freigabe:** NO-GO

## Hauptmission
Ein einzelner nicht erfolgreicher Agent darf nie einen erfolgreichen Prozesscode erzeugen, unnötige nachfolgende KI-Modellaufrufe auslösen oder einen positiven Vier-Agentenbericht verursachen. Sicherheits-, Modell- und Produktionskosten bleiben unverändert strikt blockiert.

### Verifizierter Ausgangsstand
- `main` ist öffentlich; die geplante Legacy-KI-Stilllegung liegt nur als ungeprüfter Release-Draft vor. **Keine Main-Änderungen oder Produktion.**
- Entwurf #55 hat Security-/Secret-Redaction-Regressionen und lokale Datei-/Berichts-Abgleichungen. Letzter bestätigter Lauf vor diesem Master: [40197863334](https://github.com/jefrey030/Schnapper/actions/runs/40197863334), Python 238 Tests (1 Skip), Cloudflare 16/16 PASS.
- `team/agent.py::command()` unterdrückt den Modellaufruf bisher nur bei `LEAD=KEINE AUFGABE`; bei fehlenden/fehlgeschlagenen LEAD/BRAIN/CHECK-Ergebnissen wird COMMAND bislang trotzdem aufgerufen.
- `team/agent.py::main()` liefert bisher bei gewöhnlichem `NICHT EINSATZBEREIT`, `FEHLER` oder `ÜBERSPRUNGEN` meist Exitcode 0. Der lokale Scheduler beendet Folgerollen erst nach nonzero.
- Das ist ein belegtes Fehlerketten-/Nachweisproblem, **kein** Nachweis für einen tatsächlichen Live-KI-Aufruf.

## Vier Rollen – konkrete Aufgaben

| Rolle | Arbeitsauftrag | Abnahmebeleg |
| --- | --- | --- |
| LEAD | Pfade, Abhängigkeiten und minimale Änderung identifizieren; keine alten PRs duplizieren | Branch- und Codebeleg |
| BRAIN | COMMAND vor jeder KI-Anfrage auf drei positive Vorgänger, positive CHECK-Entscheidung, echte Testresultate und Secret-Scan überprüfen; Prozess Exitcode bei Nicht-OK auf nonzero setzen | Commit und nachvollziehbare Negativtests |
| CHECK | Ohne Netzwerk/echte Modelle prüfen: COMMAND darf bei Fehlern keines der Modelle aufrufen, lokale Rolle mit Nicht-OK wird nonzero, positives Szenario bleibt nutzbar | GitHub Actions Python und Cloudflare PASS, Testzahl, Skip |
| COMMAND | Belege, Commit-ID, CI-Run und Restblocker dokumentieren; keinerlei Selbstfreigabe | Dokumentierter Bericht, NO-GO Produktion |

## Sicherheitsverträge
1. Die Rollenkette muss bei fehlenden, fehlerhaften und negativen CHECK-Ergebnissen **vor** kostenrelevanter COMMAND-Anfrage stoppen.
2. Ein `main()`-Prozess gibt nur bei `status=OK` Erfolg (Exitcode 0) zurück. Auch `KEINE AUFGABE` darf keine grüne KI-Ausführung behaupten.
3. Das technische CHECK-Protokoll kann weiterhin unabhängig als separater Bericht entstehen. `skipped` gilt nie als `PASS`.
4. Fehlerinhalte enthalten keine rohen Geheimnisse. Der Legacy-Cron bleibt auf dem Draft stillgelegt, `main` unverändert.
5. Es werden ausschließlich Mock- und Offline-Tests ausgeführt; keine Live-API, kein lokales Modell gestartet, keine Cloudflare-Migration, keine zusätzliche Nutzungskosten.
6. Vier auf GitHub verteilte Rollen sind **Aufträge**, keine autonom laufenden KI-Instanzen.

## Abnahme
- [x] COMMAND blockiert Modellaufrufe bei fehlender/fehlgeschlagener Vorgängerkette
- [x] COMMAND blockiert bei negativem oder ungeprüftem CHECK/Test/Secret-Scan
- [x] Prozessstatus nonzero für jede nicht erfolgreiche Agentenrolle, inklusive leerer Warteschlange
- [x] Positiver Testfall für vier gültige Mock-Rollen weiterhin grün
- [x] Python-/Cloudflare-CI auf Code-SHA `7e57f2738e10293d8ff7bb8e99f786e1be6f46a1` erfolgreich – [Run 40198664505](https://github.com/jefrey030/Schnapper/actions/runs/40198664505)
- [x] Finaler Code-Lauf: 244 Python-Tests (1 Skip), 16 Cloudflare-Tests (0 Skips), 0 Testfehler. Nachfolgender Dokumentationscommit erhält eigenen CI-Test.
- [x] Unabhängige Security-/Release-Freigabe verbleibt **NO-GO**

## Ausgeführte Codearbeiten und tatsächliche Testergebnisse

- `team/agent.py`: Bei fehlender/fehlerhafter LEAD-, BRAIN- oder CHECK-Vorrolle, fehlender Aufgaben-ID, negativem oder ungültigem CHECK-Urteil, fehlenden/fehlgeschlagenen Unit-Tests oder fehlendem/positivem Geheimnisscan wird COMMAND **vor der Modellinferenz** `ÜBERSPRUNGEN`. Kein KI-Anruf erfolgt in solchen Fällen.
- `team/agent.py::main`: Status `OK` gibt Exitcode 0, alle anderen Rollenstatus geben Exitcode 1. Der lokale Scheduler kann Folgerollen so beim ersten gewöhnlichen Rollenfehler stoppen. `BERICHT` bleibt als dokumentierender Sonderfall separat aufrufbar.
- `tests/test_failsafe.py`: Mock-Regressionen für ungültige Vorrollen, fehlende Dateien, negatives CHECK-Urteil, fehlerhafte/mangelnde Tests, Secret-Scan-Ausfall, positive COMMAND-Voraussetzungen und nonzero-Codes.
- `tests/test_agenten.py`: Offline-Probelauf mit nicht erreichbarer KI erwartet jetzt nonzero der Agenten; unabhängiger Gesamtbericht wird weiterhin erstellt. Positiver Vierfach-Mocklauf bleibt nutzbar.
- `team/local_service.py`: `vier_echte_ki_antworten` wird bei **jedem** technischen Pilotfehler `false`. Die frühere Fehlermeldungs-Stichwortsuche konnte ansonsten eine positive Kennzahl trotz negativer CHECK-/Prozessprüfung erzeugen.
- `tests/test_local_service.py`: Neue Regression für negativen CHECK-Pilotstatus trotz im Mock behaupteter positiver KI-Antwortzahl.

**Nachweis des kombinierten Codes:** [GitHub Actions #40198664505](https://github.com/jefrey030/Schnapper/actions/runs/40198664505), SHA `7e57f2738e10293d8ff7bb8e99f786e1be6f46a1`: Python **244 Tests**, davon **1 SKIP**, **0 FAIL**; Cloudflare-Worker **16 Tests, 16 PASS, 0 FAIL, 0 SKIP**. Beide CI-Jobs melden `success`.

**Abgrenzung:** Alle KI-Testantworten sind Offline-Simulationen. Es fand kein realer Modellaufruf, kein Deployment und kein Merge statt. Der ältere Legacy-Cron ist auf `main` bis zu einer gesonderten Review-/Merge-Freigabe weiterhin aktiv. Ein grüner Testlauf bedeutet **nicht** automatisch echte Vier-KI-Bereitschaft. **NO-GO** bleibt bestehen.
