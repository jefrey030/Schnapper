"use strict";
// Alle Inhalte werden per textContent eingesetzt (nie innerHTML), damit Titel aus
// fremden Listen keinen Code einschleusen können.
const $ = (id) => document.getElementById(id);
const euro = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
const ZUSTAND = { neu: "neu", wie_neu: "wie neu", gebraucht: "gebraucht", defekt: "defekt", unbekannt: "Zustand unbekannt" };
let timer = null;
let anfrageNr = 0;

function query() {
  const p = new URLSearchParams();
  for (const [k, v] of new FormData($("filter"))) if (String(v).trim()) p.set(k, String(v).trim());
  return p.toString();
}

function warnText(w) {
  if (w.startsWith("veraltet")) return { text: "Preis evtl. veraltet", gefahr: false, titel: w };
  if (w.startsWith("betrugsverdacht")) return { text: "Vorsicht: zu billig für Neuware", gefahr: true, titel: w };
  if (w.startsWith("kein Referenzpreis")) return { text: "Ersparnis unbekannt", gefahr: false, titel: w };
  if (w.startsWith("teurer")) return { text: "Teurer als üblich", gefahr: true, titel: w };
  return { text: w, gefahr: false, titel: w };
}

function karte(t) {
  const el = $("karte").content.firstElementChild.cloneNode(true);
  const r = el.querySelector(".rabatt");
  if (t.rabatt_prozent !== null) {
    r.textContent = Number(t.rabatt_prozent) >= 0 ? `−${Number(t.rabatt_prozent).toLocaleString("de-DE")} %` : "teurer";
  } else { r.textContent = "ohne Vergleich"; r.classList.add("ohne"); }
  el.querySelector(".preis").textContent = euro.format(Number(t.gesamtpreis));
  el.querySelector(".titel").textContent = t.titel;
  const teile = [ZUSTAND[t.zustand] || t.zustand, t.quelle];
  if (Number(t.versand) > 0) teile.push(`inkl. ${euro.format(Number(t.versand))} Versand`);
  if (t.referenzpreis) teile.push(`sonst ${euro.format(Number(t.referenzpreis))}`);
  el.querySelector(".details").textContent = teile.join(" · ");
  const ul = el.querySelector(".warnungen");
  for (const w of t.warnungen) {
    const info = warnText(w);
    const li = document.createElement("li");
    li.textContent = info.text; li.title = info.titel;
    if (info.gefahr) li.className = "gefahr";
    ul.appendChild(li);
  }
  const a = el.querySelector(".link");
  if (/^https:\/\//.test(t.url)) a.href = t.url; else a.remove();
  return el;
}

function probleme(daten) {
  const liste = [...daten.ungueltig.map((f) => "Ungültig – " + f),
                 ...daten.dubletten.map((d) => `Doppelt entfernt: „${d.titel}“`)];
  $("probleme").hidden = liste.length === 0;
  $("probleme-titel").textContent = `${liste.length} Hinweis${liste.length === 1 ? "" : "e"} zur Liste anzeigen`;
  $("probleme-liste").replaceChildren(...liste.map((txt) => { const li = document.createElement("li"); li.textContent = txt; return li; }));
}

async function suchen() {
  const nr = ++anfrageNr;
  try {
    const antwort = await fetch("/api/suche?" + query());
    const daten = await antwort.json();
    if (nr !== anfrageNr) return; // veraltete Antwort ignorieren
    if (!antwort.ok) { $("status").textContent = daten.fehler || "Fehler bei der Suche"; return; }
    $("beispiel").hidden = !daten.beispieldaten;
    $("treffer").replaceChildren(...daten.treffer.map(karte));
    $("leer").hidden = daten.treffer.length > 0;
    $("leer").textContent = daten.eingelesen === 0
      ? "Noch keine Angebote geladen. Tippe oben rechts auf „Eigene Liste“ und wähle deine CSV- oder JSON-Datei."
      : "Keine Treffer. Lockere die Filter oder suche nach etwas anderem.";
    $("status").textContent = `${daten.treffer.length} Treffer aus ${daten.eingelesen} Angeboten · Liste: ${daten.liste}`;
    probleme(daten);
  } catch {
    if (nr === anfrageNr) $("status").textContent = "Server nicht erreichbar. Läuft SCHNAPPER noch?";
  }
}

function spaeter() { clearTimeout(timer); timer = setTimeout(suchen, 250); }

async function hochladen(ev) {
  const datei = ev.target.files[0];
  ev.target.value = "";
  if (!datei) return;
  if (datei.size > 5 * 1024 * 1024) { $("status").textContent = "Datei ist größer als 5 MB."; return; }
  $("status").textContent = "Lade Liste …";
  try {
    const antwort = await fetch("/api/import", {
      method: "POST", body: datei,
      headers: { "X-Schnapper": "1", "X-Dateiname": datei.name, "Content-Type": "application/octet-stream" },
    });
    const daten = await antwort.json();
    if (!antwort.ok) {
      $("status").textContent = daten.fehler || "Liste konnte nicht geladen werden.";
      if (daten.ungueltig) probleme({ ungueltig: daten.ungueltig, dubletten: [] });
      return;
    }
    await suchen();
  } catch { $("status").textContent = "Hochladen fehlgeschlagen."; }
}

document.addEventListener("DOMContentLoaded", () => {
  $("filter").addEventListener("input", spaeter);
  $("filter").addEventListener("submit", (e) => { e.preventDefault(); suchen(); });
  $("datei").addEventListener("change", hochladen);
  suchen();
});
