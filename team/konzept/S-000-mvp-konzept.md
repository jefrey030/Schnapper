# S-000 – Konzept: erste SCHNAPPER-Suche nach günstigen Gebrauchtartikeln

Stand: 21.10.2026 · Autor: SCHNAPPER MASTER · Status: zur Prüfung (review)

> Dieses Dokument ist ein **Konzept**. Es existiert **keine** Anbindung an eBay,
> Kleinanzeigen oder andere Marktplätze. Alle Beispielwerte unten sind
> erkennbar erfundene Testdaten (`TEST-…`) und keine echten Preise.

## LEAD – 3 priorisierte MVP-Funktionen

1. **Suchanfrage erfassen und normalisieren** – Suchbegriff, Höchstpreis, Zustand, PLZ/Umkreis.
   Begründung: Ohne eindeutige, validierte Eingabe kann keine spätere Stufe sinnvoll arbeiten;
   die Funktion ist ohne externe Daten vollständig testbar.
2. **Inserate aus einer Quelle über eine Schnittstelle einlesen (zunächst Mock)** –
   ein einheitliches Inserat-Schema, befüllt von einem austauschbaren Quellen-Adapter.
   Begründung: Entkoppelt die App von noch fehlenden Zugangsdaten; eine echte Quelle kann
   später ohne Umbau angebunden werden, sobald Nutzungsrechte geklärt sind.
3. **Treffer filtern, entdoppeln und nach Preis sortieren** – inkl. Kennzeichnung veralteter Preise.
   Begründung: Das ist der eigentliche Nutzen („Schnäppchen finden“) und deckt die drei
   wichtigsten Fehlerquellen (veraltet, doppelt, unzulässige Quelle) direkt ab.

Bewusst **nicht** im MVP: Benachrichtigungen, Preisverlauf, Konto/Login, mehrere Quellen parallel.

## BRAIN – Eingabe-Ausgabe-Ablauf

```
Eingabe: Suchanfrage {begriff, max_preis_cent, zustand?, plz?, umkreis_km?}
   │
   ▼ 1. validieren/normalisieren (Kleinschreibung, Leerzeichen, Betrag in Cent ≥ 0)
   ▼ 2. Quellen-Adapter.suche(anfrage)  → Liste roher Inserate   (MVP: Mock mit Testdaten)
   ▼ 3. auf Inserat-Schema abbilden; ungültige Datensätze verwerfen + protokollieren
   ▼ 4. Quelle ohne geklärte Nutzungsrechte → komplett verwerfen (Blocker melden)
   ▼ 5. Duplikate entfernen (gleiche quelle+quell_id oder gleiche normierte URL)
   ▼ 6. veraltete Preise markieren (abgerufen_am älter als 24 h ⇒ veraltet = true)
   ▼ 7. filtern (preis_cent ≤ max_preis_cent) und aufsteigend nach preis_cent sortieren
Ausgabe: Trefferliste [Inserat] + Hinweise [{art, text}]
```

## BRAIN – minimales Datenfeld-Schema für ein Inserat

| Feld | Typ | Pflicht | Bedeutung |
| --- | --- | --- | --- |
| `quelle` | Text | ja | Kennung des Adapters, z. B. `mock` |
| `quell_id` | Text | ja | ID des Inserats innerhalb der Quelle |
| `titel` | Text | ja | Inseratstitel |
| `preis_cent` | Ganzzahl ≥ 0 | ja | Preis in Cent (keine Gleitkommazahlen) |
| `waehrung` | Text (ISO 4217) | ja | MVP: nur `EUR` |
| `zustand` | Text | nein | `neu`, `gebraucht`, `defekt`, `unbekannt` |
| `url` | Text | ja | Link zum Originalinserat |
| `abgerufen_am` | Zeitstempel (UTC, ISO 8601) | ja | Zeitpunkt des Abrufs – Basis für „veraltet“ |
| `nutzungsrecht_geklaert` | Wahrheitswert | ja | nur `true` darf angezeigt werden |

Beispiel (Testdaten): `{"quelle":"mock","quell_id":"TEST-1","titel":"TEST Fahrrad","preis_cent":5000,"waehrung":"EUR","url":"https://example.invalid/TEST-1","abgerufen_am":"2026-10-21T08:00:00Z","nutzungsrecht_geklaert":true}`

## CHECK – Fehlerszenarien mit passendem Test

| # | Fehlerszenario | Risiko | Passender Test (Gegeben / Wenn / Dann) |
| --- | --- | --- | --- |
| F1 | **veralteter Preis** | Nutzer sieht Preis, der nicht mehr gilt | Gegeben ein Inserat mit `abgerufen_am` = jetzt − 25 h / Wenn die Suche läuft / Dann ist `veraltet = true` und ein Hinweis „Preis ggf. veraltet“ wird ausgegeben; bei jetzt − 1 h ist `veraltet = false`. |
| F2 | **doppeltes Inserat** | Treffer erscheint mehrfach, Ranking verfälscht | Gegeben zwei Inserate mit gleicher `quelle`+`quell_id` (bzw. gleicher URL bis auf Groß-/Kleinschreibung und abschließenden `/`) / Wenn entdoppelt wird / Dann bleibt genau eines übrig. |
| F3 | **fehlende Nutzungsrechte** | rechtlich unzulässige Anzeige fremder Daten | Gegeben ein Inserat mit `nutzungsrecht_geklaert = false` / Wenn die Suche läuft / Dann erscheint es nicht in der Trefferliste und ein Hinweis der Art `blocker` wird ausgegeben. |
| F4 | ungültiger Preis | Absturz oder falsche Sortierung | Gegeben `preis_cent = -1` oder `"50,00"` / Wenn abgebildet wird / Dann wird der Datensatz verworfen und protokolliert, die übrigen Treffer bleiben erhalten. |

Diese Tests werden zusammen mit dem Code der MVP-Funktionen geschrieben (nächste Aufgabe);
in S-000 wird bewusst **kein App-Code** geändert.

## COMMAND – Ergebnis

- **Fertig:** Konzept für S-000 liegt vor (3 MVP-Funktionen, Ablauf, Schema, 4 Fehlerszenarien mit Tests).
- **Nicht fertig:** keine Implementierung, keine echte Datenquelle, Nutzungsrechte für Marktplätze ungeklärt.
- **Belege:** LEAD-Abschnitt (Funktionen 1–3), BRAIN-Abschnitte (Ablauf Schritte 1–7, Schema mit 9 Feldern),
  CHECK-Tabelle (F1–F4); maschinelle Strukturprüfung in `tests/test_konzept_s000.py`.
- **Nächster Schritt:** MVP-Funktion 1 + Inserat-Schema als reines Python-Modul mit Mock-Adapter
  und den Tests F1–F4 umsetzen (ohne Netzwerkzugriff).
