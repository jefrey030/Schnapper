# CHECK – Lauf 20261023-0229

**Urteil: bestanden**

Geprüft wurde der Branch `agent/master/20261022-21` @ 1833417 (lokal, nicht gepusht). Remote laut `git ls-remote`: origin/agent/master/20261022-21 = 6dbeb82, origin/main = 6dbe114.
Ich habe nichts geändert, committet oder gepusht. Für die Gegenprobe habe ich einen temporären Worktree im Scratchpad angelegt und danach wieder entfernt.

## Testzahlen (selbst ausgeführt)
| Befehl | Ergebnis |
|---|---|
| `python3 -m unittest discover -s tests` | **Ran 231 tests, OK**. Mit `-v` steht kein einziges „skip“ in der Ausgabe. brain.md nennt skipped=1, hier ist es 0. Die Abweichung ist harmlos. |
| `cd cloudflare && node --test test/*.test.mjs` | **10 tests, 10 pass, 0 fail, 0 skipped** |
| `PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers python3 -m unittest -v tests.test_app_erfassen_s009` | **15/15 OK**, `test_ak8_erfassen_und_csv_im_browser ... ok`. Der Test lief wirklich und wurde nicht übersprungen (Chromium aus /opt/pw-browsers/chromium-1243, kein `playwright install`). |
| Gegenprobe: `hinzufuegen` im Stand des Merge-Commits 2a3ae8e, darauf `tests...ErfassenAtomar` | **FAILED (failures=1)**. Der neue Rollback-Test erkennt das alte Verhalten also wirklich. |

## Akzeptanzkriterien
1. **erfüllt.** `git merge-base --is-ancestor origin/main HEAD` ergibt 0.
2. **erfüllt.** `--is-ancestor 6dbeb82 HEAD` ergibt 0, ebenso für origin/agent/master/20261022-21. Der Push ist also ein reiner Fast-Forward, ein Force-Push ist nicht nötig.
3. **erfüllt.** `git log --format='%h %p | %s'`:
   - 2a3ae8e mit den Eltern 6dbeb82 und 6dbe114: „SCHNAPPER MASTER: main (#34, #37, #42, #43) in F2 übernommen (S-009)“
   - 1833417 mit dem Elternteil 2a3ae8e: „SCHNAPPER MASTER: F2 Erfassen atomar wie Import (S-009)“

   `rev-list --first-parent 6dbeb82..HEAD` ergibt 2. Die übrigen 4 Commits in `origin/agent..HEAD` (bbbed04, 1926983, 6d91dfa, 6dbe114) stammen aus main.
4. **erfüllt.** `git diff origin/main HEAD --stat` zeigt genau 5 Dateien mit 426+/2−. Die beiden entfernten Zeilen in web.py sind Erweiterungen (Import um `Angebot` ergänzt, Pfadliste um `/api/angebot` ergänzt). `_import_lock`, `verlauf.importiere`, „Höchstpreis muss größer als 0 sein“ und „Liste nicht übernommen …“ sind alle noch vorhanden (per grep geprüft).
5. **erfüllt.** `hinzufuegen` läuft komplett unter `_import_lock` und ruft zuerst `preise_merken`, also `verlauf.importiere`. Diese Methode macht bei einer Ausnahme selbst den Rollback. Erst danach wird `_daten` unter `_lock` gesetzt. Die Lock-Reihenfolge `_import_lock` → `_lock` ist dieselbe wie in `ersetzen`, ein Deadlock-Risiko ist nicht erkennbar.
6. **erfüllt.** `test_speicherfehler_500_liste_und_verlauf_unveraendert` prüft: Status 500, Text beginnt mit „Angebot nicht übernommen“, Suche unverändert, Beispieldaten weiterhin aktiv, kein RAM-Punkt für die URL, Datei byte-gleich. Ein erneuter Versuch ergibt danach 201.
7. **erfüllt.** `test_mehrdeutiger_preis_422_liste_unveraendert` („1,234“ ergibt 422, Liste und Verlaufsdatei unverändert).
8. **erfüllt.** `test_url_mit_zugangsdaten_422`.
9. **erfüllt.** AK1–AK8 aus #39 laufen grün, der Browsertest wurde ausgeführt (siehe oben).
10. **erfüllt.** 231 Tests, OK (gefordert sind mindestens 231).
11. **erfüllt.** 10/10.
12. **erfüllt.** Ich habe `git diff origin/agent/master/20261022-21 HEAD` und `git diff origin/main...HEAD` nach `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|ZENTNA|JERRY AL|Beatmaster` durchsucht:
    - Im eigentlichen Änderungs-Diff (origin/main...HEAD) gibt es **0 Treffer**.
    - Gegen den alten PR-Kopf gibt es nur Treffer aus dem Code von main. Das sind die Prüfungen `password is not None` und der Test-Platzhalter `benutzer:passwort@models.github.ai` in tests/test_agenten.py (#43). Keine davon ist ein echtes Geheimnis.
    - `.github/workflows` ist nicht im Diff, ebenso keine Tabu-Pfade.
13. **erfüllt.** Die neuen Tests laufen nur gegen 127.0.0.1 (Server mit `port=0`, ProxyHandler leer). Die einzige fremde Domain ist `shop.example` als Testdatum und wird nicht abgerufen. Preisquellen werden nicht über das Netz abgefragt.

## Code-Qualität (Zustand.hinzufuegen / _angebot_erfassen)
- Lock und Rollback sind korrekt (siehe AK5). Der Rückgabewert wird noch unter `_lock` berechnet, es gibt also kein TOCTOU.
- Der Schutz bleibt erhalten:
  - `X-Schnapper: 1` wird in `do_POST` vor `_angebot_erfassen` geprüft.
  - Das Größenlimit `1 <= Content-Length <= MAX_ANGEBOT (4096)` gilt weiter, dazu laufen `register.pruefe` und `Angebot.aus_dict` mit den verschärften `geld()`/URL-Prüfungen aus #42.
  - Die Tests ak2_ohne_header_403 und ak2_zu_gross_413 sind grün.
- Im Frontend ist kein `innerHTML` neu dazugekommen. `angebotSpeichern` setzt nur `textContent`, und index.html enthält keine Inline-Skripte oder on*-Handler.
- Kleinigkeit ohne Auswirkung auf das Urteil: Der Test greift über einen gepatchten `Verlauf.laden` auf das private Attribut `Verlauf._daten` zu. Das ist pragmatisch, aber an die Implementierung gekoppelt.

## Hinweis für COMMAND
Ein normaler `git push origin agent/master/20261022-21` reicht (Fast-Forward von 6dbeb82 auf 1833417). `team/handoff/` bleibt unversioniert.
