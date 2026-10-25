# SCHNAPPER MASTER 2026-10-25 – P0 Sicherheitsgates und KI-Kostenstopp

**Umsetzungspfad:** bestehender Draft-PR #21, Branch `security/schnapper-failclosed-20261022`  
**Freigabe:** NO-GO bis unabhängige Abnahme; **Zusatzkosten:** 0 €  
**Verboten:** direkt auf `main` schreiben, PR mergen, Live-KI starten, Cloudflare deployen, Repo-Sichtbarkeit ändern, Paid-API, Kostenlimit verändern.

## 1. Bestandsaufnahme (nach GitHub-Read-only-Prüfung)

- Repository `jefrey030/Schnapper` ist am 25.10.2026 **public**. Ältere Berichte mit `privat` sind historisch.
- `main` @ `6dbe114271b332ed9d4c282b50c4ce02b112ac49` hat noch den Stundenplan `17 * * * *` mit stillgelegtem GitHub-Models-Backend.
- Stundenlauf [40143662656](https://github.com/jefrey030/Schnapper/actions/runs/40143662656) zeigte `ki_aufrufe=0`, `team_einsatzbereit=false`, `LEAD=KEINE AUFGABE`, `BRAIN/CHECK=ÜBERSPRUNGEN`, `COMMAND=NICHT EINSATZBEREIT`.
- Stilllegung des Legacy-Backends liegt in [Draft PR #53](https://github.com/jefrey030/Schnapper/pull/53); vom aktuellen Draft #21 getrennt prüfen, **nicht** das Cron-Verhalten aus #21 in #53 rückwärts übernehmen.
- Der Sicherheits-Draft #21 schließt die False-Ready-Lücke bei CHECK-Urteil `abgelehnt/nachbessern`, Geheimnisfund und COMMAND `freigabe=nein`; ein alter Actions-Lauf zu PR #21 war `skipped`, **kein PASS**.
- `MockAdapter` und `tests/test_mock_adapter.py` befinden sich bereits auf `main`; nicht erneut bauen.

## 2. Rollen und erledigbare Arbeit

| Rolle | konkreter Auftrag | bisheriger Ausführungsbeleg |
| --- | --- | --- |
| LEAD | Prioritäten: P0 Stilllegung #53, P0 Fail-Closed-Gates #21, P1 Task-/PR-Deduplikation | GitHub-Issues #46–#49 wurden separat konkretisiert |
| BRAIN | Korrigiere unnötige COMMAND-KI-Anfrage ohne LEAD-Aufgabe; teste Negativfall ohne Netzwerk | Codeänderung `team/agent.py`, Regression `tests/test_failsafe.py` in diesem Draft |
| CHECK | Echte vollständige Python-Tests für aktuellen HEAD; geprüftes CI statt historischem SKIP; Cloudflare-Tests gesondert | Nachweise ausschließlich über laufende CI-/Testlinks, nicht aus bloßem Draft |
| COMMAND | Dokumentiere tatsächliche Commit-/CI-ID, BLOCKED/GO, Querverweis auf #53; KEIN erfundener Modellaufruf | dieser Master, späterer bestätigter GitHub-Lauf |

## 3. Ausgeführte Codeänderung

**Fehler:** Mit leerer `team/tasks.json`-Warteschlange läuft `LEAD` auf `KEINE AUFGABE`, `BRAIN` und `CHECK` überspringen; `COMMAND` versuchte trotzdem eine KI-Anfrage. Sie ist unnötig und führte zuletzt zum Fehler des eingestellten GitHub-Models-Dienstes.

**Reparatur im Sicherheits-Draft:** Bei `LEAD.status == "KEINE AUFGABE"` setzt `COMMAND` den Status `ÜBERSPRUNGEN` und **ruft `ki.frage` nicht auf**. Ein neuer Regressionstest prüft, dass kein Modellaufruf erfolgt, kein Protokoll vorgetäuscht wird und der Status ausdrücklich `ÜBERSPRUNGEN` heißt. Bei echten anderen Fehlern bleibt die bestehende dokumentierende Funktion erhalten.

## 4. Prüfanleitung / Abnahme

1. `python3 -m unittest discover -s tests -v` gegen den tatsächlichen PR-HEAD: **CI mit Commit-SHA, Run-ID, Exitcode und Testergebnis** archivieren.
2. `cd cloudflare && node --test test/*.test.mjs`: separat ausführen und Ergebnis/Fehler nachweisen; Python-CI allein sagt nichts über diese Tests aus.
3. Sicherheitsfälle: CHECK=`abgelehnt`/`nachbessern`, COMMAND=`nein`, fehlender Secret-Scan, Secret-Antwort, leere LEAD-Aufgabe ⇒ niemals positive Teamfreigabe.
4. #21/#53 auf Workflow-Konflikte und Secret-Logausgaben prüfen. **Nicht** beide Entwürfe ungeprüft mergen.
5. Echte Vier-KI-Betriebsbereitschaft benötigt vier reale Antwort-IDs, echten Aufrufzähler, positive CHECK-Abnahme, neue gültige lokale KI-Laufzeit und gesonderte Betriebsfreigabe.

## 5. Statusinterpretation

- `ASSIGNED`: Task existiert, noch nicht von echter KI ausgeführt.
- `CODED`: Änderung auf isoliertem Branch geschrieben, nicht in Produktion.
- `CI_PASS`: belegter GitHub-Test **für exakt die getestete Commit-SHA**, keine Produktivfreigabe.
- `SKIP`/`NOT_RUN`/`BLOCKED`: kein bestandener Test bzw. kein laufendes KI-System.
- `NO-GO`: gilt bis Sicherheitsgates, Kosten-/Hostingrahmen und unabhängige Prüfung vollständig belegt sind.

## 6. Weiteres Vorgehen ohne Doppelarbeit

Vorrangiges Release-Gate ist der Stilllegungsentwurf #53, während dieser #21-Draft die unabhängig zu prüfende Sicherheitslogik trägt. **Nicht** bloß PR #21 mergen: dessen historischer Stundenworkflow enthält noch `schedule` und `models: read`. Zuerst müssen #21 und #53 konfliktfrei konsolidiert und mit aktuellen Tests neu geprüft werden.

**Aktueller Entscheid:** NO-GO für Live-KI, Automerge und Deployment. Ein grüner GitHub-Workflow gilt ausschließlich für die in ihm wirklich ausgeführten Tests.

## 7. Echtes Ausführungsprotokoll (25.10.2026)

**Änderungen umgesetzt:**

1. `team/agent.py`: COMMAND-Inferenz bei `LEAD.status=KEINE AUFGABE` aussetzen.
2. `tests/test_failsafe.py`: Regression prüft explizit `fake.frage.assert_not_called()`.
3. `tests/test_agenten.py`: historischen schwächeren Bool-Vergleich im Test auf `toJSON(... ) == 'false'` korrigiert. **Sicherheitsprüfung nicht abgeschwächt.**
4. `.github/workflows/tests.yml`: separater kostenfreier Cloudflare-Worker-Offline-Testjob ohne Deployment ergänzt.

**Gegenprüfung:**

| GitHub Run | Getesteter Commit | Tests | Ergebnis |
| --- | --- | --- | --- |
| [40154421877](https://github.com/jefrey030/Schnapper/actions/runs/40154421877) | `73c23345256f7da02481ca25931ac000e537975d` | Python | **FAIL**: 1 historischer Test erwartet alte Sichtbarkeitsregel (234 Tests, 1 skipped). Fehler danach im Test korrigiert. |
| [40154478265](https://github.com/jefrey030/Schnapper/actions/runs/40154478265) | `d1c3bfdfd6acd90721bbbb33f9d7d8e3a6167a40` | Python | **PASS**: 234 Tests, 0 Fehler, 1 skipped; neuer COMMAND-Test ausdrücklich `ok`. |
| [40154512805](https://github.com/jefrey030/Schnapper/actions/runs/40154512805) | `a3ee7b751da81f0551f65aada507e688ed3f416c` | Python + Cloudflare | **PASS**: Python 234 Tests (1 skipped), Node/Cloudflare 13/13 bestanden (0 skipped). Beide Jobs GitHub `conclusion=success`. |

**Grenze:** Tests sind echte Offline-/CI-Tests, aber die enthaltenen simulierten KI-Antworten sind **keine nachgewiesenen Live-Modelle**. Es gab bei dieser Master-Ausführung keinen externen KI-Aufruf oder produktiven Worker-Deploy. #21 bleibt Draft und darf nicht ohne Abgleich mit Stilllegungs-PR #53 zusammengeführt werden. Endgültige Sicherheits-/Produktionsfreigabe: **NO-GO**.
