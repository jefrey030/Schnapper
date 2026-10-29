# CHECK – Lauf 20261029-1028 (UTC)

Start: Thu Oct 29 10:37:49 UTC 2026 · Ende: Thu Oct 29 10:39:00 UTC 2026 (beide per `date -u`)

Geprüfter Commit: `e035a29691a4393166ab80bad1ae39c301c8956c` auf lokalem `agent/master/20261023-01`. Basis: `origin/agent/master/20261023-01` = `9cde1eea9871614da189918f8a123e3bb200f2c4`, origin/main = `6dbe114271b332ed9d4c282b50c4ce02b112ac49`.
Die Umsetzung habe ich unabhängig geprüft, Code wurde nicht geändert, nichts committet und nichts gepusht.

## Testzahlen (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest tests.test_ebay -v` | Ran 40, OK, 0 Skips. Vorher 38 `def test_` in origin, jetzt 40, also +2 |
| `python3 -m unittest tests.test_ebay_cli` | Ran 11, OK |
| `python3 -m unittest discover -s tests` | Ran 267, OK |
| `cd cloudflare && node --test test/*.test.mjs` | tests 10, pass 10, fail 0, skipped 0 |
| `unshare -rn` → `tests.test_ebay tests.test_ebay_cli` | Ran 51, OK |
| `unshare -rn` + nur Loopback (`lo_up.py`) → `discover` | Ran 267, OK |

## Codeprüfung (Diff 9cde1ee..e035a29)
- `frist = time.monotonic() + timeout` steht vor `open()`. Die Leseschleife nutzt `read1(min(64 KiB, MAX+1-gelesen))` und endet bei `b""`, bei `gelesen > MAX` oder bei überschrittener Frist. `roh` wird per `join` gebildet. Die Logik ist korrekt.
- Der Raise erfolgt außerhalb von try/with. Damit sind `__cause__` und `__context__` None. Der Text lautet `eBay antwortet zu langsam (Zeitlimit {timeout:g} s überschritten)` und enthält keine URL, kein Token und keine Kopfzeile.
- Größenprüfung („zu groß“) und JSON-Prüfung sind unverändert und kommen nach der Fristprüfung. Die Reihenfolge ist sinnvoll.
- Eine Regression ist nicht erkennbar. Die Testattrappe `read()` liefert jetzt fortlaufend, alle alten Tests sind grün. `http.client.HTTPResponse.read1` gibt es seit Python 3.5, der echte Pfad funktioniert also (Beleg: tropf.py, siehe unten).

## Akzeptanzkriterien
1. **erfüllt.** `git diff --stat origin/agent/master/20261023-01..HEAD` zeigt nur `app/schnapper/ebay.py` (+19/−1, nur `_anfrage`), `docs/EBAY.md` (+1) und `tests/test_ebay.py` (+40/−3). Nichts unter `.github/workflows`, `team/`, `web/` oder `__main__.py`.
2. **erfüllt.** `test_gesamtzeitlimit_tropfende_antwort` läuft über den echten `_anfrage` mit gepatchtem `_oeffner`, 1 Byte je `read1` und einer Uhr, die um +1 s weiterläuft. Geprüft werden „Zeitlimit“, „5 s“, `read1` ≤ 10, `__cause__` None, kein GUT-URL, kein Host, kein BASIS64 und kein Geheimnis (`ohne_geheimnis`). Der Test ist grün.
3. **erfüllt.** `test_schnelle_antwort_innerhalb_frist`: 48 Stücke zu je 1 Byte ergeben `{"a": 1}`, 200 000 Byte in mehreren 64-KiB-Stücken werden korrekt zusammengesetzt. `test_groessenlimit_und_json` (2 000 001 Byte ergeben „zu groß“) und die JSON-Fehlertests sind unverändert grün.
4. **erfüllt (selbst durchgeführt).** Mutation A: Block `if time.monotonic() > frist: …` entfernt, Ergebnis `FAIL: test_gesamtzeitlimit_tropfende_antwort`, Ran 40, FAILED (failures=1). Mutation B: `if zu_langsam: raise …` entfernt, ebenfalls FAIL. Danach `git checkout -- .`. sha256 von `ebay.py` = `45064d2c7c01496a30526a93b8c0f81cbfeffc83ac6add5b015b381e2adee250`, gleich `git show HEAD:app/schnapper/ebay.py | sha256sum`. `git diff --exit-code` ist leer, `git status --short` ist leer, der Test ist wieder OK.
5. **erfüllt.** Das Skript `tropf.py` gelesen: nur 127.0.0.1, harmlos. Mit dem neuen Code endet es mit `EbayFehler: eBay antwortet zu langsam (Zeitlimit 0.5 s überschritten)` nach real 0,748 s. Laut LEAD waren es vorher 6,0 s mit Erfolg.
6. **erfüllt.** test_ebay hat 40 Tests, OK, 0 Skips (+2). test_ebay_cli hat 11 Tests, OK.
7. **erfüllt.** discover: 267 Tests, OK.
8. **erfüllt.** node: 10 pass, 0 fail.
9. **erfüllt.** `OhneNetz` patcht `socket.create_connection`. Die URLs in test_ebay.py sind nur Datenstrings. Der Offline-Lauf (`unshare -rn`, nur Loopback) ist grün. Ohne Loopback scheitern laut BRAIN Web-, Server- und Team-Tests, weil sie 127.0.0.1 brauchen. Das betrifft die eBay-Tests nicht, die habe ich ohne Loopback selbst grün gesehen (51 OK).
10. **erfüllt.** Im neuen Diff gibt es 0 Treffer (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw/Passwort/password). Bei `origin/main...HEAD` gibt es 1 Treffer mit dem einfachen Muster, nämlich die Regex-Zeile `re.search(r"sk-ant-|ghp_|…")` im Test aus ecad218. Das ist ein Fehlalarm. Das strenge Muster ergibt 0 Treffer. ZENTNA, JERRY AL, Beatmaster und `.github/workflows` kommen weder in den Pfaden noch im Inhalt vor (0 Treffer).
11. **erfüllt (Stand jetzt).** Nichts gepusht, der lokale Branch steht 1 Commit vor origin. `git merge-base --is-ancestor origin/agent/master/20261023-01 HEAD` ergibt 0, ein Fast-Forward ist also möglich. origin/main ist enthalten. Kein Merge, kein Force. Die Commit-Nachricht und die Attributionszeilen stimmen.

## Hinweise (nicht blockierend)
- Die Header-Phase in `open()` ist durch die Frist nicht begrenzt. Ein Server, der die Statuszeile oder die Header tröpfelt, wird weiterhin nur pro Socket-Operation begrenzt. Das ist außerhalb des Auftrags, eine spätere Härtung wäre z. B. ein Socket-Deadline-Wrapper.
- Kommt das letzte Stück knapp nach der Frist an, wird auch eine vollständige Antwort als „Zeitlimit“ abgewiesen. Das ist akzeptabel und konservativ.
- Der offene Punkt F1 Fall C (TypeError statt Assertion) bleibt nachrangig offen.

## Urteil: **bestanden**
