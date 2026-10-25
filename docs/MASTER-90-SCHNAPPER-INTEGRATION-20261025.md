# MASTER 90 – SCHNAPPER Sicherheitsintegration / autonome KI gesperrt

**Stand:** 25.10.2026 · **Zweig:** `chatgpt/master90-schnapper-integration-20261025` · **Basis:** Sicherheits-PR #21 @ `07090ccacebf7cc03ff6c180eee231880658e672` · **Gegenstück:** Stilllegungs-PR #53 @ `838148ed58c8d709e8bf2fdb6bc461bfa829fbb7`

## Mission

Die separaten Sicherheitsarbeiten aus #21 und #53 **im eigenen isolierten Branch** vereinigen, ohne vorhandene fremde PR-Zweige, `main`, Cloudflare, Supabase oder reale KI-Dienste zu ändern. Qualitäts- und Sicherheitsprüfung getrennt ausweisen. Ziel ist eine gemeinsame, überprüfbare Integration; **nicht** das Starten eines Vier-KI-Betriebs.

**Harte Regeln:** 0 € zusätzliche Dienste/Kosten; kein Modell-Download, kein Ersatz-API-Vertrag, keine Sichtbarkeitsänderung, kein produktiver KI-/Worker-Start, kein Main-Merge/Deployment, keine Abschwächung des CHECK-/COMMAND- oder Not-Aus-Prinzips. Kein Mock als echte Modellantwort ausgeben. Code-/CI-PASS ersetzt keine Betriebsfreigabe.

## Ausgefüllter Arbeitsmaster (20 Arbeitspakete)

| ID | Priorität | Aufgabe | Ergebnis der aktuellen Runde |
| --- | --- | --- | --- |
| M90-01 | P0 | Ursprungs-PRs und Head-SHAs abgleichen | ERLEDIGT: #21/#53 gelesen |
| M90-02 | P0 | Überlappende Dateien bestimmen | ERLEDIGT: Stundenworkflow + `tests/test_agenten.py` |
| M90-03 | P0 | Eigenen isolierten Zweig erstellen | ERLEDIGT, oben benannter Branch |
| M90-04 | P0 | GitHub-Models-Adapter fail-closed übernehmen | UMGESETZT: `team/ki.py` aus #53 |
| M90-05 | P0 | Zeitgesteuerte GitHub-Modellaufrufe beseitigen | UMGESETZT: kein `schedule`-Event im Integrationsworkflow |
| M90-06 | P0 | Job selbst bei manuellem Trigger verweigern | UMGESETZT: fester `false &&` Job-Guard |
| M90-07 | P0 | Ausführbare KI-/Git-Push-Schritte aus Workflow entfernen | UMGESETZT: nur nicht laufender Info-Schritt, keine Agenten-/Provider-/Schreibschritte |
| M90-08 | P0 | Workflow-Berechtigung reduzieren | UMGESETZT: ausschließlich `contents: read` |
| M90-09 | P0 | Altes GitHub-Models-README korrigieren | UMGESETZT: neue Dokumentation aus #53 |
| M90-10 | P0 | KI-Off-Negativtest inklusive null Netzaufrufen | UMGESETZT in `tests/test_agenten.py`, GitHub-CI noch zu prüfen |
| M90-11 | P0 | Mock-Durchlauf isoliert erhalten | UMGESETZT: nur Test patcht den stillgelegten Modellkatalog |
| M90-12 | P0 | Workflow-Kostenschutztests auf neue Abschaltung anpassen | UMGESETZT: `tests/test_actions_cost_guard.py` |
| M90-13 | P0 | Bestehende Sicherheitslogik aus #21 bewahren | QUELLCODE BEIBEHALTEN: `team/agent.py`, `tests/test_failsafe.py`, lokale Service-/Cloudflare-Gates |
| M90-14 | P0 | Reale Python-Testreihe auf integriertem Commit ausführen | OFFEN, mit GitHub-CI nach Draft-PR prüfen |
| M90-15 | P0 | Cloudflare-Offline-Testreihe auf integriertem Commit | OFFEN, mit GitHub-CI nach Draft-PR prüfen |
| M90-16 | P0 | Unabhängigen Code-/Berechtigungsreview erhalten | OFFEN |
| M90-17 | P0 | Prüfen, dass kein aktives KI-Hosting entstanden ist | BISHER: keine Dienste aktiviert; erneute Prüfung vor Merge |
| M90-18 | P1 | Live-Not-Aus, D1 und Free-Tarif unabhängig abnehmen | OFFEN; keine Test-Deployments |
| M90-19 | P1 | Vier echte getrennte lokale Modellantworten nachweisen | NOT_RUN, **nicht** durch Unit-Mocks ersetzt |
| M90-20 | P0 | Produktions-/Releaseentscheidung | **NO-GO**, separate Freigabe notwendig |

