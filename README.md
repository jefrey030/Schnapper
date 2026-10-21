# SCHNAPPER – Vier-Agenten-Team

Eigenständige, von ZENTNA getrennte Entwicklungsumgebung mit vier Rollen:
- **LEAD:** Arbeitsaufträge priorisieren.
- **BRAIN:** technische Lösungspläne erarbeiten.
- **CHECK:** Tests, Risiken und Blocker prüfen.
- **COMMAND:** Ergebnisse abnehmen, zusammenfassen und dokumentieren.

## Status
Dies ist eine **neu erstellte Grundstruktur**, keine wiederhergestellte alte `schnapper-team.zip`.
Sie enthält einen stündlichen GitHub-Actions-Lauf, persistent gespeicherte Laufberichte und optionale Claude-API-Aufrufe.

### Ohne API-Zugang
GitHub Actions kann die Team-Logik und die technischen Checks ausführen und Berichte speichern. **Vier eigenständige KI-Modelle arbeiten dabei noch nicht.** Die Agenten laufen im sicheren Regelmodus.

### Echte KI-Aufrufe aktivieren – erst nach Kostenfreigabe
1. In GitHub unter *Settings > Secrets and variables > Actions* das Repository-Secret `ANTHROPIC_API_KEY` setzen (niemals in Dateien oder Chats posten).
2. Unter *Variables* die Variable `SCHNAPPER_AI_ENABLED` auf `true` setzen.
3. Optional die Variable `ANTHROPIC_MODEL` definieren.
4. Unter *Actions > SCHNAPPER Stundenlauf > Run workflow* testweise ausführen.
5. Den Bericht in `team/STATUS.md` und `team/runs/` kontrollieren.

**Achtung:** API-Nutzung kann Kosten verursachen; vier KI-Aufrufe je Stundenlauf können sich summieren. GitHub Actions hat ebenfalls Nutzungsgrenzen. Die Automatik führt keine beliebigen Shellbefehle aus Aufgaben aus, verändert keinen App-Quellcode und veröffentlicht nichts. Für eigenständige Implementierung, PR-Erstellung und echte externe Schnäppchenabfragen sind weitere kontrollierte Integrationen erforderlich.

### Dateien
- `team/tasks.json` — nachvollziehbarer Aufgabenbestand
- `team/runner.py` — vier Rollen mit optionalen Claude-API-Aufrufen
- `tests/test_runner.py` — Grundtests
- `.github/workflows/schnapper-hourly.yml` — stündliche Ausführung
- `team/STATUS.md` und `team/runs/` — Ergebnisse und Prüfspur

**Wichtig:** Für Preisvergleiche über eBay oder andere Plattformen werden separate erlaubte Datenquellen bzw. API-Zugänge benötigt. Kein produktiver externer Zugriff eingerichtet.
