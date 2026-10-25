# SCHNAPPER MASTER 80 – Ollama-Aufrufzähler gegen Manipulation und Parallelzugriffe absichern

**Stand:** 25.10.2026  
**Repository:** `jefrey030/Schnapper`  
**Basis:** MASTER 79 / Draft [PR #101](https://github.com/jefrey030/Schnapper/pull/101), HEAD `b201e9bf9e59e87848b2038981a566e0554c3353`  
**Neuer Arbeitsbranch:** `fix/master80-local-counter-integrity-20261025`  
**Priorität:** P0 Sicherheitsgrenzen, P1 Testintegrität  
**Budget:** 0 EUR Zusatzkosten. Nur die kostenfreien GitHub-Standardrunner im öffentlichen Repo; rein lokale synthetische Offline-Tests.  
**Freigabe:** Draft, **NO-GO** für Merge, Deployment, echte Modellaktivierung und Produktivdaten.

## Ursache

In `team/local_ollama.py` verwendete der persistierte Aufrufzähler `Path.exists/read_text/write_text` ohne exklusive Sperre. Ein Symlink konnte ungewollt fremde Dateien schreiben. Zwei gleichzeitig startende Prozesse konnten denselben alten Wert lesen, denselben Wert zurückschreiben und damit die Obergrenze unterzählen. Außerdem lieferte `frage()` die Aufrufnummer durch späteres Nachlesen der Datei, wodurch eine falsche Zuordnung bei Parallelität möglich war.

## Umsetzung auf eigenem Branch

- `_zaehle()` öffnet den Zähler auf POSIX mit `os.O_NOFOLLOW | os.O_NONBLOCK | os.O_CLOEXEC` (wo verfügbar) und sperrt den geöffneten FD mit `fcntl.flock`.
- Die FD-Prüfung lehnt alle nichtregulären Dateien und Hardlinks ab. Ungültige oder überlange Werte werden abgewiesen; die alte Datei wird dabei nicht überschrieben.
- Nach Sperre und Überprüfung reserviert die Funktion exakt eine neue Nummer und schreibt sie als achtstellige ASCII-Zahl ohne `truncate`; danach `flush` und `fsync`.
- `frage()` liefert die direkt reservierte Nummer statt eines zweiten unsicheren Dateilesevorgangs.
- `tests/test_master80_counter.py`: 15 neue Offline-Testmethoden gegen Symlinks, Hardlinks, falsche Werte, Limits, Parallelität und fehlerhafte KI-Antworten.

**Grenzen:** Weder die UUID noch der lokale Zähler beweisen vier reale Modellinferenz-Aufrufe. Die FD-Sperre schützt kooperierende Prozesse auf demselben Dateiinode, nicht gegen bösartige berechtigte Prozesse, die das Verzeichnis oder die Datei austauschen. Crash-Konsistenz beim allerersten Anlegen oder Betriebssystem-Dateisystemfehler ist nicht vollständig formal bewiesen. Dieses Paket stellt keine unabhängige Attestierung dar.

## Abnahmeliste (28 Punkte)

| # | Auftrag | Erwartete Abnahme |
| -: | --- | --- |
| 01 | Repository und Branch | jefrey030/Schnapper; Basis MASTER 79 |
| 02 | Basis-SHA verifizieren | b201e9bf9e59e87848b2038981a566e0554c3353 |
| 03 | PR #101 unverändert lassen | Nur neuer gestapelter Branch |
| 04 | Andere laufende Arbeiten respektieren | Keine fremden Branch-/PR-Updates |
| 05 | Aufrufzähler-Lücke belegen | Path.read_text/write_text ohne Lock |
| 06 | Keine Provideraktivierung | Nur lokaler Offline-Code |
| 07 | O_NOFOLLOW erzwingen | Symlink beim Öffnen blockieren |
| 08 | Keine blockierenden Spezialdateien | O_NONBLOCK |
| 09 | Reguläre Datei fordern | fstat + S_ISREG |
| 10 | Hardlinks ablehnen | nlink == 1 |
| 11 | File-Deskriptor atomar sperren | fcntl.flock(LOCK_EX) |
| 12 | Counter klein und streng parsen | ASCII 1–8 Stellen; leer nur initial |
| 13 | Negativwerte und Freitext sperren | Ohne Überschreiben ablehnen |
| 14 | Kostenlimit vor Inkrement prüfen | MAX_AUFRUFE |
| 15 | Counter nie beim Limit zurücksetzen | Vorhandenen Wert erhalten |
| 16 | Inkrement ohne Truncate-Zeitfenster | Achtstellige feste Breite |
| 17 | Sichere Dateischreibprüfung | write, flush, fsync |
| 18 | Nummer aus Reservierung nutzen | Kein zweites Nachlesen |
| 19 | Symlink-Regressionsfall | Externe Datei bleibt unverändert |
| 20 | Dangling Symlink | Fail-closed |
| 21 | FIFO/Verzeichnis/Hardlink | Fail-closed |
| 22 | Legacy-Zähler | Einstelliger Zähler lesbar |
| 23 | Manipulierte Counterformate | Abweisung ohne Mutation |
| 24 | Parallelzugriff simulieren | 6 eindeutige Werte, 6 blockierte |
| 25 | Fehlgeschlagene Modellantwort | Reservierung bleibt verbraucht |
| 26 | 15 neue Offline-Unittests | Keine echte Ollama-Instanz |
| 27 | CI am finalen SHA prüfen | Python und Cloudflare Jobs + Logs |
| 28 | Unabhängiger Review und Produktfreigabe | Bleibt NO-GO |

## Stoppsignale

Sicherheitstestfehler, unvollständige Logs, fehlender Final-HEAD-Nachweis, unklare Kosten, reale Netzwerk-Aufrufe, unabhängiger Review fehlt: **NO-GO**. Keine Änderung an `main`, keine automatischen Merges, kein Ollama-Download, kein Provider-Fallback und keine Änderung an Produktivdaten.

## Nachvollziehbare Tests

`python -m unittest discover -s tests -v` sowie `cd cloudflare && node --test test/*.test.mjs` auf finalem SHA im GitHub Workflow. Ein bestandener MOCK ist **kein** erfolgreicher Pilot echter KI-Agenten.
