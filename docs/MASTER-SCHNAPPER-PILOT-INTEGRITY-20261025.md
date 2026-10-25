# SCHNAPPER MASTER 5 – Lokale Vier-KI-Abnahme gegen falsche Pilot-Nachweise

**Datum:** 25.10.2026  
**Priorität:** P0, Prüfintegrität und Sicherheitsfreigabe  
**Bezug:** Issue #62, Sicherheitsintegration PR #55  
**Änderungsort:** isolierter Branch `fix/schnapper-local-pilot-proof-20261025` auf Basis von `integration/schnapper-p0-mainbased-20261025`  
**Freigabe:** NO-GO; Budget 0 €, weder Merge noch Deployment noch externer KI-Aufruf.

## 1. Entdeckte Schwachstelle

Die lokale Funktion `team/local_service.py::pruefe_nachweise()` prüfte vor dieser Änderung lediglich, ob `LEAD.json`, `BRAIN.json`, `CHECK.json` und `COMMAND.json` **existieren**. Für die positiven Aussagen zu Modellantworten, Freigaben und Testzahlen vertraute sie dem separaten Gesamtbericht. Die vier Datei-Inhalte wurden weder geparst noch auf Übereinstimmung geprüft. Ein vorhandener Unit-Test erzeugte vier Minimaldateien und dennoch ein positives Piloturteil.

Weiterhin stammte die Teilstatus-Aussage `vier_echte_ki_antworten` aus einem fragilen Ausschluss einzelner Fehlertext-Fragmente. Auch das lokale `ki_aufrufe.txt`-Zählerartefakt wurde vor einer Pilotfreigabe nicht explizit geprüft.

**Konsequenz:** Lokale Test-/Pilotnachweise konnten innerhalb der implementierten Prüfung einander widersprechen, ohne zwingend die positive Bewertung zu verhindern. Dies ist eine Lücke in der **Integritätsprüfung**, kein Nachweis eines externen Angriffs oder einer tatsächlich laufenden KI.

## 2. Änderungen, die dieser Master auf dem isolierten Branch umsetzt

1. Jede Rollen-JSON einlesen, syntaktisch validieren, Rollenkennung überprüfen und mit dem jeweiligen Rollenobjekt im Gesamtbericht vergleichen. Fehlend, beschädigt, falsch oder widersprüchlich = BLOCKIERT.
2. Persistiertes `ki_aufrufe.txt`-Artefakt separat einlesen; genau vier lokale Aufrufversuche müssen berichtet **und** im Zähler belegt sein.
3. `CHECK=bestanden` muss in der gespeicherten CHECK-Rolle stehen; ein bloß positives Aggregatfeld reicht nicht.
4. CHECKs Test- und Geheimnisscan-Werkzeugnachweise sind verbindlich: erfolgreicher Testlauf, echte positive Anzahl, gleiche Gesamt-Testanzahl, leere Geheimnisfundliste.
5. Die Teilstatusanzeige `vier_echte_ki_antworten` wird nicht länger aus Formulierungen der Fehlerliste ermittelt: Bei einer negativen Integritätsprüfung bleibt der Teilstatus falsch.
6. Bestehenden reinen Mock-Positivtest mit **konsistenten** Rollenobjekten, CHECK-Werkzeugbefunden und lokalem Aufrufzähler aktualisieren.
7. Unabhängige Negativtests ergänzen: widersprüchliche Rollen-Datei, beschädigtes JSON, fehlender oder falscher Zähler, CHECK abgelehnt trotz positivem Aggregat, fehlender Geheimnisscan.

## 3. Abnahmekriterien

- `python -m unittest discover -s tests -v` auf **exakter PR-HEAD-SHA**; Zahlen für PASS/FAIL/SKIP getrennt erfassen.
- `cd cloudflare && node --test test/*.test.mjs` auf derselben SHA, ohne Cloudflare-Ressourcen.
- Negativfälle verweigern eine positive Pilotabnahme und geben niemals Geheimnisse aus.
- Der konsistente Mock-Test darf weiterhin bestehen, muss aber ausdrücklich **Simulation** bleiben.
- Keine GitHub-Models-Inferenz; keine Ollama-Downloads oder echten LLM-Aufrufe, keine Datenquellenfreischaltung.
- Kein weiterer Sicherheits-PR parallel auf `main`; dieser PR ist bewusst **gestapelt** auf die bestehende Sicherheitsintegration #55.

## 4. Geltungsbereich und Grenzen

Dieses Änderungspaket prüft nur, dass die **lokalen Artefakte einander nicht widersprechen**. Es liefert **keine** kryptografisch verifizierte Modellidentität, keine unabhängigen echten vier KI-Antworten und keine Sicherheit gegen einen vollständig manipulierbaren Host. Das Aufrufzählerartefakt belegt keine tatsächliche Inferenz beim Provider. Echte Pilotabnahme benötigt weiterhin einen vertrauenswürdigen Host, nachvollziehbare Prozesslogs, unabhängige Prüfung und ausdrückliche Freigabe.

**Status nach Codeerstellung:** Implementiert auf isoliertem Branch; automatische CI erst nach tatsächlich ausgewertetem Run als PASS dokumentieren. Ohne CI: NOT_RUN. Veröffentlichung, Merge, Produktionszugriff und kostenpflichtige Dienste bleiben gesperrt.

## 5. Übergabe an Replit / unabhängige CHECK-Rolle

Replit soll **nicht** denselben Patch erneut bauen. Stattdessen: aktuellen Diff auf diesem Branch unabhängig reviewen, alle Negativtests ausführen, CI auf aktuelle SHA prüfen, echte Rolle-/Datei-Konsistenz gesondert nachvollziehen und verbliebene Risiken als NO-GO/REVIEW-READY dokumentieren. Automatisches Auftrags-Abholen durch Replit ist nicht belegt.
