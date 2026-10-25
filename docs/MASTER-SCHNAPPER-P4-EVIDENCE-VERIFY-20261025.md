# SCHNAPPER – MASTER P4: Nachweisprüfer mit SHA-256 und manipulationssicherer Pfadkontrolle

**Datum:** 25.10.2026 · **Priorität:** P0/P1 · **Budget:** 0 € Zusatzkosten · **Änderungsziel:** ausschließlich [Draft PR #55](https://github.com/jefrey030/Schnapper/pull/55)  
**Status zu Beginn:** `main` bleibt unberührt; Produktionsfreigabe **NO-GO**.

## Ziel und festgestellte Lücke
Der lokale Pilot schreibt bereits `team/work/<Lauf>/nachweise.json` mit SHA-256-Fingerabdrücken von Stundenbericht, Prozessbericht und vorhandenen Rollenberichten. Eine belastbare Offline-Funktion zum späteren Prüfen dieser Fingerabdrücke fehlt. Ein beschädigtes Ergebnis ist deshalb ohne gesonderten manuellen Vergleich nicht unmittelbar überprüfbar. Der neue Master ergänzt die technische Wiederholbarkeit der Integritätsprüfung, ohne durch bloße Checks echte KI-Agenten zu behaupten.

## Große Auftragsverteilung (Rollen als Arbeitsgebiete, NICHT externe aktive Agenten)

| Arbeitsrolle | Konkrete Aufgabe | Abnahmekriterium |
| --- | --- | --- |
| LEAD | Branch und vorhandene Nachweise prüfen, Kompatibilität und minimale Änderungen planen | Ein Master und ein Review-Draft, keine Doppel-PR |
| BRAIN | Unabhängigen lokalen Nachweisprüfer bauen; SHA-256 gegen vorhandene Dateien verifizieren, strenge Pfad-Whitelist | Keine fremden Pfade oder symbolischen Links öffnen |
| CHECK | Positive und manipulierte Offline-Testfixtures prüfen: Byte-Änderung, fehlende Datei, falscher Hash, Pfad-Traversal, unzulässiger Ordner | GitHub CI grün, reale Testzahlen angegeben |
| COMMAND | Abschlussreport mit SHA, CI-Run, blockierten Restpunkten und Nullkosten-Regeln erstellen | Dokumentation statt Fake-Autonomie |

## Sicherheits- und Funktionalitätsvorgaben

1. `python team/local_service.py --verify <LAUFORDNER>` liest ausschließlich lokale Artefakte und startet **kein** Ollama, kein Netzwerk und keine Agents.
2. Ein erlaubter Lauf ist ein direktes Verzeichnis unter `team/work/`; Pfadübergreifungen, Dateisymlinks und selbst gewählte fremde Pfadnamen werden blockiert. Fehlerlogs enthalten keine Rohdaten aus Berichten.
3. `nachweise.json` muss alle erwarteten Dateien exakt benennen. SHA-256 stimmt Byte-für-Byte überein. Fehlende, zu große und beschädigte Dateien gelten nicht als bestanden.
4. Positiv gilt nur `INTEGRITAET_OK` – niemals `KI_ERFOLGREICH`. Prüfsummen sind **keine digitale Signatur** und schützen nicht gegen Personen, die alle Dateien samt Manifest ändern können.
5. Der Prüfer wird auch nach Erstellung eines Nachweises eingesetzt, um Format-/Prüffehler bei erfolgreichen und blockierten Piloten zu entdecken.
6. Vor Merge: GitHub Actions Python- und Cloudflare-Tests grün; Produktionssysteme, `main` und kostenpflichtige Dienste bleiben unverändert.

## Abnahmecheckliste
- [ ] Lokaler Nur-Lese-Nachweisprüfer implementiert
- [ ] Reine Offline-CLI `--verify` implementiert
- [ ] Manipulations- und Pfadkontrolltests erfolgreich
- [ ] Echter CI-Testlauf für Python + Cloudflare erfolgreich
- [ ] GitHub-HEAD und Nachweise dokumentiert
- [ ] Unabhängige Produktionsfreigabe ausdrücklich weiterhin NO-GO
