"""Convierte las páginas HTML de fuente/paginas.py y fuente/anexos.py en archivos LaTeX editables.

Se usó una sola vez para crear la versión LaTeX; a partir de ahí los .tex son la fuente que se edita.
Uso: python html2tex.py <carpeta fuente> <carpeta latex>
"""
import re, sys
from pathlib import Path
from bs4 import BeautifulSoup, NavigableString, Tag

FUENTE = Path(sys.argv[1] if len(sys.argv) > 1 else "/home/claude/informe_final")
LATEX = Path(sys.argv[2] if len(sys.argv) > 2 else "/home/claude/informe_final/latex")
sys.path.insert(0, str(FUENTE))
import paginas, anexos, charts  # noqa: E402

# ---------------------------------------------------------------- texto
MATEMATICAS = {  # fórmulas MathML de las páginas, escritas a mano en LaTeX
    "<msup><mi>k</mi><mo>*</mo></msup>": r"{\formulasize\[ k^{*} = \frac{\sum \left(y/\sqrt{\mu}\right)}{\sum \sqrt{\mu}} \]}",
    "<mi>P</mi><mo>=</mo>": r"{\formulasize\[ P = \frac{R + 0{,}12\cdot R_{\text{hogar}} + 85}{1 - 0{,}15 - c - 0{,}08 - 0{,}08} \]}",
    "<msup><mi>D</mi><mn>2</mn></msup><mo stretchy": r"{\formulasize\[ D^{2}(c) - D^{2}(1) = -\frac{4}{D_{0}}\left[S_{1}\left(c^{-1/2} - 1\right) + S_{2}\left(c^{1/2} - 1\right)\right] \]}",
}
REEMPLAZOS = [  # fragmentos con símbolos que van mejor en modo matemático
    ("d(y, μ) = 4y/√μ + 4√μ − 8√y", r"$d(y,\mu) = 4y/\sqrt{\mu} + 4\sqrt{\mu} - 8\sqrt{y}$"),
    ("S₁ = Σ y/√μ, S₂ = Σ √μ y D₀", r"$S_1 = \sum y/\sqrt{\mu}$, $S_2 = \sum \sqrt{\mu}$ y $D_0$"),
    ("max(0,7; 3σ)", r"máx(0,7; 3$\sigma$)"),
    ("β (reserva de caso)", r"$\beta$ (reserva de caso)"),
    ("n/(n + K)", r"$n/(n+K)$"),
    ("k<sub>e</sub>", r"$k_e$"),
    ("85·e", r"$85\cdot e$"),
    ("(×1,2231)", r"($\times$1,2231)"),
]


def esc(t):
    """Escapa texto corriente para LaTeX y cuida los espacios de la tipografía española."""
    t = t.replace("\\", r"\textbackslash{}")
    for a, b in [("&", r"\&"), ("%", r"\%"), ("#", r"\#"), ("$", r"\$"), ("_", r"\_"), ("{", r"\{"), ("}", r"\}"), ("~", r"\textasciitilde{}")]:
        t = t.replace(a, b)
    t = re.sub(r"(\d)\s\\%", r"\1~\\%", t)          # 76 % -> 76~\%
    t = t.replace(" ", "~")
    t = re.sub(r"(\d)\.(\d{3})", r"\1.\2", t)        # miles con punto, sin cambios
    return t


