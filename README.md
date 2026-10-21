# SCHNAPPER – Vier-Agenten-Team

Eigenständige, von ZENTNA getrennte Entwicklungsumgebung mit vier Rollen:
- **LEAD:** Arbeitsaufträge priorisieren.
- **BRAIN:** technische Lösungspläne erarbeiten.
- **CHECK:** Tests, Risiken und Blocker prüfen.
- **COMMAND:** Ergebnisse abnehmen, zusammenfassen und dokumentieren.

## Status
Dies ist eine **neu erstellte Grundstruktur**, keine wiederhergestellte alte `schnapper-team.zip`.
Sie enthält einen stündlichen GitHub-Actions-Lauf, persistent gespeicherte Laufberichte und optionale Claude-API-Aufrufe.

### Kostenfreier Betriebsmodus (gewählt am 21.10.2026)
Keine kostenpflichtige Claude-/Anthropic-API verwenden. Der Stunden-Workflow übermittelt keine KI-Schlüssel. Der Runner führt nur kostenfreie, deterministische Regeln und lokale Tests aus. Die Rollen LEAD, BRAIN, CHECK, COMMAND protokollieren Arbeitsschritte, sind aber **keine vier eigenständig denkenden KI-Modelle**. Eigenständige App-Programmierung und Live-Schnäppchen-Suche sind damit noch nicht aktiv.

**Kostenhinweis:** GitHub Actions in privaten Repositories verbraucht die auf Kontoebene enthaltenen Freiminuten und ggf. kostenpflichtige Zusatznutzung. Die Kontoeinstellungen für Budget/Ausgabenbegrenzung sind nicht durch den Repository-Code kontrollierbar. Wer ausnahmslos 0 EUR Kosten möchte, muss dort eine harte Ausgabenbegrenzung festlegen und die Nutzung prüfen.

**Nachweis:** Eine Workflow-Datei allein beweist keinen tatsächlich erfolgten Stundenlauf. Für einen echten Nachweis müssen ein erfolgreicher Actions-Lauf, ein neuer `team/runs/*.json`-Bericht und ein aktualisierter `team/STATUS.md` vorliegen. Solange keine erfolgreichen Läufe nachweisbar sind, lautet der Status **nicht bestätigt**.

### Aktuelle Grenzen
- Keine Claude-KI-Aufrufe, keine kostenpflichtigen APIs.
- Keine autonomen Quellcode-Änderungen oder Veröffentlichungen.
- Keine realen eBay-/Marktplatz-Datenquellen.
- Prüfen, warum der GitHub-Actions-Testlauf https://github.com/jefrey030/Schnapper/actions/runs/39618950031 fehlgeschlagen ist, bevor die PR integriert wird.

### Dateien
- `team/tasks.json` — nachvollziehbarer Aufgabenbestand
- `team/runner.py` — vier Rollen mit optionalen Claude-API-Aufrufen
- `tests/test_runner.py` — Grundtests
- `.github/workflows/schnapper-hourly.yml` — stündliche Ausführung
- `team/STATUS.md` und `team/runs/` — Ergebnisse und Prüfspur

**Wichtig:** Für Preisvergleiche über eBay oder andere Plattformen werden separate erlaubte Datenquellen bzw. API-Zugänge benötigt. Kein produktiver externer Zugriff eingerichtet.
