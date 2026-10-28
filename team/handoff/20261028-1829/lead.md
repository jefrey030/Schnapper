# LEAD – Lauf 20261028-1829

- Start LEAD: 2026-10-28 18:31:18 UTC
- Ende LEAD: 2026-10-28 18:32:33 UTC

## Gewählte Aufgabe
**PR #39 – F2 = S-009 „Angebot in der App erfassen“**, Branch `agent/master/20261022-21`, Kopf `2666d8b` (enthält main 6dbe114, `git merge-base --is-ancestor` geprüft → **kein Merge nötig**).
Schritt: **Serverseitige Typ- und Längenprüfung der Erfassungsfelder in `POST /api/angebot`.** Nicht-Text-Werte (Objekt, Liste, Bool, null) in Textfeldern und Bool/Objekt/Liste in Geldfeldern werden mit 422 abgelehnt. `kategorie` wird serverseitig auf 100 Zeichen begrenzt (wie `maxlength="100"` im Formular).

## Begründung mit Belegen
1. #39 wurde am längsten nicht bearbeitet (zuletzt 2026-10-23 07:37 UTC, alle anderen Team-PRs am 28.10.).
2. Die F2-Akzeptanzkriterien sind durch Tests belegt, Stand `tests/test_app_erfassen_s009.py` @2666d8b: gültig `test_ak1`, ungültig 422 `test_ak3`, ohne Header 403 `test_ak2_ohne_header_403`, Größenlimit 413 `test_ak2_zu_gross_413`, Browser 390x844 ausfüllen → Treffer → CSV enthält ihn → keine Konsolenfehler `test_ak8_erfassen_und_csv_im_browser`, textContent `test_ak7_formular_und_js`. Neue Arbeit dazu erfinde ich nicht.
3. Der PR-Body (CHECK-Hinweise Lauf 20261022-2128, Punkte 2 und 3) nennt offene Lücken. Diese habe ich in einer Kopie von 2666d8b außerhalb des Klons (`git archive`, Server nur 127.0.0.1) **praktisch nachgewiesen**:
   - `{"titel": {"a":1}}` → **201**, CSV-Zeile enthält `{'a': 1}` als Titel
   - `{"titel": ["x"]}` → **201** (`['x']`), `{"titel": true}` → **201** (`True`)
   - `{"kategorie": {"k":1}}` → **201** (`{'k': 1}`)
   - `{"kategorie": "k"*3000}` → **201**, obwohl das Formular `maxlength="100"` hat (`app/schnapper/web/index.html` im PR-Diff)
   - `{"preis": true}` → 422 (wird schon korrekt abgelehnt)
   - Ursache: `app/schnapper/web.py` @2666d8b Z. 308 übernimmt Rohwerte ungeprüft (`daten = {k: eingabe[k] for k in ERFASSEN_FELDER if k in eingabe}`). `Angebot.aus_dict` → `text()` in `app/schnapper/angebot.py` Z. 142–144 macht daraus per `str(wert)` beliebigen Text.
4. Die CSV-Formel-Injection (CHECK-Hinweis 1) bleibt **ausdrücklich außen vor**: Sie bräuchte eine Import-Gegenstelle in `einlesen.py` (Roundtrip) und passt nicht in ~20 Minuten.

