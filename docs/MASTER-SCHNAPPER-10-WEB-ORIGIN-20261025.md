# SCHNAPPER – GROSSMASTER 10: Lokale Web-Suche gegen fremde Hosts und Ursprünge absichern

**Datum:** 25.10.2026 · **Priorität:** P0 für lokalen Datenschutz und unerwünschte Import-/Barcode-Befehle.  
**Basis:** GitHub `main` (App-Kern), damit alle offenen Vier-KI-Integrations-Drafts unberührt bleiben.  
**Änderungsbranch:** `fix/schnapper-local-web-origin-master10-20261025`.  
**Budget:** 0 € · **Produktivfreigabe:** NO-GO / Review erforderlich.

## 1. Master-Auftrag: unabhängige Bestandskontrolle

Der App-Kern mit Dateiimport, Suche, MockAdapter S-005/T3, Quellen-Register und Preisalarm ist bereits auf `main` vorhanden. Deshalb **kein** zweiter MockAdapter und keine fingierte Schnäppchen-Quelle.

Neue konkrete Schwachstelle: `app/schnapper/web.py` überprüfte bei GET/POST bislang nicht, ob der übertragene Hostname eine lokal zulässige Adresse ist. Bei schreibenden POST-Anfragen war lediglich der vorhersehbare Header `X-Schnapper: 1` erforderlich. Dieser Header ist **keine Authentisierung**, und eine bösartige Web-Origin oder DNS-Rebinding-ähnliche Hostname-Konstellation muss ausdrücklich abgewehrt werden. Bei `--host 0.0.0.0` ist die Anwendung bewusst aus dem WLAN erreichbar, aber ohne Benutzeranmeldung; kein Internet-Deployment zulässig.

## 2. LEAD: Umfang und Grenzen

- Die normalen Such-/Import-/Barcode-APIs, Speicherung ausschließlich auf Nutzergerät und Offline-Nutzung erhalten.
- Keine neuen Konten, API-Schlüssel, Cookies, externe Dienste, Zahlungssysteme, Cloud-Migration oder Modellaufrufe.
- Lokale Hostnames `localhost`/Loopback zulassen; bei `--host 0.0.0.0` zusätzlich private IP-Literale aus dem eigenen Netz. **Fremde DNS-Hostnamen** nicht als lokale Web-App akzeptieren.
- Beim POST einen übermittelten `Origin` mit dem erlaubten Host und exakten Port vergleichen. Ein fehlender Origin-Header ist nur zusammen mit dem schon vorhandenen `X-Schnapper`-Gate bei lokalen Skripten erlaubt.
- Harte Grenzen: Authentisierung ist damit **nicht** eingeführt; alle anderen Teilnehmer eines gemeinsam genutzten WLAN können die ungeschützte Anwendung eventuell weiterhin erreichen. `0.0.0.0` nur im vertrauenswürdigen Heimnetz.

## 3. BRAIN: Tatsächlich auf separatem Branch geänderter Code

- `app/schnapper/web.py`: Hilfsfunktion `_lokaler_host(host_header, bind_host, port)` prüft syntaktisch Hostheader, Port und konkrete IP-Adressen. DNS-Namen außer `localhost` werden abgelehnt. Netzwerkbindung kontrolliert erlaubte private IP-Literale.
- `_origin_erlaubt(origin, hostname, port)` prüft nur gleiche HTTP-Origin, exakt gleiche Adresse und Port, lehnt `Origin: null`, Fremd-Origin und URL-Pfade ab.
- `do_GET` (damit auch `HEAD`) verweigert unzulässige Host-Header vor der Suche.
- `do_POST` verweigert unzulässigen Host oder Origin **vor** Import/Barcode-Verarbeitung. Der bestehende `X-Schnapper`-Schutz bleibt bestehen; kein Wegfall alter Sperren.

## 4. CHECK: Konkrete Testpflichten

Neue Datei `tests/test_web_host_origin.py`:
1. Lokale Host-/Port-Kombinationen müssen zulässig sein; falscher Port blockiert.
2. Fremde DNS-Hostnames und Host-Manipulationen werden abgelehnt.
3. Private WLAN-IP nur bei absichtlich breiter Bindung.
4. Fremde/null-/HTTPS-Origin abweisen, gleiche HTTP-Origin zulassen.
5. Echter HTTP-GET über ein temporäres `127.0.0.1`-Socket: Suche bleibt verfügbar.
6. Echter HTTP-GET mit Host `evil.example`: HTTP 403, keine Angebotsliste.
7. Echter HTTP-POST von fremder Origin: HTTP 403, keine Importaktion.
8. Echter HTTP-POST von korrekter Origin: bestehende Fachvalidierung greift (leere Liste 422).
9. Gesamte Python-Test-Suite für finalen PR-SHA und getrennte Cloudflare-Offline-Tests nachweisen.
10. Alle Tests bleiben offline außer **lokaler Loopback-Socket**. Keine tatsächliche Fremd-IP-Verbindung, kein Scraping, kein Ollama.

## 5. COMMAND: Abnahmeentscheidung

- Vor Auswertung des exakten GitHub-CI-Testlaufs keine Test-Erfolgsmeldung.
- Log-Nachweise zu Python PASS/FAIL/SKIP und Node PASS/FAIL/SKIP, Job-IDs und Commit-SHA festhalten.
- Keine als unabhängig attestierte Live-Sicherheitsfreigabe behaupten. Insbesondere bildet ein `Origin`-Header **keine Zugangskontrolle** gegen absichtlich handelnde lokale Clients.
- Separate Reviewer soll rückwärtskompatible LAN-Nutzung, Host-/Port-Gates, vorhandene API-Aufrufe, HTTP-Head und Konflikte mit anderen App-PRs prüfen.
- Kein Merge, Deployment oder Öffnen nach außen ohne ausdrückliche Betreiberfreigabe.

## 6. Unveränderliche Projektregeln

Budget 0 €, keine kostenpflichtigen APIs oder Hosting-Tarife, keine Secrets, keine Änderungen produktiver Daten, keine Änderung Repository-Sichtbarkeit, keine direkte Änderung an `main`, keine Veröffentlichung, keine Branch-Löschung, keine automatische Replit-Übernahme behaupten.

**Nächster kleinster sicherer Schritt:** CI für diese PR-SHA auswerten, bei Problemen auf demselben isolierten Branch korrigieren, danach unabhängige Prüfung. Web-App weiter nur lokal starten.
