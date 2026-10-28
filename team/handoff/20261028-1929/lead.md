# LEAD – Lauf 20261028-1929 (UTC)

## Gewählte Aufgabe
- **F6 = S-013 „eBay vorbereiten“, PR #45** (Draft, offen)
- **Branch:** `agent/master/20261023-01` (bestehender PR-Branch, Kopf `31b52d4`). Es gibt keinen neuen Branch und keinen neuen PR. Gepusht wird nur normal (Fast-Forward), ohne Rebase und ohne Force.
- **Schritt:** Eine Kommandozeilen-Anbindung `python -m schnapper --ebay SUCHBEGRIFF` nach dem Muster von `--openprices`. Damit kann Jefrey den noch ausstehenden Sandbox-Test mit seinen eigenen Schlüsseln selbst mit einem Befehl ausführen. Dazu kommen Tests ohne Netz und ein kurzer Abschnitt in `docs/EBAY.md`.

## Begründung (Belege)
1. **Stand aller Team-PRs per REST und git (19:3x UTC):**
   - #36, #39, #40, #41, #44 und #45 sind alle `mergeable=true`/`clean`.
   - `git merge-base --is-ancestor origin/main <branch>` ergibt bei allen sechs Branches „yes“, `git merge-tree` ist überall konfliktfrei. Ein Merge von main ist also nirgends nötig.
   - CI `python-tests` ist auf allen sechs Köpfen `success` (c4ac5c5, fd16763, 33a9487, 662cf81, 41e801c, 31b52d4).
   - Keiner der PRs hat Review-Kommentare. Die zwei Issue-Kommentare an #40 (Sicherheitsbefund P0) sind laut Antwort in `33a9487` bereits behoben.
2. **#45 lag am längsten unberührt.** Er wurde zuletzt am 28.10. um 09:34 UTC aktualisiert (Lauf 20261028-0928). #39 kam in Lauf 1829 dran, #36 in 1729, #44 in 1629, #40 in 1433 und #41 in 1343.
3. **Die Lücke ist belegbar:**
   - `docs/EBAY.md` auf 31b52d4 sagt: „Noch keine Anbindung an Kommandozeile oder Weboberfläche (Folgepunkt).“
   - Der PR-Body von #45 nennt unter „Folgepunkte“: „CLI/Web-Anbindung des eBay-Adapters“ und „Sandbox-Test mit echten Schlüsseln, sobald Jefrey sie … angelegt hat“.
   - Der letzte Laufbericht (1829) führt den Sandbox-Test als offenen Punkt.
   - Ohne CLI müsste Jefrey dafür selbst Python-Code schreiben, denn `app/schnapper/__main__.py` kennt nur `DATEI` und `--openprices`.
4. **Die Änderung ist klein und konfliktarm:**
   - `__main__.py` wird von keinem der sechs Team-PRs geändert (geprüft mit `git diff --name-only origin/main origin/agent/master/<b>`).
   - Das Muster ist schon vorhanden (`--openprices`: lazy Import, Fehler führen zu Exit 3, Quellenhinweis über `lizenz`).
   - Die Tests für das Muster existieren in `tests/test_openprices.py` (Z. 255–275).
