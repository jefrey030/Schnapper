# SCHNAPPER MASTER 6 – Produktintegration

Stand: 26. Oktober 2026<br>
Arbeitsbranch: `replit/master6-product-integration-20261026`<br>
Basis: PR #129, SHA `4ac56d01cee82dded7a82f63f384524050293561`<br>
Arbeitsmodus: lokaler Branch; kein Push, kein neuer PR, kein Merge, kein Deployment.

## Ergebnis

Die vorhandene SCHNAPPER-Webapp wurde auf dem PR-#129-Stand weitergeführt. LUPE, WARENKORB, PREISDETEKTIV, MISSION und BLITZ sind in der Oberfläche verbunden. Die Suche verarbeitet nur geladene CSV-/JSON-Daten und ausdrücklich freigegebene Quellen; es wurden keine Angebote erzeugt, keine Kauf- oder Kontaktaktionen ausgeführt und keine Nutzungsbeschränkungen umgangen.

Der Arbeitsstand ist testbar, aber **nicht produktiv freigegeben**. Der neue Branch wurde nicht zu GitHub hochgeladen, weil für diesen Auftrag ein Upload erst nach gesonderter ausdrücklicher Freigabe erfolgen darf.

## Modulstatus

| Modul | Status | Tatsächlicher Umfang / Grenze |
|---|---|---|
| LUPE | PASS – offline und lokal | Begriff, Preis, Zustand, Sortierung, Region und Umkreis; Region/Entfernung werden ausschließlich aus vorhandenen Angebotsfeldern gefiltert. Dubletten, Warnungen, leere Treffer und Fehler werden angezeigt. Keine aktive Marktplatzsuche. |
| WARENKORB | PASS – Browser | Merken, entfernen, Preis/Quelle/Versand anzeigen, Angebote zur Vergleichsauswahl markieren und nach Neuladen wiederherstellen. Fehlerhafte lokale JSON-Daten werden nicht überschrieben. |
| PREISDETEKTIV | PASS – verfügbare Daten | Vergleich der ausgewählten Warenkorb-Angebote einschließlich Gesamtpreis/Versand, vorhandener Preisbeobachtungen und Warnungen. Fehlende Historie wird angezeigt. Ein Händler-„Statt“-Preis wird nicht als unabhängig bestätigter Marktpreis ausgegeben. |
| MISSION | PASS – lokaler Server | Erstellen, Bearbeiten, Pausieren, Fortsetzen, Löschen, manuelles Prüfen und persistente lokale Speicherung. Parallele Läufe derselben Mission werden innerhalb eines Serverprozesses abgewiesen. Automatik nur nach Opt-in, im sichtbaren offenen Browser und mit tabübergreifender Browser-Sperre; kein Lauf nach dem Schließen. |
| BLITZ | PASS – lokale Queue | Neue Missionstreffer mit Quelle, Preis und Angebotslink; dauerhaft dedupliziert, im Browser lokal gespeichert und als gesehen markierbar. Browser-Benachrichtigung nur nach Berechtigung und bei offenem Vordergrundlauf; Queue-Eintrag ist ausdrücklich kein Zustellnachweis. |
| Vier KI-Rollen | NICHT in der App gestartet | LEAD/BRAIN/CHECK/COMMAND bleiben durch die vorhandene Freigabe-/STOP-Logik geschützt. Die Webapp startet keine Modellaufrufe und zeigt keine synthetischen Antworten als KI-Ergebnis an. Im Laufzeit-Check fehlten lokale Ollama-Installation, erreichbares Modell und gültige Freigabe. |
| Android / PWA | PASS – Chromium-Mobil-Emulation; NOT_RUN – echtes Gerät/APK | Responsiver 390×844-Ablauf und Service-Worker-Shell geprüft. API-Daten bleiben onlineabhängig. Kein Android-Gerät/ADB verfügbar, keine APK gebaut und keine Veröffentlichung. Eine installierbare PWA erfordert auf Android einen HTTPS-Ursprung. |

## Änderungen in diesem Branch

