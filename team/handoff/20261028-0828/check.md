# CHECK-Bericht – Lauf 20261028-0828

## Urteil: **bestanden**

Geprüft: Branch `agent/master/20261023-01`, lokaler Commit `31677d0`, 1 Commit vor `origin/agent/master/20261023-01` (ecad218), nicht gepusht, 0 hinter `origin/main`. Python 3.13.18.

## Diff dieses Laufs (`git diff origin/agent/master/20261023-01..HEAD`)
- `app/schnapper/ebay.py` (+1/−1): `except (json.JSONDecodeError, UnicodeDecodeError)` wird zu `except (ValueError, RecursionError)`. Meldung und `from None` sind unverändert.
- `tests/test_ebay.py` (+15): neuer Test `AnfrageTests.test_json_zu_tief_oder_zu_lange_zahl`. Er hat 2 subTests und nutzt Mock-Opener und `Antwort`.
- Sonst keine Dateien geändert. `git diff origin/main...HEAD --stat` zeigt für den ganzen PR nur `ebay.py`, `docs/EBAY.md` und `tests/test_ebay.py`.
- Commit-Nachricht enthält die Zeilen Co-Authored-By und Claude-Session.

## Testzahlen (selbst ausgeführt)

| Lauf | Basis origin (ecad218) | Mit Fix (31677d0) |
|---|---|---|
| `python3 -m unittest discover -s tests` | 250 OK | **251 OK**, 0 Fehler |
| `python3 -m unittest -v tests.test_ebay` | 34 OK | **35 OK**, 0 skipped |
| `cd cloudflare && node --test test/*.test.mjs` | – | **10 tests, 10 pass**, 0 fail, 0 skipped |

**Gegenprobe:** Ich habe `ebay.py` per `git show origin/...:app/schnapper/ebay.py` auf den alten Stand gesetzt und den neuen Test behalten. Ergebnis: `tests.test_ebay` mit 35 Tests endet **FAILED (errors=2)**:
- `RecursionError: maximum recursion depth exceeded while decoding a JSON array`
- `ValueError: Exceeds the limit (4300 digits)`

Danach habe ich mit `git checkout -- app/schnapper/ebay.py` wiederhergestellt. `git status` meldet „nothing to commit, working tree clean“. Der Test erkennt die Lücke also.

**Ende-zu-Ende (zusätzlich, nur Scratch-Skript außerhalb des Repos):** `EbayAdapter("x", umgebung=env(), transport=ebay._anfrage).lade()` mit gemocktem `_oeffner`. Der Opener liefert erst eine Token-Antwort, dann den kaputten Körper. Socket-Verbindungen sind verboten. Für beide Körper entsteht `EbayFehler: eBay-Antwort ist kein gültiges JSON/UTF-8`, mit 2 Opener-Aufrufen.

## Sicherheit / Sperren
- Secret-Scan im Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw): **keine Treffer**. Ein `git grep` über app/tests/docs liefert nur das vorhandene Prüf-Regex in `tests/test_ebay.py:527`, kein Secret.
- Tabu-Begriffe (ZENTNA, JERRY AL, Beatmaster): keine Treffer.
- `.github/`: keine Änderung, weder im Lauf-Diff noch im PR-Diff.
- Kein Netz: Der neue Test läuft in `AnfrageTests(OhneNetz)`. Dort lösen `socket.create_connection` und `socket.connect` einen AssertionError aus, und `_oeffner` ist gemockt. Im Diff gibt es kein urlopen, kein socket und keine http-URL.

## Akzeptanzkriterien
1. **erfüllt.** `b"[" * 100000` ergibt `EbayFehler` mit der Meldung „…kein gültiges JSON/UTF-8“ (Test, Gegenprobe zeigt vorher RecursionError).
2. **erfüllt.** `b"1" * 5000` ergibt `EbayFehler` mit „JSON“ in der Meldung (Test, Gegenprobe zeigt vorher ValueError).
3. **erfüllt.** `test_groessenlimit_und_json` (Zeilen 435–440) ist unverändert und grün. Die Fälle „zu groß“, `{kaputt` mit JSON, `\xff` mit UTF-8 und das knapp unter dem Limit gelieferte JSON laufen weiter. Der Meldungstext ist identisch, der neue Test prüft ihn mit `assertEqual`.
4. **erfüllt.** `from None` ist im Code erhalten. Der Test prüft `__cause__ is None` und `__suppress_context__`, dazu `ohne_geheimnis` direkt und über `self.fehler(...)`.
5. **erfüllt.** Der neue Test `test_json_zu_tief_oder_zu_lange_zahl` steht in derselben Klasse und nutzt den `Antwort`-Mock, ohne Netz und ohne socket.
6. **erfüllt.** Abgedeckt ist die zulässige Variante „direkter Test von `_anfrage`“. Den Weg über `lade()` habe ich zusätzlich selbst nachgeprüft (siehe oben). Im Repo gibt es dafür keinen eigenen Test.
7. **erfüllt.** 35 Tests (mindestens 34 gefordert), OK, 0 skipped.
8. **erfüllt.** discover 251 OK (vorher 250), Node 10/10 pass.
9. **erfüllt.** Nur `app/schnapper/ebay.py` und `tests/test_ebay.py` sind geändert, beide erlaubt. Keine Secrets, keine Tabu-Begriffe.
10. **erfüllt.** Keine Doku-Änderung nötig: `docs/EBAY.md:71` „kein gültiges JSON“ und die Zusage im PR-Body treffen jetzt zu.

## Anmerkungen (nicht blockierend)
- `assertNotIsInstance(cm.exception, (RecursionError, AssertionError))` ist redundant, weil `assertRaises(EbayFehler)` den Typ schon sicherstellt. Es schadet aber nicht.
- Das breitere `except ValueError` deckt nur `roh.decode` und `json.loads` ab. Fremde Fehler werden dadurch nicht verdeckt. Das ist vertretbar.
- Die Kommentarmarke „AK 11 (S-013 Nachtrag)“ im Test bezieht sich auf die S-013-Nummerierung, nicht auf die AK dieses Laufs. Das ist nur kosmetisch.
- Push (nur Fast-Forward) steht noch aus. PR #45 bleibt Draft, die Merge-Entscheidung trifft Jefrey.

## Endzustand Klon
Branch `agent/master/20261023-01` auf `31677d0`, Arbeitsbaum sauber. Der temporäre Worktree im Scratchpad ist entfernt (`git worktree list` zeigt nur den Hauptklon).
