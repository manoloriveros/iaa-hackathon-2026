"""Gráficos SVG del informe final. Cada función devuelve un SVG en línea.

El ancho del viewBox coincide con el ancho físico del hueco donde va cada
figura (96 px por pulgada), así 1 unidad del SVG es 1 px de la página y los
tamaños de letra son reales. Las cifras vienen de las fuentes citadas en el
pie de cada figura.
"""
import math

INK = "#1b2a33"
QUIET = "#5b6b76"
GRID = "#e4e9ec"
AXIS = "#a9b4bb"
ACCENT = "#2a6fb0"
ACCENT_SOFT = "#a9c6e4"
MUTED = "#b9c3c9"
MUTED_SOFT = "#dde3e7"
BRAND = "#174f59"
FS = 9.6     # letra de etiquetas
FS_S = 8.8   # letra de ejes


def es(v, d=2, signo=False):
    s = f"{abs(v):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if signo:
        return ("+" if v > 0 else ("−" if v < 0 else "")) + s
    return ("−" if v < 0 else "") + s


def svg(w, h, body, label):
    return (f'<svg viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{label}" '
            f'style="font-family:InterTT,Inter,sans-serif;display:block;max-width:100%;height:auto" '
            f'xmlns="http://www.w3.org/2000/svg">{body}</svg>')


def t(x, y, s, size=FS, fill=INK, anchor="start", weight=400):
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{fill}" text-anchor="{anchor}" '
            f'font-weight="{weight}">{s}</text>')


def line(x1, y1, x2, y2, stroke, extra=""):
    return f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{stroke}" {extra}/>'


# ---------------------------------------------------------------- figura 2 (hueco ~284 px)
def completitud():
    filas = [("Lesiones corporales (autos)", 0.5634), ("Hundimiento (edificios)", 0.6626),
             ("Daños a terceros (autos)", 0.9407), ("Escape de agua (edificios)", 0.9543),
             ("Inundación (contenidos)", 0.9627), ("Robo (autos)", 0.9810)]
    w, x0, x1, y0, step = 284, 134, 250, 12, 21
    b = []
    for i, (n, v) in enumerate(filas):
        y = y0 + i * step
        bajo = v < 0.9
        b.append(t(x0 - 6, y + 4, n, FS_S, INK if bajo else QUIET, "end", 600 if bajo else 400))
        b.append(f'<rect x="{x0}" y="{y-6}" width="{x1-x0}" height="12" fill="{MUTED_SOFT}"/>')
        b.append(f'<rect x="{x0}" y="{y-6}" width="{(x1-x0)*v:.1f}" height="12" fill="{ACCENT if bajo else MUTED}"/>')
        b.append(t(x1 + 4, y + 4, f"{round(v*100)} %", FS_S, INK if bajo else QUIET, "start", 600 if bajo else 400))
    return svg(w, y0 + len(filas) * step - 4, "".join(b), "Parte de la exposición de 2024 ya reportada por peligro")


