# SCHNAPPER MASTER P0-Integration – 25.10.2026

**Ziel:** Abschaltung des veralteten GitHub-Models-Stundenlaufs (Draft #53) mit den unabhängig vorbereiteten Sicherheitsgates aus Draft #21 **auf einem separaten Integrationsbranch** zusammenführen.

**Status:** INTEGRATION IN DRAFT / NO-GO PRODUKTION. Die Erstellung dieses Masters startet keine externe KI.

## Unveränderliche Grenzen

- Budget: 0 € zusätzliche Ausgaben; kein bezahlter Dienst, kein Modell-Download, keine Cloud-Ressourcen.
- Kein Direkt-Commit auf `main`, kein Merge, kein Release, kein Deploy, keine Sichtbarkeits-/Billingänderung.
- Unit-/Offline-Tests und GitHub-CI sind erlaubt, aber keine echten Angebote, Käufe, externen KI-Aufrufe oder produktiven D1-Migrationen.
- Behauptungen `KI läuft`, `Sicherheitsfreigabe` oder `Produktion fertig` erfordern separate echte Nachweise.

## Eingangsstand und Konfliktauflösung

| Quelle | Relevanter Bestand | Entscheidung |
| --- | --- | --- |
| [Draft #21](https://github.com/jefrey030/Schnapper/pull/21) | Fail-Closed-Gates bei negativem CHECK/COMMAND, Secret-Scan und Redaktionsregeln, lokaler Not-Aus, Cloudflare-D1-Control, Regressionen; Python 234 Tests (1 Skip), Cloudflare 13/13 im Run 40154574061 | **Als Basis übernommen**, Sicherheit beibehalten |
| [Draft #53](https://github.com/jefrey030/Schnapper/pull/53) | Stillgelegter Legacy-Models-Adapter und aktualisierte README; eigener Workflow ohne Cron | Backend/README übernommen, stillgelegten Workflow **vereinfacht und zusätzlich eingeschränkt** |
| `main` | Stündlicher Legacy-Workflow, keine 4 echten KI-Aufrufe nachgewiesen | **Nicht geändert** |
| [Draft #50](https://github.com/jefrey030/Schnapper/pull/50) | Vier KI-Rollen mit noch offener Diagnoseaufgabe S-014 | **Nicht** als autonom gelaufene KI ausgeben, kein Merge |

## Master-Aufgaben und tatsächliche Umsetzung

### LEAD – PR-/Dateikonflikte und Prioritäten
- Bestehende PRs lesen und Überschneidungen dokumentieren. #21 und #53 haben Konflikt in `.github/workflows/schnapper-hourly.yml` und in den Legacy-Workflow-Tests.
- P0: alten Cron endgültig deaktivieren, keine Reaktivierung per manuellem Dispatch.
- P0: negative CHECK-/COMMAND-Urteile dürfen nie zu `team_einsatzbereit=true` führen.
- P1: saubere Dokumentation, isolierter Draft-PR gegen `main`.

### BRAIN – kombinierte Codeänderung
- Grundlage: Branch von #21 mit dem Sicherheitscode, Cloudflare-Not-Aus, Secret-Gates und Tests.
- Übernommen aus #53: `team/ki.py` deaktiviert GitHub Models vor Inferenz; `README.md` beschreibt die reale gesperrte Laufzeit.
- `.github/workflows/schnapper-hourly.yml` vollständig auf einen minimalen **manuell aufrufbaren, aber durch `if: ${{ false }}` nicht startenden** Platzhalter reduziert. **Kein `schedule`, keine `models: read`, keine `contents: write` oder KI-Schritte.**
- `tests/test_agenten.py`: Legacy-Stilllegung, kein HTTP-Aufruf und mit lokalem Nachahmer isolierte Tests absichern.
- `tests/test_actions_cost_guard.py`: Die neue dauerhafte Workflow-Sperre statt des früheren Public/Private-Cron-Guards prüfen.

### CHECK – unabhängige technische Abnahme
- GitHub CI auf **genau dem SHA** dieses Integrations-Drafts starten und die tatsächlichen Ergebnisse lesen.
- Zwei getrennte Jobs: `python -m unittest discover -s tests -v` sowie `node --test test/*.test.mjs` im Ordner `cloudflare`.
- Fehler beheben, Tests erneut ausführen. `skipped` niemals als bestanden bezeichnen.
- Negativszenarien: keine aktive Cron-Zeile, manueller Legacy-Job wird übersprungen, keine API-Nutzung, negative CHECK-/COMMAND-Freigabe, D1-Not-Aus.
- Hinweis: lokale Fake-Modelle in Unit-Tests sind **keine** echten vier externen KI-Antworten.

### COMMAND – Protokoll und Go/No-Go
- Branch-Commit, CI-Run-IDs, echte Testergebnisse und Restblocker dokumentieren.
- Kein `merge`, kein `workflow_dispatch`, kein Worker-/D1-Deploy.
- `NO-GO` bis zusätzlich unabhängiges Review und E2E-/Host-Betriebsnachweise vorliegen.
- Dieser Master verweist auf nachfolgende Nachweise, aber behauptet noch keine CI-Ergebnisse für den neuen Integrationsbranch.

## Akzeptanzkriterien

- [x] Vier Rollen und Konfliktprioritäten erstellt.
- [x] Abgeschalteten GitHub-Models-Adapter mit striktem Fail-Closed aus #53 übernommen.
- [x] Vorhandene Sicherheitsgates aus #21 in separatem Branch beibehalten.
- [x] Alten Cron-Workflow statisch deaktiviert; anstelle einer unsicheren Legacy-Aufgabe nur gesperrter Platzhalter.
- [x] Regressionen für Workflow- und Backend-Sperre aktualisiert.
- [ ] Aktuelle Python- und Cloudflare-CI für **finalen Branch-HEAD** unabhängig bestätigt.
- [ ] Externe Sicherheits-/Codeprüfung und manuelle Freigabe.
- [ ] Echte lokale KI-/Staging-Durchführung (ausdrücklich nicht Teil dieses Masters).

## Zustand

**Draft, keine produktive Freigabe.** Rollenzuweisung ist eine dokumentierte Arbeitsplanung, nicht vier laufende KI-Instanzen.
