# SCHNAPPER – Abschlussbericht Final Master

Stand: 27. Oktober 2026
Arbeitsbranch: `replit/final-integration-20261027`
Ausgangspunkt: PR #133, Commit `ce71d919d08fdc403ba003e2411cb2d3f043d586`
Ziel: sicherer Integrations-Draft-PR; kein Merge und kein Deployment.

## Ergebnis

Die beiden in den WORK-Befunden von [PR #133](https://github.com/jefrey030/Schnapper/pull/133) beschriebenen Fehler sind korrigiert und mit Regressionen abgesichert:

1. **Backup-Snapshot:** `/api/backup` liest und validiert `missionen.json` und `blitz.json` unter genau einer gemeinsamen Verzeichnissperre. Die Dateien werden über sichere Verzeichnis-Handles gelesen. Der Code ruft keine Store-Exportmethode auf, die eine zweite blockierende Sperre nehmen könnte. Die Snapshot-Decoder sind als Store-API verfügbar.
2. **Speicherstatus der Oberfläche:** MISSION-Läufe prüfen die Rückgabewerte für Ergebnisse, BLITZ-Queue und Laufprotokoll einzeln. Ein fehlgeschlagener Browser-Write kann keine Erfolgsmeldung „lokal gespeichert“ mehr auslösen; die Meldung nennt die betroffenen Bereiche. BLITZ meldet den Persistenzfehler ebenfalls direkt.

Beide neuen Regressionen wurden gegen den unveränderten PR-#133-Stand ausgeführt und scheiterten dort wie beabsichtigt. Nach der Korrektur bestehen sie. Das Rohprotokoll steht in `docs/evidence/regressions-before-fix.log`.

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

Die Stilllegung aus #131 ist im Arbeitszweig enthalten; die Datei stimmt bytegenau mit dem #131-Zweig überein. **`main` bleibt davon unberührt und führt den dortigen Legacy-Stundenworkflow weiter aus, solange #131 beziehungsweise diese Integration nicht gemergt ist.** Das wurde wegen der ausdrücklichen Vorgabe „kein Merge“ nicht geändert.

PR-Verlauf: [#129](https://github.com/jefrey030/Schnapper/pull/129) · [#130](https://github.com/jefrey030/Schnapper/pull/130) · [#131](https://github.com/jefrey030/Schnapper/pull/131) · [#132](https://github.com/jefrey030/Schnapper/pull/132) · [#133](https://github.com/jefrey030/Schnapper/pull/133) · [Final-Draft-PR #134](https://github.com/jefrey030/Schnapper/pull/134).

## Tests und Nachweise

Alle Prüfungen liefen lokal/offline mit temporären Verzeichnissen und synthetischen Angebotsdaten. Keine Produktionsdaten, externe Preisquellen, KI-Provider, Cloudflare-Bereitstellung oder kostenpflichtigen Dienste wurden verwendet.

| Prüfung | Ergebnis | Rohprotokoll |
|---|---:|---|
| Vollständige Python-Tests, `GITHUB_ACTIONS=true` einschließlich S-006-Refs | **534 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-python-tests.log` |
| Vollständige Cloudflare-Worker-Offlinetests | **16 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-cloudflare-tests.log` |
| UI-Speicherfehler-Regressionen | **4 bestanden, 0 fehlgeschlagen, 0 übersprungen** | `docs/evidence/final-ui-regression-tests.log` |
| Headless-Browser-Oberfläche bei 360 × 800 | **bestanden**: LUPE, WARENKORB, PREISDETEKTIV, BLITZ, MISSION; Upload, Vergleich, Mission-Lauf, Queue, Backup/Download und Wiederherstellung | `docs/evidence/final-headless-ui.log` |
| Zwei sichtbare Browser-Tabs | **bestanden**: Web-Lock wird gemeinsam genutzt; der zweite Tab sendet während des ersten Laufs keinen doppelten Lauf | `docs/evidence/final-headless-ui.log` |
| Neustart im isolierten Testdatenverzeichnis nach Restore | **bestanden**: 2 Missionen und 2 BLITZ-Historieneinträge nach Neustart wieder lesbar | `docs/evidence/final-restart-check.log` |
| JavaScript-Syntax, Python-Compileall, Whitespace/Diff | **bestanden** | `docs/evidence/final-static-checks.log` |
| Vorher/Nachher-Regressionsnachweis gegen PR-#133-Basis | **vorher: Backup-Test fehlgeschlagen; UI: 3 Fehlversuche/1 Erfolg. Nachher: alle Regressionen bestanden.** | `docs/evidence/regressions-before-fix.log` |

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

`.github/workflows/tests.yml` hat ausschließlich lesende Repository-Berechtigungen und startet Python-, Cloudflare-Offlinetests sowie die UI-Speicherregression. Die Jobs sind auf öffentliche Repositories und Standardrunner begrenzt; es gibt darin kein Deployment. Beim Erstellen von Draft-PR #134 war der Pull-Request-Lauf für den ersten Head-SHA noch in Arbeit; das ist kein bestandenes Ergebnis. Für den aktuellen Head ist stets der neueste Check-Status im PR maßgeblich.

## Offene Blocker und Risiken

1. Der Legacy-Stundenworkflow auf `main` ist weiterhin aktiv, bis ein Betreiber die Sicherheitsänderung nach Review ausdrücklich freigibt und später separat merged. Diese Integration hat ihn nicht auf `main` geändert.
2. Es gibt keinen Nachweis echter KI-Inferenz oder eines vorhandenen lokalen Modells.
3. Android-Gerät/Emulator fehlt.
4. Die Browserprüfung und Wiederherstellung liefen ausschließlich mit synthetischen Daten; Live-Preisquellen, Produktionshosting, echte Cloudflare-Datenbanken/Storage und externe Integrationen wurden nicht getestet.
5. Der GitHub-CI-Status des finalen Draft-PR-Commits ist nach PR-Erstellung zu prüfen. Die lokalen vollständigen Tests sind grün; ein späterer CI-Fehler bleibt bis zum GitHub-Lauf offen.
6. Für die Produktionsfreigabe bleiben ein unabhängiges Review, die bewusste Betreiberentscheidung zum Legacy-Workflow sowie separate Freigaben für KI, Geräte und externe Integrationen erforderlich.

## Entscheidung

**GO für Review als Draft-PR. NO-GO für Merge, Produktionsdatenzugriff und Deployment.** Die Offline-Prüfungen sind bestanden; die oben genannten Live-/Betreiberblocker bleiben bestehen. Es wurde weder gemergt noch deployt.

Der exakte finale Head-SHA steht in den Metadaten und im Beschreibungstext des Draft-PRs.
