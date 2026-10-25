# SCHNAPPER MASTER 77 – Integrität der lokalen Vier-KI-Pilotnachweise

**Stand:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Basis:** Master 76 / [PR #89](https://github.com/jefrey030/Schnapper/pull/89), verifizierter Ausgangs-HEAD `cc8c83fbe09451ae4da5da1604ccd1c5100e4226`  
**Branch:** `fix/master77-local-proof-gates-20261025`  
**Priorität:** P0 Sicherheitsgrenzen, P1 Prüfintegrität  
**Budget:** 0 € – ausschließlich CI-Standardrunner im öffentlichen Repository und Offline-MOCK-Tests  
**Freigabe:** Draft / NO-GO für Merge, Deployment, selbstständige KI-Aktivierung und Produktionsdaten

## Auftrag / Prüfliste (28 Punkte)

| # | Ziel | Abnahmebedingung |
|---|---|---|
| 01 | Richtiges Repo identifizieren | GitHub-Verbindung bestätigt |
| 02 | Aktuellen MASTER-76-Stand lesen | PR #89 unverändert |
| 03 | Grünes vorheriges CI prüfen | Run #199 success, nur Ausgangsbasis |
| 04 | Überschneidungen identifizieren | P0 PR #69 und #80 als getrennte Vorschläge behandelt |
| 05 | Neuen eigenen Branch anlegen | Von fix/master76..., ohne fremde Branches zu ändern |
| 06 | Separate KI-Aufrufzahl prüfen | `ki_aufrufe.txt` exakt 4 |
| 07 | Fehlenden Zähler blockieren | Fail-closed |
| 08 | Veränderten Zähler blockieren | 3/5/ungültig abweisen |
| 09 | Zähler-Symlink blockieren | Keine Umleitung auf fremde Datei |
| 10 | Exakte Rollenzuordnung prüfen | Vier unterschiedliche Rollen |
| 11 | Einzeldateien mit Gesamtbericht vergleichen | Alle vier Gleichheit |
| 12 | Vertauschte Rolle blockieren | Rolle im JSON stimmt mit Dateinamen |
| 13 | Rollen-Symlink blockieren | Kein fremder Dateipfad |
| 14 | Beschädigte Rollen-JSON blockieren | Kein positives Ergebnis |
| 15 | Fremde Datentypen der Rollen blockieren | Kein ungefangener Fehler |
| 16 | CHECK-Urteil im Rollenbeleg prüfen | Muss bestanden sein |
| 17 | CHECK-Geheimnisscan unabhängig prüfen | Muss exakt leere Liste sein |
| 18 | CHECK-Tests unabhängig prüfen | Erfolg + positive Anzahl |
| 19 | Testzahl mit Gesamtbericht abgleichen | Kein widersprüchlicher PASS |
| 20 | COMMAND-NEIN weiter respektieren | Kein Erfolg |
| 21 | Modell-/Antwort-ID-Regeln erhalten | Andere Sicherheitstore bleiben wirksam |
| 22 | STOP-Datei und Crash-Sperre erhalten | MASTER 76 unverändert im Sperrabschnitt |
| 23 | Defekte Gesamtberichte kontrolliert abweisen | `einmal()` return 1 statt Stacktrace |
| 24 | Manipulierten Bool-Testzähler nicht akzeptieren | Nur `type(...) is int` |
| 25 | Counter zusätzlich in SHA256-Manifest aufnehmen | Integritätsindikator, kein Authentizitätsbeweis |
| 26 | Adversariale Offline-Regressionen | 10 neue Testmethoden |
| 27 | Bestehende positive MOCK-Fixture angleichen | Explizit nicht als realen KI-Pilot ausgeben |
| 28 | CI auf finalem HEAD + unabhängiger Review | Bis geprüft: NO-GO |

## Kernursache

Der aktuelle lokale Dienst prüft die Rolle-Dateien, aber bestätigt die positive Gesamtmeldung bei einem Bericht, dessen angegebene Modellaufrufzahl nicht gegen `ki_aufrufe.txt` kontrolliert wurde. Außerdem war `check_urteil=bestanden` als aggregiertes Feld ausreichend, auch wenn die gespeicherte CHECK-Rolle abgelehnt, das Scanresultat fehlt oder die gemeldeten Tests widersprüchlich sind. Malformierte Berichte konnten einen ungefangenen JSON-Fehler verursachen. Gleiche Schwachstellen waren bereits in separaten Vorschlags-PRs untersucht, waren aber nicht in MASTER-76-Branch integriert.

## Umsetzung im getrennten Branch

- `team/local_service.py`: zusätzlich separaten Aufrufzähler prüfen; Symlinks und ungültige Rollenstrukturen ablehnen; Einzelrollen- und CHECK-Urteil, Tests und Geheimnisscan abgleichen; beschädigte Berichte kontrolliert ablehnen; Zähler im SHA256-Manifest aufführen.
- `tests/test_local_service.py`: bestehende positive Unit-Test-Fixture vollständig als MOCK mit CHECK-, Rollen- und Zählerartefakten markieren.
- `tests/test_master77_proof.py`: zehn Offline-Regressionen, inklusive korrupter Daten und negativer Sicherheitsfälle.
- Eigener Branch wird zur **Review** gestapelt auf MASTER 76. Keine Änderung an bestehenden PRs oder `main`.

## Was Tests NICHT beweisen

Die Test-Fake-Antworten und ein `lokal-...`-Wert beweisen **nicht** vier reale KI-Modellaufrufe. Ein lokaler SHA256-Hash ist kein kryptografisch unabhängiger Nachweis über die Herkunft von Modellantworten. Weder eine echte Ollama-Instanz noch ein Cloudflare-Worker oder reale Produktdaten werden in dieser Änderung aktiviert. Die Details der offenen PRs #69 und #80 bleiben getrennt reviewpflichtig; hier wird kein automatischer Merge beansprucht.

## Stoppsignale

- Tests rot/übersprungen mit sicherheitsrelevanter Lücke, unvollständige Logs oder falscher geprüfter Commit => kein Go.
- Fehlende CHECK-Evidenz, Zähler, lokale Rollen oder konsistente Protokolle => `BLOCKIERT`.
- Keine Kostenfreigabe, kein Provider-Fallback, keine Cloud-KI-Aktivierung.
- Keine Produktionsaktivierung ohne explizite Freigabe und unabhängige technische/operative Abnahme.

## Verweise

- [Sicherheitsbasis PR #55](https://github.com/jefrey030/Schnapper/pull/55)
- [CI-Korrektur PR #85](https://github.com/jefrey030/Schnapper/pull/85)
- [MASTER 76 / PR #89](https://github.com/jefrey030/Schnapper/pull/89)
- [Ähnlicher Sicherheitsvorschlag PR #69](https://github.com/jefrey030/Schnapper/pull/69)
- [Anderer Prüfintegritätsvorschlag PR #80](https://github.com/jefrey030/Schnapper/pull/80)

**Erfolg wird erst nach CI-Joblogs am finalen SHA behauptet; der Mastertext allein ist kein Nachweis.**
