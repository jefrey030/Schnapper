# SCHNAPPER – echtes lokales KI-Gehirn (kostenfrei)

Dieses Projekt hat vier getrennt aufgerufene Sprachmodell-Rollen:
LEAD (Priorisierung), BRAIN (technischer Entwurf), CHECK (Risiken/Tests)
und COMMAND (Abnahme). Ein echtes frei verfügbares Sprachmodell erstellt
neue Antworten statt fest programmierter Standard-Sätze.

Die Rollen sind separate Aufrufe desselben lokalen Modells und keine vier
unabhängigen, selbstlaufenden Computer. Der Code erstellt Entwürfe und
Prüfprotokolle, aber ändert keine App-Dateien automatisch.

## Sicher ohne bezahlte KI-Dienste

- Keinerlei Anthropic-, OpenAI- oder sonstige Cloud-KI-Aufrufe.
- Der einzige KI-Endpunkt ist fest auf http://127.0.0.1:11434 eingestellt.
- Modell: qwen2.5:1.5b-instruct. Das lokale Modell muss zuvor heruntergeladen sein.
- Der GitHub-Actions-Stundenlauf verwendet ausschließlich einen eigenen
  selbst gehosteten Runner mit dem Label schnapper. Keine GitHub-hosted
  Rechenminuten durch diesen Workflow.
- Mögliche Strom- und Internetkosten des eigenen Rechners bleiben bestehen.

## Einrichtung auf einem eigenen kompatiblen Rechner

1. Ollama von https://ollama.com/download installieren.
2. Einmalig lokal ausführen: ollama pull qwen2.5:1.5b-instruct
3. Ollama starten (bei unterstützten Systemen läuft es als lokaler Dienst).
4. Im SCHNAPPER-Verzeichnis ausführen:
   python3 -m unittest discover -s tests -v
   python3 team/runner.py
5. Danach echte Ergebnisdateien unter team/runs und team/STATUS.md kontrollieren.
6. Für automatischen Stundenbetrieb GitHub öffnen:
   Settings > Actions > Runners > New self-hosted runner.
   Einen EIGENEN Computer registrieren und zusätzlich mit dem Label schnapper
   versehen. Der GitHub-Runner und Ollama müssen eingeschaltet sein.
   Der GitHub-Workflow nutzt Minute 17 jeder Stunde; Verzögerungen sind möglich.

Ein älteres MacBook unterstützt unter Umständen aktuelle Ollama-Versionen
nicht. Dann ein kompatibles anderes Gerät verwenden; keine kostenpflichtigen
Server anmieten. Ein ausgeschalteter Rechner kann keinen lokalen KI-Job ausführen.

## Transparente Abnahme

Aufgabe S-000 erfordert:
- LEAD: exakt drei begründete Funktionen.
- BRAIN: Eingaben, Ausgaben, konkrete Schritte und Inserat-Datenschema.
- CHECK: Preisveraltung, Dubletten, Nutzungsrechte mit je einem Test.
- COMMAND: belegte Zusammenfassung und genau ein nächster Schritt.

Der Runner bewertet die Struktur und speichert alle lokalen Antworten.
Ein formaler Erfolg bedeutet nicht, dass Inhalte sachlich richtig sind,
dass eine App implementiert wurde, oder dass eine echte Schnäppchenquelle
funktioniert. Für diese Dinge sind gesonderte Tests notwendig.

Fehlen Ollama, das Modell oder der selbst gehostete GitHub-Runner, wird die
Aufgabe als blockiert angezeigt. Die Aufgabenliste wird nicht automatisch
als erledigt markiert; es erfolgt keine Veröffentlichung oder Zahlung.

Der erste GitHub-Stundenlauf scheiterte bereits vor belegten Arbeitsschritten.
Die exakte GitHub-Fehlerursache ist wegen fehlender Joblogs ungeklärt.
