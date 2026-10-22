# SCHNAPPER am Android-Handy starten (ohne PC)

> Stand 22.10.2026 (F5): Ablauf und Startskript am Computer geprüft, **auf einem echten Android-Gerät noch nicht getestet** (auf echtem Gerät ungetestet). Bitte melden, wenn ein Schritt hakt.

SCHNAPPER braucht nur Python, keine weiteren Pakete und kein Internet im Betrieb. Auf Android bekommst du Python über die App **Termux**.

1. **Termux installieren** aus F-Droid (f-droid.org). Die Version im Play Store ist veraltet.
2. In Termux eintippen:
   ```
   pkg update && pkg install python unzip
   termux-setup-storage
   ```
   Beim zweiten Befehl den Speicherzugriff erlauben.
3. **Code herunterladen:** Im Browser auf github.com, angemeldet, das Repo `jefrey030/Schnapper` öffnen → *Code* → *Download ZIP*. Die Datei landet unter *Downloads*.
4. In Termux entpacken und mit **einem Befehl** starten:
   ```
   cd ~ && unzip -o ~/storage/downloads/Schnapper-main.zip && cd ~/Schnapper-main
   bash start-schnapper.sh
   ```
   (Heißt der entpackte Ordner anders, in diesen Ordner wechseln.) Es erscheinen
   `SCHNAPPER startet: http://127.0.0.1:8765 …` und `SCHNAPPER läuft: http://127.0.0.1:8765`.
   Termux geöffnet lassen. Das Skript prüft vorher, ob Python da ist (sonst Hinweis
   `pkg install python`), und lädt nichts herunter.
   - `bash start-schnapper.sh` ist der Hauptweg, weil beim ZIP-Download das
     Ausführungsrecht verloren gehen kann. Wer `./start-schnapper.sh` nutzen möchte,
     setzt es einmal mit `chmod +x start-schnapper.sh`.
   - **Eigene Datei:** `bash start-schnapper.sh app/beispiele/angebote.csv`
     (ohne Angabe wird `app/vorlagen/meine-angebote.csv` genommen).
   - **Anderer Port:** `SCHNAPPER_PORT=8800 bash start-schnapper.sh`, dann in Chrome
     `http://127.0.0.1:8800` öffnen.
   - **Beenden:** Strg+C, in Termux über die Tastenleiste **CTRL** und dann **C**.
   - Die Seite ist immer nur auf diesem Handy erreichbar (fest `127.0.0.1`).

   **Alternative ohne Skript:**
   ```
   PYTHONPATH=app python -m schnapper.web app/beispiele/angebote.csv
   ```
5. In **Chrome** `http://127.0.0.1:8765` öffnen.
6. **Auf den Startbildschirm:** Chrome-Menü (⋮) → *App installieren* bzw. *Zum Startbildschirm hinzufügen*. Danach startet SCHNAPPER wie eine App, mit eigenem Symbol und ohne Adressleiste.

Für deine eigene Liste `app/vorlagen/meine-angebote.csv` verwenden (Standard des Startskripts) und dann in der App „Eigene Liste“ laden (siehe `docs/EIGENE-ANGEBOTE.md`).

## Grenzen
- Die App läuft nur, solange Termux läuft. Wird Termux beendet, zeigt die Seite „Server nicht erreichbar“.
- Sie ist nur auf diesem Handy erreichbar. Eine Version im Internet (ohne eigenes Gerät) wäre eine Veröffentlichung und braucht deine Freigabe (siehe Masterplan).

## Wichtiger Hinweis zu PR #15 (noch kein Release)
Die neue Barcode-Suche und die aktuelle Team-Vorbereitung liegen derzeit **nur**
im Entwicklungsbranch `integration/schnapper-gesamtstand-20261022` (PR #15).
Der obige Download von `main` enthält diese neuen Funktionen noch nicht.

Zum Testen erst im privaten GitHub-Repository auf den Branch
`integration/schnapper-gesamtstand-20261022` umschalten und dort `Code → Download ZIP` wählen.
Anschließend im Termux-Download-Verzeichnis die **tatsächliche ZIP-Datei**
entpacken und in ihren Ordner wechseln (Name unterscheidet sich vom `main`-Archiv).
Danach SCHNAPPER wie in Schritt 4 starten. Die Barcode-Suche bleibt ohne
`SCHNAPPER_OPENPRICES_FREIGABE=ja` ausdrücklich **aus**.

**Kein bewiesener Handytest:** Der beschriebene Ablauf ist vorbereitet, aber
auf dem echten Android-Gerät noch nicht ausgeführt. Ohne Internetverbindung
können auch nach Freigabe keine Live-Preise geladen werden.
