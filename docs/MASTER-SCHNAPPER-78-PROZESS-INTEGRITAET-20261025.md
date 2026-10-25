# SCHNAPPER MASTER 78 – Prozessidentitaet & symlink-sichere Nachweise

**Datum:** 25.10.2026  
**Projekt:** jefrey030/Schnapper  
**Ausgangsbasis:** MASTER 77, Draft PR #94, HEAD `855132e0b0ec3bb921798e6497cdac3462cb6143`  
**Arbeitszweig:** `fix/master78-process-role-evidence-20261025`  
**Modus:** P0 Sicherheitskorrektur, P1 Regression, nur Offline-MOCKs  
**Kostenlimit:** 0 EUR; kein externer KI-Provider, keine kostenpflichtigen Actions, keine Cloud-KI  
**Freigabe:** NO-GO fuer Merge, Deployment, autonomes Team und Produktivdaten bis unabhaengiger Review

## Festgestellte Schwachstellen

1. `pruefe_nachweise()` nahm fuenf erfolgreiche Prozessschritte an, ohne deren Rollen-IDs zu pruefen. Ein synthetisches Protokoll mit doppelt vorkommendem LEAD und fehlendem BERICHT koennte die reine Exitcode-Pruefung umgehen.
2. Python behandelt `False == 0` als wahr. Der bisherige Exitcode-Vergleich ohne strengen Typ erlaubte einen Bool-Wert in einem manipulierten Prozessprotokoll.
3. Beim Erstellen des SHA256-Manifests wurden Rollen-JSON-Dateien mit `.exists()` ausgewaehlt und mit `.read_bytes()` gehasht. Ein Symlink konnte trotz negativer Pruefung erneut gelesen werden. Fehler beim Manifestlesen konnten zu einem ungefangenen Dateifehler fuehren.

## MASTER 78 – Arbeits- und Abnahmeplan (28 Punkte)

| Nr. | Auftrag | Erforderlicher Nachweis |
| ---: | --- | --- |
| 01 | GitHub-Repo bestaetigen | `jefrey030/Schnapper` |
| 02 | MASTER-77-HEAD pruefen | PR #94 HEAD ermittelt |
| 03 | Bestehende P0-PRs respektieren | #55/#69/#80/#89/#94 nicht veraendern |
| 04 | Neuen isolierten Branch erzeugen | Nur auf #94 aufsetzen |
| 05 | Rollenbelege pruefen | LEAD, BRAIN, CHECK, COMMAND, BERICHT |
| 06 | Exakte Reihenfolge erzwingen | Keine vertauschten Rollen |
| 07 | Doppelte Rollen blockieren | Keine Ersatzrolle bei fuenf Exitcodes |
| 08 | Fehlende Rollen blockieren | Keine unvollstaendige Folge |
| 09 | Fremde Rollen blockieren | Keine nicht definierten Rollen |
| 10 | Bool-Exitcode blockieren | `type(code) is int` |
| 11 | Fehlerhafte Exitcodes blockieren | Ausschliesslich echte Integer 0 |
| 12 | Falsche Prozessstrukturen blockieren | Fehler statt ungefangenem Traceback |
| 13 | Manifestsicherheit pruefen | Symlinks nicht dereferenzieren |
| 14 | Rollen-Symlink abweisen | Weder lesen noch als Erfolg melden |
| 15 | Zaehler-Symlink abweisen | Fail-closed |
| 16 | Fehlende Manifestdatei behandeln | `BLOCKIERT` und Rueckgabecode 1 |
| 17 | Unlesbare Manifestdatei behandeln | Kontrollierter Fehler |
| 18 | Rollenbeleg mit Gesamtbericht vergleichen | MASTER-77-Gates erhalten |
| 19 | CHECK-Urteil kontrollieren | Bei Ablehnung kein Erfolg |
| 20 | Geheimnisscan kontrollieren | Keine Funde als PASS werten |
| 21 | Testzaehler pruefen | Positive ganzzahlige Testanzahl |
| 22 | COMMAND-NEIN respektieren | Keine automatische Freigabe |
| 23 | Crash-Sperre respektieren | MASTER-76-`flock` erhalten |
| 24 | Not-Aus respektieren | STOP-Verhalten unveraendert |
| 25 | 12 neue Offline-Regressionen | Tests in `tests/test_master78_process_evidence.py` |
| 26 | Alle vorhandenen Tests wiederholen | Python/Cloudflare-Offline-CI |
| 27 | Finalen Commit verifizieren | Exakter SHA, Jobs und Logs lesen |
| 28 | Unabhaengige Freigabe einholen | Ohne Review bleibt NO-GO |

## Tatsaechlich geaenderte Dateien

- `team/local_service.py`: striktes Prozessrollen- und Exitcode-Gate; fehlerfestes Manifestlesen ohne Symlink-Dereferenzierung.
- `tests/test_master78_process_evidence.py`: zwoelf reine Offline-Regressionen einschliesslich doppelter/vertauschter Rollen und sabotierter Manifestartefakte.
- Dieses MASTER-78-Dokument: Anforderungen, Sicherheitsgrenzen und Nachweisbedingungen.

**Wichtige Grenze:** Auch ein sauberer MOCK-PASS und vier `lokal-...`-IDs sind kein kryptografischer Beleg fuer echte KI-Modellaufrufe. SHA256 ohne unabhaengige Attestierung beweist nur Dateiintegritaet zum Zeitpunkt des Hashings.

## Test-/Freigabeverfahren

1. GitHub Actions `SCHNAPPER Tests` auf **dem finalen HEAD dieses Branches** untersuchen.
2. `python -m unittest discover -s tests -v` und Cloudflare-Offline-Tests muessen gruen sein; negative MASTER-78-Faelle muessen erkennbar laufen.
3. Ungueltige/fehlende Nachweise, falsche Rollen, Symlinks und Dateifehler muessen geschlossen blockieren.
4. Unabhaengiger Review und Abgleich gegen #69/#80 bleiben offen, sofern nicht gesondert nachgewiesen.

**Keine automatische Zusammenfuehrung, kein Deployment, keine kostenpflichtigen API-Aufrufe, keine echte Ollama-/Cloud-KI-Ausfuehrung.**
