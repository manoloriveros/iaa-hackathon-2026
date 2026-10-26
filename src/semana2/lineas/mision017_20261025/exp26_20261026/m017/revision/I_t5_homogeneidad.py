"""Tarea 5: homogeneidad NB vs renovación del efecto género (motor, contents) y de works_from_home (contents);
descomposición frecuencia / severidad. Datos 2023+2024 agrupados, base T2b nivelada por celda × año.
(a) Tweedie p=1,5 cuasi-verosimilitud, offset log(m): y ~ celda×año + X + X:NB (LR con φ de Pearson; Wald robusto por cliente)
(b) Poisson en número de siniestros, offset log(exposición × c_fila), covariable log(m / (exp × c_fila)) libre
(c) Gamma (log) en severidad media por siniestro, pesos = nº de siniestros, misma covariable de riesgo."""
import sys, json, warnings
sys.path.insert(0, "/home/claude/m017/revision")
warnings.filterwarnings("ignore")
import numpy as np, pandas as pd
import statsmodels.api as sm
from scipy import stats
from I_lib import *

df = cargar()
OUT = "/home/claude/m017/revision"
res = {}


def design(d, xname, inter=True):
    cy = pd.get_dummies(d.new_business.astype(int).astype(str) + "_" + d.year.astype(str), drop_first=True).astype(float)
    X = cy.copy()
    X["const"] = 1.0
    X["x"] = d.x.values
    if inter:
        X["x_nb"] = d.x.values * d.new_business.values.astype(float)
    return X


def fit(model_fn, d, y, X, offset, **kw):
    full = model_fn(y, X, offset, **kw).fit()
    red = model_fn(y, X.drop(columns=["x_nb"]), offset, **kw).fit()
    phi = full.pearson_chi2 / full.df_resid
    lr = (red.deviance - full.deviance) / phi
    rob = model_fn(y, X, offset, **kw).fit(cov_type="cluster", cov_kwds={"groups": pd.factorize(d.customer_id)[0]})
    noint = model_fn(y, X.drop(columns=["x_nb"]), offset, **kw).fit(cov_type="cluster",
                                                                    cov_kwds={"groups": pd.factorize(d.customer_id)[0]})
    b, se = rob.params, rob.bse
    out = dict(rel_REN=float(np.exp(b["x"])), rel_NB=float(np.exp(b["x"] + b["x_nb"])),
               rel_comun=float(np.exp(noint.params["x"])),
               rel_comun_IC90=[float(np.exp(noint.params["x"] - 1.645 * noint.bse["x"])),
                               float(np.exp(noint.params["x"] + 1.645 * noint.bse["x"]))],
               p_comun_robusto=float(noint.pvalues["x"]),
               inter=float(np.exp(b["x_nb"])), inter_IC90=[float(np.exp(b["x_nb"] - 1.645 * se["x_nb"])),
                                                           float(np.exp(b["x_nb"] + 1.645 * se["x_nb"]))],
               p_inter_LR=float(stats.chi2.sf(lr, 1)), p_inter_robusto=float(rob.pvalues["x_nb"]), phi=float(phi))
    return out


def tweedie(y, X, off):
    return sm.GLM(y, X, family=sm.families.Tweedie(var_power=1.5, link=sm.families.links.Log()), offset=off)


def poisson(y, X, off):
    return sm.GLM(y, X, family=sm.families.Poisson(), offset=off)


def gamma(y, X, off, var_weights=None):
    return sm.GLM(y, X, family=sm.families.Gamma(link=sm.families.links.Log()), offset=off, var_weights=var_weights)


for line, var, lev in (("motor", "gender", "M"), ("contents", "gender", "M"), ("contents", "works_from_home", "True")):
    d = df[df.line == line].copy()
    # nivelación Tweedie-óptima por celda × año
    d["cy"] = d.new_business.astype(int).astype(str) + "_" + d.year.astype(str)
    k = d.groupby("cy").apply(lambda s: np.sum(s.y / np.sqrt(s.m)) / np.sum(np.sqrt(s.m)), include_groups=False)
    d["ml"] = d.m * d.cy.map(k)
    d["x"] = (d[var] == lev).astype(float)
    X = design(d, "x")
    r = {}
    r["tweedie_pp"] = fit(tweedie, d, d.y.values, X, np.log(d.ml.values))
    ex = d.exposure.values * d.c_fila.values
    Xf = X.copy()
    Xf["lr"] = np.log(d.ml.values / ex)
    r["frecuencia"] = fit(poisson, d, d.nclaims.values.astype(float), Xf, np.log(ex))
    c = d.nclaims.values > 0
    dc = d[c]
    Xs = Xf[c].copy()
    sev = dc.y.values / dc.nclaims.values
    ok = sev > 0
    full = gamma(sev[ok], Xs[ok], np.zeros(ok.sum()), var_weights=dc.nclaims.values[ok].astype(float))
    r["severidad"] = fit(lambda yy, XX, oo, **kw: gamma(yy, XX, oo, var_weights=dc.nclaims.values[ok].astype(float)),
                         dc[ok], sev[ok], Xs[ok], np.zeros(ok.sum()))
    # conteos crudos de apoyo
    r["claims_por_grupo"] = d.assign(g=np.where(d.new_business, "NB", "REN")).groupby(["g", var]).nclaims.sum().to_dict()
    r["claims_por_grupo"] = {f"{a}|{b_}": int(v) for (a, b_), v in r["claims_por_grupo"].items()}
    res[f"{line}|{var}={lev}"] = r
    print(line, var, lev)
    for kk in ("tweedie_pp", "frecuencia", "severidad"):
        q = r[kk]
        print(f"  {kk:11s} rel REN {q['rel_REN']:.3f} NB {q['rel_NB']:.3f} | común {q['rel_comun']:.3f} "
              f"IC90 [{q['rel_comun_IC90'][0]:.3f},{q['rel_comun_IC90'][1]:.3f}] p {q['p_comun_robusto']:.2g} | "
              f"interacción {q['inter']:.3f} IC90 [{q['inter_IC90'][0]:.3f},{q['inter_IC90'][1]:.3f}] "
              f"p_LR {q['p_inter_LR']:.3f} p_rob {q['p_inter_robusto']:.3f} phi {q['phi']:.1f}")
    print("  ", r["claims_por_grupo"])

json.dump(res, open(f"{OUT}/I_t5_homogeneidad.json", "w"), indent=1)
