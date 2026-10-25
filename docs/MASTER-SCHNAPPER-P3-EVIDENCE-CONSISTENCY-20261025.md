# SCHNAPPER MASTER P3 – Integrität und Konsistenz lokaler KI-Nachweise

**25. Oktober 2026** · **Budget:** 0 € · **Modus:** isolierter GitHub-Draft und Offline-CI · **Release:** NO-GO  
**Zielbranch:** `integration/schnapper-p0-mainbased-20261025`, [Entwurf #55](https://github.com/jefrey030/Schnapper/pull/55)

## Hauptmission
Der technische Pilotnachweis muss die Herkunft, Reihenfolge und innere Übereinstimmung der fünf Prozessschritte (LEAD, BRAIN, CHECK, COMMAND, BERICHT) nachweisen. Ein beliebiges Array mit fünf Exitcodes 0 darf nicht länger als korrekte Prozesskette gelten. Globale Zusammenfassungen dürfen nicht von ihren Einzelbelegen abweichen.

## Bestätigter Ausgangsbefund
Die Implementierung in `team/local_service.py::pruefe_nachweise` validiert bislang nur `len(schritte)==5` und `all(x.exitcode==0)`. Dadurch werden falsch zugeordnete oder duplizierte Rollenschritte bei ansonsten positivem Mock-Bericht nicht als Prozessnachweisfehler erkannt. Ebenso sind zusammengefasste `aufgabe`, `check_urteil`, `tests_ok` und `tests_anzahl` noch nicht durchgängig gegen LEAD und CHECK in den Originaldateien abgeglichen.

## Vier unabhängige Arbeitsfunktionen

| Rolle | Aufgabe | Nachweis |
| --- | --- | --- |
| LEAD | Stand von PR #55 prüfen, nur einen neuen Master im bestehenden Branch führen | GitHub SHA + Dokument |
| BRAIN | Strikte Prozessreihenfolge und Übereinstimmung aggregierter Daten implementieren | Codeänderung auf Draft |
| CHECK | Manipulations-, Duplikat-, widersprüchliche Aufgaben-/CHECK- und negative Schemafälle als Mock-Tests ergänzen | GitHub Actions Offline-Jobs grün |
| COMMAND | GitHub-CI-Zahlen, geprüfte SHA, Grenzen und verbleibenden Freigabeblocker dokumentieren | GitHub-Kommentar und finaler Master |

## Verbindliche Invarianten
1. Exakt fünf Prozessschritte, streng in Reihenfolge LEAD → BRAIN → CHECK → COMMAND → BERICHT; keine Duplikate und keine fehlenden Rollen.
2. Jeder erfolgreich behauptete Prozess liefert integer Exitcode 0 (kein bool, kein Text).
3. Jedes Einzelrollenprotokoll nennt die entsprechende Rolle und passt exakt zum aggregierten Bericht.
4. `bericht.aufgabe` stimmt mit `LEAD.plan.aufgabe_id` überein; die strukturierte Rotation in `selected_task` muss dieselbe ID enthalten.
5. `bericht.check_urteil` und `tests_ok`/`tests_anzahl` stimmen mit `CHECK.urteil` und `CHECK.werkzeug.tests` überein. Null Tests und Test-SKIPs als Erfolg sind nicht zugelassen.
6. Keine Änderungen auf `main`, keine externen KI-Aufrufe, kein Deploy, keine Käufe oder kostenpflichtigen Cloud-Kontingente. **Mock-Tests belegen keine echte KI.**

## Abnahme
- [ ] Fünf Prozessbelege vollständig, eindeutig und geordnet geprüft
- [ ] Rollenidentität und lokale Original-JSON als Teil des Gate abgeglichen
- [ ] Aufgaben- und CHECK-/Testergebnisse im Gesamtbericht konsistent
- [ ] Positive Fixture bleibt bestehen, negative Regressionen schlagen korrekt fehl
- [ ] Python und Cloudflare GitHub Actions bei letzter SHA bestanden
- [ ] SHA, Run, Testzahlen, Restrisiken und NO-GO dokumentiert

## Unveränderte Sperren
Die bestehende PR #55 bleibt Draft; im Hauptbranch ist die Abschaltung des alten Stundenworkflows weiter nicht gemergt. Produktionsbetrieb, Ollama-Hostbetrieb, echte vier KI-Agenten und Remote-Betrieb bleiben unbestätigt. Die Freigabe für Merge und Produktion liegt beim Betreiber, nicht beim automatisierten Test.