# ---------------------------------------------------------------- figura 3 (ancho completo ~688 px)
def mezcla_peligros():
    datos = {
        "Autos": [("Daños a terceros", .305, .339), ("Lesiones corporales", .331, .303), ("Daños propios", .220, .192),
                  ("Robo", .099, .101), ("Lunas y granizo", .046, .065)],
        "Edificios": [("Incendio", .226, .455), ("Inundación", .277, .222), ("Escape de agua", .239, .109),
                      ("Tormenta", .114, .127), ("Hundimiento", .127, .076), ("Daño accidental", .018, .011)],
        "Contenidos": [("Robo", .428, .472), ("Inundación", .248, .305), ("Escape de agua", .217, .140),
                       ("Daño accidental", .107, .082)],
    }
    w, panel, step, y0 = 688, 229, 18, 30
    ybot = y0 + 5 * step + 8
    b = []
    for k, (ramo, filas) in enumerate(datos.items()):
        ox = k * panel
        xa, xb = ox + 104, ox + 218
        X = lambda v, xa=xa, xb=xb: xa + v / 0.5 * (xb - xa)
        b.append(t(ox + 2, 12, ramo, 10.2, INK, "start", 650))
        for tk in (0, .25, .5):
            b.append(line(X(tk), y0 - 9, X(tk), ybot, GRID))
            b.append(t(X(tk), ybot + 11, f"{int(tk*100)} %", FS_S, QUIET, "middle"))
        for i, (p, d, e) in enumerate(filas):
            y = y0 + i * step
            fuerte = abs(e - d) >= 0.1
            b.append(t(xa - 7, y + 3.5, p, FS_S, INK if fuerte else QUIET, "end", 650 if fuerte else 400))
            b.append(line(X(d), y, X(e), y, ACCENT if fuerte else MUTED, 'stroke-width="2"'))
            b.append(f'<circle cx="{X(d):.1f}" cy="{y}" r="3.7" fill="{MUTED}"/>')
            b.append(f'<circle cx="{X(e):.1f}" cy="{y}" r="3.7" fill="{ACCENT}"/>')
    h = ybot + 26
    leg = (f'<circle cx="{w-270}" cy="{h-6}" r="3.7" fill="{MUTED}"/>' + t(w - 262, h - 2.5, "Mercado desarrollado", FS_S, QUIET) +
           f'<circle cx="{w-140}" cy="{h-6}" r="3.7" fill="{ACCENT}"/>' + t(w - 132, h - 2.5, "Mercado emergente", FS_S, INK))
    return svg(w, h, "".join(b) + leg, "Cuota del coste por peligro en cada ramo, desarrollado frente a emergente")


# ---------------------------------------------------------------- figura 4 (hueco ~301 px)
def escalera_2023():
    filas = [("Tasa constante por ramo", .068, False), ("GLM solo emergente", .080, False),
             ("Boosting solo emergente", .083, False), ("Transferido del desarrollado", .1213, True)]
    w, xa, xb, y0, step = 300, 140, 262, 12, 22
    X = lambda v: xa + v / 0.13 * (xb - xa)
    b = []
    for i, (n, v, a) in enumerate(filas):
        y = y0 + i * step
        b.append(t(xa - 6, y + 4, n, FS_S, INK if a else QUIET, "end", 650 if a else 400))
        b.append(f'<rect x="{xa}" y="{y-7}" width="{X(v)-xa:.1f}" height="14" fill="{ACCENT if a else MUTED}"/>')
        b.append(t(X(v) + 4, y + 4, es(v, 3), FS_S, INK if a else QUIET, "start", 650 if a else 400))
    return svg(w, y0 + len(filas) * step - 6, "".join(b), "D² fuera de muestra en 2023 por enfoque")


# ---------------------------------------------------------------- figura 5 (hueco ~368 px)
def escalera_publico():
    pasos = [("Mezcla inicial", .15390, None, None, None),
             ("Nivel global", .15948, .15948, .15948, "t"),
             ("Declarados y bonificación", .16033, None, None, "m"),
             ("Nivel por celda y forma", .16519, .16511, .16522, "t"),
             ("Factores propios del emergente", .16914, .1647, .1682, "m")]
    w, xa, xb, y0, step = 368, 150, 304, 24, 20
    lo, hi = .152, .1745
    X = lambda v: xa + (v - lo) / (hi - lo) * (xb - xa)
    ybot = y0 + 4 * step + 9
    b = []
    for tk in (.155, .160, .165, .170):
        b.append(line(X(tk), y0 - 12, X(tk), ybot, GRID))
        b.append(t(X(tk), ybot + 11, es(tk, 3), FS_S, QUIET, "middle"))
    lider = .17303
    b.append(line(X(lider), y0 - 12, X(lider), ybot, QUIET, 'stroke-dasharray="3 3"'))
    b.append(t(X(lider) - 2, y0 - 16, "Líder 0,17303", FS_S, QUIET, "end"))
    b.append(t(w, y0 - 16, "D² público", FS_S, QUIET, "end", 650))
    prev = None
    for i, (n, v, pl, ph, src) in enumerate(pasos):
        y = y0 + i * step
        ult = i == len(pasos) - 1
        b.append(t(xa - 7, y + 3.5, n, FS_S, INK if src == "m" else QUIET, "end", 650 if src == "m" else 400))
        if pl is not None and ph > pl:
            b.append(f'<rect x="{X(pl):.1f}" y="{y-6}" width="{X(ph)-X(pl):.1f}" height="12" rx="2" fill="{MUTED_SOFT}" opacity=".7"/>')
        if prev is not None:
            col = ACCENT if src == "m" else "#8d99a1"
            b.append(f'<rect x="{X(prev):.1f}" y="{y-4}" width="{X(v)-X(prev):.1f}" height="8" fill="{col}"/>')
            b.append(line(X(prev), y - step + 5, X(prev), y - 4, AXIS, 'stroke-dasharray="2 2"'))
        b.append(f'<circle cx="{X(v):.1f}" cy="{y}" r="3.4" fill="{INK}"/>')
        b.append(t(w, y + 3.5, es(v, 5), FS_S, INK if ult else QUIET, "end", 650 if ult else 400))
        prev = v
    return svg(w, ybot + 16, "".join(b), "Escalera del tablero público de la semana 2 por origen de la mejora")


