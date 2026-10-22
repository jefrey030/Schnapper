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

## KI-Laufzeit: 0 € – GitHub Models
- Anbieter: **GitHub Models** (`models.github.ai`), aufgerufen mit dem automatischen
  `GITHUB_TOKEN` des Actions-Laufs (`permissions: models: read`). Kein API-Schlüssel nötig.
- Bevorzugt **Open-Weight-Modelle** (Llama, Mistral, Phi). Fest wählbar über die
  Repo-Variable `SCHNAPPER_MODELL`.
- Für persönliche Konten ratenbegrenzt kostenlos. Ohne ausdrücklich eingeschaltete
  bezahlte Nutzung wird nach Erreichen des Kontingents **blockiert, nicht abgerechnet**.
- Kostenbremsen im Code: nur Host `models.github.ai` erlaubt, max. 6 KI-Aufrufe pro Lauf
  (normal: 4), kurze Antworten. Anthropic/OpenAI-Bezahl-APIs sind ausgeschlossen (Test prüft das).

## Stundenbetrieb
`.github/workflows/schnapper-hourly.yml` läuft stündlich um :17 (UTC) auf GitHubs Servern –
ohne Tablet und ohne offene Claude-Sitzung. Ein Lauf = ein Job (~1–2 Minuten), Zeitlimit 10 Min.
**Not-Aus:** Repo-Variable `SCHNAPPER_PAUSE` = `true`.

## Kostenschutz im Code
Beide Workflows laufen **nur, wenn das Repository öffentlich ist** (dort sind GitHub-Standard-Runner
kostenlos). Solange es privat ist, werden die Jobs übersprungen und verbrauchen **keine Minuten** –
auch dann nicht, wenn im Konto ein Budget freigeschaltet wird. Für den Stundenplan zusätzlich die
Variable `SCHNAPPER_OEFFENTLICH` = `true` setzen, erst **nachdem** das Repo öffentlich ist.

## Kosten – was du in den GitHub-Einstellungen sicherstellen musst
1. **Actions:** Bei privaten Repos zählen die Minuten gegen die 2.000 Freiminuten/Monat des
   Kontos (alle Repos zusammen). Öffentliche Repos sind für Standard-Runner kostenlos.
   Budget für Actions auf **0 €** lassen bzw. „Nutzung bei Budgetgrenze stoppen“.
2. **GitHub Models:** bezahlte Nutzung **nicht** einschalten.

## Aktueller Stand (21.10.2026)
**NICHT EINSATZBEREIT.** Alle bisherigen Actions-Läufe wurden von GitHub **gar nicht gestartet**:
> The job was not started because recent account payments have failed or your spending limit needs to be increased.

Das ist eine Sperre auf Kontoebene (Freiminuten für private Repos aufgebraucht und/oder
Zahlungsproblem), kein Code-Fehler. Kostenfreie Auswege: Repository **öffentlich** machen
oder auf das neue Monatskontingent warten. Details: `team/STATUS.md`.

## Dateien
- `team/agent.py` – die vier Agenten + Stundenbericht
- `team/ki.py` – Zugang zu GitHub Models mit Kostenbremsen
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
Am Handy (Termux) geht es mit einem Befehl: `bash start-schnapper.sh` (siehe `docs/HANDY-START.md`).
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
