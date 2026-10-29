# BRAIN – Lauf 20261029-1028 (UTC)

Start: Thu Oct 29 10:33:15 UTC 2026 · Ende: Thu Oct 29 10:36:42 UTC 2026 (beide per `date -u`)

## Branch / Commit
- Branch: `agent/master/20261023-01` (mit `git checkout -B … origin/…` ausgecheckt), Ausgangskopf `9cde1eea9871614da189918f8a123e3bb200f2c4`
- Neuer Commit: `e035a29691a4393166ab80bad1ae39c301c8956c` „SCHNAPPER MASTER: F6 eBay – Gesamtzeitlimit beim Lesen der Antwort (S-013, #45)“ mit Attributionszeilen. Fast-Forward von 9cde1ee. **Nicht gepusht.**
- Worktree sauber (`git status --short` ist leer). Keine Übergabedateien im Repo.

## Geänderte Dateien (`git diff --stat origin/agent/master/20261023-01..HEAD`)
```
 app/schnapper/ebay.py | 20 +++++++++++++++++++-
 docs/EBAY.md          |  1 +
 tests/test_ebay.py    | 43 ++++++++++++++++++++++++++++++++++++++++---
 3 files changed, 60 insertions(+), 4 deletions(-)
```
Nichts unter `.github/workflows`, `team/`, `app/schnapper/web/` oder `__main__.py`.

## Umsetzung
- `ebay.py`, nur `_anfrage`: `frist = time.monotonic() + timeout` direkt vor `opener.open()`. Dann folgt eine Leseschleife mit `antwort.read1(min(64*1024, MAX_ANTWORT_BYTES + 1 - gelesen))`. Sie endet bei `b""` oder wenn `gelesen > MAX_ANTWORT_BYTES`. Nach jedem Stück wird die Frist geprüft. Bei Überschreitung wird ein Merker gesetzt, und **außerhalb** von try/with folgt `raise EbayFehler("eBay antwortet zu langsam (Zeitlimit {timeout:g} s überschritten)")`. Deshalb sind `__cause__` und `__context__` None, und der Text enthält weder URL noch Token noch Kopfzeilen. Ein Kommentar zum schlimmsten Fall (timeout + 1 Socket-Timeout) steht an der Stelle. Die Prüfungen für Größe und JSON sind unverändert.
- `tests/test_ebay.py`: `import itertools`. Die Attrappe `Antwort` hat jetzt einen Lesezeiger (`pos`), `read(n)` und `read1(n)` liefern fortlaufend, optional mit Stückgröße `stueck`, und einen Zähler `read1_aufrufe`. Zwei neue Tests:
  - `test_gesamtzeitlimit_tropfende_antwort`: 1 Byte pro `read1`, gepatchte Uhr `ebay.time.monotonic` (+1 s je Aufruf), `timeout=5`. Erwartet wird `EbayFehler` mit „Zeitlimit“ und „5 s“, höchstens 10 `read1`-Aufrufe (tatsächlich 6), Antwort nicht vollständig gelesen, `__cause__` None, keine URL, kein Host, kein Basic-Wert und kein Geheimnis im Text.
  - `test_schnelle_antwort_innerhalb_frist`: dieselbe Antwort in 1-Byte-Stücken ergibt `{"a": 1}` (49 `read1`-Aufrufe). Zusätzlich wird eine Antwort von 200 000 Byte aus mehreren 64-KiB-Stücken korrekt zusammengesetzt.
- `docs/EBAY.md`: 1 neue Tabellenzeile `eBay antwortet zu langsam (Zeitlimit …)`, Bedeutung: Antwort dauert insgesamt länger als 15 s (z. B. tröpfelnd).

## Testergebnisse
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest tests.test_ebay -v` | Ran 40 tests, OK, 0 Skips (vorher 38, also +2) |
| `python3 -m unittest tests.test_ebay_cli -v` | Ran 11 tests, OK |
| `python3 -m unittest discover -s tests` | Ran 267 tests, OK (vorher 265) |
| `cd cloudflare && node --test test/*.test.mjs` | tests 10, pass 10, fail 0 |
| Offline: `unshare -rn` + nur Loopback hochgefahren (Skript `scratchpad/lo_up.py`), `discover` | Ran 267 tests, OK |
| `tropf.py` (lokaler Server 127.0.0.1, 20 Byte je 0,3 s, timeout=0.5) | jetzt `EbayFehler: eBay antwortet zu langsam (Zeitlimit 0.5 s überschritten)` nach real 0,74 s (vorher 6,0 s mit Erfolg) |

Hinweis zum Offline-Lauf: Mit reinem `unshare -rn` ist Loopback abgeschaltet. Dann scheitern 26 Tests (2 FAIL, 24 ERROR), nämlich Web-, Server- und Team-Tests, die einen lokalen 127.0.0.1-Server brauchen (ENETUNREACH). Das betrifft weder eBay noch die Änderung: `tests.test_ebay` + `tests.test_ebay_cli` laufen auch dort grün (51 OK). Mit Loopback an und ohne externes Netz sind alle 267 Tests grün.

## Gegenprobe / Mutation
- Mutation: `if time.monotonic() > frist:` geändert zu `if False and time.monotonic() > frist:`.
- Ergebnis: `FAIL: test_gesamtzeitlimit_tropfende_antwort`, Ran 40, FAILED (failures=1). Der neue Test erkennt die Mutation also.
- Zurückgesetzt mit `git checkout -- app/schnapper/ebay.py`. `git diff --exit-code` ist leer. sha256 im Worktree `45064d2c7c01496a30526a93b8c0f81cbfeffc83ac6add5b015b381e2adee250` ist gleich `git show HEAD:app/schnapper/ebay.py | sha256sum`. Danach sind die Tests wieder grün (51 OK bzw. 267 OK).

## Secret-Scan
- `git diff HEAD~1..HEAD` (mein Commit): 0 Treffer.
- `git diff origin/main...HEAD`: 1 Treffer mit dem einfachen Muster, aber ein Fehlalarm. Es ist die Zeile `self.assertIsNone(re.search(r"sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY", text))` aus einem älteren Branch-Commit (ecad218), also ein Testmuster und kein Geheimnis. Mit strengem Muster (`sk-ant-[A-Za-z0-9]`, `ghp_` + 20 Zeichen, `AKIA[A-Z0-9]{16}`, `BEGIN … PRIVATE KEY`) gibt es 0 Treffer.
- ZENTNA, JERRY AL und Beatmaster wurden nicht berührt. Kein externer Netzaufruf, nur Mocks und 127.0.0.1.

## Offene Punkte
- Push auf `agent/master/20261023-01` (Fast-Forward 9cde1ee..e035a29) durch COMMAND nach dem CHECK.
- Der Secret-Scan von AK 10 mit dem einfachen Muster trifft das Testmuster aus ecad218. CHECK sollte das als Fehlalarm werten oder das strenge Muster verwenden.
- Der CHECK-Hinweis zu F1 Fall C (TypeError statt Assertion) bleibt weiter offen und ist nachrangig.
- Mögliche Härtung für später: `read1` hält die Frist nur, wenn jeder einzelne Socket-Lesevorgang unter dem Socket-Timeout bleibt. Die Header-Phase in `opener.open()` ist durch die Frist nicht begrenzt, weil Header-Zeilen ebenfalls tröpfeln können. Das liegt außerhalb dieses Auftrags.
