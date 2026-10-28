# BRAIN – Lauf 20261028-1929

## Ergebnis
- **Commit:** `c09c9dc` auf `agent/master/20261023-01`, direkter Nachfolger von `31b52d4`. Nur lokal committet, **nicht gepusht**. Push und Nachtrag im PR-Body von #45 übernimmt COMMAND.
- **Worktree:** `/tmp/claude-0/-home-claude-schnapper/6542dd57-933c-599a-b9d2-39b95c8e0e81/scratchpad/wt-45`. Er bleibt bis nach dem Push bestehen.

## Geänderte Dateien
- `app/schnapper/__main__.py` (+19/−2)
  - Neue Option `--ebay SUCHBEGRIFF`. Der Hilfetext nennt den Freigabeschalter, die ID- und Secret-Variablen, „Sandbox standardmäßig“ und den Produktionsschalter.
  - `schnapper.ebay` wird erst im `--ebay`-Zweig importiert (lazy).
  - Es muss genau eine Quelle angegeben sein (`DATEI`, `--openprices` oder `--ebay`), sonst `p.error` mit Exit 2.
    - Geprüft wird mit `is not None`. Deshalb führt `--ebay ""` zum Adapter und endet dort mit Exit 3 (AK 5) statt mit Exit 2.
  - `ValueError`, `EbayGesperrt` und `EbayFehler` führen zu Exit 3 mit einer Meldung `eBay: …` auf stderr.
  - `adapter.hinweise` erscheinen als `eBay-Hinweis: …` auf stderr, auch im JSON-Modus.
  - `lizenz = ebay.HINWEIS_QUELLE`.
- `tests/test_ebay_cli.py` (neu, 9 Tests). `tests/test_ebay.py` ist unverändert.
  - In jedem Lauf werfen `socket.create_connection`, `socket.socket.connect` und `urllib.request.OpenerDirector.open` einen AssertionError.
  - Die `SCHNAPPER_EBAY_*`-Variablen werden per `mock.patch.dict` entfernt.
  - `schnapper.ebay._anfrage` wird durch eine Attrappe ersetzt.
  - Abgedeckt sind AK 2 bis 10, mit Prüfung auf Geheimnisse (ID, Secret, Token) in stdout und stderr.
- `docs/EBAY.md` (+16/−1)
  - Der Satz zur fehlenden Anbindung lautet jetzt „Kommandozeile: ja (`--ebay`), Weboberfläche: noch nicht (Folgepunkt)“.
  - Neuer Abschnitt „Sandbox-Test per Kommandozeile“ mit Befehl, `--json`, `SANDBOX `-Präfix, `eBay-Hinweis` und den Exit-Codes 0 und 3.
- Unverändert: `ebay.py`, `adapter.py`, `quellen.py`, `web.py`, `web/`, `.github/`, `team/` (auf dem Branch) und `cloudflare/`.

## Tests (im Worktree)
| Befehl | Ergebnis |
| --- | --- |
| `python3 -m unittest discover -s tests` | 261 Tests OK (252 Bestand + 9 neu), 0 Fehler |
| `python3 -m unittest tests.test_ebay_cli -v` | 9/9 OK |
| `tests.test_ebay`, `tests.test_openprices`, `tests.test_abgleich_s004_s005` und `tests.test_app_quellen_web` zusammen | 91 OK, darunter `x.csv --openprices EAN` weiter grün |
| `cd cloudflare && node --test test/*.test.mjs` | 10/10 pass |
| Rauchtest `env -u SCHNAPPER_EBAY_FREIGABE PYTHONPATH=app python3 -m schnapper --ebay fahrrad` | `eBay: Freigabeschalter SCHNAPPER_EBAY_FREIGABE=ja fehlt …`, exit=3 |
| Secret-Scan des Diffs (`sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`) | leer |

## Gegenprobe (AK 12)
Aufbau: Kopie von `app/` und `tests/`, darin `__main__.py` aus `git show 31b52d4:…`.

Ergebnis: `tests.test_ebay_cli` liefert **FAILED (errors=10)**.
- Ursache: Das Argument `--ebay` ist unbekannt, deshalb kommt SystemExit 2.
- Rot werden 8 Tests; der Test zum ungültigen Suchbegriff zählt mit seinen 3 Untertests dreifach.
- Einzige Ausnahme: `test_genau_eine_quelle` bleibt auch gegen den alten Stand grün, weil ein unbekanntes Argument ebenfalls Exit 2 liefert. Er sichert also nur das Verhalten ab und ist kein Nachweis der neuen Funktion.

## Offene Punkte
- Push (Fast-Forward nach `merge-base --is-ancestor`-Prüfung) und Nachtrag im PR-Body von #45 macht COMMAND. Danach den Worktree entfernen.
- Sandbox-Test mit echten Schlüsseln macht Jefrey selbst: `PYTHONPATH=app python -m schnapper --ebay "fahrrad"`.
- Folgepunkt: Anbindung an die Weboberfläche (bewusst ausgeklammert).

## Nachbesserung Runde 1
- **Commit:** `d1a9eef` auf `agent/master/20261023-01`, neuer Commit direkt nach `c09c9dc` (kein Amend). Nur lokal, **nicht gepusht**.
- **Behoben (N1 aus check.md):**
  - In `app/schnapper/__main__.py` wählt der Zweig jetzt mit `if a.openprices is not None:` statt nach dem Wahrheitswert, passend zur Quellenzählung.
  - Eine leere EAN (`--openprices ""`) wird vorher per `p.error("--openprices braucht eine EAN")` abgewiesen. Das ergibt Exit 2 ohne Traceback, wie vor `c09c9dc`.
  - `"   "` geht weiter an den `OpenPricesAdapter` und endet dort im Exit-3-Pfad.
- **Neuer Test:** `test_openprices_leer_sauberer_fehler` in `tests/test_ebay_cli.py`. Er prüft SystemExit 2, die Meldung und dass kein Traceback kommt.
- **N2** (leere DATEI) ist bewusst unverändert, laut check.md optional.
- **Tests:**
  - `python3 -m unittest discover -s tests`: **262 OK** (261 + 1).
  - `cd cloudflare && node --test test/*.test.mjs`: **10/10 pass**.
  - Rauchtest `PYTHONPATH=app python3 -m schnapper --openprices ""`: `schnapper: error: --openprices braucht eine EAN`, exit=2.
- **Gegenprobe:**
  - Aufbau: Kopie von `app/` und `tests/`, darin `__main__.py` aus `c09c9dc`.
  - Ergebnis `tests.test_ebay_cli`: **FAILED (errors=1)**. Der neue Test schlägt mit genau dem gemeldeten `TypeError … not 'NoneType'` fehl, die übrigen 9 bleiben grün.
  - Die Kopien `gp-n1` und `check-gp` im Scratchpad sind gelöscht.
- Geänderte Dateien: nur `app/schnapper/__main__.py` (+3/−1) und `tests/test_ebay_cli.py` (+9). Worktree sauber.