# ---------------------------------------------------------------- figura 7 (hueco ~284 px)
def prevision_medido():
    grupos = [("Calibración controlada", [("Nivel por ramo, parte 1", .130158, .130158, .130158, .13016),
                                           ("Nivel revisado, parte 1", .13033, .13033, .13033, .13033),
                                           ("Forma por ramo, parte 1", .13048, .13048, .13048, .13048),
                                           ("Nivel global", .15948, .15948, .15948, .15948),
                                           ("Nivel por celda y forma", .165165, .16511, .16522, .16519)]),
              ("Cambios del modelo", [("Declarados y bonificación", .16198, .16148, .16248, .16033),
                                      ("Factores propios", .1666, .1647, .1682, .16914)])]
    w, xa, xb = 284, 120, 272
    lo, hi = -.0030, .0030
    X = lambda v: xa + (v - lo) / (hi - lo) * (xb - xa)
    b = []
    y = 12
    rows = []
    for g, casos in grupos:
        b.append(t(4, y + 3, g, 8.4, BRAND, "start", 700))
        y += 15
        for c in casos:
            rows.append((y, c)); y += 17
        y += 4
    ybot = y - 6
    for tk in (-.002, 0, .002):
        b.insert(0, line(X(tk), 6, X(tk), ybot, AXIS if tk == 0 else GRID))
        b.append(t(X(tk), ybot + 11, "0" if tk == 0 else es(tk, 3, True), FS_S, QUIET, "middle"))
    for y, (n, p, lo_, hi_, m) in rows:
        d = m - p
        fuera = m > hi_ + 6e-6 or m < lo_ - 6e-6
        b.append(t(xa - 7, y + 3.5, n, FS_S, INK if fuera else QUIET, "end", 650 if fuera else 400))
        if hi_ > lo_:
            b.append(f'<rect x="{X(lo_-p):.1f}" y="{y-5}" width="{X(hi_-p)-X(lo_-p):.1f}" height="10" rx="2" fill="{MUTED_SOFT}"/>')
        b.append(f'<circle cx="{X(d):.1f}" cy="{y}" r="3.8" fill="{ACCENT if fuera else INK}"/>')
        if fuera:
            if d > 0:
                b.append(t(X(d) - 7, y + 3.5, es(d, 5, True), FS_S, INK, "end", 650))
            else:
                b.append(t(X(d) + 7, y + 3.5, es(d, 5, True), FS_S, INK, "start", 650))
    return svg(w, ybot + 15, "".join(b), "Puntuación medida menos prevista antes de cada envío")


