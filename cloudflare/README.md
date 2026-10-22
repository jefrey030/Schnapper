# SCHNAPPER Cloud-Team – Free-only Vorbereitung

**Nicht live geschaltet.** Dieser Ordner enthält einen Cloudflare-Worker für
vier nacheinander arbeitende KI-Planungsrollen mit privaten D1-Berichten.

Die GitHub-Actions-Jobs für das private Repository bleiben unverändert.
Der Code hat zwei Sperren: `RUN_ENABLED=false` und
`ACCOUNT_FREE_PLAN_CONFIRMED=no`. In der Beispielkonfiguration sind
**keine** Cron-Trigger aktiv. Fehlende AI- oder D1-Bindings blockieren.

## Ohne Cloud-Kosten testen
```sh
node --test cloudflare/test/worker.test.mjs
```
**Lokal auf Node.js 22 ausgeführt: 10/10 Tests erfolgreich (22.10.2026).**
Die Tests simulieren Antworten; sie beweisen **keine** echte Cloud-KI.
Das D1-SQL-Schema wurde zusätzlich mit SQLite auf Fremdschlüssel und
eindeutige Stundenkennungen geprüft.

## Späterer, ausdrücklich kontrollierter Free-Rollout
1. Im Cloudflare-Dashboard prüfen, dass der aktuelle **Workers Free** Plan
   und das kostenlose Workers-AI-Kontingent gelten. Wenn unklar: STOP.
2. Erst dann private D1 `schnapper-agent-reports` im Free-Tarif erstellen,
   `sql/schema.sql` anwenden und die echte Datenbank-ID in einer Kopie
   von `wrangler.example.toml` hinterlegen. Keine Secrets ins Git.
3. Worker mit `RUN_ENABLED=false` und `crons=[]` (noch keine Jobs) deployen.
4. Einzige geplante KI-Laufzeit: native Workers AI; Modell:
   `@cf/meta/llama-3.2-1b-instruct`. Kein offenes Web-Interface.
5. Nach realem, kostenseitig geprüftem Pilot auf Free: Variablen
   `RUN_ENABLED=true`, `ACCOUNT_FREE_PLAN_CONFIRMED=yes`, danach
   **nur einen** Zeitplan `17 * * * *` aktivieren.
6. In D1 zwei echte Stunden vergleichen:
   ```sql
   SELECT slot, task_id, status, attempted_calls, error FROM schnapper_runs
   ORDER BY slot DESC LIMIT 8;
   SELECT slot, role, model, sha256, created_utc FROM schnapper_reports
   ORDER BY slot DESC, role ASC LIMIT 16;
   ```
7. Bei Fehlern oder Kostenrisiko Cron sofort entfernen und
   `RUN_ENABLED=false` setzen. Bei Paid-Plan niemals hochschalten.

**Wichtige Grenze:** Die Agenten schreiben Vorschläge und Berichte.
Sie programmieren SCHNAPPER **nicht** autonom und greifen nicht auf
private GitHub-Dateien oder externe Shopangebote zu. Dafür braucht
es später gesondert geprüfte Integrationen.

Master: `docs/MASTER-SCHNAPPER-CLOUDTEAM-20261022.md`.

## Tatsächlich geprüfte Cloudflare-Ressourcen (22.10.2026)

- Verbundenes Cloudflare-Konto antwortet auf reine Lesefunktionen.
- D1-Datenbankliste: **leer**.
- Workers-Liste: ausschließlich bestehender `jerry-al`-Worker;
  **kein** SCHNAPPER-Worker vorhanden.
- Billing- und Tarifabfragen mit aktueller OAuth-Verbindung: **403**,
  fehlender `Billing Read`-Zugriff. `default_usage_model=standard`
  beweist **keinen** Free-Tarif.
- Aus diesem Grund wurde **nichts** in Cloudflare angelegt/deployt,
  keine KI gestartet und kein Stundentimer aktiviert.

Das Software-Flag `ACCOUNT_FREE_PLAN_CONFIRMED=yes` ist nur eine
Konfigurationssperre und kein Zugriff auf Cloudflares Abrechnung.
Sollte ein Workers-Paid-Tarif oder eine spätere Umstellung vorliegen,
könnten AI-Aufrufe **auch innerhalb selbstgesetzter Aufruflimits kosten**.
Daher muss Workers Free vor Aktivierung im Dashboard nachgewiesen
und vor einer späteren Tarifumstellung die Automatik wieder deaktiviert
werden. Niemals den Wert blind auf `yes` setzen.

Jeder gestartete Inferenzversuch wird in D1 unter
`schnapper_runs.attempted_calls` **vor** dem Modellaufruf notiert.
Wenn dieses Protokoll nicht geschrieben werden kann, wird keine KI
aufgerufen; ein fehlgeschlagener Stundenlauf wird nicht automatisch neu gestartet.
