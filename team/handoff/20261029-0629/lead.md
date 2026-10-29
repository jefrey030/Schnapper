# LEAD – Lauf 20261029-0629

## Aufgabe
- F-Punkt: **F3 = S-010** „Merkliste/Preisalarme sichern und wiederherstellen (JSON)“
- PR: **#40** (Draft), Branch `agent/master/20261022-22`
- Ausgangskopf: `87eebba8e310777d1dbc4b169eea62f009464393`
- Wahlgrund: faire Rotation, F3 zuletzt 20261029-0029 und damit am längsten unberührt (INDEX.md).
- origin/main `6dbe114` ist im Branch enthalten (`git merge-base --is-ancestor origin/main origin/agent/master/20261022-22` → Exit 0). **Kein Merge nötig.**
- Diff des Branches zu main: `app/schnapper/web/app.js` (+174/−2), `index.html` (+10), `app.css` (+7), `tests/test_app_sicherung_s010.py` (+469).

## Belegter Mangel: Rundreise verliert Merkeinträge mit großgeschriebenem URL-Schema
Akzeptanz F3: „Sichern → Speicher leeren → Wiederherstellen = gleicher Stand.“ Das gilt nicht, sobald ein gemerktes Angebot eine URL wie `HTTPS://…` (oder `Https://…`) hat.

Belegkette (Stand Branch 87eebba):
1. **Server akzeptiert das Angebot**: `app/schnapper/angebot.py:189-194` prüft `urlsplit(angebot.url).scheme != "https"`. `urlsplit` macht das Schema klein, also geht `HTTPS://example.com/a` durch. Die URL wird unverändert gespeichert (`angebot.py:154` `url=text("url")`). Selbst geprüft: `Angebot.aus_dict({... "url": "HTTPS://example.com/a" ...}).url == 'HTTPS://example.com/a'`.
2. **Server liefert sie roh an die App**: `app/schnapper/web.py:122` `"url": t.angebot.url`.
3. **Merken speichert sie roh**: `app/schnapper/web/app.js:77` `m[t.id] = { …, url: t.url, … }`. Die Sicherung exportiert sie unverändert (`app.js:391`).
4. **Wiederherstellung lehnt sie ab**: `app/schnapper/web/app.js:435`
   `else if (typeof e.url !== "string" || !(e.url === "" || /^https?:\/\//.test(e.url))) falsch = "url";`
   Die Regex ist case-sensitiv. Selbst geprüft: `/^https?:\/\//.test("HTTPS://example.com/a")` → `false`.
5. Folge: Der Eintrag wird als „Merkliste: Eintrag „…“ ungültig (url)“ gemeldet und fehlt nach der Wiederherstellung. Eine Datei, die die App selbst erzeugt hat, ergibt also nicht den gleichen Stand. Bisher deckt kein Test das ab, denn alle Test-URLs sind klein geschrieben (`tests/test_app_sicherung_s010.py:45` `merk(url="https://beispiel.example/1")`).

Nur zur Einordnung, wird in diesem Lauf **nicht** geändert: Die Link-Anzeige auf main (`app.js:108/326/373` im Branch, `/^https:\/\//` ohne `i`) zeigt für solche Einträge keinen Link. Das ist Darstellung, kein Datenverlust, und kommt aus main.

## Umsetzungsplan (BRAIN)
1. Auf dem Branch `agent/master/20261022-22` ab `87eebba` arbeiten (kein Rebase, kein Force-Push).
2. In `app/schnapper/web/app.js:435` das Schema ohne Rücksicht auf Groß-/Kleinschreibung prüfen: `/^https?:\/\//i.test(e.url)`. Sonst nichts an der Prüflogik ändern. `javascript:` und andere Schemata bleiben „ungültig (url)“. Die URL wird unverändert übernommen, ohne Normalisierung, damit die Rundreise byte-gleich bleibt.
3. Neue Tests in `tests/test_app_sicherung_s010.py`:
   - **T1 Browser-Rundreise** (`test_rundreise_url_schema_grossgeschrieben`): Merkliste per `localStorage.setItem('schnapper.merkliste', …)` mit zwei Einträgen anlegen, mit `merk(url="HTTPS://beispiel.example/gross")` und `merk(url="Https://beispiel.example/misch")`, dann neu laden. Danach exportieren (`expect_download`), `localStorage.clear()`, neu laden und die Datei laden. Erwartet wird „Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen“, eine leere Fehlerliste und `self.stand()[0]` gleich dem Stand vorher (URLs unverändert).
   - **T2 Abgrenzung** (im selben Test oder separat): `merk(url="JAVASCRIPT:alert(1)")` wird weiterhin als „ungültig (url)“ gemeldet und nicht übernommen.
   - **T3 Server-Beleg (ohne Browser)**: `Angebot.aus_dict(...)` mit `url="HTTPS://beispiel.example/x"` wirft keinen Fehler und behält die URL. So ist belegt, dass solche Einträge real entstehen können.
