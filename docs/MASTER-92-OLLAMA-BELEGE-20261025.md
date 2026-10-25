# MASTER 92 – SCHNAPPER: echte Ollama-Abschlussmetadaten statt bloßer UUID

**Datum:** 25.10.2026 · **Projekt:** SCHNAPPER, isolierter lokaler Ollama-Pilot  
**Basis:** Master 91 / PR #80 @ `6aa84accb9210ddf7bc4ab9553c8a06c9b8776f2`  
**Branch:** `chatgpt/master92-ollama-proof-20261025`  
**Budget:** 0 € neue Kosten · **Betrieb:** NO-GO · **Geltung:** nur Entwicklungsbranch, kein Merge/Deploy

## 1. Mission

Bisher erzeugte `team/local_ollama.py` auf jede nichtleere simulierte Chatantwort eine selbst erzeugte `lokal-UUID` und kennzeichnete sie in nachgelagerten Prüfungen als Antwort-ID. Eine solche ID ist **kein unabhängiger Nachweis des tatsächlichen Ollama-Modelllaufs**. Abschlussmetadaten (Modellname, Rolle, `done`, `done_reason`, Zeitstempel, Tokenzählung) wurden nicht validiert.

**Ziel:** fail-closed-Abnahme echter Ollama-JSON-Strukturen, bewusste Trennung lokaler Kennung von Ollama-API-Metadaten und Negativtests gegen unvollständige/gefälschte Formatfelder. Auch diese Daten sind **keine kryptografische Modellattestierung**; ein manipulierter lokaler Host könnte sie nachbilden.

**API-Quelle:** offizielle Ollama-Dokumentation `https://docs.ollama.com/api/chat`, am 25.10.2026 geprüft. Keine echten API-Anfragen durch diesen Master.

## 2. Ausgefüllter Arbeitsmaster (24 Pakete)

| ID | Priorität | Aufgabe | Status |
| --- | --- | --- | --- |
| M92-01 | P0 | Bisheriges Master 90/91 und PR #72/#80 prüfen | DURCHGEFÜHRT |
| M92-02 | P0 | Exakten Git-Quellstand feststellen | DURCHGEFÜHRT: Basis-SHA oben |
| M92-03 | P0 | Reale CI zur Basis prüfen | DURCHGEFÜHRT: 40199158620 SUCCESS |
| M92-04 | P0 | Ollama-Antwortschema gegen offizielle Dokumentation prüfen | DURCHGEFÜHRT |
| M92-05 | P0 | Eigenen Folgebranch erstellen | DURCHGEFÜHRT |
| M92-06 | P0 | Nicht-Objekt-Antworten verweigern | CODE |
| M92-07 | P0 | Exakten Modellnamen aus `/api/chat` vergleichen | CODE |
| M92-08 | P0 | `done is True` verlangen | CODE |
| M92-09 | P0 | `done_reason == stop` verlangen | CODE |
| M92-10 | P0 | `message.role == assistant` verlangen | CODE |
| M92-11 | P0 | Nichtleeren Antworttext verlangen | CODE |
| M92-12 | P0 | Zeitzonenbewussten ISO-Zeitstempel prüfen | CODE |
| M92-13 | P0 | Tokenzahlen als echte Integer mit gültigem Bereich prüfen | CODE |
| M92-14 | P0 | Fehlerhafte Modellkatalogeinträge ablehnen statt Crash | CODE |
| M92-15 | P0 | Lokale UUID ausdrücklich als selbst erzeugte Kennung markieren | CODE |
| M92-16 | P0 | Abschlussdaten ohne Rohtext als `ollama_beleg` speichern | CODE |
| M92-17 | P0 | Lokalen Vier-Rollen-Pilot nur mit solchen Belegen akzeptieren | CODE |
| M92-18 | P0 | Alte positive Mock-Fixtures auf Ollama-Antwortstruktur anpassen | CODE |
| M92-19 | P0 | Negativfälle für abgebrochene/andere/falsch formatierte Antworten | CODE |
| M92-20 | P0 | Negativfälle gegen fehlende oder manipulierte lokale Abschlussbelege | CODE |
| M92-21 | P0 | GitHub Python/Cloudflare CI für genau den finalen Commit | AUSSTEHEND |
| M92-22 | P0 | Unabhängiger Sicherheitsreview | AUSSTEHEND |
| M92-23 | P1 | Echter lokaler Ollama-Pilot mit vier überprüfbaren Antworten | NICHT GESTARTET |
| M92-24 | P0 | Merge-, Cloud-/Kosten- und Produktionsfreigabe | NO-GO |

## 3. Umsetzung

- `team/local_ollama.py`: `_validiere_chat_antwort` erzwingt einen korrekten nicht-streamenden, vollständig beendeten Ollama-Abschluss des angeforderten Modells. `/api/tags` ignoriert ungültige Namen statt mit TypeError abzubrechen.
- `tests/test_local_ollama.py`: Positive, rein synthetische Ollama-Antwortstruktur; Negativfälle für fehlende Metadaten, falsche Modelle, Nicht-Assistant-Rollen, leere Antworten, ungültige Tokenfelder, defekte Katalogeinträge.
- `team/local_service.py`: Einzelrollen-Nachweise müssen lokale Kennung als solche ausweisen und zum angeforderten Modell passende Abschlussdaten besitzen.
- `tests/test_local_service.py`: Simulierter positiver Pilot erhält die erwarteten Felder; bewusst gefälschte oder fehlende Metadaten müssen fehlschlagen.

## 4. Wichtige Grenzen

- Eine `lokal-...` UUID wird vom Client erzeugt; es ist keine kryptografische Quittung und keine überprüfbare externe Job-ID.
- Die Felder `ollama_beleg` sind lokal beobachtete JSON-Felder, **keine Serverunterschrift** und kein Beweis gegen einen kompromittierten localhost-Prozess.
- Die Protokolle enthalten keine Beweise, dass vier autonome Agenten dauerhaft arbeiten; GitHub Unit-Tests verwenden ausschließlich Simulationen.
- Kein realer Ollama-Aufruf, kein Modell-Download, keine Provider-Abrechnung, keine Zahlungsfunktion, keine Änderungen an `main`, Cloudflare, D1 oder Supabase.

## 5. Freigabegates

1. Python Unit-Tests mit tatsächlichem GitHub-Actions-Lauf/Commit-SHA, 0 FAIL; SKIP einzeln nennen.
2. Cloudflare Offline 13/13 oder aktualisierte Testzahl mit 0 FAIL.
3. Unabhängiger Review auf gestapelter Branchkette Master 90 → 91 → 92.
4. Physischer lokaler Host, tatsächliche Modellantworten, Not-Aus, Kosten- und Host-Sicherheitsabnahme **separat**.
5. PR bleibt `draft`; kein Merge/Produktionsbetrieb ohne ausdrückliche Freigabe.
