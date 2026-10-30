"""Verify report values against their source artifacts; use the standard library and pandas for CSVs."""
import json, re, sys, hashlib
from pathlib import Path
import pandas as pd

R = Path(__file__).resolve().parents[1]
E = R / "entrega" if (R / "entrega").exists() else R
T = Path(__file__).resolve().parents[1] / "trabajo"
if not T.exists():  # Local evidence copies are packaged under entrega.
    T = None
txt = (E / "INFORME.md").read_text(encoding="utf-8")
J = lambda f: json.load(open(E / f, encoding="utf-8"))


def es(x, d):
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


def pct(x, d=1):
    return es(100 * x, d) + " %"


dev = pd.read_csv(E / "tabla_dev.csv")
D = lambda c, k, col="D2": float(dev[(dev.cand == c) & (dev.calib == k)][col].iloc[0])
hold = J("resultados_hold.json")["candidatos"]
H = lambda c: hold[c]["sin_tendencia"]["D2"]
bs = J("bootstrap_final.json"); prod = J("produccion_2025.json"); cal = J("calibracion_pcv.json"); ctx = J("contexto_2025.json")
_t = (lambda f, alt=None: json.load(open((T / f) if T else (E / (alt or Path(f).name)), encoding="utf-8")))
prep = _t("preparacion.json"); pesos = _t("pesos_2025_dev.json")
hb = J("hold_prueba_tendencia.json"); cred = J("credibilidad_entre_anios.json"); fig = J("figuras_datos.json")
tend_h = _t("pred/hold/tendencia.json", "tendencia_hold.json")
V = prod["variantes"]
pc = pd.read_csv(E / "prima_comercial_20.csv").groupby("ramo")[["prima_comercial", "prima_escrita"]].mean()
ic = lambda k: f"[{'+' if bs[k]['ic95'][0] >= 0 else '−'}{es(abs(bs[k]['ic95'][0]), 4)}; {'+' if bs[k]['ic95'][1] >= 0 else '−'}{es(abs(bs[k]['ic95'][1]), 4)}]"
checks = [
    ("total 2025", es(V["final_C1"]["total"], 0)),
    ("autos 2025", es(V["final_C1"]["totales"]["motor"]["total"], 0)),
    ("edificios 2025", es(V["final_C1"]["totales"]["buildings"]["total"], 0)),
    ("contenidos 2025", es(V["final_C1"]["totales"]["contents"]["total"], 0)),
    ("tasa autos", es(V["final_C1"]["totales"]["motor"]["tasa"], 1)),
    ("tasa edificios", es(V["final_C1"]["totales"]["buildings"]["tasa"], 1)),
    ("tasa contenidos", es(V["final_C1"]["totales"]["contents"]["tasa"], 1)),
    ("sha", V["final_C1"]["controles"]["sha256"][:16]),
    ("DEV T2b C1", es(D("T2b", "ramo"), 4)), ("HOLD T2b C1", es(H("T2b_C1"), 4)),
    ("DEV R0 C1", es(D("R0", "ramo"), 4)), ("HOLD R0", es(H("R0_C1"), 4)),
    ("dif DEV T2b-R0", "+" + es(bs["DEV_T2b_C1-R0_C1"]["dif"], 4)), ("IC DEV T2b-R0", ic("DEV_T2b_C1-R0_C1")),
    ("dif HOLD T2b-R0", "+" + es(bs["HOLD_T2b_C1-R0_C1"]["dif"], 4)), ("IC HOLD T2b-R0", ic("HOLD_T2b_C1-R0_C1")),
    ("dif DEV T2b-T1wp", "+" + es(bs["DEV_T2b_C1-T1wp_C1"]["dif"], 4)), ("IC DEV T2b-T1wp", ic("DEV_T2b_C1-T1wp_C1")),
    ("dif HOLD T2b-T1wp", "+" + es(bs["HOLD_T2b_C1-T1wp_C2"]["dif"], 4)), ("IC HOLD T2b-T1wp", ic("HOLD_T2b_C1-T1wp_C2")),
    ("N2a-N1 DEV", "+" + es(bs["DEV_N2a_C2-N1_C2"]["dif"], 4)), ("IC N2a-N1 DEV", ic("DEV_N2a_C2-N1_C2")),
    ("N2a-N1 HOLD", "+" + es(bs["HOLD_N2a_C2-N1_C2"]["dif"], 4)), ("IC N2a-N1 HOLD", ic("HOLD_N2a_C2-N1_C2")),
    ("N3-T2b DEV", "−" + es(abs(bs["DEV_N3_C2-T2b_C2"]["dif"]), 4)), ("IC N3-T2b DEV", ic("DEV_N3_C2-T2b_C2")),
    ("C2-C1 HOLD", es(abs(bs["HOLD_T2b_C2-T2b_C1"]["dif"]), 4)), ("IC C2-C1 HOLD", ic("HOLD_T2b_C2-T2b_C1")),
    ("T0 emergente", es(sum(sum(prep[f"emerging_{l}_T0_por_anio"].values()) for l in ("motor", "buildings", "contents")), 2)),
    ("compl 2024 autos", es(prep["emerging_motor_completitud_media_por_anio"]["2024"], 4)),
    ("compl 2024 edif", es(prep["emerging_buildings_completitud_media_por_anio"]["2024"], 4)),
    ("compl 2024 cont", es(prep["emerging_contents_completitud_media_por_anio"]["2024"], 4)),
    ("compl 2023 autos", es(prep["emerging_motor_completitud_media_por_anio"]["2023"], 4)),
    ("BI 90 días", pct(prep["cdf_coste_desarrollado"]["motor|bodily_injury"]["90"], 0)),
    ("BI 365 días", pct(prep["cdf_coste_desarrollado"]["motor|bodily_injury"]["365"], 0)),
    ("capital edif train", str(prep["emerging_buildings_capital_div1000"]["train"])),
    ("capital cont test", str(prep["emerging_contents_capital_div1000"]["test"])),
    ("duplicados", str(prep["developed_duplicados_retirados"])),
    ("AUC autos", es(pesos["motor"]["auc"], 2)), ("AUC hogar", es(pesos["buildings"]["auc"], 2)),
    ("incendio emergente", pct(prep["emerging_buildings_pesos_peligro"]["fire"], 1)),
    ("incendio desarrollado", pct(prep["developed_buildings_pesos_peligro"]["fire"], 1)),
    ("DEV T3bwp C2", es(D("T3bwp", "ramo_nb"), 4)), ("DEV T2b C2", es(D("T2b", "ramo_nb"), 4)),
    ("DEV N2a C2", es(D("N2a", "ramo_nb"), 4)), ("DEV N1 C2", es(D("N1", "ramo_nb"), 4)),
    ("DEV N3 C2", es(D("N3", "ramo_nb"), 4)), ("DEV E1 C2", es(D("E1", "ramo_nb"), 4)),
    ("DEV T4 C2", es(D("T4", "ramo_nb"), 4)), ("DEV T6 C2", es(D("T6", "ramo_nb"), 4)), ("DEV T5 C2", es(D("T5", "ramo_nb"), 4)),
    ("DEV T2b cuerpo", es(D("T2b", "ramo_nb", "D2_cuerpo"), 4)), ("DEV T2b w2025", es(D("T2b", "ramo_nb", "D2_w2025"), 4)),
    ("DEV T1wp w2025", es(D("T1wp", "ramo_nb", "D2_w2025"), 4)), ("DEV G1 C1", es(D("G1", "ramo"), 4)),
    ("HOLD N2a", es(H("N2a_C2"), 4)), ("HOLD N1", es(H("N1_C2"), 4)), ("HOLD T1wp", es(H("T1wp_C2"), 4)), ("HOLD T3bwp", es(H("T3bwp_C2"), 4)),
    ("tendencia hold autos", pct(tend_h["motor"]["tau_anual"] - 1, 1).replace(" %", "")),
    ("tend C2", "−" + es(abs(hb["T2b_C2"]["dif"]), 4)), ("tend C1", "−" + es(abs(hb["T2b_C1"]["dif"]), 4)),
    ("NB autos 2023", es(fig["ae_nb_anio"]["motor|True|2023"]["AE"], 2)), ("NB autos 2024", es(fig["ae_nb_anio"]["motor|True|2024"]["AE"], 2)),
    ("cred autos", es(cred["motor"]["z_optimo"], 1)),
    ("MCB autos", pct(cal["murphy"]["motor"]["MCB"] / cal["murphy"]["motor"]["S"], 1)),
    ("MCB edif", pct(cal["murphy"]["buildings"]["MCB"] / cal["murphy"]["buildings"]["S"], 1)),
    ("MCB cont", pct(cal["murphy"]["contents"]["MCB"] / cal["murphy"]["contents"]["S"], 1)),
    ("forma edif", es(cal["forma"]["buildings"]["ganancia_D2_en_muestra"], 4)),
    ("balance autos", pct(prod["balance_oof_pcv"]["motor"], 1)), ("balance cont", pct(prod["balance_oof_pcv"]["contents"], 1)),
    ("total C2", es(V["C2"]["total"], 0)), ("total preinscrita", es(V["preinscrita_C2_tendencia"]["total"], 0)),
    ("total tendencia", es(V["C1_tendencia"]["total"], 0)), ("total T2c", es(V["T2c_C1"]["total"], 0)),
    ("C2 sube", pct(V["C2"]["total"] / V["final_C1"]["total"] - 1, 1)),
    ("tasa obs 2023 autos", es(ctx["motor"]["2023"]["tasa_ultima_obs"], 1)), ("tasa obs 2024 edif", es(ctx["buildings"]["2024"]["tasa_ultima_obs"], 1)),
    ("razón edificios", es(ctx["buildings"]["2025"]["razon_riesgo_prima_escrita"], 2)),
    ("prima comercial autos", es(pc.loc["motor", "prima_comercial"], 1)), ("prima escrita edif", es(pc.loc["buildings", "prima_escrita"], 1)),
]
fallos = [(n, s) for n, s in checks if s not in txt]
# Final CSV checks.
cands = [E / "prediccion_2025_mlind.csv", E.parent / "privado" / "prediccion_2025_mlind.csv",
         E.parents[2] / "Repositorio_IAA2026" / "privado" / "semana2" / "transfer_ml_20261023" / "prediccion_2025_mlind.csv"]
csv = next((c for c in cands if c.exists()), None)
if csv is None:
    print("aviso: CSV de predicción no encontrado junto al informe; se omite su huella")
else:
    h = hashlib.sha256(csv.read_bytes()).hexdigest()
    if h != V["final_C1"]["controles"]["sha256"]:
        fallos.append(("sha del CSV", h))
for n, s in fallos:
    print("FALLA", n, s)
print(f"{len(checks) - len(fallos)} de {len(checks)} cifras del informe ligadas a su artefacto" + ("" if not fallos else " (hay fallos)"))
sys.exit(1 if fallos else 0)
