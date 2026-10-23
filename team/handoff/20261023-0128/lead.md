# LEAD-Plan – Lauf 20261023-0128

## Gewählte Aufgabe
**F6 = S-013 „eBay vorbereiten“**: `app/schnapper/ebay.py` (EbayAdapter für die eBay Browse API, OAuth Client-Credentials, Sandbox als Standard, Quelle gesperrt bis Schalter + Zugangsdaten), `tests/test_ebay.py`, `docs/EBAY.md`.

## Begründung
- Die Team-Draft-PRs #36, #39, #40, #41 und #44 decken F1–F5 ab. CHECK hat jeweils „bestanden“ gemeldet. Laut Preflight und letztem Bericht fehlt dort nichts, also gibt es keinen PR, den man fortsetzen müsste.
- Eine Aufgabe mit Status „open“ ist nur S-013. Sie steht in `team/tasks.json` auf dem Branch `origin/agent/master/20261022-20` (PR #36). Auf main fehlt sie, weil tasks.json in main veraltet ist.
- Jefrey hat F6 am 22.10.2026 freigegeben. Kosten 0 €. Es werden keine echten Schlüssel gebraucht, alle Tests laufen mit simulierten Antworten.

## Branch
`agent/master/20261023-01`, neu von `origin/main` @ 6dbe114. Vor dem Start `git fetch origin main` ausführen und bei neuerem main von dort abzweigen.

## Erlaubte Dateien (sonst nichts)
| Datei | Art |
| --- | --- |
| `app/schnapper/ebay.py` | neu |
| `tests/test_ebay.py` | neu |
| `docs/EBAY.md` | neu |
| `app/schnapper/quellen.py` | **nur falls zwingend nötig**, höchstens den `hinweis`-Text der Zeile `Quelle("ebay", …)`. Die Entscheidung `SPAETER` bleibt. Empfehlung: gar nicht ändern (siehe unten). |

**Tabu:**
- `team/tasks.json` und `team/STATUS.md`
- `.github/workflows/*`
- `README.md`
- `app/schnapper/adapter.py`, `__main__.py`, `web.py`
- `cloudflare/*`
- alles von ZENTNA, JERRY AL und Beatmaster
- fremde PRs/Branches

## Bestehende Schnittstellen (zu nutzen, nicht zu ändern)

### `app/schnapper/quellen.py`
- `Register`, `Quelle(kennung, name, entscheidung, hinweis)` und die Konstanten `ERLAUBT`, `SPAETER`, `AUSGESCHLOSSEN`.
- `Register.pruefe(kennung)` gibt `None` (frei) oder einen Grund zurück. `Register.get(kennung)`.
- In `STANDARD` steht `ebay` schon auf `SPAETER` („noch gesperrt“). Das bleibt so.

### `app/schnapper/openprices.py`: Vorlage, Muster 1:1 übernehmen
- Hostkonstanten, eigene Ausnahmen (`OpenPricesGesperrt` für Sperren, `OpenPricesFehler` für Antwort- und Netzfehler).
- `_abruf(url, timeout=15.0)` mit folgenden Prüfungen:
  - scheme `https`, exakter `hostname`, Port `None`/443 (ein ungültiger Port ist gesperrt), keine userinfo, exakter Pfad
  - `KeineWeiterleitung(HTTPRedirectHandler)`, bei dem `redirect_request` `None` zurückgibt
  - `opener.open(req, timeout=…)`, `status == 200`, `read(LIMIT+1)` und Prüfung auf `> LIMIT`
  - `json.loads` mit Abfangen von `JSONDecodeError`/`UnicodeDecodeError`
  - `OSError` wird zu `…Fehler`
- `OpenPricesAdapter.__init__(…, register=None, abruf=None, umgebung=None)`: `abruf` und `umgebung` sind für Tests injizierbar, `umgebung` ist standardmäßig `os.environ`.
- `_freigegebenes_register()`: Der Schalter hebt `SPAETER` → `ERLAUBT` **nur in einer Kopie** des Registers. `AUSGESCHLOSSEN` wird nie aufgehoben, das Standard-Register bleibt unverändert.
- `sperrgrund()` gibt `str | None` zurück.
- `lade()`: Sperre prüfen → Abruf → `zeilen_aus_antwort(...)` gibt `(zeilen, hinweise)` zurück → `lies_text(json.dumps(zeilen), "json", self._freigegebenes_register())`.
- `_preis()` lehnt bool, NaN/Inf und Werte außerhalb von 0,005 bis 1 000 000 ab. Das in ebay.py nachbauen und **keine** privaten Funktionen aus openprices importieren.

### `app/schnapper/einlesen.py`
`lies_text(text, format, register=None, jetzt=None) -> Importergebnis` mit `.angebote` und `.fehler`. Es prüft jede Zeile über `Angebot.aus_dict` und lässt nur freigegebene Quellen zu.

### `app/schnapper/angebot.py`
Rohzeilen-Schlüssel für `Angebot.aus_dict`:
- Pflichtfelder: `id`, `titel`, `preis`, `url`, `quelle`, `erfasst_am`
- optionale Felder: `waehrung` (nur `EUR`!), `versand`, `zustand` aus `ZUSTAENDE = ("neu","wie_neu","gebraucht","defekt","unbekannt")`, `referenzpreis` (leer oder größer 0), `kategorie`
- Unbekannte Schlüssel landen in `extra`.

`pruefe()` erzwingt:
- https-URL ohne Zugangsdaten
- Titel mit höchstens 300 Zeichen
- 0 < Preis ≤ 1 000 000
- keinen Zeitpunkt in der Zukunft

### `app/schnapper/adapter.py`
- `QuelleGesperrt(RuntimeError)`
- `finde(adapter, …)` ruft `adapter.lade()` auf und arbeitet mit dem Ergebnis weiter.
- Der bestehende Platzhalter `adapter.EbayAdapter` mit `FREIGABE_VARIABLE = "SCHNAPPER_EBAY_FREIGABE"` **bleibt in diesem PR unverändert**, weil die Datei nicht freigegeben ist. Die bestehenden Tests in `tests/test_abgleich_s004_s005.py` (T4) und `tests/test_app_quellen_web.py::Adapter` hängen daran und müssen grün bleiben.
- Den Platzhalter durch einen Re-Export zu ersetzen, ist ein eigener Folgepunkt. Den bitte im PR-Text nennen.

## Umsetzungshinweise `app/schnapper/ebay.py`
1. **Nur Standardbibliothek**:
   - `base64`, `datetime`, `json`, `os`, `re`, `time`
   - `urllib.parse`, `urllib.request`
   - `decimal`
2. **Konstanten**:
   - `SANDBOX_HOST = "api.sandbox.ebay.com"`, `PRODUKTION_HOST = "api.ebay.com"`, `ERLAUBTE_HOSTS = frozenset({SANDBOX_HOST, PRODUKTION_HOST})`
   - `TOKEN_PFAD = "/identity/v1/oauth2/token"`, `SUCH_PFAD = "/buy/browse/v1/item_summary/search"`
   - `SCOPE = "https://api.ebay.com/oauth/api_scope"`. Das ist der Scope-Bezeichner für Sandbox und Produktion. Er ist kein Ziel-Host.
   - `MARKTPLATZ = "EBAY_DE"`, `MAX_ERGEBNISSE = 50`, `MAX_ANTWORT_BYTES = 2_000_000`, `TIMEOUT = 15.0`
   - `FREIGABE_VARIABLE = "SCHNAPPER_EBAY_FREIGABE"`. Gleicher Name wie in adapter.py, als Literal definieren. adapter.py importiert ebay.py nicht.
   - `PRODUKTION_VARIABLE = "SCHNAPPER_EBAY_PRODUKTION"`
   - `ID_VARIABLE = "SCHNAPPER_EBAY_CLIENT_ID"`, `SECRET_VARIABLE = "SCHNAPPER_EBAY_CLIENT_SECRET"`
3. **Ausnahmen**:
   - `class EbayGesperrt(QuelleGesperrt)`. Import aus `.adapter` ist erlaubt, es gibt keinen Zirkelimport, weil adapter.py ebay.py nicht importiert.
   - `class EbayFehler(RuntimeError)`
4. **`EbayAdapter(suchbegriff, register=None, umgebung=None, transport=None, jetzt=None, limit=MAX_ERGEBNISSE)`**, `kennung = "ebay"`:
   - Der Suchbegriff wird getrimmt und muss 1 bis 100 Zeichen lang sein, sonst `ValueError`. `limit` muss zwischen 1 und 50 liegen. Beides wird sofort im Konstruktor geprüft, wie `anfrage_url` bei OpenPrices.
   - `umgebung` ist standardmäßig `os.environ`.
   - `transport(methode, url, kopfzeilen, daten) -> dict` ist für Tests injizierbar. Standard ist die Modulfunktion `_anfrage`.
   - `umgebung_name()` gibt `"produktion"` zurück, wenn `umgebung.get(PRODUKTION_VARIABLE) == "ja"`, sonst `"sandbox"`.
   - `host()` liefert den passenden Host.
   - **`sperrgrund() -> str | None`** prüft in dieser Reihenfolge und **ohne Netz**:
     - (a) Register-Eintrag fehlt oder ist `AUSGESCHLOSSEN` → Grund aus `register.pruefe`
     - (b) `FREIGABE_VARIABLE != "ja"` → Grund nennt den Variablennamen
     - (c) `CLIENT_ID` oder `CLIENT_SECRET` fehlt oder ist leer bzw. nur Leerzeichen → Grund nennt **nur die Variablennamen, nie Werte**
     - (d) sonst `self._freigegebenes_register().pruefe("ebay")`, nach dem Muster von OpenPrices
   - **`lade()`**:
     - Bei einem Sperrgrund `EbayGesperrt` auslösen, **bevor** `transport` aufgerufen wird.
     - Sonst `token = self._token()` und Suche per GET auf `https://{host}{SUCH_PFAD}?q=…&limit=…&filter=deliveryCountry:DE,priceCurrency:EUR`. Kopfzeilen: `Authorization: Bearer <token>`, `X-EBAY-C-MARKETPLACE-ID: EBAY_DE`, `Accept: application/json`, `Accept-Language: de-DE`.
     - Danach `zeilen_aus_antwort(antwort, umgebung, jetzt)` aufrufen und `lies_text(json.dumps(zeilen), "json", self._freigegebenes_register(), jetzt=…)` zurückgeben. Übersprungene Einträge stehen in `self.hinweise`.
   - **`_token()`**:
     - POST auf `https://{host}{TOKEN_PFAD}` mit den Kopfzeilen `Authorization: Basic base64(id:secret)` und `Content-Type: application/x-www-form-urlencoded`.
     - Body: `grant_type=client_credentials&scope=<SCOPE urlencodiert>`.
     - Aus der Antwort `access_token` (nicht leerer str) und `expires_in` (int > 0) lesen, sonst `EbayFehler("Token-Antwort unbrauchbar")`.
     - Den Token nur im Arbeitsspeicher der Instanz cachen, bis `expires_in - 60` s abgelaufen sind. **Nie auf Platte schreiben.**
5. **`_anfrage(methode, url, kopfzeilen, daten=None, timeout=TIMEOUT) -> dict`** (Modulfunktion, wie `openprices._abruf`):
   - Methode nur `GET`/`POST`.
   - `urlsplit`: scheme `https`, `hostname in ERLAUBTE_HOSTS` (exakter Vergleich, kein `endswith`), Port `None`/443 (ein ungültiger Port ist gesperrt), keine userinfo, Pfad exakt `TOKEN_PFAD` oder `SUCH_PFAD`. Sonst `EbayGesperrt`.
   - Opener mit Weiterleitungs-Blocker (eigener `HTTPRedirectHandler`, bei dem `redirect_request` `None` liefert). Ein 3xx wird damit zu einem Fehler und nie verfolgt.
   - `timeout` wird an `opener.open` übergeben.
   - `read(MAX_ANTWORT_BYTES + 1)` mit Größenprüfung, dann `json.loads`. UTF-8- und JSON-Fehler werden zu `EbayFehler`.
   - `HTTPError`:
     - aus dem Body höchstens 64 KB lesen
     - aus `{"errors":[{"errorId","message"}]}` die erste `errorId`/`message` holen, gekürzt auf 200 Zeichen
     - Meldung `f"eBay HTTP {code}: …"`
     - Bei 401/403 am Token-Endpunkt einen klaren Hinweis „Zugangsdaten ungültig oder falscher Modus (Sandbox/Produktion)?“ ausgeben
   - Andere `OSError` werden zu `EbayFehler("eBay nicht erreichbar: …")`.
   - **Keine** Fehlermeldung, kein `repr` und kein `print` enthält Client-ID, Secret, Basic-Header oder Token.
   - Keine Ausgabe auf stdout/stderr, kein `logging` der Kopfzeilen.
6. **`zeilen_aus_antwort(antwort, umgebung="sandbox", jetzt=None) -> (zeilen, hinweise)`** bildet Browse-`item_summary` auf Rohzeilen ab. Der Aufbau folgt der dokumentierten eBay-Struktur, die Werte in den Tests sind erfunden.
   - Fehlt `itemSummaries`, gilt das als leere Trefferliste ohne Fehler. Ist die Antwort kein dict, oder ist `itemSummaries` vorhanden, aber keine Liste, dann `EbayFehler`.
   - Höchstens `MAX_ERGEBNISSE` Einträge verarbeiten, bei mehr einen Hinweis ausgeben.
   - Pro Eintrag:
     - `itemId` muss ein nicht leerer str sein → `id = "ebay-" + itemId`, Länge begrenzen.
     - `titel = title`, auf 300 Zeichen gekürzt. In der Sandbox kommt das Präfix `"SANDBOX "` davor, damit Testdaten nie wie echte Angebote aussehen.
     - `price.value`/`price.currency`: nur `EUR`, sonst überspringen und einen Hinweis ausgeben. Der Wert wird über einen eigenen `_preis()` wie bei OpenPrices geprüft.
     - `versand` ist das kleinste `shippingOptions[].shippingCost.value` mit currency `EUR`. Ohne Angabe gilt `"0"` plus `extra` `"versand_unbekannt": True`.
     - `referenzpreis` ist `marketingPrice.originalPrice.value` (EUR), aber nur, wenn größer als der Preis, sonst `""`.
     - `url = itemWebUrl`: nur `https`, Hostname ist `ebay.de`, `ebay.com` oder endet auf `.ebay.de`/`.ebay.com`. Sonst überspringen.
     - `zustand` wird über `conditionId` zugeordnet:
       - `1000` → `neu`
       - `1500`, `2000`–`2990` → `wie_neu`
       - `3000`–`6000` → `gebraucht`
       - `7000` → `defekt`
       - alles andere → `unbekannt`
     - `quelle = "ebay"`
     - `erfasst_am = jetzt` (Abrufzeit, UTC, ISO)
     - `kategorie` ist `categories[0].categoryName`, wenn es ein str ist
     - zusätzlich in `extra`: `"kaufoptionen": buyingOptions` (z. B. AUCTION, Gebot statt Festpreis), `"umgebung": "sandbox"|"produktion"`, `"hinweis_quelle": "Daten: eBay Browse API"`
   - Unbrauchbare Einträge werden nur übersprungen und gemeldet. Sie brechen nie den ganzen Abruf ab.
7. **`quellen.py`**: Empfehlung ist, die Datei nicht zu ändern. Die Sperre ergibt sich aus `SPAETER` und der Kopie im Stil von `_freigegebenes_register` (wie bei OpenPrices). Falls doch, dann nur den `hinweis`-Text um „Schalter SCHNAPPER_EBAY_FREIGABE=ja + Zugangsdaten nötig“ ergänzen. `test_openprices.RegisterTests.test_schalter_gibt_nur_diese_quelle_frei` muss grün bleiben.
8. **Keine CLI- oder Web-Anbindung** in diesem PR. Das ist ein Folgepunkt.

## `docs/EBAY.md` (Deutsch, laienverständlich)
1. Was der Adapter tut und was nicht: Standard ist Sandbox mit Testdaten. Produktion gibt es nur mit Schalter **und** eBay-Genehmigung.
2. Schritt für Schritt:
   - kostenloses Konto unter developer.ebay.com anlegen („Join“, E-Mail bestätigen, Freischaltung kann bis zu einem Werktag dauern)
   - Application Keys → „Sandbox“ → Keyset erzeugen (App ID = Client ID, Cert ID = Client Secret)
   - optional einen Sandbox-Testnutzer anlegen
3. Schlüssel setzen, nur als Umgebungsvariablen, z. B. in Termux für die aktuelle Sitzung: `export SCHNAPPER_EBAY_CLIENT_ID=…`, `export SCHNAPPER_EBAY_CLIENT_SECRET=…`, `export SCHNAPPER_EBAY_FREIGABE=ja`. Deutliche Warnung:
   - **nie** in Dateien des Repos, in Issues/PRs oder in Chats posten
   - nicht in `.bashrc` einchecken
   - bei einem Leck in der Entwicklerkonsole neu erzeugen
4. Produktion:
   - `SCHNAPPER_EBAY_PRODUKTION=ja` mit Produktions-Keyset
   - Hinweis: Die Nutzung der Buy/Browse API in Produktion ist bei eBay eingeschränkt und braucht eine **Genehmigung bzw. Vereinbarung mit eBay** (Application Growth Check / Buy-API-Zugang)
   - Tageslimit von standardmäßig 5 000 Aufrufen
   - Kosten 0 €, aber Genehmigung nötig, und die Entscheidung trifft Jefrey
5. Liste der Variablen in einer Tabelle, Fehlerbilder mit typischen Meldungen und Ursache, und der Satz „Quelle bleibt gesperrt, solange Schalter oder Schlüssel fehlen“.
6. Quellen-Links nur auf `developer.ebay.com` (Browse-Überblick, OAuth Client-Credentials, API-Limits). „Stand 23.10.2026, Inhalte bei eBay prüfen“.

## Akzeptanzkriterien (nummeriert, prüfbar)
1. Der Diff gegenüber `origin/main` enthält nur `app/schnapper/ebay.py`, `tests/test_ebay.py` und `docs/EBAY.md`, plus optional `app/schnapper/quellen.py` (nur hinweis-Text). Prüfung: `git diff --name-only origin/main...HEAD`. Es gibt keine Änderung unter `.github/`, `team/` oder `cloudflare/`.
2. `ebay.py` nutzt nur die Standardbibliothek und importiert keine Drittpakete.
3. **Sperre ohne Netz:** Fehlt `SCHNAPPER_EBAY_FREIGABE=ja`, löst `EbayAdapter(...).lade()` `EbayGesperrt` aus, das zugleich `QuelleGesperrt` ist. Der `transport` wird nicht aufgerufen. `socket.create_connection`, `socket.socket.connect` und `urllib.request.OpenerDirector.open` sind im Test so gepatcht, dass sie einen AssertionError auslösen.
4. **Fehlende Schlüssel:** Mit Schalter `ja`, aber fehlender oder leerer (auch nur aus Leerzeichen bestehender) `CLIENT_ID` oder `CLIENT_SECRET` ist der Adapter gesperrt und macht keinen Netzaufruf (gleiche Patches wie in AK 3). Die Meldung nennt den fehlenden Variablennamen.
5. **Register:** Mit Register-Eintrag `ebay` = `AUSGESCHLOSSEN` bleibt die Sperre auch bei Schalter und Schlüsseln bestehen. `Register().pruefe("ebay")` ist nach dem Laden weiterhin nicht `None`, das Standard-Register bleibt also unverändert. `lies_text` mit `quelle="ebay"` ohne Adapter bleibt „noch gesperrt“, das deckt der bestehende Test ab.
6. **Sandbox-Standard:** Mit Schalter und Schlüsseln, aber ohne `SCHNAPPER_EBAY_PRODUKTION`, gehen alle Transport-URLs an `https://api.sandbox.ebay.com`. Das gilt auch für `PRODUKTION=nein`, `JA` und `1`.
7. **Produktion nur mit Schalter:** Nur `SCHNAPPER_EBAY_PRODUKTION=ja` führt zu `https://api.ebay.com`.
8. **Host-Allowlist:** `_anfrage` lehnt die folgenden URLs mit `EbayGesperrt` ab, **bevor** ein Opener geöffnet wird:
   - `http://api.sandbox.ebay.com/...`
   - `https://api.ebay.com.evil.example/...`
   - `https://evil.example/identity/v1/oauth2/token`
   - `https://www.ebay.com/...`
   - `https://u:p@api.ebay.com/...`
   - Port `:8443` sowie ein ungültiger Port
   - ein fremder Pfad (z. B. `/buy/browse/v1/item/123`)
   - die Methode `DELETE`
   
   Erlaubt sind nur `api.ebay.com` und `api.sandbox.ebay.com`.
9. **Keine Weiterleitungen:** Ein Test belegt, dass der Opener mit einem `HTTPRedirectHandler` gebaut wird, dessen `redirect_request` `None` liefert. Alternativ belegt er, dass eine simulierte 302-Antwort zu `EbayFehler` führt und kein zweiter Request folgt.
10. **Timeout:** `_anfrage` übergibt `timeout` an `OpenerDirector.open`, standardmäßig 15 s. Das wird per Mock geprüft. Ein simulierter `socket.timeout`/`OSError` wird zu `EbayFehler`.
11. **Größenlimit:** Eine simulierte Antwort mit mehr als 2 000 000 Bytes führt zu `EbayFehler("… zu groß")`. Kaputtes JSON oder Nicht-UTF-8 wird zu `EbayFehler`.
12. **OAuth korrekt:** Der Token-Request ist ein POST auf `/identity/v1/oauth2/token` mit `Authorization: Basic base64(id:secret)`, `Content-Type: application/x-www-form-urlencoded`, Body mit `grant_type=client_credentials` und `scope=https://api.ebay.com/oauth/api_scope`. Die Suche ist ein GET auf `/buy/browse/v1/item_summary/search` mit `q`, `limit` ≤ 50, `Authorization: Bearer <token>` und `X-EBAY-C-MARKETPLACE-ID: EBAY_DE`. Die Zugangsdaten stehen nie in der URL.
13. **Gültige Antwort:** Eine simulierte Antwort mit z. B. drei Einträgen wird korrekt abgebildet:
    - neu mit EUR-Versand
    - gebraucht mit `marketingPrice.originalPrice`
    - Auktion
    
    Erwartet wird jeweils `quelle == "ebay"`, die id beginnt mit `ebay-`, Preis, Versand, Referenzpreis und Zustand stimmen, die URL ist https auf einem eBay-Host. In der Sandbox beginnt der Titel mit `SANDBOX `. `finde(adapter, jetzt=…)` liefert Treffer ohne `fehler`.
14. **Unbrauchbare Einträge** werden übersprungen und in `hinweise` gemeldet, ohne Abbruch:
    - Fremdwährung (USD)
    - fehlender oder ungültiger Preis (NaN, bool, negativ)
    - fehlende itemId
    - `itemWebUrl` auf einem Nicht-eBay-Host oder per http
    
    Mehr als 50 Einträge werden auf 50 begrenzt, mit Hinweis. Fehlt `itemSummaries`, ergibt das 0 Treffer ohne Fehler.
15. **Fehlerantworten:**
    - Token-HTTP 401 mit eBay-Fehler-JSON → `EbayFehler` mit Code und gekürzter Meldung
    - Token-Antwort ohne `access_token` → `EbayFehler`
    - Such-HTTP 500 → `EbayFehler`
    
    In keinem Fall gibt es einen Python-Traceback einer anderen Ausnahmeklasse.
16. **Keine Secrets in Meldungen:** Ein Test mit Platzhalterwerten (z. B. `TEST-ID-xyz`/`TEST-SECRET-xyz`) prüft für alle Sperr- und Fehlerfälle (AK 3, 4, 8, 10, 11, 15), dass weder die ID noch das Secret, ihr Base64-Wert oder der Token in `str(exc)` vorkommen. Außerdem ist die gefangene stdout/stderr-Ausgabe leer. Im Modul gibt es kein `print` und kein `logging`.
17. **Token-Cache nur im Speicher:** Zwei `lade()`-Aufrufe derselben Instanz innerhalb der Gültigkeit holen nur einmal einen Token. Es wird keine Datei geschrieben (Test mit gepatchtem `builtins.open` oder Prüfung per Code-Durchsicht).
18. **Eingaben:** Ein leerer Suchbegriff, einer mit mehr als 100 Zeichen und `limit` 0 oder 51 führen schon im Konstruktor zu `ValueError`.
19. **Bestandstests unverändert grün:** `tests/test_abgleich_s004_s005.py` (T4), `tests/test_app_quellen_web.py`, `tests/test_openprices.py` und `tests/test_plan_s002.py`. Kein bestehender Test wird geändert.
20. **Tests ohne Netz:** `tests/test_ebay.py` patcht in einer `setUp`- oder Klassenumgebung `socket.create_connection` und `socket.socket.connect` mit AssertionError. Alle Tests nutzen eine eigene `umgebung`-Dict und lesen weder `os.environ` noch echte Schlüssel.
21. **Doku:** Zu `docs/EBAY.md` gibt es einen kleinen Test in `tests/test_ebay.py`. Er prüft, dass die Datei existiert und dass alle vier Variablennamen, „Sandbox“, „Genehmigung“ und „developer.ebay.com“ darin vorkommen. Außerdem prüft er, dass die Datei nichts enthält, was nach einem Schlüssel aussieht (z. B. keine Zeichenkette nach dem Muster `SBX-` + Hex bzw. `PRD-` + Hex).
22. **Secret-Scan des Diffs:** Treffer für `sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`, `SBX-[0-9a-f]{8}`, `PRD-[0-9a-f]{8}` und `CLIENT_SECRET=<nichtleerer Wert>` darf es nur als Variablennamen oder Platzhalter geben.
23. Alle Tests sind grün: Python ergibt 232 + neue Tests mit OK und 0 skipped (Basis main 216, also 216 + neue), Cloudflare 10/10.

## Testbefehle (exakt)
```bash
cd /home/claude/schnapper
python3 -m unittest discover -s tests
python3 -m unittest tests.test_ebay -v
cd cloudflare && node --test test/*.test.mjs
```

Zusätzliche Prüfungen:
```bash
cd /home/claude/schnapper
git diff --name-only origin/main...HEAD
git diff origin/main...HEAD | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|SBX-[0-9a-f]{8}|PRD-[0-9a-f]{8}' || echo "kein Treffer"
grep -nE 'print\(|logging' app/schnapper/ebay.py || echo "kein print/logging"
```

Hinweis zu AK 23: Die Basis auf main ist **216** Tests. Die 232 aus dem letzten Bericht gelten nur für den Branch von #44. Erwartet wird also 216 + n.

## Hinweise für den PR-Text (COMMAND)
- Draft-PR auf `main`, Titel z. B. „SCHNAPPER MASTER: F6 (S-013) eBay Browse API vorbereiten (Sandbox, gesperrt)“.
- Der PR-Text nennt:
  - „Mit echten Sandbox-Schlüsseln ungetestet: Es liegen keine vor. Alle Tests nutzen simulierte Antworten.“
  - Die Produktivnutzung braucht eine eBay-Genehmigung.
  - Folgepunkte: Platzhalter `adapter.EbayAdapter` ersetzen bzw. umleiten, CLI/Web-Anbindung, tasks.json-Status von S-013 nach dem Merge von #36 auf `review` setzen.
- Abhängigkeit: S-013 steht nur in #36. Ein Konflikt mit #36 ist nicht zu erwarten, weil sich keine Dateien überschneiden.
