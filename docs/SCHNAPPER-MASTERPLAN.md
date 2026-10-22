# SCHNAPPER – Masterplan aller offenen Punkte

Stand: 22.10.2026, 10:50 (Berlin) · Basis: `main` @ 4bc37e7 · Erstellt nach echter Prüfung von Repo, PRs, Tests und Actions-Läufen.

**Regeln:** 0 € Zusatzkosten · nichts ungeprüft mergen · nichts ohne Freigabe veröffentlichen · keine erfundenen Ergebnisse.
**Status:** ✅ erledigt (mit Nachweis) · 🔨 in diesem PR · ⏳ wartet auf Jefrey · 🚫 blockiert · 💤 später

## A. App (was Nutzer sehen)

| Nr | Punkt | Status | Nachweis / nächster Schritt |
| --- | --- | --- | --- |
| A1 | Angebots-Kern: Preise prüfen, Dubletten, Suche, Import | ✅ | `main` @ 5343009 (#5) |
| A2 | Handy-Oberfläche im Browser | ✅ | `main` @ 7a0b83e (#10/#11), Browsertest 390×844 |
| A3 | Quellen-Register + Adapter (S-004/S-005) | ✅ | `main` @ 7a0b83e; Kleinanzeigen gesperrt, eBay gesperrt bis Freigabe |
| A4 | **Eigene echte Angebote** laden (Vorlage + Anleitung) | 🔨 | `app/vorlagen/meine-angebote.csv`, `docs/EIGENE-ANGEBOTE.md` |
| A5 | App auf den Startbildschirm (Web-App-Manifest, Icons) | 🔨 | Chromium: 0 Manifest- und 0 Installationsfehler |
| A6 | Start am Android-Handy ohne PC (Termux) | 🔨 | `docs/HANDY-START.md` – **auf echtem Gerät noch ungetestet** |
| A7 | App im Internet, ohne eigenes Gerät | ⏳ | Wäre eine Veröffentlichung → braucht Freigabe. Kostenlos möglich, aber Python-Server müsste dafür umgebaut werden. |
| A8 | Echte Angebote automatisch (eBay Browse API) | ⏳ | Jefrey: eBay-Entwicklerkonto + Produktivfreigabe bei eBay beantragen. Bis dahin nur eigene Listen (A4). |
| A8b | **Echte Ladenpreise ohne Konto (Open Prices, ODbL)** | 🔨 | API-Adapter + getrennte Barcode-Suche in der lokalen Web-App im PR #15; nach neuen Fixes noch nicht erneut ausführbar getestet; **Live-Abruf fehlt**; nur mit `SCHNAPPER_OPENPRICES_FREIGABE=ja` |
| A9 | Preisverlauf, Benachrichtigungen, Konto | 💤 | Bewusst nicht im MVP (Konzept S-000) |

## B. Pull Requests (echter GitHub-Stand)

Stand: 22.10.2026, ca. 20:30 UTC · Basis `main` @ e134cd0 · ermittelt per GitHub-REST `pulls?state=all`. #4 ist ein Issue, kein PR.
Der frühere Abschnitt (Empfehlung #6 → #12 → #7 → #8) ist überholt: Diese PRs sind gemergt bzw. geschlossen.

### Offen (12)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #35 | security: privaten SCHNAPPER-Stundenlauf fail-closed sperren (aktuelle main-Basis) | fix/guard-private-runner-20261022-current | offen | ja |
| #34 | fix(SCHNAPPER): Websuche weist Null- und Negativ-Höchstpreise ab | fix/web-maxpreis-positiv-20261022 | offen | ja |
| #33 | fix(team): offene QA-Aufgabe + fehlerresistente Stundenrotation | fix/schnapper-open-qa-task-20261022 | offen | ja |
| #31 | security(SCHNAPPER): KI-Token nur über HTTPS und ohne Redirect übertragen | security/schnapper-ki-token-transport-20261022 | offen | ja |
| #30 | fix(SCHNAPPER): Preisalarm-Import gegen ungültige Eingaben absichern | fix/schnapper-alarm-nonfinite-20261022 | offen | ja |
| #29 | fix: SCHNAPPER-Preise, URLs und Preisalarm zusammen sicher korrigieren | fix/schnapper-guardrails-konsolidiert-20261022 | offen | ja |
| #28 | fix: SCHNAPPER-Preisalarm bei defekten Wunschlisten robust machen | fix/alarm-input-validation-20261022 | offen | ja |
| #27 | fix(preise): DE/EN-Tausenderformate korrekt und sicher einlesen | fix/preisformate-gemischt-20261022 | offen | ja |
| #26 | fix(SCHNAPPER): Preise im deutschen UND englischen Zahlenformat korrekt erkennen | fix/preisformate-englisch-20261022 | offen | nein |
| #25 | fix(SCHNAPPER): englische Tausenderpreise korrekt lesen statt falscher Schnäppchen | fix/english-thousands-prices-20261022 | offen | ja |
| #23 | fix: Robuster Angebotsimport bei kaputten URLs und korrekte Port-Dubletten | fix/schnapper-url-validierung-20261022 | offen | ja |
| #21 | Security: Fail-Closed-Abnahme, Not-Aus und getrennte Release-Gates | security/schnapper-failclosed-20261022 | offen | ja |

Hinweis: #25, #26, #27 (Preisformate) und #28, #29, #30 (Preisalarm) überschneiden sich thematisch; #29 bündelt laut Titel mehrere davon. Entscheidung bleibt bei Jefrey.

### Gemergt (15)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #32 | QA: kostenfreie Offline-Testabnahme mit unverfälschbaren FAIL-Gates | qa/offline-abnahme-kostenfrei-20261022 | gemergt 22.10. 18:39 UTC | nein |
| #20 | fix(openprices): „Zum Angebot“ öffnet lesbare Preisseite statt JSON + Abnahme main | fix/openprices-link-webseite-20261022 | gemergt 22.10. 18:01 UTC | nein |
| #19 | Preisverlauf: Tiefstpreise und geschönte Statt-Preise erkennen | feature/preisverlauf-20261022 | gemergt 22.10. 18:02 UTC | nein |
| #18 | SCHNAPPER: offene PRs zusammengeführt (#7 #8 #12–#17), Tests repariert | integration/aufraeumen-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #17 | Merkliste und Preisalarm (WARENKORB/BLITZ) | feature/merkliste-preisalarm-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #15 | SCHNAPPER Gesamtstand: offene PRs zusammengeführt + echte Ladenpreise (Open Prices) | integration/schnapper-gesamtstand-20261022 | gemergt 22.10. 16:18 UTC | nein |
| #14 | SCHNAPPER: Masterplan, eigene echte Angebote, App für den Startbildschirm | feature/schnapper-master-handy-20261022 | gemergt 22.10. 16:17 UTC | nein |
| #13 | SCHNAPPER S-005/T3: kostenloser Offline-Mock-Adapter mit Prüffällen | fix/schnapper-offline-mock-adapter-20261022 | gemergt 22.10. 16:17 UTC | ja |
| #11 | SCHNAPPER: Handy-Weboberfläche + sichere Angebotsquellen ohne Merge-Konflikt | fix/schnapper-web-main-20261022 | gemergt 22.10. 03:10 UTC | nein |
| #9 | fix: SCHNAPPER-Agentenstatus und KI-JSON fail-closed validieren | fix/agent-status-fail-closed-20261022 | gemergt 22.10. 08:35 UTC | nein |
| #8 | SCHNAPPER Cloud-Team: vier stündliche KI-Rollen – Free-only, Live-Start gesperrt | feature/cloudflare-free-hourly-20261022 | gemergt 22.10. 16:17 UTC | ja |
| #7 | SCHNAPPER: vier KI-Rollen lokal starten – null Bezahl-APIs, echte Stundenberichte | feature/local-free-ollama-agents-20261021 | gemergt 22.10. 16:17 UTC | ja |
| #5 | SCHNAPPER: App-Kern – Angebote prüfen, Dubletten, Suche, Import | feature/schnapper-angebotskern-20261021 | gemergt 22.10. 03:07 UTC | nein |
| #3 | SCHNAPPER: vier echte KI-Agenten über GitHub Models (0 €), Regelmodus entfernt | fix/ki-team-github-models-20261021 | gemergt 21.10. 20:15 UTC | nein |
| #1 | SCHNAPPER: sichere Aufgabenrotation, Tests und Modus ohne KI-API-Kosten | fix/schnapper-hourly-rotation-20261021 | gemergt 21.10. 20:15 UTC | nein |

### Geschlossen ohne Merge (7)

| PR | Titel | Branch | Status | Draft |
| --- | --- | --- | --- | --- |
| #24 | fix(SCHNAPPER): Preisalarm vor ungültigen Rabatten und Zustandsfiltern schützen | fix/alarm-nonfinite-input-20261022 | geschlossen | ja |
| #22 | SCHNAPPER: Stundenlauf nur bei eindeutig öffentlichem Repo aktivieren | fix/schnapper-stundenlauf-failclosed-20261022 | geschlossen | ja |
| #16 | SCHNAPPER: Preisquellen sichern und Testangebote eindeutig markieren | fix/schnapper-price-source-integrity-20261022 | geschlossen | ja |
| #12 | test: S-001 erlaubt echte Standardbibliothek statt fester Modulliste (Fix für #6 + #7) | fix/schnapper-stdlib-test-20261022 | geschlossen | nein |
| #10 | SCHNAPPER: Web-Oberfläche fürs Handy + Quellen-Register und Adapter (S-002) | feature/schnapper-web-quellen-20261022 | geschlossen | nein |
| #6 | SCHNAPPER MASTER: S-000 bis S-003, Vorschläge S-004–S-006, Abgleich gegen main | agent/master/20261021-21 | geschlossen | ja |
| #2 | SCHNAPPER: kostenloses lokales KI-Gehirn für 4 Agentenrollen | feature/local-free-brain-20261021 | geschlossen | ja |

## C. KI-Team (LEAD, BRAIN, CHECK, COMMAND)

| Nr | Punkt | Status | Nachweis / nächster Schritt |
| --- | --- | --- | --- |
| C1 | Stündliche Läufe auf GitHub | 🚫 | Seit 21.10. wurde **kein** Lauf ausgeführt. Ursache belegt (Job-Annotation): GitHub-Konto meldet fehlgeschlagene Zahlung / Ausgabenlimit. Workflows laufen seit 108509e absichtlich nur in öffentlichem Repo. |
| C2 | Laufzeit festlegen | ⏳ | Jefrey wählt: **(a)** Repo öffentlich → GitHub kostenlos, läuft ohne eigenes Gerät, Code sichtbar · **(b)** #7 → kostenlos, nur wenn PC an · **(c)** #8 → Cloudflare kostenlos, Freigabe nötig |
| C3 | Nachweis echter stündlicher Ausführung | 🚫 | Folgt erst nach C2 |
| C4 | Socket-Warnung in `tests/test_agenten.py` | 🔨 | `server_close()` ergänzt; strenger Testlauf ohne Warnung |

## D. Entscheidungen, die nur Jefrey treffen kann

1. **GitHub-Abrechnung prüfen** (*Settings → Billing and plans*): Warum ist das Konto gesperrt? Nichts Kostenpflichtiges freischalten.
2. **Laufzeit fürs KI-Team** wählen (C2: a, b oder c).
3. **PRs prüfen und mergen** in der Reihenfolge aus Abschnitt B.
4. **eBay-Zugang** beantragen – ja oder nein (A8).
4b. **Open Prices** einschalten – ja oder nein (A8b). Achtung ODbL: Preise nur anzeigen, keine eigene Preisdatenbank daraus.
5. **App öffentlich ins Internet** – ja oder nein (A7).

## E. Kosten
Bisher entstanden: **0 €**. Kein Punkt in diesem Plan erfordert Geld; A7, A8 und C2(c) nutzen nur kostenlose Stufen und brauchen trotzdem vorher deine Freigabe.

## Nachtrag: PR #15 – Barcodeoberfläche und Robustheit (22.10.2026)
- Echte Open-Prices-Stückpreise mit `price_per=UNIT` werden akzeptiert.
- Unendliche/ungültige Preiswerte und kaputte optionale Metadaten werden abgefangen.
- `POST /api/openprices` zeigt die bis zu 50 jüngsten gemeldeten Ladenpreise separat
  von lokalen Listen an; Browserpanel und vier lokale HTTP-Regressionstests hinzugefügt.
- **Sicherheitslage unverändert:** API-Ausgang ohne expliziten Freigabeschalter gesperrt,
  kein Worker/Cron gestartet, kein öffentlicher Server deployed, kein kostenpflichtiger Job.
- **Abnahme fehlt:** Nachträgliche Python-Tests und echte Android-Browserprobe nicht erneut
  ausgeführt; GitHub-Action ist wegen privatem Repository ausdrücklich `skipped`.
- **Nächste Schritte:** vollständige Offline-Tests mit Python ausführen, Barcode live mit
  einer freigegebenen kostenfreien API-Abfrage prüfen, Android-Lauf ohne PC bestätigen,
  Cloudflare-Free-Plan nachweisen; PR erst danach und nach Sichtung mergen.


## Nachtrag 22.10.2026 – weiterer Reparatur- und Kontocheck
- `app/schnapper/web.py`: Filter mit NaN/Infinity oder Rabatten außerhalb 0–100 % liefert 400
  statt eines potenziellen Fehlers; gleichzeitige Barcode-Abrufe werden auf einen
  lokalen API-Aufruf begrenzt, weitere Anfragen erhalten 429.
- `app/schnapper/angebot.py`: extreme Geldbeträge führen zu `AngebotFehler` statt
  unkontrolliertem Decimal-Overflow.
- `app/schnapper/openprices.py`: nicht dekodierbare API-Antworten liefern einen
  kontrollierten Fehler. Regressionstests für die Fälle wurden ergänzt.
- **Tests noch nicht tatsächlich ausgeführt:** GitHub-Actions-Lauf für das aktuelle
  Commit steht auf `skipped` (privates Repo, Kostenschutz); keine Aussage
  „alle grün“ für diesen Stand zulässig.
- Read-only-Cloudflare-Prüfung: Nur Worker `jerry-al` vorhanden,
  D1-Datenbankliste leer, `workers/account-settings` zeigt
  `default_usage_model=standard` (**kein Nachweis für Workers Free**).
  Abonnement-/Billing-Abfrage scheitert weiterhin mit HTTP 403 (fehlender OAuth-Scope).
- **0-€-Sperre beibehalten:** Kein neuer Worker, keine D1, kein Cron, keine KI-Inferenz,
  keine zahlungspflichtige GitHub-Action gestartet.
- Abnahmereihenfolge: (1) Testsuite in einer kostenlosen Python/Node-Umgebung
  wirklich ausführen, (2) auf Android manuell prüfen, (3) Open-Prices-API nur
  nach Freigabe live testen, (4) Workers-Free-Tarif nachweisen und separat
  Team-Pilot mit zwei echten Stundenprotokollen durchführen.
