# LEAD – Lauf 20261023-0629

## Aufgabe
In PR #40 (F3) ersetzt `tests/test_app_sicherung_s010.py` den fest verdrahteten Pfad `chromium-1194` durch die Chromium-Suche `_finde_chromium()` aus PR #41.

**Begründung (selbst geprüft, 06:3x UTC):**
- Auswahlregel: offenen Team-Draft-PR fortsetzen; der letzte Bericht nennt genau diesen Schritt.
- `origin/agent/master/20261022-22` = 1adad0c, enthält main 6dbe114 (0 Commits dahinter). Ein Merge ist nicht nötig.
- Zeile 18 in #40: `CHROMIUM = pathlib.Path("/opt/pw-browsers/chromium-1194/chrome-linux/chrome")`. Diese Datei gibt es nicht. Installiert ist nur `/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`.
- Die Browsertests laufen heute nur grün, weil `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers` gesetzt ist (Probe: 8/8 OK, Gesamtlauf 224 OK). Ohne die Variable werden sie still übersprungen.
- In #41 (a3fcfab), `tests/test_app_kamera_s011.py` Z. 21–35: `_finde_chromium(basis=None)` sucht unter `chromium-*/chrome-linux*/chrome` die höchste Nummer. Dazu gibt es Unit-Tests (Z. 125, 131).

## Branch
`agent/master/20261022-22` (PR #40). BRAIN checkt lokal aus mit `git checkout -b work-40 origin/agent/master/20261022-22`, committet dort und pusht **nicht**.

## Dateien
- Nur `tests/test_app_sicherung_s010.py` ändern:
  - Z. 18 ersetzen: `_finde_chromium()` 1:1 aus #41 übernehmen, dann `CHROMIUM = _finde_chromium()`.
  - Z. 80: Bedingung `CHROMIUM.is_file()` ersetzen durch `CHROMIUM is not None`.
  - Z. 86: `if CHROMIUM.is_file()` ersetzen durch `if CHROMIUM`.
  - Zwei kleine Unit-Tests für `_finde_chromium` (leeres Verzeichnis ergibt None, höchste Nummer gewinnt, mit `tempfile`) analog #41 Z. 120–131 ergänzen.
- Quelle (nur lesen): `git show origin/agent/master/20261022-2238:tests/test_app_kamera_s011.py`

## Akzeptanzkriterien
1. `git diff --name-only origin/agent/master/20261022-22` zeigt ausschließlich `tests/test_app_sicherung_s010.py`.
2. Der String `chromium-1194` kommt im Repo-Baum des Branches nicht mehr vor: `git grep -n chromium-1194` liefert keine Ausgabe.
3. `_finde_chromium()` ist inhaltlich identisch mit #41. `_finde_chromium()` liefert hier `/opt/pw-browsers/chromium-1243/chrome-linux64/chrome`.
4. `python3 -m unittest -v tests.test_app_sicherung_s010` meldet OK und **0 skipped**. Erwartet sind 8 bisherige Tests plus die neuen Unit-Tests, also etwa 10.
5. Die Browsertests laufen auch **ohne** `PLAYWRIGHT_BROWSERS_PATH` ohne Skip, weil der Standardpfad /opt/pw-browsers greift. Prüfung mit `env -u PLAYWRIGHT_BROWSERS_PATH ...` (Befehl unten).
6. Gesamtlauf `python3 -m unittest discover -s tests` ist OK, mit etwa 226 Tests (vorher 224). BRAIN nennt die exakte Zahl.
7. `cd cloudflare && node --test test/*.test.mjs` ergibt 10/10 pass.
8. Es läuft kein `playwright install` und es gibt keinen Netzabruf. Es wird nur vorinstalliertes Chromium unter /opt/pw-browsers genutzt.
9. Es kommt kein Secret hinzu. Der Scan unten liefert im Diff 0 Treffer. Keine Änderung unter `.github/`, keine Tabu-Begriffe.
10. Es entsteht genau 1 Commit auf `work-40` mit der Nachricht „SCHNAPPER MASTER: F3 Browsertest findet Chromium automatisch (statt chromium-1194)“ und den Attributionszeilen. Nicht gepusht, kein Force, kein Merge.

## Testbefehle
```
cd /home/claude/schnapper
git fetch origin agent/master/20261022-22 agent/master/20261022-2238
git checkout -b work-40 origin/agent/master/20261022-22
python3 -m unittest -v tests.test_app_sicherung_s010 2>&1 | tail -15
env -u PLAYWRIGHT_BROWSERS_PATH python3 -m unittest -v tests.test_app_sicherung_s010 2>&1 | grep -ci skip   # erwartet 0
python3 -c "import sys; sys.path.insert(0,'tests'); import test_app_sicherung_s010 as t; print(t._finde_chromium())"
python3 -m unittest discover -s tests 2>&1 | tail -3
(cd cloudflare && node --test test/*.test.mjs 2>&1 | tail -8)
git grep -n chromium-1194; git diff --name-only origin/agent/master/20261022-22
git diff origin/agent/master/20261022-22 | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY' || echo "Secret-Scan: 0"
```
