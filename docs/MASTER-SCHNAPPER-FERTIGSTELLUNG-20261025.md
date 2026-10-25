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

## 4. Ausführungsprotokoll – tatsächlich abgeschlossen

### F1 ✅ Fehlerrobuste Kommandozeile
In `app/schnapper/__main__.py` werden Suchgrenzen vor dem Dateiimport geprüft:
- Höchstpreis muss positiv sein; unlesbare Preise werden mit verständlichem Fehler gemeldet.
- Mindestrabatt muss endlich und zwischen 0 und 100 liegen; deutsches Dezimalkomma wird akzeptiert.
- Nicht vorhandene Zustände werden vor jeglicher Datei-/Verlaufsänderung abgewiesen.
- Fehlende/ungelesene Quelldateien führen zu kontrolliertem Exitcode `1`; Filterfehler zu `2`. Kein ungefangener Traceback in den getesteten Negativfällen.

### F2 ✅ Preisverlauf konsistent und fehlersicher
Die CLI ruft nun `Verlauf.importiere` statt `aufzeichnen` mit anschließendem separatem `speichern` auf. Die bestehende Transaktion setzt den Arbeitsspeicher nach Speicherfehler zurück. Im Negativtest wird keine reguläre Trefferausgabe ausgegeben. Wiederholtes Importieren derselben Beobachtung erzeugt keinen doppelten Verlaufspunkt.

### F3 ✅ Durchgängiger Offline-MVP-Abnahmetest
Die neue `tests/test_fertigstellung_mvp.py` enthält acht echte, isolierte `unittest`-Testmethoden. Geprüft: positive eigene CSV mit deutsch geschriebenem Preis-/Rabattfilter; 9 ungültige Filtervarianten; fehlende Eingabedatei; idempotenter Preisverlauf; simulierter Laufwerksfehler; lokale HTTP-Suche mit Preisgrenze und Verlauf; Upload mit Header-Pflicht und Sperrung einer ausgeschlossenen Quelle; Open-Prices-Freigabegate ohne echten Netzwerkabruf.

**Wichtig:** Die Preisdaten der Tests sind synthetische eigene CSV-Beispiele, keine echten aktuellen Kleinanzeigen- oder eBay-Schnäppchen.

### F4 ✅ Aktueller Code geprüft
Erster erfolgreicher [GitHub Actions #40216433994](https://github.com/jefrey030/Schnapper/actions/runs/40216433994) für Code-SHA `8f974554dde0cc9d15196e91d9121af248e2c013`:
- `python-tests` **292 Tests ausgeführt, 1 übersprungen, 0 fehlgeschlagen**.
- `cloudflare-tests` **16/16 bestanden, 0 übersprungen, 0 fehlgeschlagen**.
- Dokumentation einschließlich `README.md` aktualisiert; der **abschließende Dokumentations-Commit erhält einen neuen CI-Lauf** und ist nur dann separat als bestanden zu kennzeichnen, wenn dessen beide Jobs erfolgreich gemeldet wurden.

### F5–F10 ❌/⏳ Offen – nicht durch Simulation ersetzbar
- **F5:** Echte automatische Angebote benötigen Quelle mit nachgewiesenen Nutzungsrechten, freigegebener Schnittstelle und nachgewiesenen 0-€-Bedingungen. Unfreigegebene eBay-/Kleinanzeigen-Daten dürfen nicht angebunden werden.
- **F6:** Unabhängige Sicherheitsreview, positive Freigabe-Gates und ausdrücklicher Merge-Beschluss fehlen. `main` bleibt unberührt.
- **F7:** Echtes Android-Gerät und interaktive Browserprobe (Startbildschirm/Dateiupload/Merkliste) bisher **nicht** geprüft.
- **F8:** Öffentliches Hosting inklusive Datenschutz, Betriebskosten, Zugriffs-/Lastschutz und Monitoring ist nicht abgenommen; kein Release.
- **F9:** Vier echte KI-Modellantworten sowie Stunden- und Not-Aus-Liveprobe fehlen weiterhin.
- **F10:** Stilllegung des Legacy-Cron auf `main` ist weiterhin nur im Draft #55 vorbereitet und benötigt Review-/Merge-Freigabe.

## 5. Fertigstellungsstatus ohne erfundene Prozentzahl

**Offline-MVP mit eigenen Daten:** Code korrigiert, Ende-zu-Ende-API-/CLI-Tests bestanden.  
**Vollständig nutzbare automatische SCHNAPPER-Live-App:** **noch nicht fertig**.  
**Autonomes Vier-KI-Team:** **nicht als aktiv nachgewiesen**.  
**Release:** **NO-GO**; kein Merge/Deploy, 0 € neue Kosten.

Die erreichte Teilleistung ist konkret verifiziert, aber die Anzahl grüner Unit-Tests ersetzt weder echte Datenquellen noch unabhängige Sicherheits- oder Endgerätetests.


## 6. Neues erledigtes Arbeitspaket F11 – Ergebnisexport für den Offline-MVP

**25.10.2026:** Der [separate Export-Fertigstellungs-Master](MASTER-SCHNAPPER-FERTIGSTELLUNG-EXPORT-20261025.md) hat den bereits begonnenen lokalen CSV-/JSON-Export durch Referenzpreis-Übernahme, Spreadsheet-Schutz und neun neue Offline-Regressionsfälle vervollständigt. Die Tests vergleichen JSON-/CSV-Ergebnisse mit der gefilterten Suche und prüfen einen ungefährlichen CSV-Wiederimport, Nulltreffer, ungültige Filter, Download-Header, HEAD und Browserlinks.

**Status F11: ✅ überprüft, nur Offline-MVP.** [GitHub Actions #40227372613](https://github.com/jefrey030/Schnapper/actions/runs/40227372613): Python 310 ausgeführt, 1 übersprungen, keine Fehler; Cloudflare 16/16 bestanden. Dieser letzte Nachweis bezieht sich auf den dokumentierten Export-Master vor Einfügung dieses Querverweises; der aktuelle Commit wird erneut geprüft.

F5–F10 bleiben ausdrücklich **offen**: lizenzierte Liveangebote, unabhängige Review und Merge, Android-Gerätetest, Hosting/Monitoring, echte KI-Liveprobe und Legacy-Cron-Übernahme nach `main`. Ein zusätzlich abgeschlossenes Offline-Feature ist **kein** Nachweis für einen vollständig fertigen öffentlichen Dienst.
