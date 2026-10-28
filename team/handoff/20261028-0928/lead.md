# LEAD – Plan für Lauf 20261028-0928 (UTC)

## Auswahl (Prioritätsregel)
1. Offener Team-Draft-PR fortsetzen: **ja**. Gewählt wurde der im letzten Bericht genannte Folgepunkt in **#45**. LEAD hat ihn selbst nachgeprüft.
2. Aufgaben mit Status „open“ in `team/tasks.json` auf main: **keine**. S-000 bis S-003 stehen auf review, S-004 bis S-006 auf proposed.
3. F1 bis F6 sind alle durch offene Team-Draft-PRs abgedeckt (#36, #39, #40, #41, #44, #45). #50 bleibt ausgeklammert.

## Aufgabe
**PR #45 (F6 / S-013), Branch `agent/master/20261023-01`, Kopf 31677d0:** Die Funktion `_anfrage()` in `app/schnapper/ebay.py` soll bei einer syntaktisch kaputten URL `EbayGesperrt` werfen. Bisher reicht sie einen rohen `ValueError` aus `urllib.parse.urlsplit` durch.

### Codebeleg (origin/agent/master/20261023-01:app/schnapper/ebay.py, Z. 239–253)
```python
def _anfrage(methode, url, kopfzeilen, daten=None, timeout=TIMEOUT) -> dict:
    """Einzige Stelle mit Netzzugriff. Prüft Ziel, ..."""
    if methode not in ("GET", "POST"):
        raise EbayGesperrt(...)
    teile = urllib.parse.urlsplit(url)          # Z. 244 – steht NICHT im try
    try:
        port_erlaubt = teile.port in (None, 443)
    except ValueError:
        port_erlaubt = False
    if (... ): raise EbayGesperrt("Nur Token- und Suchendpunkt ...")
```
Nachgemessen mit Python 3.13.18. `urlsplit` wirft selbst `ValueError` bei:
- `https://[::1/identity/v1/oauth2/token` → `ValueError: Invalid IPv6 URL`
- `https://api.ebay.com]/buy/browse/v1/item_summary/search` → `ValueError: Invalid IPv6 URL`
- `https://api.ebay.com＃@evil.example/identity/v1/oauth2/token` (Vollbreiten-#) → `ValueError: netloc … contains invalid characters under NFKC normalization`

### Begründung und Erreichbarkeit (ehrlich bewertet)
- **Der Fehler existiert.** Die Zielprüfung soll laut Docstring („Prüft Ziel“) und laut `EbayGesperrt`-Docstring („Abruf nicht erlaubt (… Ziel-URL)“) jede unzulässige Ziel-URL als `EbayGesperrt` melden. Der Code tut das schon für kaputte Ports: Ein eigenes `try/except ValueError` um `teile.port` existiert, und `test_host_allowlist` prüft `:99999` und `:abc` ausdrücklich auf `EbayGesperrt`. Der `ValueError` aus `urlsplit` ist dieselbe Fehlerklasse an der Stelle direkt davor und wurde schlicht nicht abgedeckt. Die Regel ist also inkonsistent umgesetzt.
- **Erreichbarkeit im Produktivpfad: gering.** `EbayAdapter` baut die URLs nur aus den Konstanten `SANDBOX_HOST`/`PRODUKTION_HOST` und den Pfaden. Der Suchbegriff landet per `urlencode` in der Query und kann den Netloc nicht kaputt machen. Erreichbar ist der Fehler nur bei direktem Aufruf von `_anfrage` (so testen es auch die Tests) oder über künftigen Code, der `_anfrage` nutzt. Der Schritt ist also **Härtung und Vertragstreue der einzigen Netz-Schranke**, keine akute Lücke. Er ist trotzdem sinnvoll: klein, in ~20 Minuten machbar, im Stil des vorhandenen Port-Falls und ohne Risiko. Sicherheitlich passiert heute nichts Schlimmes, weil vor dem Netz abgebrochen wird. Falsch ist nur die Fehlerart.
- Die Alternative „Bericht zu 2666d8b nachtragen“ ist reine Doku. Sie wird zurückgestellt, weil die Prioritätsregel einen Codepunkt am offenen PR vorzieht.

## Fortzusetzender Branch
- `agent/master/20261023-01` → Draft-PR **#45** (Kopf 31677d0, mergeable_state clean).
- Keine fremden Branches, nicht #50.

## Vorgehen für BRAIN
1. Basis ist main 6dbe114. Der PR-Branch ist laut Preflight clean und hat 0 Commits Rückstand auf main (Eltern-Kette 31677d0 → ecad218 → 6dbe114). Arbeitszweig lokal von `origin/agent/master/20261023-01` anlegen. **Kein Rebase, kein Force-Push, kein Amend** bestehender Commits. Nur falls origin/main inzwischen weiter ist: `git merge origin/main` (normaler Merge-Commit).
2. In `_anfrage()` (`app/schnapper/ebay.py`) den Aufruf `urllib.parse.urlsplit(url)` so absichern, dass ein `ValueError` zu `EbayGesperrt` mit derselben bestehenden Meldung „Nur Token- und Suchendpunkt auf https://api.ebay.com bzw. https://api.sandbox.ebay.com sind erlaubt“ wird. Dabei `from None`, damit weder die Original-URL noch der Kontext in `__cause__` landet. Am einfachsten geht das, indem `urlsplit` und die Port-Prüfung in einen gemeinsamen `try`-Block kommen oder ein eigenes `try/except ValueError` erhalten, das direkt `raise EbayGesperrt(...) from None` auslöst. Die Meldung wird **nicht** um die URL erweitert.
3. Minimal bleiben: keine weiteren Refactorings, keine Änderung an Methode, Allowlist, Timeout oder JSON-Teil.
4. Test in `tests/test_ebay.py`, Klasse `AnfrageTests`: Am besten ein neuer Test `test_kaputte_url_gesperrt`. Alternativ kommen die drei URLs oben als zusätzliche Einträge in die Liste `schlecht` von `test_host_allowlist`. Der neue Test soll prüfen:
   - Jede der drei URLs (GET bzw. POST) ergibt `ebay.EbayGesperrt` per `assertRaises(ebay.EbayGesperrt)`. Geprüft: `QuelleGesperrt` erbt von `RuntimeError` (`app/schnapper/adapter.py:20`), nicht von `ValueError`. `assertRaises(ebay.EbayGesperrt)` scheitert gegen den alten Code also sauber.
   - `_oeffner` wird nicht aufgerufen (wie in `test_host_allowlist` per `side_effect=AssertionError`).
   - `cm.exception.__cause__ is None` und `__suppress_context__` ist True.
   - `self.ohne_geheimnis(cm.exception)`, und `"evil"` steht nicht in `str(cm.exception)`.
5. Gegenprobe: Den neuen Test zuerst gegen den unveränderten Code laufen lassen (erwartet: FAIL/ERROR mit `ValueError: Invalid IPv6 URL`), dann mit Fix (erwartet: OK).
6. Einen lokalen Commit auf dem Arbeitszweig mit der Nachricht „SCHNAPPER MASTER: F6 eBay – kaputte URL in _anfrage als EbayGesperrt (S-013)“ plus die vorgegebenen Attributionszeilen. **Nicht pushen**, das macht COMMAND nach dem CHECK-Urteil.

## Akzeptanzkriterien
1. `_anfrage("GET", "https://[::1/identity/v1/oauth2/token", {}, None)` wirft `EbayGesperrt`, keinen rohen `ValueError` aus `urlsplit`.
2. Dasselbe gilt für `https://api.ebay.com]/buy/browse/v1/item_summary/search` und für die NFKC-URL `https://api.ebay.com＃@evil.example/identity/v1/oauth2/token`.
3. Die Meldung ist die bestehende Allowlist-Meldung. Sie enthält weder die URL noch „evil“, weder Client-ID/Secret/Token noch Basic-Daten. `__cause__ is None`, `__suppress_context__ is True`.
4. In allen drei Fällen wird kein Opener gebaut und kein Netzzugriff versucht.
5. Die Port-Fälle `:99999`/`:abc` und alle übrigen Einträge von `test_host_allowlist` bleiben unverändert grün. Gültige URLs (inkl. `:443`) funktionieren weiter (`test_erlaubt_mit_port_443_und_timeout`).
6. Der neue Test scheitert nachweislich gegen den alten Code (Gegenprobe dokumentiert) und besteht mit dem Fix.
7. `python3 -m unittest -v tests.test_ebay`: alle OK, Anzahl 36 (bisher 35) bzw. 35 mit zusätzlichen subTests. 0 Fehler, 0 skipped.
8. `python3 -m unittest discover -s tests`: alle OK (bisher 251 auf dem Branch, erwartet 252 bzw. 251), 0 Fehler.
9. `cd cloudflare && node --test test/*.test.mjs`: 10/10 bestanden.
10. Der Diff berührt nur die erlaubten Dateien. Keine Secrets, keine Tabu-Begriffe, nichts unter `.github/`, keine Live-Netzabrufe (nur Mock).
11. Die Historie bleibt linear auf 31677d0 aufgebaut: kein Rebase, kein Amend, kein Force-Push. Für COMMAND ist ein Fast-Forward-Push möglich.

## Testbefehle (im Klon, auf dem Arbeitszweig)
```bash
cd /home/claude/schnapper
python3 -m unittest -v tests.test_ebay.AnfrageTests.test_kaputte_url_gesperrt   # gezielter Einzeltest (Name ggf. anpassen)
python3 -m unittest -v tests.test_ebay                                           # ganze eBay-Suite
python3 -m unittest discover -s tests                                            # alle Python-Tests
cd cloudflare && node --test test/*.test.mjs                                     # Cloudflare-Tests
```
Gegenprobe: Den Fix kurz zurückstellen (z. B. `git stash` nur für `app/schnapper/ebay.py`, oder den Test gegen `git show 31677d0:app/schnapper/ebay.py` in einer Scratch-Kopie laufen lassen). Den gezielten Einzeltest ausführen, das Scheitern notieren, danach den Fix wiederherstellen.

## Erlaubte Dateien
- `app/schnapper/ebay.py`: nur der Anfang von `_anfrage()` (Absicherung von urlsplit/Port)
- `tests/test_ebay.py`: nur die Klasse `AnfrageTests` (neuer Test bzw. erweiterte Liste `schlecht`)
- Optional `docs/EBAY.md`: höchstens eine Zeile in „Typische Fehlermeldungen“, falls sinnvoll, sonst unverändert

Alles andere ist tabu, insbesondere `team/tasks.json` (S-013 steht in #36 schon auf review, eine Änderung würde mit #36 kollidieren), `.github/`, `app/schnapper/web/` und fremde Branches.
