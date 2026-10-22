# LEAD – Lauf 20261022-2029

## Gewählte Aufgabe: F1 Aufräumen (tasks.json + Masterplan Abschnitt B)

**Begründung (Auswahl-Priorität):**
1. Offener Team-Draft-PR `agent/master/...`: **keiner** (REST `pulls?state=open`: #35, #34, #33, #31, #30, #29, #28, #27, #26, #25, #23, #21 – alle Branches `fix/`, `security/`; #6 `agent/master/20261021-21` ist geschlossen).
2. Aufgabe mit Status `open` in `team/tasks.json` auf main: **keine** (S-000–S-003 `review`, S-004–S-006 `proposed`).
3. Nächster offener Punkt der freigegebenen Liste: **F1** (weder in main noch als Team-PR umgesetzt). F1 ist reine Daten-/Doku-Pflege und in ~20 Min. machbar.

**Branch:** `agent/master/20261022-20`, neu von `origin/main` (= e134cd0).
Genau ein Punkt pro PR: nur F1. Draft-PR, kein Merge.

---

## Achtung: Konflikte, die BRAIN beachten muss

### K1 – Test erzwingt S-006 = "proposed"
`tests/test_branches_s006.py:61-66` (`test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten`) prüft:
- `s006["status"] == "proposed"` → **schlägt fehl**, wenn S-006 laut F1 auf `done` gesetzt wird.
- `s006["hinweis"]` enthält alle 4 Branch-Namen aus `KANDIDATEN` und den Text `Agenten löschen keine Branches` → bestehenden Hinweis **nicht kürzen, nur anhängen**.

F1 (freigegeben) verlangt S-006 = `done`, aber F1-Akzeptanz sagt „nur team/ und docs/ geändert“. Beides geht nicht gleichzeitig.
**Entscheidung LEAD:** Jefreys ausdrückliche Freigabe „S-006 done“ hat Vorrang; minimale, einzeilige Testanpassung in `tests/test_branches_s006.py` Zeile 64:
```python
        self.assertIn(s006["status"], ("proposed", "done"))
```
(übrige Prüfungen – Branch-Namen und „Agenten löschen keine Branches“ im Hinweis – bleiben unverändert; Testname bleibt). Diese **einzige Abweichung** vom Pfad-Kriterium muss COMMAND im PR-Text unter „Abweichung“ ausdrücklich nennen und begründen. Keine andere Datei außerhalb `team/`/`docs/` anfassen.

### K2 – S-007/S-008 existieren nur auf `origin/agent/master/reports`, nicht auf main
`git diff origin/main origin/agent/master/reports -- team/tasks.json` zeigt: S-007 (Entscheidungsvorlage PR #19/#20) und S-008 (Löschkandidaten-Liste) sowie ergänzte Hinweise S-004–S-006 stehen **nur** auf dem Reports-Branch.
Zusätzlich verwendet der **offene PR #33** (`fix/schnapper-open-qa-task-20261022`, von Jefrey) die ID **S-007** mit anderer Bedeutung („Null-Euro-QA …“, Status `open`). `team/runner.py:load_tasks` wirft bei doppelter ID `ValueError("Doppelte Aufgabe")`.
**Entscheidung LEAD:** S-007 und S-008 **nicht** nach main übernehmen (sonst ID-Kollision mit #33). Die IDs bleiben frei/reserviert; neue Aufgaben beginnen wie freigegeben bei **S-009**. S-007 (Reports-Branch) ist ohnehin überholt (#19, #20 am 22.10. gemergt). Im Hinweis von S-006 und im PR-Text vermerken (siehe unten). Hinweis: PR #33 und unser PR ändern beide das Ende von `tasks.json` → textueller Merge-Konflikt möglich; im PR-Text erwähnen.

---

## Konkrete Änderungen

### 1. `team/tasks.json`
Format beibehalten (2 Leerzeichen Einrückung, UTF-8, `ensure_ascii=False`, Pflichtfelder `id`, `title`, `priority` (int), `status`). S-000–S-003 unverändert.

**S-004** – nur ändern: `"status": "done"`; an `hinweis` anhängen:
` | Erledigt 22.10.2026 (Freigabe Jefrey, Lauf 20261022-2029): T1/T2 auf main belegt durch tests/test_abgleich_s004_s005.py.`

**S-005** – nur ändern: `"status": "done"`; an `hinweis` anhängen:
` | Erledigt 22.10.2026 (Freigabe Jefrey, Lauf 20261022-2029): T3 belegt durch tests/test_mock_adapter.py (MockAdapter, quelle='mock'), T4 durch tests/test_abgleich_s004_s005.py, T5 durch grüne Offline-Suite.`

**S-006** – nur ändern: `"status": "done"`; bestehenden `hinweis` vollständig behalten, anhängen:
` | Erledigt 22.10.2026 (Freigabe Jefrey, Lauf 20261022-2029): überholt – PRs #2, #6, #7, #8, #9 sind geschlossen bzw. gemergt; keine Aktion mehr nötig. S-007/S-008 (nur Vorschläge auf agent/master/reports) werden nicht übernommen; S-007 ist zudem durch offenen PR #33 belegt.`

**Neu S-009 … S-013** (Status `open`, je ≥ 2 Akzeptanzkriterien):

```json
{
  "id": "S-009",
  "priority": 9,
  "status": "open",
  "title": "F2 Angebot direkt in der App erfassen (Formular, POST-Endpunkt, CSV-Download)",
  "acceptance": [
    "Formular in der Web-App erfasst Titel, Preis, Zustand, Quelle und Link eines eigenen Angebots",
    "POST-Endpunkt nimmt Angebote nur mit Header X-Schnapper an; ohne Header Ablehnung (403), Test belegt",
    "Größenlimit für den Request-Body; zu große Anfrage wird abgewiesen (413), Test belegt",
    "Eingaben laufen durch die bestehende Prüfung (Preis, URL, Quellen-Register); ungültige Angebote werden abgewiesen",
    "Erfasste Angebote als CSV im Format von app/vorlagen/meine-angebote.csv herunterladbar",
    "Kein Netzwerkzugriff nach außen, alle Tests grün"
  ],
  "hinweis": "Freigegeben von Jefrey am 22.10.2026 als F2 (Lauf 20261022-2029 eingetragen)."
},
{
  "id": "S-010",
  "priority": 10,
  "status": "open",
  "title": "F3 Merkliste und Preisalarme als JSON sichern und wiederherstellen",
  "acceptance": [
    "Export erzeugt eine JSON-Datei mit Merkliste und Preisalarmen inkl. Formatversion",
    "Import stellt denselben Stand wieder her (Rundreise-Test: Export → Import → gleicher Inhalt)",
    "Defekte, zu große oder falsch versionierte JSON-Dateien werden mit Hinweis abgewiesen, bestehende Daten bleiben unverändert",
    "Keine Daten verlassen das Gerät, alle Tests grün"
  ],
  "hinweis": "Freigegeben von Jefrey am 22.10.2026 als F3 (Lauf 20261022-2029 eingetragen)."
},
{
  "id": "S-011",
  "priority": 11,
  "status": "open",
  "title": "F4 Barcode per Kamera scannen (BarcodeDetector)",
  "acceptance": [
    "Kamera-Knopf nutzt die Browser-API BarcodeDetector (EAN-13/EAN-8/UPC) und übernimmt den erkannten Code in die Barcode-Suche",
    "Ohne BarcodeDetector-Unterstützung oder ohne Kamerafreigabe: verständlicher Hinweis, manuelle Eingabe bleibt nutzbar",
    "Kein Bild wird gespeichert oder hochgeladen; keine externe Bibliothek",
    "Alle Tests grün"
  ],
  "hinweis": "Freigegeben von Jefrey am 22.10.2026 als F4 (Lauf 20261022-2029 eingetragen)."
},
{
  "id": "S-012",
  "priority": 12,
  "status": "open",
  "title": "F5 Ein-Befehl-Start für Android/Termux (start-schnapper.sh, docs/HANDY-START.md)",
  "acceptance": [
    "start-schnapper.sh startet die App mit einem Befehl unter Termux (prüft python3, startet Server nur auf 127.0.0.1, nennt die URL)",
    "docs/HANDY-START.md beschreibt den Ein-Befehl-Start Schritt für Schritt",
    "Skript lädt nichts aus dem Internet nach und braucht keine Zugangsdaten; Test prüft Skript auf diese Regeln",
    "Kennzeichnung, ob auf echtem Gerät getestet oder nicht; alle Tests grün"
  ],
  "hinweis": "Freigegeben von Jefrey am 22.10.2026 als F5 (Lauf 20261022-2029 eingetragen)."
},
{
  "id": "S-013",
  "priority": 13,
  "status": "open",
  "title": "F6 eBay vorbereiten (app/schnapper/ebay.py, Sandbox standard, Quelle gesperrt, docs/EBAY.md)",
  "acceptance": [
    "app/schnapper/ebay.py nutzt standardmäßig die eBay-Sandbox; Produktivbetrieb nur mit ausdrücklichem Schalter",
    "Zugangsdaten nur aus Umgebungsvariablen, nie im Repo; Test belegt, dass ohne Env keine Verbindung aufgebaut wird",
    "Quelle eBay bleibt im Quellen-Register gesperrt; Tests machen keinen Netzwerkaufruf",
    "docs/EBAY.md erklärt Entwicklerkonto, Sandbox, Produktivfreigabe und Env-Variablen",
    "Alle Tests grün"
  ],
  "hinweis": "Freigegeben von Jefrey am 22.10.2026 als F6 (Lauf 20261022-2029 eingetragen)."
}
```

### 2. `docs/SCHNAPPER-MASTERPLAN.md` – nur Abschnitt B ersetzen (Zeilen 23–37, von `## B. Offene Pull Requests` bis vor `## C.`)
Übrige Abschnitte unverändert lassen. Neuer Inhalt (Stand per REST `pulls?state=all&per_page=100`, 22.10.2026 ~20:30 UTC; #4 ist ein Issue, kein PR):

```markdown
## B. Pull Requests (echter GitHub-Stand)

Stand: 22.10.2026, ca. 20:30 UTC · Basis `main` @ e134cd0 · ermittelt per GitHub-REST `pulls?state=all`. #4 ist ein Issue, kein PR.
Der frühere Abschnitt (Empfehlung #6 → #12 → #7 → #8) ist überholt: Diese PRs sind gemergt bzw. geschlossen.

### Offen (12)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #35 | security: privaten SCHNAPPER-Stundenlauf fail-closed sperren (aktuelle main-Basis) | fix/guard-private-runner-20261022-current | offen | ja |
| #34 | fix(SCHNAPPER): Websuche weist Null- und Negativ-Höchstpreise ab | fix/web-maxpreis-positiv-20261022 | offen | ja |
| #33 | fix(team): offene QA-Aufgabe + fehlerresistente Stundenrotation | fix/schnapper-open-qa-task-20261022 | offen | ja |
| #31 | security(SCHNAPPER): KI-Token nur über HTTPS und ohne Redirect übertragen | security/schnapper-ki-token-transport-20261022 | offen | ja |
| #30 | fix(SCHNAPPER): Preisalarm-Import gegen ungültige Eingaben absichern | fix/schnapper-alarm-nonfinite-20261022 | offen | ja |
| #29 | fix: SCHNAPPER-Preise, URLs und Preisalarm zusammen sicher korrigieren | fix/schnapper-guardrails-konsolidiert-20261022 | offen | ja |
| #28 | fix: SCHNAPPER-Preisalarm bei defekten Wunschlisten robust machen | fix/alarm-input-validation-20261022 | offen | ja |
| #27 | fix(preise): DE/EN-Tausenderformate korrekt und sicher einlesen | fix/preisformate-gemischt-20261022 | offen | ja |
| #26 | fix(SCHNAPPER): Preise im deutschen UND englischen Zahlenformat korrekt erkennen | fix/preisformate-englisch-20261022 | offen | nein |
| #25 | fix(SCHNAPPER): englische Tausenderpreise korrekt lesen statt falscher Schnäppchen | fix/english-thousands-prices-20261022 | offen | ja |
| #23 | fix: Robuster Angebotsimport bei kaputten URLs und korrekte Port-Dubletten | fix/schnapper-url-validierung-20261022 | offen | ja |
| #21 | Security: Fail-Closed-Abnahme, Not-Aus und getrennte Release-Gates | security/schnapper-failclosed-20261022 | offen | ja |

Hinweis: #25, #26, #27 (Preisformate) und #28, #29, #30 (Preisalarm) überschneiden sich thematisch; #29 bündelt laut Titel mehrere davon. Entscheidung bleibt bei Jefrey.

### Gemergt (15)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #32 | QA: kostenfreie Offline-Testabnahme mit unverfälschbaren FAIL-Gates | qa/offline-abnahme-kostenfrei-20261022 | gemergt 22.10. 18:39 UTC | nein |
| #20 | fix(openprices): „Zum Angebot“ öffnet lesbare Preisseite statt JSON + Abnahme main | fix/openprices-link-webseite-20261022 | gemergt 22.10. 18:01 UTC | nein |
| #19 | Preisverlauf: Tiefstpreise und geschönte Statt-Preise erkennen | feature/preisverlauf-20261022 | gemergt 22.10. 18:02 UTC | nein |
| #18 | SCHNAPPER: offene PRs zusammengeführt (#7 #8 #12–#17), Tests repariert | integration/aufraeumen-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #17 | Merkliste und Preisalarm (WARENKORB/BLITZ) | feature/merkliste-preisalarm-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #15 | SCHNAPPER Gesamtstand: offene PRs zusammengeführt + echte Ladenpreise (Open Prices) | integration/schnapper-gesamtstand-20261022 | gemergt 22.10. 16:18 UTC | nein |
| #14 | SCHNAPPER: Masterplan, eigene echte Angebote, App für den Startbildschirm | feature/schnapper-master-handy-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #13 | SCHNAPPER S-005/T3: kostenloser Offline-Mock-Adapter mit Prüffällen | fix/schnapper-offline-mock-adapter-20261022 | gemergt 22.10. 16:17 UTC | ja |
| #11 | SCHNAPPER: Handy-Weboberfläche + sichere Angebotsquellen ohne Merge-Konflikt | fix/schnapper-web-main-20261022 | gemergt 22.10. 03:10 UTC | nein |
| #9 | fix: SCHNAPPER-Agentenstatus und KI-JSON fail-closed validieren | fix/agent-status-fail-closed-20261022 | gemergt 22.10. 08:35 UTC | nein |
| #8 | SCHNAPPER Cloud-Team: vier stündliche KI-Rollen – Free-only, Live-Start gesperrt | feature/cloudflare-free-hourly-20261022 | gemergt 22.10. 16:17 UTC | ja |
| #7 | SCHNAPPER: vier KI-Rollen lokal starten – null Bezahl-APIs, echte Stundenberichte | feature/local-free-ollama-agents-20261021 | gemergt 22.10. 16:17 UTC | ja |
| #5 | SCHNAPPER: App-Kern – Angebote prüfen, Dubletten, Suche, Import | feature/schnapper-angebotskern-20261021 | gemergt 22.10. 03:07 UTC | nein |
| #3 | SCHNAPPER: vier echte KI-Agenten über GitHub Models (0 €), Regelmodus entfernt | fix/ki-team-github-models-20261021 | gemergt 21.10. 20:15 UTC | nein |
| #1 | SCHNAPPER: sichere Aufgabenrotation, Tests und Modus ohne KI-API-Kosten | fix/schnapper-hourly-rotation-20261021 | gemergt 21.10. 20:15 UTC | nein |

### Geschlossen ohne Merge (7)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #24 | fix(SCHNAPPER): Preisalarm vor ungültigen Rabatten und Zustandsfiltern schützen | fix/alarm-nonfinite-input-20261022 | geschlossen | ja |
| #22 | SCHNAPPER: Stundenlauf nur bei eindeutig öffentlichem Repo aktivieren | fix/schnapper-stundenlauf-failclosed-20261022 | geschlossen | ja |
| #16 | SCHNAPPER: Preisquellen sichern und Testangebote eindeutig markieren | fix/schnapper-price-source-integrity-20261022 | geschlossen | ja |
| #12 | test: S-001 erlaubt echte Standardbibliothek statt fester Modulliste (Fix für #6 + #7) | fix/schnapper-stdlib-test-20261022 | geschlossen | nein |
| #10 | SCHNAPPER: Web-Oberfläche fürs Handy + Quellen-Register und Adapter (S-002) | feature/schnapper-web-quellen-20261022 | geschlossen | nein |
| #6 | SCHNAPPER MASTER: S-000 bis S-003, Vorschläge S-004–S-006, Abgleich gegen main | agent/master/20261021-21 | geschlossen | ja |
| #2 | SCHNAPPER: kostenloses lokales KI-Gehirn für 4 Agentenrollen | feature/local-free-brain-20261021 | geschlossen | ja |
```

Gesamt: 12 offen + 15 gemergt + 7 geschlossen = 34 PRs (#1–#35 ohne #4). BRAIN soll die Tabelle direkt vor dem Commit nochmals per REST gegenprüfen (`gh api 'repos/jefrey030/schnapper/pulls?state=all&per_page=100' --jq '.[]|[.number,.state,.merged_at,.draft,.head.ref]|@tsv'`) und Abweichungen übernehmen.

Optional, nur wenn trivial: Kopfzeile „Stand:“ in Zeile 3 des Masterplans **nicht** ändern (sie betrifft die anderen Abschnitte); Abschnitt B trägt seinen eigenen Stand. Abschnitt D Punkt 3 („in der Reihenfolge aus Abschnitt B“) bleibt unverändert.

### 3. `tests/test_branches_s006.py` – einzige Zeile (siehe K1)
Zeile 64: `self.assertEqual(s006["status"], "proposed")` → `self.assertIn(s006["status"], ("proposed", "done"))`.

Keine weiteren Dateien. Insbesondere **kein** App-Code, keine Workflows, nicht `team/STATUS.md` (Bericht/Status macht COMMAND separat auf `agent/master/reports`).

---

## Bestehende Tests, die Regeln für tasks.json erzwingen
- `tests/test_vorschlaege.py`
  - `test_echte_aufgaben_haben_gueltigen_status`: Status ∈ {open, in_progress, review, proposed, done}.
  - `test_vorschlaege_haben_akzeptanzkriterien`: jede `proposed`-Aufgabe hat `acceptance` als Liste mit ≥ 2 Einträgen.
  - `test_hinweis_ist_nichtleerer_text_und_aendert_status_nicht`: jedes `hinweis` ist nichtleerer String.
  - `test_lead_agent_filtert_nur_open`: `team/agent.py` enthält `t.get("status") == "open"` (nicht berührt).
- `team/runner.py:load_tasks` (via `tests/test_runner.py::test_tasks_format`, `test_vorschlaege`): Liste `tasks`, Pflichtfelder `id`, `title`, `priority`, `status`; `priority` muss `int` sein; **keine doppelten IDs**.
- `tests/test_branches_s006.py::test_s006_bleibt_vorschlag_und_nennt_alle_kandidaten`: S-006 Status (→ K1) und Hinweis muss die 4 Branches `fix/schnapper-web-main-20261022`, `feature/schnapper-web-quellen-20261022`, `feature/schnapper-angebotskern-20261021`, `fix/schnapper-hourly-rotation-20261021` sowie „Agenten löschen keine Branches“ enthalten.
- `tests/test_agenten.py` nutzt eigene Fixture-`tasks.json` → unabhängig vom echten Inhalt.
- `tests/test_abgleich_s004_s005.py`, `tests/test_mock_adapter.py` prüfen Code, nicht tasks.json (Belege für S-004/S-005).

---

## Akzeptanzkriterien (prüfbar)
1. Branch `agent/master/20261022-20` basiert auf `origin/main` (e134cd0): `git merge-base --is-ancestor origin/main HEAD` → Exit 0.
2. `team/tasks.json` ist gültiges JSON; `load_tasks()` läuft ohne Fehler; IDs eindeutig.
3. S-004, S-005, S-006 haben `"status": "done"`; ihre bisherigen `hinweis`-Texte sind unverändert enthalten (nur angehängt); S-006-Hinweis enthält „überholt“.
4. S-009 bis S-013 existieren mit `"status": "open"`, `priority` 9–13 (int), Titel beginnend mit F2…F6 und je ≥ 2 Akzeptanzkriterien gemäß obiger Liste.
5. Keine Aufgabe S-007 oder S-008 in `team/tasks.json` (Kollision mit PR #33 vermieden); S-000–S-003 unverändert.
6. `docs/SCHNAPPER-MASTERPLAN.md` Abschnitt B listet alle 34 PRs (#1–#35 ohne #4) mit Nummer, Titel, Branch, Status (offen/gemergt/geschlossen), Draft (ja/nein), übereinstimmend mit REST zum Commit-Zeitpunkt; die veraltete Empfehlung „#6 → #12 → #7 → #8“ ist entfernt; Abschnitte A, C, D, E und Nachträge unverändert.
7. `python3 -m unittest discover -s tests` → OK, Anzahl = 190 (wie main), 0 Fehler.
8. `cd cloudflare && node --test test/*.test.mjs` → 10/10 pass.
9. `git diff --name-only origin/main...HEAD` zeigt genau: `docs/SCHNAPPER-MASTERPLAN.md`, `team/tasks.json`, `tests/test_branches_s006.py` (letzteres als dokumentierte Abweichung, nur Zeile 64).
10. Secret-Scan auf dem Diff ohne Treffer (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY).
11. Draft-PR gegen main, PR-Text nennt: F1, Belege, Abweichung K1, Hinweis K2 (S-007/S-008, möglicher Textkonflikt mit #33). Kein Merge.

## Testbefehle
```bash
cd /home/claude/schnapper
python3 -c "import sys; sys.path.insert(0,'team'); from runner import load_tasks; t=load_tasks(); print(len(t), [(x['id'],x['status']) for x in t])"
python3 -m unittest discover -s tests
(cd cloudflare && node --test test/*.test.mjs)
git diff --name-only origin/main...HEAD
git diff origin/main...HEAD | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY' || echo "keine Secrets"
```
