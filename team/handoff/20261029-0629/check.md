# CHECK – Lauf 20261029-0629 (F3 / S-010, PR #40)

## Urteil: bestanden

Geprüft: lokaler Branch `agent/master/20261022-22`, HEAD `e1532c9a2e363283ec324af069fc2745f3aedc6b`, Basis origin `87eebba`.
`git log --oneline origin/agent/master/20261022-22..HEAD` → genau 1 Commit: `e1532c9 SCHNAPPER MASTER: F3 Wiederherstellung akzeptiert URL-Schema unabhängig von Groß-/Kleinschreibung (S-010)`.
origin/main ist Vorfahr von HEAD (`merge-base --is-ancestor` → 0).

## Kriterien
1. **Nur erlaubte Dateien** – erfüllt. `git diff --stat origin/agent/master/20261022-22..HEAD`: `app/schnapper/web/app.js` 1+/1−, `tests/test_app_sicherung_s010.py` +51. In app.js ändert sich ausschließlich Zeile 435 in `sicherungPruefen` (`/^https?:\/\//` → `/^https?:\/\//i`). Diff gegen origin/main...HEAD: nur app.css, app.js, index.html, Testdatei (bekannter PR-Umfang); nichts unter `.github/`, keine Tabu-Pfade (ZENTNA/Jerry/Beatmaster: 0 Treffer).
2. **Rundreise HTTPS:// / Https://** – erfüllt. `test_rundreise_url_schema_grossgeschrieben` ok: Export per Download, `localStorage.clear()`, Reload, Laden → `stand()[0] == vorher`, URLs byte-gleich (`HTTPS://beispiel.example/gross`, `Https://beispiel.example/misch`).
3. **Meldung/Fehlerliste** – erfüllt. Test prüft „Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen“ und `fehlerliste() == []`; grün.
4. **Andere Schemata bleiben ungültig** – erfüllt. `test_url_anderes_schema_grossgeschrieben_bleibt_ungueltig` ok („„js-gross“ ungültig (url)“, nur „gut“ übernommen); `test_ak6_ak7_gemischt_und_xss` ok. Eigene Regex-Probe (node): `JAVASCRIPT:alert(1)`, `javascript://x`, `data:…`, `FTP://a`, ` HTTPS://a`, `xhttps://a`, `https:/a` → alle false (Anker `^` bleibt).
5. **Server-Beleg** – erfüllt. `ServerUrlSchema.test_server_nimmt_grossgeschriebenes_schema_unveraendert_an` ok (HTTPS:// und Https://, URL unverändert, fester `jetzt`).
6. **Gegenprobe (selbst durchgeführt)** – erfüllt. sha256 neu `2fe74f5bef20bc432d1aa88042acb367f974ad1b2e3e9963c026037868bc18cc`; `git show 87eebba:app/schnapper/web/app.js` eingesetzt; Ergebnis:
   - FAIL T1: `'Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen' not found in 'Wiederhergestellt: 0 gemerkt, 0 Alarme; 2 ungültige Einträge übersprungen'`
   - FAIL T2: `'…1 gemerkt, 0 Alarme; 1 ungültige…' not found in '…0 gemerkt, 0 Alarme; 2 ungültige…'`
   - test_ak6_ak7 ok; `Ran 3 tests … FAILED (failures=2)`
   Zurückgesetzt (`git checkout -- app.js`), sha256 wieder `2fe74f5b…18cc`, `git status --short` leer.
7. **Modul grün, 0 Skips** – erfüllt. `python3 -m unittest tests.test_app_sicherung_s010 -v` → `Ran 21 tests … OK` (18 + 3), keine Skips, Chromium vorinstalliert (kein `playwright install`).
8. **Gesamtsuite / Cloudflare** – erfüllt. `python3 -m unittest discover -s tests` → `Ran 237 tests … OK`; `node --test test/*.test.mjs` → tests 10, pass 10, fail 0, skipped 0.
9. **Keine Fremdabrufe/Konsolenfehler** – erfüllt. tearDown (Z. 150–155) prüft `self.fremd == []` und `self.meldungen == []` (Konsolen-Errors); alle Browsertests grün.
10. **Secrets/Push** – erfüllt. +Zeilen des neuen Diffs gegen `sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw|secret|token` → 0 Treffer. HEAD lokal ≠ origin-Branch (nicht gepusht), nichts unter `.github/`.

## Kritische Prüfung neuer Lücken
- Das `i`-Flag erweitert nur auf Groß-/Kleinvarianten von `http://`/`https://`. Neu zugelassen wird damit auch `HTTP://…`; `http://` war schon vorher zugelassen, also keine neue Klasse.
- Wiederhergestellte URLs werden nur über `href` gesetzt, wenn `/^https:\/\//` (case-sensitiv, nur https) passt (app.js Z. 108, 326, 373). `HTTPS://`- oder `HTTP://`-Einträge werden also ohne Link angezeigt; ein ausführbares Schema kann nicht in `href` gelangen. **Keine neue XSS-/Schema-Lücke.**
- Hinweise (keine Mängel dieses Laufs): Link-Anzeige für `HTTPS://` fehlt weiterhin (aus main, laut lead bewusst nicht geändert); id > 200 Zeichen als möglicher nächster F3-Kandidat (lead).

## Klonzustand
Am Ende `git checkout --detach origin/main`, `git status` sauber.
