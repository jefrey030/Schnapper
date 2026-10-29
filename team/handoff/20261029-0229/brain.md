# BRAIN – Lauf 20261029-0229

- Startzeit: 2026-10-29 02:32:59 UTC
- Endzeit: 2026-10-29 02:34:55 UTC
- Branch: `agent/master/20261022-21` (PR #39, Draft), Basis fd16763; origin/main (6dbe114) ist bereits enthalten, kein Merge nötig
- Commit: `a87a977` „SCHNAPPER MASTER: F2 CSV-Export gegen Formel-Injektion absichern (S-009)“ (mit Attributionszeilen). **Nicht gepusht.**

## Geänderte Dateien (git diff --stat fd16763..HEAD)
- `app/schnapper/einlesen.py` (+13/-1): Konstante `CSV_FORMEL_START = ("=", "+", "-", "@", "\t", "\r")`, Hilfsfunktion `_ohne_formelschutz`, `_zeilen_csv` entfernt ein führendes `'` nur bei String-Werten, deren zweites Zeichen in CSV_FORMEL_START liegt (None/Listen bleiben unverändert). JSON-Import nicht verändert.
- `app/schnapper/web.py` (+14/-4): importiert `CSV_FORMEL_START` (keine Doppeldefinition), neue `_csv_zelle(text)`. `als_csv` wendet sie auf id, titel, zustand, quelle, kategorie und url an. Geldspalten und erfasst_am bleiben unverändert. Docstring ergänzt.
- `tests/test_app_erfassen_s009.py` (+79): neue Klassen `CsvFormelSchutz` (3 Tests: HYPERLINK-Titel und @SUMME-Kategorie geschützt plus Roundtrip mit ID-Reihenfolge; `-50 % Rabatt Sofa` und `+1 Lampe`; normaler Titel `Lastenrad 'Classic'` ohne Präfix) und `CsvImportApostroph` (3 Tests: `'Normal` bleibt; `'=1+1` und `'@A1` werden entfernt; JSON-Import lässt `'=1+1` unverändert).

## Testergebnisse
- Gesamtsuite `python3 -m unittest discover -s tests`: **243 Tests, OK** (237 vorher + 6 neue), 0 Fehler
- `tests.test_app_erfassen_s009 -v`: **27 Tests, OK**. Browsertest `test_ak8_erfassen_und_csv_im_browser` lief (ok, nicht übersprungen). `test_ak6_kopfzeile_wie_vorlage` und `test_ak6_roundtrip` ohne Änderung grün
- `test_app_kern test_input_guardrails test_app_quellen_web test_alarm`: **64 Tests, OK**
- Cloudflare `node --test test/*.test.mjs`: **10/10 pass**, 0 fail
- Gegenprobe: neue Klassen gegen web.py/einlesen.py aus fd16763 → **6 Tests, FAILED (failures=3)** (formel_roundtrip, plus_minus, apostroph_vor_formelzeichen; die 3 anderen prüfen Verhalten, das gleich bleiben soll). Danach neuen Stand wiederhergestellt, grün
- `git merge-base --is-ancestor fd16763 HEAD` → FF-OK
- Secret-Scan über den Diff → „kein Secret“
- Keine Änderung an .github/workflows, nur erlaubte Pfade, Arbeitsbaum sauber

## Offen für COMMAND
- Push ohne Force auf `agent/master/20261022-21` (Fast-Forward von fd16763), PR-Body #39 um den Nachtrag „Lauf 20261029-0229“ ergänzen, Draft lassen