- `app/schnapper/suche.py`, `alarm.py`, `blitz.py`: optionale Region-/Entfernungsfilter; die Wunsch-Deduplizierung unterscheidet diese Filter; BLITZ-Meldungen nennen die Quellkennung.
- `app/schnapper/mission.py`: persistente Suchfelder, Bearbeiten/Löschen und kontrollierte Erfassung manueller Läufe.
- `app/schnapper/web.py`: lokale Missions-/BLITZ-Endpunkte, Lauf-Sperre, Größen-/Inhaltsprüfung für JSON, gesichertes lokales Datenverzeichnis sowie Service-Worker-Auslieferung.
- `app/schnapper/web/index.html`, `app.js`, `app.css`, `sw.js`: sechs Bereiche, mobile Navigation, Warenkorbvergleich, Missionen, BLITZ-Queue, Einstellungen, Benachrichtigungsfreigabe und Offline-App-Shell. API-Antworten werden nicht durch den Service Worker zwischengespeichert.
- `tests/test_product_integration.py`: HTTP-Integration für Suche → Mission → BLITZ, Persistenz über Serverneustart, automatische Fälligkeit/Opt-in, Bearbeiten/Löschen, parallele Laufabwehr, Service Worker und Symlink-Schutz.
- `tests/test_app_quellen_web.py`: Oberflächentest auf die neuen App-Bereiche aktualisiert.

Die bestehenden Freigaben wurden beibehalten: eigene CSV-/JSON-Daten und Testdaten sind nutzbar; Open Prices und eBay bleiben ohne die bereits festgelegten Freigaben inaktiv; Kleinanzeigen bleibt ausgeschlossen. In den Tests wurde kein Netzwerkzugriff zu gesperrten Quellen ausgelöst.

## Verifikation

| Prüfschritt | Ergebnis |
|---|---|
| Gesamte Python-Suite (`GITHUB_ACTIONS=true`, Development-Modus, Warnings als Fehler) | **PASS** — 506 Tests, 0 Fehler, 0 SKIP; S-006 war aktiv und erfolgreich |
| Cloudflare offline suite | **PASS** — 16 Tests, 0 Fehler, 0 SKIP |
| S-006 separat, mit allen benötigten Remote-Refs lokal vorhanden | **PASS** — 4 Tests, 0 SKIP |
| Betreiberfreigabe, Ollama-Metadaten, Zähler/Quota | **PASS** — 43 fokussierte Tests; keine echte Inferenz ausgeführt |
| STOP/Timeout/Prozessbaum und geschützte Dateipfade | **PASS** — 17 Agent-STOP-Tests plus 5 Pfad-/Kindprozess-Tests |
| Neue Produkt-HTTP-Integration | **PASS** — 7 Tests |
| Chromium, mobile Emulation 390×844 | **PASS** — Suche, Warenkorb, Preisvergleich, Mission erstellen/ausführen, BLITZ, Einstellungen; 0 Browser-JavaScript-Ausnahmen |
| Chromium, Neuladen / lokale Wiederherstellung | **PASS** — Warenkorb, Mission und BLITZ-Queue nach Reload vorhanden; BLITZ „gesehen“ gespeichert |
| Beschädigter Browserdatensatz | **PASS** — unveränderte Rohdaten blieben erhalten, Warnung sichtbar, keine JS-Ausnahme |
| Service Worker | **PASS** — lokale PWA-Shell registriert; API-Pfade werden nicht gecacht |
| Geheimnisprüfung des geänderten Diffs | **PASS – begrenzt** — fünf häufige Credential-Muster geprüft, 0 Treffer; kein vollständiger Repository- oder Provider-Scan |
| Android-Gerät/APK | **NOT_RUN** — ADB fehlt; kein echtes Gerät und kein APK-Build getestet |
| Echte KI-Inferenz | **NOT_RUN** — `scripts/p0_readiness.py` meldete `e2e_ready=false`; kein Modell angerufen, keine Freigabe erzeugt |
| Live-Angebotsquellen / Nutzungsrechte | **NOT_RUN** — keine ungeprüfte Live-Quelle aktiviert |
| Deployment, Kauf oder Kontaktaufnahme | **NOT_RUN** — ausdrücklich außerhalb des Auftrags |

