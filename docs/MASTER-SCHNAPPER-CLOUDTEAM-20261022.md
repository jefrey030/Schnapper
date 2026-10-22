# SCHNAPPER MASTER – VIER CLOUD-KIs, KOSTENFREI UND NACHWEISBAR
Stand: 22.10.2026 – Stand allein beschreibt **Entwicklung**, keinen 24/7-Live-Betrieb.

## Mission
Die vier Rollen LEAD, BRAIN, CHECK und COMMAND sollen stündlich eigenständige
**Planungs- und Prüfaufgaben** für SCHNAPPER bearbeiten und überprüfbare
Protokolle hinterlassen, ohne offenen Chat, Tablet oder heimischen PC.

## Verbindliche Kostenregel
1. **Keine** bezahlten Provider, GitHub-Actions-Runner, KI-API-Aufrufe,
   Cloudflare Workers Paid, Kreditkäufe oder zahlungspflichtige Ressourcen.
2. **Kein** automatisches Upgrade und keine Änderung von Zahlungsmethoden
   oder Billing-Spending-Limits.
3. Cloudflare Free-Plan im Dashboard *nachweislich* bestätigen, bevor
   KI-Bindings produktiv ausgeführt oder Cron-Trigger aktiviert werden.
   API-Abfragen zur Subscription liefern beim verbundenen Cloudflare-Konto
   aktuell OAuth-Berechtigungsfehler. Der Plan gilt deshalb als **UNVERIFIZIERT**.
4. Bis dahin: RUN_ENABLED=false, ACCOUNT_FREE_PLAN_CONFIRMED=no,
   crons=[]; bei fehlender Freigabe **null** KI-Anfragen.
5. Bei fehlendem Free-Kontingent, Modell- oder Datenbankfehler sofort
   blockieren. Nie kostenpflichtig zurückfallen und nie ungeprüft neu versuchen.

## Rollen – vier getrennte echte Modellaufrufe pro Stundenpuls
- **LEAD:** maximal drei klare Arbeitspakete, sinnvolle Prioritäten,
  Begründung und Abnahmekriterien.
- **BRAIN:** einen technischen, nachvollziehbaren Vorschlag entwickeln;
  kein erfundener Code, keine behaupteten Integrationen.
- **CHECK:** Vorschläge auf Risiken, Dubletten, Preise, Datenherkunft,
  Rechtmäßigkeit und fehlende Belege prüfen. Eine KI-Antwort ist **kein**
  tatsächlich ausgeführter Unit-Test.
- **COMMAND:** Aufgabenstatus, offene Blocker und einen kleinsten
  sicheren Folgeschritt protokollieren; keine eigenmächtige Freigabe.

## Geplante Infrastruktur
- Separater Cloudflare Worker `schnapper-agent-team` mit Worker-AI-Binding.
- Festes kostengünstiges Modell `@cf/meta/llama-3.2-1b-instruct`,
  `max_tokens=180` je Rolle, kein externer Modellprovider.
- Ein Cron-Trigger `17 * * * *` (UTC); erst nach Free-Tarif-Nachweis.
- Private D1-Datenbank `schnapper-agent-reports`, keine öffentliche
  Webansicht und keine Veröffentlichung der Reports.
- Jeder beabsichtigte Modellaufruf wird vorab über\n  `schnapper_runs.attempted_calls` gespeichert. Bei D1-Ausfall keine Inferenz.\n- Einmaliger Versuch je UTC-Stunde durch D1-Primärschlüssel.
  Fehlgeschlagener Lauf wird **nicht** automatisch wiederholt.
- Vier Zeilen je abgeschlossener Stunde mit Rollenname, Modell,
  Zeit, Antworttext und SHA-256; Run hat `started/completed/blocked`.

## Was der aktuelle Worker *nicht* kann
- Nicht direkt das private GitHub-Repository lesen oder bearbeiten.
- Keine Skripte autonom testen, Commits erstellen, PRs mergen,
  Live-Angebote abrufen oder SCHNAPPER deployen.
- Kein Beleg echter Live-Ausführung, bevor D1 und KI-Provider tatsächliche
  Ausführung und Logs zeigen. Die zehn am 22.10.2026 tatsächlich lokal mit Node.js 22 ausgeführten Tests sind **Simulationen** (10/10 bestanden).

## Umsetzung und Abnahme
1. Änderungen auf eigenem GitHub-Branch vorbereiten, niemals ohne Prüfung
   in `main` zusammenführen.
2. `node --test cloudflare/test/worker.test.mjs` wurde in einer isolierten\n   Testumgebung tatsächlich ausgeführt: **10/10 bestanden**; das D1-Schema\n   bestand zusätzlich einen SQLite-Fremdschlüssel-/Duplikat-Test.\n   Diese Tests beweisen keine Cloud-KI- oder Cron-Ausführung.
3. Cloudflare-Konto im Dashboard auf Free kontrollieren. Bei Paid oder
   nicht auslesbar: **STOP**, nicht deployen/aktivieren.
4. Erst bei bestätigtem Free-Plan: kostenlose D1 anlegen,
   `cloudflare/sql/schema.sql` einspielen, Bindings konfigurieren,
   Worker mit `RUN_ENABLED=false` und `crons=[]` bereitstellen.
5. Nach einem **begrenzten** Probeaufruf plus realen vier Modellantworten
   ohne Kosten: Free-Status und Tageskontingent nochmals prüfen.
6. Erst danach `RUN_ENABLED=true` und `17 * * * *` einsetzen.
7. Mindestens zwei voneinander getrennte echte Stundenläufe verifizieren:
   vier Rollen, D1-Zeitstempel, Modellbeleg, Fehler, Quota und Kosten
   anhand Cloudflare-Dashboard protokollieren.
8. Bei jeder Unklarheit sofort deaktivieren und den konkreten Blocker
   nennen; niemals fertig melden ohne den Nachweis.

## Verifikationsbericht (stündlich, wenn live)
- ZEITFENSTER (UTC/Berlin), RUN-SLOT, TASK-ID, Status.
- LEAD / BRAIN / CHECK / COMMAND: echte Antwort oder BLOCKIERT.
- Modell und Anzahl realer Inferenzaufrufe, D1-Datensatz und SHA-256.
- Getrennt: BELEGT, UNGEPRÜFT, BLOCKIERT, NÄCHSTER SCHRITT.
- Aussagen `KI hat programmiert`, `Tests grün`, `Demos fertig`
  sind ohne tatsächlich ausgeführte Werkzeuge verboten.

**Masterstatus:** technische Implementierung und lokale Simulation vorbereitet;
Live-Tarif und 24/7-Betrieb NICHT bestätigt. Zero Cost hat Vorrang.
