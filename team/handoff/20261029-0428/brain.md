# BRAIN – Lauf 20261029-0428 (UTC) – F6 / S-013 / PR #45

Branch `agent/master/20261023-01`, Ausgang d1a9eef → Commit **9cde1eea9871614da189918f8a123e3bb200f2c4** (lokal, NICHT gepusht). Klon steht wieder auf `main`.

## Geänderte Dateien (git diff --numstat d1a9eef..HEAD)
| Datei | + | - |
|---|---|---|
| app/schnapper/ebay.py | 4 | 1 |
| tests/test_ebay.py | 31 | 2 |
| tests/test_ebay_cli.py | 17 | 0 |

Nur erlaubte Dateien. Nichts unter .github/, docs/, team/, __main__.py.

## Umsetzung
1. `ebay.py`: `import re`; in `_token` ersetzt `not token.strip()` durch `not re.fullmatch(r"[\x21-\x7e]+", token)` → `EbayFehler("Token-Antwort unbrauchbar")`, kein Wert, `_token_wert` bleibt ungesetzt, kein `.strip()`.
2. `ebay.py`, `_anfrage`: nach `except urllib.error.HTTPError`, vor `except OSError`: `except ValueError: raise EbayFehler("Anfrage an eBay ungültig (Kopfzeile)") from None`. JSON-Auswertung unverändert.
3. Tests:
   - **A** `OAuthTests.test_token_antwort_unbrauchbar`: 5 neue subTests (`TOKEN+"\nX-Evil: 1"`, `TOKEN+"\r\n"`, `"TEST TOKEN"`, `"TÖKEN"`, `"\t"`), zusätzlich Prüfung `_token_wert` leer; 1 Transportaufruf.
   - **A2** `OAuthTests.test_token_ebay_zeichen_angenommen` (neu): `TEST-TOKEN-abc` und `v^1.1#i^1#r^0#p^1#I^3#f^0#t^H4sI...==` werden angenommen, POST+GET, Bearer-Kopf exakt (AK 2).
   - **B** `AnfrageTests.test_ungueltige_kopfzeile_wird_ebayfehler` (neu): echter `_anfrage`/Opener/http.client, Socket per OhneNetz gesperrt, Kopf `Bearer TOKEN\nX: 1` → `EbayFehler` mit exakt „Anfrage an eBay ungültig (Kopfzeile)“, `__cause__` None, `ohne_geheimnis`, keine Ausgabe.
   - **C** `EbayKommandozeileTests.test_token_mit_zeilenumbruch` (neu): `main(["--ebay","fahrrad"])` mit VOLL-Umgebung, gemocktes `_anfrage` liefert Token mit `\n` → Exit 3, stderr beginnt mit `eBay: `, enthält „Token-Antwort unbrauchbar“, keinen Token/ID/Secret, nur 1 Aufruf (POST).

## Testergebnisse (eigener Lauf)
- `python3 -m unittest discover -s tests`: **Ran 265 tests, OK** (vorher 262; +3 neue Testmethoden, + 5 subTests in A).
- `python3 -m unittest tests.test_ebay tests.test_ebay_cli`: **49 Tests, OK**.
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass, 0 fail**.
- `python3 -I $SP/repro45.py <klon>/app`: **`EbayFehler | Token-Antwort unbrauchbar`** (vorher `ValueError | ... GEHEIMTOKEN ...`).
- `git merge-base --is-ancestor origin/main HEAD` → Exit 0 (enthaelt-main).
- Secret-Scan (grep nach api_key/secret/password/ghp_/sk- auf `+`-Zeilen des Diffs): leer. Nur erfundene Testwerte.

## Gegenprobe
- **(a)** Regex in `_token` zurück auf `not token.strip()`: **FAILED (failures=5)** – A rot in 4 subTests (`\nX-Evil`, `\r\n`, Leerzeichen, `TÖKEN`; `"\t"` bleibt durch `.strip()` ohnehin abgewiesen) sowie C rot.
- **(b)** `except ValueError` in `_anfrage` entfernt: **FAILED (errors=1)** – B rot mit `ValueError: Invalid header value b'Bearer TEST-TOKEN-abc\nX: 1'`.
- Danach jeweils zurückgesetzt; Wiederholung → OK, `git status` sauber.

## Hinweis
`_oeffner()` nutzt `build_opener` mit Standard-ProxyHandler; Test B funktioniert mit und ohne HTTPS_PROXY, da `putheader` vor jedem Verbindungsaufbau validiert.