# ---------------------------------------------------------------- anexo B1 (hueco ~334 px)
def tornado_s1():
    filas = [("Año base, edificios", -3.44, 3.44, "±3,44 %"),
             ("IBNR de autos (sesgo)", .80, 1.75, "+0,80 a +1,75 %"),
             ("Año base, autos", -.92, .92, "±0,92 %"),
             ("Recobros de abiertos, autos", -.75, 0, "−0,75 %"),
             ("Año base, contenidos", -.68, .68, "±0,68 %"),
             ("Capitales sin confirmar", 0, .02, "< 0,02 %")]
    w, xa, xb, y0, step, xv = 334, 128, 254, 24, 19, 260
    lo, hi = -4, 4
    X = lambda v: xa + (v - lo) / (hi - lo) * (xb - xa)
    yb = y0 + 5 * step + 9
    b = [f'<rect x="{X(-1):.1f}" y="{y0-12}" width="{X(1)-X(-1):.1f}" height="{yb-y0+12}" fill="{MUTED_SOFT}" opacity=".6"/>',
         t(X(0), y0 - 15, "Materialidad ±1 %", FS_S, QUIET, "middle")]
    for tk in (-4, -2, 0, 2, 4):
        b.append(line(X(tk), yb, X(tk), yb + 4, AXIS))
        b.append(t(X(tk), yb + 14, ("0" if tk == 0 else f"{'+' if tk>0 else '−'}{abs(tk)} %"), FS_S, QUIET, "middle"))
    b.append(line(X(0), y0 - 12, X(0), yb, AXIS))
    b.append(line(xa, yb, xb, yb, AXIS))
    for i, (n, a, c, nota) in enumerate(filas):
        y = y0 + i * step
        sup = max(abs(a), abs(c)) > 1
        b.append(t(xa - 6, y + 3.5, n, FS_S, INK if sup else QUIET, "end", 650 if sup else 400))
        b.append(f'<rect x="{X(a):.1f}" y="{y-5}" width="{max(X(c)-X(a),1.5):.1f}" height="10" fill="{ACCENT if sup else MUTED}"/>')
        b.append(t(xv, y + 3.5, nota, FS_S, INK if sup else QUIET, "start", 650 if sup else 400))
    return svg(w, yb + 20, "".join(b), "Sensibilidad del nivel de 2025 en la semana 1")


# ---------------------------------------------------------------- anexo B2 (hueco ~334 px)
def cadena_privado():
    pasos = [("Nivel global (F)", .00558, .0042, .0054), ("Declarados y NCB (F2)", .00085, .00101, .00187),
             ("Nivel por celda*", .00486, .0009, .0018), ("Forma por celda*", None, -.0023, .0025),
             ("Factores propios (F3c)", .00395, .00364, .0039)]
    w, xa, xb, y0, step = 334, 124, 314, 12, 20
    lo, hi = -.003, .0062
    X = lambda v: xa + (v - lo) / (hi - lo) * (xb - xa)
    yb = y0 + 4 * step + 8
    b = []
    for tk in (-.002, 0, .002, .004, .006):
        b.append(line(X(tk), y0 - 9, X(tk), yb, AXIS if tk == 0 else GRID))
        b.append(t(X(tk), yb + 11, "0" if tk == 0 else es(tk, 3, True), FS_S, QUIET, "middle"))
    for i, (n, p, a, c) in enumerate(pasos):
        y = y0 + i * step
        b.append(t(xa - 6, y + 3.5, n, FS_S, INK, "end"))
        b.append(f'<rect x="{X(a):.1f}" y="{y-4.5}" width="{X(c)-X(a):.1f}" height="9" rx="2" fill="{MUTED}"/>')
        if p is not None:
            b.append(f'<circle cx="{X(p):.1f}" cy="{y}" r="3.8" fill="{ACCENT}"/>')
    h = yb + 30
    leg = (f'<circle cx="{xa}" cy="{h-7}" r="3.6" fill="{ACCENT}"/>' + t(xa + 7, h - 3.5, "Público", FS_S, QUIET) +
           f'<rect x="{xa+56}" y="{h-11}" width="16" height="8" rx="2" fill="{MUTED}"/>' + t(xa + 76, h - 3.5, "Esperado en el privado", FS_S, QUIET))
    return svg(w, h, "".join(b) + leg, "Ganancia pública y esperada en el privado por paso")


