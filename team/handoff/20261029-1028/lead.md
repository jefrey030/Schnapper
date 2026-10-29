# LEAD – Lauf 20261029-1028 (UTC)

Start: Thu Oct 29 10:30:26 UTC 2026 · Ende: Thu Oct 29 10:32:08 UTC 2026 (beide per `date -u`)

## Aufgabe
- **F6 = S-013, eBay vorbereiten, Draft-PR #45**
- Wahlgrund: faire Rotation. In `team/runs/INDEX.md` (Reports-Branch) war #45 zuletzt in Lauf 20261029-0428 dran und ist damit am längsten unberührt. Der letzte Bericht (20261029-0928) empfiehlt F6/#45 ebenfalls.
- Der CHECK-Hinweis zu F1 Fall C (TypeError statt Assertion) bleibt offen. Er ist nur Testklarheit, die Mutation wird schon erkannt. Er ist deshalb nachrangig.

## Branch
- Fortgesetzt wird der bestehende Team-Branch `agent/master/20261023-01`, Kopf `9cde1eea9871614da189918f8a123e3bb200f2c4`.
- `git merge-base --is-ancestor origin/main origin/agent/master/20261023-01` ergibt Exit 0. origin/main 6dbe114 ist also enthalten, ein Merge ist nicht nötig.
- Der Branch liegt 6 Commits vor main (ecad218 … 9cde1ee). Geändert sind nur `app/schnapper/__main__.py`, `app/schnapper/ebay.py`, `docs/EBAY.md`, `tests/test_ebay.py` und `tests/test_ebay_cli.py`.
- Ausgangsstand im Worktree: `python3 -m unittest discover -s tests` ergibt `Ran 265 tests … OK`.

## Mangel (belegt): kein Gesamtzeitlimit in `_anfrage`
Die Arbeitsliste verlangt für F6 ein „Zeit-/Größenlimit“. `_anfrage` (`app/schnapper/ebay.py`) gibt `timeout=TIMEOUT` (15 s) nur an `opener.open()` weiter. Bei urllib gilt dieser Wert pro Socket-Operation, nicht für die ganze Anfrage. Ein Server, der die Antwort Byte für Byte schickt (Abstand jeweils knapp unter dem Timeout), hält `antwort.read(MAX_ANTWORT_BYTES + 1)` beliebig lange fest. Bei 2 MB Grenze sind das theoretisch bis zu 2 Mio. × 15 s. Ein Gesamtlimit (Deadline) fehlt, im Code gibt es kein `monotonic` und keine Frist rund um das Lesen der Antwort.

Beleg (nur lokal, 127.0.0.1, kein externer Abruf). Das Skript `/tmp/claude-0/-home-claude-schnapper/7385c0b5-6fd7-560e-845f-174409adc668/scratchpad/tropf.py` startet einen lokalen Server, der 20 Byte im Abstand von 0,3 s schickt. Per `mock.patch(ebay._oeffner)` wird die Anfrage dorthin umgeleitet, der echte Lesepfad von `_anfrage` läuft dabei unverändert. Aufruf mit `timeout=0.5`:

```
$ cd /home/claude/lead-wt && python3 -I .../scratchpad/tropf.py
timeout=0.5 s, Dauer=6.0 s, Ergebnis={'a': 1}
```

Ergebnis: Bei einem Limit von 0,5 s dauert die Anfrage 6,0 s, also das Zwölffache, und endet trotzdem erfolgreich, ohne `EbayFehler`. Die vorhandenen Tests prüfen nur, dass `timeout` an `open()` übergeben wird und dass `socket.timeout` gemeldet wird. Den Fall „langsam tröpfelnd“ prüfen sie nicht. Das Akzeptanzkriterium „Zeitlimit“ ist damit nicht erfüllt.

## Umsetzungsvorgabe für BRAIN
1. Auf `agent/master/20261023-01` arbeiten (lokaler Branch von origin, Kopf 9cde1ee). Kein Rebase, kein Force.
2. In `app/schnapper/ebay.py`, Funktion `_anfrage`:
   - Direkt vor `opener.open(...)` eine Frist setzen: `frist = time.monotonic() + timeout`. `time` ist bereits importiert.
   - `antwort.read(MAX_ANTWORT_BYTES + 1)` durch eine Leseschleife ersetzen. Jeder Durchlauf ruft `antwort.read1(min(64 * 1024, MAX_ANTWORT_BYTES + 1 - gelesen))` auf. `read1` liest höchstens einmal vom Socket und blockiert daher höchstens einen Socket-Timeout lang. Die Schleife endet bei `b""` (Ende) oder wenn `gelesen > MAX_ANTWORT_BYTES`.
   - Nach jedem Stück prüfen: Ist `time.monotonic() > frist` erreicht, folgt `raise EbayFehler("eBay antwortet zu langsam (Zeitlimit {timeout:g} s überschritten)")` (Wortlaut frei, er muss aber „Zeitlimit“ enthalten). Keine URL, kein Token und kein Kopfzeilenwert im Text. `from None` bzw. außerhalb des except-Kontexts.
   - Die Fehlerbehandlung für Größe und JSON bleibt wie bisher („eBay-Antwort zu groß“, „kein gültiges JSON/UTF-8“).
   - Dauer im schlimmsten Fall: höchstens `timeout` + 1 Socket-Timeout. Das gehört als kurzer Kommentar an die Stelle.
