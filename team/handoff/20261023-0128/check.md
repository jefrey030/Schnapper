# CHECK-Bericht – Lauf 20261023-0128

**Urteil: bestanden**

Geprüft: Branch `agent/master/20261023-01` @ `ecad218`, Basis `origin/main` @ `6dbe114` (unverändert aktuell). Kein Code geändert, nichts committet oder gepusht, kein Netz.

## Eigene Messungen
- `git diff --stat origin/main...`: 3 neue Dateien, 972 Zeilen hinzugefügt: `app/schnapper/ebay.py` (377), `docs/EBAY.md` (79), `tests/test_ebay.py` (516).
- `python3 -m unittest discover -s tests`: **Ran 250 tests, OK**, 0 skipped. Das sind 216 Basis + 34 neue, `tests.test_ebay -v` zeigt 34× ok.
- `cd cloudflare && node --test test/*.test.mjs`: **tests 10, pass 10, fail 0, skipped 0**.
- Secret-Scan des Diffs (`sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|SBX-hex|PRD-hex|CLIENT_SECRET=`). Es gibt nur 2 Treffer, beide harmlos:
  - `docs/EBAY.md`: `export SCHNAPPER_EBAY_CLIENT_SECRET=<deine-Cert-ID>` (Platzhalter)
  - `tests/test_ebay.py`: das Suchmuster selbst im Doku-Test
- Tabu-Pfade: keine Änderung unter `.github/`, `team/`, `cloudflare/`, `README.md`, `adapter.py`, `quellen.py` und keine Dateien von ZENTNA, JERRY AL oder Beatmaster.
- `grep print(|logging ebay.py`: kein Treffer. Das einzige `open(` ist `_oeffner().open(...)` in `ebay.py:256`.

## Eigene Gegenprobe (Skript im Scratchpad, mit Mock, ohne Netz, Sockets gepatcht)
- Echter `build_opener(_KeineWeiterleitung, FakeHTTPS)`, wobei der Fake-Handler 302 mit `Location: https://evil.example/x` liefert. Ergebnis: `EbayFehler: eBay HTTP 302`. Es gab genau **1** Request, die Weiterleitung wurde nicht verfolgt.
- `read` wird mit `n = 2000001` aufgerufen, also wird das Limit beim Lesen geprüft und nicht erst nach dem kompletten Body. `timeout=15.0` wird an `opener.open` übergeben.
- `https://api.ebay.com./…` (Punkt am Ende) und `…/token/../x` werden mit `EbayGesperrt` abgelehnt.
- Schalter `ja`, ID `TEST-ID-xyz`, Secret nur aus Leerzeichen: Ergebnis ist `EbayGesperrt` (Unterklasse von `QuelleGesperrt`) mit „Zugangsdaten fehlen: SCHNAPPER_EBAY_CLIENT_SECRET“. Der Transport wurde nicht aufgerufen. Das `repr` lautet `EbayAdapter(suchbegriff='x', umgebung='sandbox')` und enthält keine Werte.

