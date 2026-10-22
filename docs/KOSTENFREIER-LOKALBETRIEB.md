# SCHNAPPER – 4 echte KI-Agenten lokal, ohne Bezahl-API

**Status: Startweg implementiert, aber noch kein echter Lauf auf einem dauerhaft
eingeschalteten Rechner bestätigt.** GitHub Actions für das private Repository
bleiben aus Kostenschutzgründen deaktiviert. Das Repository wird **nicht**
öffentlich gemacht.

## Was wirklich passiert

- `LEAD`, `BRAIN`, `CHECK`, `COMMAND` sind vier aufeinanderfolgende
  Python-Prozesse, mit jeweils einer eigenen Anfrage an ein **lokal**
  installiertes Ollama-Sprachmodell.
- Ergebnisse landen in `team/work/` (lokal, ignoriert von Git),
  Stundenberichte unter `team/runs/` und der aktuelle Status in
  `team/STATUS.md`.
- CHECK führt zusätzlich echte Python-Unit-Tests und einen Geheimnis-Scan aus.
- Ohne vier echte Antworten und erfolgreiche Tests wird der Pilot als
  **BLOCKIERT** gemeldet. Simulations-Tests belegen keine echte KI-Inferenz.
- Es werden **keine** Cloud-LLMs, bezahlten KI-APIs, Hosting- oder
  Abonnementdienste aktiviert. Ollama spricht ausschließlich den
  bereits vorhandenen lokalen Dienst unter `127.0.0.1:11434` an.
- **Grenze:** Die KI gibt Vorschläge ab und prüft. Änderungen/Deployments
  werden niemals autonom freigegeben, sondern bleiben unter menschlicher Kontrolle.

## Voraussetzungen

Ein privater, dauerhaft eingeschalteter eigener Computer, Python 3.11+,
Git und ein lokal installiertes Ollama. Installation über
[ollama.com/download](https://ollama.com/download) und Python über
[python.org](https://www.python.org/downloads/). Benötigte Software ist
kostenfrei nutzbar; **Strom und Internet** sind davon nicht umfasst.
Für ältere Rechner zunächst ein kleines Modell wählen.

**Achtung für das MacBook Pro Mid 2012:** Das aktuelle Ollama für macOS
benötigt macOS 14 (Sonoma) oder höher. Apple unterstützt Sonoma für diesen
Mac nicht regulär. Auf älterem macOS funktioniert die aktuelle Ollama-App
nicht einfach per Installation. Ein bereits vorhandener Linux-PC oder
eine bewusst vorbereitete Linux-Installation wäre eine Alternative,
aber dafür keinesfalls die vorhandene macOS-Installation überschreiben.
Vor jeder Änderung des Betriebssystems Daten sichern.
Ollama auf Intel-Macs kann zudem nur die CPU nutzen.

Quelle: https://github.com/ollama/ollama/blob/main/docs/macos.mdx

**Keine Cloud-Modelle:** Selbst wenn Ollama auf `localhost` läuft, dürfen
Modelle mit dem Suffix `:cloud` nicht verwendet werden. Der Adapter
blockiert sie. Nur bereits installierte lokale Modelle sind erlaubt.

## Schritt 1: Auf dem eigenen Rechner

```sh
git clone https://github.com/jefrey030/Schnapper.git
cd Schnapper
git switch feature/local-free-ollama-agents-20261021
ollama pull qwen2.5:1.5b
ollama list
```

Ollama muss laufen (Desktop-App öffnen oder `ollama serve` in einem
separaten Terminal). GitHub kann für das private Repository bei
`git clone` eine einmalige Anmeldung verlangen; keine Tokens in den Chat
kopieren.

## Schritt 2: Echter Probe-Stundenlauf (ohne Automation)

**Windows PowerShell:**

```powershell
$env:SCHNAPPER_OLLAMA_MODELL="qwen2.5:1.5b"
py -3 team/local_service.py --once
```

**Linux/macOS:**

```sh
export SCHNAPPER_OLLAMA_MODELL=qwen2.5:1.5b
python3 team/local_service.py --once
```

Nur `"status": "TECHNISCHER PILOT ERFOLGREICH"` mit
`"vier_echte_ki_antworten": true`, `"tests_bestanden": true`
und `"prozesse_ok": true` bestätigt einen gelungenen technischen Probelauf.
Zusätzlich werden echte Rollenprotokolle, Modellname, lokale Laufzeit,
vier verschiedene Antwort-IDs und vier Modellaufrufe geprüft. Das Ergebnis
ist **keine** Freigabe, automatische Reparaturen oder Deployments auszuführen.
Eine SHA-256-Belegliste steht unter `team/work/<lauf>/nachweise.json`.

Der ausführliche Bericht steht in `team/runs/<lauf>.json` sowie
`team/runs/<lauf>.md`, die Rohlogs in `team/work/<lauf>/prozesse.json`.
Keine Bestätigung ohne echte lokale Modellantworten.

## Schritt 3: Stundenrhythmus erst nach bestandenem Pilot

Windows PowerShell:

```powershell
$env:SCHNAPPER_OLLAMA_MODELL="qwen2.5:1.5b"
py -3 team/local_service.py --loop
```

Linux/macOS:

```sh
export SCHNAPPER_OLLAMA_MODELL=qwen2.5:1.5b
python3 team/local_service.py --loop
```

Der Loop startet einmal sofort und danach zu jeder vollen UTC-Stunde.
Er läuft **nur solange dieses Terminal, der PC und Ollama laufen**.
Keine verdeckten Hintergrundprozesse, keine Cloud-Server. Zum Stoppen
Strg+C. Bildschirm darf aus sein; der Rechner darf nicht schlafen.

Zum Einschalten nach einem Neustart muss der Loop erneut gestartet
werden oder ein **lokaler** Windows-Aufgabenplaner/systemd-Dienst
manuell eingerichtet werden.

## Diagnose

```sh
python -m unittest discover -s tests -v
```

- **Ollama nicht erreichbar**: Lokale Ollama-App/Server starten.
- **Modell nicht installiert**: `ollama list` prüfen, exakt das Modell
  aus `SCHNAPPER_OLLAMA_MODELL` per `ollama pull` installieren.
- **Job gesperrt**: `team/work/local_runner.lock` nur nach Prüfung
  entfernen, dass keine Instanz mehr läuft.
- **4 KI-Antworten, rote Tests**: Kein erfolgreicher Pilot, Fehler zuerst
  anhand des echten Testprotokolls beheben.
- **Github Actions blockiert**: Das berührt den lokalen Betrieb nicht.

Diese Entwicklungsversion bitte nicht als fertig oder produktiv
bezeichnen, bevor ein echter Pilotlauf mit einem lokal installierten
Modell dokumentiert wurde.
