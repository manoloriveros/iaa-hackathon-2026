"""Construye tablero.html: tablero sin conexión de la validación de datos de la semana 2 (Claude, 23-10-2026).

Lee evidencia_validacion.json, tablas/controles.csv y las seis figuras PNG de la misma carpeta y escribe un único archivo
HTML con los controles filtrables (resultado, área, severidad, texto), el detalle de cada control y las figuras incrustadas
como data URI. No usa scripts externos ni conexión; se queda en el repositorio y no se publica en línea.
"""
from __future__ import annotations

import base64
import csv
import html
import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
COLOR = {'pasa': '#1baf7a', 'hallazgo': '#eb6834', 'limite': '#8e6cc6', 'informativo': '#9aa0a6'}
NOMBRE = {'pasa': 'Pasa', 'hallazgo': 'Hallazgo', 'limite': 'Límite', 'informativo': 'Informativo'}
FIGURAS = [('fig1_controles.png', 'Resumen de los controles por área y resultado'),
           ('fig2_calendario.png', 'Calendario y exposición: las 609 filas fuera de días/365 y el cierre del año'),
           ('fig3_nulos.png', 'Los nulos del 12 %: misma cuota por segmento y por año'),
           ('fig4_make_model.png', 'make_model: frecuencia por código en los dos mercados y dispersión'),
           ('fig5_test.png', 'Qué cambia en 2025: PSI por columna y nuevo negocio'),
           ('fig6_siniestros.png', 'Siniestros: retraso de reporte y concentración del coste')]
ORDEN_AREAS = ['Integridad', 'Relaciones', 'Calendario', 'Clientes', 'Direcciones', 'Clima', 'Autos', 'Edificios', 'Contenidos', 'Hogar', 'Pólizas',
               'Siniestros', 'Test', 'Entrega', 'Capas derivadas', 'Faltantes', 'Disponibilidad', 'Comercial', 'Historia', 'Objetivo', 'Métrica', 'Tendencia', 'Revisión']


