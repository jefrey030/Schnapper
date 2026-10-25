# SCHNAPPER MASTER P3 – Robuste Offline-Abnahme und Fail-Closed-Prozesse

**Datum:** 25. Oktober 2026 · **Branch:** `integration/schnapper-p0-mainbased-20261025` · **Review:** [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55) · **Budget:** 0 € Zusatzkosten · **Freigabe:** NO-GO

## Hauptauftrag
Den lokalen Vier-Rollen-Pilot gegen beschädigte oder manipulierte Nachweisdateien und fehlgeschlagene Prozessstarts absichern. Jeder technische Nachweisfehler muss zu einer klaren Sperre führen, statt eine unkontrollierte Ausnahme oder ein positives Ergebnis zu erzeugen. Keine Live-KI, kein Merge, kein Deployment.

## Vorab verifizierter Bestand

- Bestehender Draft #55 ist offen, weiterhin Reviewpflicht; `main` nicht verändern.
- In `team/local_service.py::einmal()` wird der gespeicherte Gesamtbericht mit `json.loads(report_path.read_text(...))` ohne Schutz vor ungültigem JSON oder Lesefehlern geladen. Ein defekter Bericht bricht den Pilotlauf unkontrolliert ab.
- `pruefe_nachweise()` vertraut zum Teil auf die Typen der Felder des geladenen Berichts. Unerwartete Listen/Strings anstelle von Objekten können Ausnahmen auslösen.
- Ein fehlgeschlagener Start eines Agenten-Kindprozesses (`OSError`) wird noch nicht wie ein fehlgeschlagener Agent protokolliert.
- Bis hierher bewiesene CI des vorherigen Masters: [Run #40198769377](https://github.com/jefrey030/Schnapper/actions/runs/40198769377) am Code-SHA `79cb3f6991229cec0ab665bf735d5d3ddedee4cd`: 244 Python-Tests (1 Skip) und 16/16 Cloudflare-Tests bestanden.

## Vier Arbeitsrollen

**LEAD – Bestandsaufnahme:** Datengrenzen und vorhandene Regressionen überprüfen. Änderungen nur auf dem vorhandenen Branch. Keine Duplikat-PR, keine Produktion.

**BRAIN – Implementierung:** Fehlende/kaputte JSON-Berichte mit klarer BLOCKIERT-Rückgabe behandeln; ungültige Report-Feldtypen nicht akzeptieren; Fehler beim Start eines lokalen Agenten sicher als fehlgeschlagenen Prozess aufnehmen; keine geheimnishaltigen Ausnahme-Texte ausgeben.

**CHECK – Negativ- und Positivtests:** Defekte JSON-Daten, nicht-objektförmige Reports, kaputte Rollenfelder sowie `OSError` beim Start eines Kindprozesses simulieren. Positiven Vierfach-Mocklauf erhalten, CI an exakter SHA auswerten, SKIPs getrennt benennen.

**COMMAND – Audit:** Tatsächliche Commits, GitHub-Testlauf und Restblocker hinterlegen. Keine Behauptung über vier autonome Modellagenten oder Live-Betrieb. Sicherheitsentscheidung NO-GO bis unabhängige Prüfung.

## Sicherheitsvertrag

- 0 € Zusatzkosten, keine kostenpflichtigen APIs/Modelle, keine Cloudflare-/D1-Bereitstellung.
- Keine Schreibzugriffe auf `main`, kein Merge oder Repo-Sichtbarkeitswechsel.
- Unlesbare oder ungültige Gesamtberichte ergeben Fehlercode `1` und niemals `TECHNISCHER PILOT ERFOLGREICH`.
- Ungültige Feldtypen/fehlende Rollenbelege ergeben eine normale Liste von Blockern, keinen uncaught Traceback.
- Ein `OSError` bei einem Agentenstart stoppt kostenrelevante Folgerollen; ein isolierter BERICHT-Schritt kann die Fehlerlage dokumentieren.
- Keine rohen Token- oder Subprozess-Ausnahmeinhalte in Konsolenausgaben.
- Mock-Tests sind keine produktiven KI-Aufrufe.

## Abnahmeliste

- [ ] Fail-Closed-Berichtsparser und robustes Validierungsschema implementiert
- [ ] Agenten-Prozessstartfehler sauber blockiert und dokumentiert
- [ ] Neue Negativtests für unlesbare/ungültige Berichte und ungültige Feldtypen
- [ ] Neue Regression für `OSError` mit gestoppter Folgerollenkette
- [ ] Bisherige Positivsimulation weiter bestanden
- [ ] Python- und Cloudflare-CI auf neuem Code-Stand erfolgreich
- [ ] Finaler HEAD und Testzahlen dokumentiert
- [ ] Produktivfreigabe bleibt ausdrücklich NO-GO
