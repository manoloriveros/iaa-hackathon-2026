"""Comprueba que los entregables finales coinciden con su archivo de datos y respetan las reglas de la entrega.

    python herramientas/verificar_entregables.py                        # contenido, estilo, enlaces y panel
    python herramientas/verificar_entregables.py --raiz C:/dev/Hakaton  # además, si las fuentes cambiaron desde la última extracción
    python herramientas/verificar_entregables.py --sin-navegador        # omite la prueba del panel en Chromium

Lee los PDF, las láminas y el panel ya construidos (no los regenera) y los compara con docs/entrega/datos/cifras_entregables.json:
páginas calificables, cifras en el texto de cada idioma, ausencia de identificadores de datos y de atribuciones de autoría, estilo
editorial, enlaces relativos, figuras y funcionamiento del panel sin red. Escribe docs/entrega/datos/verificacion_entregables.json y
termina con 0 si todo pasa o con 1 si algo falla. Un cambio en las fuentes se informa como aviso: obliga a regenerar, no a corregir.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parents[1]
ENT = REPO / "docs/entrega"
CIFRAS = ENT / "datos/cifras_entregables.json"
ID_DATOS = re.compile(r"\b(CL|TP|[ABCM])\d{7,9}\b")
# Nombrar las herramientas está permitido; atribuirles la autoría de una pieza, no.
AUTORIA = [re.compile(p) for p in (
    r"\b(?:by|from) (?:Claude|Codex)\b", r"\b(?:Claude|Codex)(?:'s)? (?:wrote|authored|built|developed|created|designed|produced|code\b|producer|line\b)",
    r"\b(?:de|por) (?:Claude|Codex)\b", r"\b(?:Claude|Codex) (?:escribió|desarrolló|construyó|creó|diseñó|produjo|redactó|aportó)\b")]
NEGRITA_INICIAL = re.compile(r"(?m)^\s*(?:[-*]|\d+\.)?\s*\*\*[^*\n]+\*\*\s*[:.]|^\s*(?:[-*]|\d+\.)?\s*\*\*[^*\n]+[:.]\*\*")
CLICHES = re.compile(r"(?i)en el acelerado mundo|en la era digital|es importante destacar|vale la pena considerar|¿la trampa\?|¿el truco\?|"
                     r"pero aquí está el detalle|in today's fast-paced|in the digital age|it is important to note|it's worth noting|"
                     r"here's the catch|the catch\?")
TEXTOS = ["README.md", "README.es.md", "docs/GUIA_TECNICA.md", "docs/entrega/README.md", "docs/entrega/AI_WORKFLOW_EN.md",
          "docs/entrega/USO_DE_IA_ES.md", "docs/entrega/informe/INFORME_EN.md", "docs/entrega/informe/INFORME_ES.md",
          "docs/entrega/video/GUION_VIDEO_EN.md", "docs/entrega/video/GUION_VIDEO_ES.md", "docs/expediente/README.md"]
PLANTILLAS = ["docs/entrega/web/laminas_plantilla.html", "docs/entrega/web/panel_plantilla.html", "docs/entrega/web/diagramas.js",
              "docs/entrega/web/figuras.js", "docs/entrega/web/graficos.js"]
ANEXO = {"en": "Appendix, outside the five graded pages", "es": "Anexo, fuera de las cinco páginas calificables"}
PDF = {"en": ENT / "report_en.pdf", "es": ENT / "informe_es.pdf"}


def fmt(v, dec, lang):
    s = f"{v:,.{dec}f}"
    return s if lang == "en" else s.replace(",", "\0").replace(".", ",").replace("\0", ".")


def pct(v, dec, lang):
    return fmt(v * 100, dec, lang) + ("%" if lang == "en" else " %")


def signo(v, dec, lang, porcentaje=False):
    """Número con signo explícito, + o el menos tipográfico (U+2212) que usan los textos."""
    s = pct(abs(v), dec, lang) if porcentaje else fmt(abs(v), dec, lang)
    return ("+" if v >= 0 else "\u2212") + s


def normalizar(t: str) -> str:
    return re.sub(r"\s+", " ", t.replace("\u00a0", " ").replace("\u202f", " ").replace("\u00ad", ""))


def texto_pdf(p: Path):
    from pypdf import PdfReader
    return [normalizar(pg.extract_text() or "") for pg in PdfReader(str(p)).pages]


def esperadas(c, lang):
    """Cifras que deben aparecer, tal como se escriben en cada idioma, y en qué entregable."""
    en = lang == "en"
    v, s30, ib, d = c["validacion"], c["s30"], c["ibnr"], c["datos"]
    ef, cal = c["entrega_final"], c["calibracion_nivel"]
    r41 = cal["evidencia"]["reservas_S41"]
    R = ("motor", "buildings", "contents")
    bi = next(x for x in ib["completitud_2024_por_peligro"] if x["ramo"] == "motor" and x["peligro"] == "bodily_injury")
    sub = next(x for x in ib["completitud_2024_por_peligro"] if x["ramo"] == "buildings" and x["peligro"] == "subsidence")
    pm = {x["anio"]: x for x in ib["prima_riesgo_por_anio"] if x["ramo"] == "motor"}
    res = v["reservas"]["V24"]
    top = [v["concentracion_v24"][r]["decil_superior_observado"] for r in ("motor", "buildings", "contents")]
    bat = c["controles_paquete"]["baterias"]
    casos = bat[0]["casos"] if all(b["pasan"] == b["casos"] == bat[0]["casos"] for b in bat) else None
    ok_csv = sum(1 for x in ef["controles_csv"].values() if x)
    fo, sf = c["calibracion_forma"], c["sensibilidad_final"]
    de = " of " if en else " de "
    e = {
        "puntuación pública": fmt(ef["publico"], 5, lang),
        "puntuación pública del modelo": fmt(s30["publico"], 5, lang),
        "puntuación pública de S41": fmt(ef["S41"]["publico"], 5, lang),
        "puntuación pública de la credibilidad revisada": fmt(ef["S42"]["publico"], 5, lang),
        "puntuación pública de la calibración de forma": fmt(fo["S43"]["kaggle"], 5, lang),
        "D² 2024 del modelo": fmt(v["d2_recalculado"]["V24"]["agregado"], 3, lang),
        "D² 2024 de la tasa constante": fmt(v["referencia_m00"]["V24"]["agregado"], 3, lang),
        "periodos de 2025": fmt(ef["filas"], 0, lang),
        "equipos": f"{ef['equipos']} " + ("teams" if en else "equipos"),
        "aportes del foro": f"{c['foro']['aportes']} " + ("posts" if en else "aportes"),
        "horas del foro": f"{round(c['foro']['horas'])} " + ("hours" if en else "horas"),
        "hallazgos abiertos": f"{c['validacion_ia']['abiertos']} " + ("open findings" if en else "hallazgos abiertos"),
        "total de 2025": fmt(s30["total_2025_CU"] / 1e6, 1, lang) + (" million CU" if en else " millones de CU"),
        "tasa de autos 2025": fmt(s30["tasa_2025_por_anio_exposicion"]["motor"], 1, lang) + " CU",
        "total de la entrega final": fmt(ef["total_2025_CU"] / 1e6, 1, lang) + (" million CU" if en else " millones de CU"),
        "puntuación esperada de S41": fmt(cal["S41"]["esperado"], 6, lang),

        "ruido del óptimo (edificios)": pct(cal["ramos"]["buildings"]["sigma_ruido"], 1, lang),
        "τ previa de edificios": pct(cal["ramos"]["buildings"]["tau_previa"], 1, lang),
        "τ revisada": pct(cal["tau_revisada"], 1, lang),
        "chi-cuadrado": fmt(cal["chi2"], 2, lang),
        "ganancia en el tercio usado": fmt(cal["bootstrap"]["ganancia_33"], 5, lang),
        "pérdida media en los otros dos tercios": fmt(abs(cal["bootstrap"]["ganancia_67_media"]), 5, lang),
        "prima escrita de edificios": signo(cal["ramos"]["buildings"]["prima_escrita_2024_2025"], 2, lang, True),
        "prima escrita de contenidos": signo(cal["ramos"]["contents"]["prima_escrita_2024_2025"], 2, lang, True),
        "tasa de autos sobre el último de 2024": signo(cal["ramos"]["motor"]["crecimiento_2025_S41"], 2, lang, True),
        "tasa de edificios sobre el último de 2024": signo(cal["ramos"]["buildings"]["crecimiento_2025_S41"], 2, lang, True),
        "tasa de contenidos sobre el último de 2024": signo(cal["ramos"]["contents"]["crecimiento_2025_S41"], 2, lang, True),
        "S3 de autos con la mezcla": pct(abs(cal["evidencia"]["reservas_S42"]["ibnr_lesiones_S3"]["S30"]), 1, lang),
        # Reservas con la regla de S41 (repro_s41, CLA-20261023-005) y la limitación mantenida para S41 (CLA-20261023-006)
        "S3 de autos con S41": pct(abs(r41["S3_autos"]["nivel"]), 2, lang),
        "intervalo de S3 con S41": pct(abs(r41["S3_autos"]["nivel_ic90"][1]), 2, lang) + (" to " if en else " a ")
                                   + pct(abs(r41["S3_autos"]["nivel_ic90"][0]), 2, lang),
        "error de reserva que mueve S41 en autos": pct(r41["error_material_S41"]["motor"], 1, lang),
        "completitud de lesiones": pct(round(bi["completitud_2024"], 2), 0, lang),
        "completitud de hundimiento": pct(round(sub["completitud_2024"], 2), 0, lang),
        "prima de autos observada 2024": fmt(pm[2024]["prima_T0"], 0, lang),
        "prima de autos con IBNR 2024": fmt(pm[2024]["prima_T0_mas_IBNR"], 0, lang),
        "predicción de autos 2025": fmt(pm[2025]["prediccion_final"], 0, lang),
        "correlación del cuerpo": fmt(c["publico_vs_local"]["spearman_cuerpo_05"], 2, lang),
        "correlación completa": fmt(c["publico_vs_local"]["spearman_completo"], 2, lang),
        "D² con reserva × 1": fmt(round(res["1.0"]["agregado"], 4), 4, lang),
        "D² con la peor reserva": fmt(round(min(res["0.75"]["agregado"], res["1.25"]["agregado"]), 4), 4, lang),
        "decil superior mínimo": fmt(round(min(top) * 100), 0, lang) + ("%" if en else " %"),
        "decil superior máximo": fmt(round(max(top) * 100), 0, lang) + ("%" if en else " %"),
        "recálculo independiente": f"{d['recalculo_independiente']['pasan']}{de}{d['recalculo_independiente']['total']}",
        "celdas comparadas": f"{round(d['base_reconstruida']['celdas_comparadas'] / 1e6)} " + ("million cells" if en else "millones de celdas"),
        "filas originales": fmt(d["base_reconstruida"]["filas"] / 1e6, 1, lang) + (" million rows" if en else " millones de filas"),
        "siniestros aceptados": fmt(d["flujo_siniestros"]["aceptados_asignados"], 0, lang),
        "registros de siniestros": fmt(d["flujo_siniestros"]["originales"], 0, lang),
        "capitales sin confirmar": f"{d['capitales_f0']['unconfirmed_PRM01R']} " + ("unconfirmed sums insured" if en else "capitales sin confirmación"),
        "peso de esos capitales": fmt(round(d["capitales_sin_confirmar"]["prediccion_CU"]), 0, lang) + " CU",
        "proporción de esos capitales": pct(d["capitales_sin_confirmar"]["proporcion_del_total"], 2, lang),
        "fuentes bibliográficas": f"{c['metodologia']['fuentes_investigacion']} " + ("primary sources" if en else "fuentes primarias"),
        "casos de control": f"{casos}{de}{casos}" if casos else "—falla de batería—",
        "controles de objetivo": c["bases"]["controles"].replace("/", de),
        "controles de variables": c["bases"]["f0_controles"].replace("/", de),
        "controles del CSV": f"{ok_csv}{de}{len(s30['controles_csv'])}",
        "nivel de edificios": pct(round(c["sensibilidad"]["nivel_edificios_semidistancia"], 3), 1, lang),
        "nivel de autos": (pct(c["sensibilidad"]["nivel_autos_escenario"][0], 1, lang) + " to " + pct(c["sensibilidad"]["nivel_autos_escenario"][1], 1, lang)) if en
                          else ("un " + pct(c["sensibilidad"]["nivel_autos_escenario"][0], 1, lang) + " y un " + pct(c["sensibilidad"]["nivel_autos_escenario"][1], 1, lang)),
        "empate con el envío anterior": f"{c['sensibilidad']['clientes_que_invierten_la_ventaja_V24']}{de}{fmt(c['sensibilidad']['clientes_V24'], 0, lang)}",
        "capitales sin dividir": f"{round(c['sensibilidad']['capitales_multiplicador'][0])} {'to' if en else 'a'} {round(c['sensibilidad']['capitales_multiplicador'][1])}",
        "error de reserva material en autos": pct(c["reservas_acotacion"]["por_ramo"]["motor"]["error_material"], 1, lang),
        "error de reserva material en edificios": pct(c["reservas_acotacion"]["por_ramo"]["buildings"]["error_material"], 1, lang),
        "nivel con reservas ×0,75 y ×1,25": pct(round(c["reservas_acotacion"]["nivel_max_con_b_075_125"], 3), 1, lang),
        "backtest fuera de criterio": (f"{c['sensibilidad']['backtest_ibnr']['fuera_min']} or {c['sensibilidad']['backtest_ibnr']['fuera_max']} of "
                                       if en else f"{c['sensibilidad']['backtest_ibnr']['fuera_min']} o {c['sensibilidad']['backtest_ibnr']['fuera_max']} de ")
                                      + str(c["sensibilidad"]["backtest_ibnr"]["peligros"]),
        "lesiones al cierre de 2022": "+" + pct(c["sensibilidad"]["backtest_ibnr"]["lesiones_ibnr_cierre"][0], 1, lang),
        "piso de semillas": fmt(c["sensibilidad"]["piso_semillas"], 5, lang),
        "pesos vecinos": f"{c['sensibilidad']['pesos_vecinos_que_mejoran']}{de}{c['sensibilidad']['vecinos_de_pesos_probados']}",
        "predicciones reproducidas": fmt(c["sensibilidad"]["reproduccion"]["predicciones"], 0, lang),
        "nombre del modelo definitivo": c["modelo_definitivo"]["nombre_en" if en else "nombre_es"],
        # Batería de sensibilidad de la entrega final (D103): ruido corregido, esperanzas en el privado y alarma
        "ruido 1,5 veces mayor": "1.5 times" if en else "1,5 veces",
        "umbral de la alarma": fmt(sf["alarma_S41_frente_S43"]["umbral"], 5, lang),
        "alarma de S41 frente a S43": fmt(sf["alarma_S41_frente_S43"]["media"], 7, lang),
        "alarma sin corregir el ruido": fmt(abs(sf["alarma_S41_frente_S43"]["sin_corregir_ruido"]), 7, lang),
        "alarma con posterior conjunta": fmt(sf["alarma_S41_frente_S43"]["posterior_conjunta"], 7, lang),
        "alarma con el redondeo": pct(sf["alarma_S41_frente_S43"]["redondeo_fraccion"], 1, lang),
        "alarma del nivel frente a S42": fmt(sf["alarma_S41_frente_S42"]["media"], 7, lang),
        "probabilidad de que S43 supere a S41": fmt(min(q["S43_menos_S41"]["P_S43_mejor"] for q in sf["esperanza_privado"]), 2, lang)
                                                + (" to " if en else " a ") + fmt(max(q["S43_menos_S41"]["P_S43_mejor"] for q in sf["esperanza_privado"]), 2, lang),
        "retroprueba de la forma en 2023": fmt(abs(sf["retroprueba_forma_N07"]["V23"]), 6, lang),
        "retroprueba de la forma en 2024": fmt(abs(sf["retroprueba_forma_N07"]["V24"]), 6, lang),
        "exponente de forma de autos probado": fmt(fo["ramos"]["motor"]["a_Z"], 3, lang),
    }
    for q in sf["esperanza_privado"]:
        for cand in ("S41", "S42", "S43"):
            e[f"esperanza de {cand} ({q['par']})"] = signo(q[cand]["media"], 6, lang)

    clases = {"apoyado": ("Supported", "Apoyado"), "parcial": ("Partial", "Parcial"), "sin_apoyo": ("Unsupported", "Sin apoyo"),
              "sin apoyo": ("Unsupported", "Sin apoyo")}
    for r in R:
        z, ev = cal["ramos"][r], cal["evidencia"]["ramos"][r]
        assert ev["clase"] == ev["clase_con_prima_anual"].replace("sin apoyo", "sin_apoyo"), r  # la lectura no depende de la unidad de la prima (DATA-006)
        e[f"lectura de la evidencia para S41 ({r})"] = clases[ev["clase_S41"]][0 if en else 1]
        e[f"corte de 2024 ({r})"] = signo(ev["indicadores"]["ultimo_anio"], 2, lang, True)
        e[f"efectos de etiqueta ({r})"] = signo(ev["indicadores"]["etiqueta_D95"], 2, lang, True)
        e[f"siniestralidad de 2024 ({r})"] = signo(ev["indicadores"]["siniestralidad_2024"], 2, lang, True)
        e[f"siniestralidad de 2024 con prima anual ({r})"] = signo(ev["siniestralidad_2024_prima_anual"], 2, lang, True)
        e[f"tope de tamaño ({r})"] = pct(ev["tope_tamano_S41"], 2, lang)
        e[f"ajuste de S41 ({r})"] = signo(ev["ajuste_S41"], 2, lang, True)
        e[f"credibilidad con el ruido corregido ({r})"] = fmt(c["sensibilidad_final"]["ruido"]["Z_nivel_D100_corregida"][r], 3, lang)
        e[f"parte del error de reserva que conserva S41 ({r})"] = pct(round(r41["sensibilidad_1_menos_Z_sobre_c"][r], 2), 0, lang)
        e[f"umbral de reservas de S41 ({r})"] = (" to " if en else " a ").join(fmt(x, 3, lang) for x in r41["umbral_b_S41"][r])
        e[f"siniestralidad de 2025 con S41 ({r})"] = fmt(ev["siniestralidad_2025"]["S41"], 3, lang)
        e[f"umbral de reservas de la mezcla ({r})"] = " to ".join(fmt(x, 3, lang) for x in cal["evidencia"]["reservas_S42"]["umbral_b_S30"][r]) if en else \
            " a ".join(fmt(x, 3, lang) for x in cal["evidencia"]["reservas_S42"]["umbral_b_S30"][r])
        e[f"factor de la entrega final ({r})"] = fmt(ef["factores_calibracion"][r], 4, lang)
        e[f"óptimo del público ({r})"] = fmt(z["c_optimo"], 3, lang)
        e[f"factor de S41 ({r})"] = fmt(z["c_S41"], 3, lang)
    if cal["evidencia"].get("condicion_prima"):
        e["hallazgo sobre la periodicidad de la prima"] = cal["evidencia"]["condicion_prima"]["hallazgo"]
    apendice = {
        "SHA-256 del CSV": s30["sha256_csv"], "envío de Kaggle": str(s30["envio_kaggle"]),
        "SHA-256 de la entrega final": ef["sha256_csv"], "envío de Kaggle de la entrega final": str(ef["envio_kaggle"]),
        "envío de Kaggle de S41": str(ef["S41"]["envio_kaggle"]),
        "tasa de autos de la entrega final": fmt(ef["tasa_2025_por_anio_exposicion"]["motor"], 1, lang),
        "D² V23": fmt(v["d2_recalculado"]["V23"]["agregado"], 5, lang), "D² V24": fmt(v["d2_recalculado"]["V24"]["agregado"], 5, lang),
    }
    for r in ("motor", "buildings", "contents"):
        f = s30["factores_nivel"][r]
        apendice[f"factores de nivel ({r})"] = " / ".join(fmt(f[k], 3, lang) for k in ("f23", "f24", "f"))
        apendice[f"D² V24 {r}"] = fmt(v["d2_recalculado"]["V24"][r], 5, lang)
        z = cal["ramos"][r]
        apendice[f"sondas ({r})"] = fmt(z["publico_x090"], 5, lang) + " / " + fmt(z["publico_x110"], 5, lang)
        apendice[f"factor final f × c ({r})"] = fmt(z["f_final_S41"], 4, lang)
        apendice[f"tasa de 2025 de la mezcla y de S41 ({r})"] = fmt(z["tasa_2025_modelo"], 1, lang) + " · " + fmt(z["tasa_2025_S41"], 1, lang)
    return e, apendice


def comprobar_texto(textos, cifras):
    faltan = []
    for k, s in cifras.items():
        if normalizar(s) not in textos:
            faltan.append(f"{k}: «{s}»")
    return faltan


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--raiz", type=Path, help="raíz del proyecto, para comprobar si las fuentes cambiaron")
    ap.add_argument("--sin-navegador", action="store_true")
    a = ap.parse_args()
    c = json.loads(CIFRAS.read_text(encoding="utf-8"))
    res = {}

    def anotar(nombre, ok, detalle=None, aviso=False):
        res[nombre] = {"estado": "pasa" if ok else ("aviso" if aviso else "falla"), "detalle": detalle or []}

    # 1. Páginas calificables y cifras del informe, en cada idioma
    for lang, p in PDF.items():
        paginas = texto_pdf(p)
        idx = next((i for i, t in enumerate(paginas) if ANEXO[lang] in t), None)
        anotar(f"informe_{lang}_paginas", idx is not None and idx <= 5,
               [f"anexo en la página {idx + 1 if idx is not None else '?'} de {len(paginas)}; calificables: {idx if idx is not None else '?'}"])
        cuerpo, anexo = " ".join(paginas[:idx or len(paginas)]), " ".join(paginas[idx or 0:])
        e, ap_ = esperadas(c, lang)
        anotar(f"informe_{lang}_cifras", not comprobar_texto(cuerpo + " " + anexo, e), comprobar_texto(cuerpo + " " + anexo, e))
        anotar(f"informe_{lang}_anexo", not comprobar_texto(anexo, ap_), comprobar_texto(anexo, ap_))
        pre, adv, tot = c["foro"]["por_tipo"].get("preinscripcion", 0), c["foro"]["por_tipo"].get("adverso", 0), c["foro"]["aportes"]
        # La frase del informe debe corresponder a la proporción real de preinscripciones y resultados adversos.
        bandas = [("two in five", "dos de cada cinco", 0.38, 0.45), ("more than a third", "más de un tercio", 1 / 3, 0.38),
                  ("nearly a third", "casi un tercio", 0.30, 1 / 3)]
        prop = (pre + adv) / tot
        esperada = next((x[0] if lang == "en" else x[1] for x in bandas if x[2] <= prop < x[3]), None)
        otras = [x[0] if lang == "en" else x[1] for x in bandas if (x[0] if lang == "en" else x[1]) != esperada]
        anotar(f"informe_{lang}_proporcion_foro", bool(esperada) and esperada in cuerpo and not any(o in cuerpo for o in otras),
               [f"{prop:.3f}: se espera «{esperada}»"])

    # 2. Láminas: número, PNG y cifras clave
    for lang in ("en", "es"):
        pdf = ENT / "video" / f"laminas_{lang}.pdf"
        paginas = texto_pdf(pdf) if pdf.exists() else []
        pngs = sorted((ENT / "video/laminas" / lang).glob("*.png"))
        texto = " ".join(paginas)
        e, _ = esperadas(c, lang)
        claves = ["puntuación pública", "D² 2024 del modelo", "periodos de 2025", "aportes del foro", "correlación del cuerpo",
                  "completitud de lesiones", "D² con reserva × 1", "casos de control"]
        faltan = comprobar_texto(texto, {k: e[k] for k in claves})
        anotar(f"laminas_{lang}", len(paginas) == 17 and len(pngs) == 17 and not faltan, [f"{len(paginas)} páginas, {len(pngs)} PNG"] + faltan)

    # 3. Identificadores de datos, autoría, estilo y clichés en textos y plantillas
    malos_id, malos_aut, malos_est = [], [], []
    for rel in TEXTOS + PLANTILLAS + ["docs/entrega/datos/cifras_entregables.json"]:
        p = REPO / rel
        if not p.exists():
            malos_est.append(f"{rel}: no existe")
            continue
        t = p.read_text(encoding="utf-8")
        malos_id += [f"{rel}: {m.group(0)}" for m in ID_DATOS.finditer(t)]
        if rel.endswith((".md", ".html", ".js")):
            malos_aut += [f"{rel}: «{m.group(0)}»" for rx in AUTORIA for m in rx.finditer(t)]
        if rel.endswith(".md"):
            malos_est += [f"{rel}: negrita inicial «{m.group(0).strip()[:40]}»" for m in NEGRITA_INICIAL.finditer(t)]
            malos_est += [f"{rel}: «{m.group(0)}»" for m in CLICHES.finditer(t)]
            if t.count("—") > 2:
                malos_est.append(f"{rel}: {t.count('—')} rayas largas")
    for rel in ("docs/expediente/foro/FORO.md", "docs/expediente/decisiones/DECISIONES.md"):
        p = REPO / rel
        if p.exists():
            malos_id += [f"{rel}: {m.group(0)}" for m in ID_DATOS.finditer(p.read_text(encoding="utf-8"))]
    anotar("sin_identificadores_de_datos", not malos_id, malos_id[:20])
    anotar("sin_atribucion_de_autoria", not malos_aut, malos_aut[:20])
    anotar("estilo_editorial", not malos_est, malos_est[:20])

    # 3b. Las guías de IA citan el número vigente de hallazgos del enjambre y de abiertos
    vi = c["validacion_ia"]
    guias = {"docs/entrega/AI_WORKFLOW_EN.md": f"Of the {vi['hallazgos']} swarm findings, {vi['abiertos']} remain open",
             "docs/entrega/USO_DE_IA_ES.md": f"De los {vi['hallazgos']} hallazgos del enjambre, {vi['abiertos']} siguen abiertos"}
    malos_g = [f"{rel}: falta «{frase}»" for rel, frase in guias.items() if frase not in (REPO / rel).read_text(encoding="utf-8")]
    anotar("guias_ia_hallazgos", not malos_g, malos_g)

    # 4. Enlaces relativos de los textos en Markdown
    rotos = []
    for rel in TEXTOS:
        p = REPO / rel
        if not p.exists():
            continue
        for m in re.finditer(r"!?\[[^\]]*\]\(([^)\s]+)\)", p.read_text(encoding="utf-8")):
            dest = m.group(1).split("#")[0]
            if not dest or re.match(r"[a-z]+:", dest):
                continue
            if not (p.parent / dest).exists():
                rotos.append(f"{rel} → {m.group(1)}")
    anotar("enlaces_relativos", not rotos, rotos[:20])

    # 5. Figuras en PNG por idioma
    from importlib import util
    spec = util.spec_from_file_location("ce", REPO / "herramientas/construir_entrega.py")
    ce = util.module_from_spec(spec)
    sys.argv, argv = [sys.argv[0]], sys.argv
    spec.loader.exec_module(ce)
    sys.argv = argv
    faltan_fig = [f"{lang}/{i}.png" for lang in ("en", "es") for i in ce.TAMANOS if not (ENT / "figuras" / lang / f"{i}.png").exists()]
    anotar("figuras_png", not faltan_fig, faltan_fig)

    # 6. Panel: sin errores, sin peticiones de red y con las cifras en ambos idiomas
    if a.sin_navegador:
        res["panel"] = {"estado": "omitida", "detalle": ["--sin-navegador: el panel no se abrió en Chromium"]}
    else:
        from playwright.sync_api import sync_playwright
        errores, externas, faltan_p = [], [], []
        with sync_playwright() as pw:
            b = pw.chromium.launch()
            pg = b.new_page(viewport={"width": 1440, "height": 900})
            pg.on("pageerror", lambda e: errores.append(str(e)))
            pg.on("request", lambda r: externas.append(r.url) if not r.url.startswith(("file:", "data:", "about:", "blob:")) else None)
            pg.goto((ENT / "panel_modelo.html").as_uri())
            pg.wait_for_function("window.LISTO === true", timeout=20000)
            for lang in ("es", "en"):
                pg.click(f"[data-idioma={lang}]")
                pg.wait_for_timeout(400)
                texto = normalizar(pg.inner_text("body"))
                e, _ = esperadas(c, lang)
                faltan_p += [f"{lang} {x}" for x in comprobar_texto(texto, {k: e[k] for k in ("puntuación pública", "D² 2024 del modelo", "periodos de 2025", "aportes del foro")})]
            b.close()
        anotar("panel", not errores and not externas and not faltan_p, errores[:5] + [f"red: {u}" for u in externas[:5]] + faltan_p)

    # 7. Frescura de las fuentes (aviso)
    if a.raiz:
        cambiadas = []
        for k, f in c["fuentes"].items():
            p = a.raiz / f["ruta"]
            if not p.exists():
                cambiadas.append(f"{k}: falta {f['ruta']}")
                continue
            datos = p.read_bytes()
            corte = c["foro"].get("corte") if k == "foro" else None
            if corte:  # el foro crece por el final: basta con que no cambie la parte contada
                if hashlib.sha256(datos[:corte["bytes"]]).hexdigest() != corte["sha256"]:
                    cambiadas.append(f"{k}: {f['ruta']} cambió antes de {corte['hasta_aporte']}")
                continue
            if hashlib.sha256(datos).hexdigest() != f["sha256"]:
                cambiadas.append(f"{k}: {f['ruta']} cambió")
        anotar("fuentes_sin_cambios", not cambiadas, cambiadas, aviso=True)

    fallan = [k for k, v in res.items() if v["estado"] == "falla"]
    salida = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "cifras_sha256": hashlib.sha256(CIFRAS.read_bytes()).hexdigest(),
              "pasan": sum(v["estado"] == "pasa" for v in res.values()), "avisos": [k for k, v in res.items() if v["estado"] == "aviso"],
              "fallan": fallan, "comprobaciones": res}
    (ENT / "datos/verificacion_entregables.json").write_text(json.dumps(salida, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for k, v in res.items():
        print(f"{v['estado']:>6}  {k}" + (f"  {'; '.join(v['detalle'][:4])}" if v["estado"] != "pasa" and v["detalle"] else ""))
    return 1 if fallan else 0


if __name__ == "__main__":
    sys.exit(main())
