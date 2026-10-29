# CHECK – Lauf 20261029-0729

- Start (UTC): 2026-10-29T07:35:14Z
- Ende (UTC): 2026-10-29T07:36:37Z (plus Bericht)
- Geprüft: Branch `agent/master/20261022-23`, HEAD `7b9ae8358fa9795814175b273612ecbbdb230362`, Basis `origin/agent/master/20261022-23` = `b03b986`

## Urteil: **bestanden**

## Akzeptanzkriterien

| # | Kriterium | Ergebnis | Beleg |
|---|-----------|----------|-------|
| 1 | Start über absoluten, relativen Symlink und Kette aus fremdem Ordner | erfüllt | `test_start_ueber_symlink` ok (3 Subtests). Eigene Läufe: Kette `../b in/s2` → `s1` → Skript in „Mein Ordner“ (Leerzeichen): HTTP 200, „SCHNAPPER läuft: http://127.0.0.1:8952“, Datei `…/Mein Ordner/app/vorlagen/meine-angebote.csv`. Direkter Exec über Link (`../b in/s2`, chmod +x) ebenfalls 200. Danach alle Ports frei (`ss -ltn`). |
| 2 | Direkter Aufruf wie bisher, 19 alte Tests grün | erfüllt | Modul: 20 Tests OK (19 alt + 1 neu). Eigene Läufe `bash start-schnapper.sh` im Repo-Ordner und `bash "<abs. Pfad mit Leerzeichen>/start-schnapper.sh"`: jeweils 200. Alte Testaufrufe unverändert (nur optionaler Parameter `skript=SKRIPT`). |
| 3 | Datei-Argument relativ zum Aufrufort | erfüllt | `test_relative_datei_zum_aufrufort` ok. Eigener Lauf über Symlink-Kette mit `eigene.csv` aus `auf/arbeit dir`: Datei `…/auf/arbeit dir/eigene.csv`, 200. Fehlende relative Datei → „Datei nicht gefunden: …/auf/arbeit dir/gibtsnicht.csv“, kein Start. |
| 4 | Fehlendes/falsches/relatives Python wie bisher | erfüllt | `test_fehlendes_python`, `test_falscher_interpreter_wird_abgelehnt`, `test_relativer_python_pfad_zum_aufrufort` ok. Python-Block steht vor der Pfadauflösung, `SCHNAPPER startet` erst in Z. 112. |
| 5 | Nur Builtins + Python, Host fest, exec, set -eu, Shebang, ausführbar | erfüllt | grep in Code-Zeilen nach dirname/readlink/realpath/basename: keine. Z. 1 `#!/usr/bin/env bash`, Z. 31 `set -eu`, Z. 115 `exec "$PY" -u -m schnapper.web … --host 127.0.0.1`. `git ls-files -s`: 100755. Statische Tests ok. |
| 6 | Hinweis „auf echtem Gerät ungetestet“ | erfüllt | je 1 Treffer in `start-schnapper.sh` und `docs/HANDY-START.md`. |
| 7 | Pflicht-Gegenprobe | erfüllt | Alte Datei aus `b03b986` eingesetzt → `FAILED (failures=3)`, alle drei Subtests „Skript beendet (Exit 2): Datei nicht gefunden: /tmp/tmp…/bin/app/vorlagen/meine-angebote.csv“. Wiederhergestellt + chmod 755: sha256 vorher = nachher = `0c5c0256…cd15`; `git status --short` leer. |
| 8 | Modul, Gesamtsuite, Cloudflare grün | erfüllt | Modul 20/20 OK (0 Skips); `unittest discover -s tests` 236 OK (0 Skips); `node --test` 10 pass, 0 fail, 0 skipped. `bash -n` OK. |
| 9 | Genau ein Commit über b03b986, Präfix, kein Push | erfüllt | `git log origin/…..HEAD`: nur `7b9ae83 SCHNAPPER MASTER: F5 Startskript …`; „ahead by 1“, nicht gepusht; Attributionszeilen vorhanden. |
| 10 | Nur erlaubte Dateien, keine Secrets | erfüllt | Diff b03b986..HEAD: `start-schnapper.sh`, `tests/test_start_skript_s012.py`, `docs/HANDY-START.md` (+1 Satz). Secret-Scan (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, passw) über `+`-Zeilen von `origin/main...HEAD`: 0 Treffer. Keine Tabu-Pfade (.github/workflows, ZENTNA, JERRY AL, Beatmaster). |

## Zusätzliche Randfälle (eigene)
- Pfad mit Leerzeichen (Repo-Kopie per `git archive` in „Mein Ordner“, Links in „b in“): ok.
- Symlink auf Symlink (relativ `s2 -> s1`): ok.
- Symlink auf den Repo-Ordner (`repolink/start-schnapper.sh`): ok, aufgelöster echter Ordner.
- `sh` über Symlink: „Bitte mit bash starten“, kein Start (wie bisher).

## Testzahlen
- Modul 20 OK / 0 Skips; Gesamt 236 OK / 0 Skips; Cloudflare 10/10, 0 skipped.

## Mängel
- Keine blockierenden Mängel.
- Hinweis (kein Mangel): Durch die neue Reihenfolge kommt bei gleichzeitig fehlendem Python **und** fehlender Datei/ungültigem Port jetzt zuerst die Python-Meldung (vorher Datei/Port). Exit-Code bleibt 2; laut Plan so gewollt.
- Hinweis: `git diff --name-only origin/main...HEAD` zeigt zusätzlich `README.md`; das stammt aus früheren Commits des PR-Branches (schon in `origin/agent/master/20261022-23`), nicht aus diesem Commit.

## Endzustand
- Branch `agent/master/20261022-23` ausgecheckt, HEAD `7b9ae83`, `git status --short` leer. Kein Code geändert, nichts committet oder gepusht. Prüf-Scratch nur unter `scratchpad/check0729`.
