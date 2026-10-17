"""Construye informe.html (archivo único, sin red) a partir de la corrida vigente de revisar_pendientes_restantes.py.

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
            run = sorted((HERE / "runs").glob("rest_*"))[-1]
    evidence = json.loads((run / "evidencia.json").read_text("utf-8"))
    tables = {name: read_csv(run / "tables" / f"{name}.csv") for name in
              ["historias", "referencias", "siniestros", "candidatas_NO_APLICADAS", "sin_propuesta", "evaluacion", "polizas_vecinas", "controles"]}
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
<title>Capitales pendientes restantes · IAA 2026</title>
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
    <div class="brand"><h1>Los otros 265 capitales pendientes · revisión de Claude</h1><div class="sub" id="subtitle"></div></div>
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
const GROUP = { G_other_conflicts: "G · otros conflictos", C_no_original_normal_reference: "C · sin referencia original", E_TW_dependency: "E · dependientes de T/W", D_CAP01_dependency_only: "D · apoyo dependiente de CAP01", A_retrospective_D34: "A · discrepancia C48613718" };
const PROPOSAL = { "MOV01-R": "MOV01-R · mudanza (contenidos)", "END01-R": "END01-R · ampliación con error de escala", "END02-R": "END02-R · base con ampliación adyacente", "TW01-R": "TW01-R · alias t/w", "CHAIN01-R": "CHAIN01-R · cadena con ancla original", "NUL01-R": "NUL01-R (D63)" };
const PROPOSAL_CLASS = { "MOV01-R": "n2", "END01-R": "n3", "END02-R": "n1", "TW01-R": "n1", "CHAIN01-R": "n3", "NUL01-R": "n2" };
const HOLD = { sin_referencia_en_la_poliza: "sin referencia en la póliza", referencia_contradictoria_no_ampliada: "contradicción que no es ampliación", siniestro_por_encima_del_capital_hipotetico: "siniestro por encima del capital hipotético", ampliacion_fuera_de_banda: "ampliación fuera de banda", sin_criterio: "sin criterio" };
const DIR = { prior: "anterior", later: "posterior" };
const REASON = { otra_direccion: "otra dirección", otra_direccion_y_otros_campos: "otra dirección y otros campos", "ctx_ok+compatible": "contexto igual, compatible", "ctx_ok+distancia": "contexto igual, a más de 400 días", "ctx_ok+razon": "contexto igual, razón fuera de banda", "ctx_ok+distancia+razon": "contexto igual, lejos y fuera de banda", "ctx_ok+solape": "contexto igual, solapa", "tw+compatible": "solo t/w, compatible", "tw+distancia": "solo t/w, a más de 400 días", "tw+distancia+razon": "solo t/w, lejos y fuera de banda", "tw+razon": "solo t/w, razón fuera de banda" };
const reasonEs = s => s ? s.split("; ").map(x => REASON[x] || (x.startsWith("otro_campo:") ? "otros campos: " + x.slice(11) : x)).join("; ") : "sin referencias normales";
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
const proposalBadge = (p, hold) => p ? h("span", { class: `badge ${PROPOSAL_CLASS[p] || ""}` }, PROPOSAL[p] || p) : h("span", { class: "badge hold" }, HOLD[hold] || hold || "sin propuesta");
const fieldsEs = s => s ? s.split("|").join(", ") : "ninguno";
function historyTable(rows, focusId, refId) {
  const line = rows[0].line;
  const cols = [{ key: "row_id", label: "row_id" }, { key: "source_table", label: "tabla", fmt: v => v.replace("policies_", "").replace("test_", "test ") }, { key: "period_start", label: "inicio" }, { key: "period_end", label: "fin" }, { key: "exposure", label: "exposición", num: true, fmt: v => fNum(v, 4) },
    { key: "sum_insured", label: "capital original", num: true, fmt: v => fNum(v, 0) }, { key: "base_capital", label: "capital base", num: true, fmt: (v, r) => v === r.sum_insured ? "=" : fNum(v, 0) }, { key: "branch_capital", label: "capital rama", num: true, fmt: (v, r) => v === r.sum_insured ? "=" : fNum(v, 0) },
    { key: "address_id", label: "dirección" }, { key: "renewal_decision", label: "decisión", fmt: (v, r) => v || (r.test2025 ? "test 2025" : "–") }, { key: "renewal_count", label: "renov.", num: true },
    ...FIELD_COLS[line].map(f => ({ key: f, label: f, fmt: cell })), { key: "written_premium", label: "prima", num: true, fmt: v => fNum(v, 2) }];
  return h("div", { class: "wrapcells" }, dataTable({ columns: cols, rows, searchable: false, pageSize: 50, rowClass: r => r.row_id === focusId ? "focus" : r.row_id === refId ? "ref" : "" }));
}
function refsTable(rows) {
  const cols = [{ key: "reference_row_id", label: "referencia" }, { key: "direction", label: "sentido", fmt: v => DIR[v] }, { key: "start_gap_days", label: "días", num: true }, { key: "reference_capital_CU", label: "capital ref.", num: true, fmt: v => fNum(v, 0) },
    { key: "reference_normal", label: "normal", fmt: v => v ? "sí" : "no" }, { key: "ratio_hypothetical_over_reference", label: "(÷1000)/ref", num: true, fmt: v => fNum(v, 4) },
    { key: "same_address", label: "misma dirección", fmt: v => v ? "sí" : "no" }, { key: "in_window", label: "ventana 1–400", fmt: v => v ? "sí" : "no" }, { key: "in_band", label: "banda 0,90–1,10", fmt: v => v ? "sí" : "no" }, { key: "changed_fields", label: "cambian", fmt: v => v || "–" }, { key: "unknown_fields", label: "desconocidos", fmt: v => v || "–" },
    { key: "tw_alias_only", label: "solo t/w", fmt: v => v ? "sí" : "no" }, { key: "endorsed_reference", label: "periodo ampliado", fmt: (v, r) => v ? `sí (×${fNum(r.reference_endorsement_ratio, 3)})` : "no" }, { key: "reference_corrected_by", label: "corregida por", fmt: v => v || "–" }];
  return dataTable({ columns: cols, rows, searchable: false, pageSize: 20 });
}
function policyPanel(policyId, focusId) {
  const rows = T.historias.filter(r => r.policy_id === policyId);
  const ev = T.evaluacion.find(r => r.row_id === focusId);
  const refs = T.referencias.filter(r => r.focus_row_id === focusId);
  const claims = T.siniestros.filter(c => c.policy_id === policyId);
  const neigh = T.polizas_vecinas.filter(n => n.focus_row_id === focusId);
  const box = h("div");
  const meta = h("div", { class: "meta" }, proposalBadge(ev.proposal, ev.hold), h("span", { class: "badge" }, GROUP[ev.group]), h("span", { class: "badge" }, LINE[ev.line]), h("span", { class: "badge" }, "motivos: " + reasonEs(ev.reasons)));
  if (ev.chosen_reference_row_id) meta.appendChild(h("span", { class: "badge" }, `referencia ${ev.chosen_reference_row_id} (${DIR[ev.chosen_direction]}, ${ev.chosen_gap_days} días, razón ${fNum(ev.chosen_ratio, 4)}${ev.chosen_same_address === false ? ", otra dirección" : ""})`));
  if (ev.follows_mid_term_change) meta.appendChild(h("span", { class: "badge" }, `sigue a una ampliación: (÷1000)/previo = ${fNum(ev.endorsement_ratio_hypothetical_over_prior, 3)}` + (ev.reversion_next_over_prior ? `; siguiente/previo = ${fNum(ev.reversion_next_over_prior, 3)}` : "")));
  if (ev.chain_detail) { const d = JSON.parse(ev.chain_detail); meta.appendChild(h("span", { class: "badge" }, `cadena: ancla ${d.anchor_row_id} (${d.anchor_gap_days} días) → ${d.intermediate_row_id} corregida por ${d.intermediate_corrected_by} (${fNum(d.ratio_intermediate_over_anchor, 3)}) → fila (${fNum(d.ratio_focus_over_intermediate, 3)}); fila/ancla ${fNum(d.ratio_focus_over_anchor, 3)}`)); }
  box.appendChild(meta);
  box.appendChild(timeline(rows, focusId, ev.chosen_reference_row_id));
  box.appendChild(h("h4", null, "Historia completa de la póliza (originales; capital base y de la rama cuando difieren)"));
  box.appendChild(historyTable(rows, focusId, ev.chosen_reference_row_id));
  box.appendChild(h("h4", null, "Todas las referencias de la póliza"));
  if (refs.length) box.appendChild(refsTable(refs)); else box.appendChild(h("p", { class: "note" }, "La póliza no tiene ningún otro periodo."));
  if (claims.length) { box.appendChild(h("h4", null, "Siniestros de la póliza (capa base)")); box.appendChild(dataTable({ columns: [{ key: "claim_id", label: "siniestro" }, { key: "peril", label: "peligro" }, { key: "loss_date", label: "ocurrencia" }, { key: "status", label: "estado" }, { key: "incurred_to_date", label: "incurrido", num: true, fmt: v => fNum(v, 2) }, { key: "recoveries", label: "recuperos", num: true, fmt: v => fNum(v, 2) }, { key: "assigned_row_id", label: "periodo asignado" }, { key: "period_extreme", label: "periodo extremo", fmt: v => v ? "sí" : "no" }], rows: claims, searchable: false })); }
  else box.appendChild(h("p", { class: "note" }, "Sin siniestros registrados para esta póliza en la capa base."));
  if (neigh.length) { box.appendChild(h("h4", null, "Otra póliza de hogar del mismo cliente y dirección (solo descripción)")); box.appendChild(dataTable({ columns: [{ key: "other_policy_id", label: "póliza" }, { key: "other_line", label: "ramo", fmt: v => LINE[v] }, { key: "other_row_id", label: "periodo" }, { key: "other_period_start", label: "inicio" }, { key: "other_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "hypothetical_CU", label: "÷1000 de la pendiente", num: true, fmt: v => fNum(v, 0) }, { key: "ratio_contents_over_buildings_hypothetical", label: "contenidos/edificios (÷1000)", num: true, fmt: v => fNum(v, 3) }, { key: "percentile_in_population", label: "percentil en la población", num: true, fmt: v => fPct(v, 1) }, { key: "ratio_recorded", label: "con el capital registrado", num: true, fmt: v => fNum(v, 4) }], rows: neigh, searchable: false })); }
  return box;
}
function render() {
  const main = document.getElementById("main");
  const S = E.summary, C = E.cohort, G = E.global_statistics, K = E.candidates_NOT_APPLIED, NR = E.no_reference_percentiles, NB = E.neighbour_evidence, P = E.premium_diagnostic;
  const byGroup = S.by_group, byProp = S.by_proposal;
  document.getElementById("subtitle").textContent = `Corrida ${E.run_id} · rama activa ${E.provenance.retrospective_run.split("/").pop()} · ${E.checks_summary.checks_passed}/${E.checks_summary.checks_total} controles · sin cambios de datos`;
  const toc = document.getElementById("toc");
  [["resumen", "Resumen"], ["grupos", "Los cinco grupos"], ["evidencia", "Evidencia global"], ["grupoG", "Grupo G"], ["sinref", "Sin referencia"], ["otros", "Grupos E, D y A"], ["propuestas", "Propuestas"], ["casos", "Casos"], ["explorador", "Explorador"], ["candidatas", "Candidatas"], ["controles", "Controles"]].forEach(([id, name]) => toc.appendChild(h("a", { href: "#" + id }, name)));

  // resumen
  const hero = card(12, null, null, h("div", { class: "hero" }, h("div", { class: "n" }, fInt(C.rows)), h("div", { class: "d" },
    h("p", null, h("b", null, "capitales pendientes fuera del grupo F"), ` en ${fInt(C.policies)} pólizas de hogar y ${fInt(C.history_rows)} periodos leídos desde los originales: ${fInt(C.groups.G_other_conflicts)} de otros conflictos, ${fInt(C.groups.C_no_original_normal_reference)} sin referencia original habitual, ${fInt(C.groups.E_TW_dependency)} dependientes de T/W, ${fInt(C.groups.D_CAP01_dependency_only)} con apoyo dependiente de CAP01 y la discrepancia C48613718.`),
    h("p", null, `Con la misma historia de cada póliza y tres comportamientos medidos en todo el archivo (qué pasa con el capital al mudarse, qué es una ampliación a mitad de año y qué es el alias t/w) ${fInt(K.rows)} filas quedan cubiertas por cinco criterios explícitos con lista congelada, y ${fInt(S.no_reference_rows)} no tienen en su póliza nada con qué compararse: para ellas la propuesta es de modelado, no de corrección.`),
    h("p", { class: "note" }, "Revisión propia asistida por IA, sin cambios de datos, índices ni corridas de Codex; ninguna lista está aplicada."))));
  const tiles = h("div", { class: "tiles" },
    tile("Con criterio y lista congelada", fInt(K.rows), Object.entries(K.by_proposal).map(([k, v]) => `${k.replace("-R", "")} ${v}`).join(" · ")),
    tile("Sin referencia en la póliza", fInt(S.no_reference_rows), `${fInt(S.no_reference_by_line.buildings)} edificios · ${fInt(S.no_reference_by_line.contents)} contenidos · ${fInt(S.no_reference_test2025_rows)} en test 2025`),
    tile("Con apoyo anterior", fInt(K.prior_supported), `${fInt(K.later_supported)} solo posterior`),
    tile("Filas de test 2025 con criterio", fInt(K.test2025_rows), "27 de las 123 filas de test pendientes"),
    tile("Mudanzas en contenidos", fInt(G.contents.pairs_address_change), `capital idéntico en el ${fPct(G.contents.pairs_address_change_ratio_exactly_1, 1)}`),
    tile("Ampliaciones en contenidos", fInt(G.contents.periods_after_mid_term_change_same_address), `suben ×1,20–1,60 y la renovación vuelve al nivel base`),
    tile("Alias t/w en edificios", fInt(G.buildings.tw_alias_pairs_same_address), `razón en banda en el ${fPct(G.buildings.tw_alias_pairs_in_band, 0)}`),
    tile("Controles", `${E.checks_summary.checks_passed}/${E.checks_summary.checks_total}`, "originales con hash verificado"));
  main.appendChild(section("resumen", "Resumen", h("div", { class: "grid" }, hero, card(12, "Cifras clave", null, tiles))));

  // grupos
  const g1 = h("div", { class: "grid" });
  const groupRows = Object.entries(byGroup).map(([g, s]) => ({ group: GROUP[g], rows: s.rows, buildings: s.by_line.buildings || 0, contents: s.by_line.contents || 0, test: s.test2025_rows, proposals: Object.entries(s.proposals).map(([k, v]) => `${k}: ${v}`).join(" · "), holds: Object.entries(s.holds).map(([k, v]) => `${HOLD[k] || k}: ${v}`).join(" · ") || "–" }));
  g1.appendChild(card(12, "Qué pide resolver cada grupo y qué sale de la revisión", "Los grupos son los de D48 que siguen pendientes en la rama activa. Cada fila se evaluó con todas las referencias de su póliza; la columna de propuestas resume el criterio que la cubriría.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "group", label: "grupo" }, { key: "rows", label: "filas", num: true, fmt: fInt }, { key: "buildings", label: "edificios", num: true, fmt: fInt }, { key: "contents", label: "contenidos", num: true, fmt: fInt }, { key: "test", label: "test 2025", num: true, fmt: fInt }, { key: "proposals", label: "propuestas" }, { key: "holds", label: "sin propuesta" }], rows: groupRows, searchable: false }))));
  main.appendChild(section("grupos", "Los cinco grupos", g1));

  // evidencia global
  const g2 = h("div", { class: "grid" });
  g2.appendChild(card(4, "Mudanza: edificios recalcula, contenidos conserva", `Razón capital(t)/capital(t−1) entre periodos consecutivos de la misma póliza con cambio de dirección, filas normales.`,
    barChart({ cats: ["edificios", "contenidos"], series: [{ name: "razón exactamente 1", color: COLORS.accent, values: [0, G.contents.pairs_address_change_ratio_exactly_1] }, { name: "dentro de 0,90–1,10", color: COLORS.raw, values: [G.buildings.pairs_address_change_in_band, G.contents.pairs_address_change_in_band] }], fmt: v => fPct(v, 1), tickFmt: v => fPct(v, 0) }),
    h("p", { class: "note" }, `Edificios: ${fInt(G.buildings.pairs_address_change)} pares con mudanza, razón en banda en el ${fPct(G.buildings.pairs_address_change_in_band, 1)} (percentiles 10 y 90: ${fNum(G.buildings.pairs_address_change_ratio_quantiles["0.1"], 2)} y ${fNum(G.buildings.pairs_address_change_ratio_quantiles["0.9"], 2)}). Contenidos: ${fInt(G.contents.pairs_address_change)} pares, razón igual a 1 en el ${fPct(G.contents.pairs_address_change_ratio_exactly_1, 2)}.`)));
  const q = G.contents.after_mid_term_change_ratio_quantiles;
  g2.appendChild(card(4, "Ampliación a mitad de año en contenidos", `En ${fInt(G.contents.periods_after_mid_term_change_same_address)} periodos que siguen a un mid_term_change en la misma dirección, el capital sube entre 1,20 y 1,60 veces (nunca baja) y en la renovación siguiente vuelve al nivel base indexado.`,
    barChart({ cats: ["p1", "p5", "p25", "p50", "p75", "p95", "p99"], series: [{ name: "razón ampliación/base", color: COLORS.contents, values: ["0.01", "0.05", "0.25", "0.5", "0.75", "0.95", "0.99"].map(k => q[k]) }], fmt: v => fNum(v, 3), tickFmt: v => fNum(v, 1) }),
    h("p", { class: "note" }, `Reversión siguiente/base: entre ${fNum(G.contents.reversion_next_over_base_quantiles["0.01"], 3)} y ${fNum(G.contents.reversion_next_over_base_quantiles["0.99"], 3)} en ${fInt(G.contents.endorsements_with_next_period_same_address)} casos (${fPct(G.contents.reversion_next_over_base_in_band, 0)} en banda). La etiqueta mid_term_change coincide con la firma estructural (periodo contiguo, misma dirección, mismo contador) en el ${fPct(G.contents.structural_signature.share_mid_term_change_given_contiguous_same_counter, 1)} y ${fPct(G.contents.structural_signature.share_contiguous_same_counter_given_mid_term_change, 1)} de los casos, lo que permite reconocer ampliaciones en test 2025.`)));
  g2.appendChild(card(4, "El alias t/w no toca el capital", `${fInt(G.buildings.tw_alias_pairs_same_address)} pares consecutivos de edificios en la misma dirección cambian de t a w (el ${fPct(G.buildings.tw_alias_pairs_starting_2023_01_01, 1)} el 1 de enero de 2023); su razón de capital es la misma que sin cambio.`,
    barChart({ cats: ["sin cambio de código", "cambio t→w"], series: [{ name: "razón en banda", color: COLORS.buildings, values: [G.buildings.pairs_same_address_no_construction_change_in_band, G.buildings.tw_alias_pairs_in_band] }], fmt: v => fPct(v, 2), tickFmt: v => fPct(v, 0) }),
    h("p", { class: "note" }, `Mediana ${fNum(G.buildings.tw_alias_ratio_quantiles["0.5"], 3)}, percentiles 1 y 99 en ${fNum(G.buildings.tw_alias_ratio_quantiles["0.01"], 3)} y ${fNum(G.buildings.tw_alias_ratio_quantiles["0.99"], 3)}; no hay ningún otro cambio de construcción en la misma dirección en todo el archivo.`)));
  main.appendChild(section("evidencia", "Evidencia global", g2));

  // grupo G
  const g3 = h("div", { class: "grid" });
  const gs = byGroup.G_other_conflicts;
  const reasonCats = Object.entries(gs.reasons).sort((a, b) => b[1] - a[1]);
  g3.appendChild(card(6, "Por qué las 138 filas no cumplían D34", "Motivos encontrados al comparar cada fila con todas las referencias normales de su póliza (una fila puede tener varios).", h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "r", label: "motivos de la fila" }, { key: "n", label: "filas", num: true, fmt: fInt }], rows: reasonCats.map(([r, n]) => ({ r: reasonEs(r), n })), searchable: false, pageSize: 20 }))));
  const gp = Object.entries(gs.proposals).sort((a, b) => b[1] - a[1]);
  g3.appendChild(card(6, "Lectura: errores de escala frente a cambios reales de cobertura", null, h("div", { class: "prose" },
    h("p", null, `Mudanzas (${fInt(gs.reasons.otra_direccion + (gs.reasons.otra_direccion_y_otros_campos || 0) + (gs.reasons["otra_direccion; otra_direccion_y_otros_campos"] || 0))} filas): el periodo extremo es el único en su dirección. En contenidos, el capital de la dirección anterior o siguiente coincide exactamente con el capital dividido entre mil en las ${fInt(gs.proposals["MOV01-R"])} filas (MOV01-R). En edificios, la otra casa tiene otro capital: ${fInt(gs.holds.sin_referencia_en_la_poliza)} filas se quedan sin referencia.`),
    h("p", null, `Ampliación con error de escala (${fInt(gs.proposals["END01-R"])} filas, END01-R): el periodo extremo sigue a un mid_term_change y, dividido entre mil, queda entre ${fNum(S.endorsement_ratio_quantiles_END01["0.0"], 2)} y ${fNum(S.endorsement_ratio_quantiles_END01["1.0"], 2)} veces el nivel previo, igual que cualquier ampliación del archivo; en ${fInt(S.END01_sandwich)} de ellas la renovación siguiente vuelve al nivel base (siguiente/previo entre ${fNum(S.reversion_ratio_quantiles_END01["0.0"], 3)} y ${fNum(S.reversion_ratio_quantiles_END01["1.0"], 3)}). Es un cambio real de cobertura y, además, un error de escala.`),
    h("p", null, `Nivel base con ampliación adyacente (${fInt(gs.proposals["END02-R"])} filas, END02-R): el periodo extremo es el nivel base; una referencia próxima contradice porque es un periodo ampliado (razón (÷1000)/ampliado entre ${fNum(S.contradiction_ratio_quantiles_END02["0.0"], 3)} y ${fNum(S.contradiction_ratio_quantiles_END02["1.0"], 3)}) y las demás renovaciones encajan. Es el patrón de las dos pólizas de D60.`),
    h("p", null, `Quedan una fila cubierta por el alias t/w (TW01-R) y una cadena de dos periodos extremos consecutivos tras una mudanza, el segundo ya corregido por la rama (CHAIN01-R).`))));
  main.appendChild(section("grupoG", "Grupo G: otros conflictos", g3));

  // sin referencia
  const g4 = h("div", { class: "grid" });
  const pctB = NR.buildings.percentile_of_hypothetical_in_normal_distribution_quantiles, pctC = NR.contents.percentile_of_hypothetical_in_normal_distribution_quantiles;
  g4.appendChild(card(6, `${fInt(S.no_reference_rows)} filas sin nada con qué compararse en su póliza`, `${fInt(byGroup.C_no_original_normal_reference.rows)} del grupo C (pólizas de uno o dos periodos, ${fInt(byGroup.C_no_original_normal_reference.test2025_rows)} de ellas en test 2025) y ${fInt(gs.holds.sin_referencia_en_la_poliza)} de edificios con mudanza. Dividido entre mil, su capital cae en cualquier punto de la distribución normal del ramo, no en un extremo.`,
    barChart({ cats: ["mín", "p10", "p25", "p50", "p75", "p90", "máx"], series: [{ name: "edificios", color: COLORS.buildings, values: ["0.0", "0.1", "0.25", "0.5", "0.75", "0.9", "1.0"].map(k => pctB[k]) }, { name: "contenidos", color: COLORS.contents, values: ["0.0", "0.1", "0.25", "0.5", "0.75", "0.9", "1.0"].map(k => pctC[k]) }], fmt: v => fPct(v, 1), tickFmt: v => fPct(v, 0) }),
    h("p", { class: "note" }, `Percentil del capital ÷1000 dentro de la distribución de capitales normales del ramo. Edificios: de ${fNum(NR.buildings.hypothetical_min_CU, 0)} a ${fNum(NR.buildings.hypothetical_max_CU, 0)} CU (máximo normal ${fNum(NR.buildings.normal_max_CU, 0)}); contenidos: de ${fNum(NR.contents.hypothetical_min_CU, 0)} a ${fNum(NR.contents.hypothetical_max_CU, 0)} (máximo normal ${fNum(NR.contents.normal_max_CU, 0)}).`)));
  const nbq = NB.percentile_quantiles_hypothetical;
  g4.appendChild(card(6, "La póliza vecina del mismo cliente y dirección", `${fInt(NB.no_reference_rows_with_neighbour)} de las ${fInt(S.no_reference_rows)} filas tienen, en la misma dirección y fechas, una póliza del otro ramo de hogar del mismo cliente, ninguna extrema. La razón contenidos/edificios calculada con el capital ÷1000 cae dentro del 90 % central de la población (${fInt(NB.population.pairs_same_customer_address_overlap_normal)} pares normales) en el ${fPct(NB.share_within_population_p05_p95, 1)} de los casos; con el capital registrado la razón sería mil veces mayor o menor.`,
    barChart({ cats: ["mín", "p10", "p25", "p50", "p75", "p90", "máx"], series: [{ name: "percentil en la población", color: COLORS.violet, values: ["0.0", "0.1", "0.25", "0.5", "0.75", "0.9", "1.0"].map(k => nbq[k]) }], fmt: v => fPct(v, 1), tickFmt: v => fPct(v, 0) }),
    h("p", { class: "note" }, `Población: razón contenidos/edificios con mediana ${fNum(NB.population.contents_over_buildings_ratio_quantiles["0.5"], 3)}, percentiles 5 y 95 en ${fNum(NB.population.contents_over_buildings_ratio_quantiles["0.05"], 3)} y ${fNum(NB.population.contents_over_buildings_ratio_quantiles["0.95"], 3)}. Solo descripción: no decide ninguna corrección.`)));
  g4.appendChild(card(12, "Qué se propone para estas filas: una decisión de modelado, no una corrección de datos", null, h("div", { class: "prose" },
    h("p", null, `Sin un periodo comparable en la póliza, ninguna regla de la familia D34 puede certificar la escala fila a fila, y el proyecto ya rechazó dividir por umbral de forma automática (D48). Lo que sí puede decidirse es cómo las verá el modelo. La propuesta es una transformación documentada en la construcción de F0, aplicada a cualquier capital que siga pendiente al entrenar o predecir: usar sum_insured/1000 como valor del predictor cuando el capital supera el umbral del ramo y añadir una marca capital_scale_suspect; la tabla de datos no cambia y la marca queda fuera de los predictores como las columnas audit_*.`),
    h("p", null, `Lo que la respalda: la nube extrema está separada de la normal por un hueco de 49 veces en edificios y 24 en contenidos (D59); los capitales ÷1000 de estas filas caen a lo largo de toda la distribución normal; la póliza vecina del mismo cliente da razones contenidos/edificios normales; y, en los ${fInt(P.buildings.focus_full_year_rows + P.contents.focus_full_year_rows)} periodos pendientes de año completo de toda la cohorte, la prima por mil de capital calculada con el capital ÷1000 queda donde la de las filas normales de año completo (medianas ${fNum(P.buildings.focus_full_year_premium_per_1000_hypothetical_capital_quantiles["0.5"], 3)} frente a ${fNum(P.buildings.normal_full_year_rows_premium_per_1000_capital_quantiles["0.5"], 3)} en edificios y ${fNum(P.contents.focus_full_year_premium_per_1000_hypothetical_capital_quantiles["0.5"], 3)} frente a ${fNum(P.contents.normal_full_year_rows_premium_per_1000_capital_quantiles["0.5"], 3)} en contenidos; en periodos cortos la prima no está prorrateada de forma documentada y no se compara).`),
    h("p", null, `La alternativa anotada en D48, tratar el capital como no disponible con un imputador entrenado solo en entrenamiento, sigue abierta y conviene compararla dentro de las particiones temporales. Las ${fInt(S.no_reference_test2025_rows)} filas de test 2025 son las que más pesan en esa decisión: en ellas el modelo tiene que predecir con el capital que se le dé.`))));
  main.appendChild(section("sinref", "Sin referencia en la póliza", g4));

  // E, D, A
  const g5 = h("div", { class: "grid" });
  g5.appendChild(card(4, `Grupo E: ${fInt(byGroup.E_TW_dependency.rows)} dependientes de T/W`, "Todas de edificios. Su única referencia compatible en la misma dirección difiere solo en el código de construcción: t en 2021–2022 y w desde 2023.", h("div", { class: "prose" }, h("p", null, `TW01-R: para la comparación de escala, t y w se tratan como el mismo código cuando el resto del contexto coincide; los datos no se modifican y CON01 no se activa. En todo el archivo el cambio t→w no altera el capital (razón en banda en el ${fPct(G.buildings.tw_alias_pairs_in_band, 0)} de ${fInt(G.buildings.tw_alias_pairs_same_address)} pares). ${fInt(byProp["TW01-R"].rows)} filas (${fInt(byProp["TW01-R"].prior_supported)} con apoyo anterior), razones entre ${fNum(byProp["TW01-R"].ratio_quantiles["0.0"], 4)} y ${fNum(byProp["TW01-R"].ratio_quantiles["1.0"], 4)}.`))));
  g5.appendChild(card(4, `Grupo D: ${fInt(byGroup.D_CAP01_dependency_only.rows)} con apoyo dependiente de CAP01`, "Dos filas de test 2025 cuya referencia próxima es la fila de 2024 ya corregida por CAP01.", h("div", { class: "prose" }, h("p", null, "CHAIN01-R evita la cadena circular exigiendo un ancla original normal en la misma dirección a más de 400 días y hasta dos años, y razón en banda en cada paso: ancla → fila corregida → fila pendiente, y fila pendiente → ancla. En las dos pólizas la cadena es 2023 original → 2024 corregida → 2025 pendiente, con razones de 1,03 por paso y 1,06 sobre el ancla. Es la lógica de DIST01-R con una intermedia corregida en lugar de una intermedia con faltantes; se marca la dependencia en la bitácora."))));
  g5.appendChild(card(4, "Grupo A: C48613718", "La discrepancia que D51 dejó pendiente: la referencia anterior más próxima con contexto igual queda fuera de la banda.", h("div", { class: "prose" }, h("p", null, "La historia lo explica: 28.200 en 2021, 28.800 hasta septiembre de 2022, un tramo ampliado de 40.500 hasta diciembre, 29.300.000 en 2023, 29.900 en 2024 y 30.500 en 2025. El tramo ampliado es la discrepancia; la renovación de 2024 (0,980) y la base de 2022 (1,017, con security_level nulo) encajan con 29.300. Entra en END02-R como las dos pólizas de D60, y el nulo de la referencia inicial se registra como desconocido, igual que en NUL01-R."))));
  main.appendChild(section("otros", "Grupos E, D y A", g5));

  // propuestas
  const g6 = h("div", { class: "grid" });
  const propRows = [
    ["MOV01-R", "Contenidos: referencia original normal de la misma póliza y cliente en otra dirección, demás campos conocidos iguales, ventana 1–400, razón 0,90–1,10.", "Que el capital de contenidos se conserve al mudarse: lo hace exactamente en el 99,8 % de 34.548 mudanzas. En edificios no aplica."],
    ["END01-R", "Contenidos: periodo que sigue sin hueco a un periodo normal de la misma dirección con el mismo contador (mid_term_change), contexto conocido igual; (÷1000)/previo dentro de 1,15–1,65. Subnivel con reversión observada.", "Que el periodo sea una ampliación real además de un error de escala; la banda viene de 13.055 ampliaciones del archivo (1,20–1,60). Sin reversión observada en 8 filas (fin de póliza o test)."],
    ["END02-R", "Referencia compatible (nulos como desconocidos) y toda contradicción es un periodo ampliado; la ampliación se conserva.", "Generaliza MANUAL_ENDORSE01-R (D60/D61) con condición explícita; incluye C48613718."],
    ["TW01-R", "Edificios: referencia en la misma dirección que solo difiere en t/w, ventana 1–400, razón 0,90–1,10.", "Que t y w sean el mismo código para la escala: 18.202 pares sin ningún efecto en el capital. No unifica los códigos en los datos ni activa CON01."],
    ["CHAIN01-R", "Ancla original normal a más de 400 días y hasta dos años en la misma dirección; intermedia corregida por CAP01 o la rama; razón en banda en cada paso.", "Depende de una corrección previa; se registra la dependencia. Dos de tres filas son de test 2025."],
  ].map(([p, def, risk]) => ({ p, def, risk, rows: byProp[p].rows, groups: Object.entries(byProp[p].by_group).map(([k, v]) => `${k.split("_")[0]} ${v}`).join(" · "), prior: byProp[p].prior_supported, later: byProp[p].later_supported, test: byProp[p].test2025_rows, hash: K.sha256_by_proposal[p].slice(0, 12) + "…" }));
  g6.appendChild(card(12, "Cinco criterios con lista congelada, sin aplicar", "Todos conservan las condiciones numéricas y temporales de D34 y cambian una sola cosa cada uno, medida en todo el archivo. Orden de prioridad cuando una fila cumple varios: END02, MOV01, END01, TW01, CHAIN01.",
    h("div", { class: "wrapcells ladder" }, dataTable({ columns: [{ key: "p", label: "criterio" }, { key: "def", label: "qué exige" }, { key: "risk", label: "qué asume" }, { key: "rows", label: "filas", num: true, fmt: fInt }, { key: "groups", label: "grupos" }, { key: "prior", label: "apoyo anterior", num: true, fmt: fInt }, { key: "later", label: "solo posterior", num: true, fmt: fInt }, { key: "test", label: "test 2025", num: true, fmt: fInt }, { key: "hash", label: "hash lista" }], rows: propRows, searchable: false })),
    h("div", { class: "chips", style: "margin-top:12px" }, h("span", { class: "chip" }, h("b", null, fInt(K.rows)), "candidatas en total"), h("span", { class: "chip" }, h("b", null, fInt(K.prior_supported)), "con apoyo anterior"), h("span", { class: "chip" }, h("b", null, fInt(K.test2025_rows)), "filas de test 2025"), h("span", { class: "chip" }, h("b", null, fInt(S.no_reference_rows)), "sin referencia: decisión de modelado"))));
  g6.appendChild(card(12, "Qué no cambia en ninguna propuesta", null, h("div", { class: "prose" }, h("ul", null,
    h("li", null, "Solo cambiaría sum_insured, siempre dividido entre mil, en una capa retrospectiva separada de la base, con lista por hash y sin recalcular la selección tras reparar."),
    h("li", null, "Ningún nulo se rellena, ningún código t/w se unifica en los datos, ninguna ampliación se suaviza ni se copia; los periodos ampliados conservan su capital."),
    h("li", null, "No se usan primas, siniestros ni pólizas vecinas para decidir; aparecen solo como diagnóstico."),
    h("li", null, "Las referencias posteriores no son evidencia causal al corte: la rama sigue sin aprobación para backtests por fecha."),
    h("li", null, "Cualquier aplicación necesita autorización expresa del participante y el flujo apply, verify y finalize de Limpieza; las 149 filas sin referencia no entran en ninguna lista de corrección.")))));
  main.appendChild(section("propuestas", "Propuestas", g6));

  // casos
  const g7 = h("div", { class: "grid" });
  const casesBox = h("div", { class: "span-12" });
  E.cases.forEach(c => {
    const box = h("div", { class: "case", id: "caso-" + c.key });
    box.appendChild(h("h4", null, `${c.key} · ${c.title}`));
    box.appendChild(h("p", { class: "why" }, c.why));
    box.appendChild(h("p", null, `Póliza ${c.policy_id} (${LINE[c.line]}, ${GROUP[c.group]}), fila pendiente ${c.row_id}.`));
    box.appendChild(policyPanel(c.policy_id, c.row_id));
    casesBox.appendChild(box);
  });
  g7.appendChild(card(12, `${E.cases.length} casos elegidos por regla, no a mano`, "Cada caso se seleccionó con una condición explícita (primer row_id que la cumple). La fila en naranja es la pendiente; la azul, la referencia elegida; ∅ marca un nulo; las columnas de capital base y rama muestran '=' cuando coinciden con el original."));
  g7.appendChild(casesBox);
  main.appendChild(section("casos", "Casos concretos", g7));

  // explorador
  const g8 = h("div", { class: "grid" });
  const detail = h("div", { style: "margin-top:14px" });
  const exRows = T.evaluacion.map(r => ({ ...r, group_es: GROUP[r.group], line_es: LINE[r.line], reasons_es: reasonEs(r.reasons), dir_es: r.chosen_direction ? DIR[r.chosen_direction] : "–" }));
  g8.appendChild(card(12, "Explorador de las 265 filas", "Busca por grupo, póliza, fila o criterio y pulsa una fila para ver su historia completa, sus referencias, siniestros y póliza vecina.",
    dataTable({ columns: [{ key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "group_es", label: "grupo" }, { key: "line_es", label: "ramo" }, { key: "year", label: "año", num: true }, { key: "original_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "hypothetical_CU", label: "÷1000", num: true, fmt: v => fNum(v, 0) }, { key: "reasons_es", label: "motivos" }, { key: "chosen_reference_row_id", label: "referencia", fmt: v => v || "–" }, { key: "dir_es", label: "sentido" }, { key: "chosen_ratio", label: "razón", num: true, fmt: v => v ? fNum(v, 4) : "–" }, { key: "proposal", label: "propuesta", fmt: (v, r) => proposalBadge(v, r.hold) }], rows: exRows, pageSize: 20, onRow: r => { detail.replaceChildren(h("h4", null, `Póliza ${r.policy_id} · fila ${r.row_id}`), policyPanel(r.policy_id, r.row_id)); detail.scrollIntoView({ behavior: "smooth", block: "start" }); } }), detail));
  main.appendChild(section("explorador", "Explorador", g8));

  // candidatas
  const g9 = h("div", { class: "grid" });
  const candRows = T.candidatas_NO_APLICADAS.map(r => ({ ...r, group_es: GROUP[r.group], line_es: LINE[r.line], dir_es: DIR[r.chosen_direction] }));
  g9.appendChild(card(12, `Listas congeladas (${fInt(K.rows)} filas, no aplicadas)`, `Suma de capitales originales ${fNum(K.sum_original_CU, 0)} CU; hipotéticos ${fNum(K.sum_hypothetical_CU, 0)} CU. Un hash SHA-256 por criterio: ${Object.entries(K.sha256_by_proposal).map(([k, v]) => `${k} ${v.slice(0, 12)}…`).join(" · ")}.`,
    dataTable({ columns: [{ key: "proposal", label: "criterio", fmt: v => proposalBadge(v, "") }, { key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "group_es", label: "grupo" }, { key: "line_es", label: "ramo" }, { key: "source_table", label: "tabla" }, { key: "period_start", label: "inicio" }, { key: "original_capital_CU", label: "capital original", num: true, fmt: v => fNum(v, 0) }, { key: "new_hypothetical_CU", label: "nuevo (÷1000)", num: true, fmt: v => fNum(v, 0) }, { key: "chosen_reference_row_id", label: "referencia" }, { key: "dir_es", label: "sentido" }, { key: "chosen_gap_days", label: "días", num: true }, { key: "chosen_ratio", label: "razón", num: true, fmt: v => fNum(v, 4) }, { key: "chosen_same_address", label: "misma dirección", fmt: v => v ? "sí" : "no" }, { key: "endorsement_ratio_hypothetical_over_prior", label: "(÷1000)/previo", num: true, fmt: v => v ? fNum(v, 3) : "–" }, { key: "reversion_next_over_prior", label: "siguiente/previo", num: true, fmt: v => v ? fNum(v, 3) : "–" }, { key: "chosen_reference_test2025", label: "ref. test 2025", fmt: v => v ? "sí" : "no" }], rows: candRows, pageSize: 20 })));
  const nrRows = T.sin_propuesta.map(r => ({ ...r, group_es: GROUP[r.group], line_es: LINE[r.line], reasons_es: reasonEs(r.reasons) }));
  g9.appendChild(card(12, `Sin referencia en la póliza (${fInt(S.no_reference_rows)} filas)`, "Sin propuesta de corrección; tratamiento de modelado descrito arriba.",
    dataTable({ columns: [{ key: "row_id", label: "fila" }, { key: "policy_id", label: "póliza" }, { key: "group_es", label: "grupo" }, { key: "line_es", label: "ramo" }, { key: "source_table", label: "tabla" }, { key: "year", label: "año", num: true }, { key: "original_capital_CU", label: "capital", num: true, fmt: v => fNum(v, 0) }, { key: "hypothetical_CU", label: "÷1000", num: true, fmt: v => fNum(v, 0) }, { key: "history_rows", label: "periodos", num: true }, { key: "addresses_in_policy", label: "direcciones", num: true }, { key: "reasons_es", label: "motivos" }], rows: nrRows, pageSize: 20 })));
  main.appendChild(section("candidatas", "Candidatas", g9));

  // controles
  const g10 = h("div", { class: "grid" });
  g10.appendChild(card(12, `Controles de la corrida (${E.checks_summary.checks_passed}/${E.checks_summary.checks_total})`, "Hashes de originales, derivación de la cohorte, comportamientos globales y condiciones de cada criterio.",
    h("div", { class: "wrapcells" }, dataTable({ columns: [{ key: "id", label: "id" }, { key: "name", label: "comprobación" }, { key: "passed", label: "resultado", fmt: v => h("span", { class: "status " + (v ? "ok" : "fail") }, h("span", { class: "ic" }, v ? "✓" : "✕"), v ? "pasa" : "falla") }, { key: "observed", label: "observado", fmt: v => typeof v === "object" ? JSON.stringify(v) : String(v) }], rows: E.checks, searchable: false, pageSize: 30 }))));
  g10.appendChild(card(12, "Procedencia", null, kv([["Corrida", h("span", { class: "mono" }, E.run_id)], ["Rama retrospectiva revisada", h("span", { class: "mono" }, E.provenance.retrospective_run + " (" + E.provenance.retrospective_status + ")")], ["Capa base", h("span", { class: "mono" }, E.provenance.base_run)], ["Revisión del grupo F (D63)", h("span", { class: "mono" }, C.group_F_review ? `${C.group_F_review.run} · ${C.group_F_review.cohort_rows} filas · ${C.group_F_review.cohort_sha256}` : "–")], ...Object.entries(E.provenance.inputs_sha256).map(([k, v]) => [k, h("span", { class: "mono" }, v)]), ["Entorno", `Python ${E.environment.python}, pandas ${E.environment.pandas}`]])));
  main.appendChild(section("controles", "Controles", g10));
  document.getElementById("footer").textContent = `Informe construido el ${DATA.built_utc} a partir de evidencia.json de la corrida ${E.run_id}. Revisión propia asistida por IA; no se modificaron datos ni índices; ninguna lista está aplicada.`;
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
