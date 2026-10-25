# SCHNAPPER MASTER 84 – S-006-Branchabnahme in Sicherheitskette integrieren

**Datum:** 25.10.2026  
**Projekt:** `jefrey030/Schnapper`  
**Integration-Basis:** MASTER 83 [PR #108](https://github.com/jefrey030/Schnapper/pull/108), finaler HEAD `3b4fbcaf63a8718a3ed9f0426204c3938c8841a2`  
**Quelländerung:** unabhängiger [PR #88](https://github.com/jefrey030/Schnapper/pull/88), `d530a5cbd1071436627b7569ca52821c6dbaa62f`, CI #198 grün  
**Branch:** `integration/master84-s006-full-branch-ci-20261025`  
**Kostenregel:** 0 € neue Kosten, nur Offline-Tests mit den vorhandenen öffentlichen GitHub-Standardrunnern.  
**Status:** Integrations-Draft, keine Merge-, Produktions- oder Agenten-Freigabe.

## Sicherheitsbefund

Bei der MASTER-83-CI galt der übrige Python-Testsatz als grün, obwohl
`test_kandidaten_sind_vollstaendig_in_main` mangels `origin/main` als **skipped**
protokolliert wurde. Dadurch war die Löschkandidatenprüfung **nicht durchgeführt**.
Die vorhandene Reparatur in PR #88 besitzt einen grünen CI-Nachweis, bei dem
der S-006-Test explizit `... ok` meldete.

## Tatsächliche Integrationsarbeit

- `.github/workflows/tests.yml`: im neuen Branch `fetch-depth: 0` und expliziter, rein lesender `git fetch` der fünf benötigten Remote-Refs; Prüf-Exitcodes werden mit `set -euo pipefail` beachtet. Im Unterschied zum Ausgangsdraft bleiben **Ubuntu 24.04, actions/checkout@v7, setup-python@v7, setup-node@v7, public-only-Gates und persist-credentials:false** erhalten.
- `tests/test_branches_s006.py`: geprüfte Prüfregeln aus PR #88 auf den integrierten Branch übernommen, ohne dessen Branch zu verändern. In GitHub Actions führen fehlende Git-Referenzen zu **FAIL** statt stillschweigendem **SKIP**. Genau vier Kandidaten müssen geprüft werden.
- `tests/test_master84_s006_integration.py`: elf neue synthetische Integrations- und Sicherheitsregressionen, die keine Git-Operationen mit Schreibwirkung ausführen.
- Diese Dokumentation: vollständiger Masterplan mit 5 Prüfgruppen und 51 Einzelprüfpunkten.

## 51-Punkte-Integrations- und Abnahmemaster

| # | Bereich | Abnahmekriterium |
|--:|---|---|
| 1 | Quellenprüfung | MASTER 83 / PR #108 HEAD nachlesen |
| 2 | Quellenprüfung | PR #88 als parallelen S-006-Sicherheitsentwurf verifizieren |
| 3 | Quellenprüfung | Bestehenden CI-SKIP in Master-83-Logs bestätigen |
| 4 | Quellenprüfung | PR #88 CI mit S-006 ok statt skipped nachweisen |
| 5 | Quellenprüfung | Quellworkflow und S-006-Test aus PR #88 lesen |
| 6 | Quellenprüfung | Aktuelle Runner-Versionen der Master-83-Linie dokumentieren |
| 7 | Isolierte Integration | Eigenen MASTER-84-Branch vom geprüften Master-83-HEAD erstellen |
| 8 | Isolierte Integration | PR #88 nicht verändern |
| 9 | Isolierte Integration | Anderen Teams keine Branches überschreiben |
| 10 | Isolierte Integration | Checkout v7 auf Ubuntu 24.04 beibehalten |
| 11 | Isolierte Integration | Node-v7 und Python-v7 beibehalten |
| 12 | Isolierte Integration | Git-Vollhistorie mit fetch-depth 0 abrufen |
| 13 | Isolierte Integration | Alle vier Kandidatenrefs explizit read-only holen |
| 14 | Isolierte Integration | origin/main explizit abrufen |
| 15 | Isolierte Integration | Git-Ref-Prüfung bei Fehlern abbrechen |
| 16 | Isolierte Integration | Keine persistierten Checkout-Anmeldedaten zulassen |
| 17 | Isolierte Integration | Weiterhin nur öffentliches Repository nutzen |
| 18 | Isolierte Integration | Keine Workflow-Deployment-Schritte hinzufügen |
| 19 | Fail-Closed Tests | CI fehlende origin/main ref blockiert |
| 20 | Fail-Closed Tests | CI fehlende Kandidatenref blockiert |
| 21 | Fail-Closed Tests | Wegen fehlender Historie kein grüner CI-Teilpass |
| 22 | Fail-Closed Tests | Genau vier Branchkandidaten prüfen |
| 23 | Fail-Closed Tests | Treegleichheit zweier historischer Branches gegen main prüfen |
| 24 | Fail-Closed Tests | Festes Vergleichscommit weiterhin prüfen |
| 25 | Fail-Closed Tests | Ancestor-Prüfung für Stundenrotationsbranch erhalten |
| 26 | Fail-Closed Tests | Lokale Checkouts ohne Refs dürfen Skip kenntlich machen |
| 27 | Fail-Closed Tests | S-006-Aufgabe bleibt vorgeschlagen, keine automatischen Löschungen |
| 28 | Fail-Closed Tests | Das ursprüngliche positive S-006-Szenario nachweisen |
| 29 | Neue Tests | Referenzliste des GitHub-Fetches statisch prüfen |
| 30 | Neue Tests | Sicherheits-Guard für volle Historie prüfen |
| 31 | Neue Tests | Checkout ohne persistierte Credentials prüfen |
| 32 | Neue Tests | Fetch-Befehl auf Lösch-, Merge- und Deployaktionen prüfen |
| 33 | Neue Tests | Ubuntu-24.04-Version beibehalten |
| 34 | Neue Tests | Actions-Checkout/Python/Node-Versionen prüfen |
| 35 | Neue Tests | Privatrepository-Kostenschutz in beiden Jobs prüfen |
| 36 | Neue Tests | Verlangte vier Kandidatenprüfungen bestätigen |
| 37 | Neue Tests | Fehlende einzelne Referenz in CI synthetisch blockieren |
| 38 | Neue Tests | Fehlende lokale Refs ausdrücklich als Skip behandeln |
| 39 | Neue Tests | Alle vier synthetischen Kandidaten als wirklich geprüft testen |
| 40 | Freigabe | Komplette Python-CI nach neuem HEAD durchführen |
| 41 | Freigabe | Cloudflare-Offline-CI unverändert ausführen |
| 42 | Freigabe | S-006-Test muss in GitHub-Logs ok statt skipped sein |
| 43 | Freigabe | Keine Fehler oder unerwarteten Übersprünge verschweigen |
| 44 | Freigabe | CI-Logs mit exakt finalem Commit vergleichen |
| 45 | Freigabe | Neue PR als Draft nur auf MASTER 83 öffnen |
| 46 | Freigabe | Keine Merges nach main, keine Branchlöschungen |
| 47 | Freigabe | Unabhängiger Review für Integrationszweig nötig |
| 48 | Freigabe | Parallele #69/#80/#90 bleiben separate Konfliktgates |
| 49 | Freigabe | Vier reale KI-Modelle und Dauerdienst nicht behaupten |
| 50 | Freigabe | Zusatzkosten 0 €, keine kostenpflichtige KI aktivieren |
| 51 | Freigabe | P0-Produktiv- und Käuferdemo-Gates weiterhin NO-GO |

## Noch nicht integriert / Sicherheitsgrenzen

Diese Änderung übernimmt nur das vorhandene **S-006-CI-Gate** in die MASTER-83-Kette.
Sie integriert **nicht** die eigenständigen Sicherheitsarbeiten [#69](https://github.com/jefrey030/Schnapper/pull/69),
[#80](https://github.com/jefrey030/Schnapper/pull/80) und [#90](https://github.com/jefrey030/Schnapper/pull/90).
Diese enthalten Berührungen zu `team/local_service.py` oder `team/local_ollama.py`
und brauchen eine eigene fachliche Diff-/Konfliktprüfung. Kein automatischer Merge.

Der Branchtest klassifiziert ausschließlich Git-Commit-/Tree-Verhältnisse als **Löschkandidaten**;
er löscht **keinen** Branch. Im Test ohne vollständige lokale Referenzen ist SKIP weiterhin
sichtbar erlaubt; **in GitHub-CI darf dieser Fall nicht grün durchrutschen**.

### Nachweise und Stopps

Echte Abnahme nur mit `python -m unittest discover -s tests -v` plus
`cd cloudflare && node --test test/*.test.mjs` auf dem **finalen PR-HEAD**.
S-006 muss in den Logs `... ok` ausgeben. Fehlende Ref, roter Job, offener Review,
unerlaubte Kosten, nicht integrierte konkurrierende Änderungen => **NO-GO**.

Keine produktive App-Aktivierung, keine autonom ausgeführten KI-Modelle, kein
Cloudflare-Deployment, keine Branchlöschung, keine Veröffentlichung oder Änderung an `main`.
