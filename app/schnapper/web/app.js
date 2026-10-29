"use strict";
// Alle Inhalte werden per textContent eingesetzt (nie innerHTML), damit Titel aus
// fremden Listen keinen Code einschleusen können.
const $ = (id) => document.getElementById(id);
const euro = new Intl.NumberFormat("de-DE", { style: "currency", currency: "EUR" });
const ZUSTAND = { neu: "neu", wie_neu: "wie neu", gebraucht: "gebraucht", defekt: "defekt", unbekannt: "Zustand unbekannt" };
const MAX_MERK = 200;
const MAX_ALARME = 50;
let timer = null;
let anfrageNr = 0;
// Generationszähler für Barcode-Abfragen: nur die zuletzt gestartete darf Anzeige und Knopf ändern
// (Handsuche und Kamera-Treffer können sich überholen).
let barcodeAbfrage = 0;

// ---------- Speicher (nur auf diesem Gerät) ----------
// localStorage kann fehlen oder Fehler werfen (privates Fenster, gesperrte Website-Daten).
// Dann läuft alles im Arbeitsspeicher weiter und ein Hinweis erscheint.
const speicher = {
  ersatz: {},
  lesen(name, standard) {
    try {
      const roh = window.localStorage.getItem("schnapper." + name);
      if (roh !== null) return JSON.parse(roh);
    } catch { /* weiter mit Ersatz */ }
    return name in this.ersatz ? this.ersatz[name] : standard;
  },
  schreiben(name, wert) {
    this.ersatz[name] = wert;
    try { window.localStorage.setItem("schnapper." + name, JSON.stringify(wert)); }
    catch { $("speicher-hinweis").hidden = false; }
  },
};

function merkliste() {
  const m = speicher.lesen("merkliste", {});
  return m && typeof m === "object" && !Array.isArray(m) ? m : {};
}
function alarme() {
  const a = speicher.lesen("alarme", []);
  return Array.isArray(a) ? a : [];
}
function el(tag, text, klasse) {
  const e = document.createElement(tag);
  if (text !== undefined) e.textContent = text;
  if (klasse) e.className = klasse;
  return e;
}
function zahl(x) { return Number(x).toLocaleString("de-DE"); }

// ---------- Suche ----------
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
  if (w.startsWith("referenzpreis fragwürdig")) return { text: "„Statt“-Preis fragwürdig", gefahr: true, titel: w };
  return { text: w, gefahr: false, titel: w };
}

function merkKnopf(knopf, t) {
  const setzen = () => {
    const an = t.id in merkliste();
    knopf.textContent = an ? "★" : "☆";
    knopf.setAttribute("aria-pressed", String(an));
    knopf.setAttribute("aria-label", an ? "Von der Merkliste nehmen" : "Merken");
    knopf.title = an ? "Gemerkt" : "Merken";
  };
  knopf.addEventListener("click", () => {
    const m = merkliste();
    if (t.id in m) delete m[t.id];
    else {
      if (Object.keys(m).length >= MAX_MERK) { $("status").textContent = `Merkliste ist voll (max. ${MAX_MERK}).`; return; }
      m[t.id] = { titel: t.titel, gesamtpreis: t.gesamtpreis, url: t.url, quelle: t.quelle,
                  zustand: t.zustand, gemerkt_am: new Date().toISOString() };
    }
    speicher.schreiben("merkliste", m);
    setzen();
    zaehler();
  });
  setzen();
}

