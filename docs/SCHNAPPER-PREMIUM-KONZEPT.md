# SCHNAPPER Premium und zusätzliche Erlöswege
Stand: 23.10.2026 · STATUS: KONZEPT / KEINE LIVE-ZAHLUNGEN

## Produktprinzip
SCHNAPPER bleibt in der Grundversion nützlich und kostenlos. Vorhandene Funktionen
werden **nicht rückwirkend gesperrt**: lokale Suche, Filter, Merkliste, bis zu 50
lokale Preisalarme und heutige Sicherheits-/Betrugshinweise bleiben Free.
Die vorhandenen Preisalarme prüfen nur die geladene Liste beim Öffnen: keine
Hintergrundsuche, keine Push-Nachrichten, keine Live-Angebotsgarantie.

## Kandidat für den ersten Premium-Tarif
**Arbeitspreis:** 4,99 EUR pro Monat inkl. gesetzlicher Umsatzsteuer (nur
Hypothese; erst mit Nutzertests und Kostenmessung validieren). Monatlich
kündbar, Preis und Vertragsbedingungen vor Vertragsschluss klar angeben.
Keine echte Kasse, keine Abo-Aktivierung und keine automatische Abbuchung
durch dieses Konzept.

### Kostenlose Premium-Probe: 5 Ausführungen (geplanter Startwert)
Jedes neu registrierte Konto erhält **einmalig 5 kostenlose Premium-Credits**
insgesamt, nicht 5 je Funktion. Das ist ein Vorschlag für den Produktstart,
vor Freigabe durch Messung realer Kosten pro Ausführung zu validieren.
Zwei Credits wurden erwogen, aber fünf ermöglichen mehrere sinnvolle Vergleiche.

- **1 Credit** gilt für eine ausdrücklich durch Nutzer gestartete,
  erfolgreich beantwortete KI-Schnäppchenanalyse oder einen Produktvergleich.
  Technische Fehler und abgelehnte Anfragen verbrauchen keinen Credit.
- **0 Credits** für die bereits kostenlosen Kernfunktionen, Sicherheits-
  und Betrugswarnungen. Keine nachträgliche Bezahlschranke.
- Kostenintensives **Dauer-Monitoring, Hintergrundsuche und Push** zählen
  nicht als unbegrenzte Einzel-Ausführung: dafür später ein ausdrücklich
  definiertes, hart limitiertes separates Testkontingent.
- Der Rest wird transparent angezeigt: `Noch 5 / 4 / ... / 0 kostenlose
  Premium-Ausführungen`. Bei 0: optionales Premium-Angebot, **keine
  automatische Verlängerung, Abbuchung oder Abo-Buchung**.
- Zähler und Rechte serverseitig, atomar und idempotent je Ausführung;
  erneuter Login, Gerätewechsel oder Browserdaten-Löschung setzen sie
  nicht zurück. Test gegen doppelte Requests, parallele Aufrufe und
  missbräuchliche Mehrfachkonten. Datensparsamkeit beachten.
- Solange Authentifizierung, freigegebene Live-Datenquellen, Kostenschutz
  und Premium-Funktionen fehlen, ist **nur dieser Entwurf** vorhanden.
  Vor Livegang Maximalaufwand pro Trial-Nutzer und Budgetgrenze messen.

### Free / Premium — geplante Unterschiede
| Funktion | Free (Bestand) | Premium (erst nach Umsetzung) |
| --- | --- | --- |
| Lokale Suche, Sortierung, sichere Angebotsprüfung | Ja | Ja |
| Merkliste und lokale Preisalarme | Wie bisher | Wie bisher |
| Neue Angebote von **freigegebenen** Quellen regelmäßig prüfen | Nein | Nach Datenquellen-Freigabe |
| Benachrichtigungen per Push/E-Mail | Nein | Opt-in, erst nach zuverlässigem Hintergrundbetrieb |
| Mehrere Wunschprofile mit Region/Zustand/Versand | Nein | Nach Umsetzung |
| Erweiterte Preisvergleiche und begründete KI-Erklärungen | Nur vorhandener Preisverlauf | Nach zuverlässigem Datenbestand |
| KI-Scout: nachvollziehbare Kaufempfehlung ohne automatischen Kauf | Nein | Nach Umsetzung |

