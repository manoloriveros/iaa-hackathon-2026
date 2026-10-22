"""Construye los entregables visuales a partir de docs/entrega/datos/cifras_entregables.json.

    python herramientas/construir_entrega.py figuras    # PNG por figura e idioma (docs/entrega/figuras/<idioma>/)
    python herramientas/construir_entrega.py informe    # PDF del informe en inglés y español (docs/entrega/)
    python herramientas/construir_entrega.py panel      # panel HTML autocontenido (docs/entrega/panel_modelo.html)
    python herramientas/construir_entrega.py laminas    # láminas 16:9 para grabar el video (docs/entrega/video/laminas/)
    python herramientas/construir_entrega.py todo

Requiere markdown y playwright con Chromium. No lee datos por fila, no entrena y no envía nada: solo dibuja las cifras
agregadas que ya están en el JSON (generado por herramientas/cifras_entregables.py).
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENT = REPO / "docs/entrega"
WEB = ENT / "web"
IDIOMAS = tuple(x for x in ("en", "es") if not [a for a in sys.argv if a.startswith("--idioma=")] or ("--idioma=" + x) in sys.argv)
# Tamaño natural (px CSS) del contenedor de cada figura en PNG.
TAMANOS = {"flujo": 700, "flujo_ia": 770, "siniestros": 700, "validacion_diseno": 450, "curva": 710, "publico_local": 700,
           "completitud": 390, "prima_anual": 730, "composicion": 710, "d2_ramo": 390, "deciles": 730,
           "reservas": 430, "foro": 530, "ceros": 610, "escala_d2": 610, "hallazgos": 430, "backtest": 660, "calibracion": 710}
OPCIONES = {"flujo": {"filas": 2}}


def sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def fuentes_css() -> str:
    """Inter (OFL) en woff2 con contornos TrueType, incrustada como data URI: el PDF conserva texto extraíble."""
    import base64
    reglas = []
    for nombre, peso, rango in (("inter-latin-400-normal", 400, "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
                                ("inter-latin-600-normal", 600, "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
                                ("inter-latin-700-normal", 700, "U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+0304,U+0308,U+0329,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD"),
                                ("inter-greek-400-normal", 400, "U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF"),
                                ("inter-greek-600-normal", 600, "U+0370-0377,U+037A-037F,U+0384-038A,U+038C,U+038E-03A1,U+03A3-03FF")):
        b = base64.b64encode((WEB / "fuentes" / f"{nombre}.woff2").read_bytes()).decode()
        reglas.append(f"@font-face{{font-family:'InterWeb';font-style:normal;font-weight:{peso};font-display:block;"
                      f"src:url(data:font/woff2;base64,{b}) format('woff2');unicode-range:{rango};}}")
    # 650 y 550 se resuelven con los pesos más cercanos.
    return "\n".join(reglas)


def recursos():
    css = fuentes_css() + "\n" + (WEB / "estilo.css").read_text(encoding="utf-8")
    js = "\n".join((WEB / n).read_text(encoding="utf-8") for n in ("graficos.js", "diagramas.js", "figuras.js"))
    cifras = (ENT / "datos/cifras_entregables.json").read_text(encoding="utf-8")
    return css, js, cifras


def pagina(cuerpo: str, lang: str, css_extra: str = "", js_extra: str = "", titulo: str = "IAA 2026") -> str:
    css, js, cifras = recursos()
    datos = cifras.replace("</", "<\\/")
    return (f"<!doctype html><html lang='{lang}'><head><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'>"
            f"<title>{html.escape(titulo)}</title><style>{css}\n{css_extra}</style></head><body>{cuerpo}"
            f"<script>window.CIFRAS={datos};</script><script>{js}</script><script>{CON_FUENTE.replace('__JS__', js_extra)}</script></body></html>")


# Los gráficos miden texto para colocar leyendas: se dibuja cuando Inter (incrustada) ya está cargada.
CON_FUENTE = ("(function(){var go=function(){__JS__};var f=document.fonts;"
              "if(f&&f.load){Promise.all([f.load('400 12px InterWeb'),f.load('600 12px InterWeb'),f.load('700 12px InterWeb')]).then(go,go);}"
              "else{go();}})();")


def navegador():
    from playwright.sync_api import sync_playwright
    return sync_playwright()


def figuras():
    salida = []
    with navegador() as p:
        b = p.chromium.launch()
        for lang in IDIOMAS:
            cuerpo = "".join(f"<div class='fig' id='f_{i}' style='width:{w}px'></div>" for i, w in TAMANOS.items())
            js = ("var errores=[];" + json.dumps(list(TAMANOS)) + ".forEach(function(id){try{F.dibujar(id, document.getElementById('f_'+id), '"
                  + lang + "', " + json.dumps(OPCIONES) + "[id]||{});}catch(e){errores.push(id+': '+e.message);}});window.ERRORES=errores;window.LISTO=true;")
            css = SIN_CFF + "body{margin:0;background:var(--surface-1)} .fig{padding:10px;background:var(--surface-1);display:block} .g-par,.g-tres{display:flex;gap:8px}"
            pg = b.new_page(viewport={"width": 1000, "height": 900}, device_scale_factor=2.5)
            pg.set_content(pagina(cuerpo, lang, css, js), wait_until="load")
            pg.wait_for_function("window.LISTO === true")
            pg.wait_for_timeout(100)
            err = pg.evaluate("window.ERRORES")
            if err:
                raise SystemExit(f"Errores al dibujar ({lang}): {err}")
            dst = ENT / "figuras" / lang
            dst.mkdir(parents=True, exist_ok=True)
            for i in TAMANOS:
                f = dst / f"{i}.png"
                pg.locator(f"#f_{i}").screenshot(path=str(f))
                salida.append(f.relative_to(REPO).as_posix())
            pg.close()
        b.close()
    print(json.dumps({"figuras": len(salida)}, ensure_ascii=False))
    return salida


SIN_CFF = ':root, :root[data-theme] { --fuente: "InterWeb", "DejaVu Sans", sans-serif !important; }'

CSS_INFORME = SIN_CFF + """
@page { size: A4; margin: 13mm 14mm 13mm 14mm; }
html { -webkit-print-color-adjust: exact; print-color-adjust: exact; }
body { margin: 0; background: #fff; color: var(--text-primary); font: 8.9pt/1.40 var(--fuente); }
.hoja { width: 182mm; }
h1 { font-size: 19pt; line-height: 1.15; color: var(--brand); margin: 0 0 2mm; font-weight: 700; letter-spacing: -.01em; }
h2 { font-size: 12pt; color: var(--brand); margin: 3.4mm 0 1.4mm; font-weight: 700; break-after: avoid; }
h3 { font-size: 10pt; margin: 3mm 0 1mm; font-weight: 650; break-after: avoid; }
p { margin: 0 0 1.9mm; }
.sub { color: var(--text-secondary); font-size: 8.6pt; margin-bottom: 3mm; }
.kpis { display: grid; grid-template-columns: repeat(4, 1fr); gap: 2.4mm; margin: 2mm 0 3mm; }
.kpi { border-top: 2.5px solid var(--brand); background: #f6f8f8; padding: 2mm 2.6mm 2.2mm; }
.kpi .v { font-size: 15pt; font-weight: 650; line-height: 1.15; color: var(--text-primary); }
.kpi .l { font-size: 7.8pt; color: var(--text-secondary); line-height: 1.3; margin-top: .6mm; }
figure { margin: 1.6mm 0 2.2mm; break-inside: avoid; }
figure .viva svg, figure img { width: 100%; height: auto; display: block; }
figcaption { font-size: 7.9pt; color: var(--text-secondary); margin-top: 1.2mm; line-height: 1.35; }
.fig-n { color: var(--brand); font-weight: 650; margin-right: 1.2mm; }
.fila { display: grid; grid-template-columns: 1fr 1fr; gap: 5mm; align-items: start; }
.fila-60 { display: grid; grid-template-columns: 1.35fr 1fr; gap: 5mm; align-items: start; }
.g-par, .g-tres { display: flex; gap: 2mm; }
.g-par > div, .g-tres > div { flex: 1; min-width: 0; }
table { border-collapse: collapse; width: 100%; font-size: 7.6pt; line-height: 1.3; margin: 1mm 0 2.2mm; break-inside: avoid; }
th { text-align: left; font-weight: 650; color: var(--brand); border-bottom: 1px solid var(--axis); padding: .9mm 1.5mm; background: #f3f6f6; }
td { border-bottom: 1px solid var(--grid); padding: .85mm 1.5mm; vertical-align: top; }
td.n, th.n { text-align: right; font-variant-numeric: tabular-nums; white-space: nowrap; }
.nota { font-size: 7.8pt; color: var(--text-secondary); }
.compacta table { font-size: 7.1pt; } .compacta td, .compacta th { padding: .55mm 1.3mm; }
.salto { break-after: page; height: 0; }
h2.pagina { break-before: page; }
h2.pagina:first-child { break-before: auto; }
.apendice h2 { margin-top: 0; }
.apendice { font-size: 8.4pt; }
.apendice li { margin-bottom: 1mm; }
a { color: var(--brand); text-decoration: none; }
ul { margin: 0 0 2mm 4.5mm; padding: 0; } li { margin: 0 0 .8mm; }
.marca { color: var(--text-muted); font-size: 7.6pt; }
figure.estrecha { width: 80%; margin-left: auto; margin-right: auto; }
p.formula { text-align: center; font-size: 9.6pt; margin: 0.4mm 0 1.6mm; }
"""


def md_a_html(texto: str) -> str:
    import markdown
    return markdown.markdown(texto, extensions=["tables", "md_in_html", "attr_list", "sane_lists"], output_format="html5")


def informe_html(lang: str, solo_calificable: bool) -> str:
    fuente = ENT / f"informe/INFORME_{lang.upper()}.md"
    texto = fuente.read_text(encoding="utf-8")
    if solo_calificable:
        texto = texto.split("<!-- FIN-CALIFICABLE -->")[0]
    cuerpo = md_a_html(texto)
    if lang == "es":
        cuerpo = re.sub(r"(\d) %", "\\1&nbsp;%", cuerpo)
    # Cada <figure data-fig="id"> se dibuja en vivo (vector) en lugar de la imagen PNG que ve GitHub.
    def viva(m):
        bloque = m.group(0)
        fid = re.search(r'data-fig="([^"]+)"', bloque).group(1)
        opts = re.search(r"data-opts='([^']+)'", bloque)
        img = re.search(r"<img[^>]*>", bloque)
        div = f"<div class='viva' data-fig='{fid}' data-opts='{opts.group(1) if opts else '{}'}'></div>"
        return bloque.replace(img.group(0), div) if img else bloque
    cuerpo = re.sub(r"<figure[^>]*data-fig=\"[^\"]+\"[^>]*>.*?</figure>", viva, cuerpo, flags=re.S)
    js = ("document.querySelectorAll('.viva').forEach(function(d){var o={};try{o=JSON.parse(d.getAttribute('data-opts')||'{}');}catch(e){}"
          "F.dibujar(d.getAttribute('data-fig'), d, '" + lang + "', o);});window.LISTO=true;")
    titulo = "A risk premium for every policy period" if lang == "en" else "Una prima de riesgo para cada periodo de póliza"
    return pagina(f"<main class='hoja'>{cuerpo}</main>", lang, CSS_INFORME, js, titulo)


def informe():
    from pypdf import PdfReader
    res = {}
    with navegador() as p:
        b = p.chromium.launch()
        for lang in IDIOMAS:
            pie = ("<div style='width:100%;font:7pt DejaVu Sans,sans-serif;color:#898781;padding:0 14mm;display:flex;justify-content:space-between'>"
                   + ("<span>IAA AI Hackathon 2026 · Part 1 · Manuel Rodríguez</span>" if lang == "en" else "<span>AI Hackathon IAA 2026 · Parte 1 · Manuel Rodríguez</span>")
                   + "<span><span class='pageNumber'></span> / <span class='totalPages'></span></span></div>")
            for solo in (True, False):
                pg = b.new_page()
                pg.set_content(informe_html(lang, solo), wait_until="load")
                pg.wait_for_function("window.LISTO === true")
                pg.wait_for_timeout(200)
                nombre = ("report_" if lang == "en" else "informe_") + ("calificable_" if solo else "") + lang + ".pdf"
                destino = ENT / ("_tmp_" + nombre if solo else nombre)
                pg.pdf(path=str(destino), format="A4", print_background=True, display_header_footer=True,
                       header_template="<div></div>", footer_template=pie,
                       margin={"top": "12mm", "bottom": "13mm", "left": "14mm", "right": "14mm"})
                n = len(PdfReader(str(destino)).pages)
                if solo:
                    res[lang] = {"paginas_calificables": n}
                    destino.unlink()
                else:
                    res[lang].update({"paginas_totales": n, "pdf": destino.relative_to(REPO).as_posix(), "sha256": sha(destino)})
                    (ENT / f"informe/informe_{lang}.html").write_text(informe_html(lang, False), encoding="utf-8")
                pg.close()
        b.close()
    malos = {k: v for k, v in res.items() if v["paginas_calificables"] > 5}
    print(json.dumps(res, ensure_ascii=False))
    if malos:
        raise SystemExit(f"El cuerpo calificable supera cinco páginas: {malos}")
    return res


def panel():
    plantilla = (WEB / "panel_plantilla.html").read_text(encoding="utf-8")
    css, js, cifras = recursos()
    datos = cifras.replace("</", "<\\/")
    out = plantilla.replace("/*__CSS__*/", css).replace("/*__JS__*/", js).replace("/*__CIFRAS__*/", "window.CIFRAS=" + datos + ";")
    destino = ENT / "panel_modelo.html"
    destino.write_text(out, encoding="utf-8")
    with navegador() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1440, "height": 900})
        errores = []
        pg.on("pageerror", lambda e: errores.append(str(e)))
        pg.goto(destino.as_uri())
        pg.wait_for_timeout(600)
        b.close()
    if errores:
        raise SystemExit(f"Errores en el panel: {errores}")
    print(json.dumps({"panel": destino.relative_to(REPO).as_posix(), "bytes": destino.stat().st_size, "sha256": sha(destino)}))


def captura_panel(b, lang: str) -> str:
    """Captura de la sección de validación del panel (modo claro), para la lámina que lo presenta."""
    import base64
    panel_html = ENT / "panel_modelo.html"
    if not panel_html.exists():
        raise SystemExit("Falta docs/entrega/panel_modelo.html: ejecute antes la orden panel.")
    pg = b.new_page(viewport={"width": 1000, "height": 640}, device_scale_factor=2, color_scheme="light")
    pg.goto(panel_html.as_uri())
    pg.wait_for_function("window.LISTO === true")
    pg.click(f"[data-idioma={lang}]")
    pg.wait_for_timeout(300)
    pg.evaluate("document.getElementById('validacion').scrollIntoView({block: 'start'})")
    pg.wait_for_timeout(300)
    png = pg.screenshot()
    destino = ENT / "video/capturas" / lang
    destino.mkdir(parents=True, exist_ok=True)
    (destino / "panel_validacion.png").write_bytes(png)
    pg.close()
    return "data:image/png;base64," + base64.b64encode(png).decode()


def laminas():
    plantilla = (WEB / "laminas_plantilla.html").read_text(encoding="utf-8")
    hechas = []
    with navegador() as p:
        b = p.chromium.launch()
        for lang in IDIOMAS:
            capturas = {}  # La lámina 15 ya no muestra la captura del panel (desde S42 explica la calibración del nivel).
            pg = b.new_page(viewport={"width": 1920, "height": 1080}, device_scale_factor=1)
            errores = []
            pg.on("pageerror", lambda e: errores.append(str(e)))
            css, js, cifras = recursos()
            pg.set_content(plantilla.replace("/*__CSS__*/", css).replace("/*__JS__*/", js)
                           .replace("/*__CIFRAS__*/", "window.CIFRAS=" + cifras.replace("</", "<\\/") + ";")
                           .replace("/*__CAPTURAS__*/", "window.CAPTURAS=" + json.dumps(capturas) + ";")
                           .replace("__LANG__", lang), wait_until="load")
            try:
                pg.wait_for_function("window.LISTO === true", timeout=15000)
            except Exception:
                raise SystemExit(f"Las láminas ({lang}) no terminaron: {errores}")
            n = pg.evaluate("document.querySelectorAll('.lamina').length")
            # Ninguna lámina puede desbordar su caja de 1920 × 1080.
            desbordes = pg.evaluate("""Array.from(document.querySelectorAll('.lamina')).map(function (l, i) {
                var r = l.getBoundingClientRect(), malos = [];
                l.querySelectorAll('.cuerpo, .cuerpo *, .pie').forEach(function (e) {
                  var b = e.getBoundingClientRect();
                  if (b.width && (b.bottom > r.bottom - 40 || b.right > r.right - 90)) malos.push(e.tagName + '.' + e.className);
                });
                return malos.length ? (i + 1) + ': ' + malos.slice(0, 3).join(', ') : '';
              }).filter(Boolean)""")
            dst = ENT / "video/laminas" / lang
            dst.mkdir(parents=True, exist_ok=True)
            for viejo in dst.glob("*.png"):
                viejo.unlink()
            for k in range(n):
                f = dst / f"{k + 1:02d}.png"
                pg.locator(".lamina").nth(k).screenshot(path=str(f))
                hechas.append(f.relative_to(REPO).as_posix())
            pdf = ENT / "video" / f"laminas_{lang}.pdf"
            pg.emulate_media(media="print")
            pg.pdf(path=str(pdf), width="1920px", height="1080px", print_background=True, margin={"top": "0", "bottom": "0", "left": "0", "right": "0"})
            pg.close()
            print(json.dumps({"idioma": lang, "laminas": n, "pdf": pdf.relative_to(REPO).as_posix(), "desbordes": desbordes}, ensure_ascii=False))
        b.close()
    print(json.dumps({"laminas": len(hechas)}))


def main():
    orden = sys.argv[1] if len(sys.argv) > 1 else "todo"
    if orden in ("figuras", "todo"):
        figuras()
    if orden in ("informe", "todo"):
        informe()
    if orden in ("panel", "todo"):
        panel()
    if orden in ("laminas", "todo"):
        laminas()
    registro = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "orden": orden,
                "cifras_sha256": sha(ENT / "datos/cifras_entregables.json")}
    (ENT / "datos/ultima_construccion.json").write_text(json.dumps(registro, indent=1) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
