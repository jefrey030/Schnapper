# CHECK – Lauf 20261028-1929

## Urteil: **nachbessern**

Die Umsetzung erfüllt die Akzeptanzkriterien 1–15. Sie bringt aber eine kleine, ungetestete Regression im Bestand von `--openprices` mit (siehe N1). Die Korrektur ist eine Zeile plus ein Test. Danach ist das Ergebnis aus meiner Sicht „bestanden“.

## Geprüfter Stand
- Worktree: `/tmp/claude-0/-home-claude-schnapper/6542dd57-933c-599a-b9d2-39b95c8e0e81/scratchpad/wt-45`
- Commit: `c09c9dc`, Eltern-Commit `31b52d4` (= `origin/agent/master/20261023-01`). Es ist genau ein Commit. Die Trailer „Co-Authored-By“ und „Claude-Session“ sind vorhanden. Der Worktree ist sauber.

## Belege

| Prüfung | Befehl | Ergebnis |
| --- | --- | --- |
| Python-Gesamtsuite | `python3 -m unittest discover -s tests` | **261 Tests OK** (252 + 9) |
| Cloudflare | `cd cloudflare && node --test test/*.test.mjs` | **10/10 pass**, 0 fail |
| Geänderte Dateien im neuen Commit | `git diff origin/agent/master/20261023-01..agent/master/20261023-01 --stat` | `app/schnapper/__main__.py`, `docs/EBAY.md` und `tests/test_ebay_cli.py` (neu). Alle stehen auf der Erlaubt-Liste, `tests/test_ebay.py` ist unangetastet. |
| Diff gegen main | `git diff origin/main...agent/master/20261023-01 --stat` | 5 Dateien: der PR-Bestand mit `ebay.py`, `test_ebay.py` und `EBAY.md` plus die 3 oben genannten. Keine Dateien unter `.github/`, `team/` oder `cloudflare/`. |
| Secret-Scan | grep nach `sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`, password, token auf den `+`-Zeilen | Keine echten Werte. Die Treffer sind nur die erfundenen Testwerte (`TOK-geheim-xyz`, `ID-geheim-123`, `SECRET-geheim-456`) und Bezeichner wie `TOKEN_PFAD`. |
| Tabu-Pfade | grep -i `zentna`, `jerry`, `beatmaster` im Diff gegen main | leer |
| Ohne Netz | `unshare -rn python3 -m unittest tests.test_ebay_cli tests.test_ebay tests.test_openprices` | 72 Tests OK in einem Netz-Namespace ohne Netz |
| Netzsperre im Test | Code-Review von `lauf()` | `socket.create_connection`, `socket.socket.connect` und `OpenerDirector.open` werfen einen AssertionError. `_anfrage` wird per Attrappe ersetzt, `SCHNAPPER_EBAY_*` per `patch.dict` geleert bzw. entfernt. |
| Rauchtest | `env -u SCHNAPPER_EBAY_FREIGABE … python3 -m schnapper --ebay fahrrad` | `eBay: Freigabeschalter SCHNAPPER_EBAY_FREIGABE=ja fehlt …`, exit=3 |
| Gegenprobe (AK 12) | Kopie von `app/` und `tests/` im Scratchpad (`check-gp`), darin `__main__.py` aus `git show 31b52d4:…`, dann `python3 -m unittest tests.test_ebay_cli` | **FAILED (errors=10)**. Das deckt sich mit dem Bericht. `test_genau_eine_quelle` ist auch gegen den alten Stand grün, wie im Bericht offen angegeben. |

## Akzeptanzkriterien

