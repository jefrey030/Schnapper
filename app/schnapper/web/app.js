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
  // Gibt true zurück, wenn der Wert dauerhaft im Browser-Speicher liegt.
  schreiben(name, wert) {
    this.ersatz[name] = wert;
    try { window.localStorage.setItem("schnapper." + name, JSON.stringify(wert)); return true; }
    catch { $("speicher-hinweis").hidden = false; return false; }
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
  const ean = $("barcode").value.trim();
  const status = $("barcode-status");
  const knopf = $("barcode-knopf");
  $("barcode-treffer").replaceChildren();
  $("barcode-lizenz").textContent = "";
  if (!/^[0-9]{8,14}$/.test(ean)) {
    status.textContent = "Bitte einen Barcode mit 8 bis 14 Ziffern eingeben.";
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
    const daten = await antwort.json();
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
    status.textContent = "Server oder Preisquelle nicht erreichbar.";
  } finally {
    knopf.disabled = false;
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

// Gemeinsame Alarmprüfung für Anlegen und Wiederherstellen (wie der Server /api/suche):
// Höchstpreis > 0 mit höchstens 2 Nachkommastellen (kein mehrdeutiges "1,234"),
// Mindestrabatt 0–100. Komma gilt als Dezimaltrenner. Gibt null oder den Feldnamen zurück.
function zahlWert(x) { return Number(x.replace(",", ".")); }
const maxPreisOk = (x) => typeof x === "string" &&
  (x === "" || (/^[0-9]{1,9}(?:[.,][0-9]{1,2})?$/.test(x) && zahlWert(x) > 0));
const minRabattOk = (x) => typeof x === "string" &&
  (x === "" || (/^[0-9]{1,3}(?:[.,][0-9]{1,2})?$/.test(x) && zahlWert(x) >= 0 && zahlWert(x) <= 100));
function alarmFehler(w) {
  if (typeof w.text !== "string" || !w.text.trim() || w.text.length > 200) return "text";
  if (!maxPreisOk(w.max_preis)) return "max_preis";
  if (!minRabattOk(w.min_rabatt)) return "min_rabatt";
  if (!w.max_preis && !w.min_rabatt) return "max_preis/min_rabatt";
  if (typeof w.zustand !== "string" || !(w.zustand === "" || Object.hasOwn(ZUSTAND, w.zustand))) return "zustand";
  return null;
}

const ALARM_FEHLERTEXT = {
  text: "Suchbegriff höchstens 200 Zeichen.",
  max_preis: "„Bis €“ als Zahl größer 0 mit höchstens 2 Nachkommastellen, ohne Tausenderpunkt und ohne €, z. B. 1299,99.",
  min_rabatt: "„Ab % billiger“ zwischen 0 und 100, höchstens 2 Nachkommastellen.",
  "max_preis/min_rabatt": "„Bis €“ oder „Ab % billiger“ angeben.",
  zustand: "Zustand unbekannt.",
};

async function alarmAnlegen() {
  const w = aktuellerWunsch();
  if (!w) return;
  const falsch = alarmFehler(w);
  if (falsch) { $("status").textContent = `Preisalarm nicht angelegt: ${ALARM_FEHLERTEXT[falsch] || falsch}`; return; }
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

// ---------- Sichern & Wiederherstellen ----------
// Merkliste und Preisalarme als JSON-Datei sichern. Beim Wiederherstellen wird der
// bisherige Stand ersetzt (nicht gemischt); nur geprüfte Felder werden übernommen.
const SICHERUNG_VERSION = 1;
const MAX_SICHERUNG = 1024 * 1024;

function sicherungErstellen() {
  const obj = { format: "schnapper-sicherung", version: SICHERUNG_VERSION, erstellt_am: new Date().toISOString(),
                merkliste: merkliste(), alarme: alarme() };
  const blob = new Blob([JSON.stringify(obj, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = `schnapper-sicherung-${obj.erstellt_am.slice(0, 10)}.json`;
  document.body.appendChild(a);
  a.click();
  a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 0);
  $("sicherung-status").textContent =
    `Gesichert: ${Object.keys(obj.merkliste).length} gemerkt, ${obj.alarme.length} Alarme.`;
  $("sicherung-fehler").replaceChildren();
}

function istObjekt(x) { return x !== null && typeof x === "object" && !Array.isArray(x); }
function istText(x, min, max) { return typeof x === "string" && x.length >= min && x.length <= max; }
// Der Server liefert gesamtpreis als Dezimal-String ("54.89"); ältere Einträge können Zahlen sein.
function preisOk(x) {
  if (typeof x === "number") return Number.isFinite(x) && x >= 0;
  return typeof x === "string" && x.length <= 20 && /^[0-9]+(?:\.[0-9]+)?$/.test(x);
}
function kurz(x) { const s = String(x); return s.length > 40 ? s.slice(0, 40) + "…" : s; }

// Reine Funktion: prüft eine eingelesene Sicherung, ohne etwas zu speichern.
function sicherungPruefen(obj) {
  const fehler = [];
  const abweisen = (grund) => ({ ok: false, merkliste: {}, alarme: [], fehler: [grund] });
  if (!istObjekt(obj) || obj.format !== "schnapper-sicherung") return abweisen("Keine SCHNAPPER-Sicherung (format fehlt oder falsch).");
  if (obj.version !== SICHERUNG_VERSION) return abweisen(`Version ${kurz(obj.version)} wird nicht unterstützt (erwartet ${SICHERUNG_VERSION}).`);
  if (!istObjekt(obj.merkliste)) return abweisen("Merkliste fehlt oder ist kein Objekt.");
  if (!Array.isArray(obj.alarme)) return abweisen("Alarme fehlen oder sind keine Liste.");
  const ids = Object.keys(obj.merkliste);
  if (ids.length > MAX_MERK) return abweisen(`Zu viele Merkeinträge: ${ids.length} (max. ${MAX_MERK}).`);
  if (obj.alarme.length > MAX_ALARME) return abweisen(`Zu viele Preisalarme: ${obj.alarme.length} (max. ${MAX_ALARME}).`);

  const merk = Object.create(null);
  for (const id of ids) {
    const e = obj.merkliste[id];
    let falsch = null;
    if (!istText(id, 1, 200) || id === "__proto__") falsch = "Schlüssel";
    else if (!istObjekt(e)) falsch = "kein Objekt";
    else if (!istText(e.titel, 1, 500)) falsch = "titel";
    else if (!preisOk(e.gesamtpreis)) falsch = "gesamtpreis";
    else if (typeof e.url !== "string" || !(e.url === "" || /^https?:\/\//.test(e.url))) falsch = "url";
    else if (typeof e.quelle !== "string") falsch = "quelle";
    else if (typeof e.zustand !== "string") falsch = "zustand";
    else if (e.gemerkt_am !== undefined && typeof e.gemerkt_am !== "string") falsch = "gemerkt_am";
    if (falsch) { fehler.push(`Merkliste: Eintrag „${kurz(id)}“ ungültig (${falsch})`); continue; }
    const neu = { titel: e.titel, gesamtpreis: e.gesamtpreis, url: e.url, quelle: e.quelle, zustand: e.zustand };
    if (e.gemerkt_am !== undefined) neu.gemerkt_am = e.gemerkt_am;
    merk[id] = neu;
  }

  const alarmListe = [];
  const gesehen = new Set();
  obj.alarme.forEach((w, i) => {
    let falsch = null;
    if (!istObjekt(w)) falsch = "kein Objekt";
    else falsch = alarmFehler(w);
    if (!falsch && w.angelegt_am !== undefined && typeof w.angelegt_am !== "string") falsch = "angelegt_am";
    if (falsch) { fehler.push(`Alarme: Eintrag ${i + 1} ungültig (${falsch})`); return; }
    const neu = { text: w.text, max_preis: w.max_preis, min_rabatt: w.min_rabatt, zustand: w.zustand };
    if (w.angelegt_am !== undefined) neu.angelegt_am = w.angelegt_am;
    const schluessel = wunschText(neu);
    if (gesehen.has(schluessel)) { fehler.push(`Alarme: Eintrag ${i + 1} doppelt, übersprungen`); return; }
    gesehen.add(schluessel);
    alarmListe.push(neu);
  });
  return { ok: true, merkliste: merk, alarme: alarmListe, fehler };
}

function sicherungMelden(text, fehler) {
  $("sicherung-status").textContent = text;
  $("sicherung-fehler").replaceChildren(...fehler.map((f) => el("li", f)));
}

// Schreibt Merkliste und Alarme ganz oder gar nicht. Schlägt ein Schreibvorgang fehl,
// wird der vorherige Stand (Browser-Speicher und Ersatz) wiederhergestellt und gemeldet.
function sicherungUebernehmen(neueMerkliste, neueAlarme) {
  const NAMEN = ["merkliste", "alarme"];
  const vorher = {};
  try { for (const name of NAMEN) vorher[name] = window.localStorage.getItem("schnapper." + name); }
  catch {
    $("speicher-hinweis").hidden = false;
    sicherungMelden("Wiederherstellung fehlgeschlagen: Browser-Speicher ist nicht verfügbar. Nichts geändert.", []);
    return false;
  }
  const ersatzVorher = { ...speicher.ersatz };
  const neu = { merkliste: neueMerkliste, alarme: neueAlarme };
  const geschrieben = [];
  for (const name of NAMEN) {
    if (!speicher.schreiben(name, neu[name])) break;
    geschrieben.push(name);
  }
  if (geschrieben.length === NAMEN.length) return true;
  // Ein fehlgeschlagenes setItem ändert den Eintrag nicht; zurückgesetzt werden nur bereits geschriebene.
  let zurueck = true;
  for (const name of geschrieben) {
    const schluessel = "schnapper." + name;
    try { if (vorher[name] === null) window.localStorage.removeItem(schluessel); else window.localStorage.setItem(schluessel, vorher[name]); }
    catch { zurueck = false; }
  }
  speicher.ersatz = ersatzVorher;
  sicherungMelden(zurueck
    ? "Wiederherstellung fehlgeschlagen: Browser-Speicher ist voll oder gesperrt. Nichts geändert."
    : "Wiederherstellung fehlgeschlagen: Browser-Speicher ist voll oder gesperrt; der vorherige Stand konnte nicht vollständig zurückgeschrieben werden. Bitte Seite neu laden und prüfen.", []);
  zaehler();
  merklisteZeigen();
  alarmePruefen();
  return false;
}

async function sicherungLaden(ev) {
  const datei = ev.target.files[0];
  ev.target.value = "";
  if (!datei) return;
  if (datei.size > MAX_SICHERUNG) { sicherungMelden("Sicherung abgewiesen: Datei ist größer als 1 MiB. Nichts geändert.", []); return; }
  let obj;
  try { obj = JSON.parse(await datei.text()); }
  catch { sicherungMelden("Sicherung abgewiesen: Die Datei ist kein gültiges JSON. Nichts geändert.", []); return; }
  const ergebnis = sicherungPruefen(obj);
  if (!ergebnis.ok) { sicherungMelden("Sicherung abgewiesen: " + ergebnis.fehler[0] + " Nichts geändert.", []); return; }
  if (!sicherungUebernehmen(ergebnis.merkliste, ergebnis.alarme)) return;
  const n = Object.keys(ergebnis.merkliste).length;
  sicherungMelden(`Wiederhergestellt: ${n} gemerkt, ${ergebnis.alarme.length} Alarme; ` +
                  `${ergebnis.fehler.length} ungültige Einträge übersprungen`, ergebnis.fehler);
  zaehler();
  merklisteZeigen();
  alarmePruefen();
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
  $("sicherung-export").addEventListener("click", sicherungErstellen);
  $("sicherung-datei").addEventListener("change", sicherungLaden);
  for (const knopf of document.querySelectorAll(".ansichten button")) {
    knopf.addEventListener("click", () => zeige(knopf.dataset.ansicht));
  }
  try { window.localStorage.getItem("schnapper.test"); } catch { $("speicher-hinweis").hidden = false; }
  zaehler();
  suchen();
  alarmePruefen();
});
