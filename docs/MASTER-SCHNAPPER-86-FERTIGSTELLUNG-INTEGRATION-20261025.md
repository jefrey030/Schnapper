# SCHNAPPER MASTER 86 – Fertigstellungsintegration und Ollama-Nachweise

**Datum:** 25.10.2026
**Repository:** `jefrey030/Schnapper`
**Basis:** [MASTER 85 / PR #120](https://github.com/jefrey030/Schnapper/pull/120), `c7795b47c0e5d7da93227a5fc9e4e553f7898fc1`
**Integrationsquelle:** unabhängiger [Ollama-Nachweis-PR #90](https://github.com/jefrey030/Schnapper/pull/90)
**Branch:** `integration/master86-ollama-proof-readiness-20261025`
**Budget:** 0 EUR zusätzliche Kosten, keine externen KI-Aufrufe
**Freigabe:** DRAFT / NO-GO für Merge, Deployment und tatsächlichen Vier-KI-Betrieb.

## Bestandsprüfung

Die MASTER-85-Kette liegt gegenüber `main` (Stand `6dbe114271b332ed9d4c282b50c4ce02b112ac49`) 80 Commits voraus, jedoch noch **nicht** in `main` integriert. Parallele [PR #69](https://github.com/jefrey030/Schnapper/pull/69) und [PR #80](https://github.com/jefrey030/Schnapper/pull/80) überlappen bei `team/local_service.py` inhaltlich mit MASTER77–85. **Kein unkontrolliertes Auto-Merge dieser Entwürfe.**

PR #90 enthält die bisher nicht in MASTER85 enthaltene Validierung der Ollama-Abschlussantworten. Deren Vertragsprüfung wird in die bestehende Sicherheitskette übertragen, **ohne** die älteren unsicheren Zählerzugriffe aus PR #90 zurückzuübernehmen.

## Im eigenen Integrationszweig umgesetzte Änderungen

- `team/local_ollama.py`: Modell, `done`, `done_reason`, Assistant-Rolle, nichtleerer Antworttext, Zeitzonenzeitstempel, Integer-Tokenzahlen prüfen. Antwort-ID als ausschließlich lokal erzeugte Kennung ausweisen; Abschlussdaten separat ausgeben. Bestehenden atomaren Call-Counter, Lock-Timeout, hartes Sechserlimit und die bereits reservierte Aufrufnummer beibehalten.
- `team/local_service.py`: Für jede Rolle werden die lokalen Ollama-Abschlussfelder auch beim Gesamtbericht geprüft; fehlerhafte oder nur behauptete Abschlussdaten blockieren den technischen Pilot. Vorherige Hash-, Prozess- und Rollenbelegprüfungen bleiben bestehen.
- `tests/test_local_ollama.py`: PR90-Regressionsfälle mit synthetischen Ollama-Antworten.
- `tests/test_master80_counter.py`: synthetische Erfolgs-/Fehlerantworten für neuen Vertrag aktualisiert, parallele Quotenkontrolle beibehalten.
- `tests/test_master77_proof.py` und `tests/test_local_service.py`: reine MOCK-Proben mit explizit nicht attestierter ID und Abschlussfeldern.
- `tests/test_master86_proof_integration.py`: separate Vertrags- und Integrationsregressionen; keine echten Modelle, kein Netzwerk.

## 70-Punkte-Fertigstellungsplan

Die Matrix ist eine **Nachweis- und Restaufgabenliste**; die Ausführung aller Punkte wird nicht bloß durch ihre Aufnahme behauptet.

| Nr. | Gruppe | Einzelarbeit |
|---:|---|---|
| 1 | A Ausgangslage | Repo und PR120 verifizieren |
| 2 | A Ausgangslage | Sicherheitskette gegen main vergleichen |
| 3 | A Ausgangslage | 80 nicht integrierte Commits festhalten |
| 4 | A Ausgangslage | PR69 Pilotbelege prüfen |
| 5 | A Ausgangslage | PR80 Rollenbelege prüfen |
| 6 | A Ausgangslage | PR90 Ollama-Belege prüfen |
| 7 | A Ausgangslage | Parallelzweige unverändert lassen |
| 8 | A Ausgangslage | MASTER85-Basissicherheit erhalten |
| 9 | A Ausgangslage | Neuen eigenen Branch verwenden |
| 10 | A Ausgangslage | 0 EUR Zusatzkosten einhalten |
| 11 | B Modellnachweise | PR90-Validator übernehmen |
| 12 | B Modellnachweise | Falschen Antworttyp abweisen |
| 13 | B Modellnachweise | Falsches Modell abweisen |
| 14 | B Modellnachweise | Unvollständige Antwort abweisen |
| 15 | B Modellnachweise | Falsche Assistant-Rolle abweisen |
| 16 | B Modellnachweise | Leeren Modelltext abweisen |
| 17 | B Modellnachweise | Ungültigen Zeitstempel abweisen |
| 18 | B Modellnachweise | Fehlende Zeitzone abweisen |
| 19 | B Modellnachweise | Tokenzählung streng validieren |
| 20 | B Modellnachweise | Katalogeinträge filtern |
| 21 | B Modellnachweise | Lokale UUID korrekt kennzeichnen |
| 22 | B Modellnachweise | Providerdaten separat erfassen |
| 23 | B Modellnachweise | Reservierte Aufrufnummer behalten |
| 24 | B Modellnachweise | Zählersperre erhalten |
| 25 | B Modellnachweise | Aufrufquote 1 bis 6 erhalten |
| 26 | B Modellnachweise | Cloud-/Redirect-Sperren erhalten |
| 27 | C Viererteam-Check | Vier Rollen-Abschlussbelege erforderlich |
| 28 | C Viererteam-Check | Jede Rollen-ID als lokal ausweisen |
| 29 | C Viererteam-Check | Jede Rolle mit erwarteter Modellkennung prüfen |
| 30 | C Viererteam-Check | Chat-Abschluss pro Rolle prüfen |
| 31 | C Viererteam-Check | Tokenzahlen pro Rolle prüfen |
| 32 | C Viererteam-Check | Zeitstempel pro Rolle prüfen |
| 33 | C Viererteam-Check | Vier eindeutige lokale IDs weiterhin prüfen |
| 34 | C Viererteam-Check | CHECK-Gate erhalten |
| 35 | C Viererteam-Check | COMMAND-Gate erhalten |
| 36 | C Viererteam-Check | Sieben verpflichtende Artefakt-Hashes erhalten |
| 37 | C Viererteam-Check | Prozessrollen und Exitcodes bewahren |
| 38 | C Viererteam-Check | STOP/Runner-Lock erhalten |
| 39 | D Offline-Tests | Neue Integrationsregressionen |
| 40 | D Offline-Tests | Positive synthetische Fixture |
| 41 | D Offline-Tests | Fehlender ID-Typ negativ |
| 42 | D Offline-Tests | Falscher ID-Typ negativ |
| 43 | D Offline-Tests | Fehlender Abschlussbeleg negativ |
| 44 | D Offline-Tests | Falsches Modell negativ |
| 45 | D Offline-Tests | Unvollständiger Chat negativ |
| 46 | D Offline-Tests | Kontextlimit-Abbruch negativ |
| 47 | D Offline-Tests | Falsche Rolle negativ |
| 48 | D Offline-Tests | Naiver Zeitstempel negativ |
| 49 | D Offline-Tests | Null Token negativ |
| 50 | D Offline-Tests | Bool Token negativ |
| 51 | D Offline-Tests | Korrekte Mockvalidierung positiv |
| 52 | D Offline-Tests | Fehlende Providerfelder negativ |
| 53 | D Offline-Tests | MASTER80-Quoten-Tests behalten |
| 54 | D Offline-Tests | MASTER77-Mocktests behalten |
| 55 | D Offline-Tests | S-006-CI-Gate erhalten |
| 56 | D Offline-Tests | Cloudflare-Offline-Tests erhalten |
| 57 | E Übergabe und Restabnahme | Draft-PR erstellen |
| 58 | E Übergabe und Restabnahme | GitHub CI final prüfen |
| 59 | E Übergabe und Restabnahme | Python-Testergebnisse protokollieren |
| 60 | E Übergabe und Restabnahme | Cloudflare-Testergebnisse protokollieren |
| 61 | E Übergabe und Restabnahme | S-006 explizit ok statt Skip |
| 62 | E Übergabe und Restabnahme | CI-Fehler im eigenen Branch reparieren |
| 63 | E Übergabe und Restabnahme | Finale SHA bestätigen |
| 64 | E Übergabe und Restabnahme | Keine reale Vier-KI-Behauptung |
| 65 | E Übergabe und Restabnahme | PR69/80/90 Konfliktprüfung offen |
| 66 | E Übergabe und Restabnahme | Unabhängiger Sicherheitsreview offen |
| 67 | E Übergabe und Restabnahme | Lokalen Host-Endtest offen kennzeichnen |
| 68 | E Übergabe und Restabnahme | Deployment gesperrt |
| 69 | E Übergabe und Restabnahme | Main-Merge gesperrt |
| 70 | E Übergabe und Restabnahme | Keine bezahlten APIs |

## Release-Gates

**CODE-GO:** erst, wenn Python + Cloudflare Offline-CI am finalen HEAD erfolgreich und S-006 nicht übersprungen ist.

**REVIEW-GO:** noch offen; unabhängige Sicherheitsprüfung und inhaltliche PR-Konfliktbereinigung (#69/#80/#90) nötig.

**LIVE-GO:** noch offen; vier echte Ollama-Antworten auf vertrauenswürdigem Host, Kosten-/Fehler-/Not-Aus-Test und Zustimmung zur Inbetriebnahme nötig. Synthetische JSON-Objekte und lokale UUIDs beweisen keine echte Modellinferenz.

**MAIN/PROD:** kein Merge, kein Deploy, keine Branchlöschung, keine Cloud-/Bezahl-API, keine Änderungen an Produktivdaten.