| AK | Bewertung | Beleg |
| --- | --- | --- |
| 1 | erfüllt | Der Hilfetext nennt FREIGABE, CLIENT_ID, CLIENT_SECRET, „Sandbox standardmäßig“ und PRODUKTION. Der Import steht nur im `elif a.ebay`-Zweig. |
| 2 | erfüllt | `test_genau_eine_quelle` deckt 3 Fälle mit SystemExit 2 ab. Der Bestandstest `x.csv --openprices` ist grün (Gesamtsuite). |
| 3 | erfüllt | `test_ohne_schalter_gesperrt_ohne_netz` prüft rc 3, stdout leer, stderr beginnt mit `eBay: ` und nennt die Variable. Der Rauchtest ergibt exit 3. |
| 4 | erfüllt | `test_schalter_ohne_secret` prüft, dass das Secret genannt wird, ID, Secret und Token aber nicht ausgegeben werden. |
| 5 | erfüllt | `test_ungueltiger_suchbegriff` prüft `""`, `"   "` und 101 Zeichen: rc 3, kein Traceback, 0 Attrappen-Aufrufe. |
| 6 | erfüllt | `test_ebay_fehler` prüft rc 3, `eBay: eBay HTTP 401`, keine Geheimnisse in der Ausgabe. |
| 7 | erfüllt | `test_erfolg_sandbox_text`: Präfix `SANDBOX ` und `[ebay]`, `HINWEIS_QUELLE`, der USD-Hinweis auf stderr, nur der Sandbox-Host, POST und GET, keine Geheimnisse. |
| 8 | erfüllt | `test_erfolg_json`: gültiges JSON, `quelle=ebay`, Präfix `SANDBOX `, `lizenz` korrekt, kein Hinweis in stdout. |
| 9 | erfüllt | `test_filter_wirken` prüft `--max-preis 100` und `--suche trekking`. |
| 10 | erfüllt | `test_produktion_nur_mit_schalter`: Host `api.ebay.com`, kein `SANDBOX`-Präfix. |
| 11 | erfüllt | Der Satz ist ersetzt. Der neue Abschnitt enthält Befehl, `--json`, Präfix und Exit-Codes 0/3, nur mit Platzhaltern. |
| 12 | erfüllt | Die Gegenprobe ist rot (errors=10), siehe oben. |
| 13 | **teilweise** | Alle Tests sind grün (261) und die geschützten Dateien sind unverändert. Das Verhalten von `--openprices ""` hat sich aber verschlechtert (N1). |
| 14 | erfüllt | Der Secret-Scan ist sauber, die Tests laufen ohne Netz. |
| 15 | erfüllt (lokal) | Ein Commit, direkter Nachfolger von `31b52d4`. Push und PR-Nachtrag stehen noch aus (Aufgabe von COMMAND). |

## Nachbesserungspunkte

**N1 (Regression, muss behoben werden): `--openprices ""` stürzt jetzt mit Traceback ab.**
- Ursache: Die neue Prüfung zählt mit `is not None`. Für `--openprices ""` ist die Zahl der Quellen also 1. Der Zweig wird aber weiter per Wahrheitswert gewählt (`if a.openprices:`). Damit fällt `""` durch in `else: lies_datei(None)`.
- Beleg neu: `PYTHONPATH=app python3 -m schnapper --openprices ""` endet mit `TypeError: argument should be a str … not 'NoneType'` und exit=1.
- Beleg alt (`31b52d4`): `schnapper: error: entweder DATEI oder --openprices EAN angeben` mit Exit 2.
- Korrektur: in `__main__.py` `if a.openprices:` durch `if a.openprices is not None:` ersetzen. Dann prüft der `OpenPricesAdapter` die leere EAN und meldet sie über den Exit-3-Pfad. Alternativ `""` vor der Zählung als fehlend behandeln (alte Semantik, Exit 2).
- Dazu einen Test in `tests/test_ebay_cli.py` ergänzen, z. B. „`--openprices ""` ergibt kein TypeError bzw. einen kontrollierten Exit 2 oder 3“.

**N2 (Hinweis, optional):** `python -m schnapper ""` (leere DATEI) lief früher in `p.error` mit Exit 2. Jetzt kommt die Meldung „UNGÜLTIG: Nur .json oder .csv …“, ebenfalls mit Exit 2. Das ist unkritisch, aber eine Verhaltensänderung. Sie kann bleiben.

## Sonstiges
- Es gab keine Live-Aufrufe externer Dienste. An Code, Commits und Push wurde nichts geändert.
- Die Gegenprobe-Kopie liegt im Scratchpad unter `/tmp/claude-0/-home-claude-schnapper/6542dd57-933c-599a-b9d2-39b95c8e0e81/scratchpad/check-gp` und kann gelöscht werden.

## Runde 2

### Urteil: **bestanden**

