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

- [x] Fail-Closed-Berichtsparser und robuste Typprüfungen implementiert
- [x] Agenten-Prozessstartfehler sicher gesperrt und ohne rohe Exception protokolliert
- [x] Neue Negativtests für unlesbare/ungültige Berichte und ungültige Feldtypen
- [x] Neue Regression für `OSError` mit gestoppter Folgerollenkette
- [x] Bisherige positive Offline-Simulation weiterhin bestanden
- [x] [GitHub CI #40202225565](https://github.com/jefrey030/Schnapper/actions/runs/40202225565) zum Code-SHA `f561235670de18dfe1727fc9ee0ad0304896930b` erfolgreich
- [x] Code-SHA `f561235670de18dfe1727fc9ee0ad0304896930b`, Python 248 Tests (1 Skip), Cloudflare 16/16 PASS dokumentiert
- [x] Produktivfreigabe bleibt ausdrücklich NO-GO

## Tatsächlich ausgeführte Arbeiten (nachweisbar)

**BRAIN – Code:** `team/local_service.py` prüft den JSON-Gesamtbericht schon beim Laden. Defekte UTF-8-/JSON-Dateien und ein gültiges JSON mit einem anderen Root-Typ führen zu Exitcode 1 und `BLOCKIERT`; eine Erfolgskennzahl oder nachgelagerte Pilotfreigabe entsteht nicht. Der Prüfpfad kontrolliert `agenten`, Rollenfelder, Modellinformationen, Plan, COMMAND und Prozessliste als korrekte Datentypen. Ein fehlgeschlagener Start eines Kindprozesses (`OSError`) wird mit `exitcode=-4` im Prozessnachweis dokumentiert, der genaue Exception-Text wird nicht in Logs übernommen; kostenrelevante Folgerollen werden übersprungen. Ein Berichtsschritt kann die Fehlersituation weiterhin festhalten.

**CHECK – Tests:** Vier zusätzliche Unit-Testmethoden in `tests/test_local_service.py` prüfen defektes JSON, Listen-/Null-Root, unpassende Feldtypen, `OSError` und falsche grüne Berichte. Beim ersten CI-Test gab es wegen einer **zwischenzeitlich ebenfalls verschärften CHECK-Freigaberegel** eine veraltete Testerwartung (`tests/test_agenten.py`): bei fehlgeschlagenen Werkzeugtests wird heute überhaupt keine CHECK-KI mehr angefragt, anstatt nachträglich ein `abgelehnt`-Urteil zu generieren. Die Regression wurde an diese strengere Sperre angepasst, **nicht** das Sicherheitsgate abgeschwächt.

**Ausgeführte CI (vor diesem abschließenden Dokumentationscommit):** [Run 40202225565](https://github.com/jefrey030/Schnapper/actions/runs/40202225565) am SHA `f561235670de18dfe1727fc9ee0ad0304896930b`, **248 Python-Tests, 1 übersprungen, 0 Fehler** und **16 Cloudflare-Tests, 16 bestanden, 0 Fehler, 0 übersprungen**. Beide Jobs `success`. Der Abschluss-Dokumentationscommit muss separat durch dieselben Jobs bestätigt werden.

**Freigabe und Grenzen:** Änderungen ausschließlich im Review-Draft [#55](https://github.com/jefrey030/Schnapper/pull/55). Keine Änderung an `main`, kein Merge, kein Cloudflare-Deploy, kein kostenpflichtiger Dienst und kein echter autonomer Vier-KI-Lauf. Ein grüner Test beweist nur den getesteten Code, keine Live-/Betriebsabnahme. Der auf `main` bestehende veraltete Stundenjob ist bis zu einer separat autorisierten Übernahme weiterhin ein offener P0-Blocker. Status **NO-GO**.