4. Pflicht-Gegenprobe: `app.js` vorübergehend auf 87eebba zurücksetzen (`git show 87eebba:app/schnapper/web/app.js > app/schnapper/web/app.js`), dann muss T1 rot sein. Danach wiederherstellen und die sha256 vergleichen.
5. Ein Commit, Nachricht z. B. „SCHNAPPER MASTER: F3 Wiederherstellung akzeptiert URL-Schema unabhängig von Groß-/Kleinschreibung (S-010)“. Nicht pushen, das macht COMMAND nach CHECK.

## Erlaubte Dateien (eng)
- `app/schnapper/web/app.js` (nur Zeile 435, Regex-Flag `i`)
- `tests/test_app_sicherung_s010.py`

Alles andere bleibt unverändert, insbesondere `index.html` (CSP), `web.py`, `angebot.py`, `team/*`, `.github/*`.

## Akzeptanzkriterien
1. Der Diff gegen 87eebba betrifft nur die zwei erlaubten Dateien. In `app.js` ändert sich genau die URL-Prüfung in `sicherungPruefen` (ca. Zeile 435).
2. Eine von der App selbst exportierte Sicherung mit Merkeinträgen `HTTPS://…` / `Https://…` stellt nach `localStorage.clear()` + Neuladen exakt denselben `schnapper.merkliste`-Stand wieder her (T1).
3. Meldung nach T1: „Wiederhergestellt: 2 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen“, `#sicherung-fehler` ist leer.
4. URLs mit anderem Schema (`javascript:`/`JAVASCRIPT:`) werden weiter als „ungültig (url)“ gemeldet und nicht übernommen (T2, dazu der bestehende `test_ak6_ak7_gemischt_und_xss` grün).
5. T3 belegt, dass der Server `HTTPS://…` annimmt und unverändert behält.
6. **Pflicht-Gegenprobe**: Mit der alten `app.js` (87eebba) schlägt T1 fehl. Ausgabe protokollieren, danach zurücksetzen und die sha256 gleich zur neuen Datei.
7. Alle bestehenden Tests in `tests/test_app_sicherung_s010.py` bleiben grün (vorher 18) und haben **0 Skips** (Browser muss laufen).
8. Gesamtsuite `python3 -m unittest discover -s tests` OK, Cloudflare `node --test` 10/10.
9. Keine fremden Netzabrufe in den Browsertests (bestehende Route-Sperre, `self.fremd == []`), keine Konsolenfehler.
10. Secret-Scan über den neuen Commit liefert 0 Treffer. Kein Push auf main, nichts unter `.github/workflows`, kein Force-Push. Push nur durch COMMAND nach „bestanden“ von CHECK.

## Testbefehle
```
cd /home/claude/schnapper
python3 -m unittest tests.test_app_sicherung_s010 -v
python3 -m unittest discover -s tests
cd cloudflare && node --test test/*.test.mjs
```
Hinweis: Die Browsertests laufen mit Playwright und dem **vorinstallierten Chromium** (`_finde_chromium()` im Test findet es selbst). **Kein `playwright install`.**

## Verboten
- Push auf `main`, Force-Push, Rebase des PR-Branches
- Änderungen an `.github/workflows`
- Secrets lesen, schreiben oder ausgeben
- Live-Netzabrufe (Tests nur gegen lokalen Server mit Beispieldaten)

## Hinweis für spätere F3-Läufe (nicht jetzt)
- Ein zweiter, ähnlicher Rundreisebruch: Der Server begrenzt die Angebots-`id` nicht (`angebot.py:152`, selbst geprüft mit einer 300 Zeichen langen id), die Wiederherstellung verlangt aber `istText(id, 1, 200)` (`app.js:431`). Gemerkte Angebote mit id > 200 Zeichen gehen beim Wiederherstellen verloren. Möglicher Kandidat für den nächsten F3-Lauf.

## Klonzustand
Der Klon `/home/claude/schnapper` steht detached auf origin/main `6dbe114` und ist sauber (`git status` leer). Die temporäre Worktree wurde entfernt.
