"""Append existing validation evidence to a candidate delivery record.

Read paired-bootstrap, simulated-public, reserve-sensitivity, robustness,
half-year and level-drift records from the workspace. Add optional line means,
row-level prediction provenance and the preregistered decision criterion when
available. Preserve CRLF in the delivery JSON; do not recalculate model results.

Usage: python anexar_entrega.py <key> <candidate> <previous> <sha256> <weight_selection> [<shape>]
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from comun import WORK

O = Path("/mnt/user-data/outputs/Envios")


def c(v, k=5):
    return f"{v:+.{k}f}".replace(".", ",")


def main():
    key, cand, prev, sha, seleccion = sys.argv[1:6]
    forma = sys.argv[6] if len(sys.argv) > 6 else "motor:1.09:0.95,buildings:1.08:1.14,contents:1.07:1"
    P = O / f"{key.upper()}_model_delivery.json"
    j = json.loads(P.read_text(encoding="utf-8"))
    b = json.loads((WORK / f"bootstrap_reference_{key}.json").read_text())
    ps = json.loads((WORK / f"publico_simulado_{key}.json").read_text())
    inf = json.loads((WORK / f"influencia_reservas_{key}.json").read_text())
    rob = json.loads((WORK / f"robustez_{key}_frente_{prev.lower()}.json").read_text())["candidatos"][cand]
    sem = json.loads((WORK / f"semestres_{key}.json").read_text())
    der = json.loads((WORK / f"deriva_nivel_{key}.json").read_text())

    def ic_txt(d):
        t = f"{c(d['dif'], 6)}; IC95 cliente [{c(d['ic95_cliente'][0], 6)}; {c(d['ic95_cliente'][1], 6)}]"
        if "ic95_direccion" in d:
            t += f", dirección [{c(d['ic95_direccion'][0], 6)}; {c(d['ic95_direccion'][1], 6)}]"
        return t

    def fmt(d):
        return (f"{c(d['dif'])}; IC95 cliente [{c(d['ic95_cliente'][0])}; {c(d['ic95_cliente'][1])}], "
                f"dirección [{c(d['ic95_direccion'][0])}; {c(d['ic95_direccion'][1])}]")
    j["validacion"]["intervalos_2024_frente_a_A_G_y_H"] = {
        "valores": {k: {"frente_a_AG": fmt(b[k]["CL_menos_AG"]), "frente_a_H": fmt(b[k]["CL_menos_H"])} for k in ("motor", "buildings", "contents", "agregado")},
        "metodo": "Modelos_base/bootstrap_reference.py: 1.000 réplicas Poisson por grupo, denominador fijo; mismas filas y T0",
        "nota": "A_G y H ajustan su meta dentro de 2024, así que la comparación local los favorece"}
    j["validacion"][f"frente_a_{prev}"] = {f: {k: f"{c(v['dif'])} (P>0 {str(v['P_mejora']).replace('.', ',')})" for k, v in rob[f].items()} for f in ("V23", "V24")}
    j["validacion"][f"frente_a_{prev}"]["sin_el_0_1_por_ciento_superior_V23_V24"] = {k: f"{c(rob['V23'][k]['dif_sin_top01'])} / {c(rob['V24'][k]['dif_sin_top01'])}" for k in rob["V24"]}
    tab = {}
    cn = inf["candidato"]; other = inf["comparadores"][0]
    for a in ("0.75", "1.0", "1.25"):
        tab[a] = {}
        for scope in ("motor", "buildings", "contents", "agregado"):
            row = inf["escenarios"][a][scope]
            tab[a][scope] = {f"d2_{cn}_{other}_H_A_G": [row["d2"][k] for k in (cn, other, "H", "A_G")],
                             f"{cn}_menos_H": ic_txt(row[f"{cn}_menos_H"]),
                             f"{cn}_menos_{other}": ic_txt(row[f"{cn}_menos_{other}"]),
                             f"{cn}_menos_A_G": ic_txt(row[f"{cn}_menos_A_G"]),
                             "diez_clientes_mas_favorables_frente_a_H": c(row[f"{cn}_menos_H"]["diez_clientes_mas_favorables"], 6),
                             "frente_a_H_sin_esos_diez": c(row[f"{cn}_menos_H"]["dif_sin_esos_diez"], 6)}
            if a == "1.25" and "cambio_numerador_por_peligro_a_mas25" in row[f"{cn}_menos_H"]:
                tab[a][scope]["cambio_numerador_frente_a_H_por_peligro"] = row[f"{cn}_menos_H"]["cambio_numerador_por_peligro_a_mas25"]
    j["validacion"]["reservas_de_caso_2024"] = {"tabla": tab, "metodo": "Modelos_base/influencia_reservas.py: etiqueta T0 + (a - 1) x reserva de caso de los abiertos aceptados (a = 0,75; 1; 1,25), predicciones sin cambio; IC95 por cliente; los diez clientes más favorables son un diagnóstico de influencia, no un criterio de descarte"}
    st = {}
    for a, res in sem["resultados"].items():
        st[a] = {k: {"filas": v["filas"], "peso_exposicion": v["peso_exposicion"], "madurez": v["madurez"],
                     f"{cn}_menos_H": ic_txt(v[f"{cn}_menos_H"]), f"{cn}_menos_{other}": ic_txt(v[f"{cn}_menos_{other}"]),
                     f"{cn}_menos_A_G": ic_txt(v[f"{cn}_menos_A_G"])} for k, v in res.items()}
    j["validacion"]["semestres_2024"] = {"tabla": st, "metodo": "Modelos_base/semestres.py: semestre de inicio del periodo (H1 enero-junio, H2 julio-diciembre); madurez = exposición efectiva / nominal; IC95 por cliente y, si se calculó, por dirección"}
    if (WORK / f"medias_por_ramo_{key}.json").exists():
        med = json.loads((WORK / f"medias_por_ramo_{key}.json").read_text())
        j["validacion"]["medias_por_ramo"] = {"tabla": med["medias"], "definiciones": med["definiciones"],
                                              "metodo": f"Modelos_base/exportar_predicciones.py (experimentos/medias_por_ramo_{key}.json)"}
    pq = WORK / f"predicciones_v23_v24_{key}.parquet"
    if pq.exists():
        h = hashlib.sha256(pq.read_bytes()).hexdigest()
        j["predicciones_por_fila_v23_v24"] = {"archivo": f"Hackaton/Semana 1/Modelos_base/experimentos/predicciones_v23_v24_{key}.parquet", "sha256": h,
                                              "columnas": ["row_id", "line", "corte", "y_T0", "reserva_caso", "prediction"],
                                              "nota": "las mismas predicciones que miden d2_sel (V23, sin factor) y d2_v24_f23 (V24, con el factor de V23); reserva_caso permite rehacer T0 + (a - 1) x reserva"}
    if (WORK / f"criterio_{key}.json").exists():
        j["criterio_fijado_antes_de_resultados"] = json.loads((WORK / f"criterio_{key}.json").read_text(encoding="utf-8"))
    p30 = ps["V24"]["30%"]; p30v23 = ps["V23"]["30%"]
    k_sp = f"{cand}-S09b"; k_prev = f"{prev}-{cand}"
    f1 = lambda x: f"{100 * x:.1f}".replace(".", ",")
    j["publico_simulado"] = (f"En 1.000 subconjuntos aleatorios del 30 % de los clientes, {cand} supera a S09b en el {f1(p30[k_sp]['P_mayor_que_0'])} % de los casos en V24 y el {f1(p30v23[k_sp]['P_mayor_que_0'])} % en V23, "
                             f"y a {prev} en el {f1(1 - p30[k_prev]['P_mayor_que_0'])} % (V24) y el {f1(1 - p30v23[k_prev]['P_mayor_que_0'])} % (V23) (Modelos_base/experimentos/publico_simulado_{key}.json)")
    j["validacion"]["seleccion_de_pesos"] = seleccion
    j["validacion"]["regla_de_nivel"] = {"metodo": "mezcla3.py --nivel=s17: fuera de la referencia de nivel los componentes cuyo total 2025/V24 se aparta más de un 1,5 % del ancla del ramo",
                                         "deriva_por_componente": {line: {r: v["deriva"] for r, v in comps.items()} for line, comps in der.items()}}
    j["reproduccion"] = (f"En el equipo: python3 reproducir_mezcla.py experimentos/spec_{key}_propio.json {forma} s17 {cand}_main {sha} "
                         "(desde Modelos_base; repite la mezcla a partir de las predicciones guardadas de cada componente)")
    txt = json.dumps(j, indent=1, ensure_ascii=False).replace("\n", "\r\n") + "\r\n"
    P.write_text(txt, encoding="utf-8", newline="")
    print(j["publico_simulado"])
    print(json.dumps(j["validacion"][f"frente_a_{prev}"], ensure_ascii=False))


if __name__ == "__main__":
    main()
