"""Convierte las figuras SVG de charts.py (fuente/) en PDF vectoriales para LaTeX.

Cada SVG se imprime con Chromium (Playwright) en una página del tamaño exacto del gráfico, con las fuentes
Inter en TrueType, de modo que el texto del PDF sigue siendo texto. Uso: python build_figuras.py <carpeta fuente> <carpeta salida>
"""
import asyncio, re, sys
from pathlib import Path

FUENTE = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/informe_final")
SALIDA = Path(sys.argv[2] if len(sys.argv) > 2 else "/home/claude/informe_final/latex/figuras")
sys.path.insert(0, str(FUENTE))
import charts  # noqa: E402

NOMBRES = ["completitud", "mezcla_peligros", "escalera_2023", "escalera_publico", "prevision_medido",
           "tornado_s1", "cadena_privado", "reservas", "credibilidad_k", "esquema_modelo", "flujo_ia"]
FONTS = (FUENTE / "fonts").resolve()
CSS = "".join(f'@font-face{{font-family:"InterTT";src:url("file://{FONTS}/Inter-{w}.ttf");font-weight:{n};}}'
              for w, n in [("Regular", 400), ("Medium", 500), ("SemiBold", 600), ("Bold", 700)])


async def main():
    from playwright.async_api import async_playwright
    SALIDA.mkdir(parents=True, exist_ok=True)
    async with async_playwright() as p:
        b = await p.chromium.launch()
        pg = await b.new_page()
        for n in NOMBRES:
            svg = getattr(charts, n)()
            w = float(re.search(r'width="([\d.]+)"', svg).group(1))
            h = float(re.search(r'height="([\d.]+)"', svg).group(1))
            html = (f'<!doctype html><html><head><meta charset="utf-8"><style>{CSS}'
                    f'html,body{{margin:0;padding:0}} svg{{display:block}} text{{font-feature-settings:"calt" 0, "liga" 0}}</style></head>'
                    f'<body>{svg}</body></html>')
            tmp = SALIDA / f"_{n}.html"
            tmp.write_text(html)
            await pg.goto(tmp.resolve().as_uri())
            await pg.wait_for_timeout(150)
            await pg.pdf(path=str(SALIDA / f"{n}.pdf"), width=f"{w}px", height=f"{h}px",
                         margin={"top": "0", "bottom": "0", "left": "0", "right": "0"}, print_background=True)
            tmp.unlink()
            print(f"{n}: {w:.0f} x {h:.0f} px")
        await b.close()

asyncio.run(main())
