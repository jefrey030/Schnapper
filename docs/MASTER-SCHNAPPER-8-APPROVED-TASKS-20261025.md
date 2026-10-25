# SCHNAPPER – GROSSMASTER 8: Freigegebene Aufgaben als Pflicht vor jedem KI-Lauf

**Datum:** 25.10.2026  
**Projekt:** SCHNAPPER / Vier-Agenten-KI-System  
**Priorität:** P0 – Kostenschutz, Aufgabengovernance und keine erfundenen Eigenläufe  
**Quelle:** `team/tasks.json`  
**Umsetzung:** eigener Draft-Branch `fix/schnapper-approved-tasks-master8-20261025`  
**Basis:** `integration/schnapper-p0-mainbased-20261025` / bestehender Sicherheitsentwurf #55  
**Vorhandener Auftrag:** Issue #83 (MASTER 76), bereits thematisch zuständig.  
**Freigabe:** NO-GO für Merge, Veröffentlichung, Deploy und echten KI-Betrieb.  
**Kosten:** 0 € zusätzliche Ausgaben.

## 1. Unabhängig belegte Ausgangslage

`team/tasks.json` enthält sieben Aufgaben S-000 bis S-006, davon vier mit `review` und drei mit `proposed`. **Keine** hat den Status `open` und keine eine explizite Freigabe `approved: true`. Der Cloudflare Worker enthielt dagegen bisher eine separate statische Vierer-Rotation S-000 bis S-003 und hätte nach anderen Gate-Freigaben Aufgaben unabhängig vom autoritativen Aufgabenbestand gewählt.

Das ist kein Beleg für laufende Modelle oder angefallene Kosten, aber eine konkrete Architekturabweichung mit künftigem Risiko ungewollter Anfragen.

## 2. P0-Umsetzung – tatsächlich geändert

### BRAIN (Code)
- `cloudflare/src/worker.mjs`: hartkodierten Vier-Aufgaben-Katalog entfernt; `TASKS` als bewusst leeren freigegebenen Snapshot angelegt.
- `chooseApprovedTask(tasks, hourIndex)` wählt **nur** `status==='open'` **und** `approved===true` mit gültiger ID, nicht leerem Ziel, positiver numerischer `revision` und eingetragenem `owner`; doppelte oder fehlerhafte IDs blockieren.
- Auswahl sortiert nach Task-ID, um stabile Reihenfolgen zu erzielen.
- `runSlot` gibt bei null genehmigten Aufgaben `KEINE AUFGABE` mit `attempted_calls:0` **vor D1-Slot-Claim und jedem Modellaufruf** zurück.
- Für isolierte Offline-Unit-Tests existiert der dritte Funktionsparameter `taskSource`. Der produktive `scheduled()`-Handler verwendet ausschließlich den fest einkompilierten Snapshot und **keine per Env-/HTTP-Input injizierten Aufgaben**.

### CHECK (Tests)
- `cloudflare/test/worker.test.mjs`: Bestehende positiven Offline-Tests erhalten ausdrücklich einen **synthetischen, genehmigten Testauftrag**, der keine Freigabe für Cloud- oder Live-Betrieb impliziert.
- Neuer Vertragstest lädt `team/tasks.json` ausschließlich in der **Node-Testumgebung**, filtert `status=open AND approved=true` und verlangt Gleichheit mit dem veröffentlichten Worker-Snapshot.
- Negativtests: keine genehmigte Aufgabe -> keine Modellabfrage und kein D1-Slot-Claim; `review`, `proposed`, nicht genehmigte `open` und unechte Freigabewerte -> blockiert; doppelte IDs, unvollständige Revision/Owner -> blockiert.
- Positivtest: stabile Task-Auswahl unabhängig von der Eingabereihenfolge.

### LEAD (Governance)
- **Keine** der sieben vorhandenen Aufgaben wurde von `review` oder `proposed` auf `open` geändert.
- Das Freigabefeld `approved=true` wurde keiner Bestandsaufgabe ohne Betreiberentscheidung hinzugefügt.
- Für eine spätere zulässige Änderung müssen Aufgaben in `team/tasks.json` **manuell mit gesonderter Zustimmung** geöffnet und freigegeben werden, und die generierte/synchronisierte Worker-Aufgabenliste muss im Review angepasst werden. Der Vertrags-Test verhindert einen unbemerkten Quellstand-Konflikt.
- Diese Lösung führt **keinen** dynamischen autonomen Aufgabenimport ein; sie sperrt absichtlich, bis die sichere Synchronisation und Betreiberfreigabe eingerichtet ist.

### COMMAND (Abnahme)
- GitHub-Workflow `SCHNAPPER Tests` auf exakter PR-SHA; Python/Cloudflare offline prüfen; echte Logs mit PASS/FAIL/SKIP auswerten.
- Test-Simulationen niemals als vier echte KI-Modellaufrufe bezeichnen.
- Release ist selbst bei allen grünen Tests nicht freigegeben; Sicherheitsreview, Kosten-/Free-Tier-Nachweis und gesonderte Hostabnahme bleiben nötig.

## 3. Verbindliche Abnahmekriterien

1. `node --test test/*.test.mjs` im Ordner `cloudflare` (keine externe KI).
2. `python -m unittest discover -s tests -v` (keine produktiven Preisquellen).
3. `No approved open task means zero model calls and no D1 claim` wirklich `ok` im Log.
4. `Cloudflare task snapshot exactly mirrors approved open team/tasks.json` wirklich `ok` im Log.
5. Alle alten Cloudflare-Schutztests weiterhin positiv, kein fehlendes Not-Aus und keine Permission-Ausweitung.
6. Ungültige Freigaben, doppelte Aufgaben oder fehlende Metadaten ergeben null KI-Aufrufe.
7. GitHub-CI nur für exakte letzte Commit-SHA werten, kein `skipped` als `PASS`.
8. Replit/CHECK soll den Code unabhängig reviewen; der GitHub-PR startet Replit nicht automatisch.

## 4. Grenzen und offene Folgearbeit

**0 € Zusatzkosten;** keine Modell-Downloads, keine Paid APIs, kein Merge, kein `main`-Commit, keine Deployments, keine Cloudflare-Bindings oder D1-Migration, keine Secrets, keine Änderung von GitHub-Sichtbarkeit oder Billing, keine Live-KI, keine fremden Branches löschen.

Die separate lokale Ollama-Aufgabenplanung und der Cloudflare-Snapshot sind **noch nicht eine gemeinsame verteilte Live-Datenbank**; dieser Master stellt zunächst einen prüfbaren gemeinsamen Quellvertrag und den sicheren Null-Aufgaben-Zustand her. Ein späterer automatischer Aufgaben-Übergabemechanismus braucht explizite Betreiberfreigabe und unabhängige Tests.

**Entscheidung:** Bis zur abschließenden Sicherheitsprüfung und Host-Freigabe ausdrücklich **NO-GO**.
