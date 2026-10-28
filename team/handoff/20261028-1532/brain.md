# BRAIN – Lauf 20261028-1532

- Start (UTC): Wed Oct 28 15:37:34 UTC 2026
- Ende (UTC): Wed Oct 28 15:38:51 UTC 2026
- Worktree: /home/claude/brain-wt-1532, Branch agent/master/20261022-23 (Basis origin a584774)
- Commit (nur lokal, nicht gepusht): 779e8b7d492aa423e13bdf75d28bbdd2cd98ba71
  "SCHNAPPER MASTER: F5 Startskript meldet Start mit sh verständlich (S-012)" mit Trailern Co-Authored-By und Claude-Session
- `git rev-list --count HEAD..origin/agent/master/20261022-23` = 0 (Fast-Forward-fähig, 1 Commit)

## Geänderte Dateien (3 files changed, 28 insertions(+), 0 deletions)
- start-schnapper.sh (+7): Zeile im Kopfkommentar unter „Verhalten:“, POSIX-Wächter `[ -z "${BASH_VERSION:-}" ]` vor `set -eu`, BASH_SOURCE und 10#. Zeile 1 weiterhin `#!/usr/bin/env bash`, `set -eu` eigene Zeile, Modus 100755.
- docs/HANDY-START.md (+2): Spiegelstrich in Schritt 4 zu `sh start-schnapper.sh` vs. `bash start-schnapper.sh`. Bestehende Sätze unverändert.
- tests/test_start_skript_s012.py (+19): `test_start_mit_sh_meldet_bash` (dash, ersatzweise /bin/sh wenn nicht bash, sonst skipTest).

## Testergebnisse
- `python3 -m unittest -v tests.test_start_skript_s012`: 17 Tests, OK (neuer Test lief ohne Skip mit /usr/bin/dash)
- `python3 -m unittest discover -s tests`: 233 Tests, OK (Ausgangsstand vor Änderung: 232, OK)
- `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0
- `dash start-schnapper.sh`: stderr „Bitte mit bash starten: bash start-schnapper.sh“, exit=2, stdout leer. `sh start-schnapper.sh` (sh -> dash) ebenso exit=2.
- `bash -n start-schnapper.sh && dash -n start-schnapper.sh`: beide OK (Exit 0)
- Secret-Scan des Diffs: „kein Secret“

## Gegenprobe
Skript aus a584774 temporär eingesetzt (`git show a584774:start-schnapper.sh`), nur den neuen Test ausgeführt:
FAILED (failures=1) – AssertionError: 'Bitte mit bash starten' not found in '.../start-schnapper.sh: 31: Bad substitution\n'.
Danach Fix wiederhergestellt (Modus 755), Modul wieder 17/17 OK.

## Hinweise
- Kein Push, kein Merge, keine Änderungen an .github/, team/, app/, cloudflare/.