## Branch
`agent/master/20261022-21` (bestehender PR-Branch #39). Darauf aufsetzen und einen normalen Commit anlegen. Kein neuer Branch, kein Rebase, kein Force-Push und kein neuer PR. Arbeiten in einem eigenen Worktree außerhalb des Klons (z. B. `/home/claude/brain-wt-1829`).

## Akzeptanzkriterien (nummeriert, prüfbar)
1. `POST /api/angebot` mit `X-Schnapper: 1` antwortet **422** mit JSON-Feld `fehler`, wenn eines der Textfelder `titel`, `zustand`, `url`, `kategorie` vorhanden ist und **kein `str`** ist (Objekt, Liste, Zahl, Bool, `null`). Der Fehlertext nennt den Feldnamen. Ausnahme, falls BRAIN so entscheidet und begründet: `null` darf bei optionalen Feldern als „leer“ gelten.
2. Ebenso **422**, wenn `preis`, `versand` oder `referenzpreis` vorhanden ist und weder `str` noch `int`/`float` ist. **`bool` zählt nicht als Zahl** (`isinstance(x, bool)` explizit ausschließen). Zahlen wie `450` und `19.9` bleiben gültig (201).
3. `kategorie` mit mehr als 100 Zeichen (nach `strip`) ergibt **422**. Genau 100 Zeichen ergeben 201. Die Grenze steht als Konstante in `web.py` (z. B. `MAX_KATEGORIE = 100`) und ist gleich dem `maxlength` in `index.html`.
4. Bei jeder Ablehnung nach AK 1–3 bleiben Liste und Beispielstatus unverändert (`/api/suche` vorher == nachher, wie in `test_ak3`). Der Preisverlauf wird nicht beschrieben.
5. Bestehendes Verhalten bleibt gleich: `GUELTIG` ergibt 201, Felder außerhalb der Whitelist (`quelle`, `id`, `erfasst_am`, `waehrung`) werden weiter ignoriert (`test_ak4` grün), 400/403/411/413 unverändert.
6. Neue Tests in `tests/test_app_erfassen_s009.py` (neue Klasse, z. B. `ErfassenTypen`) decken mit `subTest` mindestens ab: `titel` als dict/list/bool/int, `kategorie` als dict, `preis` als bool/list/dict, `kategorie` 101 vs. 100 Zeichen, `preis` als JSON-Zahl 450 → 201.
7. **Gegenprobe:** Die neuen Tests schlagen mit `web.py` von 2666d8b fehl (mindestens die Fälle dict-Titel und 101-Zeichen-Kategorie). Ausgabe dokumentieren.
8. Die Prüfung steckt nur im Handler-Pfad `/api/angebot` (`_angebot_erfassen` oder eine Hilfsfunktion in `web.py`). **`angebot.py` und `einlesen.py` werden nicht geändert**, damit sich das Verhalten von CSV/JSON-Import nicht verschiebt.
9. `python3 -m unittest discover -s tests` ist komplett grün, 0 Fehler. Die Anzahl entspricht 233 plus den neuen Tests, Skips höchstens wie vorher. Der Browsertest `test_ak8_erfassen_und_csv_im_browser` läuft tatsächlich und wird nicht übersprungen.
10. `cd cloudflare && node --test test/*.test.mjs` ergibt 10 pass / 0 fail.
11. Der Diff gegen 2666d8b berührt nur die erlaubten Dateien. Keine Änderung an `.github/`, `team/` oder `cloudflare/`. Secret-Scan des Diffs ist leer (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY).
12. Commit ist ein Fast-Forward-Nachfolger von 2666d8b mit den Trailern Co-Authored-By und Claude-Session. Push normal ohne Force (nur COMMAND). Der PR bleibt Draft, der Body bekommt den Abschnitt „Update Lauf 20261028-1829“ (bisheriger Text unverändert).

## Erlaubte Dateien
- `app/schnapper/web.py`
- `tests/test_app_erfassen_s009.py`
- optional nur zum Gleichziehen der Konstante: `app/schnapper/web/index.html` (keine Layoutänderung)

Nicht erlaubt: `app/schnapper/angebot.py`, `app/schnapper/einlesen.py`, `app.js`, `app.css`, `team/*`, `.github/*`, `cloudflare/*`.

## Testbefehle
```
python3 -m unittest tests.test_app_erfassen_s009 -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Gegenprobe (AK 7): die neue Testdatei gegen `git show 2666d8b:app/schnapper/web.py` laufen lassen, z. B. web.py im Worktree kurz zurücksetzen und danach wiederherstellen.
Playwright nutzt das vorinstallierte Chromium (`_finde_chromium()`, `/opt/pw-browsers`), **kein `playwright install`**. Kein Netzzugriff nach außen, Server nur 127.0.0.1, keine Live-Preisquellen.

## Hinweise für BRAIN/CHECK
- Kleinste Lösung: Vor `Angebot.aus_dict` die Werte in `daten` prüfen, mit einer Schleife über die Text- und Geldfelder und einem frühen `return self._json(UNPROCESSABLE_ENTITY, …)`.
- Was das Formular sendet (`Object.fromEntries(new FormData(form))`), sind immer Strings. Der Browserweg bleibt also unberührt.
- Die Merge-Entscheidung liegt bei Jefrey. Fremde Branches und PRs werden nicht angefasst.

Ende LEAD: 2026-10-28 18:32:33 UTC