5. **Bewusst ausgeklammert:**
   - Anbindung an die Weboberfläche (zu groß, und `index.html`/`app.js` sind Konfliktzone von #39, #40 und #41).
   - Umbau des Platzhalters `adapter.EbayAdapter`. Ein einfacher Re-Export ginge nicht, weil der echte Adapter einen Pflicht-`suchbegriff` hat und `ebay.py` aus `adapter.py` importiert (Zirkelimport). Außerdem nutzen Bestandstests in `test_abgleich_s004_s005.py` und `test_app_quellen_web.py` `EbayAdapter()` ohne Argumente.

## Akzeptanzkriterien
1. **Neue Option:** `--ebay SUCHBEGRIFF` in `app/schnapper/__main__.py`.
   - Der Hilfetext nennt `SCHNAPPER_EBAY_FREIGABE=ja`, die Zugangsdaten-Variablen und „Sandbox standardmäßig“.
   - `schnapper.ebay` wird nur innerhalb des `--ebay`-Zweigs importiert (lazy), so wie `openprices`.
2. **Genau eine Quelle:** Es muss genau eines von `DATEI`, `--openprices EAN` und `--ebay SUCHBEGRIFF` angegeben sein, sonst `p.error(...)` (SystemExit 2).
   - Zu testen sind: keines, `x.csv --ebay foo`, `--openprices <EAN> --ebay foo`.
   - Der bestehende Test `x.csv --openprices EAN` muss weiter grün bleiben.
3. **Ohne Freigabeschalter:**
   - `main(["--ebay", "fahrrad"])` ohne `SCHNAPPER_EBAY_FREIGABE` liefert Rückgabewert **3**.
   - Auf stderr steht eine Zeile, die mit `eBay: ` beginnt und `SCHNAPPER_EBAY_FREIGABE` nennt. stdout bleibt leer.
   - Es findet **kein Netzaufruf** statt. Im Test sind `socket.create_connection`, `socket.socket.connect` und `urllib.request.OpenerDirector.open` so gepatcht, dass sie AssertionError werfen.
   - Die `SCHNAPPER_EBAY_*`-Variablen werden im Test gezielt entfernt (`mock.patch.dict`), damit die Umgebung des Rechners das Ergebnis nicht beeinflusst.
4. **Schalter gesetzt, Schlüssel fehlen:**
   - `FREIGABE=ja`, `CLIENT_ID=ID-geheim-123`, kein Secret: Rückgabewert 3.
   - stderr nennt `SCHNAPPER_EBAY_CLIENT_SECRET`, enthält aber **nicht** `ID-geheim-123`. Es gibt keinen Netzaufruf.
5. **Ungültiger Suchbegriff:** Leer, nur Leerzeichen oder 101 Zeichen ergeben Rückgabewert 3 mit `eBay: `-Meldung (ValueError aus dem Adapter), ohne Traceback und ohne Netzaufruf.
6. **eBay-Fehler:**
   - Fall: Schalter und Schlüssel sind gesetzt, und ein gepatchtes `schnapper.ebay._anfrage` wirft `EbayFehler("eBay HTTP 401 …")`.
   - Erwartet: Rückgabewert 3, stderr enthält `eBay: eBay HTTP 401`, kein Traceback.
   - Weder Client ID noch Secret erscheinen in stdout oder stderr.
7. **Erfolgsfall Sandbox ohne Netz:**
   - Aufbau: `schnapper.ebay._anfrage` wird durch eine Attrappe ersetzt. Sie liefert für POST auf den Token-Pfad `{"access_token": "TOK-geheim-xyz", "expires_in": 7200}` und für GET auf den Suchpfad eine `itemSummaries`-Liste mit zwei gültigen EUR-Angeboten (https-Link auf `www.ebay.de`) und einem ungültigen (z. B. USD).
   - Rückgabewert 0.
   - Die Textausgabe zeigt beide Titel mit Präfix `SANDBOX ` und `[ebay]` sowie den Quellenhinweis `Daten: eBay Browse API` (`ebay.HINWEIS_QUELLE`).
   - Der übersprungene Eintrag (`adapter.hinweise`) erscheint auf **stderr**, z. B. als `eBay-Hinweis: …`.
   - Alle Aufrufe der Attrappe gingen an Host `api.sandbox.ebay.com`, nicht an `api.ebay.com`.
   - In stdout und stderr kommen weder `TOK-geheim-xyz` noch Client ID oder Secret vor.
   - Die Testdaten sind so gewählt, dass die Angebote nicht vom Betrugsverdacht-Filter (`ohne_verdacht`) verworfen werden.
8. **JSON-Ausgabe:**
   - Wie AK 7, aber mit `--json`. stdout ist gültiges JSON.
   - `treffer[*].quelle == "ebay"`, Titel beginnen mit `SANDBOX `, `lizenz == "Daten: eBay Browse API"`.
   - Es gibt keine Hinweise oder Fehlermeldungen in stdout; stdout enthält nur JSON.
9. **Filter wirken:**
   - `--ebay … --max-preis X` filtert eines der zwei gültigen Angebote weg, der Rückgabewert ist 0.
   - Alternativ geht der Nachweis auch über `--suche`.
10. **Produktion nur mit Schalter:** Mit `SCHNAPPER_EBAY_PRODUKTION=ja` gehen die Aufrufe der Attrappe an `api.ebay.com`, und die Titel haben **kein** `SANDBOX `-Präfix. Das ist ein kurzer Test.
11. **`docs/EBAY.md`:**
    - Der Satz „Noch keine Anbindung an Kommandozeile …“ wird ersetzt durch „Kommandozeile: ja (`--ebay`), Weboberfläche: noch nicht (Folgepunkt)“.
    - Neuer kurzer Abschnitt „Sandbox-Test per Kommandozeile“ mit dem Befehl `PYTHONPATH=app python -m schnapper --ebay "fahrrad"`, optional `--json`, und dem Hinweis auf das `SANDBOX `-Präfix und die Exit-Codes (0 OK, 3 gesperrt/Fehler).
    - Nur Platzhalter, keine echten Werte.
12. **Gegenprobe:** Die neuen CLI-Tests laufen gegen `app/schnapper/__main__.py` von `31b52d4`, also mit `git show 31b52d4:app/schnapper/__main__.py` in einer Kopie. Sie müssen rot werden, weil das Argument `--ebay` unbekannt ist und deshalb SystemExit 2 kommt.
13. **Bestand bleibt grün:**
    - Alle bisherigen Tests bleiben unverändert grün. Erwartet sind 252 + neue Tests, plus/minus umgebungsbedingte Skips.
    - `ebay.py`, `adapter.py`, `quellen.py`, `.github/`, `team/` und `cloudflare/` bleiben **unverändert**.
14. **Keine Geheimnisse und keine Netzaufrufe:**
    - Es gibt keine echten Schlüssel und keine Live-Abrufe, weder in Tests noch beim Entwickeln.
    - Der Secret-Scan des Diffs (`sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`) ist leer, abgesehen von den bekannten Platzhaltern in der Doku.
15. **Ein Commit** auf `agent/master/20261023-01`, direkter Nachfolger von `31b52d4`.
    - Nachricht z. B. „SCHNAPPER MASTER: F6 eBay-Sandbox-Test per Kommandozeile (--ebay)“.
    - Trailer gemäß Session-Vorgabe.
    - Push nur nach `git merge-base --is-ancestor origin/agent/master/20261023-01 HEAD`, normal und ohne Force.
    - Der PR-Body von #45 bekommt per `gh api -X PATCH` einen angehängten Nachtrag. Der PR bleibt Draft, es gibt keinen Merge.

## Erlaubte Dateien
- `app/schnapper/__main__.py`
- `tests/test_ebay.py`. Alternativ ist eine neue Datei `tests/test_ebay_cli.py` erlaubt, wenn das übersichtlicher ist. In diesem Fall bleibt `tests/test_ebay.py` unangetastet.
- `docs/EBAY.md`

Alles andere ist tabu, insbesondere `.github/workflows`, `team/` (auf dem Feature-Branch), `app/schnapper/ebay.py`, `adapter.py`, `quellen.py`, `web.py`, `web/*`, `cloudflare/`, fremde PRs (#19, #50, #102–#134) und alles von ZENTNA, JERRY AL/Jerry-AL und Beatmaster.

## Arbeitsweise
Gearbeitet wird in einem Wegwerf-Worktree, **nicht** direkt im Klon:
```sh
cd /home/claude/schnapper && git fetch origin
git worktree add /tmp/claude-0/-home-claude-schnapper/6542dd57-933c-599a-b9d2-39b95c8e0e81/scratchpad/wt-45 -B agent/master/20261023-01 origin/agent/master/20261023-01
```
Danach in diesem Worktree arbeiten, committen und pushen. Nach dem Push wird der Worktree mit `git worktree remove` entfernt.

## Testbefehle (im Worktree-Stamm)
```sh
python3 -m unittest discover -s tests
python3 -m unittest tests.test_ebay -v          # bzw. tests.test_ebay_cli -v
python3 -m unittest tests.test_openprices -v    # CLI-Bestand (--openprices) unverändert grün
python3 -m unittest tests.test_abgleich_s004_s005 tests.test_app_quellen_web -v
cd cloudflare && node --test test/*.test.mjs
```

Zur Gegenprobe (AK 12) kommt `__main__.py` von 31b52d4 in eine Kopie des Worktrees, dann laufen die neuen CLI-Tests dort und müssen rot sein.

Neue Browsertests sind nicht nötig. In der Gesamtsuite laufen die bestehenden Playwright-Tests mit dem vorinstallierten Chromium (`/opt/pw-browsers`, automatische Suche über `_finde_chromium()`). **Nie `playwright install` ausführen.**

Manueller Rauchtest ohne Netz und ohne Schlüssel, Exit 3 erwartet:
```sh
env -u SCHNAPPER_EBAY_FREIGABE PYTHONPATH=app python3 -m schnapper --ebay fahrrad; echo "exit=$?"
```
