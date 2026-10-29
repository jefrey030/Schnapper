# LEAD – Lauf 20261029-0428 (UTC)

## Aufgabe
- F-Punkt: **F6 = S-013** eBay vorbereiten (Browse-API-Adapter, gesperrt ohne Schlüssel, Sandbox-Standard, docs/EBAY.md)
- PR: **#45** (Draft), Branch `agent/master/20261023-01`
- Ausgangskopf: `d1a9eefd50179687d16bfc93e306d8f475d4b1b2` (d1a9eef)
- Wahlgrund (faire Rotation laut INDEX.md): F6 zuletzt 20261028-1929. Danach kamen F4 (2328), F3 (0029), F5 (0128), F2 (0229) und F1 (0328) dran. F6 ist damit am längsten unberührt. #50 bleibt auf Halt.
- Branch enthält origin/main 6dbe114: `git merge-base --is-ancestor origin/main origin/agent/master/20261023-01` liefert Exit 0. Ein Merge ist nicht nötig.

## Mangel (belegt): Token kann über eine ValueError-Meldung nach außen gelangen
Zusage in `docs/EBAY.md:57` und `:88` sowie im Modul-Docstring `app/schnapper/ebay.py:8`: Meldungen enthalten nie Client ID, Secret oder Token.

Ursache:
- `app/schnapper/ebay.py:350-352` (`_token`): Geprüft wird nur, ob `access_token` ein nicht-leerer `str` ist. Steuerzeichen wie `\n` oder `\r` werden nicht abgewiesen.
- `app/schnapper/ebay.py:371` setzt den Token ungeprüft in die Kopfzeile `Authorization: Bearer <token>`.
- `app/schnapper/ebay.py:259-274` (`_anfrage`) fängt nur `HTTPError` und `OSError`. `http.client.putheader` wirft bei einem ungültigen Kopfzeilenwert `ValueError('Invalid header value %r')`, **mit dem kompletten Wert**. Das passiert noch vor jedem Verbindungsaufbau. `urllib`'s `do_open` fängt nur `OSError`, also läuft der ValueError roh nach außen.
- `app/schnapper/__main__.py` (Diff, Zweig `elif a.ebay`) fängt `ValueError` und gibt `eBay: {exc}` auf stderr aus. Der Token landet so im Terminal oder Log.

Reproduktion ohne Netz (Socket blockiert; der Fehler entsteht vor dem Verbindungsaufbau):
```
SP=/tmp/claude-0/-home-claude-schnapper/21a9fcf0-278c-523b-893d-946439a89370/scratchpad
python3 -I $SP/repro45.py $SP/lead45/app
# Ausgabe: ValueError | Invalid header value b'Bearer GEHEIMTOKEN\nX-Evil: 1'
```
(`$SP/lead45` = `git archive` von d1a9eef. `repro45.py` blockiert `socket.create_connection`, `socket.socket.connect` und `getaddrinfo`. Der Transport liefert bei POST `{"access_token": "GEHEIMTOKEN\nX-Evil: 1", "expires_in": 7200}` und reicht GET an das echte `ebay._anfrage` weiter.)

Bestehende Tests decken das nicht ab. `tests/test_ebay.py:252-262` (`test_token_antwort_unbrauchbar`) prüft nur `{}`, `""`, fehlendes oder ungültiges `expires_in`, Zahl und Liste, aber keinen Token mit Steuerzeichen oder Nicht-ASCII.

## Umsetzungsvorgabe (BRAIN)
1. **`app/schnapper/ebay.py`, `_token`:** Den Token zusätzlich mit `re.fullmatch(r"[\x21-\x7e]+", token)` prüfen, also nur druckbares ASCII ohne Leerzeichen. Dafür `import re` ergänzen. Passt der Token nicht, `EbayFehler("Token-Antwort unbrauchbar")` werfen, mit genau demselben Text wie heute und ohne den Wert. `self._token_wert` darf in diesem Fall nicht gesetzt werden. Der Token wird nicht mehr per `.strip()` verändert; der heutige Ausdruck `not token.strip()` darf in der neuen Prüfung aufgehen.
2. **`app/schnapper/ebay.py`, `_anfrage`:** Als Absicherung im `try` um `_oeffner().open(...)` zusätzlich `except ValueError:` fangen und `raise EbayFehler("Anfrage an eBay ungültig (Kopfzeile)") from None` werfen, ohne den Text der Ausnahme. Den Block nach dem bestehenden `except urllib.error.HTTPError` und vor oder nach `except OSError` setzen. Die JSON-Auswertung am Ende (Zeile 277-280) bleibt unverändert.
3. **`tests/test_ebay.py`:** Neue Tests in den bestehenden Klassen, alle über `OhneNetz` (Socket gesperrt):
   - **A** (in `OAuthTests`): Tokens `TOKEN+"\nX-Evil: 1"`, `TOKEN+"\r\n"`, `"TEST TOKEN"` (Leerzeichen), `"TÖKEN"` (Nicht-ASCII) und `"\t"` lösen jeweils `EbayFehler` mit „Token-Antwort unbrauchbar“ aus. `ohne_geheimnis` greift, und es gibt genau 1 Transportaufruf (kein GET). Am einfachsten ergänzt man diese Werte als zusätzliche subTests in `test_token_antwort_unbrauchbar`.
   - **B** (in `AnfrageTests`): Der echte `_anfrage`-Pfad mit `self.KOPF` plus einer Kopfzeile, deren Wert `\n` enthält, z. B. `{"Authorization": "Bearer " + TOKEN + "\nX: 1"}`. Ein Opener wird nicht gemockt, damit der echte `http.client` validiert; der Socket bleibt durch `OhneNetz` gesperrt. Erwartet: `EbayFehler` (kein `ValueError`, kein `AssertionError`), `ohne_geheimnis` greift, und die Meldung enthält `TOKEN` nicht.
   - **C** (in `tests/test_ebay_cli.py`, falls dort ein gemockter Transport-Weg existiert; sonst entfällt C): `main(["--ebay", "x"])` mit Freigabe-Umgebung und einem Transport, der einen Token mit `\n` liefert. Erwartet: Exit 3, stderr beginnt mit `eBay: ` und enthält den Token nicht.
