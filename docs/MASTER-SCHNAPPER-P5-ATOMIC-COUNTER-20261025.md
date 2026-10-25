# SCHNAPPER MASTER P5 – atomare lokale Aufrufzählung und parallele Prozesssicherheit

**25. Oktober 2026 · 0 € Zusatzkosten · Draft PR #55 · Keine Produktionsfreigabe**

## Hauptmission
Eine Race-Condition im lokalen Ollama-Aufrufzähler schließen. Die vier KI-Rollen werden sequentiell vom lokalen Dienst aufgerufen, aber der Adapter ist auch einzeln nutzbar; mehrere Prozesse oder Threads könnten derzeit denselben Stand aus der Datei lesen, beide erhöhen und beide eine Modellanfrage innerhalb eines nominell gleichen Budgets senden.

## Belegter Ausgangsbefund
In `team/local_ollama.py::KI._zaehle()` folgen `read_text`, Limitprüfung und `write_text` getrennt ohne exklusiven Lock. Diese Read-Modify-Write-Sequenz ist **nicht atomar**. `KI.frage()` liest den Zähler später nochmals und könnte unter Konkurrenz eine falsche `aufruf_nr` berichten. Die vorangegangene P4-Härtung gegen falsche Datenformate, ungültige Limits und Symlinks bleibt erhalten.

## Vier Arbeitsrollen (Aufträge, keine behaupteten externen KIs)
| LEAD | BRAIN | CHECK | COMMAND |
| --- | --- | --- | --- |
| Bestehenden PR und Kostenpolitik verifizieren | Atomare Sperre, fehlersicheren Zähler und genaue Versuch-IDs implementieren | Offline-Race-/Crash-/Stale-Lock-Regressionen und komplette CI prüfen | Commit- und CI-Nachweis sowie Restrisiken dokumentieren |

## Abnahmekriterien
1. Vor dem Lesen/Schreiben wird ausschließlich lokal ein `mkdir`-basierter, exklusiver Sperrordner mit engem Zugriffsschutz angelegt. Existiert er bereits, erfolgt sofort `KINichtVerfuegbar` **ohne** weiteren Modellaufruf.
2. Bei Schreibfehlern, beschädigtem Zähler oder unerwarteter Ausnahme: Modellaufruf blockiert, Sperre nach Möglichkeit entfernt, keine positive KI-Bereitschaft.
3. Eine tatsächlich gezählte Anfrage gibt ihre eigene Aufrufnummer direkt aus dem gesperrten Inkrement zurück; spätere konkurrierende Schreibvorgänge dürfen die Nummer nicht verändern.
4. Ein verbliebener Lock nach Absturz führt **fail-closed** zur Blockade. Keine automatische riskante Wiederaufnahme oder stilles Löschen fremder/staler Locks.
5. Nur Mock-/Offline-Tests; Ollama bleibt fest auf localhost begrenzt. Keine Live-Modelle, Cloud-APIs, Kosten, Secrets, Merge- oder Deployment-Aktionen.
6. Tests und Dokumentation auf abschließender GitHub-Commit-SHA mit echten Ergebnissen nachweisen. **NO-GO Produktion** ohne unabhängige Review.

## Abnahmeprotokoll
- [ ] Lock und Rückgabewert im bestehenden Draft implementiert
- [ ] Kollision von parallelen Aufrufzählungen fail-closed geprüft
- [ ] Verbliebene Lockdatei / Sperrordner blockiert korrekt
- [ ] Counter-Fehler geben Lock frei und starten keine Modelle
- [ ] Bestehende positive / negative Tests bleiben grün
- [ ] Python und Cloudflare CI auf finalem HEAD bestanden
- [ ] SHA, Run-ID, Kosten-/Autonomie-Grenzen dokumentiert

**Verbleibende Freigabesperre:** Draft #55 ist nicht auf `main` übernommen; ein grüner Offline-Test beweist keine autonome Vier-KI-Laufzeit. Mehrprozessbetrieb benötigt nach Review eine echte Integrations- und Lastprobe auf dem eigenen Host. Locking verhindert normale parallele konkurrierende Abläufe, ersetzt keine vertrauenswürdigen Dateiberechtigungen gegen lokalen Vollzugriff.
