# SCHNAPPER: kostenlose Offline-Testabnahme

Stand: 22.10.2026. **Kein Deployment, keine Freigabe des autonomen Betriebs.**

## Ausführen

Voraussetzungen: lokale Kopie dieses Repositories mit Git-Metadaten, Python 3.11+ und Node.js 22 (kein `npm install`). Alle Befehle im Repository-Hauptordner:

```bash
python3 scripts/offline_abnahme.py
```

Optional eigenes lokales Protokollverzeichnis:

```bash
python3 scripts/offline_abnahme.py --report-dir ./testberichte-lokal
```

Das Werkzeug startet die bestehenden Python-Unittests mit strenger Warnungsprüfung sowie die vorhandenen `cloudflare/test/*.test.mjs` über Node. Es schreibt `summary.json`, `python.log` und `node.log`. Ohne angegebenen Berichtspfad entstehen die Dateien in einem temporären lokalen Verzeichnis.

## Harte Regeln

- Fehlende Testdateien, fehlendes Python/Node, Timeout, Fehlercode, **übersprungene/fehlende Tests** oder unbekannte Git-Commit-ID => `FAIL`, Exitcode 1.
- `PASS_UNIT_ONLY` bedeutet **ausschließlich**: zwei lokale Testgruppen wurden ohne gemeldete Skips ausgeführt; echte GitHub-CI, Cloudflare-Worker, Staging, Preisquellen, Android und Dauerbetrieb sind **nicht** geprüft.
- Das Werkzeug verwendet keine bezahlten Runner, installiert keine Pakete und ruft selbst keine externen Dienste auf. Bestehende Repository-Tests müssen separat darauf geprüft bleiben, dass sie ausschließlich gemockte oder lokale Quellen nutzen.
- Rohprotokolle können Testdaten enthalten. Nicht veröffentlichen, bevor sie auf Geheimnisse geprüft wurden.
- In privaten Repositories überspringt der bestehende GitHub-Workflow aus Kostenschutz die Runner. Diese Entscheidung bleibt unverändert. `skipped` ist nie ein Abnahmenachweis.

## Eigenprüfung des Werkzeugs

Isolierte lokale Test-Fix­tures, keine SCHNAPPER-Gesamtsuite:
- 1 Python- und 1 Node-Test erfolgreich => `PASS_UNIT_ONLY`.
- 1 übersprungener Python-Test => `FAIL`.
- Beide Testordner fehlen => `FAIL`.

**Vor jeder Live-Freigabe weiterhin notwendig:** komplette Tests für die genaue Ziel-SHA, Sicherheitsprüfung, Staging-/End-to-End-Abnahme, Not-Aus-Test, 0-€-Kostenprüfung und ausdrückliche Betreiberfreigabe.
