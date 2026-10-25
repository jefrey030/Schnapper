# SCHNAPPER – Vier-Agenten-KI-Team

Eigenständige, von ZENTNA und JERRY AL getrennte Entwicklungsumgebung für die
Schnäppchen-/Preisvergleichs-App SCHNAPPER.

## Die vier Agenten
Jeder Agent ist ein **eigener Prozess** (eigener Workflow-Schritt) mit **eigener
Anfrage an ein echtes Sprachmodell** und eigener Ergebnisdatei:

| Agent | Aufgabe | Echte Werkzeuge zusätzlich zur KI |
| --- | --- | --- |
| **LEAD** | wählt eine offene Aufgabe, schreibt Aufträge und Akzeptanzkriterien | Aufgabenrotation aus `team/tasks.json` |
| **BRAIN** | analysiert das Repo, entwickelt einen Verbesserungsvorschlag | Repo-Überblick; Vorschlag nach `team/proposals/` |
| **CHECK** | prüft BRAINs Vorschlag gegen Kriterien | führt alle Unit-Tests aus, Geheimnis-Scan; rote Tests/Funde ⇒ „abgelehnt“ |
| **COMMAND** | koordiniert, gibt frei/nicht frei, protokolliert | Stundenbericht, `team/STATUS.md` |

Bekommt ein Agent keine echte KI-Antwort, wird er als **NICHT EINSATZBEREIT**
protokolliert. Es gibt **keinen Regelmodus**, der sich als KI ausgibt.

## KI-Laufzeit: Legacy-Dienst stillgelegt, lokale Option vorbereiten

**GitHub Models wurde am 30.07.2026 vollständig eingestellt.** Der frühere
Katalog und die Inferenz-API unter `models.github.ai` funktionieren nicht mehr.
Die alten Aussagen über kostenlose GitHub-Models-Kontingente und vier
automatisch arbeitende KI-Agenten gelten **nicht** mehr. Der Adapter in
`team/ki.py` verweigert Aufrufe ausdrücklich (Fail-Closed).

Die bereits vorhandene, freiwillige Alternative ist `team/local_ollama.py`:
Nur auf einem **eigenen kompatiblen Rechner** mit einem **bereits lokal installierten
Ollama-Modell** kann `SCHNAPPER_KI_BACKEND=ollama` gesetzt werden.
Sie greift fest auf `127.0.0.1:11434` zu, lehnt Weiterleitungen und
Cloud-Modellnamen ab und aktiviert weder einen fremden Anbieter noch einen
automatischen Download. Die Existenz dieses Adapters **beweist keinen laufenden
Modellhost** und keine vier echten KI-Antworten.

Eine unverbindliche, read-only Vorabdiagnose ist:
```
python3 team/diagnose_local.py
```
Der Diagnoseaufruf prüft vorhandene lokale Voraussetzungen. Er startet
keinen KI-Dienst, lädt keine Modelle herunter und aktiviert keinen Dauerbetrieb.

## Stundenbetrieb: vorerst aus Sicherheitsgründen aus

Der frühere GitHub-Actions-Stundenplan ist in
`.github/workflows/schnapper-hourly.yml` in diesem Entwurf entfernt.
Auch der manuelle Workflow-Aufruf wird am Job-Gate verweigert; die
Berechtigung ist auf `contents: read` reduziert. GitHub-hosted Runner
erreichen kein beliebiges lokales `127.0.0.1`-Ollama des Nutzers.

Die Rollen LEAD, BRAIN, CHECK und COMMAND bleiben als getrennte
Codeprozesse und Aufgaben definiert. **Es wird dadurch keine externe KI
automatisch gestartet.** Ein grüner Unit-Test oder Workflow ohne echte
Modellantworten ist kein Nachweis für funktionierenden Vier-KI-Betrieb.

## Kosten, Datenschutz und Freigabe

- **Budgetgrenze: 0 € zusätzliche Kosten.** Keine Bezahl-API,
  Budgeterhöhung, automatische Modellinstallation oder Cloud-Fallback.
