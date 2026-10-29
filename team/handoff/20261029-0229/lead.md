# LEAD – Lauf 20261029-0229

- Startzeit: 2026-10-29 02:30:23 UTC
- Endzeit: 2026-10-29 02:32:16 UTC

## Gewählte Aufgabe
**F2 / S-009 „Angebot direkt in der App erfassen“, Draft-PR #39**, Branch fortsetzen: `agent/master/20261022-21` (Kopf `fd16763`).
Schritt: **CSV-Export `/api/angebote.csv` gegen Formel-Injektion absichern (CWE-1236)**. Textzellen, die mit `=`, `+`, `-`, `@`, Tab oder CR beginnen, bekommen beim Export ein führendes `'`. Damit die Rückübernahme gleich bleibt, entfernt der CSV-Import genau dieses `'` wieder, aber nur, wenn darauf eines dieser Zeichen folgt.

## Begründung mit Belegen
1. **Kein Konflikt, keine Review-Kommentare:** Alle Team-PRs #36, #39, #40, #41, #44, #45, #50 haben per REST `mergeable=true` und `mergeable_state=clean`. Jeder F-Branch liegt 0 Commits hinter origin/main (6dbe114). Review-Kommentare: überall 0. Issue-Kommentare gibt es nur in #40 (P0 schon in 33a9487 behoben und beantwortet) und #50.
2. **#50 / S-014 wurde nicht gewählt:** Laut Kommentar vom 25.10. ist S-014 „Halt“, weil GitHub Models eingestellt ist. Fortsetzen hieße, gegen diese Ansage zu arbeiten.
3. **Keine Aufgabe „open“ in tasks.json auf main:** Dort stehen nur S-000–S-003 auf review und S-004–S-006 auf proposed.
4. **Längste Pause:** Nach dem nicht fortsetzbaren #50 wurden #36 (F1, zuletzt 28.10. 17:29) und #39 (F2, zuletzt 28.10. 18:29) am längsten nicht angefasst. #36 ist nur eine Doku-Tabelle, die mit der Zeit veraltet; das wäre kosmetisch. #39 hat dagegen einen echten Sicherheitsmangel.
5. **Mangel reproduziert:** Ich habe `als_csv` aus origin/agent/master/20261022-21 (per git archive im Scratchpad) mit dem Titel `=HYPERLINK("https://boese.example";"Klick")` und der Kategorie `@SUMME(1+1)` aufgerufen. Die Ausgabe enthält die Zellen ungeschützt:
   `e-1;"=HYPERLINK(""https://boese.example"";""Klick"")";5.00;0.00;;unbekannt;eigene;@SUMME(1+1);https://x.example/a;...`
   Excel/LibreOffice werten solche Zellen als Formel aus. Titel und Kategorie sind beliebige Texte. Außerdem kommen über `/api/import` auch fremde Listen in den Export. Im Branch gibt es bisher keinerlei Schutz (git grep nach „Formel/formula“ findet nichts).

