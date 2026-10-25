# MASTER 93 – SCHNAPPER: Replay-Schutz und ehrliche KI-Erfolgsnachweise

**Datum:** 25. Oktober 2026  
**Projekt:** SCHNAPPER / lokale Ollama-Anbindung  
**Basis:** [Master 92 / PR #90](https://github.com/jefrey030/Schnapper/pull/90), HEAD `1d8ad3bbbfce750bfa09661d36391809dd33bff2`  
**Arbeitszweig:** `chatgpt/master93-replay-evidence-20261025`  
**Betrieb:** nur isolierte Codeprüfung; 0 € zusätzliche Kosten; keine kostenpflichtigen Modelle/APIs; keine Veröffentlichung, kein Main-Merge, kein Deployment und keine echten KI-Agenten gestartet.

## Arbeitsauftrag

Finde und behebe zwei konkrete Restschwachstellen im lokalen Ollama-Evidenzpfad:

1. **Replay:** MASTER 92 prüfte die Syntax von `created_at`, jedoch nicht dessen Aktualität. Eine Stunden oder Jahre alte formal gültige Ollama-JSON-Antwort konnte deshalb im nächsten Durchlauf als neuer Abschluss akzeptiert werden. Ab jetzt blockiert der Adapter und zusätzlich der lokale Pilot-Prüfer veraltete oder stark vorausdatierte Antworten (höchstens 10 Minuten alt und maximal 2 Minuten in der Zukunft). Die Rechneruhr muss dafür vertrauenswürdig gestellt sein.
2. **Echtheits-Falschaussage:** `vier_echte_ki_antworten` wurde aus **Fehlermeldungs-Teilstrings** abgeleitet. Eine einzige fehlerhafte, aber anders benannte Sicherheitsprüfung konnte dazu führen, dass trotz `status=BLOCKIERT` das Feld irreführend `true` meldete. Diese Ableitung wurde entfernt. Lokale Daten-Konsistenz wird getrennt als `lokale_antwortbelege_vollstaendig` berichtet; `vier_echte_ki_antworten` bleibt ohne unabhängige Host-/Providerattestierung konservativ `false`.

## Ausgefüllter großer Master – 24 Pakete

| Paket | Priorität | Aufgabe | Status |
| --- | --- | --- | --- |
| M93-01 | P0 | Aktuellen SHA von PR #90, #80, #72 feststellen | ERLEDIGT |
| M93-02 | P0 | GitHub-CI-Basisergebnisse prüfen | ERLEDIGT: #40200331680 grün |
| M93-03 | P0 | Überlappende Änderungen/Reviews sichten | ERLEDIGT: gestapelte Drafts; #90 kein Review |
| M93-04 | P0 | Eigenen isolierten Prüfzweig erstellen | ERLEDIGT |
| M93-05 | P0 | Ollama-Antwortvalidator aus Master 92 lesen | ERLEDIGT |
| M93-06 | P0 | Veraltete JSON-Replay-Lücke bestimmen | ERLEDIGT |
| M93-07 | P0 | Zeitfenster zur Annahme definieren | UMGESETZT: minus 10 bis plus 2 Minuten |
| M93-08 | P0 | Vergangenheits-/Zukunftsprüfung im Ollama-Adapter ergänzen | CODE UMGESETZT |
| M93-09 | P0 | Freshness zusätzlich beim späteren Pilot-Abgleich prüfen | CODE UMGESETZT |
| M93-10 | P0 | Ältere synthetische Testdaten auf dynamische UTC-Zeit korrigieren | CODE UMGESETZT |
| M93-11 | P0 | Adapter-Replay-Negativtest: stark veraltet | CODE UMGESETZT |
| M93-12 | P0 | Adapter-Replay-Negativtest: stark vorausdatiert | CODE UMGESETZT |
| M93-13 | P0 | Frische Antwort weiterhin akzeptieren | CODE UMGESETZT |
| M93-14 | P0 | Lokale Pilot-Negativprobe: vier veraltete Belege | CODE UMGESETZT |
| M93-15 | P0 | Bisherigen `vier_echte_ki_antworten`-Berechnungsweg prüfen | ERLEDIGT |
| M93-16 | P0 | Fehlertextbasierte positive Erfolgsaussage entfernen | CODE UMGESETZT |
| M93-17 | P0 | Eigenbeleg-Konsistenz separat als bool berichten | CODE UMGESETZT |
| M93-18 | P0 | Lokale UUID nicht als echte Providerattestierung werten | UMGESETZT |
| M93-19 | P0 | Positiven Mocklauf auf konservative Ehrlichkeit testen | CODE UMGESETZT |
| M93-20 | P0 | Python-Gesamtsuite des Master-93-Branchs | NOCH ZU PRÜFEN |
| M93-21 | P0 | Cloudflare-Offline-Suite des Master-93-Branchs | NOCH ZU PRÜFEN |
| M93-22 | P0 | Integrations-PR und echte Logs/SHA dokumentieren | NOCH ZU PRÜFEN |
| M93-23 | P0 | Unabhängige Security-Abnahme/Review einholen | OFFEN; kein Eigenreview als unabhängig ausgeben |
| M93-24 | P0 | Echte vier Modellantworten, Live-Not-Aus, Budget und Deployment-Gates | OFFEN / NO-GO |

## Test- und Betriebsgrenzen

- Das Zeitfenster ist bewusst fail-closed und setzt eine korrekt konfigurierte lokale Rechneruhr voraus; es verhindert einfache Replays alter Antworten, **nicht** gezieltes Fälschen frischer lokaler Daten durch einen kompromittierten Host.
- `antwort_id` bleibt selbst erzeugt. Es gibt keinen kryptografisch signierten Ollama-Proof und keine unabhängige Identitätsgarantie des lokalen Modells.
- Der positive Testpfad nutzt absichtlich Prozess-Mocks und synthetische Antwortdateien. **Ein Unit-Test darf das Feld `vier_echte_ki_antworten` nicht wahr setzen.**
- Selbst bei vollständigem lokalen Datenabgleich wird nur `LOKALER PILOT FORMAL BESTANDEN (ECHTHEIT UNVERIFIZIERT)` ausgegeben.
- Das gewünschte autonome Vier-KI-Team wird hier nicht aktiviert; ein externer Host, tatsächliche installierte Modelle, saubere authentifizierte Provider-Logs, Kosten-/Stop-Nachweise, unabhängige Prüfung und Freigabe fehlen.

## Abnahme

Nur SHA-fixierte echte CI-Läufe mit exakten Python-/Cloudflare-PASS-/SKIP-/FAIL-Zahlen gelten als Code-Testnachweis; ein grüner Test ersetzt keine Security-/Produktionsfreigabe. Frühere Master 90/91/92 und ihre PRs bleiben offen, bestehende Branches unverändert. **Gesamtstatus bis zu dokumentierter unabhängiger Freigabe: NO-GO.**
