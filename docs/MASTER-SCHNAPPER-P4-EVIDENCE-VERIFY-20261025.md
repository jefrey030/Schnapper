# SCHNAPPER – MASTER P4: Nachweisprüfer mit SHA-256 und manipulationssicherer Pfadkontrolle

**Datum:** 25.10.2026 · **Priorität:** P0/P1 · **Budget:** 0 € Zusatzkosten · **Änderungsziel:** ausschließlich [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55)  
**Status zu Beginn:** `main` bleibt unberührt; Produktionsfreigabe **NO-GO**.

## Ziel und festgestellte Lücke
Der lokale Pilot schreibt bereits `team/work/<Lauf>/nachweise.json` mit SHA-256-Fingerabdrücken von Stundenbericht, Prozessbericht und vorhandenen Rollenberichten. Eine belastbare Offline-Funktion zum späteren Prüfen dieser Fingerabdrücke fehlt. Ein beschädigtes Ergebnis ist deshalb ohne gesonderten manuellen Vergleich nicht unmittelbar überprüfbar. Der neue Master ergänzt die technische Wiederholbarkeit der Integritätsprüfung, ohne durch bloße Checks echte KI-Agenten zu behaupten.

## Große Auftragsverteilung (Rollen als Arbeitsgebiete, NICHT externe aktive Agenten)

| Arbeitsrolle | Konkrete Aufgabe | Abnahmekriterium |
| --- | --- | --- |
| LEAD | Branch und vorhandene Nachweise prüfen, Kompatibilität und minimale Änderungen planen | Ein Master und ein Review-Draft, keine Doppel-PR |
| BRAIN | Unabhängigen lokalen Nachweisprüfer bauen; SHA-256 gegen vorhandene Dateien verifizieren, strenge Pfad-Whitelist | Keine fremden Pfade oder symbolischen Links öffnen |
| CHECK | Positive und manipulierte Offline-Testfixtures prüfen: Byte-Änderung, fehlende Datei, falscher Hash, Pfad-Traversal, unzulässiger Ordner | GitHub CI grün, reale Testzahlen angegeben |
| COMMAND | Abschlussreport mit SHA, CI-Run, blockierten Restpunkten und Nullkosten-Regeln erstellen | Dokumentation statt Fake-Autonomie |

## Sicherheits- und Funktionalitätsvorgaben

1. `python team/local_service.py --verify <LAUFORDNER>` liest ausschließlich lokale Artefakte und startet **kein** Ollama, kein Netzwerk und keine Agents.
2. Ein erlaubter Lauf ist ein direktes Verzeichnis unter `team/work/`; Pfadübergreifungen, Dateisymlinks und selbst gewählte fremde Pfadnamen werden blockiert. Fehlerlogs enthalten keine Rohdaten aus Berichten.
3. `nachweise.json` muss alle erwarteten Dateien exakt benennen. SHA-256 stimmt Byte-für-Byte überein. Fehlende, zu große und beschädigte Dateien gelten nicht als bestanden.
4. Positiv gilt nur `INTEGRITAET_OK` – niemals `KI_ERFOLGREICH`. Prüfsummen sind **keine digitale Signatur** und schützen nicht gegen Personen, die alle Dateien samt Manifest ändern können.
5. Der Prüfer wird auch nach Erstellung eines Nachweises eingesetzt, um Format-/Prüffehler bei erfolgreichen und blockierten Piloten zu entdecken.
6. Vor Merge: GitHub Actions Python- und Cloudflare-Tests grün; Produktionssysteme, `main` und kostenpflichtige Dienste bleiben unverändert.

## Abnahmecheckliste
- [x] Lokaler Nur-Lese-Nachweisprüfer implementiert
- [x] Reine Offline-CLI `--verify` implementiert
- [x] Zehn Manipulations- und Pfadkontrolltests erfolgreich
- [x] Echter CI-Testlauf Python + Cloudflare erfolgreich, Code-SHA `ac4ba5d3f2b6db1e5ea3a860f40ad5ab1e250c81`, [Run #40211791992](https://github.com/jefrey030/Schnapper/actions/runs/40211791992)
- [x] Code-HEAD und reale CI-Zahlen dokumentiert (Dokumentationscommit erhält separaten CI-Test)
- [x] Unabhängige Produktionsfreigabe ausdrücklich weiterhin NO-GO

## Ausführung – echte GitHub-Arbeit

- `team/local_service.py`: neue, vollständig offline arbeitende Prüffunktion `pruefe_manifest(lauf)`. Sie nimmt nur direkte Laufordner unter `team/work`, akzeptiert keine Symlinks, prüft das Manifest als JSON-Objekt unter Größenlimit und bildet die Dateiliste **selbst** anhand des bekannten Rollen-/Berichtsschemas.
- SHA-256 aller erwarteten Dateien wird erneut aus den Bytes berechnet und mit der gespeicherten Prüfsumme verglichen. Fehlt eine Datei, ist der Digest ungültig, der Datensatz zu groß, die Lauf-ID fremd oder die Manifest-Pfadauflistung manipuliert, lautet das Ergebnis `BLOCKIERT`.
- `--verify LAUFORDNER`: manuell aufrufbares Nur-Lese-Kommando, das keine Arbeitsrollen, Modelle, Netzwerkdienste oder Scheduler-Sperren startet.
- Nach `nachweise.json`-Erstellung wird die neue Prüfung auch bei der normalen lokalen Pilotverarbeitung aufgerufen; falls sie scheitert, wird der Prozess insgesamt als blockiert zurückgemeldet.
- `tests/test_local_service.py`: zehn zusätzliche eigenständige Offline-Testmethoden für positiven/negativen Pilot, geänderte oder gelöschte Datei, unzulässigen Pfad, symbolischen Link, ungültigen SHA-256, widersprüchliche Ergebnisangabe, fehlende Agenten, fremden Laufordner und CLI ohne Prozessstart.
- Ein unmittelbar entdeckter Syntaxfehler im neu ergänzten Test-Kontextmanager wurde vor dem **abschließenden** Testlauf korrigiert.

**Geprüfter Code-HEAD:** `ac4ba5d3f2b6db1e5ea3a860f40ad5ab1e250c81`, [GitHub Actions #40211791992](https://github.com/jefrey030/Schnapper/actions/runs/40211791992). Python: **271 Tests**, **1 übersprungen**, **0 fehlgeschlagen**. Cloudflare: **16 Tests**, **16 bestanden**, **0 fehlgeschlagen**, **0 übersprungen**. Beide Jobs melden Erfolg.

**Grenzen:** Ein SHA-256-Manifest ist ohne externe Signatur **kein** kryptografischer Authentizitätsnachweis gegen Akteure mit Schreibzugriff auf alle lokalen Artefakte. Die Tests nutzen synthetische Daten; es wurde kein echter Ollama-/Cloudflare-Modelllauf aktiviert. `main` ist von dieser Korrektur unberührt. Die ältere Stundenjob-Stilllegung auf `main` und die unabhängige produktive Security-Abnahme bleiben offen. Veröffentlichung/Release weiterhin **NO-GO**. Kosten 0 €.
