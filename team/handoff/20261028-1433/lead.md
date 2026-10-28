# LEAD – Lauf 20261028-1433

## Gewählte Aufgabe
- **F3 / S-010 / PR #40**: Merkliste/Preisalarme sichern und wiederherstellen.
- Lücke: Ein Merkeintrag mit dem Schlüssel `"__proto__"` wird beim Wiederherstellen **stillschweigend verworfen**. Er wird nicht als ungültig gemeldet.
- Branch: **`agent/master/20261022-22`** (bestehender Team-Branch, Kopf `f0cc84c`, 4 Commits vor main 6dbe114, 0 dahinter). Hier wird fortgesetzt, es gibt keinen neuen Branch und keinen neuen PR.

## Begründung mit Beleg
- **Auswahlregel:** Einen offenen Team-Draft-PR fortzusetzen hat Vorrang. #41 und #45 wurden zuletzt viel bearbeitet. #40 wurde seit dem 23.10. (`f0cc84c`) nicht mehr angefasst.
- **Akzeptanzkriterium der Arbeitsliste F3:** „MAX_MERK/MAX_ALARME prüfen, **ungültige melden**“.
- **Beleg im Code** (`app/schnapper/web/app.js` auf `origin/agent/master/20261022-22`):
  - Z. 395: `const ids = Object.keys(obj.merkliste);`. `JSON.parse` legt `"__proto__"` als **eigenen** Schlüssel an, er ist also in `ids` enthalten.
  - Z. 399: `const merk = {};` ist ein normales Objekt mit `Object.prototype`.
  - Z. 403: `istText(id, 1, 200)` lässt `"__proto__"` durch.
  - Z. 414: `merk[id] = neu;`. Bei `id === "__proto__"` ruft das den Setter von `Object.prototype.__proto__` auf. Dadurch wird der **Prototyp** von `merk` ersetzt, ein Eintrag entsteht nicht.
  - Folge: `Object.keys(merk)` und `JSON.stringify(merk)` (in `speicher.schreiben`) enthalten den Eintrag nicht. Die Zählung „Wiederhergestellt: n gemerkt“ (Z. ~463) stimmt, aber `fehler` bleibt leer. Der Eintrag geht verloren, **ohne gemeldet zu werden**.
  - Ohne localStorage (Ersatzspeicher `speicher.ersatz`) bleibt außerdem ein Objekt mit manipuliertem Prototyp im Arbeitsspeicher. `id in merkliste()` (Z. 65 und 348) prüft auch die Prototypkette.
- **Selbst geprüft** mit Node, gleiche Logik:
  `JSON.parse('{"merkliste":{"__proto__":{"titel":"x"},"a":{"titel":"y"}}}')`
  ergibt `ids = ['__proto__','a']`, aber `Object.keys(merk) = ['a']` und `JSON.stringify(merk) = {"a":…}`.
- **Testlage auf dem Branch:** Im Worktree laufen `tests.test_app_sicherung_s010` mit 10/10 OK, `unittest discover` mit 226/226 OK und `node --test` mit 10/10. Kein Test deckt `__proto__` ab (`grep __proto__ tests/test_app_sicherung_s010.py` findet nichts).
- **Freigabe:** Es ist keine neue Freigabe nötig. Die Änderung bleibt innerhalb von F3 („ungültige melden“). Formate, CSP, Server und Workflows sind nicht betroffen.

## Umsetzungsanweisung (BRAIN)
1. Auf den bestehenden Branch wechseln: `git checkout agent/master/20261022-22`.
   - Vorher prüfen: Der lokale Branch steht auf `origin/agent/master/20261022-22` (`f0cc84c`).
   - Falls er lokal nicht existiert: `git checkout -b agent/master/20261022-22 origin/agent/master/20261022-22`.
2. In `app/schnapper/web/app.js`, Funktion `sicherungPruefen`, die Schlüsselprüfung (Z. 403) so erweitern, dass `"__proto__"` als ungültiger Schlüssel gilt:
   - `if (!istText(id, 1, 200) || id === "__proto__") falsch = "Schlüssel";`
   - Die Meldung entsteht dann automatisch über die bestehende Zeile: `Merkliste: Eintrag „__proto__“ ungültig (Schlüssel)`.
   - **Zusätzlich** (Absicherung in der Tiefe) das Ergebnisobjekt prototypfrei anlegen: Z. 399 `const merk = Object.create(null);`. `JSON.stringify` und `Object.keys` funktionieren damit unverändert.
   - Sonst nichts an app.js ändern. Insbesondere `merkliste()`, das Anlegen von Merkeinträgen und die Alarme bleiben unverändert.
3. In `tests/test_app_sicherung_s010.py` einen neuen Browsertest in der Klasse `Browser` ergänzen, z. B. `test_proto_schluessel_wird_gemeldet`:
   - Die Sicherungsdatei als **Roh-Bytes** bauen, damit der Schlüssel sicher im JSON steht. Python-`json.dumps` mit `{"__proto__": …}` funktioniert. Alternativ die Bytes von Hand schreiben, zum Beispiel:
     `json.dumps(sicherung(merkliste={"__proto__": merk("Böse"), "gut": merk("Rad")})).encode()`
     Prüfen, dass der Text `"__proto__"` darin vorkommt.
   - Über die vorhandene Hilfsfunktion `self.lade(...)` laden. Davor `self.seite.click('[data-ansicht="alarme"]')`, wie in den anderen Tests.
   - Erwartet wird:
     - Die Meldung enthält `Wiederhergestellt: 1 gemerkt, 0 Alarme; 1 ungültige Einträge übersprungen`.
     - `self.fehlerliste()` hat genau 1 Eintrag und enthält `„__proto__“ ungültig (Schlüssel)`.
     - `self.stand()[0]` hat genau die Schlüssel `["gut"]`.
     - `self.seite.evaluate("Object.getPrototypeOf(JSON.parse(localStorage.getItem('schnapper.merkliste'))) === Object.prototype")` ist `True`.
     - `self.seite.evaluate("({}).titel")` ist `None`. Damit ist belegt, dass `Object.prototype` nicht verschmutzt ist.
