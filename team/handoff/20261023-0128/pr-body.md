## Zusammenfassung
F6 = **S-013 „eBay vorbereiten“**: Dieser PR enthält einen Adapter für die eBay Browse API (`EbayAdapter`). Die Anmeldung läuft über OAuth Client-Credentials, Standard ist die **Sandbox**. Die Quelle bleibt **gesperrt**, bis der Schalter `SCHNAPPER_EBAY_FREIGABE=ja` gesetzt ist und beide Zugangsdaten vorhanden sind. Das Standard-Register ändert sich nicht, `ebay` steht dort weiter auf `SPAETER`.

## Geänderte Dateien (alle neu, 972 Zeilen)
- `app/schnapper/ebay.py` (377): `EbayAdapter`, `_anfrage`, `zeilen_aus_antwort`, `EbayGesperrt(QuelleGesperrt)`, `EbayFehler`
- `tests/test_ebay.py` (516): 34 Tests
- `docs/EBAY.md` (79): Laienanleitung mit Entwicklerkonto, Sandbox-Keyset, Umgebungsvariablen und Fehlerbildern

Nicht geändert: `quellen.py`, `adapter.py`, `team/`, `.github/`, `cloudflare/`, `README.md`.

## Testergebnisse
- `python3 -m unittest discover -s tests`: **Ran 250 tests, OK** (216 Basis + 34 neu, 0 skipped). Vor dem Push erneut gelaufen, wieder 250 OK.
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**, 0 fail.
- Secret-Scan des Diffs: Es gibt nur zwei harmlose Treffer, nämlich den Platzhalter `<deine-Cert-ID>` in der Doku und das Suchmuster im Doku-Test.
- CHECK-Urteil: **bestanden**. Alle 23 Akzeptanzkriterien sind erfüllt.

## Sicherheitsmerkmale
- **Ohne Schalter oder Schlüssel gesperrt.** Die Sperre wird vor jedem Token- oder Netzaufruf geprüft. Fehlermeldungen nennen nur die Variablennamen und nie Werte.
- **Sandbox ist Standard.** Produktion wird nur genutzt, wenn `SCHNAPPER_EBAY_PRODUKTION` genau den Wert `ja` hat.
- **Host-Allowlist.** Erlaubt sind nur `api.sandbox.ebay.com` und `api.ebay.com`, und zwar nur über https, auf Port 443, ohne userinfo, mit exaktem Pfad und mit der Methode GET/POST.
- **Keine Weiterleitungen.** Ein 302 wird zum Fehler, und es gibt keinen zweiten Request.
- Timeout 15 s. Antworten sind auf 2 000 000 Bytes begrenzt, das Limit wird schon beim Lesen geprüft. Kaputtes JSON und Nicht-UTF-8 werden abgefangen.
- **Token nur im Speicher.** Er wird nicht auf Platte geschrieben und läuft automatisch ab und wird erneuert. Zugangsdaten stehen nie in URLs.
- Keine Geheimnisse in Meldungen und `repr`. Das Modul enthält kein `print` und kein `logging`, HTTP-Fehler werden ohne Exception-Kette (`from None`) erzeugt.
- Es kommt nur die Standardbibliothek zum Einsatz. Die Ergebnisse laufen über `lies_text`/`Angebot.aus_dict` (EUR, https, Preisgrenzen) und sind auf 50 begrenzt.
- In den Tests sind alle Netzwege gepatcht (`socket.create_connection`, `socket.socket.connect`, `OpenerDirector.open`).

## Wichtige Hinweise
- **Mit echten eBay-Sandbox-Schlüsseln ungetestet.** Es liegen keine vor. Alle Tests verwenden simulierte Antworten.
- **Für die Produktivnutzung braucht es eine Genehmigung von eBay. Das entscheidet Jefrey.**

## Folgepunkte
- Den Platzhalter `adapter.EbayAdapter` ersetzen oder auf `ebay.EbayAdapter` umleiten (Re-Export).
- CLI/Web-Anbindung des eBay-Adapters.
- `_anfrage` wirft bei einer syntaktisch kaputten URL (z. B. `https://[::1/…`) einen `ValueError` aus `urlsplit` statt `EbayGesperrt`. Dabei gibt es keinen Netzaufruf, und die URLs werden nur intern gebaut. Optional in `EbayGesperrt` umwandeln.
- `team/tasks.json`: S-013 nach dem Merge von #36 auf `review`/`done` setzen.
- Sandbox-Test mit echten Schlüsseln, sobald Jefrey sie gemäß `docs/EBAY.md` als Umgebungsvariablen angelegt hat.

🤖 Generated with [Claude Code](https://claude.com/claude-code)

https://claude.ai/code/session_01BiSgSJgzLa7GunSXoaUcaX