def main():
    ev = json.loads((HERE / 'evidencia_validacion.json').read_text(encoding='utf-8'))
    with (HERE / 'tablas' / 'controles.csv').open(encoding='utf-8', newline='') as f:
        filas = list(csv.DictReader(f))
    for r in filas:
        d = ev['detalle'].get(r['id'], {})
        r['detalle'] = json.dumps(d, ensure_ascii=False, indent=1)[:6000]
    areas = [a for a in ORDEN_AREAS if any(r['area'] == a for r in filas)] + sorted({r['area'] for r in filas} - set(ORDEN_AREAS))
    conteo = {a: {k: sum(1 for r in filas if r['area'] == a and r['resultado'] == k) for k in COLOR} for a in areas}
    res = ev['resumen']['por_resultado']
    figs = []
    for nombre, pie in FIGURAS:
        b = (HERE / nombre).read_bytes()
        figs.append((nombre, pie, 'data:image/png;base64,' + base64.b64encode(b).decode('ascii')))

    # gráfico de barras apiladas por área, SVG en línea
    ancho, alto_fila, izq, der = 760, 22, 150, 20
    maxn = max(sum(conteo[a].values()) for a in areas)
    escala = (ancho - izq - der) / maxn
    svg = [f'<svg viewBox="0 0 {ancho} {alto_fila * len(areas) + 30}" role="img" aria-label="Controles por área y resultado">']
    for i, a in enumerate(areas):
        y = 10 + i * alto_fila
        svg.append(f'<text x="{izq - 8}" y="{y + 15}" text-anchor="end" class="eje">{html.escape(a)}</text>')
        x = izq
        for k in ['pasa', 'hallazgo', 'limite', 'informativo']:
            n = conteo[a][k]
            if n:
                w = n * escala
                svg.append(f'<rect x="{x:.1f}" y="{y + 3}" width="{max(w - 2, 1):.1f}" height="{alto_fila - 6}" rx="3" fill="{COLOR[k]}" data-area="{html.escape(a)}" data-res="{k}" class="barra"><title>{html.escape(a)}: {n} {NOMBRE[k].lower()}</title></rect>')
                if w > 14:
                    svg.append(f'<text x="{x + w / 2 - 1:.1f}" y="{y + 15}" text-anchor="middle" class="valor">{n}</text>')
                x += w
    svg.append('</svg>')

    datos = json.dumps(filas, ensure_ascii=False).replace('</', '<\\/')
    tiles = ''.join(f'<div class="tile" data-res="{k}"><div class="n" style="color:{COLOR[k]}">{res.get(k, 0)}</div><div class="l">{NOMBRE[k]}</div></div>' for k in ['pasa', 'hallazgo', 'limite', 'informativo'])
    opciones_area = ''.join(f'<option value="{html.escape(a)}">{html.escape(a)}</option>' for a in areas)
    galeria = ''.join(f'<figure><img src="{uri}" alt="{html.escape(pie)}" loading="lazy"><figcaption>{html.escape(nombre)}: {html.escape(pie)}</figcaption></figure>' for nombre, pie, uri in figs)
    hallazgos = ''.join(f'<li><span class="sev {h["severidad"]}">{h["severidad"]}</span> <b>{h["id"]}</b> {html.escape(h["titulo"])} <span class="obs">{html.escape(h["observado"])}</span></li>' for h in ev['resumen']['hallazgos'])
    limites = ''.join(f'<li><b>{l["id"]}</b> {html.escape(l["titulo"])}</li>' for l in ev['resumen']['limites'])

    page = f'''<!doctype html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Validación de datos S2</title>
<style>
:root {{ --bg:#ffffff; --panel:#f6f7f9; --ink:#1f2328; --ink2:#57606a; --line:#e1e4e8; --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#8e6cc6; --gris:#9aa0a6; }}
@media (prefers-color-scheme: dark) {{ :root:not([data-theme="light"]) {{ --bg:#0f1316; --panel:#171c21; --ink:#e6e8eb; --ink2:#aab2bb; --line:#2a3139; }} }}
:root[data-theme="dark"] {{ --bg:#0f1316; --panel:#171c21; --ink:#e6e8eb; --ink2:#aab2bb; --line:#2a3139; }}
* {{ box-sizing:border-box; }}
body {{ margin:0; background:var(--bg); color:var(--ink); font:14px/1.45 system-ui,-apple-system,"Segoe UI",Roboto,sans-serif; }}
main {{ max-width:1180px; margin:0 auto; padding:20px 16px 48px; }}
h1 {{ font-size:22px; margin:0 0 4px; }} h2 {{ font-size:17px; margin:28px 0 10px; }}
.sub {{ color:var(--ink2); margin:0 0 16px; }}
.tiles {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(140px,1fr)); gap:10px; }}
.tile {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:12px 14px; cursor:pointer; }}
.tile.activo {{ outline:2px solid var(--s1); }}
.tile .n {{ font-size:28px; font-weight:700; line-height:1; }} .tile .l {{ color:var(--ink2); margin-top:4px; }}
.grafico {{ background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px 12px; margin-top:12px; overflow-x:auto; }}
.grafico svg {{ width:100%; height:auto; min-width:560px; }}
.eje {{ fill:var(--ink2); font-size:11px; }} .valor {{ fill:#ffffff; font-size:10px; font-weight:600; }}
.barra {{ cursor:pointer; }} .barra:hover {{ opacity:.85; }}
.leyenda {{ display:flex; gap:14px; flex-wrap:wrap; color:var(--ink2); font-size:12px; margin:6px 0 0; }}
.leyenda span::before {{ content:""; display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:5px; vertical-align:-1px; background:var(--c); }}
.filtros {{ display:flex; gap:8px; flex-wrap:wrap; margin:10px 0; align-items:center; }}
.filtros select, .filtros input {{ background:var(--panel); color:var(--ink); border:1px solid var(--line); border-radius:8px; padding:7px 9px; font:inherit; }}
.filtros input {{ flex:1; min-width:200px; }}
.filtros button {{ background:transparent; color:var(--ink2); border:1px solid var(--line); border-radius:8px; padding:7px 10px; cursor:pointer; font:inherit; }}
.cuenta {{ color:var(--ink2); font-size:12px; }}
table {{ width:100%; border-collapse:collapse; }}
th, td {{ text-align:left; padding:8px 8px; border-bottom:1px solid var(--line); vertical-align:top; }}
th {{ color:var(--ink2); font-weight:600; font-size:12px; position:sticky; top:0; background:var(--bg); cursor:pointer; }}
tr.fila {{ cursor:pointer; }} tr.fila:hover td {{ background:var(--panel); }}
.pill {{ display:inline-block; padding:2px 8px; border-radius:999px; color:#fff; font-size:11px; font-weight:600; }}
.sev {{ display:inline-block; min-width:24px; text-align:center; padding:1px 6px; border-radius:6px; font-size:11px; font-weight:700; border:1px solid var(--line); }}
.sev.P0 {{ background:var(--s2); color:#fff; border-color:var(--s2); }} .sev.P1 {{ background:#f6c7b3; color:#5a2a14; }} .sev.P2 {{ background:var(--panel); color:var(--ink2); }}
.obs {{ color:var(--ink2); }}
tr.detalle td {{ background:var(--panel); }}
pre {{ margin:0; white-space:pre-wrap; word-break:break-word; font:12px/1.4 ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; max-height:420px; overflow:auto; }}
.meta {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(220px,1fr)); gap:6px 16px; margin-bottom:8px; }}
.meta div span {{ color:var(--ink2); }}
figure {{ margin:0 0 18px; background:var(--panel); border:1px solid var(--line); border-radius:10px; padding:10px; }}
figure img {{ width:100%; height:auto; display:block; border-radius:6px; }}
figcaption {{ color:var(--ink2); font-size:12px; margin-top:6px; }}
ul.lista {{ padding-left:18px; }} ul.lista li {{ margin:4px 0; }}
footer {{ color:var(--ink2); font-size:12px; margin-top:28px; border-top:1px solid var(--line); padding-top:10px; }}
@media (max-width:640px) {{ .oculta {{ display:none; }} }}
</style>
</head>
<body>
<main>
<h1>Validación exhaustiva de los datos de la semana 2 (mercado emergente)</h1>
<p class="sub">Claude (Cowork), 23 de octubre de 2026. {ev['resumen']['controles']} controles sobre los trece Parquet emergentes, el desarrollado y las capas de Codex; corrida {html.escape(ev['utc'])}. Tablero sin conexión: se queda en el repositorio. Las cifras salen de <code>evidencia_validacion.json</code>; los casos por fila están en privado.</p>

<section class="tiles" id="tiles">{tiles}</section>

<div class="grafico">{''.join(svg)}
<div class="leyenda">{''.join(f'<span style="--c:{COLOR[k]}">{NOMBRE[k]}</span>' for k in ['pasa', 'hallazgo', 'limite', 'informativo'])}</div></div>

<h2>Controles</h2>
<div class="filtros">
<select id="fres"><option value="">Todos los resultados</option>{''.join(f'<option value="{k}">{NOMBRE[k]}</option>' for k in COLOR)}</select>
<select id="farea"><option value="">Todas las áreas</option>{opciones_area}</select>
<select id="fsev"><option value="">Toda severidad</option><option value="P0">P0</option><option value="P1">P1</option><option value="P2">P2</option></select>
<input id="ftxt" type="search" placeholder="Buscar en identificador, título, observado o detalle…">
<button id="limpiar" type="button">Limpiar</button>
<span class="cuenta" id="cuenta"></span>
</div>
<table id="tabla">
<thead><tr><th data-k="id">ID</th><th data-k="area">Área</th><th data-k="titulo">Control</th><th data-k="resultado">Resultado</th><th data-k="severidad" class="oculta">Sev.</th><th data-k="observado" class="oculta">Observado</th><th data-k="vd_semana1" class="oculta">S1</th></tr></thead>
<tbody id="cuerpo"></tbody>
</table>

<h2>Los {len(ev['resumen']['hallazgos'])} hallazgos</h2>
<ul class="lista">{hallazgos}</ul>
<h2>Los {len(ev['resumen']['limites'])} límites</h2>
<ul class="lista">{limites}</ul>

<h2>Figuras</h2>
{galeria}

<footer>Revisión de IA sobre copias con huella comprobada; no es revisión profesional independiente. Generado por <code>construir_tablero.py</code> desde la evidencia; para repetir la validación, <code>validar_datos_s2.py</code> (ver INFORME.md).</footer>
</main>
<script>
const DATOS = {datos};
const COLOR = {json.dumps(COLOR)};
const NOMBRE = {json.dumps(NOMBRE, ensure_ascii=False)};
const esc = s => String(s ?? '').replace(/[&<>"]/g, c => ({{'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}}[c]));
const fres = document.getElementById('fres'), farea = document.getElementById('farea'), fsev = document.getElementById('fsev'), ftxt = document.getElementById('ftxt');
let orden = {{k: 'id', asc: true}};
let abierto = null;
function filtrar() {{
  const q = ftxt.value.trim().toLowerCase();
  let f = DATOS.filter(r => (!fres.value || r.resultado === fres.value) && (!farea.value || r.area === farea.value) && (!fsev.value || r.severidad === fsev.value)
    && (!q || (r.id + ' ' + r.titulo + ' ' + r.observado + ' ' + r.esperado + ' ' + r.detalle).toLowerCase().includes(q)));
  f.sort((a, b) => (a[orden.k] > b[orden.k] ? 1 : a[orden.k] < b[orden.k] ? -1 : 0) * (orden.asc ? 1 : -1));
  const tb = document.getElementById('cuerpo');
  tb.innerHTML = f.map(r => `<tr class="fila" data-id="${{esc(r.id)}}"><td><b>${{esc(r.id)}}</b></td><td>${{esc(r.area)}}</td><td>${{esc(r.titulo)}}</td><td><span class="pill" style="background:${{COLOR[r.resultado]}}">${{NOMBRE[r.resultado]}}</span></td><td class="oculta">${{r.severidad ? `<span class="sev ${{esc(r.severidad)}}">${{esc(r.severidad)}}</span>` : ''}}</td><td class="oculta obs">${{esc(r.observado)}}</td><td class="oculta obs">${{esc(r.vd_semana1)}}</td></tr>`
    + (abierto === r.id ? `<tr class="detalle"><td colspan="7"><div class="meta"><div><span>Esperado:</span> ${{esc(r.esperado) || '—'}}</div><div><span>Control de semana 1:</span> ${{esc(r.vd_semana1) || '—'}}</div><div><span>Casos por fila:</span> ${{r.casos ? esc(r.casos) + ' (' + esc(r.n_casos) + ' filas, en privado)' : 'ninguno'}}</div></div><pre>${{esc(r.detalle)}}</pre></td></tr>` : '')).join('');
  document.getElementById('cuenta').textContent = f.length + ' de ' + DATOS.length + ' controles';
  document.querySelectorAll('.tile').forEach(t => t.classList.toggle('activo', t.dataset.res === fres.value));
}}
document.getElementById('cuerpo').addEventListener('click', e => {{ const tr = e.target.closest('tr.fila'); if (!tr) return; abierto = abierto === tr.dataset.id ? null : tr.dataset.id; filtrar(); }});
document.querySelectorAll('th[data-k]').forEach(th => th.addEventListener('click', () => {{ const k = th.dataset.k; orden = {{k, asc: orden.k === k ? !orden.asc : true}}; filtrar(); }}));
document.querySelectorAll('.tile').forEach(t => t.addEventListener('click', () => {{ fres.value = fres.value === t.dataset.res ? '' : t.dataset.res; filtrar(); }}));
document.querySelectorAll('.barra').forEach(b => b.addEventListener('click', () => {{ farea.value = b.dataset.area; fres.value = b.dataset.res; filtrar(); window.scrollTo({{top: document.getElementById('tabla').offsetTop - 80, behavior: 'smooth'}}); }}));
[fres, farea, fsev].forEach(s => s.addEventListener('change', filtrar));
ftxt.addEventListener('input', filtrar);
document.getElementById('limpiar').addEventListener('click', () => {{ fres.value = farea.value = fsev.value = ''; ftxt.value = ''; abierto = null; filtrar(); }});
filtrar();
</script>
</body>
</html>
'''
    (HERE / 'tablero.html').write_text(page, encoding='utf-8')
    print('tablero.html', (HERE / 'tablero.html').stat().st_size, 'bytes')


if __name__ == '__main__':
    main()