# ---------------------------------------------------------------- anexo B3 (ancho completo ~688 px)
def reservas():
    filas = [("Autos, reserva de caso", .697, 1.321, .955, 1.045, .647, .997, .797, True, "−0,66 %"),
             ("Edificios, reserva de caso", .751, 1.255, .926, 1.074, .500, 1.333, .974, True, "−0,10 %"),
             ("Contenidos, reserva de caso", .533, 1.479, .866, 1.134, .740, 2.078, 1.222, True, "+0,47 %"),
             ("Autos, IBNR", .341, 2.001, .885, 1.121, .912, 1.718, 1.267, False, "+0,31 %"),
             ("Autos, IBNR de lesiones", .243, 2.572, .855, 1.160, 1.021, 2.021, 1.427, False, "+0,36 %"),
             ("Edificios, IBNR", 0, 2.501, .633, 1.402, .551, 1.686, .991, False, "−0,01 %"),
             ("Contenidos, IBNR", 0, 2.8, .522, 1.489, .230, 1.271, .674, False, "−0,19 %")]
    w, xa, xb, y0, step = 688, 150, 500, 26, 20
    hi = 2.8
    X = lambda v: xa + min(v, hi) / hi * (xb - xa)
    yb = y0 + 6 * step + 10
    b = [t(522, y0 - 14, "Clase", FS_S, QUIET, "start", 650), t(w, y0 - 14, "F3c en el punto", FS_S, QUIET, "end", 650)]
    for tk in (0, .5, 1, 1.5, 2, 2.5):
        b.append(line(X(tk), y0 - 10, X(tk), yb, GRID))
        b.append(t(X(tk), yb + 11, es(tk, 1).replace(",0", ""), FS_S, QUIET, "middle"))
    b.append(line(X(1), y0 - 10, X(1), yb, QUIET, 'stroke-dasharray="3 3"'))
    for i, (n, fa, fb, ma, mb, ea, eb, e, mat, cam) in enumerate(filas):
        y = y0 + i * step
        col = ACCENT if mat else INK
        op = 1 if mat else .6
        b.append(t(xa - 8, y + 3.5, n, FS_S, INK if mat else QUIET, "end", 650 if mat else 400))
        b.append(f'<rect x="{X(fa):.1f}" y="{y-7}" width="{X(fb)-X(fa):.1f}" height="14" fill="{MUTED_SOFT}"/>')
        b.append(f'<rect x="{X(ma):.1f}" y="{y-7}" width="{X(mb)-X(ma):.1f}" height="14" fill="{MUTED}"/>')
        b.append(line(X(ea), y, X(eb), y, col, f'stroke-width="3" opacity="{op}"'))
        b.append(f'<circle cx="{X(e):.1f}" cy="{y}" r="3.6" fill="{col}" opacity="{op}"/>')
        b.append(t(522, y + 3.5, "Incertidumbre material" if mat else "Acotado", FS_S, INK if mat else QUIET, "start", 650 if mat else 400))
        b.append(t(w, y + 3.5, cam, FS_S, QUIET, "end"))
    h = yb + 30
    leg = (f'<rect x="{xa}" y="{h-11}" width="16" height="8" fill="{MUTED_SOFT}"/>' + t(xa + 20, h - 4, "Rango con nivel recalibrado", FS_S, QUIET) +
           f'<rect x="{xa+190}" y="{h-11}" width="16" height="8" fill="{MUTED}"/>' + t(xa + 210, h - 4, "Rango con nivel fijo", FS_S, QUIET) +
           line(xa + 310, h - 7, xa + 327, h - 7, ACCENT, 'stroke-width="3"') + t(xa + 332, h - 4, "Estimación con los datos (IC90)", FS_S, QUIET))
    return svg(w, h, "".join(b) + leg, "Acreditación de reservas para F3c")