- Keine Änderung der Repository-Sichtbarkeit und keine automatische
  Aktivierung von Tests, KI, eBay oder neuen Datenquellen.
- Kein Merge, Deployment oder Produktionsbetrieb ohne unabhängige
  Abnahme und ausdrückliche Freigabe.
- Für alle vier KI-Rollen sind echte separate Modellantworten, Testbefunde
  und Sicherheitsprüfung zu belegen. Simulierte Antworten heißen
  ausdrücklich Test oder Mock.

## Status der Stilllegung

Dieser Text dokumentiert den **Stand im Integrations-Draft-PR #55**. Vor einem
geprüften Merge enthält `main` weiterhin den alten Stundenworkflow.
Der zuletzt geprüfte Stundenlauf [40143662656](https://github.com/jefrey030/Schnapper/actions/runs/40143662656)
hatte **0 echte KI-Aufrufe**. Der sichere Offline-Weg und die nachweisbare
Stilllegung haben Priorität vor einer neuen autonomen KI-Konfiguration.

## Dateien
- `team/agent.py` – die vier Agenten + Stundenbericht
- `team/ki.py` – gesperrter Legacy-GitHub-Models-Adapter; kein produktiver Netzaufruf
- `team/local_ollama.py` – ausschließlich optionales Modell auf eigenem Rechner
- `team/diagnose_local.py` – read-only Systemprüfung ohne KI-Aufruf
- `team/runner.py` – Aufgaben laden und rotieren
- `team/tasks.json` – Aufgabenbestand
- `team/runs/` – Stundenberichte (`.md` + Rohdaten `.json`), `team/proposals/` – BRAIN-Vorschläge
- `tests/` – Unit-Tests (u. a. End-to-End mit lokalem Nachahmer von GitHub Models)

Für echte Preisvergleiche (eBay usw.) sind eigene, erlaubte Datenquellen nötig – noch nicht angebunden.

## App-Kern (`app/schnapper`)
Die eigentliche Schnäppchen-Logik, unabhängig vom KI-Team. Nur Python-Standardbibliothek, kein Internetzugriff, keine Kosten.

- **Angebote prüfen:** Preis > 0, nur EUR, nur `https://`, gültiger Zustand, keine Zukunftszeitpunkte. Preise in deutschem und englischem Format (`1.299,99 €`).
- **Warnungen:** veralteter Preis (älter als 24 Std.), Betrugsverdacht (Neuware ≥ 80 % unter Referenzpreis), fehlender Referenzpreis (dann wird keine Ersparnis behauptet).
- **Dubletten:** gleiche URL ohne Tracking-Parameter oder gleiche Quelle + fast gleicher Titel + Preis ±2 %. Der neueste Eintrag bleibt. Gleiches Produkt bei anderer Quelle bleibt als Vergleich erhalten.
- **Suche/Filter:** Suchwörter (Umlaute egal: „Kopfhoerer“ findet „Kopfhörer“), Höchstpreis inkl. Versand, Mindestrabatt, Zustand, Quelle, Kategorie; Sortierung nach Rabatt, Preis oder neueste.
- **Import:** `.json` oder `.csv` (Trennzeichen `;` oder `,`). Fehlerhafte Zeilen werden gemeldet, der Rest wird verarbeitet.

```
PYTHONPATH=app python -m schnapper app/beispiele/angebote.csv --suche kopfhoerer --max-preis 60
```

`app/beispiele/angebote.csv` enthält **ausgedachte Beispieldaten** (`.example`-Adressen), keine echten Angebote. Echte Angebote brauchen eine Datenquelle mit geklärten Nutzungsrechten (z. B. offizieller Partner-Feed). Gescrapt wird nichts.

## Web-Oberfläche
```
PYTHONPATH=app python -m schnapper.web app/beispiele/angebote.csv
```
Dann im Browser `http://127.0.0.1:8765` öffnen. Suche, Filter, Sortierung und „Eigene Liste“ (CSV/JSON hochladen) funktionieren am Handy wie am PC. Hochgeladene Listen bleiben nur im Arbeitsspeicher (Ausnahme: Preisverlauf mit `--verlauf`, siehe unten).
Mit `--host 0.0.0.0` ist die Seite im eigenen WLAN erreichbar (ohne Passwort, daher nur im Heimnetz).

### Merkliste und Preisalarm in der Web-Oberfläche
- **☆ Merken** auf jeder Karte: Das Angebot landet in der **Merkliste**. Dort steht, ob der Preis in der aktuell geladenen Liste seit dem Merken **günstiger, teurer oder gleich** ist – oder ob das Angebot verschwunden ist.
- **⚡ Preisalarm für diese Suche:** Suchbegriff plus „Bis €“ und/oder „Ab % billiger“ eingeben, Knopf drücken. Unter **Preisalarme** steht bei jedem Öffnen, welche Wünsche gerade erfüllt sind (günstigstes Angebot zuerst). Die Zahl am Reiter zeigt, wie viele Alarme anschlagen.
- Verdächtige (Betrugsverdacht) und veraltete Angebote lösen **keinen** Alarm aus.
- Merkliste und Alarme werden nur **im Browser dieses Geräts** gespeichert (max. 200 gemerkte Angebote, 50 Alarme). Kein Konto, kein Server-Speicher.

## Preisverlauf (`app/schnapper/verlauf.py`)
Mit `--verlauf DATEI` hält SCHNAPPER jeden gesehenen Preis fest (bereinigte URL, Erfassungszeit, Gesamtpreis inkl. Versand – keine Personendaten, nur lokal):
```
PYTHONPATH=app python -m schnapper.web meine-liste.csv --verlauf verlauf.json
PYTHONPATH=app python -m schnapper meine-liste.csv --verlauf verlauf.json
```
Dann zeigt jede Karte:
- **Tiefstpreis seit N Tagen**, wenn der aktuelle Preis der niedrigste der letzten 30 Tage ist,
- **↓/↑ vorher X €** bei einer Preisänderung seit der letzten Beobachtung,
- die **Preisspanne** der letzten 30 Tage,
- **„Statt“-Preis fragwürdig**, wenn der angegebene Referenzpreis mehr als 20 % über allem liegt, was in mindestens 7 Tagen und 3 Beobachtungen gesehen wurde (geschönte Rabatte).

Wer dieselbe Liste mehrmals lädt, erzeugt keine doppelten Einträge. Eine beschädigte Verlaufsdatei wird nicht überschrieben; SCHNAPPER startet dann mit Fehlermeldung.

## Preisalarm auf der Kommandozeile (`app/schnapper/alarm.py`)
Wunschliste als JSON (Beispiel: `app/beispiele/wuensche.json`):
```json
{"wuensche": [{"name": "Kopfhörer bis 60 €", "suche": "kopfhoerer", "max_preis": "60", "zustaende": ["gebraucht", "wie_neu"]}]}
```
```
PYTHONPATH=app python -m schnapper.alarm app/beispiele/angebote.csv app/beispiele/wuensche.json
```
Jeder Wunsch braucht einen Suchbegriff und mindestens Höchstpreis (inkl. Versand) oder Mindestrabatt. Optionen: `--mit-veraltet` (auch Preise älter als 24 Std.), `--json`.
Rückgabewert für Automatisierung: `0` = mindestens ein Alarm, `3` = kein Alarm, `2` = fehlerhafte Wünsche, `1` = Datei nicht lesbar.

## Quellen-Register (`app/schnapper/quellen.py`)
Angezeigt werden nur Angebote aus freigegebenen Quellen (Plan S-002): `mock` und `eigene` sind erlaubt, `ebay` bleibt gesperrt bis zur Genehmigung, `kleinanzeigen` ist ausgeschlossen und lässt sich nicht freischalten. Zusätzliche Quellen werden in einer `quellen.json` neben der Datei freigegeben, jeweils mit Hinweis zum Nutzungsrecht.


## Reiner Offline-Mock-Adapter (S-005/T3)

Die eigene Testquelle `MockAdapter` benötigt **keinen Account, keine
KI-API, keine Netzwerkverbindung und keine zusätzlichen Pakete**.
Sie liefert genau zwei deutlich als **TEST** markierte Beispieldatensätze
mit nicht aufrufbaren `.invalid`-Links. Einer der beiden Preise ist bewusst
älter als 24 Stunden und wird als **veraltet** markiert. Das sind keine
echten Schnäppchen.

```sh
PYTHONPATH=app python -c "from schnapper.adapter import MockAdapter, finde; print([(t.angebot.titel, str(t.angebot.gesamtpreis), t.warnungen) for t in finde(MockAdapter()).treffer])"
python -m unittest discover -s tests -v
```

Die Quelle `mock` muss im Quellen-Register freigegeben sein. Vom
MockAdapter eingeschleuste fremde Quellen werden abgewehrt. Die Tests
`tests/test_mock_adapter.py` prüfen unter anderem Netzwerkfreiheit,
gesperrte Quellen, veraltete Preise und fehlerhafte Testdaten. Diese
Implementierung schließt **nur** den Offline-Testblocker S-005/T3;
Liveangebote/eBay-Zugang bleiben bewusst gesperrt, bis Nutzungsrechte
und Kosten überprüfbar freigegeben sind.

## Weitere Dokumente
- `docs/SCHNAPPER-MASTERPLAN.md` – alle offenen Punkte mit Status, Nachweis und offenen Entscheidungen
- `docs/EIGENE-ANGEBOTE.md` – echte, selbst gefundene Angebote eintragen und laden (Vorlage: `app/vorlagen/meine-angebote.csv`)
- `docs/HANDY-START.md` – SCHNAPPER am Android-Handy mit Termux starten und auf den Startbildschirm legen
- `docs/OPEN-PRICES.md` – echte Ladenpreise zu einem Barcode (Open Prices, ODbL); aus, bis `SCHNAPPER_OPENPRICES_FREIGABE=ja`


## Fertigstellungsabnahme: Offline-MVP (25.10.2026)

Der [große Fertigstellungs-Master](docs/MASTER-SCHNAPPER-FERTIGSTELLUNG-20261025.md)
trennt die **bereits nutzbare Offline-App** von unerfüllten Live-/Release-Voraussetzungen.

- Neu: Die Kommandozeile prüft Preis-/Rabatt-/Zustandsfilter **vor** Datei-/Verlaufzugriff,
  beendet fehlerhafte Eingaben mit Exitcode `2` und erklärt fehlende Dateien kontrolliert
  mit Exitcode `1` statt eines Python-Tracebacks.
- Neu: Das CLI-Schreiben des Preisverlaufs nutzt `Verlauf.importiere` und meldet
  einen Speicherfehler, statt eine nicht gespeicherte Änderung als Erfolg auszugeben.
- Die neue `tests/test_fertigstellung_mvp.py` prüft mit eigenen Testdaten sowohl CLI-Import
  und Preisvergleich als auch echte lokale HTTP-Anfragen für Websuche, Datei-Upload,
  Blockade unfreigegebener Quellen und gesperrte Barcode-Netzwerkabfragen.
- [CI-Nachweis zum ersten Code-Stand](https://github.com/jefrey030/Schnapper/actions/runs/40216433994):
  292 Python-Tests (1 übersprungen, 0 Fehler), 16/16 Cloudflare-Tests (0 Fehler).
  Diese Tests verwenden keine fremden Preis-APIs oder live laufende KI-Agenten.

**Nicht fertig:** echte automatische Angebote aus freigegebenen Quellen, tatsächliche
Android-Geräteabnahme, unabhängige Sicherheitsprüfung, geprüfte Live-KI und öffentliche
Veröffentlichung. Ohne Freigabe bleibt der Integrations-Draft ungemergt.