def inline(node):
    """Texto con marcas en línea (negrita, cursiva, código, enlaces, subíndices)."""
    out = []
    for c in node.children if isinstance(node, Tag) else [node]:
        if isinstance(c, NavigableString):
            out.append(esc(str(c)))
        elif c.name == "b":
            out.append(r"\textbf{" + inline(c) + "}")
        elif c.name == "i":
            out.append(r"\textit{" + inline(c) + "}")
        elif c.name == "span" and "mono" in c.get("class", []):
            out.append(r"\codigo{" + inline(c) + "}")
        elif c.name == "span" and "small" in c.get("class", []):
            out.append(r"{\small " + inline(c) + "}")
        elif c.name == "span":
            out.append(inline(c))
        elif c.name == "a":
            out.append(r"\href{" + c["href"] + "}{" + inline(c) + "}")
        elif c.name == "sub":
            out.append("$_{" + esc(c.get_text()) + "}$")
        elif c.name == "br":
            out.append(r"\\ ")
        elif c.name == "math":
            out.append(mathml(c))
        else:
            out.append(inline(c))
    s = "".join(out)
    for a, b in REEMPLAZOS:
        s = s.replace(esc(a) if "<" not in a else a, b)
    return s


def mathml(node):
    h = str(node)
    for k, v in MATEMATICAS.items():
        if k in h:
            return v
    raise ValueError("fórmula sin traducción: " + h[:80])


ANEXO = False  # True mientras se convierten los anexos: tablas más compactas


def tabla(t):
    """<table class="tight"> -> entorno tabla con tabularx."""
    filas = t.find_all("tr")
    cab = filas[0]
    cols = []
    for th in cab.find_all("th"):
        w = re.search(r"width:(\d+)%", th.get("style", ""))
        r = "r" in th.get("class", [])
        if w:
            cols.append(("D" if r else "L") + "{" + f"{int(w.group(1))/100:.2f}" + "}")
        else:
            cols.append("R" if r else "Y")
    spec = "@{}" + "".join(cols) + "@{}"
    env = "tablachica" if ANEXO else "tabla"
    out = [r"\begin{" + env + "}", r"\begin{tabularx}{\linewidth}{" + spec + "}"]
    out.append(" & ".join(r"\cab{" + inline(th) + "}" for th in cab.find_all("th")) + r" \\ \cabrule")
    for i, tr in enumerate(filas[1:]):
        tds = tr.find_all("td")
        tot = "tot" in tr.get("class", [])
        celdas = []
        for td in tds:
            c = inline(td)
            if td.get("colspan"):
                c = r"\multicolumn{" + td["colspan"] + "}{@{}l}{" + c + "}"
            celdas.append(c)
        linea = " & ".join(celdas) + r" \\"
        if tot:
            out.append(r"\totrule" + "\n" + r"\rowcolor{totbg} " + linea.replace(r" \\", r" \\"))
        else:
            out.append(linea + (r" \fila" if i < len(filas) - 2 and "tot" not in filas[i + 2].get("class", []) else ""))
    out.append(r"\end{tabularx}")
    out.append(r"\end{" + env + "}")
    return "\n".join(out)


def flujo(div):
    """Figura 1: tabla de seis etapas por dos semanas."""
    cells = [c for c in div.find_all("div", recursive=False)]
    etapas = [c for c in cells if "st" in c.get("class", [])]
    filas = []
    for cls in ("c1", "c2"):
        filas.append([c for c in cells if cls in c.get("class", [])])
    rl = [c for c in cells if "rl" in c.get("class", [])]
    out = [r"% Figura 1: flujo de las dos semanas (editar las celdas directamente)",
           r"\begin{center}\fontsize{7.1pt}{9pt}\selectfont\setlength{\tabcolsep}{1.3mm}\renewcommand{\arraystretch}{1.05}",
           r"\begin{tabularx}{\textwidth}{@{}L{0.09}!{\color{white}\vrule width 1.2mm}" + ("Y!{\\color{white}\\vrule width 1.2mm}" * 5) + "Y@{}}"]
    e = []
    for st in etapas:
        sp = st.find("span")
        tit = esc(st.contents[0].strip())
        e.append(r"\etapa{" + tit + "}{" + esc(sp.get_text()) + "}")
    out.append(" & " + " & ".join(e) + r" \\ \noalign{\vskip 1.2mm}")
    for k, fila in enumerate(filas):
        lab = rl[k]
        semana = esc(lab.contents[0].strip())
        sub = esc(lab.find("span").get_text())
        macro = r"\cuno" if k == 0 else r"\cdos"
        out.append(r"\semana{" + semana + "}{" + sub + "} & " + " & ".join(macro + "{" + inline(c) + "}" for c in fila)
                   + (r" \\ \noalign{\vskip 1.2mm}" if k == 0 else r" \\"))
    out.append(r"\end{tabularx}\end{center}\vspace{-2.5mm}")
    return "\n".join(out)


