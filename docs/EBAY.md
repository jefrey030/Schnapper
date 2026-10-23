# eBay-Anbindung (S-013) – vorbereitet, standardmäßig gesperrt

Stand 23.10.2026, Inhalte bei eBay prüfen.

## Was der Adapter tut – und was nicht

- `app/schnapper/ebay.py` kann Angebote über die offizielle **eBay Browse API** suchen
  (Marktplatz eBay.de, Preise in Euro, Lieferung nach Deutschland).
- **Standard ist die Sandbox**: eine Testumgebung von eBay mit erfundenen Testdaten.
  Solche Angebote bekommen in SCHNAPPER immer das Präfix `SANDBOX ` im Titel.
- **Produktion** (echte eBay-Angebote) nutzt der Adapter nur mit dem Schalter
  `SCHNAPPER_EBAY_PRODUKTION=ja` **und** nur, wenn eBay die Nutzung genehmigt hat.
- Der Adapter schreibt nichts auf die Platte. Zugangsdaten und Token liegen nur im Arbeitsspeicher.
- Es gibt kein Scraping. Erlaubt sind nur `api.ebay.com` und `api.sandbox.ebay.com` über HTTPS,
  Weiterleitungen werden nicht verfolgt.
- Noch keine Anbindung an Kommandozeile oder Weboberfläche (Folgepunkt).

**Quelle bleibt gesperrt, solange Schalter oder Schlüssel fehlen.**

## Schritt für Schritt: Sandbox-Zugang

1. Auf <https://developer.ebay.com> ein kostenloses Entwicklerkonto anlegen („Join“),
   die E-Mail bestätigen. Die Freischaltung kann bis zu einem Werktag dauern.
2. Im Entwicklerportal **Application Keys** öffnen, beim Bereich **Sandbox** ein Keyset erzeugen.
   - **App ID** = Client ID
   - **Cert ID** = Client Secret
3. Optional: einen Sandbox-Testnutzer anlegen (für die Suche nicht nötig).

## Schlüssel setzen – nur als Umgebungsvariablen

Beispiel für Termux, gilt nur für die aktuelle Sitzung (Platzhalter durch die eigenen Werte ersetzen):

```sh
export SCHNAPPER_EBAY_CLIENT_ID=<deine-App-ID>
export SCHNAPPER_EBAY_CLIENT_SECRET=<deine-Cert-ID>
export SCHNAPPER_EBAY_FREIGABE=ja
```

> **Warnung:**
> - Schlüssel **nie** in Dateien des Repos, in Issues/PRs oder in Chats posten.
> - Keine `.bashrc` oder andere Datei mit Schlüsseln einchecken.
> - Ist ein Schlüssel doch einmal sichtbar geworden: im Entwicklerportal sofort neu erzeugen.

## Produktion (echte Angebote)

- `SCHNAPPER_EBAY_PRODUKTION=ja` setzen und das **Produktions-Keyset** verwenden.
- Die Nutzung der Buy/Browse API in Produktion ist bei eBay eingeschränkt und braucht eine
  **Genehmigung bzw. Vereinbarung mit eBay** (Application Growth Check / Buy-API-Zugang).
- Tageslimit standardmäßig 5 000 Aufrufe.
- Kosten 0 €, aber Genehmigung nötig. Die Entscheidung trifft Jefrey.

## Variablen

| Variable | Bedeutung | Standard |
| --- | --- | --- |
| `SCHNAPPER_EBAY_FREIGABE` | `ja` erlaubt Abrufe überhaupt | fehlt → gesperrt |
| `SCHNAPPER_EBAY_CLIENT_ID` | App ID aus dem Keyset | fehlt → gesperrt |
| `SCHNAPPER_EBAY_CLIENT_SECRET` | Cert ID aus dem Keyset | fehlt → gesperrt |
| `SCHNAPPER_EBAY_PRODUKTION` | genau `ja` → Produktion, sonst Sandbox | Sandbox |

## Typische Fehlermeldungen

| Meldung | Ursache |
| --- | --- |
| `Freigabeschalter SCHNAPPER_EBAY_FREIGABE=ja fehlt` | Schalter nicht gesetzt |
| `Zugangsdaten fehlen: SCHNAPPER_EBAY_CLIENT_ID …` | Variable fehlt oder ist leer |
| `Quelle 'ebay' ausgeschlossen …` | Im Quellen-Register ausgeschlossen, Schalter hilft nicht |
| `eBay HTTP 401 … Zugangsdaten ungültig oder falscher Modus (Sandbox/Produktion)?` | Falsche Schlüssel oder Sandbox-Schlüssel in Produktion (bzw. umgekehrt) |
| `eBay HTTP 429 …` | Tageslimit erreicht |
| `eBay nicht erreichbar: …` | Kein Netz, Zeitüberschreitung (15 s) |
| `eBay-Antwort zu groß` / `kein gültiges JSON` | Unerwartete Antwort von eBay |

Meldungen enthalten nie Client ID, Secret oder Token.

## Quellen (developer.ebay.com)

- Browse API, Überblick: <https://developer.ebay.com/api-docs/buy/browse/overview.html>
- OAuth Client-Credentials: <https://developer.ebay.com/api-docs/static/oauth-client-credentials-grant.html>
- API-Limits: <https://developer.ebay.com/develop/get-started/api-call-limits>
