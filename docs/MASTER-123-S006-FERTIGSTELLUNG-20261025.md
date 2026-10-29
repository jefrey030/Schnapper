# MASTER 123 – Fertigstellungs-Integration: MASTER 122 + S-006-CI-Gate

**Datum:** 25.10.2026 | **Projekt:** SCHNAPPER | **Status:** DRAFT, kein Release | **Budget:** 0 EUR Zusatzkosten.

## Entscheidender Ausgangsbefund

[MASTER 122 / PR #122](https://github.com/jefrey030/Schnapper/pull/122) bestand CI am finalen SHA `293e3699475982d7b7b0f162ccf9cc8c32f4fc24` mit Python **290 PASS, 1 SKIP** und Cloudflare **16 PASS** (Run 40217039979). Der einzige SKIP: `test_kandidaten_sind_vollstaendig_in_main`, weil `origin/main` im CI-Checkout fehlte. Ein bestandener Workflow war also keine vollständige S-006-Branchprüfung.

Eine vorhandene, bereits erarbeitete S-006-Korrektur steht in [PR #109](https://github.com/jefrey030/Schnapper/pull/109) und dessen Vorgänger PR #88. Dieser Master integriert ausschließlich die erforderliche Prüf- und Checkout-Logik in die **separate** MASTER-122-Sicherheitskette. Keine fremde Branch überschreiben oder schließen.

## Technische Umsetzung auf eigenem neuen Branch

**Branch:** `fix/master123-s006-ci-integration-20261025`, auf HEAD von PR #122 aufgebaut.

1. `tests/test_branches_s006.py`: vorhandenen **Fail-Closed**-Test aus PR #109 übernommen. Fehlende `origin/main`- oder Kandidatenrefs in GitHub Actions werden zu TEST-FAIL (nicht SKIP). Alle vier historischen Branchkandidaten müssen wirklich geprüft werden, ohne sie zu löschen. Lokal ohne vollständige Refs darf SKIP weiterhin ehrlich ausgewiesen werden.
2. `.github/workflows/tests.yml`: volle Historie `fetch-depth: 0`, read-only `git fetch` der exakt benötigten Referenzen, kein persistiertes Checkout-Token, `set -euo pipefail`, keine Deployment- oder Löschaktionen. Vorhandene Versionen von `checkout@v4`, `setup-python@v5`, `setup-node@v4`, `ubuntu-latest`, öffentliches Repo-Gate unverändert beibehalten.
3. `tests/test_master123_s006_integration.py`: 11 bekannte Offline-Regressionen aus dem MASTER-84-Entwurf übernommen, nur die statischen Versionskontrollen auf die vorhandenen Runner-Versionen angepasst. Validiert fehlende Refs, Branch-Gesamtprüfung, Kosten- und Token-Schutz, Workflow-Berechtigungen und keine Git-Schreibaktionen.

**Sicherheitsgrenze:** Testnachweise aus vorigen Branches beweisen diese Integration noch nicht. Erst die GitHub CI auf dem finalen MASTER-123-SHA zählt.

## Großmaster: 36 Arbeitspakete / Rollen

### LEAD: Zustand & Prioritäten
- [x] 01: Bestehenden MASTER-122-PR und dessen HEAD identifizieren.
- [x] 02: Exakten Python-SKIP in GitHub-Rohlog nachweisen.
- [x] 03: Vorhandene S-006-Korrektur aus PR #109 ermitteln.
- [x] 04: Bestehende S-006-Datei und CI-Konfiguration nachlesen.
- [x] 05: Keine neuen parallelen Privatdaten- oder Modell-Projekte starten.
- [x] 06: Integrationsbasis MASTER 122 festlegen statt main direkt zu verändern.
- [x] 07: Separaten Entwicklungszweig angelegt.

### BUILDER: echte Integration
- [x] 08: S-006-Test auf vier Pflichtkandidaten und FAIL bei CI-Lücke bringen.
- [x] 09: Workflow-Historie vollständig abrufen.
- [x] 10: Alle fünf Remote-Referenzen explizit holen.
- [x] 11: Checkout-Credentials nicht persistieren.
- [x] 12: Bestehende Runner-/Action-Versionen beibehalten.
- [x] 13: Bestehende öffentliche Null-Zusatzkosten-Runner-Regel beibehalten.
- [x] 14: Vorhandene 11 S-006-Integrationsregressionen übernehmen.
- [x] 15: Keine echten KI-Läufe oder Branchlöschungen implementieren.
- [x] 16: Änderungen in neue GitHub-Commits schreiben.

### CHECK: reproduzierbare Sicherheitsprüfung
- [ ] 17: GitHub-Python-Suite auf **finalem neuen SHA** ausführen.
- [ ] 18: GitHub-Cloudflare-Tests auf finalem neuen SHA ausführen.
- [ ] 19: Im Python-Rohlog ausdrücklich S-006 `... ok` prüfen.
- [ ] 20: Python-PASS, FAIL, SKIP anhand `Ran N tests` ermitteln.
- [ ] 21: Cloudflare PASS/FAIL/SKIP aus Rohlog ermitteln.
- [ ] 22: Negativtests für fehlende Referenzen belegen.
- [ ] 23: Im GitHub-Diff keine andere Produktionsfunktion verändert nachweisen.
- [ ] 24: Unabhängigen fachlichen Review des Integrations-PR einholen.
- [ ] 25: Abhängigkeiten mit parallel gestapelten PRs #109/#120/#121 koordinieren.
- [ ] 26: Bei fehlenden Remote-Branches nicht grün melden; bewusst stoppen.

### COMMAND: ehrlicher Abschluss / projektweite Abnahme
- [ ] 27: Draft-PR für Integration gegen PR #122 eröffnen.
- [ ] 28: Exakten finalen Head-SHA mit Workflow vergleichen.
- [ ] 29: CI-Belege und Restblocker im PR protokollieren.
- [ ] 30: Keine Merge-/Deploy-/Produktivaktion ohne gesonderte Freigabe.
- [ ] 31: ZENTNA-Produktionsdatenrechte weiterhin als separaten P0-Blocker führen.
- [ ] 32: Keine ZENTNA-Prod-Migration ohne Rollback, E2E und unabhängige Freigabe.
- [ ] 33: JERRY Auth/Kosten-Draft #118 unabhängig mit funktionierender CI abnehmen.
- [ ] 34: SCHNAPPER echtes lokales KI-Host-E2E erst nach separater Betreiberfreigabe prüfen.
- [ ] 35: Käuferdemo und Produkteinführung nur anhand echter Host-/Browsernachweise bewerten.
- [ ] 36: Master abschließen mit klarem GO/NO-GO und ohne erfundene Gesamtprozente.

## Noch offene projektweite Risiken

- **ZENTNA:** Zuletzt bestätigtes produktives Profil-SELECT-Leck für `status` / `zents_balance`, fehlende drei Schutz-/Moderatorfunktionen. Vorhandene Reparaturentwürfe sind kein Produktionsrollout.
- **JERRY AL:** Auth-/Provider-Schutzentwurf PR #118; CI zuvor nicht erfolgreich; echte Musik-/Bild-/Video-Erzeugung nicht belegt.
- **SCHNAPPER:** Vollständige Integration, unabhängiger Review und echte vier lokale Modellantworten fehlen. Dieser PR repariert ein CI-Prüfgate; das Produkt ist damit nicht verkaufs-/betriebsbereit.

## Verbindliche Grenzen

Keine kostenpflichtigen APIs/Modelle, keine autonomen KI-Starts, keine Produktivdatenänderungen, keine Merge-/Branchlöschungen, keine Käuferfreigabe. **NO-GO** bis alle erforderlichen Freigabegates erfüllt sind.
