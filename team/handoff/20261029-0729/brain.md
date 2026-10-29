# BRAIN – Lauf 20261029-0729

- Start (UTC): Thu Oct 29 07:33:44 UTC 2026
- Ende (UTC): Thu Oct 29 07:34:55 UTC 2026
- Branch: agent/master/20261022-23 (ausgecheckt, nicht gepusht), 1 Commit über b03b986
- Commit-SHA: 7b9ae8358fa9795814175b273612ecbbdb230362
- Nachricht: "SCHNAPPER MASTER: F5 Startskript startet auch über Symlink (S-012)"

## Geänderte Dateien (+/-)
- start-schnapper.sh: +30 / -32 (Modus 100755 bleibt)
- tests/test_start_skript_s012.py: +32 / -2
- docs/HANDY-START.md: +1 / -0

## Umsetzung
- Reihenfolge neu: bash-Wächter, set -eu, fehler(), AUFRUF_DIR, Prüfung "Zu viele Argumente", Python suchen und prüfen (py-ok:42), Skriptordner per
  `"$PY" -I -c 'import pathlib, sys; print(pathlib.Path(sys.argv[1]).resolve().parent)' "${BASH_SOURCE[0]}"`, Datei, Port, cd/PYTHONPATH/exec unverändert.
- Kopfkommentar: "Aufruf über Symlink (z. B. ~/bin/schnapper) nutzt den echten SCHNAPPER-Ordner." Hinweis "auf echtem Gerät ungetestet" bleibt.
- Test: starte(..., skript=SKRIPT); neuer test_start_ueber_symlink mit Subtests absolut/relativ/kette, skipUnless(hasattr(os, "symlink")).
- Doku: ein Satz unter Schritt 4 (Symlink-Beispiel).

## Testergebnisse
- bash -n start-schnapper.sh: OK
- python3 -m unittest tests.test_start_skript_s012 -v: Ran 20 tests, OK (0 Skips; 19 alte + 1 neuer)
- python3 -m unittest discover -s tests: Ran 236 tests, OK (0 Skips)
- cd cloudflare && node --test test/*.test.mjs: 10 Tests, 10 pass, 0 fail, 0 skipped
- Secret-Scan im Diff (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY): 0 Treffer

## Gegenprobe (Pflicht)
- Alte Datei aus b03b986 eingesetzt: test_start_ueber_symlink FAILED (failures=3), alle drei Subtests rot mit
  "Skript beendet (Exit 2): Datei nicht gefunden: /tmp/tmp…/bin/app/vorlagen/meine-angebote.csv".
- Neue Datei wiederhergestellt, chmod 755; sha256 vorher = nachher = 0c5c0256b47e6cffb6f08fd9bec20899a874249c7d23368ddfdd5a823368cd15.

## Sperren
- Kein Push, kein Merge, kein Force-Push, keine Workflows/Secrets, keine Live-Abrufe, nichts von ZENTNA/JERRY AL/Beatmaster.