4. Keine weiteren Änderungen: kein Umbau, keine neuen Konstanten außer bei echtem Bedarf.

## Erlaubte Dateien
- `app/schnapper/ebay.py`
- `tests/test_ebay.py`
- `tests/test_ebay_cli.py` (nur für Test C)

Nicht erlaubt: `app/schnapper/__main__.py`, `docs/`, `team/`, `.github/`, alle anderen Dateien.

## Akzeptanzkriterien
1. Ein Token mit `\n`, `\r`, Leerzeichen, Tab oder Nicht-ASCII führt in `lade()` zu `EbayFehler("Token-Antwort unbrauchbar")`. Es folgt kein GET-Aufruf und kein Token-Cache.
2. Gültige Tokens wie bisher (z. B. `TEST-TOKEN-abc` und eBay-typische Zeichen wie `v^1.1#i^1#r^0#p^1#I^3#f^0#t^H4sI...=`) werden weiter angenommen, und die bestehenden OAuth-Tests bleiben grün.
3. Ein `ValueError` aus `_oeffner().open(...)` wird in `_anfrage` zu `EbayFehler`. Die Meldung enthält weder den Kopfzeilenwert noch ein Element aus `GEHEIM`.
4. Die Reproduktion `python3 -I $SP/repro45.py <Arbeitsklon>/app` gibt `EbayFehler | Token-Antwort unbrauchbar` aus und nicht mehr `ValueError | ... GEHEIMTOKEN ...`.
5. Kein Test öffnet eine echte Verbindung (OhneNetz-Sperre aktiv, kein Zugriff auf eBay oder Open Prices).
6. Die Gesamtsuite ist grün. Python: vorher 262 laut letztem F6-Lauf, nachher entsprechend mehr. Cloudflare 10/10.
7. Gegenprobe: Wird der neue Regex-Check in `_token` zurückgenommen, wird mindestens Test A rot. Wird das neue `except ValueError` in `_anfrage` zurückgenommen, wird Test B rot. Danach jeweils zurücksetzen.
8. Der Diff gegen d1a9eef berührt nur erlaubte Dateien. Secret-Scan über den Diff ist leer, nichts unter `.github/`, kein Force-Push.
9. Der Branch enthält weiterhin origin/main (`merge-base --is-ancestor` liefert Exit 0).

## Testbefehle
```
cd <Arbeitsklon>   # Branch agent/master/20261023-01
python3 -m unittest discover -s tests
python3 -m unittest tests.test_ebay tests.test_ebay_cli -v
python3 -m unittest tests.test_ebay.OAuthTests tests.test_ebay.AnfrageTests -v
cd cloudflare && node --test test/*.test.mjs
python3 -I /tmp/claude-0/-home-claude-schnapper/21a9fcf0-278c-523b-893d-946439a89370/scratchpad/repro45.py "$PWD/app"
git diff --stat d1a9eef..HEAD
git merge-base --is-ancestor origin/main HEAD && echo enthaelt-main
```

## Hinweis Gegenprobe (CHECK)
CHECK führt die Gegenproben selbst aus und setzt danach mit `git checkout -- app/schnapper/ebay.py` zurück:
- (a) Nur den Regex-Check in `_token` entfernen: Test A muss rot werden.
- (b) Nur `except ValueError` in `_anfrage` entfernen: Test B muss rot werden, als `ValueError` statt `EbayFehler`.

Zusätzlich prüft CHECK, dass `repro45.py` gegen den neuen Stand keinen Token mehr ausgibt. Am Ende muss `git status` sauber sein.

## Weitere Beobachtung (nicht Teil dieses Laufs)
Auf main bricht `python -m schnapper ""` mit dem Fehler „entweder DATEI oder …“ ab (`bool("")`). Auf #45 fällt derselbe Aufruf in `lies_datei("")` („Nur .json oder .csv …“, Exit 2). Das Verhalten hat sich also leicht geändert, ist aber harmlos. Es ist ein möglicher Kandidat für einen späteren F6-Lauf.
