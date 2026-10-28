| Lauf | Aufgabe | Urteil CHECK | Tests | PR | Agenten getrennt |
|---|---|---|---|---|---|
| 20261022-2029 | F1 Aufräumen (tasks.json S-004–S-006 done, S-009–S-013 open; Masterplan Abschnitt B) | bestanden (Runde 2 nach 1× nachbessern) | Python 190/190, Cloudflare 10/10 | #36 (Draft) | ja |
| 20261022-2128 | F2 = S-009 Angebot direkt in der App erfassen | bestanden (Runde 1) | Python 202/202, Cloudflare 10/10 | #39 (Draft) | ja |
| 20261022-2228 | F3 = S-010 Merkliste/Preisalarme als JSON sichern und wiederherstellen | bestanden (Runde 1) | Python 196/196, Cloudflare 10/10 | #40 (Draft) | ja |
| 20261022-2238 | F4 = S-011 Barcode per Kamera scannen | bestanden (Runde 1) | Python 200/200, Cloudflare 10/10 | #41 (Draft) | ja |
| 20261022-2328 | F5 = S-012 Ein-Befehl-Start für Android/Termux (start-schnapper.sh) | bestanden (Runde 1) | Python 232/232, Cloudflare 10/10 | #44 (Draft) | ja |
| 20261023-0128 | F6 = S-013 eBay vorbereiten (Browse-API-Adapter, gesperrt ohne Schlüssel, docs/EBAY.md) | bestanden (Runde 1) | Python 250/250, Cloudflare 10/10 | #45 (Draft) | ja |
| 20261023-0229 | PR #39 (F2/S-009) auf main 6dbe114 gebracht, hinzufuegen atomar mit _import_lock/Rollback | bestanden (Runde 1) | Python 231/231, Cloudflare 10/10 | #39 (Draft, aktualisiert) | ja |
| 20261023-0329 | PR #40 (F3/S-010) per Merge auf main 6dbe114 gebracht, Alarm-Prüfung beim Wiederherstellen an Server-Regeln angeglichen | bestanden (Runde 1) | Python 224/224, Cloudflare 10/10, S-010-Browsertests 4/4 | #40 (Draft, aktualisiert) | ja |
| 20261023-0429 | PR #41 (F4/S-011) per Merge auf main 6dbe114 gebracht, Chromium-Pfad in Browsertests automatisch gesucht | bestanden (Runde 1) | Python 227/227 (0 Skips), Kamera-Browsertests 11/11, Cloudflare 10/10 | #41 (Draft, aktualisiert) | ja |
| 20261023-0529 | PR #36 (F1) per Merge auf main 6dbe114 gebracht, PR-Tabelle Abschnitt B auf Live-Stand, S-009–S-013 auf review | bestanden (Runde 1) | Python 216/216, Cloudflare 10/10 | #36 (Draft, aktualisiert) | ja |
| 20261023-0629 | PR #40 (F3/S-010): Chromium-Suche `_finde_chromium()` aus #41 in Browsertests übernommen, kein fester chromium-1194-Pfad mehr | bestanden (Runde 1) | Python 226/226, S-010-Modul 10/10 ohne Skip, Cloudflare 10/10 | #40 (Draft, aktualisiert) | ja |
| 20261028-0828 | F6 = S-013 PR #45: kaputtes eBay-JSON (zu tief verschachtelt, zu lange Zahl) als EbayFehler statt Python-Absturz, Test ergänzt | bestanden (Runde 1) | Python 251/251, test_ebay 35/35, Cloudflare 10/10 | #45 (Draft, aktualisiert) | ja |
| 20261028-0928 | F6 = S-013 PR #45: kaputte URL (ValueError aus urlsplit) in _anfrage als EbayGesperrt, Test ergänzt | bestanden (Runde 1) | Python 252/252, test_ebay 36/36, Cloudflare 10/10 | #45 (Draft, aktualisiert) | ja |
