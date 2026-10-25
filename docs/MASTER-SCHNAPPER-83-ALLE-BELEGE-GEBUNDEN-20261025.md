# SCHNAPPER MASTER 83 – Alle sieben Nachweise an tatsächlich geprüfte Daten binden

**Datum:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Basis:** MASTER 82 – [PR #106](https://github.com/jefrey030/Schnapper/pull/106), HEAD `950a970fba40a1ecbb7e0ae92bc8d494bd950058`  
**Arbeitszweig:** `fix/master83-all-evidence-binding-20261025`  
**Priorität:** P0: Beweis-Integrität; P1: Offline Regression; P2: Integration und Review  
**Budget:** 0 € zusätzliche kostenpflichtige Dienste; keine Bezahl-API, keine Produktivfreigabe  
**Modus:** Nur Codeänderung auf eigenem Branch, MOCK-Tests und GitHub-CI.

## Nachgewiesene Ursache

MASTER 82 schloss eine Lücke für das intern erstellte `prozesse.json`. Der Stundenbericht, `LEAD.json`, `BRAIN.json`, `CHECK.json`, `COMMAND.json` und `ki_aufrufe.txt` wurden aber zwar als JSON/Zähler validiert, ihre Hashes im Manifest kamen später von **erneut gelesenen** Dateien. Werden diese Dateien nach der fachlichen Prüfung ausgetauscht, können konsistent scheinende positive Manifest-Hashes für ungeprüfte Inhalte entstehen.

## Implementierung

- `team/local_service.py`: der begrenzte, symlink-sichere Dateileser `_lese_sicher()` liefert maximal 2 MB aus *einem* Dateideskriptor und lässt nur reguläre Dateien zu.
- `pruefe_nachweise(..., beleg_hashes=...)` merkt zu **denselben gelesenen Bytes**, die tatsächlich als Rollen-JSON oder lokaler Zähler geprüft wurden, jeweils den SHA256-Schnappschuss.
- `einmal()` merkt den SHA256 des gelesenen Stundenberichts und erhält zusätzlich die fünf Snapshots aus den vier Rollen plus Zähler.
- Vor dem erfolgreichen Manifest müssen **alle sieben Artefakte** übereinstimmen: sechs ursprünglich geprüfte Belege plus der bereits in MASTER 82 an seine eigenen Laufdaten gebundene Prozessbeleg. Fehlende, ausgewechselte oder anders formatierte Dateien verhindern ein positives Ergebnis.
- `tests/test_master82_process_binding.py`: bestehende Mock-Hook-Signatur für optionale Hash-Snapshots aktualisiert.
- `tests/test_master83_all_evidence_binding.py`: neue Offline-Testklasse für Dateimutationen nach der fachlichen Prüfung, einschließlich semantisch gleicher Inhalte mit veränderten Bytes und Symlink-Austausch.

## Abnahme- und Arbeitsliste – 49 Punkte

| # | Bereich | Konkreter Nachweis |
|--:|---|---|
| 1 | Quellenlage | MASTER 82 PR #106 und finalen Ausgangs-SHA bestimmen |
| 2 | Quellenlage | Bestehende Sicherheits-PRs #69, #80, #90 lesen |
| 3 | Quellenlage | Nicht dieselben Beweisprüfungen unkoordiniert erneut schreiben |
| 4 | Quellenlage | Eigenen Arbeitszweig auf MASTER-82-HEAD erzeugen |
| 5 | Quellenlage | Andere Branches, main und Produktionssysteme nicht verändern |
| 6 | Ursache | Bisherige SHA256-Bindung nur für prozesse.json identifizieren |
| 7 | Ursache | Ungebundene Bericht-Datei im Prüfpfad ermitteln |
| 8 | Ursache | Ungebundene LEAD-Datei ermitteln |
| 9 | Ursache | Ungebundene BRAIN-Datei ermitteln |
| 10 | Ursache | Ungebundene CHECK-Datei ermitteln |
| 11 | Ursache | Ungebundene COMMAND-Datei ermitteln |
| 12 | Ursache | Ungebundenen lokalen Aufrufzähler ermitteln |
| 13 | Umsetzung | Reguläre Dateien mit O_NOFOLLOW am FD öffnen |
| 14 | Umsetzung | Groesse des Beleges auf 2 MB begrenzen |
| 15 | Umsetzung | FIFOs und Spezialdateien mit fstat ablehnen |
| 16 | Umsetzung | Bytes direkt aus sicherem Lesepfad als JSON parsen |
| 17 | Umsetzung | Hash nur aus denselben JSON-Validierungsbytes bilden |
| 18 | Umsetzung | Prüfhash für Bericht speichern |
| 19 | Umsetzung | Prüfhash für vier Rollen speichern |
| 20 | Umsetzung | Prüfhash für Aufrufzähler speichern |
| 21 | Umsetzung | Alle sechs Schnappschüsse mit finalem Manifest vergleichen |
| 22 | Umsetzung | Unvollständige Prüfhashliste abweisen |
| 23 | Umsetzung | Originalen Prozesshash-Gate von MASTER 82 behalten |
| 24 | Umsetzung | Bei Manipulation strukturierte BLOCKIERT-Antwort erzeugen |
| 25 | Offline-Regression | Sieben unveränderte Artefakte akzeptieren – nur MOCK |
| 26 | Offline-Regression | LEAD nach Validierung manipulieren – BLOCKIERT |
| 27 | Offline-Regression | BRAIN nach Validierung manipulieren – BLOCKIERT |
| 28 | Offline-Regression | CHECK nach Validierung manipulieren – BLOCKIERT |
| 29 | Offline-Regression | COMMAND nach Validierung manipulieren – BLOCKIERT |
| 30 | Offline-Regression | Stundenbericht nach Validierung manipulieren – BLOCKIERT |
| 31 | Offline-Regression | Aufrufzähler nach Validierung manipulieren – BLOCKIERT |
| 32 | Offline-Regression | Numerisch gleichen Zähler mit anderen Bytes abweisen |
| 33 | Offline-Regression | Semantisch gleiche Rollen-JSON mit anderen Bytes abweisen |
| 34 | Offline-Regression | Semantisch gleichen Bericht mit anderen Bytes abweisen |
| 35 | Offline-Regression | Symlink bei Bericht nach Validierung abweisen |
| 36 | Offline-Regression | Symlink bei Rolle nach Validierung abweisen |
| 37 | Offline-Regression | Symlink bei Zähler nach Validierung abweisen |
| 38 | Offline-Regression | Fehlenden Zähler ohne vollständige Hashliste abweisen |
| 39 | Offline-Regression | Kaputten Rollenbericht ohne vollständige Hashliste abweisen |
| 40 | Freigabe & Integration | Alte MASTER-77- bis MASTER-82-Regressionen erhalten |
| 41 | Freigabe & Integration | GitHub Python CI auf finalem SHA prüfen |
| 42 | Freigabe & Integration | Cloudflare Offline CI auf finalem SHA prüfen |
| 43 | Freigabe & Integration | Logs auf neue Tests und echte Gesamtsumme prüfen |
| 44 | Freigabe & Integration | SKIP-Angaben im Testlauf sichtbar kennzeichnen |
| 45 | Freigabe & Integration | Parallele PR-Dateiüberschneidungen dokumentieren |
| 46 | Freigabe & Integration | Keine voreilige Merge-Konfliktfreiheit behaupten |
| 47 | Freigabe & Integration | Unabhängiges Security-Review als offene Schranke kennzeichnen |
| 48 | Freigabe & Integration | Vier echte KI-Modellaufrufe nicht als nachgewiesen melden |
| 49 | Freigabe & Integration | Kein Autodeploy, keine Kostenfreigabe oder Auto-Merge |

## Integrations- und Reviewlage

Die eigenen Folge-PRs von MASTER 76 bis 83 sind **gestapelte Draft-Änderungen**, keine bereits produktiv eingebauten Patches. Daneben existieren eigenständige Entwürfe [PR #69](https://github.com/jefrey030/Schnapper/pull/69), [PR #80](https://github.com/jefrey030/Schnapper/pull/80), [PR #90](https://github.com/jefrey030/Schnapper/pull/90). Sie können dieselben Dateien betreffen. Für einen gemeinsamen Integrations-Branch müssen diese Inhalte später manuell überprüft, Konflikte beseitigt und End-to-End-Tests neu ausgeführt werden; aus einzelnen grünen PR-CI-Läufen folgt **keine** Gesamtfreigabe.

## Sicherheitsmodell & Grenzen

Auch vollständige SHA256-Dateibindungen beweisen **nicht**, dass vier KI-Modellaufrufe tatsächlich bei einem unabhängigen Provider stattfanden. Die MOCK-Fixtures verwenden absichtlich simulierte Daten. Die Dateibindung schützt gegen nachträgliche lokale Änderungen im Prüfzeitfenster, nicht gegen einen bösartigen Akteur mit Kontrolle über Runner, Code, Prozessspeicher oder alle Artefaktquellen. Ohne unabhängige Review bleibt jeder Merge und jedes Deployment gesperrt.

## Stop/Go

**CODE-GO:** GitHub Actions auf dem finalen Commit, beide Jobs erfolgreich; neue Negativtests tatsächlich ausgeführt.  
**MERGE-GO:** NICHT erteilt – unabhängiger Review und integrierte Konfliktprüfung fehlen.  
**LIVE-GO:** NICHT erteilt – echte lokale Ollama-Rotation, autonomer Dauerbetrieb und operativer Sicherheitsnachweis fehlen.

Keine kostenpflichtigen Provider, keine externen KI-Aufrufe, keine Deployments, keine Änderungen an `main`, keine Kaufhandlung, keine automatische Zusammenführung.