function karte(t) {
  const e = $("karte").content.firstElementChild.cloneNode(true);
  const r = e.querySelector(".rabatt");
  if (t.rabatt_prozent !== null) {
    r.textContent = Number(t.rabatt_prozent) >= 0 ? `−${zahl(t.rabatt_prozent)} %` : "teurer";
  } else { r.textContent = "ohne Vergleich"; r.classList.add("ohne"); }
  e.querySelector(".preis").textContent = euro.format(Number(t.gesamtpreis));
  e.querySelector(".titel").textContent = t.titel;
  const teile = [ZUSTAND[t.zustand] || t.zustand, t.quelle];
  if (Number(t.versand) > 0) teile.push(`inkl. ${euro.format(Number(t.versand))} Versand`);
  if (t.referenzpreis) teile.push(`sonst ${euro.format(Number(t.referenzpreis))}`);
  e.querySelector(".details").textContent = teile.join(" · ");
  verlaufZeile(e.querySelector(".verlauf"), t);
  const ul = e.querySelector(".warnungen");
  for (const w of t.warnungen) {
    const info = warnText(w);
    const li = el("li", info.text, info.gefahr ? "gefahr" : "");
    li.title = info.titel;
    ul.appendChild(li);
  }
  const a = e.querySelector(".link");
  if (/^https:\/\//.test(t.url)) a.href = t.url; else a.remove();
  merkKnopf(e.querySelector(".merken"), t);
  return e;
}

// Preisverlauf: Tiefstpreis, Spanne der letzten 30 Tage, vorheriger Preis
function verlaufZeile(p, t) {
  const v = t.verlauf;
  if (!v) return;
  const teile = [];
  if (v.ist_tiefstpreis) {
    p.appendChild(el("span", `Tiefstpreis seit ${v.seit_tagen} Tag${v.seit_tagen === 1 ? "" : "en"}`, "tief"));
  }
  if (v.vorher !== null) {
    const diff = Number(t.gesamtpreis) - Number(v.vorher);
    teile.push(`${diff < 0 ? "↓" : "↑"} vorher ${euro.format(Number(v.vorher))}`);
  }
  teile.push(`${euro.format(Number(v.tiefst))}–${euro.format(Number(v.hoechst))} in ${v.seit_tagen} Tagen`);
  p.appendChild(el("span", teile.join(" · ")));
  p.title = `${v.anzahl} Preise beobachtet`;
  p.hidden = false;
}

function probleme(daten) {
  const liste = [...daten.ungueltig.map((f) => "Ungültig – " + f),
                 ...daten.dubletten.map((d) => `Doppelt entfernt: „${d.titel}“`)];
  $("probleme").hidden = liste.length === 0;
  $("probleme-titel").textContent = `${liste.length} Hinweis${liste.length === 1 ? "" : "e"} zur Liste anzeigen`;
  $("probleme-liste").replaceChildren(...liste.map((txt) => el("li", txt)));
}

async function suchen() {
  const nr = ++anfrageNr;
  alarmKnopf();
  try {
    const antwort = await fetch("/api/suche?" + query());
    const daten = await antwort.json();
    if (nr !== anfrageNr) return; // veraltete Antwort ignorieren
    if (!antwort.ok) { $("status").textContent = daten.fehler || "Fehler bei der Suche"; return; }
    // Mock-Angebote bleiben selbst nach dem Import als Testdaten markiert.
    $("beispiel").hidden = !(daten.beispieldaten || daten.enthaelt_testdaten);
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
  zeige("suche");
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
    alarmePruefen();
  } catch { $("status").textContent = "Hochladen fehlgeschlagen."; }
}

async function barcodeSuchen(ev) {
  ev.preventDefault();
  const nr = ++barcodeAbfrage;  // ältere, noch laufende Abfragen verfallen
  const ean = $("barcode").value.trim();
  const status = $("barcode-status");
  const knopf = $("barcode-knopf");
  $("barcode-treffer").replaceChildren();
  $("barcode-lizenz").textContent = "";
  if (!/^[0-9]{8,14}$/.test(ean)) {
    status.textContent = "Bitte einen Barcode mit 8 bis 14 Ziffern eingeben.";
    knopf.disabled = false;  // eine verfallene ältere Abfrage gibt den Knopf nicht mehr frei
    return;
  }
  knopf.disabled = true;
  status.textContent = "Frage Ladenpreise ab …";
  try {
    const antwort = await fetch("/api/openprices", {
      method: "POST",
      headers: { "X-Schnapper": "1", "Content-Type": "application/json" },
      body: JSON.stringify({ ean }),
    });
    if (nr !== barcodeAbfrage) return;
    const daten = await antwort.json();
    if (nr !== barcodeAbfrage) return;
    if (!antwort.ok) {
      status.textContent = daten.fehler || "Ladenpreise konnten nicht abgerufen werden.";
      return;
    }
    // Ladenpreise bleiben getrennt von der eigenen Angebotsliste: nicht merkbar.
    $("barcode-treffer").replaceChildren(...daten.treffer.map((t) => {
      const e = karte(t);
      e.querySelector(".merken")?.remove();
      return e;
    }));
    $("barcode-lizenz").textContent = daten.lizenz || "";
    status.textContent = daten.treffer.length === 0
      ? "Keine passenden gemeldeten Preise gefunden."
      : `${daten.treffer.length} Preise gefunden · ${daten.begrenzung}`;
    if (daten.hinweise.length) status.textContent += ` · ${daten.hinweise.length} Einträge übersprungen`;
  } catch {
    if (nr === barcodeAbfrage) status.textContent = "Server oder Preisquelle nicht erreichbar.";
  } finally {
    if (nr === barcodeAbfrage) knopf.disabled = false;
  }
}

// ---------- Kamera-Scan (S-011) ----------
// Läuft komplett im Browser: Bilder werden weder gespeichert noch hochgeladen.
const KAMERA_FORMATE = ["ean_13", "ean_8", "upc_a"];
const KAMERA_ZEITLIMIT = 20000;
const kamera = { stream: null, timer: null, frist: null, laeuft: false, lauf: 0 };  // lauf: Generationszähler

async function kameraFormate() {
  try {
    if (typeof BarcodeDetector.getSupportedFormats !== "function") return KAMERA_FORMATE;
    const da = await BarcodeDetector.getSupportedFormats();
    return KAMERA_FORMATE.filter((f) => da.includes(f));
  } catch { return []; }
}

async function kameraVerfuegbar() {
  if (!("BarcodeDetector" in window) || !window.isSecureContext) return false;
  if (typeof navigator.mediaDevices?.getUserMedia !== "function") return false;
  return (await kameraFormate()).length > 0;
}

function kameraStoppen(meldung) {
  clearTimeout(kamera.timer);
  clearTimeout(kamera.frist);
  kamera.timer = kamera.frist = null;
  kamera.laeuft = false;
  kamera.lauf++;  // offene Kamera-Anfragen älterer Läufe verfallen
  if (kamera.stream) kamera.stream.getTracks().forEach((t) => t.stop());
  kamera.stream = null;
  $("kamera-bild").srcObject = null;
  $("kamera-bereich").hidden = true;
  const fokusZurueck = document.activeElement === $("kamera-abbrechen");  // nur Fokus vom Abbrechen-Knopf zurückgeben
  $("kamera-abbrechen").hidden = true;
  $("kamera-knopf").disabled = false;
  if (fokusZurueck) $("kamera-knopf").focus();
  if (meldung !== undefined) $("kamera-status").textContent = meldung;
}

function kameraFehler(err) {
  if (err?.name === "NotAllowedError" || err?.name === "SecurityError") return "Kamerazugriff verweigert – Barcode bitte eintippen.";
  if (err?.name === "NotFoundError" || err?.name === "OverconstrainedError") return "Keine Kamera gefunden – Barcode bitte eintippen.";
  return "Kamera konnte nicht gestartet werden – Barcode bitte eintippen.";
}

async function kameraScannen() {
  if (kamera.laeuft) return;
  kamera.laeuft = true;
  $("kamera-knopf").disabled = true;
  $("kamera-abbrechen").hidden = false;  // Abbrechen schon während Berechtigungsdialog/Formatabfrage möglich
  $("kamera-abbrechen").focus();  // deaktivierter Startknopf verliert den Fokus: Tastatur/Screenreader landen auf Abbrechen
  $("kamera-status").textContent = "Kamera wird gestartet …";
  const lauf = ++kamera.lauf;
  let stream;
  try {
    stream = await navigator.mediaDevices.getUserMedia({ video: { facingMode: "environment" }, audio: false });
  } catch (err) {
    if (lauf === kamera.lauf) kameraStoppen(kameraFehler(err));  // veralteter Fehler stört neueren Lauf nicht
    return;
  }
  if (lauf !== kamera.lauf) { stream.getTracks().forEach((t) => t.stop()); return; }  // abgebrochen oder neu gestartet
  kamera.stream = stream;
  const video = $("kamera-bild");
  try {
    const formate = await kameraFormate();
    if (lauf !== kamera.lauf || kamera.stream !== stream) return;  // während der Formatabfrage abgebrochen oder neu gestartet
    const detektor = new BarcodeDetector({ formats: formate });
    video.srcObject = stream;
    $("kamera-bereich").hidden = false;
    await video.play();
    if (kamera.stream !== stream) return;
    $("kamera-status").textContent = "Barcode vor die Kamera halten …";
    kamera.frist = setTimeout(() => kameraStoppen("Kein Barcode erkannt – bitte erneut versuchen oder eintippen."), KAMERA_ZEITLIMIT);
    const runde = async () => {
      if (kamera.stream !== stream) return;
      let codes = [];
      try { codes = await detektor.detect(video); } catch { codes = []; }
      if (kamera.stream !== stream) return;
      const treffer = codes.map((c) => String(c.rawValue || "").trim()).find((c) => /^[0-9]{8,14}$/.test(c));
      if (treffer) {
        $("barcode").value = treffer;
        kameraStoppen(`Barcode erkannt: ${treffer}`);
        $("barcode-form").requestSubmit();
        return;
      }
      kamera.timer = setTimeout(runde, 200);
    };
    runde();
  } catch (err) {
    if (kamera.stream === stream) kameraStoppen(kameraFehler(err));
  }
}

// ---------- Preisalarm ----------
function aktuellerWunsch() {
  const f = new FormData($("filter"));
  const w = { text: String(f.get("text") || "").trim(), max_preis: String(f.get("max_preis") || "").trim(),
              min_rabatt: String(f.get("min_rabatt") || "").trim(), zustand: String(f.get("zustand") || "") };
  return w.text && (w.max_preis || w.min_rabatt) ? w : null;
}

function alarmKnopf() {
  const ok = aktuellerWunsch() !== null;
  $("alarm-anlegen").disabled = !ok;
  $("alarm-tipp").hidden = ok;
}

function wunschText(w, mitText = true) {
  const teile = mitText ? [`„${w.text}“`] : [];
  if (w.max_preis) teile.push(`bis ${w.max_preis} €`);
  if (w.min_rabatt) teile.push(`ab ${w.min_rabatt} % billiger`);
  if (w.zustand) teile.push(ZUSTAND[w.zustand] || w.zustand);
  return teile.join(" · ");
}

async function alarmAnlegen() {
  const w = aktuellerWunsch();
  if (!w) return;
  const liste = alarme();
  if (liste.some((x) => wunschText(x) === wunschText(w))) { $("status").textContent = "Diesen Preisalarm gibt es schon."; return; }
  if (liste.length >= MAX_ALARME) { $("status").textContent = `Höchstens ${MAX_ALARME} Preisalarme.`; return; }
  // Erst beim Server prüfen lassen, ob die Zahlen lesbar sind
  const antwort = await fetch("/api/suche?" + alarmQuery(w)).catch(() => null);
  if (!antwort || !antwort.ok) { $("status").textContent = "Preisalarm nicht angelegt: Eingaben prüfen."; return; }
  liste.push({ ...w, angelegt_am: new Date().toISOString() });
  speicher.schreiben("alarme", liste);
  $("status").textContent = `Preisalarm angelegt: ${wunschText(w)}`;
  alarmePruefen();
}

function alarmQuery(w) {
  const p = new URLSearchParams({ text: w.text, sortierung: "preis", ohne_veraltet: "1" });
  if (w.max_preis) p.set("max_preis", w.max_preis);
  if (w.min_rabatt) p.set("min_rabatt", w.min_rabatt);
  if (w.zustand) p.set("zustand", w.zustand);
  return p.toString();
}

let alarmTreffer = 0;
async function alarmePruefen() {
  const liste = alarme();
  const karten = await Promise.all(liste.map(async (w, i) => {
    const e = $("karte-alarm").content.firstElementChild.cloneNode(true);
    e.querySelector(".titel").textContent = w.text;
    e.querySelector(".details").textContent = wunschText(w, false);
    e.querySelector(".loeschen").addEventListener("click", () => {
      const neu = alarme().filter((_, j) => j !== i);
      speicher.schreiben("alarme", neu);
      alarmePruefen();
    });
    const marke = e.querySelector(".ausgeloest");
    let treffer = [];
    try {
      const antwort = await fetch("/api/suche?" + alarmQuery(w));
      if (antwort.ok) treffer = (await antwort.json()).treffer;
      else marke.textContent = "Eingabe ungültig";
    } catch { marke.textContent = "Server nicht erreichbar"; }
    if (treffer.length) {
      marke.textContent = `⚡ ${treffer.length} Treffer · ab ${euro.format(Number(treffer[0].gesamtpreis))}`;
      e.classList.add("an");
      const ul = e.querySelector(".alarm-treffer");
      for (const t of treffer.slice(0, 3)) {
        const li = el("li");
        const a = el("a", `${euro.format(Number(t.gesamtpreis))} – ${t.titel}`);
        if (/^https:\/\//.test(t.url)) { a.href = t.url; a.target = "_blank"; a.rel = "noopener noreferrer"; }
        li.append(a, el("span", ` · ${t.quelle}`, "leise"));
        ul.appendChild(li);
      }
    } else if (!marke.textContent) marke.textContent = "noch nichts unter der Grenze";
    return { e, an: treffer.length > 0 };
  }));
  karten.sort((x, y) => Number(y.an) - Number(x.an));
  $("alarm-liste").replaceChildren(...karten.map((k) => k.e));
  $("alarm-leer").hidden = liste.length > 0;
  alarmTreffer = karten.filter((k) => k.an).length;
  zaehler();
}

// ---------- Merkliste ----------
async function merklisteZeigen() {
  const m = merkliste();
  const ids = Object.keys(m);
  let aktuell = {};
  try {
    const antwort = await fetch("/api/suche?mit_verdacht=1");
    if (antwort.ok) for (const t of (await antwort.json()).treffer) aktuell[t.id] = t;
  } catch { aktuell = null; }
  const karten = ids.sort((a, b) => (m[b].gemerkt_am || "").localeCompare(m[a].gemerkt_am || "")).map((id) => {
    const alt = m[id];
    const jetzt = aktuell ? aktuell[id] : undefined;
    const e = $("karte").content.firstElementChild.cloneNode(true);
    const r = e.querySelector(".rabatt");
    const preis = Number(jetzt ? jetzt.gesamtpreis : alt.gesamtpreis);
    e.querySelector(".preis").textContent = euro.format(preis);
    e.querySelector(".titel").textContent = alt.titel;
    const details = [ZUSTAND[alt.zustand] || alt.zustand, alt.quelle];
    if (alt.gemerkt_am) details.push("gemerkt am " + new Date(alt.gemerkt_am).toLocaleDateString("de-DE"));
    e.querySelector(".details").textContent = details.filter(Boolean).join(" · ");
    if (aktuell === null) { r.textContent = "Stand unbekannt"; r.classList.add("ohne"); }
    else if (!jetzt) { r.textContent = "nicht mehr in der Liste"; r.classList.add("ohne"); }
    else {
      const diff = Number(jetzt.gesamtpreis) - Number(alt.gesamtpreis);
      if (Math.abs(diff) < 0.005) { r.textContent = "Preis unverändert"; r.classList.add("ohne"); }
      else if (diff < 0) r.textContent = `${euro.format(-diff)} günstiger`;
      else { r.textContent = `${euro.format(diff)} teurer`; r.classList.add("hoch"); }
      for (const w of jetzt.warnungen) {
        const info = warnText(w);
        e.querySelector(".warnungen").appendChild(el("li", info.text, info.gefahr ? "gefahr" : ""));
      }
    }
    const a = e.querySelector(".link");
    if (/^https:\/\//.test(alt.url || "")) a.href = alt.url; else a.remove();
    const knopf = e.querySelector(".merken");
    merkKnopf(knopf, { id, ...alt });
    knopf.addEventListener("click", () => { if (!(id in merkliste())) e.remove(); $("merk-leer").hidden = Object.keys(merkliste()).length > 0; });
    return e;
  });
  $("merk-liste").replaceChildren(...karten);
  $("merk-leer").hidden = ids.length > 0;
}

// ---------- Ansichten ----------
function zaehler() {
  const n = Object.keys(merkliste()).length;
  $("anzahl-merk").hidden = n === 0;
  $("anzahl-merk").textContent = String(n);
  $("anzahl-alarm").hidden = alarmTreffer === 0;
  $("anzahl-alarm").textContent = `⚡${alarmTreffer}`;
}

function zeige(ansicht) {
  for (const knopf of document.querySelectorAll(".ansichten button")) {
    knopf.setAttribute("aria-pressed", String(knopf.dataset.ansicht === ansicht));
  }
  for (const name of ["suche", "merkliste", "alarme"]) $("ansicht-" + name).hidden = name !== ansicht;
  if (ansicht === "merkliste") merklisteZeigen();
  if (ansicht === "alarme") alarmePruefen();
  if (ansicht === "suche") suchen();
}

document.addEventListener("DOMContentLoaded", () => {
  $("barcode-form").addEventListener("submit", barcodeSuchen);
  $("filter").addEventListener("input", spaeter);
  $("filter").addEventListener("submit", (e) => { e.preventDefault(); suchen(); });
  $("datei").addEventListener("change", hochladen);
  $("alarm-anlegen").addEventListener("click", alarmAnlegen);
  $("kamera-knopf").addEventListener("click", kameraScannen);
  $("kamera-abbrechen").addEventListener("click", () => kameraStoppen("Kamera-Scan abgebrochen."));
  document.addEventListener("visibilitychange", () => { if (document.visibilityState === "hidden" && kamera.laeuft) kameraStoppen("Kamera-Scan beendet."); });
  window.addEventListener("pagehide", () => { if (kamera.laeuft) kameraStoppen(); });
  kameraVerfuegbar().then((ok) => {
    if (ok) $("kamera-knopf").disabled = false;
    else $("kamera-status").textContent = "Kamera-Scan wird von diesem Browser nicht unterstützt – bitte Barcode eintippen.";
  }, () => { $("kamera-status").textContent = "Kamera-Scan wird von diesem Browser nicht unterstützt – bitte Barcode eintippen."; });
  for (const knopf of document.querySelectorAll(".ansichten button")) {
    knopf.addEventListener("click", () => zeige(knopf.dataset.ansicht));
  }
  try { window.localStorage.getItem("schnapper.test"); } catch { $("speicher-hinweis").hidden = false; }
  zaehler();
  suchen();
  alarmePruefen();
});