## Branch
- Fortgesetzt: `agent/master/20261022-21` (PR #39, Draft bleibt Draft)
- Vor dem Push: `git fetch origin`. Falls origin/main inzwischen neuer ist: `git merge origin/main` (**kein Rebase, kein Force-Push**), Konflikte auflösen und die Tests erneut ausführen.

## Umsetzungsschritte (BRAIN)
1. `git fetch origin && git checkout -B agent/master/20261022-21 origin/agent/master/20261022-21`
2. `app/schnapper/web.py`: Konstante `CSV_FORMEL_START = ("=", "+", "-", "@", "\t", "\r")` und Hilfsfunktion `_csv_zelle(text: str) -> str` anlegen. Sie gibt `"'" + text` zurück, wenn `text` mit einem dieser Zeichen beginnt, sonst `text` unverändert. In `als_csv` auf alle Textspalten anwenden: id, titel, zustand, quelle, kategorie, url. Geldspalten und erfasst_am bleiben unverändert, denn sie werden vom Server erzeugt bzw. sind Decimal. Die Docstring-Zeile zum Schutz ergänzen.
3. `app/schnapper/einlesen.py`, nur in `_zeilen_csv`: In jeder Zeile bei String-Werten ein führendes `'` entfernen, **nur** wenn das zweite Zeichen in `("=", "+", "-", "@", "\t", "\r")` liegt. None-Werte (kurze Zeilen) und alle anderen Werte bleiben unverändert. JSON-Import nicht ändern. Einen gemeinsamen Satz an Zeichen verwenden: in einlesen.py definieren und in web.py importieren, damit es keine Doppeldefinition gibt.
4. `tests/test_app_erfassen_s009.py` um eine Testklasse `CsvFormelSchutz` (oder Tests in `CsvExport`) ergänzen:
   a. Server-Test: Titel `=HYPERLINK("https://boese.example";"Klick")` und Kategorie `@SUMME(1+1)` erfassen (201). Im CSV-Download beginnt keine Datenzelle mit `= + - @ \t \r`. Die Zellen sind `'=HYPERLINK(...)` bzw. `'@SUMME(1+1)` (mit csv.reader, Trennzeichen `;` prüfen).
   b. Rückübernahme: `lies_text(csv_text, "csv")` liefert genau den Originaltitel und die Originalkategorie zurück, ohne `'` und ohne Fehler.
   c. Titel `-50 % Rabatt Sofa` und `+1 Lampe`: geschützt exportiert und unverändert zurückgelesen.
   d. Unit-Test einlesen: `'Normal` (kein Formelzeichen danach) bleibt `'Normal`. Ein normaler Titel bleibt ohne Präfix (bestehender Roundtrip-Test bleibt grün).
5. Gegenprobe: Die neuen Tests gegen `app/schnapper/web.py` und `app/schnapper/einlesen.py` aus fd16763 bzw. 6dbe114 laufen lassen (z. B. `git stash` nur der App-Dateien oder `git show fd16763:app/schnapper/web.py > ...`). Sie müssen rot sein; danach den Stand wiederherstellen.
6. Commit: `SCHNAPPER MASTER: F2 CSV-Export gegen Formel-Injektion absichern (S-009)` mit den Attributionszeilen. COMMAND: Push ohne Force (Fast-Forward prüfen), PR-Body #39 per REST um einen Nachtrag „Lauf 20261029-0229“ ergänzen, Draft lassen.

## Akzeptanzkriterien (prüfbar)
1. Im CSV-Download `/api/angebote.csv` beginnt keine Datenzelle der Textspalten mit `=`, `+`, `-`, `@`, Tab oder CR. Betroffene Zellen beginnen mit `'`.
2. `lies_text(<Export>, "csv")` liefert für Titel/Kategorie mit diesen Startzeichen exakt den Originalwert zurück, ohne Fehler und mit gleicher ID-Reihenfolge.
3. Werte ohne Formel-Startzeichen werden byte-gleich wie bisher exportiert. Bestehende Tests `test_ak6_kopfzeile_wie_vorlage` und `test_ak6_roundtrip` sind unverändert grün. Die Kopfzeile ist identisch mit `app/vorlagen/meine-angebote.csv`.
4. Der CSV-Import entfernt `'` nur vor `= + - @ \t \r`. `'Normal` bleibt `'Normal`. Der JSON-Import ist unverändert.
5. Gegenprobe: Die neuen Tests schlagen mit dem App-Code von fd16763 fehl (failures>0) und sind mit dem neuen Code grün.
6. Gesamtsuite grün (`python3 -m unittest discover -s tests`, erwartet ≥ 237 + neue Tests, 0 Fehler). `test_app_erfassen_s009` vollständig grün, inklusive Browsertest `test_ak8_erfassen_und_csv_im_browser` (390x844, keine Konsolenfehler) ohne Skip. Cloudflare 10/10.
7. Diff gegenüber fd16763 betrifft nur die erlaubten Pfade (unten). Keine Änderung an .github/workflows. Secret-Scan über den Diff ohne Treffer.
8. Push ohne Force (fd16763 ist Vorfahr des neuen Kopfes). PR #39 bleibt Draft, kein Merge.

## Testbefehle
```
cd /home/claude/schnapper && python3 -m unittest discover -s tests
cd /home/claude/schnapper && python3 -m unittest tests.test_app_erfassen_s009 -v
cd /home/claude/schnapper && python3 -m unittest tests.test_app_kern tests.test_input_guardrails tests.test_app_quellen_web tests.test_alarm -v   # weitere Nutzer von lies_text/einlesen
cd /home/claude/schnapper/cloudflare && node --test test/*.test.mjs
cd /home/claude/schnapper && git diff --stat fd16763..HEAD && git merge-base --is-ancestor fd16763 HEAD && echo FF-OK
cd /home/claude/schnapper && git diff fd16763..HEAD | grep -nE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY' || echo "kein Secret"
```
Browsertests nutzen Playwright mit vorinstalliertem Chromium (`_finde_chromium()`, /opt/pw-browsers). **Kein `playwright install`**, keine Live-Netzabrufe.

## Erlaubte Pfade
- `app/schnapper/web.py`
- `app/schnapper/einlesen.py` (nur `_zeilen_csv` + Konstante)
- `tests/test_app_erfassen_s009.py`
- Bei einem Merge mit origin/main zusätzlich nur die Konfliktdateien, die der Merge selbst berührt

Verboten: .github/workflows, fremde Branches, main, Rebase/Force-Push, Merge des PRs.
