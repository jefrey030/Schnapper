# SCHNAPPER – großer Fertigstellungs-Master (25.10.2026)

**Ziel:** Nutzbare App statt bloßer KI-Statusberichte; dokumentierte funktionale Abnahme, konkrete Code-Reparaturen, klare Sperren vor Live-/Release.  
**Repository:** `jefrey030/Schnapper` · **Arbeitsbranch:** `integration/schnapper-p0-mainbased-20261025` · [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55) · **Zusatzkosten:** 0 €.  
**Modus:** bestehende Review-Branch fortführen; kein Merge, kein Deployment, kein eBay-/Open-Prices-Livezugriff, keine Modellkosten.

## 1. Verifizierter App-Bestand
- Python-App-Kern `app/schnapper` mit Angebotsprüfung, Versand-Gesamtpreis, Dubletten, Textsuche, Warnungen, Filtern, CSV-/JSON-Import.
- Lokaler HTTP-Server `app/schnapper/web.py` mit responsive Browserseite, Such-API, sicherem Upload, Merkliste/Alarm im Browser, optionalem Preisverlauf, Open-Prices-API standardmäßig gesperrt.
- Offline-MockAdapter mit `TEST`-Daten und nicht abrufbaren `.invalid`-URLs.
- `team/agent.py` und lokale KI-Option sind Entwicklungsinfrastruktur, **keine** überprüfte Vier-KI-Liveausführung. `main` enthält weiterhin den alten Cron; dessen Stilllegung existiert nur als Draft-Code.
- `docs/SCHNAPPER-MASTERPLAN.md` von 22.10. ist historisch und keine aktuelle, vollständig erledigte Abnahme.

## 2. Priorisierter Fertigstellungskatalog

| ID | Priorität | Fertigstellungsschritt | Bewertung |
| --- | --- | --- | --- |
| F1 | P0 | CLI: ungültige Filter/fehlende Daten kontrolliert mit Exitcode und Nachricht behandeln | Direkt im Review-Draft umsetzen und testen |
| F2 | P0 | Preisverlauf über `Verlauf.importiere` speichern, Rollback bei Dateifehler; niemals halbfertige Änderung als Erfolg ausgeben | Direkt im Review-Draft umsetzen und testen |
| F3 | P0 | Offline-End-to-End der App prüfen: eigene CSV-Daten, CLI-JSON, lokaler Webserver, Import, Suche, gesperrte Fremdquelle, Preisverlauf | Automatisierter Regressionstest ohne Fremdnetz |
| F4 | P0 | Sicherheits- und Offline-CI für **exakte finale SHA** mit PASS/SKIP/FAIL dokumentieren | GitHub Actions |
| F5 | P0 | Nachweisbare Freigabe für echte Angebotsquellen inkl. Nutzungsrechten / 0-€-Limit | Blockiert bis externe Genehmigung; nichts aktivieren |
| F6 | P0 | Unabhängige Code-/Sicherheitsreview und Freigabe zum Merge auf `main` | Betreiberentscheidung, vorher NO-GO |
| F7 | P1 | Reale Android-Browser-/Startbildschirmprobe mit echten Geräten | Noch nicht durchgeführt |
| F8 | P1 | Öffentliches Hosting, Datenschutz, Betrieb, Logs, Sicherheits- und Lasttests | Nicht ohne ausdrückliche Veröffentlichungsgenehmigung |
| F9 | P1 | Vier reale separate Agenten, Not-Aus unter echter Laufzeit und Quoten-/Kostenbelege | Ohne lokale Modellhostprobe nicht nachgewiesen |
| F10 | P1 | Legacy-GitHub-Cron nach Code-Review im Hauptbranch sicher entfernen | Nur nach ausdrücklicher Merge-Freigabe |

## 3. Abnahmebedingungen
- **F1–F3:** Tatsächliche Codeänderungen und reproduzierbare Offline-Tests, keine leeren Testbehauptungen.
- **F4:** Beide GitHub-Jobs `success`, Testzahlen und übersprungene Tests explizit genannt.
- **F5/F7/F8/F9:** Ungetestet und nicht freigabefähig nicht als fertig ausgeben.
- Kein Kauf, keine bezahlte API, keine Captcha- oder Nutzungsbedingungsumgehung.
- Vor Livebetrieb: unabhängige Security-Review + Betreiberfreigabe + belegte 0-€-Umgebung.
- Dokumentierte Rollen LEAD/BRAIN/CHECK/COMMAND sind Verantwortungsbereiche, keine spontan gestarteten externen KI-Instanzen.

## 4. Ausführungsprotokoll
Wird im selben Master nach tatsächlichen Commits und GitHub-Tests ergänzt. Abschluss nur mit beweisbarer finaler Commit-SHA.