## Technische Integration und Sicherheitsentscheidung

- Der gesamte Code für CHECK, COMMAND, STOP-Logik und die Cloudflare-Prüfer verbleibt aus #21 unverändert auf diesem Zweig.
- Der eingestellte GitHub-Models-Client wird aus #53 übernommen und verweigert die Modellbestimmung, bevor er einen API-Aufruf ausführt.
- Der frühere Workflow wird **nicht bloß per Job-Flag unterdrückt**, sondern verliert zusätzlich Zeitplan, Modellberechtigung, Agentenbefehle, Token-Umgebung und Schreib-/Push-Schritte. Das verhindert eine versehentliche Reaktivierung durch eine einfache Änderung am `if`-Ausdruck.
- Die reinen Python-Testmocks sind weiterhin als Nachahmer gekennzeichnet. Sie weisen keine laufenden KI-Agenten nach.
- Die Schutzprüfung aus #21 gegen private/fehlende Repository-Sichtbarkeit bleibt im deaktivierten Job-Guard enthalten, gilt aber ausdrücklich nicht als Live-Cost-Test.
- Der Branch ist auf #21 aufgebaut, **kein automatischer Merge beider PRs**. Die Dokumentation und KI-Abschaltung aus #53 wurden selektiv übernommen. Ein unabhängiger Vergleich auf einem späteren Integrationsstand bleibt erforderlich.

## Abnahmekriterien

1. `python -m unittest discover -s tests -v`: Exit 0, 0 FAIL; Skips explizit nennen.
2. Cloudflare-Offline-Tests: Exit 0 und alle relevanten Fälle PASS, ohne Deployment.
3. `.github/workflows/schnapper-hourly.yml` enthält keinen Zeitplan, keine Models-Berechtigung, keine Agenten-/Provideraufrufe, keinen Git-Push und einen `false &&`-Guard.
4. Keine Änderungen an `main`, den Köpfen der bestehenden PRs, der Repo-Sichtbarkeit, echten Nutzerkonten, Budgets, Secrets oder Produktionssystemen.
5. Ein separater Security-Review mit Konfliktprüfung und nachweisbarer Kostenfreigabe ist nötig. Bis dahin **nicht mergen** und **nicht reaktivieren**.

## Fremde Projekte – nur Koordination, keine behauptete Ausführung

- ZENTNA #86/#87/#95: JWT-/HTTP-E2E, vollständige CI, Backup/Restore und unabhängiger Review offen; Käuferdemo NO-GO.
- JERRY #118: Token-UI, verteiltes Providerlimit und belastbare CI offen.
- SCHNAPPER ONE #1/#2: vollständiges Offline-Gate offen.
- BEATMEISTER #2/#3: Android-/Audio-/Integrationsabnahme offen.

**Wichtig:** Die Erstellung dieses Dokuments und eines GitHub-Draft-PRs startet keine autonomen KI-Teams und genehmigt weder Veröffentlichung noch Produktion.