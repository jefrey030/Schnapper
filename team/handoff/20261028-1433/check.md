# CHECK – Lauf 20261028-1433

- Start: 2026-10-28T14:38:44Z
- Ende:  2026-10-28T14:39:50Z
- Geprüft: Commit 4274324 (agent/master/20261022-22, lokal), eigener Worktree /home/claude/check-wt (detached). Der Worktree wurde danach entfernt. Kein Code geändert, nichts committet, nichts gepusht.

## Urteil: **bestanden**

## Testzahlen (selbst ausgeführt)
- `python3 -m unittest -v tests.test_app_sicherung_s010`: Ran 11, OK. 0 übersprungen, `test_proto_schluessel_wird_gemeldet` lief mit dem vorinstallierten Chromium und ist „ok“.
- `python3 -m unittest discover -s tests`: Ran 227, OK.
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0, skipped 0.
- Gegenprobe: app.js aus `origin/agent/master/20261022-22` (f0cc84c) eingespielt, dann den neuen Test ausgeführt. Ergebnis: **FAIL**, Meldung `... not found in 'Wiederhergestellt: 1 gemerkt, 0 Alarme; 0 ungültige Einträge übersprungen'`. Danach `git checkout -- app.js`; der Status war sauber.

## Akzeptanzkriterien
1. ✔ `git diff origin/agent/master/20261022-22...HEAD --stat` zeigt nur `app/schnapper/web/app.js` (4 ±) und `tests/test_app_sicherung_s010.py` (+15).
   - `origin/main...HEAD` zeigt zusätzlich app.css und index.html. Diese stammen aus den früheren PR-#40-Commits, nicht aus diesem Lauf.
2. ✔ Z. 403 lautet `if (!istText(id, 1, 200) || id === "__proto__") falsch = "Schlüssel";`. Die Meldung entsteht über die bestehende Zeile `Merkliste: Eintrag „${kurz(id)}“ ungültig (${falsch})`.
3. ✔ Z. 399 lautet `const merk = Object.create(null);`. Sonst gibt es keine Änderung in app.js; nur `sicherungPruefen` ist betroffen.
4. ✔ Der Test existiert, lief und ist grün (siehe oben).
5. ✔ Der Test prüft:
   - die Meldung „1 gemerkt, 0 Alarme; 1 ungültige Einträge übersprungen“,
   - `len(fehlerliste)==1` mit `„__proto__“ ungültig (Schlüssel)`,
   - die gespeicherten Schlüssel `["gut"]`,
   - den Prototyp des geparsten localStorage-Inhalts,
   - `({}).titel` ist None,
   - dass `"__proto__"` in den Roh-Bytes steht.
6. ✔ Die Gegenprobe ist rot (siehe oben).
   - Zur Plausibilität: Der Test würde auch fehlschlagen, wenn nur `Object.create(null)` geändert wäre. Dann entstünde `__proto__` als eigener Eintrag und es hieße „2 gemerkt“. Beide Teile des Fixes sind also abgedeckt.
7. ✔ Vorher 10, jetzt 11 Tests in diesem Modul, alle grün.
8. ✔ 227 Tests, OK.
9. ✔ 10 pass / 0 fail.
10. ✔ Keine Änderung an index.html, app.css, web.py, CSP, .github/, team/ oder docs/ in diesem Commit.
    - Im Diff zu main gibt es keine Pfade unter `.github/`, `team/` oder `docs/` und keine Tabu-Pfade (ZENTNA, JERRY AL, Beatmaster).
    - Kein neues `innerHTML`; es steht nur im bestehenden Kommentar in Z. 2.
11. ✔ Der Secret-Scan auf `origin/main...HEAD` ist leer. Gesucht wurde nach sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, password/secret-Zuweisungen.
12. ✔ Genau 1 neuer Commit (`rev-list --count` = 1). Er ist Nachfolger von `origin/agent/master/20261022-22` (`merge-base --is-ancestor` erfolgreich). Beide Trailer (Co-Authored-By, Claude-Session) sind vorhanden. Er ist nicht gepusht.

## Regressionsprüfung (merk ohne Prototyp)
- `ergebnis.merkliste` wird nur so verwendet:
  - in `speicher.schreiben`: `ersatz[name] = wert` und `JSON.stringify`,
  - über `Object.keys(...)`.
- Ohne localStorage liefert `merkliste()` das Objekt ohne Prototyp aus `speicher.ersatz`. Die Prüfung `typeof === "object"` und `!Array.isArray` greift weiter.
- Die Verbraucher nutzen nur `in`, `delete`, Zuweisung, `Object.keys`, Spread (`{ id, ...alt }` auf den Einträgen; die Einträge selbst sind normale Objekte) und `JSON.stringify`. Alle funktionieren mit einem Objekt ohne Prototyp.
- Kein Aufruf von `hasOwnProperty`, `toString` oder `valueOf` und keine String-Interpolation auf merkliste/merk. Die zwei `p.toString()` (Z. 51, 269) betreffen URLSearchParams.
- Mit localStorage liefert `JSON.parse` ohnehin wieder ein normales Objekt; der Test belegt das.
- `abweisen` gibt weiterhin `{}` zurück. Das ist harmlos, weil es nie gespeichert wird.

## Hinweise
- Der Push erfolgt durch COMMAND, normal und ohne Force. PR #40 bleibt Draft; ein kurzer Nachtrag im PR-Body ist optional.
