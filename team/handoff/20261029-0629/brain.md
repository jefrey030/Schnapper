# BRAIN – Lauf 20261029-0629 (F3 / S-010)

## Branch / Commit
- Branch `agent/master/20261022-22`, Ausgangskopf 87eebba (geprüft), lokal, NICHT gepusht.
- Commit: `e1532c9a2e363283ec324af069fc2745f3aedc6b`
  „SCHNAPPER MASTER: F3 Wiederherstellung akzeptiert URL-Schema unabhängig von Groß-/Kleinschreibung (S-010)“

## Geänderte Dateien (gegen 87eebba)
- `app/schnapper/web/app.js` +1/−1 (Zeile 435: `/^https?:\/\//i.test(e.url)`, sonst nichts)
- `tests/test_app_sicherung_s010.py` +51/−0
  - T1 `Browser.test_rundreise_url_schema_grossgeschrieben` (HTTPS:// + Https://, Export → clear → Reload → Laden; Meldung „Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen“, Fehlerliste leer, Stand identisch, URLs unverändert)
  - T2 `Browser.test_url_anderes_schema_grossgeschrieben_bleibt_ungueltig` (JAVASCRIPT:alert(1) → „ungültig (url)“, nicht übernommen; daneben gültiger HTTPS://-Eintrag übernommen)
  - T3 `ServerUrlSchema.test_server_nimmt_grossgeschriebenes_schema_unveraendert_an` (Angebot.aus_dict mit HTTPS:// und Https://, fester `jetzt`, URL unverändert)

## Testergebnisse
- Modul `python3 -m unittest tests.test_app_sicherung_s010 -v`: 21 Tests OK (vorher 18, +3), 0 Skips, 0 Fehler. Browser lief mit vorinstalliertem Chromium.
- Gesamtsuite `python3 -m unittest discover -s tests`: 237 Tests OK, 0 Skips.
- Cloudflare `node --test test/*.test.mjs`: 10/10 pass, 0 fail, 0 skipped.
- Browsertests: tearDown prüft `self.fremd == []` und keine Konsolenfehler – alle grün.
- Secret-Scan (Muster key/secret/token/password/private key/ghp_/github_pat_/AKIA/sk-) über die +Zeilen des Commits: 0 Treffer.

## Pflicht-Gegenprobe
- `git show 87eebba:app/schnapper/web/app.js > app/schnapper/web/app.js`, dann T1, T2, T3:
  - T1 FAIL: `'Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen' not found in 'Wiederhergestellt: 0 gemerkt, 0 Alarme; 2 ungültige Einträge übersprungen'`
  - T2 FAIL: erwartet „1 gemerkt … 1 ungültige“, erhalten „0 gemerkt, 0 Alarme; 2 ungültige“ (der HTTPS://-Eintrag wurde mit verworfen)
  - T3 ok (erwartet, prüft nur den Server)
  - Ergebnis: Ran 3, FAILED (failures=2)
- Wiederhergestellt; sha256 vorher = nachher = `2fe74f5bef20bc432d1aa88042acb367f974ad1b2e3e9963c026037868bc18cc`.

## Abweichungen vom Plan
- Keine inhaltlichen. T2 als eigener Test umgesetzt und enthält zusätzlich einen gültigen `HTTPS://`-Eintrag, deshalb ist T2 in der Gegenprobe ebenfalls rot (zusätzlicher Beleg).
- T3 übergibt einen festen Zeitpunkt `jetzt`, damit das Ergebnis nicht von der Uhr abhängt.

## Klonzustand
- Branch mit Commit bleibt lokal; Klon am Ende `git checkout --detach origin/main`, sauber.