3. In `tests/test_ebay.py`:
   - Die Attrappe `Antwort` bekommt einen Lesezeiger. `read(n)` und neu `read1(n)` liefern fortlaufend Stücke und am Ende `b""`. Alle vorhandenen Tests müssen unverändert grün bleiben, insbesondere `test_groessenlimit_und_json` (2 000 001 Byte ergeben „zu groß“) und der Ende-zu-Ende-Test.
   - Neuer Test `test_gesamtzeitlimit_tropfende_antwort`: Attrappe mit `status=200`, deren `read1` pro Aufruf genau 1 Byte gültiges JSON liefert, zum Beispiel `b'{"a": 1}' + b" " * 40`. Dazu `mock.patch.object(ebay.time, "monotonic")` mit einer Uhr, die bei jedem Aufruf um 1 s weiterläuft. Aufruf über den echten `_anfrage`-Pfad mit gepatchtem `_oeffner` und `timeout=5`. Erwartet wird `EbayFehler` mit „Zeitlimit“ im Text, `read1` wird höchstens etwa 10-mal aufgerufen, und der Text enthält weder URL noch Token. Kein `time.sleep` und kein echtes Netz.
   - Neuer Test `test_schnelle_antwort_innerhalb_frist`: Dieselbe Antwort ohne fortlaufende Uhr ergibt das Dict `{"a": 1}`. Er zeigt, dass die Schleife korrekt zusammensetzt.
4. In `docs/EBAY.md`, Zeile mit „Zeitüberschreitung (15 s)“, eine neue Zeile bzw. einen Zusatz einfügen: „`eBay antwortet zu langsam (Zeitlimit …)`“, Bedeutung: Antwort dauert insgesamt länger als 15 s. Höchstens 2 Zeilen ändern.
5. Commit-Nachricht: `SCHNAPPER MASTER: F6 eBay – Gesamtzeitlimit beim Lesen der Antwort (S-013, #45)` mit den Attributionszeilen aus dem System-Hinweis. Nicht pushen, das macht COMMAND nach dem CHECK.

## Erlaubte Dateien
- `app/schnapper/ebay.py` (nur `_anfrage`, ggf. eine Konstante)
- `tests/test_ebay.py`
- `docs/EBAY.md` (höchstens 2 Zeilen)

Alles andere ist tabu, insbesondere `.github/workflows/`, `team/`, `app/schnapper/web/`, `__main__.py` und fremde Branches.

## Akzeptanzkriterien
1. `git diff --stat origin/agent/master/20261023-01..HEAD` zeigt nur die drei erlaubten Dateien, keine unter `.github/workflows`.
2. Eine tröpfelnde Antwort (1 Byte pro Lesevorgang, Uhr läuft weiter) endet über `_anfrage` mit `EbayFehler`, der „Zeitlimit“ enthält. Der Text enthält weder URL noch Token noch Kopfzeilen, `__cause__` ist None.
3. Eine schnelle Antwort aus mehreren Stücken wird korrekt zu JSON zusammengesetzt. Größenlimit (2 000 001 Byte ergeben „zu groß“) und JSON-Fehlerfall bleiben unverändert.
4. Gegenprobe/Mutation: Wird die Fristprüfung in `_anfrage` auskommentiert oder entfernt, scheitert der neue Test (FAIL). Danach zurücksetzen und mit `git diff` bzw. sha256 belegen, dass `ebay.py` wieder dem Commit-Stand entspricht.
5. Optionaler Zusatzbeleg (nur lokal 127.0.0.1): Das Skript `tropf.py` aus dem Scratchpad endet mit dem neuen Code nach etwa 0,5–1,1 s mit `EbayFehler` „Zeitlimit“ statt nach 6,0 s mit Erfolg.
6. `python3 -m unittest tests.test_ebay -v` ist grün, 0 Skips, mindestens 2 Tests mehr als vorher. `tests.test_ebay_cli` ist grün.
7. `python3 -m unittest discover -s tests` ist grün, mindestens 267 Tests.
8. `cd cloudflare && node --test test/*.test.mjs` ergibt 10 pass, 0 fail.
9. Kein echter Netzaufruf in den Tests, keine Live-Abrufe bei eBay oder Open Prices. Der Lauf funktioniert auch offline, zum Beispiel mit `unshare -rn`, falls verfügbar.
10. Secret-Scan über `git diff origin/main...HEAD` (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY) ergibt 0 Treffer. Keine Inhalte von ZENTNA, JERRY AL oder Beatmaster berührt.
11. Kein Push auf main, kein Merge, kein Force-Push. Der Push erfolgt nur auf `agent/master/20261023-01` durch COMMAND nach bestandenem CHECK (Fast-Forward von 9cde1ee).

## Testbefehle
```
python3 -m unittest tests.test_ebay -v
python3 -m unittest tests.test_ebay_cli -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Browsertests sind für diesen Schritt nicht nötig. Falls doch, dann nur mit Playwright und vorinstalliertem Chromium, kein `playwright install`.

Hinweis: Der LEAD-Worktree `/home/claude/lead-wt` ist wieder entfernt (`git worktree list` zeigt nur den Klon).