def protocolo(div):
    out = [r"% Figura 5: protocolo de trabajo con IA (seis pasos)",
           r"\begin{tcbraster}[raster columns=6, raster equal height, raster column skip=1.6mm, raster before skip=1.2mm, raster after skip=0.6mm]"]
    pasos = div.find_all("div", recursive=False)
    for i, pdiv in enumerate(pasos):
        b = pdiv.find("b")
        tit = esc(b.get_text())
        resto = esc("".join(str(x) for x in pdiv.contents if isinstance(x, NavigableString)).strip())
        h = "h" in pdiv.get("class", [])
        opts = "colback=brand, colframe=brand, coltext=white" if h else ""
        flecha = "" if i == len(pasos) - 1 else r", overlay={\node[anchor=west, inner sep=0pt] at ([xshift=0.35mm]frame.east) {\color{brand}\bfseries\fontsize{10pt}{10pt}\selectfont›};}"
        titcol = r"{\color{white}\semibold\fontsize{7.5pt}{9pt}\selectfont " + tit + r"\par}\vspace{0.3mm}" if h else r"\pasotit{" + tit + "}"
        out.append(r"\begin{paso}[" + opts + flecha + "]" + titcol + resto + r"\end{paso}")
    out.append(r"\end{tcbraster}")
    return "\n".join(out)


def kpis(div):
    items = div.find_all("div", class_="kpi")
    n = len(items)
    out = [r"\setlength{\kpiancho}{\dimexpr(\textwidth-" + f"{2.2*(n-1):.1f}" + r"mm)/" + str(n) + r"\relax}",
           r"\vspace{1.2mm}\noindent"]
    out.append(r"\hfill".join(r"\kpi{" + inline(k.find("div", class_="v")) + "}{" + inline(k.find("div", class_="l")) + "}" for k in items))
    out.append(r"\par\vspace{2.4mm}")
    return "\n".join(out)


def glosario(div):
    items = div.find_all("div", recursive=False)
    out = [r"\begin{glosario}\fontsize{7.4pt}{9.6pt}\selectfont\setlength{\tabcolsep}{1.6mm}",
           r"\begin{tabularx}{\linewidth}{@{}YYY@{}}"]
    filas = [items[i:i + 3] for i in range(0, len(items), 3)]
    for k, f in enumerate(filas):
        celdas = []
        for it in f:
            b = it.find("b")
            resto = esc("".join(str(x) for x in it.contents if isinstance(x, NavigableString)).strip())
            celdas.append(r"\gl{" + esc(b.get_text()) + "}{" + resto + "}")
        out.append(" & ".join(celdas) + (r" \\[1.2mm]" if k < len(filas) - 1 else r" \\"))
    out.append(r"\end{tabularx}\end{glosario}")
    return "\n".join(out)


def definiciones(div):
    items = div.find_all("div", class_="def")
    out = [r"\vspace{0.6mm}\noindent\setlength{\tabcolsep}{0pt}", r"\begin{tabularx}{\linewidth}{@{}Y@{\hspace{4mm}}Y@{}}"]
    for i in range(0, len(items), 2):
        par = items[i:i + 2]
        celdas = [r"\definicion{" + esc(d.find("h4").get_text()) + "}{" + inline(d.find("p")) + "}" for d in par]
        out.append(" & ".join(celdas) + (r" \\[1.4mm]" if i + 2 < len(items) else r" \\"))
    out.append(r"\end{tabularx}\par\vspace{1mm}")
    return "\n".join(out)


