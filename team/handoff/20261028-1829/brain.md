# BRAIN – Lauf 20261028-1829

- Start BRAIN: 2026-10-28 18:32:53 UTC
- Ende BRAIN: 2026-10-28 18:35:06 UTC
- Branch: `agent/master/20261022-21` (PR #39), alter Kopf `2666d8b` (enthält main 6dbe114, kein Merge nötig)
- Neuer Commit: `fd16763e43bfa1370039b85b3d7d5625aba6a993` (Fast-Forward-Nachfolger von 2666d8b, **nicht gepusht**, das macht COMMAND)
- Gearbeitet direkt im Klon /home/claude/schnapper (Vorgabe des Auftrags: Branch ausgecheckt lassen), nicht in einem separaten Worktree.

## Geänderte Dateien (`git diff --stat 2666d8b HEAD`)
```
 app/schnapper/web.py            | 23 ++++++++++++++++++++++
 tests/test_app_erfassen_s009.py | 43 +++++++++++++++++++++++++++++++++++++++++
 2 files changed, 66 insertions(+)
```
`index.html` blieb unverändert, weil dort schon `maxlength="100"` steht. Ein Test prüft die Gleichheit mit der Konstante.

## Kurzbeschreibung
- `web.py`: neue Konstanten `TEXT_FELDER`, `GELD_FELDER`, `PFLICHT_FELDER`, `MAX_KATEGORIE = 100` und die Hilfsfunktion `typfehler(daten)`. `_angebot_erfassen` ruft sie direkt nach der Whitelist und **vor** `Angebot.aus_dict` auf. Bei einem Fehler kommt sofort 422 `{"fehler": "Feld '<name>' …"}`; Liste und Verlauf bleiben unberührt.
  - Textfelder: nur `str`. Geldfelder: `str`, `int` oder `float`, `bool` ist explizit ausgeschlossen.
  - Entscheidung zu `null` (AK 1, Ausnahme): Bei den optionalen Feldern `zustand`, `kategorie`, `versand` und `referenzpreis` gilt `null` als leer, so wie bisher in `aus_dict`. Bestehende Clients ändern dadurch ihr Verhalten nicht. Bei den Pflichtfeldern `titel`, `preis` und `url` ergibt `null` eine 422 „Feld '<name>' fehlt“.
  - `kategorie` darf nach `strip` höchstens 100 Zeichen haben. Mit 101 Zeichen kommt 422, genau 100 (auch mit umgebenden Leerzeichen) ergibt 201.
- `angebot.py` und `einlesen.py` sind unverändert, der Import verhält sich also wie bisher.
- Neue Testklasse `ErfassenTypen` in `tests/test_app_erfassen_s009.py` mit 4 Tests und subTests:
  - Textfelder: dict, list, bool, int und null für titel, url, zustand und kategorie
  - Geldfelder: bool, list, dict und null für preis, versand und referenzpreis
  - gültige Fälle: Zahlen 450, 19.9 und 0, dazu null in optionalen Feldern → 201
  - Kategorielänge 101 gegen 100, Konstante gleich maxlength in index.html

Jeder 422-Fall prüft den Feldnamen im Fehlertext und dass `/api/suche` vorher und nachher gleich ist.

## Gegenprobe (AK 7), neue Tests gegen web.py @2666d8b
`FAILED (failures=17, errors=1)` bei 4 Tests.
- **Fehlschlag:** dict-Titel → `201 != 422`; ebenso list-, bool- und int-Titel sowie dict-, bool- und int-Kategorie; versand false/[] → 201.
- **Fehler:** `test_kategorie_laenge` → ImportError `MAX_KATEGORIE`.
- **Einzeln nachgeprüft:** kategorie mit 101 Zeichen → **201** auf dem alten Stand.

Auszug:
```
ERROR: test_kategorie_laenge (tests.test_app_erfassen_s009.ErfassenTypen.test_kategorie_laenge)
ImportError: cannot import name 'MAX_KATEGORIE' from 'schnapper.web' (/home/claude/schnapper/app/schnapper/web.py)
FAIL: test_geldfelder_nur_text_oder_zahl (tests.test_app_erfassen_s009.ErfassenTypen.test_geldfelder_nur_text_oder_zahl) (feld='preis', wert=True)
AssertionError: 'preis' not found in 'Preis darf kein Wahrheitswert sein'
FAIL: test_geldfelder_nur_text_oder_zahl (tests.test_app_erfassen_s009.ErfassenTypen.test_geldfelder_nur_text_oder_zahl) (feld='preis', wert=[450])
AssertionError: 'preis' not found in 'Preis nicht lesbar: [450]'
FAIL: test_geldfelder_nur_text_oder_zahl (tests.test_app_erfassen_s009.ErfassenTypen.test_geldfelder_nur_text_oder_zahl) (feld='preis', wert={'p': 1})
AssertionError: 'preis' not found in "Preis nicht lesbar: {'p': 1}"
FAIL: test_geldfelder_nur_text_oder_zahl (tests.test_app_erfassen_s009.ErfassenTypen.test_geldfelder_nur_text_oder_zahl) (feld='preis', wert=None)
AssertionError: 'preis' not found in 'Preis nicht lesbar: None'
FAIL: test_geldfelder_nur_text_oder_zahl (tests.test_app_erfassen_s009.ErfassenTypen.test_geldfelder_nur_text_oder_zahl) (feld='versand', wert=False)
AssertionError: 201 != 422 : {'id': 'e-6bba6f86', 'anzahl': 1}
FAILED (failures=17, errors=1)
```

## Eigene Testergebnisse (nach Umsetzung)
- `python3 -m unittest tests.test_app_erfassen_s009 -v` → **Ran 21, OK**. `test_ak8_erfassen_und_csv_im_browser` lief tatsächlich mit dem vorinstallierten Chromium und wurde nicht übersprungen.
- `python3 -m unittest discover -s tests`:
  - neu: **Ran 237, OK (skipped=1)**
  - vorher: 233, OK (skipped=1)
  - also +4 neue Tests, Skips unverändert
- `cd cloudflare && node --test test/*.test.mjs` → **10 tests, 10 pass, 0 fail**
- Secret-Scan des Diffs (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY): leer.
- Nicht angefasst: `.github/`, `team/`, `cloudflare/`. Keine Netzaufrufe nach außen, Server nur auf 127.0.0.1.

## Offen
- Die CSV-Formel-Injection (CHECK-Hinweis 1) bleibt laut LEAD bewusst außen vor.
- Für COMMAND: normal pushen ohne Force, den PR als Draft lassen, im PR-Body den Abschnitt „Update Lauf 20261028-1829“ ergänzen.
