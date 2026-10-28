# BRAIN-Bericht – Lauf 20261028-0828

## Branch
`agent/master/20261023-01` (lokal, Tracking `origin/agent/master/20261023-01`). Basis ecad218, `git merge --no-edit origin/main` gab „Already up to date“.
**Nicht gepusht.** Lokal 1 Commit vor origin.

## Commit
`31677d0` – „SCHNAPPER MASTER: F6 eBay – zu tiefes JSON und zu lange Zahlen als EbayFehler (S-013)“, mit Co-Authored-By- und Claude-Session-Zeile.

## Geänderte Dateien (2 Dateien, +16/−1)
- `app/schnapper/ebay.py` (+1/−1): In `_anfrage()` wird `except (json.JSONDecodeError, UnicodeDecodeError)` zu `except (ValueError, RecursionError)`. Meldung „eBay-Antwort ist kein gültiges JSON/UTF-8“ und `from None` bleiben gleich.
- `tests/test_ebay.py` (+15): neuer Test `test_json_zu_tief_oder_zu_lange_zahl` in derselben Klasse wie `test_groessenlimit_und_json`. Zwei subTests mit den Körpern `b"[" * 100_000` und `b"1" * 5000`, beide mit Mock-Opener (`Antwort`, `mock.patch.object(ebay, "_oeffner")`), ohne Netz. Der Test prüft:
  - Ausnahme ist `EbayFehler`
  - Meldungstext exakt wie bisher
  - `__cause__ is None` und `__suppress_context__` (also `from None`)
  - `ohne_geheimnis`
  - zusätzlich der Weg über den Helfer `self.fehler(...)` mit „JSON“

`docs/EBAY.md` ist nicht geändert. Nach der Korrektur stimmt „kein gültiges JSON“ auch für diese Fälle (AK 10: keine Doku-Änderung nötig).

## Eigene Testergebnisse
- Gegenprobe ohne den Fix (ebay.py per stash zurückgesetzt): `tests.test_ebay` hat 35 Tests, **FAILED (errors=2)**. Der neue Test erkennt die Lücke also.
- Mit Fix: `python3 -m unittest -v tests.test_ebay` hat **35/35 OK**, 0 skipped (vorher 34).
- `python3 -m unittest discover -s tests` hat **251 Tests OK** (vorher 250), 0 Fehler.
- `cd cloudflare && node --test test/*.test.mjs` ergab **10 tests, 10 pass, 0 fail, 0 skipped**.
- `git grep` nach Secret-Mustern in app/tests/docs: nur 1 Treffer, `tests/test_ebay.py:527`. Das ist das schon vorhandene Prüf-Regex im Test selbst, kein Secret.
- `git diff --stat origin/agent/master/20261023-01`: nur die beiden erlaubten Dateien.

## Offene Punkte
- Push (nur Fast-Forward auf `agent/master/20261023-01`) steht aus und ist Sache von LEAD/Jefrey. PR #45 bleibt Draft.
- Den optionalen Ende-zu-Ende-Test über `EbayAdapter.lade()` (AK 6) habe ich nicht eigens geschrieben. Laut lead.md reicht der direkte Test von `_anfrage`.
- Ein breiteres `ValueError` fängt jetzt auch andere `ValueError` aus `json.loads`/`decode` ab. Das ist gewollt und zeigt dieselbe Meldung.