def bloque(node, col=False):
    """Convierte un nodo de bloque; col=True dentro de una columna (sin \\section)."""
    if isinstance(node, NavigableString):
        s = str(node).strip()
        if not s:
            return ""
        m = re.fullmatch(r"\{\{FIG:(\w+)\}\}", s)
        if m:
            return r"\includegraphics[width=\linewidth]{figuras/" + m.group(1) + ".pdf}"
        m = re.fullmatch(r"\{\{TABLA:(\w+)\}\}", s)
        if m:
            return r"\input{tablas/" + m.group(1) + "}"
        return esc(s)
    n, cls = node.name, node.get("class", [])
    if n == "h1":
        return r"\titulo{" + inline(node) + "}"
    if n == "h2":
        return r"\section*{" + inline(node) + "}"
    if n == "h3":
        return r"\subsection*{" + inline(node) + "}"
    if n == "p":
        if "sub" in cls:
            return r"\subtitulo{" + inline(node) + "}"
        if "byline" in cls:
            return r"\byline{" + inline(node) + "}"
        if "lead" in cls:
            return r"\lead{" + inline(node) + "}"
        if "cap" in cls:
            b = node.find("b")
            if b and node.contents[0] is b:
                resto = "".join(inline(x) for x in node.contents[1:]).strip()
                return r"\pie{" + inline(b) + "}{" + resto + "}"
            return r"\pie{}{" + inline(node) + "}"
        if "small" in cls:
            return r"\chico{" + inline(node) + "}"
        if "ref" in cls:
            return r"\item " + inline(node)
        return inline(node) + r"\par"
    if n == "math":
        return mathml(node)
    if n == "table":
        return tabla(node)
    if n == "ul":
        return r"\begin{itemize}[leftmargin=4mm, itemsep=0.5mm, topsep=0.4mm, parsep=0pt]" + "\n" + "\n".join(
            r"\item " + inline(li) for li in node.find_all("li")) + "\n" + r"\end{itemize}"
    if n == "div":
        if "kpis" in cls:
            return kpis(node)
        if "flow" in cls:
            return flujo(node)
        if "proto" in cls:
            return protocolo(node)
        if "gloss" in cls:
            return glosario(node)
        if "defs" in cls:
            return definiciones(node)
        if "refs" in cls:  # el marcador {{REFS}} se rellena con anexos.REFERENCIAS
            refs = [inline(BeautifulSoup(r, "html.parser")) for r in anexos.REFERENCIAS]
            return (r"\begin{enumerate}[leftmargin=5mm, itemsep=0.4mm, topsep=0.4mm, parsep=0pt]\small" + "\n"
                    + "\n".join(r"\item " + r for r in refs) + "\n" + r"\end{enumerate}")
        if "box" in cls:
            h4 = node.find("h4")
            cuerpo = "\n".join(bloque(c, col) for c in node.children if not (isinstance(c, Tag) and c.name == "h4"))
            if h4:
                return r"\begin{recuadro}{" + inline(h4) + "}" + "\n" + cuerpo.strip() + "\n" + r"\end{recuadro}"
            return r"\begin{recuadrosin}" + "\n" + cuerpo.strip() + "\n" + r"\end{recuadrosin}"
        for c, frac in (("cols-6040", "0.575"), ("cols-4060", "0.45"), ("cols-6535", "0.65"), ("cols", "0.5")):
            if c in cls:
                hijos = [x for x in node.children if isinstance(x, Tag)]
                izq = "\n".join(bloque(x, True) for x in hijos[0].children) if hijos[0].name == "div" and not hijos[0].get("class") else bloque(hijos[0], True)
                der = "\n".join(bloque(x, True) for x in hijos[1].children) if hijos[1].name == "div" and not hijos[1].get("class") else bloque(hijos[1], True)
                return r"\dos{" + frac + "}{%" + "\n" + izq.strip() + "\n}{%\n" + der.strip() + "\n}"
        return "\n".join(bloque(c, col) for c in node.children)
    return inline(node)


