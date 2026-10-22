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
Die Tests simulieren Antworten; sie beweisen **keine** echte Cloud-KI.

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
   SELECT slot, task_id, status, error FROM schnapper_runs
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
