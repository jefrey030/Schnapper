# SCHNAPPER ONE

Eigenständiges KI-Teilprojekt für **Alltagsassistent**, **Spar-Agent**, **Kaufprüfer** und **Verkaufsassistent**. Enthält ein vom SCHNAPPER-Team abgeleitetes Vier-Agenten-System: **LEAD, BRAIN, CHECK, COMMAND**.

**Stand: 23.10.2026 – technischer Prototyp, KEIN produktiver KI-Dauerbetrieb.**

## Was wirklich vorhanden ist

- Eigenes `team/` mit fünf SCHNAPPER-ONE-Aufgaben (ONE-001 bis ONE-005)
- Vier getrennte Python-Agenten mit GitHub-Models-Anbindung (ab Werk **AUS**)
- Eigenständige Offline-Tests, die ohne Modellzugriff laufen
- Unabhängige GitHub-Actions-Workflows für Tests und optionalen manuellen Pilotbetrieb
- Kein Zugriff auf bestehende SCHNAPPER-/ZENTNA-Daten
- Keine Veröffentlichung, Käufe, kostenpflichtigen APIs oder echte Abozahlungen

**Achtung:** Die erfolgreich durchgelaufenen sechs Offline-Tests verwenden für das Viererteam einen simulierten KI-Dienst. Das ist kein Nachweis, dass vier echte KI-Modelle zuverlässig arbeiten. Simulationsantworten werden im Status korrekt als **NICHT EINSATZBEREIT** gezählt.

## Installation / Test ohne kostenpflichtige Dienste

Python 3.11 oder neuer. Im Projektordner:

```sh
python -m unittest discover -s tests -v
```

Keine Installation zusätzlicher Pakete erforderlich.

## Erst nach expliziter Freigabe: Pilot mit echter KI

Der GitHub-Workflow `team-manual.yml` wird **niemals zeitgesteuert** ausgeführt. Seine Freigaben sind restriktiv: öffentliches Repository UND GitHub-Actions-Variable `SCHNAPPER_ONE_KI_ENABLED=true`. Vor der Aktivierung müssen die GitHub-Models-Abrechnung und die tatsächlichen kostenfreien Kontingente überprüft werden; Freigabe nur bei **0 € Zusatzkostenrisiko**. Ansonsten AUS lassen.

Im freigegebenen Pilot läuft pro manuell gestarteter Ausführung höchstens ein Prozess je Rolle, und das gesamte Modellbudget ist auf vier Antworten begrenzt. Der Lauf schreibt Protokolle und legt ein Artefakt ab. Ohne eindeutig dokumentierte echte Antworten und erfolgreiche Tests darf das Team nicht als einsatzbereit gelten.

## Geplante Tarife, nicht aktiviert

| Produkt | Monatlicher Planpreis |
| --- | ---: |
| SCHNAPPER Premium – Sparautopilot | 4,99 € |
| SCHNAPPER KI – Alltagsassistent | 9,99 € |
| Kombipaket – Vorschlag | 12,99 € |

Einmalig fünf kostenlose KI-Aufträge vor einem freiwillig gewählten Abo. Keine automatische Zahlung, keine unbegrenzte KI-Nutzung ohne Kostenkontrolle. Sämtliche Abo-Funktionen sind **Planung**, nicht Teil dieses Team-Prototyps.

## Integration

SCHNAPPER ONE bleibt zunächst separat; erst nach echter KI-Abnahme und Sicherheitsprüfung kann es über eine dokumentierte Schnittstelle in SCHNAPPER eingebaut werden. Die Entwicklung des SCHNAPPER-Hauptprojekts wird nicht verändert.

Weitere Details in [MIGRATION.md](MIGRATION.md) und [team/STATUS.md](team/STATUS.md).