Reproduzierbare Abnahme:

```sh
git fetch --no-tags origin '+refs/heads/*:refs/remotes/origin/*'
GITHUB_ACTIONS=true PYTHONPATH=app python3 -X dev -W error -m unittest discover -s tests -v
node --test cloudflare/test/*.test.mjs
GITHUB_ACTIONS=true PYTHONPATH=app python3 -X dev -W error -m unittest discover -s tests -p test_branches_s006.py -v
PYTHONPATH=app python3 -m unittest tests.test_product_integration -v
PYTHONPATH=app python3 -m py_compile app/schnapper/*.py
node --check app/schnapper/web/app.js
node --check app/schnapper/web/sw.js
git diff --check
```

Der vorhandene Sammler kann Python-/Cloudflare-Rohlogs und JSON-Zusammenfassung ablegen:

```sh
GITHUB_ACTIONS=true PYTHONPATH=app python3 scripts/offline_abnahme.py --report-dir /tmp/schnapper-master6-abnahme
```

`PASS_UNIT_ONLY` aus diesem Sammler ist kein Produktions- oder KI-Freigabenachweis.

## PR #129 – GitHub Actions auf der exakten Basis-SHA

Read-only auf `4ac56d01cee82dded7a82f63f384524050293561` geprüft: Workflow-Lauf `40388669054` abgeschlossen mit `success`; Python- und Cloudflare-Jobs beide `success`. PR #129 ist weiterhin Draft/offen und basiert auf `main` SHA `6dbe114271b332ed9d4c282b50c4ce02b112ac49`. Der GitHub-Run testete den PR-Merge-Stand `0aaf6dabac707f7165b2620f851665b07599432f` — nicht den hier nicht hochgeladenen MASTER-6-Branch.

- Actions-Lauf: <https://github.com/jefrey030/Schnapper/actions/runs/40388669054>
- Python-Rohlog: <https://github.com/jefrey030/Schnapper/actions/runs/40388669054/job/121803577879>
- Cloudflare-Rohlog: <https://github.com/jefrey030/Schnapper/actions/runs/40388669054/job/121803578229>

## Offene Abnahmeblocker

1. Keine zugelassene aktuelle Angebotsquelle wurde aktiviert. Ohne eigene rechtmäßig verfügbare Liste bleibt LUPE eine lokale/importbasierte Suche; keine Aussage über Live-Marktpreise.
2. Kein echtes Android-Gerät, keine HTTPS-Produktivadresse und kein APK-Build getestet. LAN-Bindung ist nicht als sichere Produktivbereitstellung zu behandeln.
3. Das vorhandene Vier-KI-System ist nicht in die Weboberfläche eingebunden und wurde nicht ausgeführt. Lokales Modell und ausdrückliche Betreiberfreigabe fehlen; deshalb keine echte KI-Abnahme.
4. Eine laufende MISSION-Suche ist ein kurzer synchroner, lokaler In-Memory-Vorgang ohne Kindprozess. Pausieren verhindert weitere geplante Läufe, ist aber kein Abbruch eines bereits gestarteten Such-Threads.
5. Kein GitHub-Upload für diesen Arbeitsbranch und kein neuer Draft-PR: dafür fehlt die gesonderte ausdrückliche Freigabe.

## Hand-off

Der Branch basiert exakt auf PR #129 und verändert weder PR #129 noch `main` oder andere Entwicklungsbranches. Die lokale Abnahme deckt den Produktablauf und die vorhandenen Sicherheitsregressionen ab. Vor jeder externen Abgabe muss WORK den lokalen Commit, Testbelege und die oben genannten Grenzen unabhängig prüfen. Es erfolgten keine produktiven Datenänderungen, kostenpflichtigen Aufrufe, Berechtigungsänderungen, Merges oder Deployments.
