# CHECK – Lauf 20261029-0229

- Startzeit: 2026-10-29 02:35:30 UTC
- Endzeit: 2026-10-29 02:37:30 UTC
- Geprüft: lokaler Branch `agent/master/20261022-21`, Kopf `a87a977` (nicht gepusht), Arbeitsbaum sauber

## Urteil: **bestanden**

(Eine kleine Randfall-Anmerkung, siehe unten. Sie blockiert nicht und ist kein Akzeptanzkriterium.)

## Branch / Fast-Forward
- `git log --oneline origin/agent/master/20261022-21..HEAD` → genau 1 Commit: `a87a977 SCHNAPPER MASTER: F2 CSV-Export gegen Formel-Injektion absichern (S-009)`
- `git merge-base --is-ancestor origin/agent/master/20261022-21 HEAD` → FF-OK (origin = fd16763)
- origin/main (6dbe114) ist Vorfahr von HEAD → kein Merge nötig
- Die Commit-Nachricht enthält die Attributionszeilen (Co-Authored-By, Claude-Session)

## Testzahlen (selbst ausgeführt)
- `python3 -m unittest discover -s tests`: **243 Tests, OK**, 0 Skips (mit `-v` geprüft: kein „skipped“)
- `tests.test_app_erfassen_s009 -v`: **27 Tests, OK**. `test_ak8_erfassen_und_csv_im_browser` lief durch („ok“, kein Skip). `test_ak6_kopfzeile_wie_vorlage` und `test_ak6_roundtrip` sind grün.
- `test_app_kern test_input_guardrails test_app_quellen_web test_alarm`: **64 Tests, OK**
- Cloudflare `node --test test/*.test.mjs`: **10 Tests, 10 pass, 0 fail, 0 skipped**
- Gegenprobe (Testdateien von HEAD, App-Code `web.py`/`einlesen.py` von fd16763, per git archive im Scratchpad): CsvFormelSchutz + CsvImportApostroph → **FAILED (failures=3)**

## Akzeptanzkriterien
1. **Kein ungeschützter Formelstart im Export: erfüllt.** `als_csv` ruft `_csv_zelle` für id, titel, zustand, quelle, kategorie und url auf. Eigene Probe mit `=1+1`, `+1`, `-1`, `@A`, `\tTab` und `\rCR`: Alle Zellen werden mit `'` vorangestellt exportiert. Der Test `test_formel_zellen_geschuetzt_und_roundtrip` prüft alle Datenzellen mit csv.reader und `;`.
2. **Rückübernahme exakt: erfüllt.** Bei `=HYPERLINK(...)`, `@SUMME(1+1)`, `-50 % Rabatt Sofa`, `+1 Lampe`, `=1+1`, `+1`, `-1` und `@A` liefert `lies_text(...,"csv")` den Originalwert zurück, ohne Fehler und mit gleicher ID-Reihenfolge (getestet). Bei `\tTab` und `\rCR` kommt `Tab` bzw. `CR` zurück. Das liegt nicht an dieser Änderung: Der Import entfernt Leerraum schon vorher (`angebot.py:144` `.strip()`). Mit dem alten Code ergibt sich dasselbe Ergebnis (gegengeprüft).
3. **Normale Werte bleiben byte-gleich: erfüllt.** `normal`, `x=1`, `'normal`, `Lastenrad 'Classic'` und `＝1` (Vollbreiten-=) werden unverändert exportiert. Die ak6-Tests sind im Diff unverändert (keine entfernten Zeilen in der Testdatei) und grün. Die Kopfzeile wird weiter über `CSV_SPALTEN` geprüft (`test_ak6_kopfzeile_wie_vorlage` grün).
4. **Import entfernt `'` nur vor Formelzeichen: erfüllt.** `_ohne_formelschutz` prüft `isinstance(str)`, Länge ≥ 2, `'` an erster Stelle und ein Formelzeichen an zweiter. `'Normal` bleibt `'Normal`, `''=x` bleibt `''=x`. None-Werte und Listen (DictReader-Restkey) bleiben unberührt. `_zeilen_json` ist unverändert, Test `test_json_import_unveraendert` ist grün. Zahlenfelder: `'-5` wird zu `-5` und dann wie `-5` abgewiesen („Preis muss größer als 0 sein“). Geldspalten werden beim Export nicht verändert, und Preise sind immer > 0, also wird nichts verfälscht.
5. **Gegenprobe: erfüllt.** 3 Fehlschläge mit altem Code, grün mit neuem Code (siehe oben).
6. **Gesamtsuite grün: erfüllt.** 243 = 237 + 6 neue, Browsertest ohne Skip, Cloudflare 10/10.
7. **Pfade, Workflows, Secrets: erfüllt.** Der Diff fd16763..HEAD betrifft nur `app/schnapper/einlesen.py` (Konstante, `_ohne_formelschutz` und `_zeilen_csv`), `app/schnapper/web.py` und `tests/test_app_erfassen_s009.py`. Der Diff origin/main...HEAD enthält zusätzlich nur die früheren F2-Dateien (web/app.css, app.js, index.html), es gibt keine `.github/workflows`-Änderung. Die Konstante ist nur einmal definiert (in einlesen.py) und wird in web.py importiert. Secret-Scan (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, password/passwort) auf dem Diff origin/main...HEAD: keine Treffer. Tabu-Scan (ZENTNA, JERRY AL/Jerry-AL, Beatmaster): keine Treffer.
8. **Push ohne Force / Draft: noch offen für COMMAND.** Fast-Forward ist möglich (FF-OK). Push und PR-Nachtrag stehen noch aus. Es gibt keinen Merge.

## Anmerkung (nicht blockierend, optional für einen späteren Lauf)
- **Neuer Roundtrip-Verlust beim Randfall `'` + Formelzeichen als Originalwert:** Ein Titel, der wörtlich mit `'=x` beginnt, wird als `'=x` exportiert (kein Schutz nötig, denn die Zelle beginnt mit `'`). Beim Import wird daraus `=x`. Mit dem alten Code kam `'=x` zurück. Das ist sicherheitlich unkritisch, denn ein erneuter Export schützt die Zelle wieder, und der Fall ist praktisch selten. Wenn man das beheben will, braucht es ein symmetrisches Escaping. Ein Weg: Beim Export bekommt auch ein Wert, der mit `'` + Formelzeichen beginnt, ein zusätzliches `'`, und der Import entfernt genau ein `'` vor (`'` + Formelzeichen). Dann braucht es dafür einen eigenen Test.
- Unabhängig von dieser Änderung: Der Sniffer erkennt bei sehr kurzen CSV-Zeilen das Trennzeichen nicht (Fallback auf Komma). Das war schon vorher so.

## Nachbesserungsliste
Keine Pflicht-Nachbesserung.