Geprüfter Stand: `d1a9eef` (Eltern-Commit `c09c9dc` → `31b52d4`), Worktree `wt-45` sauber, `git merge-base --is-ancestor origin/agent/master/20261023-01 HEAD` = ja (Fast-Forward möglich). Die Commit-Trailer „Co-Authored-By“ und „Claude-Session“ sind vorhanden. Es gibt kein Amend und keinen Push.

### Belege

| Prüfung | Ergebnis |
| --- | --- |
| `python3 -m unittest discover -s tests` | **262 Tests OK** (252 + 10) |
| `cd cloudflare && node --test test/*.test.mjs` | **10/10 pass**, 0 fail |
| Ohne Netz: `unshare -rn python3 -m unittest tests.test_ebay_cli tests.test_ebay tests.test_openprices` | **73 Tests OK** |
| Diff `origin/agent/master/20261023-01..agent/master/20261023-01` | nur `app/schnapper/__main__.py`, `docs/EBAY.md` und `tests/test_ebay_cli.py` (alle erlaubt). Keine Dateien unter `.github/`, `team/` oder `cloudflare/`, und `ebay.py`, `adapter.py`, `quellen.py`, `web*` sind unverändert. |
| Secret-Scan auf den `+`-Zeilen (`sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`) | leer |
| Tabu (`zentna`, `jerry`, `beatmaster`) im Diff gegen main | 0 Treffer |
| N1 behoben: `PYTHONPATH=app python3 -m schnapper --openprices ""` | `schnapper: error: --openprices braucht eine EAN`, rc=2, kein Traceback |
| `--openprices "   "` und `--openprices 0` | Meldung „Open Prices: EAN/Barcode muss aus 8 bis 14 Ziffern bestehen“, rc=3 (kontrolliert) |
| Rauchtest `env -u SCHNAPPER_EBAY_FREIGABE … --ebay fahrrad` | `eBay: Freigabeschalter SCHNAPPER_EBAY_FREIGABE=ja fehlt …`, exit=3 |
| Gegenprobe N1: Kopie mit `__main__.py` aus `c09c9dc` | `tests.test_ebay_cli` liefert **FAILED (errors=1)**. Fehlgeschlagen ist genau `test_openprices_leer_sauberer_fehler` mit `TypeError … not 'NoneType'`, die übrigen 9 sind grün. Damit ist der neue Test wirksam. |
| Gegenprobe AK 12: Kopie mit `__main__.py` aus `31b52d4` | **FAILED (failures=1, errors=10)**. Ursache ist das unbekannte `--ebay`, und der neue Test zeigt die abweichende Meldung. Die Kopie `check-r2` ist wieder gelöscht. |

### Akzeptanzkriterien

| AK | Bewertung |
| --- | --- |
| 1–11 | erfüllt. Seit Runde 1 unverändert, die Diff-Ansicht `c09c9dc..d1a9eef` berührt nur die Zweigwahl für `--openprices` und einen neuen Test. Alle Tests für AK 2–10 sind grün. |
| 12 | erfüllt. Die Gegenprobe gegen `31b52d4` ist rot (siehe oben). |
| 13 | erfüllt. N1 ist behoben, der Bestand ist grün (262) und die geschützten Dateien sind unverändert. N2 (leere DATEI, Exit 2 mit anderer Meldung) bleibt bewusst so, unkritisch. |
| 14 | erfüllt. Der Secret-Scan ist leer, die Tests laufen ohne Netz. |
| 15 | lokal erfüllt, mit einer Abweichung: Es sind **zwei** Commits (`c09c9dc` plus Nachbesserung `d1a9eef`) statt einem. Das ist eine Folge der Nachbesserung ohne Amend und nachvollziehbar, kein Hindernis. Ausstehend für COMMAND: Push (normal, ohne Force) und Nachtrag im PR-Body von #45 per `gh api -X PATCH`, PR bleibt Draft. |

### Hinweise für COMMAND
- Den Push vor dem Ausführen erneut mit `merge-base --is-ancestor` prüfen. Danach den Worktree `wt-45` mit `git worktree remove` entfernen.
- Die alte Gegenprobe-Kopie `/tmp/claude-0/-home-claude-schnapper/6542dd57-933c-599a-b9d2-39b95c8e0e81/scratchpad/check-gp` aus Runde 1 ist laut BRAIN schon gelöscht.
