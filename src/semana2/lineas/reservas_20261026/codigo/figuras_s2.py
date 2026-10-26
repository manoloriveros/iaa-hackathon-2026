"""Figuras y datos de contexto del informe de reservas de la semana 2 (F3c).

Uso: python3 figuras_s2.py <raiz> [datos|figuras]   (sin etapa, las dos)
  datos    calcula resultados/curvas.json (respuesta del nivel a b y a k, con la misma cadena que reservas_s2.py)
           y resultados/contexto.json (parámetros de la cadena, cuotas de nuevo negocio y totales de 2025)
  figuras  dibuja figuras/*.png solo a partir de los JSON de resultados/

Las curvas usan las funciones de reservas_s2.py (cadena, Base, nivel_ramos) sin cambiarlas. No son preinscritas: ilustran
los umbrales y escenarios que sí lo son.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

RAIZ = Path(sys.argv[1]).resolve()
RES = RAIZ / "resultados"
FIG = RAIZ / "figuras"
LINEAS = ["motor", "buildings", "contents"]
CELDAS = ["motor_0", "motor_1", "buildings_0", "buildings_1", "contents_0", "contents_1"]
NOMBRE = {"motor": "Autos", "buildings": "Edificios", "contents": "Contenidos"}


def leer(n):
    return json.loads((RES / n).read_text(encoding="utf-8"))


def guardar(n, obj):
    obj = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **obj}
    (RES / n).write_text(json.dumps(obj, ensure_ascii=False, indent=1), encoding="utf-8")


def r(x, n=6):
    return None if x is None else round(float(x), n)


# ---------------------------------------------------------------- datos

def etapa_datos():
    import pandas as pd
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    argv = sys.argv
    sys.argv = [argv[0], str(RAIZ)]
    import reservas_s2 as R  # lee sys.argv[1] al importarse
    sys.argv = argv
    P = R.cadena()
    B = R.Base(P)
    LARGOS = R.LARGOS

    def nivel(l, rr):
        rho = {s: (rr if s.startswith(l) else 1.0) for s in CELDAS}
        return R.nivel_ramos(rho, P)

    grid_b = [round(x, 2) for x in np.arange(0.40, 1.6001, 0.01)]
    grid_k = [round(x, 2) for x in np.arange(0.25, 2.5001, 0.025)]
    cur = {}
    for l in LINEAS:
        for nom, ps in (("ramo", None),) + (((("largo", [LARGOS[l]]),) if l in LARGOS else ())):
            for tipo, grid in (("b", grid_b), ("k", grid_k)):
                mz, f3, c0, c1 = [], [], [], []
                for x in grid:
                    rr = B.rho(l, b=x, peligros=ps)[0] if tipo == "b" else B.rho(l, k=x, peligros=ps)[0]
                    nv = nivel(l, rr)
                    mz.append(r(rr - 1, 6)); f3.append(r(nv[l], 6)); c0.append(r(nv[f"{l}_0"], 6)); c1.append(r(nv[f"{l}_1"], 6))
                cur[f"{l}|{tipo}|{nom}"] = {"x": grid, "mezcla": mz, "F3c": f3, f"F3c_{l}_0": c0, f"F3c_{l}_1": c1}
    guardar("curvas.json", {"nota": "no preinscrito: ilustra la respuesta del nivel 2025 al multiplicador b de la reserva de caso y k del IBNR, "
                                    "con las mismas funciones de reservas_s2.py; el error de nivel base afecta solo al ramo indicado",
                            "curvas": cur})

    # contexto: parámetros de la cadena y cuotas de nuevo negocio
    DAT = RAIZ / "datos"
    nb = {}
    for l in LINEAS:
        t = pd.read_parquet(DAT / f"test_{l}.parquet", columns=["new_business"])
        p = pd.read_parquet(DAT / f"policies_{l}.parquet", columns=["new_business"])
        nb[l] = {"filas_2025": int(len(t)), "cuota_nb_2025": r(t.new_business.astype(bool).mean(), 4),
                 "filas_2023_2024": int(len(p)), "cuota_nb_2023_2024": r(p.new_business.astype(bool).mean(), 4)}
    tt = sum(v["filas_2025"] for v in nb.values()); ttr = sum(v["filas_2023_2024"] for v in nb.values())
    nb["total"] = {"filas_2025": tt, "cuota_nb_2025": r(sum(v["filas_2025"] * v["cuota_nb_2025"] for v in nb.values()) / tt, 4),
                   "filas_2023_2024": ttr, "cuota_nb_2023_2024": r(sum(v["filas_2023_2024"] * v["cuota_nb_2023_2024"] for k, v in nb.items() if k != "total") / ttr, 4)}
    totF = P["totales"]["F3c"]
    cuota_nb_F3c = {l: r(totF[f"{l}_1"] / (totF[f"{l}_0"] + totF[f"{l}_1"]), 4) for l in LINEAS}
    sg = json.loads((RAIZ / "cadena" / "sonda_global_resultado.json").read_text(encoding="utf-8"))
    guardar("contexto.json", {
        "Z_g": P["Z_g"], "c_g_publicado": r(P["c_g_publicado"], 6), "g_global": r(min(max(P["c_g_publicado"] ** P["Z_g"], 0.75), 1.33), 6),
        "sonda_global_claves": sorted(sg.keys()),
        "Z_s": P["Z_s"], "c_s": {s: r(v, 6) for s, v in P["c_s"].items()}, "a_s": {s: r(v, 6) for s, v in P["a_s"].items()},
        "b_s": {s: r(v, 6) for s, v in P["b_s"].items()}, "w_designada": {l: r(v, 4) for l, v in P["w_designada"].items()},
        "totales_2025": {m: {s: r(v, 2) for s, v in P["totales"][m].items()} for m in ("F3c", "F3d", "mezcla")},
        "cuota_nuevo_negocio_en_total_F3c_2025": cuota_nb_F3c, "nuevo_negocio_filas": nb})
    print("curvas y contexto escritos")


# ---------------------------------------------------------------- figuras

SUP, INK, INK2, MUTED, GRID, BASE = "#fcfcfb", "#0b0b0b", "#52514e", "#898781", "#e1e0d9", "#c3c2b7"
C1, C2, C3 = "#2a78d6", "#eb6834", "#1baf7a"
BANDA = "#f0efec"
ESTADO = {"acotado": ("#0ca30c", "✓", "Acotado"), "incertidumbre_material": ("#fab219", "!", "Incertidumbre material"),
          "indicio_de_desvio_material": ("#d03b3b", "✗", "Indicio de desvío material"), "sin_estimacion": ("#898781", "–", "Sin estimación")}


def coma(x, d=2, signo=False):
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    if x < 0:
        return "−" + s
    return ("+" + s) if (signo and x > 0) else s


def estilo():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({
        "font.family": "DejaVu Sans", "font.size": 9.5, "figure.facecolor": SUP, "axes.facecolor": SUP, "savefig.facecolor": SUP,
        "axes.edgecolor": BASE, "axes.linewidth": 0.8, "axes.labelcolor": INK2, "axes.titlecolor": INK, "axes.titlesize": 10.5,
        "axes.titlelocation": "left", "axes.titlepad": 8, "xtick.color": MUTED, "ytick.color": MUTED, "xtick.labelcolor": INK2,
        "ytick.labelcolor": INK2, "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.7, "grid.linestyle": "-",
        "axes.spines.top": False, "axes.spines.right": False, "legend.frameon": False, "legend.fontsize": 9, "text.color": INK,
        "savefig.dpi": 170, "lines.solid_capstyle": "round", "lines.solid_joinstyle": "round", "axes.axisbelow": True})
    return plt


def fmt_eje(ax, eje="y", d=1, pct=False, signo=False):
    from matplotlib.ticker import FuncFormatter
    f = FuncFormatter(lambda v, _: coma(v * (100 if pct else 1), d, signo) + (" %" if pct else ""))
    (ax.yaxis if eje == "y" else ax.xaxis).set_major_formatter(f)


def pie(fig, texto):
    fig.text(0.01, 0.005, texto, fontsize=7.5, color=MUTED, ha="left", va="bottom")


def fig0_resumen(plt):
    """Semáforo: clase de la reserva de caso (b) y del IBNR (k) por ramo, con el efecto central en F3c (no preinscrito)."""
    from matplotlib.patches import FancyBboxPatch
    d, b, c, g = leer("parte_d.json")["escenarios"], leer("parte_b.json")["beta"], leer("parte_c.json")["k"], leer("parte_g.json")
    W = 12.4
    fig, ax = plt.subplots(figsize=(W, 4.4))
    ax.set_axis_off(); ax.set_xlim(0, W); ax.set_ylim(0, 4.4)
    X = (0.15, 1.65, 5.75, 9.85)
    cols = [(X[0], "Ramo"), (X[1], "Reserva de caso de los abiertos (b)"), (X[2], "Siniestros aún no reportados (k)"), (X[3], "β y k_e a la vez\n(no preinscrito)")]
    for x, t in cols:
        ax.text(x, 4.02, t, fontsize=9.5, color=INK2, va="center", fontweight="bold")
    ax.plot([0.1, W - 0.1], [3.66, 3.66], color=BASE, lw=0.8)
    for i, l in enumerate(LINEAS):
        y = 3.08 - i * 1.18
        ax.text(X[0], y, NOMBRE[l], fontsize=11, va="center", color=INK)
        for x0, est, txt in (
                (X[1], d[f"{l}|b|ramo"]["clase_F3c"],
                 [f"β {coma(b[f'{l}|_ramo']['beta'], 3)}   IC90 [{coma(b[f'{l}|_ramo']['ic90'][0], 3)}; {coma(b[f'{l}|_ramo']['ic90'][1], 3)}]",
                  "F3c se mueve 1 % " + rango_txt(d[f"{l}|b|ramo"]["umbral_F3c"], "b")]),
                (X[2], d[f"{l}|k|ramo"]["clase_F3c"],
                 [f"k_e {coma(c[f'{l}|_ramo']['k_e'], 3)}   IC90 [{coma(c[f'{l}|_ramo']['ic90_k_e'][0], 3)}; {coma(c[f'{l}|_ramo']['ic90_k_e'][1], 3)}]",
                  "F3c se mueve 1 % " + rango_txt(d[f"{l}|k|ramo"]["umbral_F3c"], "k")])):
            col, sim, nom = ESTADO[est]
            ax.add_patch(FancyBboxPatch((x0, y - 0.17), 0.34, 0.34, boxstyle="round,pad=0,rounding_size=0.06", fc=col, ec="none"))
            ax.text(x0 + 0.17, y, sim, ha="center", va="center", fontsize=11, color="#0b0b0b" if col == "#fab219" else "#ffffff", fontweight="bold")
            ax.text(x0 + 0.48, y + 0.21, nom, fontsize=10, va="center", color=INK)
            ax.text(x0 + 0.48, y - 0.06, txt[0], fontsize=8.5, va="center", color=INK2)
            ax.text(x0 + 0.48, y - 0.30, txt[1], fontsize=8.5, va="center", color=INK2)
        v = g["G2_escenario_central"]["por_ramo_aislado"][l]["nivel_F3c"]
        ax.text(X[3], y + 0.12, coma(v * 100, 2, True) + " %", fontsize=13, va="center", color=INK)
        ax.text(X[3], y - 0.24, "en el nivel 2025 del ramo", fontsize=8.5, va="center", color=INK2)
        if i < 2:
            ax.plot([0.1, W - 0.1], [y - 0.6, y - 0.6], color=GRID, lw=0.7)
    pie(fig, "Clase con la regla de la semana 1 y la materialidad del 1 % del nivel 2025 de F3c del ramo. "
             "Fuente: resultados/parte_b, parte_c, parte_d y parte_g.json.")
    fig.savefig(FIG / "fig0_resumen.png", bbox_inches="tight"); plt.close(fig)


def rango_txt(u, v):
    if u[0] is None and u[1] is None:
        return f"con ningún {v} de la rejilla"
    if u[0] is None:
        return f"solo si {v} > {coma(u[1], 3)}"
    if u[1] is None:
        return f"solo si {v} < {coma(u[0], 3)}"
    return f"si {v} sale de [{coma(u[0], 3)}; {coma(u[1], 3)}]"


def rango(u):
    lo = "0" if u[0] is None else coma(u[0], 3)
    hi = "∞" if u[1] is None else coma(u[1], 3)
    return f"[{lo}; {hi}]"


def fig1_reservas(plt):
    a = leer("parte_a.json")
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), gridspec_kw={"width_ratios": [1.05, 1]})
    filas = [(l, y) for l in LINEAS for y in (2023, 2024)]
    ys = np.arange(len(filas))[::-1]
    for yy, (l, an) in zip(ys, filas):
        q = a["por_ramo_anio"][f"{l}_{an}"]
        pag, res, ib = (q["T0"] - q["reserva"]) / 1e6, q["reserva"] / 1e6, q["ibnr_implicito"] / 1e6
        ax.barh(yy, pag, height=0.56, color=C1, edgecolor=SUP, linewidth=1.5)
        ax.barh(yy, res, left=pag, height=0.56, color=C2, edgecolor=SUP, linewidth=1.5)
        ax.barh(yy, ib, left=pag + res, height=0.56, color=C3, alpha=0.45, edgecolor=SUP, linewidth=1.5)
        ax.text(pag + res + ib + 0.12, yy, f"reserva {coma(q['reserva_sobre_T0'] * 100, 1)} % de T0", va="center", fontsize=8.6, color=INK2)
    ax.set_yticks(ys, [f"{NOMBRE[l]} {an}" for l, an in filas])
    ax.set_xlabel("millones de CU")
    ax.set_xlim(0, 10.6); ax.grid(axis="y", visible=False)
    fmt_eje(ax, "x", 0)
    from matplotlib.patches import Patch
    ax.legend(handles=[Patch(color=C1, label="Pagado neto de recobros"), Patch(color=C2, label="Reserva de caso"),
                       Patch(color=C3, alpha=0.45, label="IBNR implícito (fuera de T0)")],
              loc="upper center", fontsize=8.2, bbox_to_anchor=(0.45, -0.13), ncol=3)
    ax.set_title("Qué parte del coste de 2023-2024 es todavía estimación")
    # panel 2: reserva por peligro
    nombres = {"bodily_injury": "lesiones corporales", "third_party_prop": "daños materiales a terceros", "own_damage": "daños propios",
               "theft": "robo", "glass_hail": "lunas y granizo", "flood": "inundación", "subsidence": "hundimiento", "fire": "incendio",
               "escape_of_water": "escape de agua", "storm": "tormenta", "accidental_damage": "daño accidental"}
    pp = sorted(a["por_peligro"].items(), key=lambda kv: (LINEAS.index(kv[0].split("|")[0]), -kv[1]["reserva"]))
    pp = [kv for kv in pp if kv[1]["reserva"] >= 5000]
    y2 = np.arange(len(pp))[::-1]
    tot = a["totales"]["reserva"]
    colr = {"motor": C1, "buildings": C2, "contents": C3}
    for yy, (k, v) in zip(y2, pp):
        l, p = k.split("|")
        ax2.barh(yy, v["reserva"] / 1e6, height=0.6, color=colr[l])
        ax2.text(v["reserva"] / 1e6 + 0.03, yy, f"{coma(v['reserva'] / tot * 100, 1)} %  ({v['abiertos']} abiertos)", va="center", fontsize=8.2, color=INK2)
    ax2.set_yticks(y2, [f"{NOMBRE[k.split('|')[0]]}: {nombres[k.split('|')[1]]}" for k, _ in pp], fontsize=8.6)
    ax2.set_xlim(0, 3.3); ax2.grid(axis="y", visible=False); fmt_eje(ax2, "x", 1)
    ax2.set_xlabel("reserva de caso, millones de CU (y % de toda la reserva)")
    ax2.set_title("Dónde está la reserva: casi la mitad es lesiones corporales")
    fig.tight_layout(rect=(0, 0.03, 1, 1))
    pie(fig, "Fuente: resultados/parte_a.json (siniestros del emergente asignados a su periodo, valorados al 31-12-2024). Peligros con menos de 5.000 CU de reserva omitidos en el panel derecho.")
    fig.savefig(FIG / "fig1_reservas.png", bbox_inches="tight"); plt.close(fig)


def fig2_cadena(plt):
    from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
    a, d, ctx = leer("parte_a.json"), leer("parte_d.json"), leer("contexto.json")
    fig = plt.figure(figsize=(11, 6.9))
    ax = fig.add_axes([0.0, 0.5, 1.0, 0.5]); ax.set_axis_off(); ax.set_xlim(0, 11); ax.set_ylim(0, 3.4)
    T0 = a["totales"]["T0"]; R_ = a["totales"]["reserva"]
    mot = d["escenarios"]["motor|b|ramo"]["en_0.75"]
    Tm = a["por_ramo_anio"]["motor_2023"]["T0"] + a["por_ramo_anio"]["motor_2024"]["T0"]
    Rm = a["por_ramo_anio"]["motor_2023"]["reserva"] + a["por_ramo_anio"]["motor_2024"]["reserva"]
    cajas = [
        (0.15, "1. Reserva de caso", f"{coma(R_ / 1e6, 2)} M CU en\n1.055 abiertos ({coma(R_ / T0 * 100, 1)} % de T0)", f"Autos: {coma(Rm / 1e6, 2)} M CU\n× b = 0,75"),
        (2.35, "2. Etiquetas T0\nde 2023-2024", f"{coma(T0 / 1e6, 2)} M CU\nincurrido − recobros", f"T0 de autos\n{coma(-0.25 * Rm / Tm * 100, 2, True)} %"),
        (4.55, "3. Nivel base\nde la mezcla", "designada por balance\nlínea ML por escalar Tweedie", f"nivel base de autos\n{coma(mot['rho_mezcla'] * 100, 2, True)} %"),
        (6.75, "4. Sondas del\npúblico", f"global Z_g {coma(ctx['Z_g'], 3)}\npor celda Z_s {coma(min(ctx['Z_s'].values()), 2)}–{coma(max(ctx['Z_s'].values()), 3)}", "el público fija el\nnivel absoluto"),
        (8.95, "5. Nivel 2025\nde F3c", "F2 y factores\nconservan el nivel\nde cada celda", f"nivel de F3c en autos\n{coma(mot['F3c_ramo'] * 100, 2, True)} %"),
    ]
    for i, (x, tit, cuerpo, ej) in enumerate(cajas):
        ax.add_patch(FancyBboxPatch((x, 1.55), 1.9, 1.65, boxstyle="round,pad=0,rounding_size=0.12", fc="#ffffff", ec=BASE, lw=0.9))
        ax.text(x + 0.95, 2.86, tit, ha="center", va="center", fontsize=9.6, fontweight="bold", color=INK)
        ax.text(x + 0.95, 2.1, cuerpo, ha="center", va="center", fontsize=8.3, color=INK2, linespacing=1.35)
        col = C2 if i < 3 else (C1 if i == 4 else MUTED)
        ax.add_patch(FancyBboxPatch((x + 0.1, 0.3), 1.7, 0.95, boxstyle="round,pad=0,rounding_size=0.1", fc=col if i != 3 else BANDA,
                                    ec="none", alpha=0.14 if i != 3 else 1))
        ax.text(x + 0.95, 0.78, ej, ha="center", va="center", fontsize=8.8, color=INK, linespacing=1.3)
        if i < 4:
            ax.add_patch(FancyArrowPatch((x + 1.92, 2.38), (x + 2.18, 2.38), arrowstyle="-|>", mutation_scale=12, color=MUTED, lw=1.2,
                                         shrinkA=0, shrinkB=0, zorder=5))
            ax.add_patch(FancyArrowPatch((x + 1.82, 0.78), (x + 2.28, 0.78), arrowstyle="-|>", mutation_scale=10, color=MUTED, lw=1.0,
                                         shrinkA=0, shrinkB=0, zorder=5))
    ax.text(0.15, 1.36, "Ejemplo: si los abiertos de autos acabaran costando un 25 % menos de lo reservado", fontsize=8.6, color=INK2, va="center")
    # panel inferior: pendientes mezcla -> F3c en b = 0,75 por ramo
    ax2 = fig.add_axes([0.1, 0.13, 0.36, 0.29])
    for l, col in zip(LINEAS, (C1, C2, C3)):
        e = d["escenarios"][f"{l}|b|ramo"]["en_0.75"]
        ax2.plot([0, 1], [e["rho_mezcla"] * 100, e["F3c_ramo"] * 100], color=col, lw=2, marker="o", ms=7, mec=SUP, mew=1.5)
        ax2.text(-0.04, e["rho_mezcla"] * 100, f"{NOMBRE[l]} {coma(e['rho_mezcla'] * 100, 2)} %", ha="right", va="center", fontsize=8.4, color=INK2)
        ax2.text(1.06, e["F3c_ramo"] * 100 + (0.35 if l == "contents" else (-0.4 if l == "buildings" else -0.02)),
                 f"{NOMBRE[l]} {coma(e['F3c_ramo'] * 100, 2)} %", ha="left", va="center", fontsize=8.4, color=INK2)
    ax2.axhspan(-1, 1, color=BANDA, zorder=0)
    ax2.set_xlim(-0.85, 1.75); ax2.set_xticks([0, 1], ["nivel base\nde la mezcla", "nivel 2025\nde F3c"]); ax2.grid(axis="x", visible=False)
    ax2.set_ylim(-6.2, 0.6); fmt_eje(ax2, "y", 0, signo=True)
    ax2.set_ylabel("cambio de nivel, %")
    ax2.set_title("Reserva de caso × 0,75 en un solo ramo", fontsize=9.8)
    ax2.text(-0.8, 0.12, "banda de ±1 %", fontsize=7.8, color=MUTED, ha="left", va="bottom")
    # panel inferior derecho: elasticidades por celda
    ax3 = fig.add_axes([0.6, 0.13, 0.37, 0.29])
    el = d["elasticidad_analitica"]
    celdas = [("motor_0", "Autos renov."), ("motor_1", "Autos nuevo"), ("buildings_0", "Edificios renov."), ("buildings_1", "Edificios nuevo"),
              ("contents_0", "Contenidos renov."), ("contents_1", "Contenidos nuevo")]
    vals = [el[c.split("_")[0]][c] for c, _ in celdas]
    yy = np.arange(len(celdas))[::-1]
    cols = [C1, C1, C2, C2, C3, C3]
    ax3.barh(yy, vals, height=0.55, color=cols)
    for y_, v in zip(yy, vals):
        ax3.text(v + 0.01, y_, coma(v, 3), va="center", fontsize=8.4, color=INK2)
    ax3.axvline(el["uniforme"], color=INK2, lw=1)
    ax3.set_ylim(-0.6, len(celdas) + 0.25)
    ax3.text(0.615, len(celdas) - 0.15, f"línea: error igual en los tres ramos, 1 − Z_g = {coma(el['uniforme'], 3)}", fontsize=7.8,
             color=INK2, va="center", ha="right")
    ax3.set_yticks(yy, [n for _, n in celdas], fontsize=8.6); ax3.grid(axis="y", visible=False)
    ax3.set_xlim(0, 0.62); fmt_eje(ax3, "x", 1)
    ax3.set_title("Qué fracción de un error de nivel base llega a F3c", fontsize=9.8)
    ax3.set_xlabel("elasticidad con el error en un solo ramo (1 = sin sondas)")
    pie(fig, "Fuente: resultados/parte_a.json, parte_d.json (escenarios en b = 0,75 y elasticidad analítica) y contexto.json. «Renov.» es renovación; «nuevo», nuevo negocio.")
    fig.savefig(FIG / "fig2_cadena.png", bbox_inches="tight"); plt.close(fig)


def fig3_respuesta(plt):
    cu, d, b = leer("curvas.json")["curvas"], leer("parte_d.json")["escenarios"], leer("parte_b.json")["beta"]
    fig, axs = plt.subplots(1, 3, figsize=(11.5, 4.1), sharey=True)
    for ax, l in zip(axs, LINEAS):
        c = cu[f"{l}|b|ramo"]
        x = np.array(c["x"])
        ax.axhspan(-1, 1, color=BANDA, zorder=0)
        ic = b[f"{l}|_ramo"]["ic90"]
        ax.axvspan(ic[0], ic[1], color=C1, alpha=0.10, zorder=0.5, lw=0)
        ax.plot(x, np.array(c["mezcla"]) * 100, color=MUTED, lw=1.6, label="nivel base de la mezcla (sin sondas)")
        ax.plot(x, np.array(c["F3c"]) * 100, color=C1, lw=2.2, label="nivel 2025 de F3c")
        u = d[f"{l}|b|ramo"]["umbral_F3c"]
        for k_, uu in enumerate(u):
            if uu is not None and 0.4 <= uu <= 1.6:
                yv = -1 if k_ == 0 else 1
                ax.plot([uu], [yv], marker="o", ms=7, color=C1, mec=SUP, mew=1.5, zorder=5)
                ax.annotate(coma(uu, 3), (uu, yv), xytext=(0, -14 if k_ == 0 else 8), textcoords="offset points", ha="center", fontsize=8.2, color=INK2)
        bp = b[f"{l}|_ramo"]["beta"]
        ax.plot([bp], [d[f"{l}|b|ramo"]["F3c_con_beta_puntual"] * 100], marker="D", ms=6.5, color=INK, mec=SUP, mew=1.2, zorder=6)
        ax.annotate(f"β {coma(bp, 3)}", (bp, d[f"{l}|b|ramo"]["F3c_con_beta_puntual"] * 100), xytext=(6, 10), textcoords="offset points", fontsize=8.2, color=INK)
        ax.text(ic[0] + 0.012, 3.8, f"IC90 de β\n[{coma(ic[0], 3)}; {coma(ic[1], 3)}]", fontsize=7.8, color=INK2, va="top")
        ax.set_title(NOMBRE[l] + " · " + ESTADO[d[f"{l}|b|ramo"]["clase_F3c"]][2].lower())
        ax.set_xlim(0.4, 1.6); ax.set_ylim(-4, 4)
        ax.set_xlabel("b: lo que de verdad falta por pagar / reserva")
        ax.set_xticks([0.6, 0.8, 1.0, 1.2, 1.4])
        fmt_eje(ax, "x", 1)
    fmt_eje(axs[0], "y", 0, signo=True)
    axs[0].set_ylabel("cambio de nivel 2025 del ramo, %")
    axs[0].text(0.42, 1.12, "banda de ±1 %", fontsize=7.8, color=MUTED)
    h, lab = axs[0].get_legend_handles_labels()
    fig.legend(h, lab, loc="upper center", ncol=2, bbox_to_anchor=(0.5, 1.04), fontsize=8.8)
    fig.tight_layout(rect=(0, 0.03, 1, 0.96))
    pie(fig, "Gris: nivel base de la mezcla (paso 3 de la figura 2). Azul: nivel 2025 de F3c (paso 5). Puntos: cruces del 1 %. Rombo: β puntual. "
             "Fuente: resultados/curvas.json, parte_b.json y parte_d.json.")
    fig.savefig(FIG / "fig3_respuesta_b.png", bbox_inches="tight"); plt.close(fig)


def bosque(ax, filas, titulo, etiqueta_x, xlim):
    """filas: (nombre, punto, ic, umbral, clase, extra) con extra = lista de (punto, ic, estilo, etiqueta)."""
    n = len(filas)
    for i, (nom, pto, ic, u, cl, extra) in enumerate(filas):
        y = n - 1 - i
        if u is not None:
            lo = xlim[0] if u[0] is None else u[0]
            hi = xlim[1] if u[1] is None else u[1]
            ax.add_patch(__import__("matplotlib.patches", fromlist=["Rectangle"]).Rectangle((lo, y - 0.36), hi - lo, 0.72, color=BANDA, zorder=0, lw=0))
        if pto is not None:
            ax.plot(ic, [y + 0.12] * 2, color=C1, lw=2.2, zorder=3)
            ax.plot([pto], [y + 0.12], marker="o", ms=7.5, color=C1, mec=SUP, mew=1.5, zorder=4)
        else:
            ax.text(xlim[0] + 0.03 * (xlim[1] - xlim[0]), y + 0.12, "sin celdas con 20 cerrados", fontsize=8, color=MUTED, va="center")
        for (p2, ic2, est, _) in extra:
            if p2 is None:
                continue
            ax.plot(ic2, [y - 0.16] * 2, color=C2, lw=1.6, zorder=3)
            ax.plot([p2], [y - 0.16], marker=est, ms=7, color=C2 if est == "o" else SUP, mec=C2 if est != "o" else SUP, mew=1.5, zorder=4)
        col, sim, nomc = ESTADO[cl] if cl else (MUTED, "", "")
        if cl:
            ax.text(xlim[1] + 0.045 * (xlim[1] - xlim[0]), y, nomc, fontsize=8.4, va="center", color=INK2)
            ax.plot([xlim[1] + 0.022 * (xlim[1] - xlim[0])], [y], marker="s", ms=10, color=col, clip_on=False)
            ax.text(xlim[1] + 0.022 * (xlim[1] - xlim[0]), y, sim, fontsize=7, va="center", ha="center", fontweight="bold",
                    color="#0b0b0b" if col == "#fab219" else "#ffffff", clip_on=False)
    ax.set_yticks(range(n), [f[0] for f in filas][::-1])
    ax.set_ylim(-0.6, n - 0.4); ax.set_xlim(*xlim)
    ax.axvline(1, color=INK2, lw=0.9, zorder=1)
    ax.grid(axis="y", visible=False)
    ax.set_title(titulo); ax.set_xlabel(etiqueta_x)
    ax.set_xticks(np.round(np.arange(np.ceil(xlim[0] * 5) / 5, xlim[1] + 1e-9, 0.2 if xlim[1] - xlim[0] < 2.5 else 0.4), 2))
    fmt_eje(ax, "x", 1)


def fig4_beta(plt):
    b, d = leer("parte_b.json")["beta"], leer("parte_d.json")["escenarios"]
    filas = []
    for nom, kb, kd in (("Autos", "motor|_ramo", "motor|b|ramo"), ("Autos: lesiones corporales", "motor|bodily_injury", "motor|b|largo"),
                        ("Autos: resto de peligros", "motor|_resto", "motor|b|resto"), ("Edificios", "buildings|_ramo", "buildings|b|ramo"),
                        ("Edificios: hundimiento", "buildings|subsidence", "buildings|b|largo"), ("Edificios: resto de peligros", "buildings|_resto", "buildings|b|resto"),
                        ("Contenidos", "contents|_ramo", "contents|b|ramo")):
        q = b[kb]
        des = q.get("desarrollado", {})
        filas.append((nom, q["beta"], q["ic90"], d[kd]["umbral_F3c"], d[kd]["clase_F3c"],
                      [(des.get("beta_recalculado"), des.get("ic90"), "o", "desarrollado")]))
    fig, ax = plt.subplots(figsize=(10.5, 4.9))
    bosque(ax, filas, "β: reserva que haría falta / reserva contabilizada, con IC90", "β (1 = la reserva de caso acierta en media)", (0.3, 2.2))
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Line2D([], [], color=C1, marker="o", lw=2, ms=7, mec=SUP, label="emergente 2023-2024"),
                       Line2D([], [], color=C2, marker="o", lw=1.6, ms=7, mec=SUP, label="desarrollado (semana 1, recalculado)"),
                       Patch(color=BANDA, label="b que mueven F3c menos del 1 %")], loc="upper center", fontsize=8.4,
              bbox_to_anchor=(0.5, -0.13), ncol=3)
    fig.subplots_adjust(right=0.78, left=0.2, bottom=0.2)
    pie(fig, "Fuente: resultados/parte_b.json (400 réplicas Poisson, semilla 20261026, celdas con 20 o más cerrados) y parte_d.json (umbrales de F3c).")
    fig.savefig(FIG / "fig4_beta.png", bbox_inches="tight"); plt.close(fig)


def fig5_ibnr(plt):
    c, d = leer("parte_c.json")["k"], leer("parte_d.json")["escenarios"]
    filas = []
    for nom, kc, kd in (("Autos", "motor|_ramo", "motor|k|ramo"), ("Autos: lesiones corporales", "motor|bodily_injury", "motor|k|largo"),
                        ("Autos: resto de peligros", "motor|_resto", None), ("Edificios", "buildings|_ramo", "buildings|k|ramo"),
                        ("Edificios: hundimiento", "buildings|subsidence", "buildings|k|largo"), ("Edificios: resto de peligros", "buildings|_resto", None),
                        ("Contenidos", "contents|_ramo", "contents|k|ramo")):
        q = c[kc]
        filas.append((nom, q["k_e"], q["ic90_k_e"], d[kd]["umbral_F3c"] if kd else None, d[kd]["clase_F3c"] if kd else None,
                      [(q["k_conteos"], q["ic90_k_conteos"], "o", "conteos")]))
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.9), gridspec_kw={"width_ratios": [1.45, 1]})
    bosque(ax, filas, "k_e: coste tardío observado / previsto (cohorte 2023), IC90", "k_e (1 = la curva del desarrollado acierta)", (0.0, 2.9))
    from matplotlib.lines import Line2D
    from matplotlib.patches import Patch
    ax.legend(handles=[Line2D([], [], color=C1, marker="o", lw=2, ms=7, mec=SUP, label="coste"),
                       Line2D([], [], color=C2, marker="o", lw=1.6, ms=7, mec=SUP, label="número de siniestros"),
                       Patch(color=BANDA, label="k que mueven F3c menos del 1 %")], loc="upper center", fontsize=8.4,
              bbox_to_anchor=(0.45, -0.13), ncol=3)
    # panel derecho: coste tardío observado frente a previsto
    grupos = [("Autos", "motor|_ramo"), ("lesiones", "motor|bodily_injury"), ("resto autos", "motor|_resto"), ("Edificios", "buildings|_ramo"),
              ("hundimiento", "buildings|subsidence"), ("Contenidos", "contents|_ramo")]
    x = np.arange(len(grupos))
    obs = [c[k]["coste_tardio_observado"] / 1e6 for _, k in grupos]; pre = [c[k]["coste_tardio_previsto"] / 1e6 for _, k in grupos]
    ax2.bar(x - 0.17, pre, width=0.32, color=MUTED, label="previsto por la curva del desarrollado")
    ax2.bar(x + 0.17, obs, width=0.32, color=C1, label="observado (reportado en 2024)")
    ax2.set_xticks(x, [g for g, _ in grupos], fontsize=8.4, rotation=20, ha="right"); ax2.grid(axis="x", visible=False)
    fmt_eje(ax2, "y", 1); ax2.set_ylabel("millones de CU")
    ax2.set_title("Coste de 2023 que se reportó en 2024")
    ax2.legend(fontsize=8.2, loc="upper right")
    fig.subplots_adjust(left=0.15, right=0.97, wspace=0.62, bottom=0.24)
    pie(fig, "Fuente: resultados/parte_c.json (400 réplicas por siniestro) y parte_d.json. Los dos «resto de peligros» no tienen escenario k propio en el plan.")
    fig.savefig(FIG / "fig5_ibnr.png", bbox_inches="tight"); plt.close(fig)


def fig6_estructura(plt):
    e = leer("parte_e.json")
    fig, (ax, ax2) = plt.subplots(1, 2, figsize=(11.5, 4.4), gridspec_kw={"width_ratios": [1, 1.25]})
    for i, (l, col) in enumerate(zip(LINEAS, (C1, C2, C3))):
        q = e["E1_emergente"][l]
        pts = sorted((float(k[2:]), v["delta_a"]) for k, v in q.items() if k.startswith("b_"))
        ax.plot([p[0] for p in pts], [p[1] for p in pts], color=col, lw=2, marker="o", ms=7, mec=SUP, mew=1.5, label=NOMBRE[l])
    ax.axhline(0, color=INK2, lw=0.9); ax.axvline(1, color=GRID, lw=0.8)
    ax.set_xlabel("b aplicado a la reserva de caso"); ax.set_ylabel("Δa: cambio del exponente de inclinación")
    ax.set_xticks([0.6, 0.8, 1.0, 1.2, 1.4, 1.6, 1.8, 2.0])
    fmt_eje(ax, "x", 1); fmt_eje(ax, "y", 3, signo=True)
    ax.set_title("E1. ¿Inclinaría la reserva las relatividades?")
    ax.legend(fontsize=8.4, loc="upper left")
    # E3: cota del cambio de factor por variable, sin y con credibilidad
    filas = []
    nomv = {"ncb_banda": "bonificación (NCB)", "previos": "siniestros previos", "gender": "género", "wfh": "teletrabajo", "marketing_segment": "segmento"}
    for k, v in e["E3_factores"].items():
        l, var = k.split("|")
        for grupo, q in v.items():
            et = NOMBRE[l] + (" renov." if grupo.endswith("_0") else (" nuevo" if grupo.endswith("_1") else "")) + ": " + nomv[var]
            filas.append((et, q["max_abs_cambio_log_factor"], q["max_abs_cambio_log_factor_con_credibilidad_no_preinscrito"], l))
    filas.sort(key=lambda f: (LINEAS.index(f[3]), f[0]))
    y = np.arange(len(filas))[::-1]
    for yy, (et, sin, con, l) in zip(y, filas):
        ax2.plot([con * 100, sin * 100], [yy, yy], color=GRID, lw=2, zorder=1)
        ax2.plot([sin * 100], [yy], marker="o", ms=7, color=SUP, mec=C2, mew=1.6, zorder=3)
        ax2.plot([con * 100], [yy], marker="o", ms=7, color=C1, mec=SUP, mew=1.5, zorder=4)
    ax2.set_yticks(y, [f[0] for f in filas], fontsize=8.2); ax2.grid(axis="y", visible=False)
    ax2.set_xscale("symlog", linthresh=1); ax2.set_xlim(0, 20)
    ax2.set_xticks([0, 0.5, 1, 2, 5, 10, 20], ["0", "0,5", "1", "2", "5", "10", "20"])
    ax2.set_xlabel("mayor cambio del factor en los extremos del IC90 de β, % (escala logarítmica desde 1)")
    from matplotlib.lines import Line2D
    ax2.legend(handles=[Line2D([], [], ls="", marker="o", ms=7, color=SUP, mec=C2, mew=1.6, label="sin credibilidad (preinscrito, cota)"),
                        Line2D([], [], ls="", marker="o", ms=7, color=C1, mec=SUP, label="con credibilidad n/(n+300) (no preinscrito)")],
               loc="upper center", fontsize=8.2, bbox_to_anchor=(0.4, -0.16), ncol=2)
    ax2.set_title("E3. Factores de F2 y F3c")
    fig.tight_layout(rect=(0, 0.04, 1, 1))
    pie(fig, "Fuente: resultados/parte_e.json. Δa con T0 como referencia; el exponente se reajusta con el nivel reoptimizado en 2023-2024.")
    fig.savefig(FIG / "fig6_estructura.png", bbox_inches="tight"); plt.close(fig)


def etapa_figuras():
    FIG.mkdir(exist_ok=True)
    plt = estilo()
    for f in (fig0_resumen, fig1_reservas, fig2_cadena, fig3_respuesta, fig4_beta, fig5_ibnr, fig6_estructura):
        f(plt)
        print("ok", f.__name__)


if __name__ == "__main__":
    et = sys.argv[2] if len(sys.argv) > 2 else "todas"
    if et in ("datos", "todas"):
        etapa_datos()
    if et in ("figuras", "todas"):
        etapa_figuras()
