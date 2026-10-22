# Eigene echte Angebote in SCHNAPPER

Solange keine offizielle Schnittstelle (z. B. eBay) freigegeben ist, ist das der **erlaubte Weg zu echten Angeboten**: Du trägst Angebote, die du selbst gefunden hast, in eine Liste ein und lädst sie in SCHNAPPER. Die App prüft Preise, entfernt Doppelte, warnt vor Verdächtigem und sortiert nach Ersparnis.

## 1. Vorlage nehmen
`app/vorlagen/meine-angebote.csv` enthält nur die Spaltenüberschriften. Am Handy geht es am einfachsten mit **Google Tabellen**: neue Tabelle anlegen, die Überschriften aus der Vorlage in Zeile 1 schreiben, Angebote darunter eintragen, dann *Datei → Herunterladen → CSV*.

## 2. Spalten

| Spalte | Pflicht | Beispiel | Hinweis |
| --- | --- | --- | --- |
| `id` | ja | `1` | Jede Zeile eine andere Nummer |
| `titel` | ja | `Kopfhörer Over-Ear kabellos` | In eigenen Worten, kurz |
| `preis` | ja | `49,99` | Ohne Versand, Komma oder Punkt egal |
| `versand` | nein | `4,90` | Leer = kostenlos |
| `referenzpreis` | nein | `129,00` | Üblicher Preis (z. B. Neupreis). Ohne ihn zeigt SCHNAPPER keine Ersparnis an |
| `zustand` | nein | `gebraucht` | `neu`, `wie_neu`, `gebraucht`, `defekt` |
| `quelle` | ja | `eigene` | **Immer `eigene`**. Andere Werte werden abgewiesen |
| `kategorie` | nein | `audio` | Frei wählbar |
| `url` | ja | `https://…` | Link zum Angebot, muss mit `https://` beginnen |
| `erfasst_am` | ja | `2026-10-22T10:00:00Z` | Wann du den Preis gesehen hast. Älter als 24 Std. → Hinweis „Preis evtl. veraltet“ |

## 3. Laden
In der SCHNAPPER-Oberfläche oben rechts **„Eigene Liste“** antippen und die CSV wählen. Fehlerhafte Zeilen werden unter „Hinweise zur Liste“ mit Grund angezeigt, der Rest wird trotzdem geladen. Die Liste bleibt nur im Arbeitsspeicher; beim Neustart ist sie weg, deine Datei bleibt natürlich erhalten.

## Was erlaubt ist
- Angebote, die du selbst angesehen und notiert hast, mit Link zur Originalseite.
- **Nicht** erlaubt: Inhalte automatisiert von Plattformen kopieren (Scraping). Kleinanzeigen verbietet das ausdrücklich; die App weist diese Quelle ab.
