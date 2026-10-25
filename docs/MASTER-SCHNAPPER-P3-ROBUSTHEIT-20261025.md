# SCHNAPPER – MASTER P3: Fehlertolerante KI-Übergaben & Beweisqualität

**Datum:** 25. Oktober 2026  
**Arbeitszweig:** `integration/schnapper-p0-mainbased-20261025`  
**Review:** [PR #55](https://github.com/jefrey030/Schnapper/pull/55) (Draft)  
**Budget:** 0 € Zusatzkosten  
**Freigabestatus:** NO-GO für Merge, Cloudflare-/Ollama-Livebetrieb und Produktion

## 1. Belegte Ausgangssituation

- `team/agent.py::lies` verarbeitet JSON aus Vorgängerdateien ohne Fehler-/Formatbehandlung. Ungültige oder unlesbare Dateien können Folgeprozess oder Gesamtbericht unkontrolliert abbrechen lassen.
- `team/agent.py::brain` greift nach `LEAD.status=OK` direkt auf `l["plan"]` und `aufgabe_id` zu. Eine beschädigte, aber formal `OK` markierte Rolle kann den nächsten Schritt abstürzen lassen. Eine unzulässige `aufgabe_id` wird zudem zur Erstellung eines Dateinamens genutzt.
- `team/agent.py::check` greift auf `l["plan"]`, `b["ki"]["text"]` und `tests["ok"]` ungeprüft zu. Fehlende Felder dürfen keine Anfrage an ein KI-Modell und keine falsche Freigabe auslösen.
- `team/agent.py::tests_ausfuehren` verarbeitet einen Test-Timeout oder fehlenden Testinterpreter bisher nicht als strukturierten Negativbefund.
- `team/local_service.py::einmal` kann bei einer beschädigten oder nicht als Objekt formatierten `team/runs/<lauf>.json`-Datei abbrechen, bevor ein verlässlicher `BLOCKIERT`-Status vorliegt.
- Letzter bereits geprüfter Ausgangs-HEAD im Review: `79cb3f6991229cec0ab665bf735d5d3ddedee4cd`, [GitHub-CI 40198769377](https://github.com/jefrey030/Schnapper/actions/runs/40198769377): 244 Python-Tests (1 übersprungen), 16/16 Cloudflare-Tests bestanden. Dieser Nachweis gilt **noch nicht** für den P3-Master.

## 2. Vier getrennte Arbeitsrollen und Abnahme

| Rolle | Auftrag | Tatsächlicher Nachweis |
| --- | --- | --- |
| LEAD | Vorbedingungen, Gefahrstellen und sichere Reihenfolge bestimmen; Kosten- und Freigaberegeln beibehalten | belegte Datei-/PR-Bestandsaufnahme |
| BRAIN | JSON-Verarbeitung und LEAD/BRAIN/CHECK-Übergaben gegen beschädigte Struktur und unsichere Dateinamen härten; Testausfälle sicher blockieren | Code-Commits auf bestehendem Branch |
| CHECK | Offline-Regressionen für korrupte/überlange JSON-Berichte, fehlende LEAD/BRAIN-Felder, kaputte Aufgaben-IDs, Test-Timeout und Pilotbericht ergänzen | GitHub Actions Python-/Cloudflare-Jobs auf finaler SHA |
| COMMAND | Testergebnisse und Commit-Nachweise festhalten; alle unerledigten Produktivblocker explizit nennen | aktualisierter Master + PR-Kommentar |

## 3. Umsetzungsvorschriften

1. **Fehlschlag geschlossen:** Ungültige JSON-Rollenberichte, fremde Formattypen und Lesefehler => keine positive KI-Vorrolle und kein kostenrelevanter Folgeaufruf.
2. Ein formal `OK` markierter LEAD- oder BRAIN-Bericht benötigt die tatsächlich verwendeten strukturierten Felder, bevor BRAIN/CHECK das Modell überhaupt aufrufen dürfen.
3. Ungültige oder pfadbildende `aufgabe_id`-Werte werden vor der Dateierzeugung blockiert.
4. Ein Testlauf darf bei Timeout, fehlendem Prozess oder fehlendem Zählbeleg niemals `tests_ok=true` werden.
5. Lokale beschädigte Gesamtberichte erhalten einen sichtbaren negativen Status (kein ungefangener JSON-Fehler).
6. Testdaten sind ausschließlich synthetisch, ohne echte Tokens oder reale KI-Modelle.
7. **Keine** Veröffentlichung, keine kostenpflichtigen APIs, kein Cloudflare-Deploy, kein Merge auf `main`, keine Reaktivierung des ausgedienten GitHub-Models-Cron.

## 4. Abnahmekriterien

- [ ] Quellenfelder und lokale Berichte werden fail-closed gelesen.
- [ ] BRAIN und CHECK ignorieren unvollständige Vorgänger, ohne Modellanfrage.
- [ ] Unsichere Aufgaben-ID kann keine Datei außerhalb `team/proposals` schreiben.
- [ ] Test-Timeout/fehlender Testprozess wird als gescheitert vermerkt.
- [ ] Beschädigter Pilotbericht kann nicht als Erfolg ausgegeben werden.
- [ ] Neue Negative/Positive Regressionen bestanden.
- [ ] Beide GitHub CI-Jobs für den **finalen HEAD** mit Laufnummer und exakten Zahlen geprüft.
- [ ] Keine produktive Freigabe oder Kostenaktivierung. **NO-GO** bleibt bestehen.

## 5. Beweisgrenzen

Ein grüner GitHub-CI-Job beweist ausschließlich die dabei ausgeführten Offline-Tests. Er beweist **nicht** vier autonome echte KI-Agenten, Ollama-Verfügbarkeit am privaten Rechner, sicher angeschlossene Preisquellen, gesicherte Staging-Zugriffe oder produktive Cloudflare-Bindings. Vier Rollen in diesem Master sind Arbeitspakete, keine selbstständig gestarteten KI-Instanzen.
