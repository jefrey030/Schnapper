# SCHNAPPER – P0-Endabnahme, 26.10.2026

## Entscheidung

**NO-GO.** Die zwei reproduzierten Fehler sind korrigiert und durch reale lokale Regressionen abgedeckt. Ein vollständiger KI-/Android-Betriebsnachweis liegt nicht vor. Kein Merge, Deployment, App-Release oder kostenpflichtiger Aufruf.

## Integrationsprüfung

| PR | Geprüfter Kopf | Befund |
|---|---|---|
| #124 | bbadec46e52f9581c5929a4159574e7f431df026 | S-006 fehlt in CI nicht stillschweigend: fehlende Referenzen führen zum Fehler; alle Kandidaten geprüft. Bestandteil der lokalen Ausgangshistorie. |
| #125 | 5a4bcd29b975f92c7c9951bc96f89d43e771ce8d | STOP wurde aktiv überwacht, aber nur direkter Prozess beendet. Hier durch Prozessgruppenabbruch ergänzt. Bestandteil der lokalen Ausgangshistorie. |
| #126 | 4151013b634bf07277da3e05ffc1c4faf09cc699 | Ausgangsbaum 0a10be2ea285639edbae9582384b89b9a7c48003 identisch mit lokalem Integrationsstand. Freigabe, Zähler, Pflichtbelege bleiben erhalten. |
| #127 | 1b25970eefe8d12a4f5a04fbbb56d92c3c32b512 | Vier geänderte Dateien überschneiden sich nicht mit Sicherheitskorrekturen. Separater kombinierter Teststand: 491 Python-Tests und 16 Node-Tests bestanden, keine Skips. Keine Änderung am Replit-Branch. |

Die vier PR-127-Dateien wurden nur in einen temporären Teststand übernommen. Der Upload enthält keine Missions-/BLITZ-Änderungen. Dessen Testbericht nennt die Ausgangs-SHA; der zusätzliche Overlay-Inhalt stammt exakt aus den vier Dateien von PR #127. Das ist keine Behauptung eines bereits gemergten Git-Commits.

## Korrekturen

- Eigene POSIX-Session pro Rolle, TERM/KILL an ganze Prozessgruppe bei STOP; KILL bei Timeout und für verbliebene Nachkommen nach Rollenende. Begrenztes Drain/Wait.
- FD-verankerte Verzeichnisöffnung, O_NOFOLLOW in jeder Komponente, atomarer Austausch privater Artefakte. Rollen-, Vorschlags- und Berichtsausgaben nutzen diese Funktionen.
- Symlink-Negativtest für alle vier Rollen LEAD/BRAIN/CHECK/COMMAND; Leseschutz und atomarer Austausch eines Dateilinks ohne Veränderung seines Ziels.
- Reale harmlose Nachkommenprozesse: TERM ignorieren, Elternprozess früh beendet, Timeout. Keine simulierte Inferenz als echt bezeichnet.
- `scripts/p0_readiness.py`: nur lesende Vorprüfung; keine Freigabe erzeugt, keine KI gestartet.

## Vier Rollen – geprüfte Offline-Gates

LEAD muss eine gültige offene Aufgaben-ID liefern. BRAIN benötigt einen gültigen LEAD-Auftrag und schreibt einen Vorschlag. CHECK benötigt gültige Vorgänger, echte ausgeführte Unit-Tests und einen sauberen Geheimnisscan. COMMAND benötigt bestätigte Vorgänger und ein strukturiertes Abschlussprotokoll. Jede fehlende/korrupte/negative Übergabe blockiert. Die gesamte Suite enthält diese Regressionen; das belegt ausschließlich Kontrolllogik, keine vier realen Modellantworten.

## Verbindliche offene P0-Gates

