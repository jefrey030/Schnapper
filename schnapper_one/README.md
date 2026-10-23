# SCHNAPPER ONE – eigenständiges KI-Viererteam (Vorbereitung)

**Status 23.10.2026: Code-Klon vorbereitet, produktiver KI-Betrieb NICHT freigegeben.**
Dieses Team wurde aus der Architektur des SCHNAPPER-Viererteams abgeleitet.
LEAD, BRAIN, CHECK und COMMAND besitzen voneinander getrennte Rollen,
separate Ergebnisse und eigene Modellanfragen, **sobald ausdrücklich aktiviert**.

## Projektgrenze
Alle Dateien für dieses Teilprojekt liegen nur unter `schnapper_one/` auf
`project/schnapper-one-team-20261023`. Die reguläre SCHNAPPER-App wird nicht
geändert. Es ist **noch kein eigenes GitHub-Repository** (der verbundene
GitHub-Zugang unterstützt das Erstellen neuer Repositories aktuell nicht).
Für eine strikte organisatorische Trennung das Verzeichnis später in ein
eigenes Repository `schnapper-one` übertragen; vorher keine Produktivfreigabe.

## KI-Team – vier unabhängige Schritte
| Agent | Masterauftrag |
|---|---|
| **LEAD** | wählt eine offene ONE-Aufgabe, legt prüfbare Kriterien fest |
| **BRAIN** | erstellt technischen Umsetzungsvorschlag und Testfälle |
| **CHECK** | kontrolliert Vorschlag, Sicherheit, Tests und Grenzen |
| **COMMAND** | fasst alle Belege zusammen, gibt nur interne Empfehlung |

Das Team **plant und prüft**. Es programmiert nicht automatisch,
veröffentlicht nichts, liest keine fremden privaten Konten und kauft nichts.
Selbst grüne Tests sind kein Beweis echter Modellantworten.

## Geschäftsziel
- SCHNAPPER KI, Alltagsassistent: **9,99 EUR/Monat** (Wunschpreis).
- SCHNAPPER Premium (separate Haupt-App): **4,99 EUR/Monat** (Wunschpreis).
- Komplett **12,99 EUR/Monat** (unverbindlicher Bündelvorschlag).
- **5 einmalige kostenlose KI-Aufträge** über beide Funktionen zusammen,
  kein automatischer Wechsel in ein bezahltes Abo.
- Echte KI-Kosten, Rechnungen, Datenschutz, Kündigung und Nutzerrechte vor
  einer Umsetzung gesondert prüfen. Diese Angaben sind noch keine Abo-Funktion.

## Offline Tests (kein Token, keine echten Modelle)
```bash
cd schnapper_one
python -m unittest discover -s tests -v
```

## Agentenbetrieb (noch gesperrt)
GitHub-Models-Backend aus dem SCHNAPPER-Team technisch geklont, aber
`SCHNAPPER_ONE_KI_ENABLED` fehlt standardmäßig und verhindert alle
Modellanfragen. Ein `GITHUB_TOKEN` allein reicht nicht zur Aktivierung.
Es gibt **keinen stündlichen automatischen Workflow** für SCHNAPPER ONE.
Der Workflow `.github/workflows/schnapper-one-agents.yml` erlaubt nur einen
manuellen Lauf bei bewusst aktivierter Gate-Variable im **öffentlichen**
Repository und mit getrennten vier Aufrufschritten. Es werden keine
Produktionsdaten, keine Zahlungen und keine Deployments ausgelöst.

Nach ausdrücklicher Freigabe und Kostenprüfung:
- Variable `SCHNAPPER_ONE_KI_ENABLED=true`
- Manuellen GitHub-Workflow auf dem Projekt-Branch starten
- Vier eindeutige echte Modell-Antwort-IDs, grüner CHECK-Test und
  positiver COMMAND-Bericht sind vor Einsatzbereitschaft erforderlich
- Alle Berichte und Vorschläge werden nur als Workflow-Artefakt
  für die anschließende unabhängige Sichtung aufbewahrt

**Kein echter vierfacher Modelltest bisher nachgewiesen.**
