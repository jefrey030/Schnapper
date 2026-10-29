# SCHNAPPER MASTER – Lauf 20261029-0229 (UTC)

Agenten getrennt: ja (LEAD, BRAIN, CHECK, COMMAND je eigener Subagent)

## Aufgabe
F2 / S-009 „Angebot direkt in der App erfassen“, Draft-PR #39 (Branch `agent/master/20261022-21`, Ausgangskopf `fd16763`).
Schritt: Den CSV-Export `/api/angebote.csv` gegen Formel-Injektion absichern (CWE-1236). Bisher wurden Titel und Kategorie wie `=HYPERLINK("https://boese.example";"Klick")` oder `@SUMME(1+1)` ungeschützt exportiert. Excel und LibreOffice werten solche Zellen als Formel aus. Über `/api/import` können auch fremde Listen in den Export gelangen.

## Ergebnis je Agent

| Agent | Zeit (UTC) | Ergebnis |
| --- | --- | --- |
| ORCHESTRATOR-Preflight | 02:29 | main @ 6dbe114 grün: 216 Tests OK (1 Skip), Cloudflare 10/10, kein Secret. Team-Draft-PRs #36, #39, #40, #41, #44, #45, #50 offen. Lauf freigegeben. |
| LEAD | 02:30:23–02:32:16 | F2 / PR #39 gewählt. Alle Team-PRs `mergeable_state` clean, keine Review-Kommentare. #50 (S-014) steht auf „Halt“. #39 war mit #36 am längsten unberührt und hat einen echten Sicherheitsmangel. Mangel reproduziert: `als_csv` gibt `"=HYPERLINK(...)"` und `@SUMME(1+1)` ungeschützt aus. 8 Akzeptanzkriterien. Erlaubt sind nur `app/schnapper/web.py`, `app/schnapper/einlesen.py` (`_zeilen_csv` und Konstante) und `tests/test_app_erfassen_s009.py`. |
| BRAIN | 02:32:59–02:34:55 | Commit `a87a977`. `CSV_FORMEL_START = ("=", "+", "-", "@", "\t", "\r")` und `_ohne_formelschutz` in `einlesen.py`: `_zeilen_csv` entfernt ein führendes `'` nur vor diesen Zeichen. `web.py` importiert die Konstante. Neue Funktion `_csv_zelle()` für id, titel, zustand, quelle, kategorie und url, Geldspalten und erfasst_am bleiben unverändert. 6 neue Tests (`CsvFormelSchutz` 3, `CsvImportApostroph` 3). 243 Tests OK, Gegenprobe rot (failures=3). |
| CHECK | 02:35:30–02:37:30 | **bestanden**. Tests selbst wiederholt: 243 OK ohne Skips, Modul 27/27, 64 OK, Cloudflare 10/10. Gegenprobe selbst rot (failures=3). Eigene Probe mit `=1+1`, `+1`, `-1`, `@A`, `\tTab` und `\rCR`: alle geschützt. Bei Tab und CR geht führender Leerraum durch das schon vorhandene `.strip()` verloren, mit altem Code genauso. Diff nur erlaubte Pfade, keine Workflow-Änderung, Secret- und Tabu-Scan leer. AK 1–7 erfüllt, AK 8 an COMMAND übergeben. |
| COMMAND | 02:38:27–02:39:40 | Urteil geprüft. `git log origin/…..lokal` zeigt genau 1 Commit (a87a977), `merge-base --is-ancestor` → FF-OK. Push `fd16763..a87a977` ohne Force (02:38:37). PR-Body #39 per REST (`gh api -X PATCH`) um den Nachtrag „Lauf 20261029-0229: CSV-Export gegen Formel-Injektion (CWE-1236)“ ergänzt. Danach per REST geprüft: `draft=true`, `head.sha=a87a977…`, `state=open`. Entwürfe für STATUS.md und tasks.json im Übergabeordner, JSON mit `json.tool` geprüft. |

## Commits
- `a87a977` SCHNAPPER MASTER: F2 CSV-Export gegen Formel-Injektion absichern (S-009)
- Branch-Kopf auf origin: `a87a977ebb612075d8b71bb232dbfbcc1b822f6c` (vorher `fd16763e43bfa1370039b85b3d7d5625aba6a993`)
- Diff: `app/schnapper/einlesen.py` +13/−1, `app/schnapper/web.py` +14/−4, `tests/test_app_erfassen_s009.py` +79
- origin/main (6dbe114) ist schon enthalten, ein Merge war nicht nötig.

## Tests
- `python3 -m unittest discover -s tests`: 243 OK (vorher 237, +6 neu), 0 Skips
- `python3 -m unittest tests.test_app_erfassen_s009 -v`: 27/27 OK. Der Browsertest `test_ak8_erfassen_und_csv_im_browser` lief ohne Skip. `test_ak6_kopfzeile_wie_vorlage` und `test_ak6_roundtrip` sind unverändert grün.
- `tests.test_app_kern tests.test_input_guardrails tests.test_app_quellen_web tests.test_alarm`: 64 OK
- Gegenprobe (neue Tests gegen `web.py`/`einlesen.py` aus fd16763): FAILED (failures=3)
- `cd cloudflare && node --test test/*.test.mjs`: 10/10 pass
- Secret-Scan über den Diff: 0 Treffer

## PR
https://github.com/jefrey030/schnapper/pull/39 – Draft, Kopf a87a977. Der Nachtrag „Lauf 20261029-0229“ steht im Body, der übrige Body ist unverändert. Kein Merge, kein Kommentar.

## Hinweis aus CHECK (nicht blockierend)
- Wenn ein Originalwert wörtlich mit `'=x` beginnt, wird er als `'=x` exportiert (die Zelle braucht keinen Schutz) und kommt beim Import als `=x` zurück. Mit dem alten Code kam `'=x` zurück. Sicherheitlich ist das unkritisch, denn ein erneuter Export schützt die Zelle wieder. Der Fall ist selten. Eine Lösung wäre symmetrisches Escaping (siehe nächster Schritt).
- Unabhängig von dieser Änderung: Bei sehr kurzen CSV-Zeilen erkennt der Sniffer das Trennzeichen nicht und fällt auf Komma zurück. Das war schon vorher so.

## Blocker
- Die Merge-Entscheidung über #36, #39, #40, #41, #44, #45 und #50 liegt bei Jefrey.
- #50 (S-014) bleibt laut Kommentar vom 25.10. auf „Halt“, weil GitHub Models eingestellt ist.
- #39, #40 und #41 ändern dieselben Stellen in `app.js`/`index.html`. Beim Mergen sind Folgekonflikte zu erwarten.

## Fehlende Zugangsdaten
- Keine für diesen Schritt.
- Für F6 (#45) liegen die eBay-Sandbox-Schlüssel (Client-ID/-Secret) weiterhin nicht vor. Nur Jefrey hat sie, sie gehören nur in Umgebungsvariablen laut `docs/EBAY.md`, nie ins Repo.

## Nächster kleinster Schritt
- In #39 (optional): Symmetrisches Escaping für den Randfall `'` + Formelzeichen. Der Export setzt dann auch vor einen Wert, der mit `'` + Formelzeichen beginnt, ein zusätzliches `'`, und der Import entfernt genau ein `'`. Dazu ein eigener Roundtrip-Test mit `'=x`.
- Sonst einen anderen Team-PR mit belegbarem Mangel wählen.
