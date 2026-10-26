"""Tarea 6: fuga / estabilidad. ¿La variable está fijada antes del periodo? ¿Hay señales de artefacto posterior al
siniestro? Pruebas:
 1) constancia por cliente / póliza entre años;
 2) faltantes de ocupación según haya o no siniestro en el mismo año (un dato capturado al siniestrar daría menos NA);
 3) panel balanceado (mismos clientes en 2023 y 2024): relación de la variable con la frecuencia de 2023 y de 2024
    (un artefacto posterior se asociaría más con el año del siniestro que con el otro);
 4) NB de 2024 (clientes nuevos, dato capturado al inicio): el efecto aparece en clientes sin historia previa;
 5) relación con siniestros declarados previos (prior_claims_5y, anterior al periodo)."""
import sys, json
sys.path.insert(0, "/home/claude/m017/revision")
import numpy as np, pandas as pd
from I_lib import *

df = cargar()
OUT = "/home/claude/m017/revision"
res = {}
cu = pd.read_parquet(f"{DE}/customers.parquet")
res["clientes_filas_unicas"] = bool(cu.customer_id.is_unique)
c = df[df.line == "contents"]
res["wfh_polizas_multianio_con_cambio"] = int((c.groupby("policy_id").works_from_home.nunique() > 1).sum())
res["wfh_polizas_multianio"] = int((c.groupby("policy_id").size() > 1).sum())

# 2) NA de ocupación vs siniestro en el año
d = df[df.line.isin(["motor", "contents"])].copy()
d["claim"] = d.nclaims > 0
res["occ_NA_por_siniestro"] = {f"{l}|{y}|{'con' if k else 'sin'}": round(float(g.occ.eq('NA').mean()), 4)
                                for (l, y, k), g in d.groupby(["line", "year", "claim"])}

# 3) panel balanceado: frecuencia relativa (siniestros / m nivelado) por nivel, mismos clientes, ambos años
out3 = {}
for line, vs in VARS.items():
    s = df[df.line == line].copy()
    both = s.groupby("customer_id").year.nunique()
    s = s[s.customer_id.isin(both[both == 2].index)]
    s["cy"] = s.new_business.astype(int).astype(str) + s.year.astype(str)
    s["ml"] = s.m * s.cy.map(s.groupby("cy").y.sum() / s.groupby("cy").m.sum())
    for v in vs:
        r = {}
        for yr in (2023, 2024):
            t = s[s.year == yr]
            g = t.groupby(v).agg(n=("nclaims", "sum"), ml=("ml", "sum"), y=("y", "sum"))
            base_f = g.n.sum() / g.ml.sum()
            g["frec_rel"] = g.n / g.ml / base_f
            g["pp_rel"] = g.y / g.ml
            r[yr] = g
        a, b = r[2023], r[2024]
        if len(a) <= 3:
            out3[f"{line}|{v}"] = {str(k): dict(frec23=round(a.frec_rel[k], 3), frec24=round(b.frec_rel[k], 3),
                                                pp23=round(a.pp_rel[k], 3), pp24=round(b.pp_rel[k], 3))
                                   for k in a.index}
        else:
            w = np.minimum(a.n, b.n)
            out3[f"{line}|{v}"] = dict(corr_frec_23_24=round(float(np.corrcoef(np.log(a.frec_rel), np.log(b.frec_rel))[0, 1]), 3),
                                       corr_pp_23_24=round(float(np.corrcoef(np.log(a.pp_rel.clip(1e-3)), np.log(b.pp_rel.clip(1e-3)))[0, 1]), 3),
                                       niveles=int(len(a)), clientes=int(s.customer_id.nunique()))
    out3[f"{line}|clientes_panel"] = int(s.customer_id.nunique())
res["panel_balanceado"] = out3

# 4) NB 2024 (clientes nuevos): frecuencia relativa por nivel
out4 = {}
for line, vs in VARS.items():
    t = df[(df.line == line) & (df.year == 2024) & df.new_business].copy()
    t["ml"] = t.m * t.y.sum() / t.m.sum()
    for v in vs:
        if t[v].nunique() > 3:
            continue
        g = t.groupby(v).agg(n=("nclaims", "sum"), ml=("ml", "sum"))
        out4[f"{line}|{v}"] = {str(k): round(float(x), 3) for k, x in (g.n / g.ml / (g.n.sum() / g.ml.sum())).items()}
res["NB2024_frec_rel"] = out4

# 5) relación con siniestros declarados previos (antes del periodo)
out5 = {}
cl = cu.copy()
cl["occ"] = cl.occupation.where(cl.occupation.isna(),
                                cl.occupation.astype(object).str.lower().str.strip().str.replace("self-employed ", "", regex=False).str.strip()).fillna("NA")
for v in ("gender", "marketing_segment"):
    out5[v] = cl.groupby(v).prior_claims_5y.mean().round(3).to_dict()
out5["previous_insurer_rango_media"] = [round(float(x), 3) for x in cl.groupby("previous_insurer").prior_claims_5y.mean().agg(["min", "max"])]
res["prior_claims_5y_media"] = out5

# marketing_segment: ¿derivado de la edad? tabla cruzada con policyholder_age_band (contents)
pc = pd.read_parquet(f"{DE}/policies_contents.parquet", columns=["row_id", "policyholder_age_band"])
s = df[df.line == "contents"].merge(pc, on="row_id")
ct = pd.crosstab(s.marketing_segment.str.split("_").str[0], s.policyholder_age_band, normalize="index").round(2)
res["segmento_vs_edad"] = ct.to_dict()
print(json.dumps(res, indent=1, default=str))
json.dump(res, open(f"{OUT}/I_t6_fuga.json", "w"), indent=1, default=str)
