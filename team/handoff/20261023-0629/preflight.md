# Preflight Lauf 20261023-0629 (Orchestrator, ohne Änderungen)

- Zeit: 2026-10-23T06:29:55Z
- Klon: /home/claude/schnapper, origin/main = 6dbe114 („security(SCHNAPPER): token only via HTTPS, block redirects (#43)“) – unverändert seit Lauf 20261023-0529.
- Tests main: `python3 -m unittest discover -s tests` → 216 Tests OK; `cd cloudflare && node --test test/*.test.mjs` → 10/10 pass.
- Secret-Scan (sk-ant-, ghp_, github_pat_, AKIA, PRIVATE KEY, Passwörter): keine Treffer außer Erkennungs-Regex in team/agent.py und Erwähnung im Bericht 20261022-0728 (kein Secret).
- Letzter Bericht: team/runs/20261023-0529-master.md (Branch agent/master/reports), Kopie in letzter-bericht.md. Nächster kleinster Schritt dort: Chromium-Suche `_finde_chromium()` aus #41 in `tests/test_app_sicherung_s010.py` auf PR #40 übernehmen.
- F1–F6 haben je einen offenen Team-Draft-PR: #36 (F1), #39 (F2), #40 (F3), #41 (F4), #44 (F5), #45 (F6). Neu: #50 (agent/master/s014-viererteam-20261023, Inhalt nicht geprüft).

## Offene PRs (REST, 06:29 UTC)
| PR | Branch | Kopf | Draft | Titel |
|---|---|---|---|---|
| #50 | agent/master/s014-viererteam-20261023 | 74e88d9 | draft=true | SCHNAPPER: 4 KI-Master + offene S-014-Aufgabe für sicheren Diagnose-Lauf |
| #45 | agent/master/20261023-01 | ecad218 | draft=true | SCHNAPPER MASTER: F6 eBay vorbereiten – Browse-API-Adapter, gesperrt ohne Schlüssel (S-013) |
| #44 | agent/master/20261022-23 | a584774 | draft=true | SCHNAPPER MASTER: F5 Ein-Befehl-Start für Android/Termux (S-012) |
| #41 | agent/master/20261022-2238 | a3fcfab | draft=true | SCHNAPPER MASTER: F4 Barcode per Kamera scannen (S-011) |
| #40 | agent/master/20261022-22 | 1adad0c | draft=true | SCHNAPPER MASTER: F3 Merkliste und Preisalarme sichern und wiederherstellen (S-010) |
| #39 | agent/master/20261022-21 | 1833417 | draft=true | SCHNAPPER MASTER: F2 Angebot direkt in der App erfassen (S-009) |
| #36 | agent/master/20261022-20 | 8d4e90b | draft=true | SCHNAPPER MASTER: F1 Aufräumen – tasks.json (S-004–S-006 done, S-009–S-013 open) und PR-Tabelle |
| #35 | fix/guard-private-runner-20261022-current | a264da0 | draft=true | security: privaten SCHNAPPER-Stundenlauf fail-closed sperren (aktuelle main-Basis) |
| #33 | fix/schnapper-open-qa-task-20261022 | 880f6d2 | draft=true | fix(team): offene QA-Aufgabe + fehlerresistente Stundenrotation |
| #30 | fix/schnapper-alarm-nonfinite-20261022 | 0838157 | draft=true | fix(SCHNAPPER): Preisalarm-Import gegen ungültige Eingaben absichern |
| #28 | fix/alarm-input-validation-20261022 | 4cf94d5 | draft=true | fix: SCHNAPPER-Preisalarm bei defekten Wunschlisten robust machen |
| #27 | fix/preisformate-gemischt-20261022 | ac5b7a0 | draft=true | fix(preise): DE/EN-Tausenderformate korrekt und sicher einlesen |
| #26 | fix/preisformate-englisch-20261022 | b81308c | draft=false | fix(SCHNAPPER): Preise im deutschen UND englischen Zahlenformat korrekt erkennen |
| #25 | fix/english-thousands-prices-20261022 | 0af7bd6 | draft=true | fix(SCHNAPPER): englische Tausenderpreise korrekt lesen statt falscher Schnäppchen |
| #23 | fix/schnapper-url-validierung-20261022 | 02700ab | draft=true | fix: Robuster Angebotsimport bei kaputten URLs und korrekte Port-Dubletten |
| #21 | security/schnapper-failclosed-20261022 | 1594fb8 | draft=true | Security: Fail-Closed-Abnahme, Not-Aus und getrennte Release-Gates |