4. **Gegenprobe:** Den neuen Test gegen das unveränderte app.js laufen lassen, also `git stash` nur für app.js oder app.js aus `f0cc84c` temporär einspielen. Er muss **rot** sein, weil die Meldung „0 ungültige“ lautet bzw. die Fehlerliste leer ist. Danach den Fix wiederherstellen.
5. Ein Commit auf `agent/master/20261022-22`:
   - Nachricht z. B. „SCHNAPPER MASTER: F3 Sicherung meldet Schlüssel __proto__ als ungültig (S-010)“.
   - Mit den Trailern aus der Systemerinnerung (Co-Authored-By und Claude-Session).
   - Kein Push durch BRAIN. Der Push erfolgt später durch COMMAND, normal und ohne Force.

## Akzeptanzkriterien (prüfbar)
1. `git diff origin/agent/master/20261022-22 --stat` zeigt **nur** `app/schnapper/web/app.js` und `tests/test_app_sicherung_s010.py`.
2. In `sicherungPruefen` wird `id === "__proto__"` als ungültiger Schlüssel behandelt. Die Fehlermeldung lautet `Merkliste: Eintrag „__proto__“ ungültig (Schlüssel)`.
3. `merk` in `sicherungPruefen` wird mit `Object.create(null)` angelegt.
4. Der neue Browsertest existiert, läuft mit dem vorinstallierten Chromium (nicht übersprungen) und ist grün.
5. Der neue Test prüft: die Meldung „1 gemerkt … 1 ungültige Einträge übersprungen“, genau 1 Fehlerlisteneintrag mit `„__proto__“ ungültig (Schlüssel)`, gespeicherte Merkliste = nur `gut`, und dass `({}).titel` undefined ist.
6. Gegenprobe: Mit dem app.js aus `f0cc84c` ist der neue Test **rot**.
7. Alle bisherigen Tests in `tests/test_app_sicherung_s010.py` bleiben grün. Bisher sind es 10, danach 11.
8. `python3 -m unittest discover -s tests`: OK, 227 Tests (226 + 1), 0 Fehler.
9. `cd cloudflare && node --test test/*.test.mjs`: 10 pass / 0 fail.
10. Folgendes bleibt unverändert:
    - Keine Änderung an `index.html`, `app.css`, `web.py`, an der CSP, an `.github/`, `team/` und `docs/`.
    - Weiterhin kein `innerHTML`.
11. Der Secret-Scan des Diffs (`sk-ant-`, `ghp_`, `github_pat_`, `AKIA`, `PRIVATE KEY`) ist leer.
12. Genau 1 neuer Commit mit beiden Trailern. Der Branch ist ein Nachfolger von `origin/agent/master/20261022-22`, also kein Rebase und kein Force.

## Testbefehle
```sh
cd /home/claude/schnapper
python3 -m unittest -v tests.test_app_sicherung_s010
python3 -m unittest discover -s tests
(cd cloudflare && node --test test/*.test.mjs)
# Gegenprobe (danach zurücksetzen!)
git show f0cc84c:app/schnapper/web/app.js > /tmp/alt.js   # bzw. Scratchpad
cp app/schnapper/web/app.js "$SCRATCH/neu.js"; cp /tmp/alt.js app/schnapper/web/app.js
python3 -m unittest -v tests.test_app_sicherung_s010     # erwartet: neuer Test FAIL
cp "$SCRATCH/neu.js" app/schnapper/web/app.js; git diff --stat
git diff origin/agent/master/20261022-22 | grep -E 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY' || echo "kein Secret"
```

**Browsertests:** Playwright mit dem vorinstallierten Chromium, das `_finde_chromium()` unter `/opt/pw-browsers` bzw. `PLAYWRIGHT_BROWSERS_PATH` findet. **Kein `playwright install`.** Es gibt keine Netz- oder Live-Abrufe außer git.

## Erlaubte Dateien
- `app/schnapper/web/app.js` (nur die Funktion `sicherungPruefen`)
- `tests/test_app_sicherung_s010.py`

**Nicht erlaubt:**
- `team/tasks.json` und `team/STATUS.md` (S-010 liegt nur in #36 vor, wie in früheren Läufen)
- `.github/workflows`, `index.html`, `web.py`
- andere Branches
- `upc_e` bzw. #41, das bleibt bis zur Freigabe gesperrt

## Hinweise für CHECK und COMMAND
- Den PR-Body von #40 bei Bedarf um einen kurzen Nachtrag ergänzen (Lauf 20261028-1433, neuer Kopf, Testzahlen). Kein Merge, keine Änderung am Draft-Status.
- Tabu: ZENTNA, JERRY AL, Beatmaster.