**Sicherheitsfunktionen niemals hinter Bezahlschranke verstecken:**
Verdachtswarnungen, fragwürdige Referenzpreise, alte Daten und Quellenhinweise.

## SCHNAPPER KI – Alltagsassistent (geplante zweite Produktsäule)
SCHNAPPER soll zugleich als allgemeiner KI-Assistent für Alltagsthemen dienen,
zum Beispiel Texte, E-Mails, Bewerbungen, Lernen, Ideen, Rezepte, Organisation,
Fragen und Erklärungen. Ein eigener, klar gekennzeichneter Chat-Bereich ist
vorgesehen. Es handelt sich noch **nicht um eine implementierte Funktion** und
nicht um ChatGPT selbst. Ein geeignetes KI-Modell kann später über eine
kontrollierte Schnittstelle angebunden werden.

### Navigation und Abos – gewünschte monatliche Arbeitspreise
| Plan | Monatspreis | Inhalt |
| --- | ---: | --- |
| Free | 0 EUR | Bestehende Gratis-Suche und 5 gemeinsame KI-Probeausführungen |
| SCHNAPPER Premium | 4,99 EUR | Geplanter KI-Schnäppchen-Autopilot |
| SCHNAPPER KI | 9,99 EUR | Geplanter allgemeiner Alltagsassistent |
| SCHNAPPER Komplett | 12,99 EUR | Beide Abos zusammen; Bündelpreis als Vorschlag |

Der Nutzer hat **4,99 EUR für Premium und 9,99 EUR für SCHNAPPER KI**
gewählt. Die 12,99 EUR für Komplett sind noch ein unverbindlicher Vorschlag.
Alle Preise sind nur für die Produktplanung: vor Aktivierung reale laufende
Modellkosten, Zahlungsgebühren, Datenschutz, rechtliche Anforderungen und
Nachfrage prüfen. Keine unbeschränkte KI-Nutzung versprechen.

### Gemeinsamer kostenloser KI-Test
Ein neu registriertes Konto bekommt einmalig **5 kostenlose KI-Ausführungen
insgesamt**, nicht fünf je Produkt. Ein erfolgreicher, vom Nutzer ausgelöster
KI-Chat-Auftrag oder KI-Produktcheck verbraucht einen Credit. Technische Fehler
verbrauchen keinen Credit, normale kostenlose Suche und Sicherheitswarnungen
ebenfalls nicht. Monitoring und Benachrichtigungen bekommen gesonderte
Kosten-/Nutzungslimits. Es gibt nach den 5 Ausführungen **keine automatische
Abo-Umwandlung oder Abbuchung**.

### Voraussetzungen vor jeglichem Livegang
- Authentifizierung und serverseitig manipulationsgeschützte Credits,
  idempotente Abzüge, Abo-Rechte und fair-use-Limits implementieren und testen.
- Sichere Modell-Schnittstelle mit hartem Kostenbudget, Missbrauchsschutz,
  Fehlerbehandlung und expliziten Ausführungsgrenzen entwickeln.
- Datenschutzhinweise, Löschoptionen und Umgang mit Chatinhalten klar regeln;
  keine automatische Weitergabe privater Chatinhalte an Händler.
- Produktbezogene Live-Suche nur über genehmigte, echte und aktuell geprüfte
  Datenquellen. Keine erfundenen Angebote und keine selbstständigen Käufe.
- Zahlungsflüsse nur im Testmodus entwickeln; Abo, Kündigung, Erstattung und
  Rechtewechsel unabhängig prüfen, bevor irgendetwas öffentlich buchbar wird.
- Getrennte Produktnutzungsdaten und Deckungsbeiträge je Tarif messen.
- Bestehende Gratisfunktionen und Schutzwarnungen nicht einschränken.

## Zusätzliche Einnahmen (getrennt messen)
1. Affiliate-Erlöse aus zulässigen Partnerprogrammen; offenlegen, klar markierte
   Links, Quellen- und Partnerbedingungen beachten, keine erfundenen Preise.
2. Händler-Werkzeug für verwaltete eigene Angebote, später eigenes B2B-Abo,
   nur bei nachvollziehbarem Nutzen, getrennt von neutraler Produktsuche.
