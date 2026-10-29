# CHECK – Lauf 20261029-0428 (UTC) – F6 / S-013 / PR #45

**Urteil: bestanden**

Geprüft: lokaler Commit 9cde1eea9871614da189918f8a123e3bb200f2c4 auf `agent/master/20261023-01` (1 Commit vor origin d1a9eef, Fast-Forward, kein Force-Push nötig). Unabhängig ausgeführt, keine Netzaufrufe, kein Code geändert. Klon danach wieder auf `main`, `git status` sauber.

## Diffs
- `git diff origin/agent/master/20261023-01..`: nur `app/schnapper/ebay.py` (+4/-1), `tests/test_ebay.py` (+31/-2), `tests/test_ebay_cli.py` (+17). Inhalt entspricht der Umsetzungsvorgabe: `import re`, Regex `[\x21-\x7e]+` statt `token.strip()`, `except ValueError` zwischen HTTPError und OSError mit `from None`, ohne Ausnahmetext. JSON-Auswertung unverändert.
- `git diff origin/main...`: `__main__.py`, `ebay.py`, `docs/EBAY.md`, `tests/test_ebay.py`, `tests/test_ebay_cli.py`. Das ist der bisherige PR-Umfang; der neue Commit berührt davon nur erlaubte Dateien.

## Akzeptanzkriterien
1. **erfüllt.** `OAuthTests.test_token_antwort_unbrauchbar` hat subTests für `\nX-Evil: 1`, `\r\n`, Leerzeichen, `TÖKEN` und `\t`. Geprüft werden „Token-Antwort unbrauchbar“, `ohne_geheimnis`, genau 1 Transportaufruf (kein GET) und `_token_wert` leer. Alles grün.
2. **erfüllt.** `test_token_ebay_zeichen_angenommen`: `TEST-TOKEN-abc` und `v^1.1#i^1#…==` laufen als POST+GET durch, der Bearer-Kopf ist exakt. Die bestehenden OAuth-Tests bleiben grün.
3. **erfüllt.** `AnfrageTests.test_ungueltige_kopfzeile_wird_ebayfehler` läuft über den echten Opener und http.client. Ergebnis: `EbayFehler("Anfrage an eBay ungültig (Kopfzeile)")`, `__cause__` None, `ohne_geheimnis` (GEHEIM), TOKEN nicht enthalten.
4. **erfüllt.** `python3 -I $SP/repro45.py /home/claude/schnapper/app` gibt `EbayFehler | Token-Antwort unbrauchbar` aus. Zusatz: Mit entferntem Regex greift die zweite Absicherung, die Ausgabe ist dann `EbayFehler | Anfrage an eBay ungültig (Kopfzeile)`, wieder ohne Token.
5. **erfüllt.** Die neuen Tests in test_ebay.py liegen in `OhneNetz`-Klassen. Der CLI-Test nutzt eine gemockte Attrappe, die nur POST erhält. Kein Netz nötig, und die Suite lief offline grün.
6. **erfüllt.** `python3 -m unittest discover -s tests`: Ran 265 tests, OK (vorher 262, +3 Methoden). `tests.test_ebay tests.test_ebay_cli`: 49, OK. Cloudflare `node --test`: 10/10 pass, 0 fail.
7. **erfüllt (eigene Gegenprobe).**
   - (a) Regex zurück auf `not token.strip()`: FAILED (failures=5). Rot werden 4 subTests von A (`\n`, `\r\n`, Leerzeichen, `TÖKEN`) und C (`test_token_mit_zeilenumbruch`). `\t` wird schon durch `.strip()` abgewiesen, das ist erwartbar.
   - (b) `except ValueError` entfernt: FAILED (errors=1). B wird rot mit `ValueError: Invalid header value b'Bearer TEST-TOKEN-abc\nX: 1'`.
   - Danach jeweils `git checkout -- .`. Die Gesamtsuite ist wieder OK, `git status` sauber.
8. **erfüllt.** Der Diff gegen d1a9eef berührt nur erlaubte Dateien. Secret-Scan auf `+`-Zeilen (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw): Im neuen Commit gibt es keine Treffer. Im Gesamtdiff gegen origin/main stehen nur harmlose Treffer: `teile.password is not None` (URL-Prüfung) und ein Test-Assert mit den Suchmustern. Kein `.github/`, kein ZENTNA, JERRY AL oder Beatmaster. Kein Force-Push: origin-Kopf d1a9eef ist Vorfahr von HEAD.
9. **erfüllt.** `git merge-base --is-ancestor origin/main HEAD` liefert Exit 0.

## Anmerkung
Test C (CLI) ist vorhanden und grün. Er wird schon bei Gegenprobe (a) rot und deckt damit den Weg bis zur stderr-Ausgabe ab. Die Beobachtung zu `python -m schnapper ""` aus lead.md ist nicht Teil dieses Laufs und wurde nicht bewertet.