# ---------------------------------------------------------------- anexo B4 (hueco ~334 px)
def credibilidad_k():
    ks = [30, 60, 100, 150, 300]
    series = [("Contenidos, 2023 → 2024", [.00780, .00759, .00695, .00619, .00464], ACCENT, 1),
              ("Contenidos, 2024 → 2023", [.00847, .00827, .00749, .00659, .00483], ACCENT, .5),
              ("Autos, 2023 → 2024", [.00284, .00282, .00278, .00274, .00262], "#7d8b94", 1),
              ("Autos, 2024 → 2023", [.00160, .00162, .00166, .00169, .00175], "#7d8b94", .5)]
    w, xa, xb, y0, yb = 334, 42, 196, 20, 150
    X = lambda k: xa + (math.log(k) - math.log(25)) / (math.log(340) - math.log(25)) * (xb - xa)
    Y = lambda v: yb - v / .009 * (yb - y0)
    b = []
    for v in (0, .002, .004, .006, .008):
        b.append(line(xa, Y(v), xb, Y(v), AXIS if v == 0 else GRID))
        b.append(t(xa - 4, Y(v) + 3, "0" if v == 0 else es(v, 3, True), FS_S, QUIET, "end"))
    for k in ks:
        b.append(t(X(k), yb + 12, str(k), FS_S, QUIET, "middle"))
    for k, nom in ((60, "F3d"), (300, "F3c")):
        b.append(line(X(k), y0 - 4, X(k), yb, QUIET, 'stroke-dasharray="3 3"'))
        b.append(t(X(k), y0 - 8, f"{nom}, K = {k}", FS_S, QUIET, "middle"))
    for j, (n, vals, c, op) in enumerate(series):
        pts = " ".join(f"{X(k):.1f},{Y(v):.1f}" for k, v in zip(ks, vals))
        b.append(f'<polyline points="{pts}" fill="none" stroke="{c}" stroke-opacity="{op}" stroke-width="1.8"/>')
        for k, v in zip(ks, vals):
            b.append(f'<circle cx="{X(k):.1f}" cy="{Y(v):.1f}" r="2.4" fill="{c}" fill-opacity="{op}"/>')
        ly = 46 + j * 16
        b.append(line(206, ly, 220, ly, c, f'stroke-opacity="{op}" stroke-width="1.8"'))
        b.append(t(224, ly + 3, n, 8.2, INK if c == ACCENT else QUIET))
    b.append(t(xb, yb + 25, "K, escala logarítmica", FS_S, QUIET, "end"))
    return svg(w, yb + 30, "".join(b), "Ganancia fuera de tiempo de los factores según K")


# Esquemas editoriales adaptados del panel; no incorporan pesos o métricas nuevos.
def esquema_modelo():
    b=[]
    for x,w,col,title,sub in [(0,214,'#fbede6','Coste total con árboles','Tweedie: ceros y costes positivos'),(242,260,'#e8f0f9','Frecuencia × severidad','por causa de siniestro'),(528,160,'#e8f1f2','Combinación por ramo','prima de riesgo')]:
        b.append(f'<rect x="{x}" y="3" width="{w}" height="32" rx="3" fill="{col}" stroke="{AXIS}" stroke-width="0.5"/>')
        b.append(t(x+w/2,16,title,10,BRAND,'middle',600));b.append(t(x+w/2,28,sub,9.1,QUIET,'middle'))
    b.append(t(228,24,'+',15,BRAND,'middle',600));b.append(t(515,24,'→',16,BRAND,'middle',600))
    return svg(688,38,''.join(b),'Semana 1: coste total y frecuencia por severidad se combinan por ramo')

def flujo_ia():
    b=[]
    def box(x,y,w,h,title,sub,fill='#eef3f5',ink=BRAND):
        b.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="3" fill="{fill}" stroke="{AXIS}" stroke-width="0.6"/>')
        b.append(t(x+w/2,y+14,title,11.1,ink,'middle',600))
        if sub:b.append(t(x+w/2,y+28,sub,10,('#f0f5f6' if ink=='#ffffff' else QUIET),'middle'))
    b.append(t(344,10,'Pregunta actuarial, datos y criterios definidos antes de comparar',10,QUIET,'middle'))
    for x,title,sub in [(0,'IA · Modelado','código y estimaciones'),(236,'IA · Alternativas','hipótesis y comparadores'),(472,'IA · Contraste','réplicas y pruebas adversas')]:box(x,17,216,35,title,sub)
    for x in [108,344,580]:b.append(line(x,52,x,59,AXIS))
    box(0,60,688,35,'Foro común: propuestas, evidencia y resultados adversos','cada cambio conserva su motivo, autor y versión','#e8f0f9')
    b.append(line(344,95,344,103,AXIS))
    box(0,104,330,35,'Controles y paneles','conciliación, métricas, escenarios y huellas')
    b.append(t(344,128,'→',16,BRAND,'middle',600))
    box(358,104,330,35,'Mi revisión actuarial','supuestos, correcciones y decisión final',BRAND,'#ffffff')
    b.append(t(344,153,'Salida: receta reproducible, predicciones y expediente de decisión',10,QUIET,'middle'))
    return svg(688,158,''.join(b),'Circuito de trabajo con IA: preguntas actuariales, propuestas, contraste, controles y decisión del participante')
