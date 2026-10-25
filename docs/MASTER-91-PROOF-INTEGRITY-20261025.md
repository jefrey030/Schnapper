# MASTER 91 – SCHNAPPER: unabhängige Nachweisprüfung

**Datum:** 25. Oktober 2026  
**Basis:** MASTER 90 / PR #72 / Commit `1a28375f63bf4806fe479e72b514836623bdd969`  
**Zweig:** `chatgpt/master91-proof-integrity-20261025`  
**Umfang:** nur lokaler Pilotnachweis und Unit-Tests  
**Budget:** 0 € neue Kosten  
**Betriebsentscheidung:** NO-GO bis unabhängiger Review und reale lokale Betriebsabnahme

## 1. Auftrag

Der lokale SCHNAPPER-Dienst darf keinen Vier-KI-Erfolg anzeigen, wenn:
- eine oder mehrere Rollen-Dateien fehlen oder ungültig sind,
- der finale Stundenbericht etwas anderes als die vier Einzeldateien enthält,
- einzelne Rollen-Dateien vertauscht oder durch Symbolic Links ersetzt wurden,
- der auf Platte vorhandene Zähler nicht exakt vier erfolgreiche lokale Versuche belegt,
- die Berichtdatei defektes JSON enthält.

Es werden keine echten Modelle gestartet; die Tests nutzen ausschließlich nachgebildete Prozesse. Keinen Merge/Release aus dieser Runde ableiten.

## 2. Zwanzig Arbeitspakete

| Nr. | Aufgabe | Stand |
| --- | --- | --- |
| 01 | Master-90-Branch und PR #72 lesen | ERLEDIGT |
| 02 | GitHub CI-Stand des Basiscommits prüfen | ERLEDIGT: Run #40198104147 grün |
| 03 | Security- und Produktionsfreigaben trennen | ERLEDIGT: PR #72 bleibt Draft/NO-GO |
| 04 | Lokale Pilot-Beweisfunktion analysieren | ERLEDIGT |
| 05 | Lücke Gesamtbericht versus Einzeldateien erkennen | ERLEDIGT |
| 06 | Speicherdateien nicht nur auf Existenz prüfen | CODE UMGESETZT |
| 07 | JSON-Dateien auf korrekten Rollennamen prüfen | CODE UMGESETZT |
| 08 | Inhalte mit Gesamtbericht vergleichen | CODE UMGESETZT |
| 09 | Datei-Symlinks abweisen | CODE UMGESETZT |
| 10 | Ungültige/fehlende Rollen-JSON-Daten abweisen | CODE UMGESETZT |
| 11 | Fehlende oder abweichende Aufrufzähler abweisen | CODE UMGESETZT |
| 12 | Ungültige Stundenbericht-JSON-Datei fail-closed behandeln | CODE UMGESETZT |
| 13 | Bestehenden positiven reinen Mocktest an neue Beweise anpassen | CODE UMGESETZT |
| 14 | Negativtest gegen widersprüchliche Rollen-Datei | CODE UMGESETZT |
| 15 | Negativtest gegen ungültigen/fehlenden Zähler | CODE UMGESETZT |
| 16 | Negativtest gegen beschädigte Rollen-JSON-Datei | CODE UMGESETZT |
| 17 | Negativtest gegen beschädigten finalen Bericht | CODE UMGESETZT |
| 18 | Gesamte Python-Unit-CI reproduzierbar prüfen | AUSSTEHEND vor CI-Lauf |
| 19 | Cloudflare-Offline-CI auf HEAD prüfen | AUSSTEHEND vor CI-Lauf |
| 20 | Unabhängiger Review, Live-Ollama, Kosten- und Produktionsfreigabe | BLOCKED / NO-GO |

## 3. Sicherheitsabgrenzung

Der Abgleich ist ein **Konsistenztest lokaler Prüfartefakte**, keine kryptografische Attestierung, kein Host- oder Modellnachweis gegen einen absichtlichen Angreifer mit Schreibrechten auf alle Dateien. Echte lokale Modellantworten, Signaturen, vertrauenswürdige Laufzeitumgebung und unabhängige Freigabe fehlen weiterhin. Synthetische Testantworten sind ausdrücklich **Mocks**.

## 4. Abnahme

- `python -m unittest discover -s tests -v`: aktuelle Anzahl, Pass, Fail, Skip, Exitcode auf aktuellem Commit.
- Cloudflare `node --test test/*.test.mjs`: PASS/FAIL getrennt.
- Staging-/Cloudflare-Live-Test, echte Ollama-Responses und Main-Merge: **nicht in diesem Auftrag**.
- Keine Produktionsdaten, keine Secrets, keine neue Budgetfreischaltung und keine Veränderungen an PR #72.

## 5. Nächste Schritte

Nach erfolgreich bestätigten Tests Code-Diff unabhängig prüfen; vor eventuellem Merge Basis-/Zielstand und Security-Reviews erneut abgleichen. Bei Fehler: ausschließlich die eigene Prüfbranch-Datei korrigieren und neuen CI-Lauf mit exakter SHA dokumentieren.