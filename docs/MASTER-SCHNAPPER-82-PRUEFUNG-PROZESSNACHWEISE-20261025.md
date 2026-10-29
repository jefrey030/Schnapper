# SCHNAPPER MASTER 82 – Große Sicherheitsprüfung und gebundene Prozessnachweise

**Datum:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Basis:** MASTER 81 / [PR #103](https://github.com/jefrey030/Schnapper/pull/103), HEAD `df30c0dd86c95982998a400cdc8f9a1fcd88b730`  
**Branch:** `fix/master82-process-manifest-binding-20261025`  
**Priorität:** P0 Nachweisintegrität, P1 Integrationsplanung  
**Modus:** Ausschließlich Offline-MOCK + öffentliches GitHub-CI, 0 € Zusatzkosten  
**Merge/Deployment/Live-Modell:** NICHT FREIGEGEBEN

## Aktueller Bestand und Integrationsrisiko

Die bisherige Sicherheitskette ist gestapelt und **noch nicht in main**:
- MASTER 76 [PR #89](https://github.com/jefrey030/Schnapper/pull/89): lokale Lock-/Crash-Sicherung.
- MASTER 77 [PR #94](https://github.com/jefrey030/Schnapper/pull/94): Rollenbelege, CHECK, Zähler.
- MASTER 78 [PR #97](https://github.com/jefrey030/Schnapper/pull/97): Prozessrollen und Manifestfehler.
- MASTER 79 [PR #101](https://github.com/jefrey030/Schnapper/pull/101): sichere Dateiöffnung für Artefakt-Hashes.
- MASTER 80 [PR #102](https://github.com/jefrey030/Schnapper/pull/102): atomare lokale Aufrufquote.
- MASTER 81 [PR #103](https://github.com/jefrey030/Schnapper/pull/103): harte Quote und begrenzte Sperrwartezeit.

Separate Entwürfe [PR #69](https://github.com/jefrey030/Schnapper/pull/69), [PR #80](https://github.com/jefrey030/Schnapper/pull/80) und [PR #90](https://github.com/jefrey030/Schnapper/pull/90) überschneiden sich in Sicherheitsnachweis- und Modellprüfungen. Ein grüner CI-Lauf auf einem Draft-HEAD beweist **keinen erfolgreichen Integrationstest auf main**. Vor jeder Merge-Entscheidung ist ein unabhängiger Vergleich der PR-Diffs und ein integrierter Endtest erforderlich.

## Bestätigtes Problem

`einmal()` erzeugte `prozesse.json` aus seiner internen Rollen-/Exitcode-Liste und prüfte `pruefe_nachweise(..., schritte)` ausschließlich gegen diese interne Liste. Das spätere SHA256-Manifest nahm die Prozessdatei jedoch erneut von der Festplatte. War diese Datei zwischen Schreiben und späterem Lesen ausgetauscht, konnte ein zur Laufzeit abweichendes Protokoll mit einem gültig berechneten Hash zusammen mit der vorher erfolgreich geprüften Liste als positiver Techniknachweis gelten.

## Tatsächlich implementierte Korrektur

1. Der Dienst serialisiert `schritte` genau einmal in UTF-8-Bytes und bildet davon einen erwarteten SHA256-Hash.
2. Derselbe Bytepuffer wird in `team/work/<lauf>/prozesse.json` geschrieben.
3. Die vorhandene sichere `_hash_sicher()`-Funktion öffnet die endgültig gespeicherte Pflichtdatei.
4. **Vor** einem positiven Ergebnis wird der Manifest-Hash dieser Prozessdatei mit dem ursprünglichen internen SHA256 verglichen. Bei Abweichung: strukturierter Status `BLOCKIERT`, `vier_echte_ki_antworten=false`, Rückgabecode 1.
5. Die zehn neuen `tests/test_master82_process_binding.py`-Testmethoden überprüfen normale MOCK-Fälle und neun verschiedene Manipulationen nach dem initialen Schreiben.

**Einschränkung:** Die Prüfung bindet nur `prozesse.json` an die intern beobachteten Rollen-/Exitcodes. Sie ist keine unabhängige kryptografische Bestätigung echter LLM-Inferenz. Lokal privilegierte Akteure, die Code, Speicher, Unterordner oder den gesamten Runner kontrollieren, liegen außerhalb des dadurch bewiesenen Sicherheitsmodells. Die übrigen Artefakt-Differenzen zwischen fachlicher Prüfung und späterem Hash erfordern weiterführende Arbeit.

## 45-Punkte-Abnahmeplan

| # | Bereich | Prüfschritt |
|---:|---|---|
| 01 | GitHub-Basis | Repository jefrey030/Schnapper prüfen |
| 02 | GitHub-Basis | MASTER-81-PR #103 und HEAD lesen |
| 03 | GitHub-Basis | Eigene Branch-Isolation erzwingen |
| 04 | GitHub-Basis | Überlappende P0-PRs #69/#80/#90 dokumentieren |
| 05 | GitHub-Basis | GitHub-CI des Vorgängers als Basis prüfen |
| 06 | Prozessdatenbindung | Originales Prozessprotokoll deterministisch serialisieren |
| 07 | Prozessdatenbindung | SHA256 der originalen Prozessbytes ermitteln |
| 08 | Prozessdatenbindung | Exakt dieselben Bytes in prozesse.json schreiben |
| 09 | Prozessdatenbindung | Manifest-Hash über sichere FD-Öffnung bilden |
| 10 | Prozessdatenbindung | Manifest-Hash mit Original-Hash vergleichen |
| 11 | Prozessdatenbindung | Jede Abweichung geschlossen blockieren |
| 12 | Prozessdatenbindung | Konsistente MOCK-Positivefälle erhalten |
| 13 | Prozessdatenbindung | Negative Exitcodes weiter blockieren |
| 14 | Prozessdatenbindung | Doppelte Rollen weiter blockieren |
| 15 | Prozessdatenbindung | Keine echten KI-Antworten behaupten |
| 16 | Manipulationsregression | Prozessrolle nachträglich austauschen |
| 17 | Manipulationsregression | Prozess-Exitcode nachträglich verändern |
| 18 | Manipulationsregression | Zusätzliche JSON-Felder ablehnen |
| 19 | Manipulationsregression | Anderes JSON-Format ohne inhaltliche Änderung erkennen |
| 20 | Manipulationsregression | Leeres JSON-Dokument ablehnen |
| 21 | Manipulationsregression | Beschädigtes JSON ablehnen |
| 22 | Manipulationsregression | Komplett leere Prozessdatei ablehnen |
| 23 | Manipulationsregression | Angehängten Zeilenumbruch erkennen |
| 24 | Manipulationsregression | Angehängten Freitext erkennen |
| 25 | Manipulationsregression | Unveränderte MOCK-Datei akzeptieren |
| 26 | Integrationskontrolle | Unveränderte STOP-/Not-Aus-Sperre erhalten |
| 27 | Integrationskontrolle | Dateideskriptor-Hash aus MASTER 79 erhalten |
| 28 | Integrationskontrolle | Quota-Limit und Lock-Timeout aus MASTER 81 erhalten |
| 29 | Integrationskontrolle | Sicherheitsgate CHECK/COMMAND erhalten |
| 30 | Integrationskontrolle | Vier Modellaufrufe nicht als echt attestieren |
| 31 | Integrationskontrolle | Bestehende Python-Regressionen wiederholen |
| 32 | Integrationskontrolle | Cloudflare-Offline-Regressionen ausführen |
| 33 | Integrationskontrolle | Finalen HEAD-SHA mit CI-Run vergleichen |
| 34 | Integrationskontrolle | Job-Logs auf Testzahl und echte Fehler prüfen |
| 35 | Integrationskontrolle | CI-SKIP ausdrücklich sichtbar lassen |
| 36 | Freigabe | Weder main noch fremde Branches ändern |
| 37 | Freigabe | Keine produktive Veröffentlichung oder Merges auslösen |
| 38 | Freigabe | Keine Ollama-Modelle/Bezahlprovider aktivieren |
| 39 | Freigabe | Keine echten Preisabrufe oder Produktionsdaten |
| 40 | Freigabe | Unabhängigen Security-Review verlangen |
| 41 | Freigabe | Merge-Reihenfolge der gestapelten PRs offen kennzeichnen |
| 42 | Freigabe | Separate parallele PRs auf inhaltliche Überschneidung prüfen |
| 43 | Freigabe | Restliche TOCTOU- und lokale Vertrauensgrenzen nennen |
| 44 | Freigabe | NO-GO bis Review und Live-Beweis dokumentieren |
| 45 | Freigabe | Kostenregel 0 EUR beibehalten |

## Exit-Gates

- **CODE-GO** ausschließlich wenn Python und Cloudflare-Offline-CI am **finalen HEAD** erfolgreich sind und die Testnamen in den Python-Logs nachweisbar sind.
- **MERGE-GO** bleibt gesperrt bis unabhängige technische Überprüfung, Konfliktmatrix und integrierter Branch-Gesamttest vorliegen.
- **LIVE-/PROD-GO** bleibt gesperrt bis echte Modellaufrufe, Nutzer-/Kostenfreigabe, Zugriffs- und Secret-Tests unabhängig nachgewiesen werden.
- Nie automatische Merges, Branch-Löschungen, Cloud-/Ollama-Aktivierung, Käufe, Änderungen an main oder produktiven Daten.

### Reproduzierbare Offline-Testaufrufe

`python -m unittest discover -s tests -v`

`cd cloudflare && node --test test/*.test.mjs`

Dieses Dokument belegt den Auftrag und Umfang. Ob der finale Commit bestanden hat, muss anhand echter GitHub-Actions-Jobs separat überprüft werden.