def pagina(html):
    soup = BeautifulSoup(html, "html.parser")
    partes = [bloque(c) for c in soup.contents]
    return "\n\n".join(p for p in partes if p.strip()) + "\n"


# ---------------------------------------------------------------- tablas generadas
def es(v, d=2):
    return charts.es(v, d)


def tabla_primas():
    import pandas as pd
    d = pd.read_csv(FUENTE / "prima_comercial_F3c_20ref.csv")
    ramo = {"motor": "Autos", "buildings": "Edificios", "contents": "Contenidos"}
    canal = {"broker": "Corredor", "direct": "Directo"}
    e = d.exposure  # exposición exacta (cuatro decimales en el CSV)
    out = [r"% Tabla de la página 5: generada por html2tex.py desde prima_comercial_F3c_20ref.csv (prima_comercial_20ref.py).",
           r"\begin{tabla}\fontsize{7pt}{8.2pt}\selectfont\setlength{\tabcolsep}{0.9mm}\renewcommand{\arraystretch}{1.0}",
           r"\begin{tabularx}{\linewidth}{@{}lllRRRRRRR@{}}",
           r"\cab{Póliza} & \cab{Ramo} & \cab{Canal} & \cab{Exposición} & \cab{Prima de riesgo R} & \cab{Catástrofe} & \cab{Gasto fijo} & \cab{Prima comercial P} & \cab{Prima escrita anual} & \cab{P anualizada / escrita} \\ \cabrule"]
    for i, r in d.iterrows():
        out.append(f"{r.row_id} & {ramo[r.line]} & {canal[r.channel]} & {es(r.exposure)} & {es(r.R)} & {es(r['cat'])} & {es(r.fijo)} & "
                   f"\\textbf{{{es(r.P)}}} & {es(r.written_premium)} & {es(r.P / e[i] / r.written_premium)} \\\\" + (r" \fila" if i < len(d) - 1 else ""))
    for l in ["motor", "buildings", "contents"]:
        s = d[d.line == l]; ee = s.exposure
        out.append(r"\totrule" + "\n" + r"\rowcolor{totbg} \multicolumn{4}{@{}l}{\textbf{Total " + ramo[l].lower() + "}} & "
                   + " & ".join(r"\textbf{" + x + "}" for x in [es(s.R.sum()), es(s["cat"].sum()), es(s.fijo.sum()), es(s.P.sum()), es(s.written_premium.sum()), es((s.P / ee).sum() / s.written_premium.sum())]) + r" \\")
    ee = d.exposure
    out.append(r"\totrule" + "\n" + r"\rowcolor{totbg} \multicolumn{4}{@{}l}{\textbf{Total de las 20 pólizas}} & "
               + " & ".join(r"\textbf{" + x + "}" for x in [es(d.R.sum()), es(d["cat"].sum()), es(d.fijo.sum()), es(d.P.sum()), es(d.written_premium.sum()), es((d.P / ee).sum() / d.written_premium.sum())]) + r" \\")
    out += [r"\end{tabularx}", r"\end{tabla}"]
    return "\n".join(out) + "\n"


def tabla_lista(cabeceras, filas, spec, chips=False):
    out = [r"\begin{tablachica}", r"\begin{tabularx}{\linewidth}{" + spec + "}",
           " & ".join(r"\cab{" + esc(c) + "}" for c in cabeceras) + r" \\ \cabrule"]
    for i, f in enumerate(filas):
        celdas = [esc(x) for x in f]
        out.append(" & ".join(celdas) + r" \\" + (r" \fila" if i < len(filas) - 1 else ""))
    out += [r"\end{tabularx}", r"\end{tablachica}"]
    return "\n".join(out) + "\n"


