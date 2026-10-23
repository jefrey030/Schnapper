# BRAIN-Bericht – Lauf 20261023-0128

## Ergebnis
- Branch: `agent/master/20261023-01` (von origin/main @ 6dbe114), **nicht gepusht**
- Commit: `ecad218` – „SCHNAPPER MASTER: F6 eBay vorbereiten (S-013)“ (Autor jefrey030, Co-Authored-By/Claude-Session-Zeilen am Ende)

## Geänderte Dateien (alle neu)
- `app/schnapper/ebay.py` – EbayAdapter, `_anfrage`, `zeilen_aus_antwort`, `EbayGesperrt(QuelleGesperrt)`, `EbayFehler`
- `tests/test_ebay.py` – 34 Tests
- `docs/EBAY.md` – Laienanleitung
- `quellen.py` **nicht** geändert (Empfehlung befolgt), `adapter.py` unverändert.

## Tests
- `python3 -m unittest discover -s tests`: **Ran 250 tests – OK** (216 Basis + 34 neu, 0 skipped)
- `python3 -m unittest tests.test_ebay`: 34 OK
- `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**, 0 fail, 0 skipped
- `git diff --name-only origin/main...HEAD`: nur die 3 Dateien
- Secret-Scan: einziger Treffer ist das Suchmuster selbst im Doku-Test (Zeile mit `sk-ant-|ghp_|…`); `CLIENT_SECRET=` nur als Platzhalter `<deine-Cert-ID>` in docs/EBAY.md
- `grep print/logging ebay.py`: kein Treffer

## Akzeptanzkriterien
1. Diff nur 3 erlaubte Dateien – geprüft per git diff.
2. Nur Standardbibliothek (+ urllib.error) und Paketmodule – `QuelltextTests` prüft Importliste.
3. Sperre ohne Schalter – `SperreTests.test_ohne_schalter_gesperrt` (socket.create_connection, socket.socket.connect, OpenerDirector.open gepatcht; Transport 0 Aufrufe; isinstance QuelleGesperrt).
4. Fehlende/leere/Leerzeichen-Schlüssel – `test_fehlende_schluessel`, Meldung nennt nur Variablennamen.
5. AUSGESCHLOSSEN und fehlender Register-Eintrag bleiben gesperrt; Standard-Register nach `lade()` weiterhin gesperrt – `test_ausgeschlossen_bleibt_gesperrt`, `test_standardregister_bleibt_unveraendert`.
6./7. Sandbox-Standard (None, nein, JA, 1, " ja", "") bzw. Produktion nur bei `ja` – `UmgebungTests`.
8. Host-Allowlist inkl. http, evil-Suffix, fremder Host, www.ebay.com, userinfo, :8443, :99999, :abc, fremder Pfad, DELETE – `test_host_allowlist` (Opener-Bau verboten).
9. Redirect-Handler liefert None + 302 → EbayFehler, nur ein open-Aufruf – `test_keine_weiterleitung`, `test_302_kein_zweiter_request`.
10. timeout=15.0 Standard an opener.open, socket.timeout/URLError/ConnectionReset → EbayFehler.
11. >2 000 000 Bytes → „zu groß“, kaputtes JSON und Nicht-UTF-8 → EbayFehler.
12. OAuth-POST (Basic, Content-Type, Body grant_type/scope), GET mit q/limit/filter/Bearer/Marketplace-ID/Accept-Language; keine Zugangsdaten in URLs – `test_token_und_suche`, zusätzlich Ende-zu-Ende über echten `_anfrage`-Pfad mit Mock-Opener.
13. Drei Einträge (neu+EUR-Versand min 3.50, gebraucht+originalPrice 60, Auktion conditionId 2500) korrekt; SANDBOX-Präfix; `finde(..., jetzt=)` ohne fehler.
14. USD, fehlender/NaN/bool/negativer Preis, fehlende/leere itemId, fremder Host, Suffix-Trick, http, Nicht-Objekt → 11 Hinweise ohne Abbruch; >50 → 50 + Hinweis; ohne itemSummaries → 0 Treffer.
15. Token 401 mit Fehler-JSON (Code, errorId, auf 200 Zeichen gekürzt, Hinweis Sandbox/Produktion), Token ohne access_token, Suche 500 → EbayFehler.
16. Platzhalter TEST-ID-xyz/TEST-SECRET-xyz, Base64 und Token in keiner Meldung/repr; stdout/stderr leer; kein print/logging im Modul.
17. Zwei `lade()` → ein Token-POST, `builtins.open` gepatcht; Ablauf (expires_in 30) holt neuen Token.
18. Leer, nur Leerzeichen, 101 Zeichen, None, limit 0/51/-1/True/"10" → ValueError.
19. Bestandstests unverändert grün (Gesamtlauf 250 OK).
20. Netz-Patches in setUp der Basisklasse `OhneNetz`; alle Tests mit eigener umgebung-Dict (ein Test prüft os.environ-Default mit `mock.patch.dict(clear=True)`).
21. Doku-Test: Datei, 4 Variablennamen, Sandbox, Genehmigung, developer.ebay.com, Sperr-Satz, keine SBX-/PRD-Hex-Muster, keine echten CLIENT_*=Werte.
22. Secret-Scan siehe oben.
23. 216 + 34 = 250 OK, Cloudflare 10/10.

## Designentscheidungen
- Versandkosten dürfen 0 sein (eigene `_versandkosten`), Preis wie OpenPrices `_preis` (0,005–1 000 000).
- `extra` enthält zusätzlich `waehrung: EUR` als Pflichtfeld-konforme Angabe; `kaufoptionen`, `umgebung`, `hinweis_quelle`, ggf. `versand_unbekannt`.
- HTTPError-Meldungen werden ohne Exception-Kette (`from None`) erzeugt, damit keine Header/Objekte im Traceback landen.
- `__repr__` des Adapters zeigt nur Suchbegriff und Umgebung.

## Offene Punkte / Folgepunkte (für PR-Text)
- Mit echten Sandbox-Schlüsseln ungetestet: Es liegen keine vor. Alle Tests nutzen simulierte Antworten.
- Produktivnutzung braucht eBay-Genehmigung (Entscheidung Jefrey).
- Platzhalter `adapter.EbayAdapter` ersetzen bzw. auf `ebay.EbayAdapter` umleiten.
- CLI/Web-Anbindung.
- tasks.json-Status S-013 nach Merge von #36 auf `review` setzen.
- Kein Push, kein PR erstellt (Aufgabe von COMMAND).