3. Klar gekennzeichnete Werbe-/Sponsoring-Plätze ohne Einfluss auf organische
   Reihenfolge, Warnsignale oder Deal-Bewertungen.
4. Optional: einmaliger professioneller Gebrauchtpreis-Report (nur mit
   ausreichenden rechtmäßig erhobenen Vergleichsdaten und Qualitätsprüfung).

Keine Werbung als organische Empfehlung tarnen; keine bezahlten Bevorzugungen
in der neutralen Schnäppchen-Sortierung.

## Technische Umsetzung: stufenweise, erst auf separatem Branch
0. Abhängigkeiten nachweisen: sichere Konten/Authentifizierung, rechtmäßig
   nutzbare echte Angebotsquellen, autorisierte Hintergrundjobs, Kostenbremse.
1. Feature-Flag `PREMIUM_ENABLED=false` als sichere Grundeinstellung. Eine
   Anzeigenansicht nur als `Geplant`/Test, keine Kauf-Schaltfläche bei fehlender
   Zahlungsintegration.
2. Server-seitige Freigaben: `free` / `premium`, Status, Ablaufzeit,
   Zahlungsereignis-/Transaktions-ID, begrenzte Zugriffe; niemals lokal im
   Browser gespeicherter `premium=true` als Berechtigungsnachweis.
3. Zahlungsanbieter ausschließlich in Sandbox/Testmodus. Webhooks per
   Anbieter-Signatur validieren, replay- und duplikatfest; keinerlei
   Kartendaten selbst speichern. Nach Kauf, Kündigung, Erstattung und Ausfall
   Rechte stets korrekt und datensparsam verwalten.
4. Klare Preis-, Laufzeit-, Widerrufs-, Rechnungs- und Kündigungsinformation.
   Gesetzliche Kündigungs- und ggf. Widerrufsmöglichkeit im Web prüfen;
   Rechtstexte und Unternehmens-/Steuerfragen vor Produktivbetrieb prüfen.
5. Echte Preisquellen anschließen und nach Nutzungsrecht, Aktualität und
   Quotenlimits überprüfen. Erst danach Hintergrundsuche, Push-Opt-in,
   KI-Scout und Benachrichtigungs-Qualität messen.
6. Beta mit freiwilligen Testnutzern, Kennzahlen: Premium-Konversion,
   Kündigungsrate, Erlös pro aktivem Nutzer, Deckungsbeitrag pro Abo,
   Fehler/Fehlalarme; danach über öffentliche Freischaltung entscheiden.

## Mindest-Abnahmekriterien
- Bestehende kostenlose Funktionen und Tests unverändert erfolgreich.
- Ohne aktivierte Freigabe keine zahlungspflichtigen Vorgänge, keine echten
  E-Mails/Push- oder externen Angebotsabrufe.
- Unberechtigte Nutzer können Premium-APIs nicht aufrufen; kein Zugang über
  gefälschte Browserflags, abgelaufene oder zurückgebuchte Abos.
- Webhook-Duplikat, ungültige Signatur, API-Ausfall und mehrfacher Login
  getestet; Rechte werden korrekt deaktiviert.
- Nachgewiesene Datenquelle und Einwilligung, Rate-Limits und Quoten für
  Benachrichtigungen; keine versteckten Folgekosten.
- Kündigung/Widerruf, Nutzerrechte und Kosten vor Livegang juristisch und
  technisch abgenommen.

## Beispielrechnung (keine Prognose)
3.000 durchschnittlich monatlich aktive Nutzer x 5 % Premium x 4,99 EUR
x 12 Monate = **8.982 EUR jährlicher Abo-Bruttoumsatz** vor Steuerabzug,
Gebühren, Erstattungen, Betriebskosten und Nutzerabgängen.
Das setzt einen stabilen Durchschnitt von 150 zahlenden Abonnenten voraus.

## Nicht erledigt
Dieses Dokument ist eine Architektur- und Produktskizze. Auth, Payments,
Benachrichtigungen, Livequellen, Premium-Endpunkte und Vertragstexte wurden
damit **nicht** implementiert, getestet oder freigegeben. Kein Merge
oder Deployment ohne unabhängige Prüfung.
