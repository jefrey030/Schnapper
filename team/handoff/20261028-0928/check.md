# CHECK – Lauf 20261028-0928 (UTC)

## Urteil: **bestanden**

Unabhängig geprüft im Klon /home/claude/schnapper, Branch `agent/master/20261023-01`, Python 3.13.18, Node v22.23.4.

## 1. Historie und Diff
- `git log --oneline origin/agent/master/20261023-01..agent/master/20261023-01` ergibt genau einen Commit: `31b52d4 SCHNAPPER MASTER: F6 eBay – kaputte URL in _anfrage als EbayGesperrt (S-013)`.
- Kette: 31b52d4 → 31677d0 (= origin/agent/master/20261023-01) → ecad218 → 6dbe114 (= origin/main). `merge-base --is-ancestor` bestätigt, dass ein Fast-Forward möglich ist und origin/main Vorfahr ist. Es gibt keinen Merge-Commit, kein Rebase und kein Amend. Die Attributionszeilen sind vorhanden.
- `git diff origin/main...agent/master/20261023-01 --stat`: ebay.py +381, docs/EBAY.md +79, tests/test_ebay.py +548 (der ganze PR #45).
- Neuer Commit: nur `app/schnapper/ebay.py` (+5/−1) und `tests/test_ebay.py` (+17).
  - In ebay.py steht `urlsplit(url)` jetzt in einem eigenen `try`. Bei `except ValueError` folgt `raise EbayGesperrt(<bestehende Allowlist-Meldung, wortgleich mit Z. 256/257>) from None`. Sonst ist nichts geändert.
  - In test_ebay.py gibt es den neuen Test `AnfrageTests.test_kaputte_url_gesperrt` mit drei subTests.
- `git status` ist leer.

## 2. Testläufe (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest -v tests.test_ebay.AnfrageTests.test_kaputte_url_gesperrt` | Ran 1, OK |
| `python3 -m unittest -v tests.test_ebay` | Ran 36, OK, 0 skipped |
| `python3 -m unittest discover -s tests` | Ran 252, OK |
| `cd cloudflare && node --test test/*.test.mjs` | 10 tests, 10 pass, 0 fail, 0 skipped |

## 3. Gegenprobe (selbst)
Den Stand HEAD habe ich per `git archive` in die Scratch-Kopie `/tmp/claude-0/-home-claude-schnapper/1d687d9a-1f8f-5613-8160-df7b64595919/scratchpad/gegenprobe` gelegt. Dort habe ich `app/schnapper/ebay.py` durch `git show origin/agent/master/20261023-01:app/schnapper/ebay.py` ersetzt (per diff verifiziert).
- Einzeltest: **FAILED (errors=3)**. Ursache: 2× `ValueError: Invalid IPv6 URL`, 1× `ValueError: netloc 'api.ebay.com＃@evil.example' contains invalid characters under NFKC normalization`.
- Ganze eBay-Suite alt: Ran 36, FAILED (errors=3). Es scheitert also nur der neue Test.
- Der Arbeitsbaum im Klon blieb unberührt, `git status` ist danach leer.

## 4. Scans
- Secrets: Im Diff von 31b52d4 gibt es keine Treffer für `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token=`.
- Tabu-Begriffe (ZENTNA, JERRY AL/Jerry-AL, Beatmaster): keine Treffer.
- Pfade: nur ebay.py und test_ebay.py. Nichts unter `.github/`, `team/tasks.json` und `app/schnapper/web/` sind unverändert. `docs/EBAY.md` hat der Commit nicht angefasst.
- Netz: Der neue Test patcht `_oeffner` (`side_effect=AssertionError`) und `OpenerDirector.open`. Die Basisklasse `OhneNetz` sperrt `socket.create_connection` u. a. Im Diff kommen kein `urlopen`, keine Sockets und kein `requests` vor.

## 5. Akzeptanzkriterien
1. **erfüllt.** `_anfrage("GET", "https://[::1/identity/v1/oauth2/token", {}, None)` wirft `EbayGesperrt`. Das habe ich direkt geprüft, `isinstance(e, ValueError)` ist False.
2. **erfüllt.** `https://api.ebay.com]/…` (POST) und die NFKC-URL (GET) werfen beide `EbayGesperrt`. Direkt geprüft und im Test abgedeckt.
3. **erfüllt.** Die Meldung lautet in allen drei Fällen exakt „Nur Token- und Suchendpunkt auf https://api.ebay.com bzw. https://api.sandbox.ebay.com sind erlaubt“. `__cause__` ist None und `__suppress_context__` ist True. Der Test prüft `ohne_geheimnis`, „evil“ und die URL.
4. **erfüllt.** `_oeffner` ist mit AssertionError gepatcht und wird nicht erreicht. Die Exception entsteht vor `urllib.request.Request`.
5. **erfüllt.** `test_host_allowlist` (inkl. `:99999`/`:abc`) und `test_erlaubt_mit_port_443_und_timeout` sind grün. Der Port-, http-, Userinfo- und Allowlist-Pfad ist unverändert. Stichprobe: alle vier ergeben `EbayGesperrt` wie zuvor.
6. **erfüllt.** Die Gegenprobe in Abschnitt 3 scheitert mit dem alten Code, mit dem Fix ist sie OK.
7. **erfüllt.** tests.test_ebay: 36 OK, 0 Fehler, 0 skipped.
8. **erfüllt.** discover: 252 OK.
9. **erfüllt.** Node: 10/10.
10. **erfüllt.** Siehe Abschnitt 4.
11. **erfüllt.** Die Historie ist linear auf 31677d0, ein Fast-Forward ist möglich, nichts ist gepusht.

## 6. Adversariale Prüfung
- **Keine anderen Ausnahmen verschluckt.** Im neuen `try` steht nur `urlsplit`. Gefangen wird nur `ValueError`, keine weiteren Typen.
- **Allowlist-Verhalten unverändert.** Die Port-Prüfung, die Bedingung, die Meldung und der Ablauf nach der Prüfung sind identisch. Gültige URLs laufen weiter durch.
- **Das Brain-Protokoll stimmt mit dem Ist-Zustand überein.** Commit-Hash, Dateien, Zahlen und Gegenprobe-Fehlertexte decken sich.
- Anmerkungen, nicht blockierend:
  - Die Meldung ist jetzt zweimal im Code dupliziert. Eine Konstante wäre schöner, LEAD hat aber bewusst minimalen Umfang verlangt.
  - Bei einer Nicht-String-URL (z. B. `123`) wirft `urlsplit` weiterhin `AttributeError` statt `EbayGesperrt`. Das war vorher genauso und ist nicht Teil des Auftrags. Im Produktivpfad ist es unerreichbar, weil die URLs aus Konstanten kommen. Optional könnte ein späterer Lauf das härten.
  - Erreichbarkeit im Produktivpfad: gering, wie LEAD schreibt. Die Änderung ist eine Härtung und Vertragstreue.

## Empfehlung an COMMAND
Fast-Forward-Push von 31b52d4 auf `origin/agent/master/20261023-01` (PR #45).
