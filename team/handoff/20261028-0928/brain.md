# BRAIN – Bericht Lauf 20261028-0928 (UTC)

## Arbeitszweig
- Lokal `agent/master/20261023-01`, angelegt von `origin/agent/master/20261023-01` (Kopf 31677d0).
- origin/main = 6dbe114 ist schon Vorfahr. Kein Merge nötig, kein Rebase, kein Amend, **nicht gepusht**.
- Neuer Commit: **31b52d4d183e6f88934b31988deaeb7e22fb6c3e** (Eltern 31677d0, linear, Fast-Forward möglich)
  „SCHNAPPER MASTER: F6 eBay – kaputte URL in _anfrage als EbayGesperrt (S-013)“, mit den vorgegebenen Attributionszeilen.

## Geänderte Dateien (2 Dateien, +22/−1)
- `app/schnapper/ebay.py`: nur der Anfang von `_anfrage()`. `urlsplit(url)` steht jetzt in einem eigenen `try`. Bei `ValueError` folgt `raise EbayGesperrt("Nur Token- und Suchendpunkt auf https://api.ebay.com bzw. https://api.sandbox.ebay.com sind erlaubt") from None`. Die Meldung ist identisch mit der bestehenden und enthält keine URL. Port-Prüfung, Methode, Allowlist, Timeout und JSON-Teil sind unverändert.
- `tests/test_ebay.py`: neuer Test `AnfrageTests.test_kaputte_url_gesperrt` mit drei subTests:
  - `POST https://[::1/identity/v1/oauth2/token`
  - `GET https://api.ebay.com]/buy/browse/v1/item_summary/search`
  - `POST https://api.ebay.com＃@evil.example/identity/v1/oauth2/token` (U+FF03)
  - Der Test prüft `assertRaises(ebay.EbayGesperrt)`, `_oeffner` mit `side_effect=AssertionError` sowie `opener_verboten()`, `__cause__ is None`, `__suppress_context__` True, `ohne_geheimnis` und dass weder „evil“ noch die URL in `str(exc)` stehen.
- `docs/EBAY.md`: unverändert, weil die Meldung dieselbe ist.

## Gegenprobe (Test vor dem Fix, alter Code 31677d0)
`python3 -m unittest -v tests.test_ebay.AnfrageTests.test_kaputte_url_gesperrt` → **FAILED (errors=3)**. Alle drei subTests scheiterten mit rohem `ValueError`:
- 2× `ValueError: Invalid IPv6 URL`
- 1× `ValueError: netloc 'api.ebay.com＃@evil.example' contains invalid characters under NFKC normalization`

Mit dem Fix: **OK** (1 Test).

## Testergebnisse (Python 3.13.18, Node)
- `python3 -m unittest -v tests.test_ebay.AnfrageTests.test_kaputte_url_gesperrt` → Ran 1, OK
- `python3 -m unittest -v tests.test_ebay` → **Ran 36, OK** (vorher 35), 0 Fehler, 0 skipped
- `python3 -m unittest discover -s tests` → **Ran 252, OK** (vorher 251), 0 Fehler, 0 skipped
- `cd cloudflare && node --test test/*.test.mjs` → **10/10 pass**, 0 fail, 0 skipped

## Prüfungen
- Der Diff berührt nur die erlaubten Dateien. Nichts unter `.github/`, `team/tasks.json` ist unverändert, keine Tabu-Begriffe und keine Secrets im Diff (per grep geprüft).
- Kein Netzzugriff: nur Mocks, keine Aufrufe zu eBay oder anderen Preisquellen.

## Offene Punkte
- Push des Commits 31b52d4 auf `origin/agent/master/20261023-01` (PR #45) übernimmt COMMAND nach dem CHECK-Urteil.
- Zurückgestellt laut LEAD: Bericht zu 2666d8b nachtragen (reine Doku).
- Erreichbarkeit im Produktivpfad bleibt gering (URLs kommen aus Konstanten). Der Schritt ist eine Härtung bzw. Vertragstreue, keine akute Lücke.