def tabla_experimentos():
    filas = []
    for s, e, r, c, d in anexos.EXPERIMENTOS:
        filas.append((s, e, r, r"\chip{" + c + "}{" + esc(d) + "}"))
    out = [r"% Anexo A: experimentos (anexos.py). Chips: ok = entró, alt = alternativa, no = descartado.",
           r"\begin{tablachica}", r"\begin{tabularx}{\linewidth}{@{}L{0.06}L{0.31}YL{0.20}@{}}",
           r"\cab{Sem.} & \cab{Experimento} & \cab{Resultado medido} & \cab{Decisión} \\ \cabrule"]
    for i, (s, e, r, d) in enumerate(filas):
        out.append(f"{esc(s)} & {esc(e)} & {esc(r)} & {d} \\\\" + (r" \fila" if i < len(filas) - 1 else ""))
    out += [r"\end{tabularx}", r"\end{tablachica}"]
    return "\n".join(out) + "\n"


def tabla_shas():
    out = [r"\begin{tablachica}", r"\begin{tabularx}{\linewidth}{@{}L{0.32}L{0.18}Y@{}}",
           r"\cab{Entrega} & \cab{SHA-256 (inicio)} & \cab{Cómo se regenera} \\ \cabrule"]
    for i, (a, b, c) in enumerate(anexos.SHAS):
        out.append(esc(a) + r" & \codigo{" + esc(b) + "} & " + esc(c) + r" \\" + (r" \fila" if i < len(anexos.SHAS) - 1 else ""))
    out += [r"\end{tabularx}", r"\end{tablachica}"]
    return "\n".join(out) + "\n"


def main():
    (LATEX / "paginas").mkdir(exist_ok=True); (LATEX / "anexos").mkdir(exist_ok=True); (LATEX / "tablas").mkdir(exist_ok=True)
    anexos.SHAS[1] = ("final_creible, parte 2", "1a003d8682f1…", "construir_final.py con los recibos de las sondas")
    nombres = ["01_resumen", "02_definiciones_datos", "03_modelos", "04_ia_validacion", "05_prima_comercial"]
    for n, html in zip(nombres, [paginas.P1, paginas.P2, paginas.P3, paginas.P4, paginas.P5]):
        (LATEX / "paginas" / f"{n}.tex").write_text(f"% Página {n[:2]} (calificada)\n" + pagina(html))
    an = ["06_anexo_a_experimentos", "07_anexo_b_sensibilidad", "08_anexo_b_c_d", "09_anexo_e_f", "10_anexo_g_h_i"]
    global ANEXO
    ANEXO = True
    for n, html in zip(an, anexos.PAGINAS):
        (LATEX / "anexos" / f"{n}.tex").write_text(f"% Página {n[:2]} (anexo)\n" + pagina(html))
    (LATEX / "tablas" / "primas.tex").write_text(tabla_primas())
    (LATEX / "tablas" / "experimentos.tex").write_text(tabla_experimentos())
    (LATEX / "tablas" / "crono.tex").write_text("% Anexo E: cronología (anexos.py)\n" + tabla_lista(
        ["Fecha", "Hito", "Resultado y lectura"], anexos.CRONO, "@{}L{0.09}L{0.48}Y@{}"))
    (LATEX / "tablas" / "herramientas.tex").write_text("% Anexo F: herramientas (anexos.py)\n" + tabla_lista(
        ["Herramienta", "Uso concreto", "Control que la acompañó"], anexos.HERRAMIENTAS, "@{}L{0.27}L{0.38}Y@{}"))
    (LATEX / "tablas" / "shas.tex").write_text("% Anexo G: huellas de las entregas (anexos.py)\n" + tabla_shas())
    print("archivos escritos en", LATEX)


if __name__ == "__main__":
    main()