## Akzeptanzkriterien
| AK | Ergebnis | Beleg |
| --- | --- | --- |
| 1 | erfüllt | `git diff --name-only` liefert nur `ebay.py`, `EBAY.md` und `test_ebay.py` |
| 2 | erfüllt | `ebay.py:17-29` importiert nur Standardbibliothek und Paketmodule; dazu `QuelltextTests.test_nur_standardbibliothek_kein_print_logging` |
| 3 | erfüllt | `ebay.py:361-364`: die Sperre wird vor `_token`/Transport geprüft. Test `SperreTests.test_ohne_schalter_gesperrt`, Patches in `OhneNetz.setUp` (test_ebay.py:106-119) |
| 4 | erfüllt | `ebay.py:318-330` (strip, nur Namen); Test `test_fehlende_schluessel`; Gegenprobe |
| 5 | erfüllt | `ebay.py:323-325`, 310-316 (Kopie des Registers); Tests `test_ausgeschlossen_bleibt_gesperrt`, `test_standardregister_bleibt_unveraendert` |
| 6/7 | erfüllt | `ebay.py:304-308` (exakter Vergleich `== "ja"`); `UmgebungTests` |
| 8 | erfüllt | `ebay.py:242-253` (exakter Vergleich `hostname in ERLAUBTE_HOSTS`, https, Port, userinfo, Pfad, Methode); `test_host_allowlist` mit `_oeffner` und `OpenerDirector.open` als AssertionError |
| 9 | erfüllt | `ebay.py:210-218` mit eigenem `HTTPRedirectHandler`, `redirect_request` liefert None; Tests `test_keine_weiterleitung`, `test_302_kein_zweiter_request`; Gegenprobe mit echtem Opener |
| 10 | erfüllt | `ebay.py:256`, 268-270; Tests `test_erlaubt_mit_port_443_und_timeout`, `test_timeout_und_oserror` |
| 11 | erfüllt | `ebay.py:259`, 271-276 (`read(LIMIT+1)`); Test `test_groessenlimit_und_json`; Gegenprobe n=2000001 |
| 12 | erfüllt | `ebay.py:333-372`; Tests `test_token_und_suche`, `test_ende_zu_ende_mit_simuliertem_opener` |
| 13 | erfüllt | `zeilen_aus_antwort` in `ebay.py:124-207` (SANDBOX-Präfix, EUR, Versand-Minimum, Referenzpreis > Preis, eBay-Host-Prüfung), danach Validierung über `lies_text`/`Angebot.aus_dict`; Test `test_drei_eintraege` inklusive `finde` |
| 14 | erfüllt | Tests `test_unbrauchbare_eintraege`, `test_mehr_als_50`, `test_ohne_item_summaries` |
| 15 | erfüllt | `ebay.py:260-267`, 221-236 (gekürzt auf 200 Zeichen, Hinweis bei 401/403 am Token-Endpunkt, `from None`); Tests `test_http_fehler_token_401`, `test_http_fehler_suche_500`, `test_token_antwort_unbrauchbar` |
| 16 | erfüllt | `ohne_geheimnis()` prüft `str` und `repr` gegen ID, Secret, Base64 und Token; stdout/stderr leer; kein print/logging |
| 17 | erfüllt | Token liegt nur in Instanzattributen (`ebay.py:349-350`); Tests `test_token_cache_nur_im_speicher` (mit gepatchtem `builtins.open`) und `test_token_abgelaufen` |
| 18 | erfüllt | `ebay.py:286-290`; Test `test_ungueltige_eingaben` |
| 19 | erfüllt | Gesamtlauf mit 250 Tests OK; keine bestehende Testdatei geändert |
| 20 | erfüllt | `OhneNetz.setUp`; die Tests nutzen `env()`-Dicts, `os.environ` nur über `patch.dict(clear=True)` |
| 21 | erfüllt | `DokuTests.test_doku`; `docs/EBAY.md` behandelt das kostenlose Entwicklerkonto, das Sandbox-Keyset (App ID/Cert ID) und die Genehmigung durch eBay für Produktion, außerdem Tageslimit, Variablentabelle, Fehlerbilder, den Sperrsatz und Links nur auf developer.ebay.com |
| 22 | erfüllt | Secret-Scan siehe oben |
| 23 | erfüllt | 250 OK, 0 skipped; Cloudflare 10/10 |

## Hinweise (kein Mangel, nicht blockierend)
- `_anfrage` mit syntaktisch kaputter URL (z. B. `https://[::1/…`) wirft `ValueError` aus `urlsplit` statt `EbayGesperrt`. Es findet trotzdem kein Netzaufruf statt, und die URLs werden nur intern gebaut. Optional in einem Folgepunkt in `EbayGesperrt` umwandeln.
- Ob die Anbindung mit echten Sandbox-Schlüsseln funktioniert, ist ungetestet. Das ist wie vorgesehen im PR-Text zu nennen.
