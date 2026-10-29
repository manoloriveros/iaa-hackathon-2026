"""Construye informe_final_es.pdf: cinco páginas calificadas y anexos."""
import asyncio, hashlib, json, re, sys
from pathlib import Path
import pandas as pd
import charts, paginas, anexos

BASE = Path(__file__).parent
CSV = BASE / "prima_comercial_F3c_20ref.csv"
OUT_HTML = BASE / "informe_final_es.html"
OUT_PDF = BASE / "informe_final_es.pdf"
anexos.SHAS[1] = ("final_creible, parte 2", "1a003d8682f1…", "construir_final.py con los recibos de calibración")


def es(v, d=2):
    return charts.es(v, d)


def tabla_primas():
    d = pd.read_csv(CSV)
    ramo = {"motor": "Autos", "buildings": "Edificios", "contents": "Contenidos"}
    canal = {"broker": "Corredor", "direct": "Directo"}
    h = ('<table class="tight num prim"><tr><th>Póliza</th><th>Ramo</th><th>Canal</th><th class="r">Exposición</th>'
         '<th class="r">Prima de riesgo R</th><th class="r">Catástrofe</th><th class="r">Gasto fijo</th>'
         '<th class="r">Prima comercial P</th><th class="r">Prima escrita anual</th><th class="r">P anualizada / escrita</th></tr>')
    rows = []
    for _, r in d.iterrows():
        rows.append(f'<tr><td>{r.row_id}</td><td>{ramo[r.line]}</td><td>{canal[r.channel]}</td>'
                    f'<td class="r">{es(r.exposure)}</td>'
                    f'<td class="r">{es(r.R)}</td><td class="r">{es(r["cat"])}</td><td class="r">{es(r.fijo)}</td>'
                    f'<td class="r"><b>{es(r.P)}</b></td><td class="r">{es(r.written_premium)}</td>'
                    f'<td class="r">{es(r.P / r.exposure / r.written_premium)}</td></tr>')
    for l in ["motor", "buildings", "contents"]:
        s = d[d.line == l]
        rows.append(f'<tr class="tot"><td colspan="4">Total {ramo[l].lower()}</td><td class="r">{es(s.R.sum())}</td>'
                    f'<td class="r">{es(s["cat"].sum())}</td><td class="r">{es(s.fijo.sum())}</td>'
                    f'<td class="r">{es(s.P.sum())}</td><td class="r">{es(s.written_premium.sum())}</td>'
                    f'<td class="r">{es((s.P / s.exposure).sum() / s.written_premium.sum())}</td></tr>')
    rows.append(f'<tr class="tot"><td colspan="4">Total de las 20 pólizas</td><td class="r">{es(d.R.sum())}</td>'
                f'<td class="r">{es(d["cat"].sum())}</td><td class="r">{es(d.fijo.sum())}</td>'
                f'<td class="r">{es(d.P.sum())}</td><td class="r">{es(d.written_premium.sum())}</td>'
                f'<td class="r">{es((d.P / d.exposure).sum() / d.written_premium.sum())}</td></tr>')
    return h + "".join(rows) + "</table>"


FIGS = {k: getattr(charts, k) for k in ["completitud", "mezcla_peligros", "escalera_2023", "escalera_publico",
                                        "prevision_medido", "tornado_s1", "cadena_privado", "reservas", "credibilidad_k", "esquema_modelo", "flujo_ia"]}
TABLAS = {"primas": tabla_primas, "experimentos": anexos.tabla_experimentos, "crono": anexos.tabla_crono,
          "herramientas": anexos.tabla_herramientas, "shas": anexos.tabla_shas}


def fill(s):
    s = re.sub(r"\{\{FIG:(\w+)\}\}", lambda m: FIGS[m.group(1)](), s)
    s = re.sub(r"\{\{TABLA:(\w+)\}\}", lambda m: TABLAS[m.group(1)](), s)
    s = s.replace("{{REFS}}", "".join(f'<p class="ref">{i + 1}. {r}</p>' for i, r in enumerate(anexos.REFERENCIAS)))
    s = re.sub(r"(\d) %", "\\1\u00a0%", s)
    return s


def page(body, n, total, cls=""):
    if n in (3, 4): cls = (cls + " readable").strip()
    return (f'<section class="page {cls}"><div class="runhead"><span>{paginas.RUNHEAD}</span>'
            f'<span>Manuel Rodríguez · Kaggle: manoloriveros</span></div>'
            f'<div class="content">{fill(body)}</div>'
            f'<div class="foot"><span>{"Página calificada" if n <= 5 else "Anexo, fuera de las cinco páginas calificadas"}</span>'
            f'<span>{n} / {total}</span></div></section>')


def build():
    bodies = [paginas.P1, paginas.P2, paginas.P3, paginas.P4, paginas.P5] + anexos.PAGINAS
    total = len(bodies)
    css = (BASE / "style.css").read_text()
    html = ('<!doctype html><html lang="es"><head><meta charset="utf-8"><title>Prima de riesgo asistida por IA en dos mercados</title>'
            f'<style>{css}</style></head><body>'
            + "".join(page(b, i + 1, total, "anx" if i >= 5 else "") for i, b in enumerate(bodies)) + "</body></html>")
    OUT_HTML.write_text(html)
    return total


async def render():
    from playwright.async_api import async_playwright
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        await pg.goto(OUT_HTML.as_uri())
        await pg.wait_for_timeout(300)
        over = await pg.evaluate("""() => [...document.querySelectorAll('.content')].map((c,i)=>{const r=c.getBoundingClientRect(); let m=0; for (const e of c.querySelectorAll('*')) { const b=e.getBoundingClientRect(); if (b.height>0) m=Math.max(m,b.bottom-r.top);} return {p:i+1, sh:Math.round(m), ch:c.clientHeight};})""")
        await pg.pdf(path=str(OUT_PDF), format="A4", print_background=True, prefer_css_page_size=True)
        await b.close()
    return over


if __name__ == "__main__":
    n = build()
    over = asyncio.run(render())
    for o in over:
        flag = "DESBORDA" if o["sh"] > o["ch"] + 1 else "ok"
        print(f"página {o['p']}: {o['sh']} / {o['ch']} px  {flag}  (libre {o['ch']-o['sh']} px)")
    print(OUT_PDF, hashlib.sha256(OUT_PDF.read_bytes()).hexdigest()[:16])
