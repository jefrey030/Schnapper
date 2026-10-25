# SCHNAPPER – MASTER 75: CI-Warnungen, Runner-Stabilität und Sicherheitsgates

**Stand:** 25.10.2026  
**Projekt:** jefrey030/Schnapper  
**Basis:** PR #55, `integration/schnapper-p0-mainbased-20261025`, geprüfter Start-HEAD `79cb3f6991229cec0ab665bf735d5d3ddedee4cd`  
**Eigener Branch:** `fix/master75-ci-node24-ubuntu24-20261025`  
**Priorität:** P0 (unveränderte Sicherheit), P1 (Warnungsbeseitigung)  
**Budget:** 0 € zusätzliche Kosten; nur öffentliche Standardrunner; keine bezahlten APIs  
**Modus:** isolierter Review-Branch; KEIN Merge/Deploy/Live-KI

## A. Mission (20 Prüf-/Arbeitsaufträge)

| Nr. | Priorität | Auftrag | Nachweis/Abnahme |
| --- | --- | --- | --- |
| 01 | P0 | Richtiges SCHNAPPER-Repo identifizieren | GitHub: jefrey030/Schnapper |
| 02 | P0 | Sicherheits-PR #55 zuordnen | Draft, Basis main, nicht gemergt |
| 03 | P0 | CI-HEAD und realen letzten Run verifizieren | Run 192 / ID 40198769377 / success |
| 04 | P0 | Python-Job verifizieren | success im Run 192 |
| 05 | P0 | Cloudflare-Offline-Job verifizieren | success im Run 192 |
| 06 | P0 | Legacy-KI-Workflow kontrollieren | keine cron-Schedule, `if: ${{ false }}` |
| 07 | P1 | Node-20-Action-Warnung lokalisieren | checkout@v4, setup-python@v5, setup-node@v4 |
| 08 | P1 | Neuere Node-24-kompatible Actions wählen | checkout@v7, setup-python@v7, setup-node@v7 |
| 09 | P1 | Ubuntu-Migration begrenzen | `ubuntu-24.04` statt `ubuntu-latest` in Testjobs |
| 10 | P0 | CI-Token klein halten | `permissions: contents: read` |
| 11 | P0 | Checkout-Zugangsdaten nicht persistieren | `persist-credentials: false` |
| 12 | P0 | Unnötigen Node-Paketcache ausschalten | `package-manager-cache: false` |
| 13 | P0 | Private-Repo-Kostenbarriere erhalten | `if: github.event.repository.private == false` |
| 14 | P0 | Jobzeitlimit erhalten | je 5 Minuten |
| 15 | P0 | Python- und Cloudflare-Offlinetests unverändert starten | `unittest` / `node --test` |
| 16 | P1 | Offline-Regressionen für Workflow-Schutz schreiben | `tests/test_ci_hardening.py` |
| 17 | P1 | Vollständiges Python-Testpaket auf finalem Commit prüfen | GitHub Actions neuer PR: **ausstehend** |
| 18 | P1 | Vollständige Cloudflare-Offline-Tests auf finalem Commit prüfen | GitHub Actions neuer PR: **ausstehend** |
| 19 | P0 | Sicherheitsreview durch unabhängige Stelle | **ausstehend** |
| 20 | P0 | Separates Go/No-Go für Merge/Deploy/Live-KI | **NO-GO** |

## B. Tatsächlich ausgeführte Änderungen

1. GitHub-Repository und PR #55 gelesen; Run #192 (40198769377) sowie beide erfolgreichen Job-Schritte bestätigt.
2. In der aktiven, gesicherten Integrationsbasis den stillgelegten Legacy-Workflow und den Test-Kostenschutz geprüft.
3. Einen **neuen eigenen Branch** vom geprüften PR-Head erstellt. Die Branches `main`, PR #55 und die übrigen PRs bleiben unverändert.
4. Nur `.github/workflows/tests.yml` gehärtet: drei Actions auf v7, feste Ubuntu-24.04-Runner, keine Checkout-Credentials, kein unnötiger Paketcache.
5. Neue statische Offline-Regressionen in `tests/test_ci_hardening.py` ergänzt.
6. Dieses Master-Protokoll geschrieben. Live- und Produktionsprüfung erfolgt **nicht**.

## C. Sicherheitsgrenzen

- **Kein** `main`-Merge, Auto-Merge, Deployment, produktiver Datenbankzugriff oder Produktions-Secret.
- **Keine** GitHub-Models-Reaktivierung, bezahlte KI, Cloud-LLM-Abfrage oder autonome Teamaktivierung.
- Vier-KI-Teamrollen (LEAD/BRAIN/CHECK/COMMAND) hier ausschließlich konzeptionell: keine vorgetäuschten Agentenbelege.
- Die Prüfung des CI-Workflows ersetzt weder einen End-to-End-Test der Anwendung noch ein Sicherheitsreview.
- Die Ubuntu-24.04-Fixierung ist eine **temporäre Stabilitätsmaßnahme**. Ubuntu 26.04 muss vor erneuter Umstellung explizit getestet werden.
- Node.js 22 ist weiterhin die **Test-Laufzeit des Cloudflare-Codes**. Node.js 24 ist die interne Laufzeit der aktualisierten GitHub-Actions – beides ist zu unterscheiden.

## D. Freigabekriterien / Stoppsignale

**GO für Code-Review**, wenn auf dem finalen HEAD beide Tests grün sind und keine neuen Warnungen durch alte Actions entstehen.  
**NO-GO**, wenn Runnerkosten, Privatrepo-Runs, fehlende Logs, rote Tests, Konflikte oder Unterschiede zwischen geprüfter und finaler SHA auftreten.  
**NO-GO für Produktion**, bis explizite Eigentümerfreigabe + unabhängige Security-Abnahme + reale Host-/Kosten-/Integrationsprüfungen vorliegen.

## E. Quellen und geprüfte Belege

- Sicherheitsintegration: https://github.com/jefrey030/Schnapper/pull/55
- Vorheriger erfolgreicher CI-Lauf: https://github.com/jefrey030/Schnapper/actions/runs/40198769377
- Checkout v7: https://github.com/actions/checkout
- Setup-Python v7: https://github.com/actions/setup-python
- Setup-Node v7: https://github.com/actions/setup-node
- Ubuntu-Runner-Migration: https://github.blog/changelog/2026-09-17-ubuntu-26-generally-available-and-latest-migration/

**Abnahmezustand beim Schreiben:** Änderungen auf getrenntem Branch vorhanden; CI-Verifikation auf finalem HEAD und unabhängiges Review ausstehend.
