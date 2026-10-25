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
- [x] Lock und Rückgabewert im bestehenden Draft implementiert
- [x] Thread-Kollision von parallelen Aufrufzählungen fail-closed geprüft
- [x] Verbliebene Sperrordner, Lock-Dateien und Symlinks blockieren korrekt
- [x] Zähler-Schreibfehler geben Lock frei, während gescheiterte Lock-Entfernung fail-closed blockiert
- [x] Bestehende positive / negative Tests bleiben grün
- [x] Python und Cloudflare auf Code-HEAD `a058c5688ab19e52efc0d3f784bb7eb7b68c3b62` bestanden – [CI #40214516418](https://github.com/jefrey030/Schnapper/actions/runs/40214516418)
- [x] Code-SHA und CI: 284 Python-Tests (1 Skip), 16/16 Cloudflare-Tests. Keine Live-KI; Veröffentlichung NO-GO.

**Verbleibende Freigabesperre:** Draft #55 ist nicht auf `main` übernommen; ein grüner Offline-Test beweist keine autonome Vier-KI-Laufzeit. Mehrprozessbetrieb benötigt nach Review eine echte Integrations- und Lastprobe auf dem eigenen Host. Locking verhindert normale parallele konkurrierende Abläufe, ersetzt keine vertrauenswürdigen Dateiberechtigungen gegen lokalen Vollzugriff.

## Ausgeführte Implementierung, 25.10.2026

### Atomare Reservierung für genau einen Modellversuch
Die Methode `team/local_ollama.py::KI._zaehle` erstellt vor jedem Lesen und Inkrementieren einen exklusiven Sperrordner `ki_aufrufe.txt.lock` neben der Zählerdatei. `pathlib.Path.mkdir(mode=0o700)` ist ein atomarer Ausschlussmechanismus des Dateisystems: Ein zweiter Aufrufer erhält beim existierenden Lock sofort die kontrollierte Ausnahme `KINichtVerfuegbar`. Die früheren P4-Prüfungen für negative/übergroße Zähler, Budget 1–6 und Zähler-Symlinks bleiben bestehen. Im Erfolgsfall gibt `_zaehle()` die reservierte Nummer zurück; `frage()` verwendet diese Nummer im Ergebnis anstelle eines späteren erneuten Dateilesens.

### Fehler und Wiederaufnahme
Bei ungültigem Zähler, Budgetüberschreitung und simuliertem Schreibfehler wird kein Modell gestartet; die Sperre wird auf dem regulären Fehlerpfad entfernt. Misslingt das Entfernen, gilt der Aufruf als fehlgeschlagen und die übrig gebliebene Sperre blockiert weitere Versuche. **Kein automatisches Entsperren oder Zurücksetzen** bei vermutetem Absturz. Betreiber prüfen in diesem Fall zunächst, dass kein Prozess mehr läuft und die gespeicherten Aufrufdaten intakt sind; jede spätere manuelle Freigabe erfordert eine gesonderte bewusste Entscheidung.

### Sieben zusätzliche Mock-Regressionsfälle
`tests/test_local_ollama.py` prüft: konkurrierenden Zugriff mit einem synchronisierten Thread-Paar; verwaisten Sperrordner; Wiederfreigabe nach simuliertem Schreibfehler; Budgetgrenze mit Lock-Bereinigung; korrekte Versuch-ID unabhängig von späterem Dateiinhalt; fehlgeschlagene Sperrenentfernung; Lock durch Datei/Symlink. Die Tests führen keinerlei echte Ollama-HTTP-Anfragen aus.

**Letzter getesteter Code-Stand:** SHA `a058c5688ab19e52efc0d3f784bb7eb7b68c3b62`, [GitHub Actions #40214516418](https://github.com/jefrey030/Schnapper/actions/runs/40214516418). `python-tests` **284 ausgeführt / 1 SKIP / 0 FAIL**; `cloudflare-tests` **16 PASS / 0 FAIL / 0 SKIP**. Beide GitHub-Jobs `success`. Dieser Dokumentationscommit wird ebenfalls separat von GitHub Actions überprüft.

**Abgrenzung:** Die Konkurrenzprüfung simuliert zwei Threads, keinen produktiven Mehrprozess- oder Cloud-Dauertest. Exklusiver lokaler Sperrordner ist keine kryptografische Authentifizierung gegenüber Angreifern mit voller lokaler Dateizugriffskontrolle. Das Archivieren der CI ist kein Nachweis von vier real autonomen KI-Prozessen. Der Legacy-Stundenjob auf `main` bleibt bis zur separaten Freigabe unberührt. **0 € zusätzliche Dienste aktiviert; NO-GO Merge/Deployment**.
