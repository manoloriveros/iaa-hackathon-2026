"""Construye informe.html (archivo único, sin red) a partir de la corrida vigente de revisar_contexto_pendiente.py.

Uso: python construir_informe.py [ruta_de_la_corrida]
Sin argumento usa current_run.json o, si no existe, la corrida más reciente de runs/. Escribe runs/<corrida>/informe.html,
copia informe.html a la raíz de la carpeta y actualiza el manifest.json de la corrida.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

HERE = Path(__file__).resolve().parent


def find_root(start: Path) -> Path:
    for candidate in [start, *start.parents]:
        if (candidate / "RUTAS_PROYECTO.json").is_file():
            return candidate
    raise FileNotFoundError("No se encontró RUTAS_PROYECTO.json hacia arriba.")


ROOT = find_root(HERE)


def digest(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            h.update(block)
    return h.hexdigest()


def read_csv(path: Path) -> list[dict]:
    rows = []
    with path.open(encoding="utf-8", newline="") as stream:
        for row in csv.DictReader(stream):
            out = {}
            for k, v in row.items():
                if v is None or v == "":
                    out[k] = None
                elif v in ("True", "False"):
                    out[k] = v == "True"
                else:
                    try:
                        f = float(v)
                        out[k] = int(f) if f.is_integer() and "." not in v and "e" not in v.lower() else f
                    except ValueError:
                        out[k] = v
            rows.append(out)
    return rows


def main() -> None:
    if len(sys.argv) > 1:
        run = Path(sys.argv[1]).resolve()
    else:
        cur = HERE / "current_run.json"
        if cur.is_file():
            run = ROOT / json.loads(cur.read_text("utf-8"))["workspace_relative_run"]
        else:
            run = sorted((HERE / "runs").glob("ctx_*"))[-1]
    evidence = json.loads((run / "evidencia.json").read_text("utf-8"))
    tables = {name: read_csv(run / "tables" / f"{name}.csv") for name in
              ["historias", "referencias", "puentes", "siniestros", "candidatas_NO_APLICADAS", "retenidas", "escalera", "polizas_vecinas", "controles"]}
    data = {"evidence": evidence, "tables": tables, "built_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = TEMPLATE.replace("/*__DATA__*/", payload)
    (run / "informe.html").write_text(html, encoding="utf-8")
    (HERE / "informe.html").write_text(html, encoding="utf-8")
    manifest_path = run / "manifest.json"
    manifest = json.loads(manifest_path.read_text("utf-8"))
    manifest["informe.html"] = digest(run / "informe.html")
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({"run": str(run.relative_to(ROOT)).replace("\\", "/"), "informe_bytes": len(html.encode("utf-8")), "sha256": manifest["informe.html"]}))


TEMPLATE = r"""<!doctype html>
<html lang="es" data-theme="auto">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Capitales con contexto incompleto · IAA 2026</title>
<style>
:root{
  color-scheme:light;
  --page:#f9f9f7; --surface:#fcfcfb; --surface-2:#f3f3f0; --ink:#0b0b0b; --ink-2:#52514e; --muted:#898781; --grid:#e1e0d9; --axis:#c3c2b7;
  --buildings:#eb6834; --contents:#1baf7a; --violet:#6250d6; --raw:#a9a79f; --good:#0ca30c; --warn:#fab219; --crit:#d03b3b; --accent:#2a78d6;
  --radius:14px; --shadow:0 1px 2px rgba(11,11,11,.04), 0 8px 24px -16px rgba(11,11,11,.18);
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){ color-scheme:dark; --page:#0d0d0d; --surface:#1a1a19; --surface-2:#222220; --ink:#f0efec; --ink-2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835;
    --buildings:#d95926; --contents:#199e70; --violet:#9085e9; --raw:#6b6a64; --accent:#3987e5; --shadow:none; }
}
:root[data-theme="dark"]{ color-scheme:dark; --page:#0d0d0d; --surface:#1a1a19; --surface-2:#222220; --ink:#f0efec; --ink-2:#c3c2b7; --muted:#898781; --grid:#2c2c2a; --axis:#383835;
  --buildings:#d95926; --contents:#199e70; --violet:#9085e9; --raw:#6b6a64; --accent:#3987e5; --shadow:none; }
*{box-sizing:border-box}
html{scroll-behavior:smooth}
html,body{margin:0;background:var(--page);color:var(--ink);font-family:system-ui,-apple-system,"Segoe UI",sans-serif;font-size:14px;line-height:1.5}
a{color:inherit}
header.top{position:sticky;top:0;z-index:20;background:color-mix(in srgb,var(--page) 88%,transparent);backdrop-filter:blur(10px);border-bottom:1px solid var(--grid)}
.wrap{max-width:1280px;margin:0 auto;padding:0 20px}
.topbar{display:flex;align-items:center;gap:16px;padding:12px 0;flex-wrap:wrap}
.brand{display:flex;flex-direction:column;gap:2px;margin-right:auto}
.brand h1{font-size:17px;margin:0;font-weight:650;letter-spacing:-.01em}
.brand .sub{color:var(--ink-2);font-size:12px}
.seg{display:inline-flex;border:1px solid var(--grid);border-radius:999px;padding:2px;background:var(--surface)}
.seg button{border:0;background:transparent;color:var(--ink-2);padding:5px 12px;border-radius:999px;font:inherit;font-size:12.5px;cursor:pointer}
.seg button[aria-pressed="true"]{background:var(--ink);color:var(--page)}
nav.toc{display:flex;gap:4px;overflow-x:auto;padding:0 0 10px;scrollbar-width:none}
nav.toc a{text-decoration:none;color:var(--ink-2);padding:7px 11px;border-radius:10px;font-size:13px;white-space:nowrap}
nav.toc a:hover{background:var(--surface-2)}
main{padding:22px 0 60px}
section{margin:0 0 34px;scroll-margin-top:118px}
.case{scroll-margin-top:118px}
section>h2{font-size:12px;letter-spacing:.08em;text-transform:uppercase;color:var(--muted);margin:0 0 12px;font-weight:600}
.grid{display:grid;grid-template-columns:repeat(12,1fr);gap:16px}
.card{background:var(--surface);border:1px solid var(--grid);border-radius:var(--radius);padding:18px 20px;box-shadow:var(--shadow);min-width:0}
.card h3{font-size:15px;margin:0 0 6px;font-weight:650;letter-spacing:-.01em}
.card h4{font-size:13.5px;margin:14px 0 6px;font-weight:600}
.card .lead{color:var(--ink-2);margin:0 0 12px;font-size:13px}
.span-12{grid-column:span 12}.span-8{grid-column:span 8}.span-6{grid-column:span 6}.span-4{grid-column:span 4}
@media (max-width:1000px){.span-8,.span-6,.span-4{grid-column:span 12}}
.tiles{display:grid;grid-template-columns:repeat(auto-fit,minmax(165px,1fr));gap:12px}
.tile{background:var(--surface);border:1px solid var(--grid);border-radius:12px;padding:14px 16px}
.tile .label{color:var(--ink-2);font-size:12px}
.tile .value{font-size:24px;font-weight:650;letter-spacing:-.02em;margin-top:2px}
.tile .note{color:var(--muted);font-size:11.5px;margin-top:4px}
.hero{display:flex;align-items:baseline;gap:14px;flex-wrap:wrap}
.hero .n{font-size:54px;font-weight:700;letter-spacing:-.03em;line-height:1}
.hero .d{color:var(--ink-2);max-width:70ch}
p{margin:0 0 10px}
.prose p{max-width:92ch}
.prose ul{max-width:92ch;padding-left:20px}
.chips{display:flex;flex-wrap:wrap;gap:8px;align-items:center}
.chip{display:inline-flex;align-items:center;gap:6px;border:1px solid var(--grid);border-radius:999px;padding:4px 10px;font-size:12.5px;background:var(--surface-2)}
.chip b{font-weight:650}
.kv{display:grid;grid-template-columns:max-content 1fr;gap:4px 14px;font-size:13px;margin:8px 0}
.kv div:nth-child(odd){color:var(--ink-2)}
.chart{position:relative;width:100%}
.chart svg{width:100%;height:auto;display:block;overflow:visible}
.legend{display:flex;flex-wrap:wrap;gap:6px 14px;margin:6px 0 2px;font-size:12px;color:var(--ink-2)}
.legend span{display:inline-flex;align-items:center;gap:6px}
.legend i{display:inline-block;width:12px;height:12px;border-radius:3px;background:var(--c)}
.tip{position:fixed;z-index:50;pointer-events:none;background:var(--ink);color:var(--page);padding:8px 10px;border-radius:8px;font-size:12px;box-shadow:0 6px 18px rgba(0,0,0,.25);max-width:300px;display:none}
.tip b{font-size:13px}
.tip .row{display:flex;gap:8px;align-items:center}
.tip .key{display:inline-block;width:12px;height:3px;border-radius:2px;background:var(--c)}
.tbl-wrap{overflow:auto;border:1px solid var(--grid);border-radius:10px}
table.tbl{border-collapse:collapse;width:100%;font-size:12.5px;font-variant-numeric:tabular-nums}
table.tbl th,table.tbl td{padding:7px 10px;border-bottom:1px solid var(--grid);text-align:left;white-space:nowrap}
.wrapcells table.tbl td{white-space:normal}
table.tbl th{position:sticky;top:0;background:var(--surface-2);color:var(--ink-2);font-weight:600;cursor:pointer;user-select:none}
table.tbl th.sorted::after{content:" ▴";font-size:10px}
table.tbl th.sorted.desc::after{content:" ▾"}
table.tbl td.num,table.tbl th.num{text-align:right}
table.tbl tr:last-child td{border-bottom:0}
table.tbl tr:hover td{background:var(--surface-2)}
table.tbl tr.focus td{background:color-mix(in srgb,var(--warn) 18%,var(--surface))}
table.tbl tr.ref td{background:color-mix(in srgb,var(--accent) 12%,var(--surface))}
table.tbl tr.clickable{cursor:pointer}
.tbl-bar{display:flex;gap:10px;align-items:center;flex-wrap:wrap;margin:8px 0}
.tbl-bar input{font:inherit;font-size:13px;padding:7px 10px;border:1px solid var(--grid);border-radius:8px;background:var(--surface);color:var(--ink);min-width:240px}
.tbl-bar .count{color:var(--muted);font-size:12px;margin-left:auto}
.pager{display:flex;gap:6px;align-items:center;margin-top:8px;font-size:12.5px}
.pager button{border:1px solid var(--grid);background:var(--surface);color:var(--ink);border-radius:8px;padding:4px 10px;font:inherit;cursor:pointer}
.pager button:disabled{opacity:.4;cursor:default}
.status{display:inline-flex;align-items:center;gap:6px;font-weight:600}
.status .ic{width:16px;height:16px;border-radius:50%;display:inline-flex;align-items:center;justify-content:center;font-size:11px;color:#fff}
.status.ok .ic{background:var(--good)}.status.fail .ic{background:var(--crit)}
.badge{display:inline-block;border-radius:6px;padding:1px 7px;font-size:11.5px;background:var(--surface-2);border:1px solid var(--grid);color:var(--ink-2)}
.badge.n1{border-color:var(--good);color:var(--good)}.badge.n2{border-color:var(--accent);color:var(--accent)}.badge.n3{border-color:var(--warn);color:#8a5a00}.badge.hold{border-color:var(--crit);color:var(--crit)}
:root[data-theme="dark"] .badge.n3{color:var(--warn)}
.mono{font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;font-size:12px}
.note{color:var(--muted);font-size:12px}
.case{border:1px solid var(--grid);border-radius:12px;padding:14px 16px;background:var(--surface);margin:0 0 14px}
.case h4{margin:0 0 4px;font-size:14px}
.case .why{color:var(--ink-2);font-size:13px;margin:0 0 10px}
.case .meta{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 10px}
.timeline svg{width:100%;height:auto;display:block;overflow:visible}
.ladder td.level{font-weight:600}
footer{color:var(--muted);font-size:12px;padding:20px 0;border-top:1px solid var(--grid);margin-top:30px}
</style>
</head>
<body>
<header class="top"><div class="wrap">
  <div class="topbar">
    <div class="brand"><h1>Capitales pendientes con contexto incompleto · revisión de Claude</h1><div class="sub" id="subtitle"></div></div>
    <div class="seg" role="group" aria-label="tema"><button data-theme="auto">Auto</button><button data-theme="light">Claro</button><button data-theme="dark">Oscuro</button></div>
  </div>
  <nav class="toc" id="toc"></nav>
</div></header>
<main><div class="wrap" id="main"></div></main>
<footer><div class="wrap" id="footer"></div></footer>
<div class="tip" id="tip" role="tooltip"></div>
<script id="data" type="application/json">/*__DATA__*/</script>
<script>
const DATA = JSON.parse(document.getElementById("data").textContent);
const E = DATA.evidence, T = DATA.tables;
const fInt = n => n === null || n === undefined ? "–" : new Intl.NumberFormat("es-CO").format(Math.round(n));
const fNum = (n, d = 2) => n === null || n === undefined || isNaN(n) ? "–" : new Intl.NumberFormat("es-CO", { minimumFractionDigits: d, maximumFractionDigits: d }).format(n);
const fPct = (n, d = 1) => n === null || n === undefined ? "–" : fNum(n * 100, d) + " %";
const fCompact = n => { const a = Math.abs(n); if (a >= 1e6) return fNum(n / 1e6, 1) + "M"; if (a >= 1e3) return fNum(n / 1e3, a >= 1e4 ? 0 : 1) + "K"; return fNum(n, 0); };
const COLORS = { buildings: "var(--buildings)", contents: "var(--contents)", raw: "var(--raw)", violet: "var(--violet)", accent: "var(--accent)", warn: "var(--warn)", crit: "var(--crit)" };
const LINE = { buildings: "Edificios", contents: "Contenidos" };
const LEVEL = { N0_D34_estricto: "N0 · D34 estricto", N1_puente_dos_lados: "N1 · puente a dos lados", N2_vecino_conocido: "N2 · vecino conocido", N3_identidad_sin_campo: "N3 · identidad sin campo" };
const LEVEL_CLASS = { N1_puente_dos_lados: "n1", N2_vecino_conocido: "n2", N3_identidad_sin_campo: "n3" };
const BRIDGE = { AMBOS_LADOS_IGUALES: "iguales a ambos lados", SOLO_ANTERIOR_CONOCIDO: "solo anterior conocido", SOLO_POSTERIOR_CONOCIDO: "solo posterior conocido", AMBOS_LADOS_DISTINTOS: "distintos a cada lado", SIN_VECINO_CONOCIDO: "sin vecino conocido" };
const DIR = { prior: "anterior", later: "posterior" };
const HOLD = { referencia_contradictoria_en_la_poliza: "referencia contradictoria en la póliza", campo_ausente_con_vecinos_distintos: "campo ausente con vecinos distintos", siniestro_por_encima_del_capital_hipotetico: "siniestro por encima del capital hipotético", sin_referencia_compatible: "sin referencia compatible" };

function h(tag, attrs, ...children) {
  const el = document.createElement(tag);
  if (attrs) for (const [k, v] of Object.entries(attrs)) { if (k === "class") el.className = v; else if (k === "style") el.style.cssText = v; else if (k.startsWith("on")) el.addEventListener(k.slice(2), v); else if (v !== null && v !== undefined) el.setAttribute(k, v); }
  for (const c of children.flat()) { if (c === null || c === undefined) continue; el.appendChild(typeof c === "string" || typeof c === "number" ? document.createTextNode(String(c)) : c); }
  return el;
}
const svg = (tag, attrs) => { const el = document.createElementNS("http://www.w3.org/2000/svg", tag); for (const [k, v] of Object.entries(attrs || {})) el.setAttribute(k, v); return el; };
const tip = document.getElementById("tip");
function showTip(ev, title, rows) { tip.replaceChildren(h("b", null, title), ...rows.map(r => h("div", { class: "row" }, r.color ? h("span", { class: "key", style: `--c:${r.color}` }) : null, h("span", null, r.value), h("span", { style: "opacity:.75" }, r.label)))); tip.style.display = "block"; moveTip(ev); }
function moveTip(ev) { const pad = 14; let x = ev.clientX + pad, y = ev.clientY + pad; const r = tip.getBoundingClientRect(); if (x + r.width > innerWidth - 8) x = ev.clientX - r.width - pad; if (y + r.height > innerHeight - 8) y = ev.clientY - r.height - pad; tip.style.left = x + "px"; tip.style.top = y + "px"; }
const hideTip = () => { tip.style.display = "none"; };

function barChart(opts) {
  const { cats, series, stacked = false, fmt = fInt, tickEvery = 1, catLabel = c => c, title, yScale = "linear" } = opts;
  const W = 760, mL = 54, mR = 12, mT = 14, pw = W - mL - mR;
  const n = cats.length, k = series.length;
  const labelChars = Math.max(...cats.map(c => String(catLabel(c)).length));
  const rotate = n > 1 && labelChars * 6.4 * Math.ceil(n / tickEvery) > pw * 1.05;
  const mB = rotate ? Math.min(96, 30 + labelChars * 3.2) : 42, H = (opts.height || 220) + (mB - 42), ph = H - mT - mB;
  const totals = cats.map((c, i) => stacked ? series.reduce((s, x) => s + (x.values[i] || 0), 0) : Math.max(...series.map(x => x.values[i] || 0)));
  const maxV = Math.max(1e-9, ...totals);
  const niceMax = (() => { const p = Math.pow(10, Math.floor(Math.log10(maxV))); const m = maxV / p; const step = m <= 1 ? .2 : m <= 2 ? .5 : m <= 5 ? 1 : 2; return Math.ceil(m / step) * step * p; })();
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": title || "" });
  const yTicks = 4;
  const tickFmt = opts.tickFmt || (v => niceMax <= 1 ? fNum(v, 2) : niceMax <= 10 ? fNum(v, 1) : fCompact(v));
  const scale = v => yScale === "sqrt" ? Math.sqrt(Math.max(0, v) / niceMax) : v / niceMax;
  for (let i = 0; i <= yTicks; i++) { const frac = i / yTicks, v = yScale === "sqrt" ? niceMax * frac * frac : niceMax * frac, y = mT + ph - ph * frac; root.appendChild(svg("line", { x1: mL, x2: W - mR, y1: y, y2: y, stroke: "var(--grid)", "stroke-width": 1 })); const tx = svg("text", { x: mL - 8, y: y + 4, "text-anchor": "end", "font-size": 11, fill: "var(--muted)" }); tx.textContent = tickFmt(v); root.appendChild(tx); }
  root.appendChild(svg("line", { x1: mL, x2: W - mR, y1: mT + ph, y2: mT + ph, stroke: "var(--axis)", "stroke-width": 1 }));
  const band = pw / n, gap = 2, inner = Math.min(band * .72, stacked ? 26 : 26 * k), bw = stacked ? inner : Math.max(2, (inner - gap * (k - 1)) / k);
  const sy = v => ph * scale(v);
  cats.forEach((c, i) => {
    const x0 = mL + band * i + (band - inner) / 2;
    let acc = 0;
    const g = svg("g");
    series.forEach((s, j) => {
      const v = s.values[i] || 0, hgt = sy(v);
      const x = stacked ? x0 : x0 + j * (bw + gap);
      const y = stacked ? mT + ph - sy(acc) - hgt : mT + ph - hgt;
      if (v > 0) {
        const r = Math.min(4, bw / 2, hgt);
        const d = stacked && j < k - 1 && series.slice(j + 1).some(z => (z.values[i] || 0) > 0) ? `M${x},${y + hgt} v${-hgt} h${bw} v${hgt} z` : `M${x},${y + hgt} v${-(hgt - r)} a${r},${r} 0 0 1 ${r},${-r} h${bw - 2 * r} a${r},${r} 0 0 1 ${r},${r} v${hgt - r} z`;
        const p = svg("path", { d, fill: s.color });
        if (stacked && j > 0) { p.setAttribute("stroke", "var(--surface)"); p.setAttribute("stroke-width", 2); }
        g.appendChild(p);
      }
      acc += v;
    });
    const hit = svg("rect", { x: mL + band * i, y: mT, width: band, height: ph, fill: "transparent" });
    const rows = series.map(s => ({ color: s.color, value: fmt(s.values[i] || 0), label: s.name }));
    hit.addEventListener("pointerenter", ev => { showTip(ev, catLabel(c), k === 1 ? [rows[0]] : rows); g.style.opacity = ".82"; });
    hit.addEventListener("pointermove", moveTip);
    hit.addEventListener("pointerleave", () => { hideTip(); g.style.opacity = "1"; });
    root.appendChild(g); root.appendChild(hit);
    if (n <= 12 && k === 1 && (series[0].values[i] || 0) > 0) { const tx = svg("text", { x: x0 + inner / 2, y: mT + ph - sy(series[0].values[i]) - 6, "text-anchor": "middle", "font-size": 11, fill: "var(--ink-2)" }); tx.textContent = fmt(series[0].values[i]); root.appendChild(tx); }
    if (i % tickEvery === 0) { const cx = mL + band * i + band / 2; const tx = svg("text", { x: cx, y: mT + ph + 16, "text-anchor": "middle", "font-size": 11, fill: "var(--muted)" }); tx.textContent = String(catLabel(c)); if (rotate) { tx.setAttribute("transform", `rotate(-28 ${cx} ${mT + ph + 16})`); tx.setAttribute("text-anchor", "end"); } root.appendChild(tx); }
  });
  const box = h("div", { class: "chart" });
  if (k >= 2) box.appendChild(h("div", { class: "legend" }, series.map(s => h("span", null, h("i", { style: `--c:${s.color}` }), s.name))));
  box.appendChild(root);
  return box;
}

function dataTable(opts) {
  const { columns, rows, pageSize = 25, searchable = true, caption, rowClass, onRow } = opts;
  let filtered = rows.slice(), page = 0, sortKey = null, sortDesc = false;
  const box = h("div");
  const bar = h("div", { class: "tbl-bar" });
  const count = h("span", { class: "count" });
  const input = h("input", { type: "search", placeholder: "Buscar…", "aria-label": "Buscar" });
  if (searchable) bar.appendChild(input);
  if (caption) bar.appendChild(h("span", { class: "note" }, caption));
  bar.appendChild(count);
  const wrap = h("div", { class: "tbl-wrap" }); const table = h("table", { class: "tbl" }); wrap.appendChild(table);
  const pager = h("div", { class: "pager" });
  box.append(bar, wrap, pager);
  function draw() {
    table.replaceChildren();
    const thead = h("thead"), trh = h("tr");
    columns.forEach(c => { const th = h("th", { class: (c.num ? "num " : "") + (sortKey === c.key ? "sorted " + (sortDesc ? "desc" : "") : ""), onclick: () => { if (sortKey === c.key) sortDesc = !sortDesc; else { sortKey = c.key; sortDesc = false; } apply(); } }, c.label); trh.appendChild(th); });
    thead.appendChild(trh); table.appendChild(thead);
    const tbody = h("tbody");
    const start = page * pageSize;
    filtered.slice(start, start + pageSize).forEach(r => { const tr = h("tr", { class: (rowClass ? rowClass(r) : "") + (onRow ? " clickable" : "") }); if (onRow) tr.addEventListener("click", () => onRow(r)); columns.forEach(c => { const v = r[c.key]; tr.appendChild(h("td", { class: c.num ? "num" : "" }, c.fmt ? c.fmt(v, r) : (v === null || v === undefined ? "–" : String(v)))); }); tbody.appendChild(tr); });
    table.appendChild(tbody);
    count.textContent = `${fInt(filtered.length)} filas` + (filtered.length !== rows.length ? ` (de ${fInt(rows.length)})` : "");
    const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
    pager.replaceChildren(h("button", { disabled: page === 0 ? "" : null, onclick: () => { page--; draw(); } }, "Anterior"), h("span", null, `Página ${page + 1} de ${pages}`), h("button", { disabled: page >= pages - 1 ? "" : null, onclick: () => { page++; draw(); } }, "Siguiente"));
    pager.style.display = pages <= 1 ? "none" : "flex";
  }
  function apply() {
    const q = input.value.trim().toLowerCase();
    filtered = q ? rows.filter(r => columns.some(c => String(r[c.key] ?? "").toLowerCase().includes(q))) : rows.slice();
    if (sortKey) filtered.sort((a, b) => { const x = a[sortKey], y = b[sortKey]; if (x === y) return 0; if (x === null || x === undefined) return 1; if (y === null || y === undefined) return -1; const r = typeof x === "number" && typeof y === "number" ? x - y : String(x).localeCompare(String(y)); return sortDesc ? -r : r; });
    page = 0; draw();
  }
  input.addEventListener("input", apply);
  draw();
  return box;
}
const tile = (label, value, note) => h("div", { class: "tile" }, h("div", { class: "label" }, label), h("div", { class: "value" }, value), note ? h("div", { class: "note" }, note) : null);
const card = (span, title, lead, ...body) => h("div", { class: `card span-${span}` }, title ? h("h3", null, title) : null, lead ? h("p", { class: "lead" }, lead) : null, ...body);
const kv = pairs => h("div", { class: "kv" }, pairs.flatMap(([k, v]) => [h("div", null, k), h("div", null, v)]));
const section = (id, title, ...body) => h("section", { id }, h("h2", null, title), ...body);
const levelBadge = (lvl, holds) => holds ? h("span", { class: "badge hold" }, "retenida") : h("span", { class: `badge ${LEVEL_CLASS[lvl] || ""}` }, LEVEL[lvl] || lvl);
const fieldsEs = s => s ? s.split("|").join(", ") : "ninguno";

/* ---------- línea de tiempo de una póliza ---------- */
const dayMs = 86400000;
const toDate = s => new Date(s + "T00:00:00Z");
function timeline(rows, focusId, refId) {
  const W = 760, H = 190, mL = 60, mR = 14, mT = 16, mB = 30, pw = W - mL - mR, ph = H - mT - mB;
  const t0 = Date.UTC(2021, 0, 1), t1 = Date.UTC(2025, 11, 31);
  const x = d => mL + pw * (toDate(d).getTime() - t0) / (t1 - t0);
  const vals = rows.map(r => r.sum_insured).concat(rows.filter(r => r.row_id === focusId).map(r => r.sum_insured / 1000));
  const lo = Math.log10(Math.min(...vals) / 1.6), hi = Math.log10(Math.max(...vals) * 1.6);
  const y = v => mT + ph - ph * (Math.log10(v) - lo) / (hi - lo);
  const root = svg("svg", { viewBox: `0 0 ${W} ${H}`, role: "img", "aria-label": "capital por periodo" });
  for (let yr = 2021; yr <= 2026; yr++) { const xx = x(`${yr}-01-01`); root.appendChild(svg("line", { x1: xx, x2: xx, y1: mT, y2: mT + ph, stroke: "var(--grid)" })); if (yr < 2026) { const tx = svg("text", { x: xx + 4, y: mT + ph + 16, "font-size": 11, fill: "var(--muted)" }); tx.textContent = yr; root.appendChild(tx); } }
  for (let p = Math.ceil(lo); p <= Math.floor(hi); p++) { const yy = y(Math.pow(10, p)); root.appendChild(svg("line", { x1: mL, x2: W - mR, y1: yy, y2: yy, stroke: "var(--grid)", "stroke-dasharray": "2 3" })); const tx = svg("text", { x: mL - 8, y: yy + 4, "text-anchor": "end", "font-size": 11, fill: "var(--muted)" }); tx.textContent = fCompact(Math.pow(10, p)); root.appendChild(tx); }
  const line = rows[0].line;
  rows.forEach(r => {
    const x1 = x(r.period_start), x2 = Math.max(x1 + 2, x(r.period_end) + pw / ((t1 - t0) / dayMs));
    const isFocus = r.row_id === focusId, isRef = r.row_id === refId;
    const yy = y(r.sum_insured);
    const color = isFocus ? "var(--crit)" : isRef ? "var(--accent)" : COLORS[line];
    const seg = svg("line", { x1, x2, y1: yy, y2: yy, stroke: color, "stroke-width": isFocus || isRef ? 6 : 4, "stroke-linecap": "round" });
    seg.addEventListener("pointerenter", ev => showTip(ev, `${r.row_id} · ${r.period_start} → ${r.period_end}`, [{ value: fNum(r.sum_insured, 0) + " CU", label: "capital original" }, { value: r.address_id, label: "dirección" }, { value: r.renewal_decision || (r.test2025 ? "test 2025" : "–"), label: "decisión" }]));
    seg.addEventListener("pointermove", moveTip); seg.addEventListener("pointerleave", hideTip);
    root.appendChild(seg);
    if (isFocus) {
      const yh = y(r.sum_insured / 1000);
      root.appendChild(svg("line", { x1, x2, y1: yh, y2: yh, stroke: "var(--crit)", "stroke-width": 2, "stroke-dasharray": "5 4" }));
      root.appendChild(svg("line", { x1: (x1 + x2) / 2, x2: (x1 + x2) / 2, y1: yy, y2: yh, stroke: "var(--crit)", "stroke-width": 1, "stroke-dasharray": "2 3" }));
      const tx = svg("text", { x: x2 + 4, y: yh + 4, "font-size": 11, fill: "var(--crit)" }); tx.textContent = "÷1000 = " + fNum(r.sum_insured / 1000, 0); root.appendChild(tx);
    }
  });
  const addrs = [...new Set(rows.map(r => r.address_id))];
  if (addrs.length > 1) rows.forEach((r, i) => { if (i > 0 && rows[i - 1].address_id !== r.address_id) { const xx = x(r.period_start); root.appendChild(svg("line", { x1: xx, x2: xx, y1: mT, y2: mT + ph, stroke: "var(--violet)", "stroke-width": 1.5 })); const tx = svg("text", { x: xx + 3, y: mT + 10, "font-size": 10, fill: "var(--violet)" }); tx.textContent = "mudanza"; root.appendChild(tx); } });
  const box = h("div", { class: "timeline" });
  box.appendChild(h("div", { class: "legend" }, h("span", null, h("i", { style: `--c:${COLORS[line]}` }), "periodo normal"), h("span", null, h("i", { style: "--c:var(--crit)" }), "periodo pendiente (y su valor ÷1000)"), h("span", null, h("i", { style: "--c:var(--accent)" }), "referencia elegida"), addrs.length > 1 ? h("span", null, h("i", { style: "--c:var(--violet)" }), "cambio de dirección") : null));
  box.appendChild(root);
  return box;
}

const FIELD_COLS = { buildings: ["construction_type", "occupancy", "accidental_damage_cover", "voluntary_excess", "compulsory_excess", "smoke_alarms", "mortgage"], contents: ["tenure", "security_level", "high_value_items", "accidental_damage_cover", "works_from_home", "lodgers", "bicycle_cover", "voluntary_excess", "compulsory_excess"] };
const cell = v => v === null || v === undefined ? h("span", { style: "color:var(--crit);font-weight:600" }, "∅") : typeof v === "boolean" ? (v ? "sí" : "no") : String(v);
function historyTable(rows, focusId, refId) {
  const line = rows[0].line;
  const cols = [{ key: "row_id", label: "row_id" }, { key: "source_table", label: "tabla", fmt: v => v.replace("policies_", "").replace("test_", "test ") }, { key: "period_start", label: "inicio" }, { key: "period_end", label: "fin" }, { key: "exposure", label: "exposición", num: true, fmt: v => fNum(v, 4) },
    { key: "sum_insured", label: "capital original", num: true, fmt: v => fNum(v, 0) }, { key: "address_id", label: "dirección" }, { key: "renewal_decision", label: "decisión", fmt: (v, r) => v || (r.test2025 ? "test 2025" : "–") }, { key: "renewal_count", label: "renov.", num: true },
    ...FIELD_COLS[line].map(f => ({ key: f, label: f, fmt: cell })), { key: "written_premium", label: "prima", num: true, fmt: v => fNum(v, 2) }];
  return h("div", { class: "wrapcells" }, dataTable({ columns: cols, rows, searchable: false, pageSize: 50, rowClass: r => r.row_id === focusId ? "focus" : r.row_id === refId ? "ref" : "" }));
}
function refsTable(rows) {
  const cols = [{ key: "reference_row_id", label: "referencia" }, { key: "direction", label: "sentido", fmt: v => DIR[v] }, { key: "start_gap_days", label: "días", num: true }, { key: "reference_capital_CU", label: "capital ref.", num: true, fmt: v => fNum(v, 0) }, { key: "ratio_hypothetical_over_reference", label: "(÷1000)/ref", num: true, fmt: v => fNum(v, 4) },
    { key: "in_window", label: "ventana 1–400", fmt: v => v ? "sí" : "no" }, { key: "in_band", label: "banda 0,90–1,10", fmt: v => v ? "sí" : "no" }, { key: "known_fields_equal", label: "conocidos iguales", fmt: v => v ? "sí" : "no" }, { key: "changed_fields", label: "cambian", fmt: v => v || "–" }, { key: "unknown_fields", label: "desconocidos", fmt: v => v || "–" }, { key: "compatible_known_context", label: "compatible", fmt: v => v ? "sí" : "no" }];
  return dataTable({ columns: cols, rows, searchable: false, pageSize: 20 });
}
function policyPanel(policyId, focusId) {
  const rows = T.historias.filter(r => r.policy_id === policyId);
  const lad = T.escalera.find(r => r.row_id === focusId);
  const refs = T.referencias.filter(r => r.focus_row_id === focusId);
  const bridges = T.puentes.filter(b => b.focus_row_id === focusId);
  const claims = T.siniestros.filter(c => c.policy_id === policyId);
  const neigh = T.polizas_vecinas.filter(n => n.focus_row_id === focusId);
  const box = h("div");
  box.appendChild(h("div", { class: "meta" }, levelBadge(lad.level, lad.holds), h("span", { class: "badge" }, LINE[lad.line]), h("span", { class: "badge" }, lad.tier === "C_fila_incompleta" ? "tier C: la fila pendiente tiene un nulo" : "tier B: el nulo está en las referencias"), h("span", { class: "badge" }, "campo ausente: " + fieldsEs(lad.own_missing_fields)), lad.chosen_reference_row_id ? h("span", { class: "badge" }, `referencia ${lad.chosen_reference_row_id} (${DIR[lad.chosen_direction]}, ${lad.chosen_gap_days} días, razón ${fNum(lad.chosen_ratio, 4)})`) : null, lad.holds ? h("span", { class: "badge hold" }, lad.holds.split("|").map(x => HOLD[x] || x).join("; ")) : null));
  box.appendChild(timeline(rows, focusId, lad.chosen_reference_row_id));
  box.appendChild(h("h4", null, "Historia completa de la póliza (originales)"));
  box.appendChild(historyTable(rows, focusId, lad.chosen_reference_row_id));
  box.appendChild(h("h4", null, "Referencias originales con capital normal"));
  box.appendChild(refsTable(refs));
  if (bridges.length) { box.appendChild(h("h4", null, "Puentes del campo ausente (misma dirección)")); box.appendChild(dataTable({ columns: [{ key: "field", label: "campo" }, { key: "bridge_status", label: "estado", fmt: v => BRIDGE[v] || v }, { key: "prior_row_id", label: "anterior" }, { key: "prior_value", label: "valor anterior" }, { key: "later_row_id", label: "posterior" }, { key: "later_value", label: "valor posterior" }, { key: "distinct_known_values_same_address", label: "valores conocidos en la póliza" }], rows: bridges, searchable: false })); }
  if (claims.length) { box.appendChild(h("h4", null, "Siniestros de la póliza (capa base)")); box.appendChild(dataTable({ columns: [{ key: "claim_id", label: "siniestro" }, { key: "peril", label: "peligro" }, { key: "loss_date", label: "ocurrencia" }, { key: "status", label: "estado" }, { key: "incurred_to_date", label: "incurrido", num: true, fmt: v => fNum(v, 2) }, { key: "recoveries", label: "recuperos", num: true, fmt: v => fNum(v, 2) }, { key: "assigned_row_id", label: "periodo asignado" }, { key: "period_extreme", label: "periodo extremo", fmt: v => v ? "sí" : "no" }], rows: claims, searchable: false })); }
  else box.appendChild(h("p", { class: "note" }, "Sin siniestros registrados para esta póliza en la capa base."));
  if (neigh.length) { box.appendChild(h("h4", null, "Otra póliza de hogar del mismo cliente y dirección (solo descripción)")); box.appendChild(dataTable({ columns: [{ key: "other_policy_id", label: "póliza" }, { key: "other_line", label: "ramo", fmt: v => LINE[v] }, { key: "other_row_id", label: "periodo" }, { key: "other_period_start", label: "inicio" }, { key: "other_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "hypothetical_CU", label: "÷1000 de la pendiente", num: true, fmt: v => fNum(v, 0) }], rows: neigh, searchable: false })); }
  return box;
}

/* ---------- secciones ---------- */
function render() {
  const main = document.getElementById("main");
  const L = E.ladder, C = E.cohort, G = E.global_field_statistics, D = E.distributions, K = E.candidates_NOT_APPLIED;
  document.getElementById("subtitle").textContent = `Corrida ${E.run_id} · rama activa ${E.provenance.retrospective_run.split("/").pop()} · ${E.summary.checks_passed}/${E.summary.checks_total} controles · sin cambios de datos`;
  const toc = document.getElementById("toc");
  [["resumen", "Resumen"], ["cohorte", "Qué son estas filas"], ["campos", "Qué dicen los campos ausentes"], ["historias", "Historias y referencias"], ["escalera", "Escalera de criterios"], ["casos", "Casos concretos"], ["explorador", "Explorador"], ["candidatas", "Candidatas"], ["propuesta", "Propuesta"], ["controles", "Controles"]].forEach(([id, name]) => toc.appendChild(h("a", { href: "#" + id }, name)));

  // resumen
  const hero = card(12, null, null, h("div", { class: "hero" }, h("div", { class: "n" }, fInt(C.rows)), h("div", { class: "d" }, h("p", null, h("b", null, "capitales pendientes con contexto incompleto"), ` en ${fInt(C.policies)} pólizas de hogar (${fInt(C.by_line.buildings)} de edificios, ${fInt(C.by_line.contents)} de contenidos), ${fInt(C.history_rows)} periodos leídos desde los originales.`),
    h("p", null, `Los 154 son el grupo F de D48 que sigue pendiente en la rama activa (${E.provenance.retrospective_status.replace("verified_retrospective_", "")}); las dos pólizas retenidas en D57 y revisadas en D60 quedaron corregidas en CAP06R. En ${fInt(L.by_tier.C_fila_incompleta)} filas el nulo está en la propia fila pendiente; en ${fInt(L.by_tier.B_referencias_incompletas)} la fila está completa y el nulo está en sus referencias. Todas tienen una referencia original próxima que encaja en los campos conocidos; ninguna cumple el criterio estricto porque un campo es desconocido, no porque sea distinto.`),
    h("p", { class: "note" }, "Revisión propia asistida por IA, sin cambios de datos, índices ni corridas de Codex; la lista de candidatas no se aplica."))));
  const tiles = h("div", { class: "tiles" },
    tile("Candidatas sin aplicar", fInt(K.rows), `${fInt(L.any_direction.by_level.N1_puente_dos_lados)} N1 · ${fInt(L.any_direction.by_level.N2_vecino_conocido)} N2 · ${fInt(L.any_direction.by_level.N3_identidad_sin_campo)} N3`),
    tile("Retenidas", fInt(E.held.rows), "referencia contradictoria por tramo ampliado"),
    tile("Con apoyo anterior", fInt(L.prior_only.candidates), "disponible al corte; el resto solo posterior"),
    tile("Filas de test 2025", fInt(L.test2025_rows_in_candidates), `${fInt(L.candidates_with_test2025_reference)} candidatas de 2024 se apoyan en test 2025`),
    tile("Campos D34 con nulos", "3", "smoke_alarms, security_level, high_value_items"),
    tile("Cambios de esos campos en la misma dirección", "0", `en ${fCompact(G.buildings.consecutive_pairs_same_address + G.contents.consecutive_pairs_same_address)} pares consecutivos del archivo`),
    tile("Siniestros sobre el capital ÷1000", "0", `${fInt(D.claims_in_extreme_periods)} siniestros aceptados en periodos pendientes`),
    tile("Controles", `${E.summary.checks_passed}/${E.summary.checks_total}`, "originales y tablas de Codex con hash verificado"));
  main.appendChild(section("resumen", "Resumen", h("div", { class: "grid" }, hero, card(12, "Cifras clave", null, tiles))));

  // cohorte
  const g1 = h("div", { class: "grid" });
  g1.appendChild(card(4, "Por tabla de origen", "Filas de entrenamiento 2021–2024 y filas de test 2025.", barChart({ cats: Object.keys(L.by_source_table), series: [{ name: "filas", color: COLORS.raw, values: Object.values(L.by_source_table) }], catLabel: c => c.replace("policies_", "").replace("test_", "test ") })));
  g1.appendChild(card(4, "Por año de inicio", null, barChart({ cats: Object.keys(L.by_year), series: [{ name: "filas", color: COLORS.raw, values: Object.values(L.by_year) }] })));
  g1.appendChild(card(4, "Campo ausente en la fila pendiente", `${fInt(L.by_tier.B_referencias_incompletas)} filas completas: el nulo está en la referencia.`, barChart({ cats: Object.keys(L.own_missing_fields), series: [{ name: "filas", color: COLORS.raw, values: Object.values(L.own_missing_fields) }], catLabel: c => c || "ninguno (tier B)" })));
  g1.appendChild(card(12, "Derivación de la cohorte", null, h("div", { class: "chips" }, h("span", { class: "chip" }, h("b", null, "202"), "grupo F (D48, congelado en D56)"), h("span", null, "−"), h("span", { class: "chip" }, h("b", null, "46"), "aplicadas en CAP05R (D58)"), h("span", null, "−"), h("span", { class: "chip" }, h("b", null, "2"), "retenidas en D57, revisadas en D60 y corregidas en CAP06R (D61)"), h("span", null, "="), h("span", { class: "chip", style: "border-color:var(--accent)" }, h("b", null, fInt(C.rows)), "filas revisadas aquí")),
    kv([["Hash SHA-256 de los row_id ordenados", h("span", { class: "mono" }, C.sha256_sorted_row_ids)], ["Pendientes en la rama", `${fInt(C.pending_in_branch_total)} (${Object.entries(C.pending_groups_in_branch).map(([k, v]) => `${k}: ${v}`).join(" · ")})`], ["Periodos por póliza", Object.entries(D.history_periods_per_policy).map(([k, v]) => `${k} periodos: ${v} pólizas`).join(" · ")], ["Pólizas con cambio de dirección en su historia", fInt(D.policies_with_address_change)], ["Decisión de renovación de la fila pendiente", Object.entries(D.focus_renewal_decision).map(([k, v]) => `${k}: ${v}`).join(" · ")]])));
  main.appendChild(section("cohorte", "Qué son estas filas", g1));

  // campos
  const g2 = h("div", { class: "grid" });
  const fieldRows = [];
  for (const line of ["buildings", "contents"]) for (const [f, s] of Object.entries(G[line].fields)) if (s.null_rows) { const ch = G[line].field_changes_between_consecutive_periods[f]; fieldRows.push({ line: LINE[line], field: f, null_share: s.null_share, null_share_extreme: s.null_share_extreme, pairs: ch.pairs_both_known_same_address, changes_same: ch.changes_same_address, changes_move: ch.changes_with_address_change }); }
  g2.appendChild(card(12, "Los tres campos que pueden faltar son atributos del inmueble, no de la escala", "En todo el archivo original de hogar (train y test), solo estos tres campos D34 tienen nulos, en torno al 2,5 % de las filas, con la misma frecuencia en las filas extremas. Entre periodos consecutivos de la misma póliza en la misma dirección nunca cambian; smoke_alarms solo cambia cuando cambia la dirección.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "line", label: "ramo" }, { key: "field", label: "campo" }, { key: "null_share", label: "nulos en el archivo", num: true, fmt: v => fPct(v, 2) }, { key: "null_share_extreme", label: "nulos en filas extremas", num: true, fmt: v => fPct(v, 2) }, { key: "pairs", label: "pares consecutivos con ambos conocidos, misma dirección", num: true, fmt: fInt }, { key: "changes_same", label: "cambios en la misma dirección", num: true, fmt: fInt }, { key: "changes_move", label: "cambios con mudanza", num: true, fmt: fInt }], rows: fieldRows, searchable: false }))));
  const ratioRows = ["buildings", "contents"].map(line => ({ line: LINE[line], pairs: G[line].consecutive_pairs_same_address, inband: G[line].ratio_consecutive_same_address_in_band, q01: G[line].ratio_consecutive_same_address_quantiles["0.01"], q50: G[line].ratio_consecutive_same_address_quantiles["0.5"], q99: G[line].ratio_consecutive_same_address_quantiles["0.99"], moves: G[line].consecutive_pairs_address_change, move_inband: G[line].ratio_consecutive_address_change_in_band }));
  g2.appendChild(card(6, "Cómo cambia el capital entre periodos consecutivos normales", "Razón capital(t)/capital(t−1) en la misma dirección: casi siempre dentro de 0,90–1,10 (indexación anual), con pocas ampliaciones o reducciones. Con mudanza, el capital de edificios se recalcula.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "line", label: "ramo" }, { key: "pairs", label: "pares misma dirección", num: true, fmt: fInt }, { key: "inband", label: "dentro de 0,90–1,10", num: true, fmt: v => fPct(v, 2) }, { key: "q01", label: "p1", num: true, fmt: v => fNum(v, 3) }, { key: "q50", label: "mediana", num: true, fmt: v => fNum(v, 3) }, { key: "q99", label: "p99", num: true, fmt: v => fNum(v, 3) }, { key: "moves", label: "pares con mudanza", num: true, fmt: fInt }, { key: "move_inband", label: "en banda con mudanza", num: true, fmt: v => fPct(v, 1) }], rows: ratioRows, searchable: false }))));
  const P = E.premium_diagnostic;
  g2.appendChild(card(6, "Prima escrita por mil de capital (solo diagnóstico)", "Prima anualizada por cada 1.000 CU de capital. Con el capital registrado, las filas pendientes pagarían mil veces menos que el resto; con el capital ÷1000 quedan en la misma distribución. La prima no se usa como criterio: su base y prorrateo no están documentados.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "line", label: "ramo" }, { key: "q", label: "cuantil" }, { key: "normal", label: "filas normales", num: true, fmt: v => fNum(v, 3) }, { key: "focus", label: "pendientes con capital ÷1000", num: true, fmt: v => fNum(v, 3) }], rows: ["buildings", "contents"].flatMap(line => ["0.05", "0.25", "0.5", "0.75", "0.95"].map(q => ({ line: LINE[line], q: "p" + Math.round(parseFloat(q) * 100), normal: P[line].normal_rows_premium_per_1000_capital_quantiles[q], focus: P[line].focus_premium_per_1000_hypothetical_capital_quantiles[q] }))), searchable: false, pageSize: 10 })),
    h("p", { class: "note" }, `Mediana con el capital tal cual: edificios ${fNum(P.buildings.focus_premium_per_1000_recorded_capital_median, 5)}, contenidos ${fNum(P.contents.focus_premium_per_1000_recorded_capital_median, 5)} por mil.`)));
  main.appendChild(section("campos", "Qué dicen los campos ausentes", g2));

  // historias y referencias
  const g3 = h("div", { class: "grid" });
  const gapCounts = D.chosen_gap_days_counts; const gapLabels = ["1–90 días", "91–180 días", "181–270 días", "271–364 días", "365 días", "366 días"]; const gapVals = [0, 0, 0, 0, 0, 0];
  for (const [d, n] of Object.entries(gapCounts)) { const v = parseInt(d); const k = v <= 90 ? 0 : v <= 180 ? 1 : v <= 270 ? 2 : v <= 364 ? 3 : v === 365 ? 4 : 5; gapVals[k] += n; }
  g3.appendChild(card(4, "Distancia a la referencia elegida", "La mayoría son renovaciones anuales; las distancias cortas corresponden a tramos de cambio a mitad de año.", barChart({ cats: gapLabels, series: [{ name: "candidatas", color: COLORS.accent, values: gapVals }] })));
  const ratios = T.candidatas_NO_APLICADAS.map(r => r.chosen_ratio); const rb = { "0,96–0,97": 0, "0,97–0,98": 0, "0,98–0,99": 0, "0,99–1,00": 0, "1,00–1,01": 0, "1,01–1,02": 0, "1,02–1,03": 0, "1,03–1,04": 0 };
  ratios.forEach(v => { const k = v < .97 ? "0,96–0,97" : v < .98 ? "0,97–0,98" : v < .99 ? "0,98–0,99" : v < 1 ? "0,99–1,00" : v < 1.01 ? "1,00–1,01" : v < 1.02 ? "1,01–1,02" : v < 1.03 ? "1,02–1,03" : "1,03–1,04"; rb[k]++; });
  g3.appendChild(card(4, "Razón (capital ÷1000) / referencia", `Entre ${fNum(D.chosen_ratio_quantiles["0.0"], 4)} y ${fNum(D.chosen_ratio_quantiles["1.0"], 4)}: la indexación anual de 2–3 % en un sentido u otro, nunca cerca de los bordes de la banda.`, barChart({ cats: Object.keys(rb), series: [{ name: "candidatas", color: COLORS.accent, values: Object.values(rb) }] })));
  g3.appendChild(card(4, "Sentido de la referencia elegida", "Se prefiere la anterior cuando existe; las posteriores solo caben en la rama retrospectiva.", barChart({ cats: ["anterior", "posterior"], series: [{ name: "candidatas", color: COLORS.accent, values: [L.direction_of_chosen_reference.prior || 0, L.direction_of_chosen_reference.later || 0] }] })));
  g3.appendChild(card(6, "Puentes del campo ausente en la misma dirección", `${fInt(Object.values(L.bridge_statuses_same_address).reduce((a, b) => a + b, 0))} campos ausentes en ${fInt(L.by_tier.C_fila_incompleta)} filas: en ${fInt(L.bridge_statuses_same_address.AMBOS_LADOS_IGUALES)} hay un valor conocido antes y otro después, siempre iguales; en el resto solo hay un lado conocido porque la fila pendiente es el primer o el último periodo. D56 contó un caso con valores distintos: era una mudanza, no un cambio en el mismo inmueble.`,
    barChart({ cats: Object.keys(L.bridge_statuses_same_address), series: [{ name: "campos", color: COLORS.violet, values: Object.values(L.bridge_statuses_same_address) }], catLabel: c => BRIDGE[c] })));
  const otherRows = [["Filas con alguna referencia de contexto distinto", `${fInt(L.rows_with_other_references_changed)} (${Object.entries(L.changed_fields_in_other_references).map(([k, v]) => `${k}: ${v}`).join(" · ")}); son mudanzas o el alias T/W, nunca la referencia elegida`], ["Filas con referencia anterior y posterior compatibles", fInt(L.both_directions_compatible)], ["Filas con una referencia contradictoria (contexto igual, razón fuera de banda)", `${fInt(L.contradictions)}: tramos cortos con capital ampliado, retenidas`], ["Siniestros en las 154 pólizas", `${fInt(D.claims_total)} (${fInt(D.claims_accepted)} aceptados, ${fInt(D.claims_in_extreme_periods)} en periodos pendientes; ninguno supera el capital ÷1000)`], ["Otra póliza de hogar del mismo cliente y dirección", `${fInt(D.focus_rows_with_neighbour_policy)} filas; ninguna de esas pólizas vecinas es extrema`], ["Tier B: campo ausente en las referencias", Object.entries(L.tier_B_detail.reference_missing_fields).map(([k, v]) => `${k}: ${v}`).join(" · ") + `; en ${fInt(L.tier_B_detail.only_focus_knows_the_field)} pólizas solo la fila pendiente conoce el campo`]].map(([k, v]) => ({ k, v }));
  g3.appendChild(card(6, "Otras referencias de la misma póliza", null, h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "k", label: "aspecto" }, { key: "v", label: "observado" }], rows: otherRows, searchable: false }))));
  main.appendChild(section("historias", "Historias y referencias", g3));

  // escalera
  const ladderRows = [
    { level: "N0 · D34 estricto", def: "Todos los campos D34 conocidos e iguales en la fila y en la referencia, sin solape, inicio a 1–400 días, razón 0,90–1,10 (criterio vigente de CAP01 y de la rama).", any: 0, prior: 0, risk: "Ninguno nuevo. Deja las 154 pendientes de forma indefinida: el nulo no se puede conocer." },
    { level: "N1 · puente a dos lados", def: "Como N0, pero el campo ausente se acepta como desconocido si en la misma dirección hay un valor conocido antes y otro después, iguales entre sí.", any: L.any_direction.by_level.N1_puente_dos_lados, prior: L.prior_only.by_level.N1_puente_dos_lados, risk: "Exige que el inmueble no cambiara entre dos observaciones iguales; el archivo no tiene un solo cambio de estos campos en la misma dirección." },
    { level: "N2 · vecino conocido", def: "Como N1, pero basta un valor conocido a un solo lado (primer o último periodo de la póliza); en tier B, los demás periodos conocidos coinciden con la fila.", any: L.any_direction.by_level.N2_vecino_conocido, prior: L.prior_only.by_level.N2_vecino_conocido, risk: "El valor del otro lado no se observa; la identidad del riesgo sigue dada por cliente, dirección y el resto de campos." },
    { level: "N3 · identidad sin campo", def: "Solo identidad: cliente, dirección y todos los demás campos conocidos iguales; ningún otro periodo informa el campo (tier B con dos periodos).", any: L.any_direction.by_level.N3_identidad_sin_campo, prior: L.prior_only.by_level.N3_identidad_sin_campo, risk: "Es el caso más débil: una sola referencia, que además no informa el campo. La razón de capital sigue siendo la prueba principal." },
  ];
  const cum = L.any_direction.cumulative, cumP = { N1: L.prior_only.by_level.N1_puente_dos_lados, "N1+N2": L.prior_only.by_level.N1_puente_dos_lados + L.prior_only.by_level.N2_vecino_conocido, "N1+N2+N3": L.prior_only.candidates };
  const g4 = h("div", { class: "grid" });
  g4.appendChild(card(12, "Escalera de criterios", "Cada nivel incluye a los anteriores. Las dos filas retenidas no entran en ningún nivel aunque su referencia más próxima encaje. 'Cualquier sentido' vale para la rama retrospectiva; 'solo anterior' es el subconjunto cuya evidencia existía al inicio del periodo corregido.",
    h("div", { class: "wrapcells ladder" }, dataTable({ columns: [{ key: "level", label: "nivel" }, { key: "def", label: "qué exige" }, { key: "any", label: "filas (cualquier sentido)", num: true, fmt: fInt }, { key: "prior", label: "filas (solo anterior)", num: true, fmt: fInt }, { key: "risk", label: "qué asume y qué riesgo añade" }], rows: ladderRows, searchable: false })),
    h("div", { class: "chips", style: "margin-top:12px" }, h("span", { class: "chip" }, h("b", null, fInt(cum.N1)), "acumulado N1"), h("span", { class: "chip" }, h("b", null, fInt(cum["N1+N2"])), "acumulado N1+N2"), h("span", { class: "chip" }, h("b", null, fInt(cum["N1+N2+N3"])), "acumulado N1+N2+N3"), h("span", { class: "chip" }, h("b", null, fInt(E.held.rows)), "retenidas"), h("span", { class: "chip", style: "border-color:var(--accent)" }, h("b", null, fInt(cumP["N1+N2+N3"])), "de ellas con apoyo anterior"))));
  g4.appendChild(card(6, "Qué no cambia en ningún nivel", null, h("div", { class: "prose" }, h("ul", null, h("li", null, "Ningún nulo se rellena: el campo queda desconocido en la tabla y la bitácora lo registra como desconocido."), h("li", null, "La referencia siempre es un periodo original de la misma póliza, cliente y dirección, con capital normal, sin solape, a 1–400 días, con todos los demás campos iguales y razón 0,90–1,10 tras dividir entre mil."), h("li", null, "No se usan reparaciones previas como referencia, ni primas, ni siniestros, ni pólizas vecinas para decidir."), h("li", null, "Una referencia contradictoria en la póliza retiene la fila aunque la más próxima encaje."), h("li", null, "Solo cambia sum_insured, y solo en una capa retrospectiva separada de la base, como CAP02R a CAP06R.")))));
  g4.appendChild(card(6, "Qué pasa si no se decide nada", null, h("div", { class: "prose" }, h("p", null, `Las ${fInt(C.rows)} filas conservan capitales mil veces mayores que el resto de su propia historia. En la base hay ${fInt(L.test2025_rows_in_candidates)} de ellas en el test de 2025: cualquier modelo que use el capital como predictor las verá como riesgos mil veces mayores al predecir. En entrenamiento, ${fInt(K.rows - K.test2025_rows)} candidatas más las retenidas tienen capitales fuera de escala que distorsionan la relación capital–coste en la cola alta.`), h("p", null, "La alternativa de modelado es tratar esos capitales como no disponibles con un imputador entrenado solo en entrenamiento, como ya anotó D48; es más opaca que una corrección documentada fila a fila y no aprovecha la historia de la propia póliza."))));
  main.appendChild(section("escalera", "Escalera de criterios", g4));

  // casos
  const g5 = h("div", { class: "grid" });
  const casesBox = h("div", { class: "span-12" });
  E.cases.forEach(c => {
    const box = h("div", { class: "case", id: "caso-" + c.key });
    box.appendChild(h("h4", null, `${c.key} · ${c.title}`));
    box.appendChild(h("p", { class: "why" }, c.why));
    box.appendChild(h("p", null, `Póliza ${c.policy_id} (${LINE[c.line]}), fila pendiente ${c.row_id}.`));
    box.appendChild(policyPanel(c.policy_id, c.row_id));
    casesBox.appendChild(box);
  });
  g5.appendChild(card(12, `${E.cases.length} casos elegidos por regla, no a mano`, "Cada caso se seleccionó con una condición explícita (primer row_id que la cumple) y muestra la historia completa de la póliza, sus referencias, los puentes del campo ausente y los siniestros. La fila en naranja es la pendiente; la azul, la referencia elegida; ∅ marca un nulo."));
  g5.appendChild(casesBox);
  main.appendChild(section("casos", "Casos concretos", g5));

  // explorador
  const g6 = h("div", { class: "grid" });
  const detail = h("div", { style: "margin-top:14px" });
  const explorerRows = T.escalera.map(r => ({ ...r, line_es: LINE[r.line], dir_es: r.chosen_direction ? DIR[r.chosen_direction] : "–" }));
  g6.appendChild(card(12, "Explorador de las 154 filas", "Busca por póliza, fila o campo y pulsa una fila para ver su historia completa, sus referencias y sus puentes.",
    dataTable({ columns: [{ key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "line_es", label: "ramo" }, { key: "year", label: "año", num: true }, { key: "original_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "hypothetical_CU", label: "÷1000", num: true, fmt: v => fNum(v, 0) }, { key: "own_missing_fields", label: "campo ausente", fmt: v => v || "(en la referencia)" }, { key: "bridge_statuses", label: "puente", fmt: v => v ? v.split("|").map(x => BRIDGE[x] || x).join("; ") : "–" }, { key: "chosen_reference_row_id", label: "referencia" }, { key: "dir_es", label: "sentido" }, { key: "chosen_gap_days", label: "días", num: true }, { key: "chosen_ratio", label: "razón", num: true, fmt: v => fNum(v, 4) }, { key: "level", label: "nivel", fmt: (v, r) => levelBadge(v, r.holds) }], rows: explorerRows, pageSize: 20, onRow: r => { detail.replaceChildren(h("h4", null, `Póliza ${r.policy_id} · fila ${r.row_id}`), policyPanel(r.policy_id, r.row_id)); detail.scrollIntoView({ behavior: "smooth", block: "start" }); } }), detail));
  main.appendChild(section("explorador", "Explorador", g6));

  // candidatas
  const g7 = h("div", { class: "grid" });
  const candRows = T.candidatas_NO_APLICADAS.map(r => ({ ...r, line_es: LINE[r.line], dir_es: DIR[r.chosen_direction] }));
  g7.appendChild(card(12, `Lista congelada de ${fInt(K.rows)} candidatas (no aplicadas)`, `SHA-256 de los row_id ordenados: ${K.sha256_sorted_row_ids}. Suma de capitales originales ${fNum(K.sum_original_CU, 0)} CU; hipotéticos ${fNum(K.sum_hypothetical_CU, 0)} CU. ${fInt(K.prior_supported)} con apoyo anterior, ${fInt(K.rows - K.prior_supported)} solo posterior; ${fInt(K.test2025_rows)} filas de test 2025; ${fInt(K.reference_is_test2025)} con referencia en test 2025.`,
    dataTable({ columns: [{ key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "line_es", label: "ramo" }, { key: "source_table", label: "tabla" }, { key: "period_start", label: "inicio" }, { key: "original_capital_CU", label: "capital original", num: true, fmt: v => fNum(v, 0) }, { key: "new_hypothetical_CU", label: "nuevo (÷1000)", num: true, fmt: v => fNum(v, 0) }, { key: "chosen_reference_row_id", label: "referencia" }, { key: "dir_es", label: "sentido" }, { key: "chosen_gap_days", label: "días", num: true }, { key: "chosen_ratio", label: "razón", num: true, fmt: v => fNum(v, 4) }, { key: "unknown_fields_focus", label: "desconocido en la fila", fmt: v => v || "–" }, { key: "unknown_fields_reference", label: "desconocido en la ref.", fmt: v => v || "–" }, { key: "level", label: "nivel", fmt: v => levelBadge(v, "") }, { key: "chosen_reference_test2025", label: "ref. test 2025", fmt: v => v ? "sí" : "no" }], rows: candRows, pageSize: 20 })));
  g7.appendChild(card(12, `Retenidas (${fInt(E.held.rows)})`, "Su referencia más próxima encaja, pero otro periodo de la misma póliza con contexto igual queda fuera de la banda: un tramo corto con capital ampliado. Se retienen para revisión manual, como las dos pólizas de D60.",
    dataTable({ columns: [{ key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "line", label: "ramo", fmt: v => LINE[v] }, { key: "original_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "chosen_reference_row_id", label: "referencia más próxima" }, { key: "chosen_ratio", label: "razón", num: true, fmt: v => fNum(v, 4) }, { key: "holds", label: "motivo", fmt: v => v.split("|").map(x => HOLD[x] || x).join("; ") }], rows: T.retenidas, searchable: false })));
  main.appendChild(section("candidatas", "Candidatas", g7));

  // propuesta
  const g8 = h("div", { class: "grid" });
  g8.appendChild(card(12, "Propuesta NUL01-R v1 (campo D34 ausente tratado como desconocido), sin aplicar", "Una regla para la rama retrospectiva, con lista congelada y autorización expresa, en la misma forma que CAP02R a CAP06R.",
    h("div", { class: "prose" },
      h("p", null, "Alcance: las 154 filas del grupo F que siguen pendientes en la rama activa; las dos pólizas de D60 ya fueron corregidas en CAP06R. Referencia: el periodo original más próximo de la misma póliza, cliente y dirección, con capital normal, sin solape, a 1–400 días, con todos los campos D34 conocidos iguales y razón (capital/1000)/referencia entre 0,90 y 1,10; cuando hay anterior y posterior se prefiere la anterior. El campo nulo, en la fila o en la referencia, se registra como desconocido en la bitácora (columna context_unknown_fields) y no se imputa en ningún caso."),
      h("p", null, `Orden sugerido: primero las ${fInt(L.any_direction.by_level.N1_puente_dos_lados)} filas N1 (campo conocido e igual a ambos lados), luego las ${fInt(L.any_direction.by_level.N2_vecino_conocido)} N2 y por último las ${fInt(L.any_direction.by_level.N3_identidad_sin_campo)} N3 (tier B con dos periodos). Si se prefiere una sola autorización, las tres categorías cumplen la misma condición numérica y de identidad; la escalera solo gradúa cuánta evidencia adicional hay sobre el campo que falta.`),
      h("p", null, `Retener las ${fInt(E.held.rows)} filas con referencia contradictoria (tramo ampliado en la póliza) y revisarlas a mano con el mismo criterio que D60. Las ${fInt(L.test2025_rows_in_candidates)} filas de test 2025 entran con apoyo anterior; las ${fInt(L.candidates_with_test2025_reference)} filas de 2024 cuyo apoyo es test 2025 quedan marcadas como respaldo posterior, igual que en CAP02R.`),
      h("p", null, "Por qué es defendible: en los originales, smoke_alarms, security_level y high_value_items nunca cambian entre periodos consecutivos de la misma póliza en la misma dirección (cero cambios en más de 1,1 millones de pares conocidos); smoke_alarms cambia solo con mudanza. La igualdad en ese campo no añade información sobre la escala del capital cuando ya coinciden cliente, dirección y los demás campos. Lo que prueba la escala es la razón de capital frente a la propia historia de la póliza, que en las 152 candidatas queda entre 0,968 y 1,035, exactamente la indexación anual que muestra el archivo."),
      h("p", null, "Qué haría revisarla: un cambio documentado del generador de datos en el que un campo nulo signifique otra cosa que 'no registrado'; una fila cuya razón quede fuera de banda; un siniestro aceptado por encima del capital hipotético; o la confirmación de unidades por el organizador, que haría innecesaria toda la rama."),
      h("p", { class: "note" }, "Lo que no propone: no rellena nulos, no toca la base ni current_dataset.json, no amplía la ventana de 400 días, no aplica cascadas, no usa primas ni siniestros para decidir y no cambia el guard de predictores. Es una propuesta sin aplicar; cualquier aplicación necesita autorización expresa del participante y seguiría el flujo apply/verify/finalize de Limpieza."))));
  main.appendChild(section("propuesta", "Propuesta", g8));

  // controles
  const g9 = h("div", { class: "grid" });
  g9.appendChild(card(12, `Controles de la corrida (${E.summary.checks_passed}/${E.summary.checks_total})`, "Hashes de originales y de las tablas de Codex, derivación de la cohorte, reproducción de los conteos de D56, condiciones numéricas y de identidad.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "id", label: "id" }, { key: "name", label: "comprobación" }, { key: "passed", label: "resultado", fmt: v => h("span", { class: "status " + (v ? "ok" : "fail") }, h("span", { class: "ic" }, v ? "✓" : "✕"), v ? "pasa" : "falla") }, { key: "observed", label: "observado", fmt: v => typeof v === "object" ? JSON.stringify(v) : String(v) }], rows: E.checks, searchable: false, pageSize: 30 }))));
  g9.appendChild(card(12, "Procedencia", null, kv([["Corrida", h("span", { class: "mono" }, E.run_id)], ["Rama retrospectiva validada", h("span", { class: "mono" }, E.provenance.retrospective_run + " (" + E.provenance.retrospective_status + ")")], ["Capa base", h("span", { class: "mono" }, E.provenance.base_run)], ...Object.entries(E.provenance.inputs_sha256).map(([k, v]) => [k, h("span", { class: "mono" }, v)]), ["Entorno", `Python ${E.environment.python}, pandas ${E.environment.pandas}`]])));
  main.appendChild(section("controles", "Controles", g9));
  document.getElementById("footer").textContent = `Informe construido el ${DATA.built_utc} a partir de evidencia.json de la corrida ${E.run_id}. Revisión propia asistida por IA; no se modificaron datos ni índices; la lista de candidatas no está aplicada.`;
}
document.querySelectorAll("[data-theme]").forEach(b => b.addEventListener("click", () => { document.documentElement.dataset.theme = b.dataset.theme; try { localStorage.setItem("iaa.theme", b.dataset.theme); } catch (e) {} document.querySelectorAll("[data-theme]").forEach(x => x.setAttribute("aria-pressed", String(x === b))); }));
try { const th = localStorage.getItem("iaa.theme"); if (th) document.documentElement.dataset.theme = th; } catch (e) {}
document.querySelectorAll("[data-theme]").forEach(x => x.setAttribute("aria-pressed", String(x.dataset.theme === (document.documentElement.dataset.theme || "auto"))));
render();
</script>
</body>
</html>
"""

if __name__ == "__main__":
    main()
