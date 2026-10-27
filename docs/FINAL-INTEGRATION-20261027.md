# SCHNAPPER – Abschlussbericht Final Master

Stand: 27. Oktober 2026
Arbeitsbranch: `replit/final-integration-20261027`
Ausgangspunkt: PR #133, Commit `ce71d919d08fdc403ba003e2411cb2d3f043d586`
Ziel: sicherer Integrations-Draft-PR; kein Merge und kein Deployment.

## Ergebnis

Die Befunde aus den WORK-Berichten von [PR #133](https://github.com/jefrey030/Schnapper/pull/133) sind im Folge-PR korrigiert und mit Regressionen abgesichert:

1. **Backup-Snapshot:** `/api/backup` liest und validiert `missionen.json` und `blitz.json` unter genau einer gemeinsamen Verzeichnissperre. Die Dateien werden über sichere Verzeichnis-Handles gelesen. Der Code ruft keine Store-Exportmethode auf, die eine zweite blockierende Sperre nehmen könnte. Die Snapshot-Decoder sind als Store-API verfügbar.
2. **Speicherstatus der Oberfläche:** MISSION-Läufe prüfen die Rückgabewerte für Ergebnisse, BLITZ-Queue und Laufprotokoll einzeln. Ein fehlgeschlagener Browser-Write kann keine Erfolgsmeldung „lokal gespeichert“ mehr auslösen; die Meldung nennt die betroffenen Bereiche. BLITZ meldet den Persistenzfehler ebenfalls direkt.
3. **Alarmspeicherung:** Ein Preisalarm wird erst nach bestätigtem Browser-Write als angelegt gemeldet; bei `false` bleibt die Fehlermeldung sichtbar und die Prüfung wird nicht gestartet.
4. **HTTP-409-Konflikte:** `apiPost` und `apiGet` erhalten HTTP-Status, `aktualisieren`-Flag und Pfad am Fehlerobjekt. Bei einem 409 der Missionsmutation wird die Missionsliste kontrolliert neu geladen; Formularwerte bleiben erhalten. Es gibt keinen automatischen Wiederholungsversuch; die Oberfläche fordert zur Prüfung und bewussten Wiederholung auf.

Die ursprünglichen Backup-/MISSION-Regressionen scheiterten gegen den unveränderten PR-#133-Stand wie beabsichtigt. Die zwei zusätzlichen UI-Regressionen scheitern ebenfalls gegen den vorherigen PR-#134-Stand und bestehen nach der Korrektur. Rohbelege: `docs/evidence/regressions-before-fix.log` und `docs/evidence/final-ui-p1-regressions-before-fix.log`.

## Abgleich der PRs #129–#133

Der Arbeitsstand baut auf #133 auf; frühere Änderungen wurden weder neu gestartet noch überschrieben. Die Speicherung verwendet die aktuelle, gemeinsame `sicherer_speicher.py`-Lösung. Die älteren Varianten aus #130/#132 wurden nicht parallel weitergeführt. Die stalen Revisionen lösen weiterhin einen expliziten Konflikt aus; Änderungen werden nicht still zusammengeführt. Nach dem Konflikt muss neu geladen und bewusst erneut versucht werden.

Die zuvor aus dem finalen #133-Teststand fehlenden bzw. nicht mehr passenden Regressionen sind im aktuellen Testbestand wie folgt abgedeckt:

| Frühere Regression | Aktueller Gegenpart | Vertragsunterschied |
|---|---|---|
| #130 `test_two_preloaded_instances_do_not_overwrite_each_other` | `test_zwei_instanz_aenderungen_erkennen_konflikt_und_rebase_nicht_still` | Bewusster Konflikt statt stiller automatischer Zusammenführung |
| #130 `test_eight_parallel_independent_instances_preserve_all_changes` | `test_acht_vorgeladene_instanz_aenderungen_bleiben_nach_explizitem_retry_erhalten` | Ein erster Schreibvorgang, übrige Konflikte; nach Reload und explizitem Retry bleiben alle Änderungen erhalten |
| #130 `test_symlink_store_and_lock_are_rejected_without_touching_target` | `test_verlinkte_oder_fremdlesbare_speicherdatei_blockiert`, `test_speicherlock_symlink_und_beschaedigte_datei_bleiben_unveraendert` | Store-Leaf und gemeinsame Sperrdatei bleiben fail-closed |
| #130 `test_corruption_after_load_blocks_mutation_and_preserves_bytes` | `test_speicherlock_symlink_und_beschaedigte_datei_bleiben_unveraendert` | Beschädigte Datei wird nicht überschrieben |
| #130 `test_directory_symlink_rejected_without_outside_write` | `test_uebergeordneter_symlink_und_leaf_symlink_blockiert`, `test_verzeichnisaustausch_waehrend_schreiben_beruehrt_aussen_nicht` | Keine Schreibumleitung in ein fremdes Verzeichnis |
| #130 `test_stored_file_is_private_and_roundtrips` | `test_private_mission_datei_ueberlebt_neustart` | Dateimodus und Reload bleiben abgesichert |
| #130 `test_failed_write_does_not_change_persisted_data` | `test_speicherfehler_laesst_alte_missionen_unveraendert` | Bestehender Schreibfehler-Schutz bleibt erhalten |
| #132 `test_preloaded_instances_cannot_emit_duplicate` / `test_parallel_independent_instances_emit_exactly_once` | `test_gleichzeitige_deduplizierung_meldet_einmal_und_keinen_stillverlust`, `test_sechs_vorgeladene_instanz_duplizieren_treffer_nicht` | Konflikte werden erkennbar; kein stiller Verlust oder doppelter Treffer |
| #132 `test_symlink_parent_never_creates_external_files` | `test_blitz_symlink_im_uebergeordneten_ordner_blockiert` | Kein Schreiben außerhalb des Datenspeichers |
| #132 `test_symlink_leaf_and_lock_fail_closed` | `test_blitz_leaf_und_speicherlock_symlink_werden_abgewiesen` | BLITZ nutzt dieselbe gemeinsame Sperrdatei |
| #132 `test_corruption_after_loading_is_not_overwritten` | `test_blitz_beschaedigung_nach_laden_bleibt_unveraendert` | Beschädigte BLITZ-Historie bleibt unverändert |
| #132 `test_private_atomic_file_survives_reload` | `test_blitz_private_datei_ueberlebt_neustart` | Dateimodus und Reload bleiben abgesichert |
| #133 `alarmAnlegen` darf fehlgeschlagenen Write nicht als Erfolg melden | `failed alarm persistence is never reported as created` | `false` bleibt Fehler; kein Erfolg und keine Alarmprüfung |
| #133 HTTP 409 darf `status`/`aktualisieren` nicht verlieren | `409 refreshes mission list, preserves form data, and never retries mutation` | Status/Flag erhalten; Missionsliste einmal neu laden; Eingaben bleiben; keine Mutation wird wiederholt |

Die 13 ursprünglichen #130/#132-Regressionen laufen gegen die neue Speicher-API nicht unverändert durch: 6 bestanden, 6 Fehler und 1 Fehlschlag. Die Fehler resultieren aus dem geänderten Konfliktvertrag (explizites `MissionsKonflikt`/`BlitzKonflikt`), dem entfernten privaten `_speichern`-Hook und dem ersetzten per-Datei-Locknamen. Der Fehlschlag prüft den alten Lock-Dateinamen, nicht den gemeinsamen Lock. Das ist kein Nachweis für stillen Datenverlust oder einen Bypass; die jeweilige Ersetzung muss Work anhand der neuen Tests abnehmen.

Die Stilllegung aus #131 ist im Arbeitszweig enthalten; die Datei stimmt bytegenau mit dem #131-Zweig überein. **`main` bleibt davon unberührt und führt den dortigen Legacy-Stundenworkflow weiter aus, solange #131 beziehungsweise diese Integration nicht gemergt ist.** Das wurde wegen der ausdrücklichen Vorgabe „kein Merge“ nicht geändert.

PR-Verlauf: [#129](https://github.com/jefrey030/Schnapper/pull/129) · [#130](https://github.com/jefrey030/Schnapper/pull/130) · [#131](https://github.com/jefrey030/Schnapper/pull/131) · [#132](https://github.com/jefrey030/Schnapper/pull/132) · [#133](https://github.com/jefrey030/Schnapper/pull/133) · [Final-Draft-PR #134](https://github.com/jefrey030/Schnapper/pull/134).

## Tests und Nachweise

Alle Prüfungen liefen lokal/offline mit temporären Verzeichnissen und synthetischen Angebotsdaten. Keine Produktionsdaten, externe Preisquellen, KI-Provider, Cloudflare-Bereitstellung oder kostenpflichtigen Dienste wurden verwendet. Seit den lokalen Python-/Cloudflare-Vollsuiten wurden nur Web-UI-JavaScript, Node-Regressionen und Dokumentation ergänzt; der neue PR-Head muss die automatische CI erneut bestehen.

| Prüfung | Ergebnis | Rohprotokoll |
|---|---:|---|
| Vollständige Python-Tests, `GITHUB_ACTIONS=true` einschließlich S-006-Refs | **534 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-python-tests.log` |
| Vollständige Cloudflare-Worker-Offlinetests | **16 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-cloudflare-tests.log` |
| UI-Speicherfehler-Regressionen (Ergebnisse, BLITZ, Laufprotokoll, Alarm, HTTP 409) | **6 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-ui-regression-tests.log` |
| Headless-Browser-Oberfläche bei 360 × 800 | **bestanden**: LUPE, WARENKORB, PREISDETEKTIV, BLITZ, MISSION; Upload, Vergleich, Mission-Lauf, Queue, Backup/Download und Wiederherstellung | `docs/evidence/final-headless-ui.log` |
| Zwei sichtbare Browser-Tabs | **bestanden**: Web-Lock wird gemeinsam genutzt; der zweite Tab sendet während des ersten Laufs keinen doppelten Lauf | `docs/evidence/final-headless-ui.log` |
| Neustart im isolierten Testdatenverzeichnis nach Restore | **bestanden**: 2 Missionen und 2 BLITZ-Historieneinträge nach Neustart wieder lesbar | `docs/evidence/final-restart-check.log` |
| JavaScript-Syntax, Python-Compileall, Whitespace/Diff | **bestanden** | `docs/evidence/final-static-checks.log` |
| Vorher/Nachher-Regressionsnachweis | **Backup-/MISSION-Fehler vor dem Fix reproduziert; die zwei neuen UI-Fehler scheitern auf dem vorherigen PR-#134-Head (4 pass/2 fail) und bestehen nach dem Fix (6 pass/0 fail).** | `docs/evidence/regressions-before-fix.log`, `docs/evidence/final-ui-p1-regressions-before-fix.log` |

Kommandos:

```sh
PYTHONPATH=app:team GITHUB_ACTIONS=true python3 -X dev -W error -m unittest discover -s tests -v
cd cloudflare && node --test test/*.test.mjs
node --test tests/test_storage_failure_ui.mjs
node --check app/schnapper/web/app.js
python3 -m compileall -q app team tests
git diff --check
node tests/browser_ui_e2e.mjs
```

Der Browserlauf benötigt ausschließlich einen lokal gestarteten SCHNAPPER-Testserver mit eigenem temporärem Datenverzeichnis und Chromium mit lokalem DevTools-Port. Die Testdatei erzeugt synthetische Daten selbst. Der Wiederherstellungs- und Neustartnachweis verwendet nur dieses temporäre Verzeichnis.

## KI- und Android-Bereitschaft

- **Lokale KI: BLOCKED.** In der Testumgebung wurden keine unterstützte lokale Laufzeit und keine Modellgewichte im Repository gefunden. `OLLAMA_HOST` und `OLLAMA_MODELS` waren nicht gesetzt. Es gab **keinen** Modell-Download, keine Inferenz und keine Aktivierung.
- Die Cloudflare-Tests verwenden Mock-Aufrufe; sie belegen keine echte Modellinferenz.
- **Android: BLOCKED.** `adb` und `emulator` sind nicht verfügbar; es gab keinen Gerätetest.
- Nachweise: `docs/evidence/local-runtime-readiness.log`.

## CI und Freigabegrenzen

`.github/workflows/tests.yml` hat ausschließlich lesende Repository-Berechtigungen und startet Python-, Cloudflare-Offlinetests sowie die UI-Speicherregression. Die Jobs sind auf öffentliche Repositories und Standardrunner begrenzt; es gibt darin kein Deployment. Frühere Heads von PR #134 hatten erfolgreiche Testläufe; für den nachfolgenden Fix-Head ist ausschließlich der neueste Check-Status in PR #134 maßgeblich. Diese Datei behauptet keinen CI-Erfolg für einen noch nicht geprüften Head.

## Offene Blocker und Risiken

1. Der Legacy-Stundenworkflow auf `main` ist weiterhin aktiv, bis ein Betreiber die Sicherheitsänderung nach Review ausdrücklich freigibt und später separat merged. Diese Integration hat ihn nicht auf `main` geändert.
2. Es gibt keinen Nachweis echter KI-Inferenz oder eines vorhandenen lokalen Modells.
3. Android-Gerät/Emulator fehlt.
4. Die Browserprüfung und Wiederherstellung liefen ausschließlich mit synthetischen Daten; Live-Preisquellen, Produktionshosting, echte Cloudflare-Datenbanken/Storage und externe Integrationen wurden nicht getestet.
5. `main` ist laut GitHub branch-protection API nicht geschützt; Repository-Rulesets wurden nicht gefunden. Es gibt damit keine technisch erzwungenen Required Reviews/Checks auf `main`. Nicht geändert.
6. Für die Produktionsfreigabe bleiben ein formales unabhängiges Review, die bewusste Betreiberentscheidung zum Legacy-Workflow sowie separate Freigaben für KI, Geräte und externe Integrationen erforderlich. Reviewer-Anforderung und formale Review-Einträge müssen auf PR #134 separat geprüft werden.

## Entscheidung

**GO für Review als Draft-PR. NO-GO für Merge, Produktionsdatenzugriff und Deployment.** Die Offline-Prüfungen sind bestanden; die oben genannten Live-/Betreiberblocker bleiben bestehen. Es wurde weder gemergt noch deployt.

Der exakte finale Head-SHA steht in den Metadaten und im Beschreibungstext des Draft-PRs.
