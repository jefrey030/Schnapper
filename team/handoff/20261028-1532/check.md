# CHECK – Lauf 20261028-1532

- Start (UTC): 2026-10-28T15:39:13Z
- Ende (UTC): 2026-10-28T15:40:33Z
- Geprüfter Commit: 779e8b7d492aa423e13bdf75d28bbdd2cd98ba71 (Elter a584774 = origin/agent/master/20261022-23)
- Eigener Worktree: /home/claude/check-wt-1532 (detached auf 779e8b7), danach mit `git worktree remove` entfernt.

## Urteil: bestanden

## Belege pro Kriterium

1. **Nur erlaubte Dateien** – `git diff --stat origin/agent/master/20261022-23..779e8b7`:
   `docs/HANDY-START.md | 2 ++`, `start-schnapper.sh | 7 +++++++`, `tests/test_start_skript_s012.py | 19 +++`; 3 files, 28 insertions(+). `git diff --stat origin/main...779e8b7` zeigt zusätzlich nur README.md aus dem bestehenden PR-#44-Stand (a584774), nichts Neues. OK
2. **Shebang / set -eu / Modus** – `head -1`: `#!/usr/bin/env bash`; `grep -n '^set -eu$'` → Z. 28; `git ls-tree 779e8b7 start-schnapper.sh` → `100755`. OK
3. **Wächter-Position / POSIX** – Wächter Z. 24–27 (`if [ -z "${BASH_VERSION:-}" ]`), `set -eu` Z. 28, `BASH_SOURCE` Z. 38, `10#` Z. 69. `bash -n` → 0, `dash -n` → 0, zusätzlich `bash --posix -n` → OK. OK
4. **dash/sh-Start** – `dash start-schnapper.sh` → exit=2, stdout leer, stderr `Bitte mit bash starten: bash start-schnapper.sh`, kein „Bad substitution“. `sh start-schnapper.sh` (/bin/sh → /usr/bin/dash) ebenso exit=2. Kein Server (im Test per `lauscht(port)` geprüft). OK
5. **bash-Verhalten unverändert** – `python3 -m unittest -v tests.test_start_skript_s012`: Ran 17 tests, OK (u. a. test_start_ohne_argument_aus_fremdem_cwd, test_start_mit_datei_argument, test_fehlende_datei, test_ungueltiger_port, test_fehlendes_python, test_host_fest_127). Manuell: `bash start-schnapper.sh /nichtda.csv` → „Datei nicht gefunden“, exit 2; `SCHNAPPER_PORT=abc bash …` → „Ungültiger Port…“, exit 2. OK
6. **Neuer Test** – `test_start_mit_sh_meldet_bash ... ok` (kein Skip, dash vorhanden). Imports os/shutil vorhanden. OK
7. **Gegenprobe** – Skript aus a584774 im Check-Worktree eingesetzt, nur neuer Test: `AssertionError: 'Bitte mit bash starten' not found in '…/start-schnapper.sh: 31: Bad substitution\n'` → `FAILED (failures=1)`. Danach `git checkout -- start-schnapper.sh`, `cmp` identisch, Modus 100755, Status sauber. OK (von CHECK selbst nachvollzogen)
8. **Doku** – `grep -cF` in docs/HANDY-START.md: „auf echtem Gerät ungetestet“ 1, `bash start-schnapper.sh` 5, `SCHNAPPER_PORT=8800 bash start-schnapper.sh` 1, `bash start-schnapper.sh app/beispiele/angebote.csv` 1, `PYTHONPATH=app python -m schnapper.web` 1, `pkg install python unzip` 1, neu „Bitte mit bash starten“ 1. OK
9. **Statische Regeln** – grep auf curl/wget/pip/git/apt/npm/pkg außerhalb Kommentar/printf/fehler: leer; dirname/readlink/realpath/basename/0.0.0.0: leer. Tests test_keine_downloads_oder_installation, test_keine_externen_hilfsprogramme, test_host_fest_127 grün. OK
10. **Volle Suite** – `python3 -m unittest discover -s tests`: Ran 233 tests, OK (Ausgangsstand a584774: Ran 232, OK → +1). `cd cloudflare && node --test test/*.test.mjs`: tests 10, pass 10, fail 0. OK
11. **Secret-Scan / Tabu** – `git diff origin/main...779e8b7 | grep -niE 'sk-ant-|ghp_|github_pat_|AKIA|PRIVATE KEY|passw(or)?d\s*[:=]|secret\s*[:=]|token\s*[:=]'` → „kein Secret“. Keine Pfade unter .github/, team/, app/, cloudflare/; keine ZENTNA/JERRY AL/Beatmaster-Bezüge im Diff. OK
12. **Commit** – 1 Commit (`rev-list --count origin/…..779e8b7` = 1), `rev-list --count 779e8b7..origin/agent/master/20261022-23` = 0 (Fast-Forward). Nachricht `SCHNAPPER MASTER: F5 Startskript meldet Start mit sh verständlich (S-012)` mit Trailern `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>` und `Claude-Session: https://claude.ai/code/session_01Km4opyYpAxB6CyzTqKe1hH`. OK

## Anmerkungen (nicht blockierend)
- Wächter beruht auf `BASH_VERSION`. Wer diese Variable bewusst exportiert und dann `sh` nutzt, umgeht ihn und erhält wieder „Bad substitution“. Praktisch irrelevant, bash exportiert BASH_VERSION nicht.
- zsh/ksh/busybox sind hier nicht installiert, nur dash wurde real geprüft (zsh setzt kein BASH_VERSION, Wächter greift dort laut Logik ebenfalls).
- Behauptungen in brain.md (233/232 Tests, 10/10, Gegenprobe rot, 100755) stimmen mit eigenen Messungen überein.
