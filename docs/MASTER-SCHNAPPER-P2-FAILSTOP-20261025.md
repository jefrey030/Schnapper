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
- [ ] COMMAND blockiert Modellaufrufe bei fehlender/fehlgeschlagener Vorgängerkette
- [ ] COMMAND blockiert bei negativem oder ungeprüftem CHECK/Test/Secret-Scan
- [ ] Prozessstatus nonzero für jede nicht erfolgreiche Agentenrolle, inklusive leerer Warteschlange
- [ ] Positiver Testfall für vier gültige Mock-Rollen weiterhin grün
- [ ] Python-/Cloudflare-CI auf exakter Commit-SHA erfolgreich
- [ ] Finaler Run mit echten Testzahlen/SKIPs dokumentiert
- [ ] Unabhängige Security-/Release-Freigabe verbleibt **NO-GO**
