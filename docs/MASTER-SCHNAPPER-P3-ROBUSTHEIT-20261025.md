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

- [x] Quellenfelder und lokale Berichte werden fail-closed gelesen.
- [x] BRAIN und CHECK ignorieren unvollständige Vorgänger, ohne Modellanfrage.
- [x] Unsichere Aufgaben-ID kann keine Datei außerhalb `team/proposals` schreiben.
- [x] Test-Timeout/fehlender Testprozess wird als gescheitert vermerkt.
- [x] Beschädigter Pilotbericht kann nicht als Erfolg ausgegeben werden.
- [x] Neue Negativregressionen und vorhandene Positivtests bestanden.
- [x] Beide GitHub CI-Jobs für den geprüften **Code-HEAD** mit Laufnummer und exakten Zahlen geprüft; Dokumentations-HEAD nach Abschluss erneut prüfen.
- [x] Keine produktive Freigabe oder Kostenaktivierung. **NO-GO** bleibt bestehen.

## 5. Beweisgrenzen

Ein grüner GitHub-CI-Job beweist ausschließlich die dabei ausgeführten Offline-Tests. Er beweist **nicht** vier autonome echte KI-Agenten, Ollama-Verfügbarkeit am privaten Rechner, sicher angeschlossene Preisquellen, gesicherte Staging-Zugriffe oder produktive Cloudflare-Bindings. Vier Rollen in diesem Master sind Arbeitspakete, keine selbstständig gestarteten KI-Instanzen.

## 6. Tatsächlich ausgeführte Arbeiten

**Ausführung nur im vorhandenen Draft-Branch.** LEAD/BRAIN/CHECK/COMMAND stehen für getrennte Arbeitsaufträge. Keine vier autonomen externen KIs wurden gestartet.

- `team/agent.py`: `lies` akzeptiert ausschließlich lesbare, bis 128 KB große JSON-Objekte. Fehlende, ungültige oder übergroße Rollenbelege werden als nicht gültig behandelt. `tests_ausfuehren` behandelt fehlende Prozesse und Zeitüberschreitungen als `ok=false, anzahl=0`.
- `team/agent.py::brain`: Ein formal `OK` markierter LEAD-Beleg braucht eine gültige Aufgaben-ID. Die ID darf nur harmlose alphanumerische Zeichen, Unterstriche und Bindestriche enthalten. Ungültige ID => `ÜBERSPRUNGEN` **vor** KI-Inferenz oder Dateischreibvorgang.
- `team/agent.py::check`: Fehlende LEAD/BRAIN-Inhalte, nicht lesbarer Vorschlagstext, fehlerhafte/fehlende Tests oder ein Geheimnisbefund verhindern die CHECK-Inferenz. Bereits vorhandene deterministische Prüfungen werden weiter protokolliert.
- `team/local_service.py`: Beschädigte, nicht als JSON-Objekt formatierte, nicht lesbare oder übergroße Pilotberichte liefern `BLOCKIERT` und Exitcode 1.
- Neue Regressionen: `tests/test_p3_corrupt_evidence.py` mit sechs unittest-Testmethoden und mehreren negativen Unterfällen, ausschließlich mit künstlichen Daten und Mock-Objekten. Vorhandene positive Offline-Tests blieben erfolgreich.

## 7. Geprüfter Nachweis

[GitHub Actions #40202246295](https://github.com/jefrey030/Schnapper/actions/runs/40202246295), Code-Commit `4b714f96cf86b1561a91c95f6ecddbf0cf0692b4`: **Python 254 Tests ausgeführt, 1 SKIP, 0 Fehler**; **Cloudflare 16/16 PASS, 0 Fehler, 0 SKIP**.

Die Zahlen belegen nur die ausgeführte Test-Suite zum genannten Commit. Ein abschließender Dokumentations-Commit verändert den Branch-HEAD und benötigt einen erneuten GitHub-CI-Abgleich.

**Restblocker:** keine unabhängige externe Sicherheitsprüfung, keine echte KI-Hostausführung, kein Cloudflare-Staging oder produktive Releasefreigabe. Der alte Legacy-Stundenworkflow auf `main` bleibt bis zur gesonderten Freigabe weiterhin unberührt. **Entscheidung: NO-GO.**