| Gate | Konkreter Nachweis / fehlender Nachweis | Nächster Schritt |
|---|---|---|
| Echter Vier-KI-Lauf | Vorprüfung: Ollama nicht installiert, Dienst/Modell nicht verfügbar; keine gültige lokale Betreiberdatei. Keine Inferenz ausgeführt. | Auf geeignetem eigenen Host Ollama und lokales zulässiges Modell bereitstellen; genau eine offene Aufgabe und kurzlebige Betreiberdatei gemäß operator_approval.py. Danach einmaliger Lauf, keine Schleife. |
| Laufender Modellrequest bei STOP | Separater Ollama-Server liegt außerhalb der Rollen-Prozessgruppe. Serverabbruch bisher nicht nachgewiesen. | Exklusiven Testserver mit messbarer Anfragebeendigung prüfen; keine Prozesse anderer Nutzer beenden. |
| Prozess-/Dateisystem-Isolation | Eigene Prozessgruppe stoppt gewöhnliche Nachkommen. Absichtlich mittels setsid ausbrechender Code und Verschieben bereits geöffneter Verzeichnisse durch gleichberechtigte Prozesse sind nicht isoliert. | Vor Freigabe Vertrauensmodell festlegen und bei untrusted Code OS-Sandbox/cgroup/geschützten Nutzerkontext nachweisen. |
| Finale CI und Review | Neue SHA braucht GitHub-CI und unabhängigen fachlichen Review. | SHA-gebundene Jobs, S-006 ohne Skip, Pflichtprüfungen und Konfliktprüfung. |
| Android-/Produkt-Endabnahme | adb nicht installiert; kein Gerät/Emulator angeschlossen, keine Android-Bedienprüfung. MISSION/BLITZ laut #127 Bibliotheken ohne vollständige UI-/Scheduler-/Push-Anbindung. | Unten stehende Geräteabnahme ausführen; fehlende Produktanbindung separat umsetzen. |

## Kostenlos geprüfte Alternative

llama.cpp/llama-server unterstützt lokale CPU-/GPU-Inferenz und lokale HTTP-Chat-Endpunkte. Primärquelle: https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md . Hier ist llama-server ebenfalls nicht installiert; kein Modellbestand oder echter Lauf nachgewiesen. Der vorhandene Adapter validiert Ollama-spezifische Abschlussmetadaten. Deshalb kein stiller Austausch und keine erfundenen Ollama-Belege. Alternative erfordert eigenen lokalen Adapter, eigene Metadatenprüfung, dieselben Freigabe-/Zähler-/STOP-Gates und echten Vier-Rollen-Test. Modelllizenz und Hardwarekosten sind separat zu beachten; keine kostenpflichtige API aktiviert.

## Vorbereiteter echter E2E-Ablauf

1. Auf dem Testhost `python scripts/p0_readiness.py` ausführen. Blocker beseitigen, nicht umgehen. Betreiberdatei bleibt privat und wird nie committet. Bestehende Tasks nicht pauschal schließen: isolierte Testkopie mit genau einer autorisierten offenen Aufgabe verwenden.
2. Einmal `python team/local_service.py --once`, mit lokalem Modell und ohne Cloud-Fallback. Alle vier Rollen müssen echte Antworten und Exitcode 0 liefern; genau vier Aufrufe, konsistente Aufgaben-ID, gültige Abschlussmetadaten, CHECK bestanden und COMMAND-Freigabe.
3. Erzeugten Lauf mit `python team/local_service.py --verify team/work/LAUF` prüfen: sieben Pflichtdateien und Byte-Hashes müssen stimmen. Rohdaten privat halten, nur redigierte Ergebnisse veröffentlichen.
4. Separater frischer Testlauf: STOP während laufender Inferenz. Alle Rollen-/Modellprozesse nachweislich beendet, keine Nachfolgerolle gestartet, keine spätere Ausgabe und kein Erfolgsbericht.
5. Negativfälle: abgelaufene/falsche Freigabe, STOP vor Start, fehlendes Modell, korrupte Belege, manipulierte Links. Jeder Fall muss blockieren; Testartefakte privat und temporär.

## Android-Abnahme vorbereitet, noch nicht bestanden

Mit einem echten Android-Gerät und dem später freigegebenen Testhost: Chrome-Seite laden; Hoch-/Querformat, Touchbedienung, Tastatur und Zurück-Taste; Suche/Filter/Dubletten/Preisverlauf; ungültige Eingaben und leere Ergebnisse; Reload/Offline/Netzabbruch; Manifest/Icons/Startbildschirm/Standalone; Daten dürfen keine Geheimnisse oder fremde Profile zeigen. MISSION/BLITZ erst nach tatsächlicher UI-Anbindung funktional abnehmen. Android-Version, Browser-Version, Test-URL, geprüfte SHA, Datum und Screenshots protokollieren. Keine reine Manifestprüfung als Geräteabnahme zählen.

## Upload-Grenze

Ausdrückliche Nutzerfreigabe für eigenen Zweig und Draft-PR liegt vor. Neue Dateien und Diff werden auf Zugangsdaten, private Testdaten und unbeabsichtigte Inhalte geprüft. Replits Zweig, main und Hosting bleiben unverändert. Keine Sicherheitsfreigabe vor Pflichtnachweisen.
