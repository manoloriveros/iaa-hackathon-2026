"""A05 (2): evaluación OOF totalmente anidada desde los raw guardados.

Para cada pliegue externo j: el nivel k de cada tronco, los pesos de la mezcla, C1 y C2 se estiman solo con los
otros pliegues, y los pesos y factores con predicciones internas cuyo k tampoco usó el pliegue j (k_{-i,-j}).
Uso: python3 anidado.py <dev|pcv> <salida.json> <receta1> [receta2 ...]   receta = A+B+C:encoge (encoge 0..1)
"""
import sys, json
import numpy as np, pandas as pd
from comun import *
from evaluar import mezcla_pesos, metricas, bootstrap_dif
import receta

FASE, SALIDA, RECETAS = sys.argv[1], sys.argv[2], sys.argv[3:]
import os
FIJOS = {}
if os.environ.get("MLIND_PESOS_FIJOS"):  # JSON de e26_pesos_des24.py; pesos por posición
    _j = json.load(open(os.environ["MLIND_PESOS_FIJOS"]))
    FIJOS = {l: list(_j["ramos"][l]["pesos"].values()) for l in LINEAS}
K_NB = 200.0
t = receta.tabla(FASE).reset_index(drop=True)
folds = pliegue(t.customer_id.values)
y = t.y.values; e = t.exposure.values; cf = t.c_fila.values; nbv = t.new_business.values


def raw_de(c):
    """raw del tronco con el que se hicieron las predicciones de la fase (dev/hold comparten; pcv/prod comparten)."""
    sub = {"dev": ["dev", "hold"], "pcv": ["pcv", "prod"]}[FASE]
    out = []
    for l in LINEAS:
        for s in sub:
            f = TRABAJO / "pred" / s / f"{c}raw_{l}.parquet"
            if f.exists():
                out.append(pd.read_parquet(f)); break
        else:
            raise FileNotFoundError(f"{c}raw_{l} en {sub}")
    r = pd.concat(out, ignore_index=True)
    v = t[["row_id"]].merge(r, on="row_id", how="left").raw.values
    assert not np.isnan(v).any(), c
    return v


def k_nivel(rw, m):
    return factor_tweedie(y[m], np.exp(rw[m]) * e[m] * cf[m])


def predecir(cs, enc, entreno, objetivo, R):
    """Mezcla + C1 + C2 estimados con 'entreno' (máscara) y aplicados a 'objetivo'. Los pesos y factores usan
    predicciones internas OOF dentro de 'entreno' con k que no ven el resto."""
    pli = np.unique(folds[entreno])
    U_in = np.zeros((entreno.sum(), len(cs))); idx = np.where(entreno)[0]
    U_out = np.zeros((objetivo.sum(), len(cs))); ido = np.where(objetivo)[0]
    for l in LINEAS:  # el nivel k es por ramo, como en transfer2.salidas y gbm.py
        L = (t.line.values == l)
        for i in pli:
            mi = (folds[idx] == i) & L[idx]
            fit = entreno & (folds != i) & L
            for a, c in enumerate(cs):
                U_in[mi, a] = k_nivel(R[c], fit) * np.exp(R[c][idx[mi]]) * e[idx[mi]]
        mo = L[ido]
        for a, c in enumerate(cs):
            U_out[mo, a] = k_nivel(R[c], entreno & L) * np.exp(R[c][ido[mo]]) * e[ido[mo]]
    res = {}
    for l in LINEAS:
        il_in = (t.line.values[idx] == l); il_out = (t.line.values[objetivo] == l)
        M = U_in[il_in] * cf[idx][il_in][:, None]
        if enc < 0:  # E26: pesos fijos estimados fuera (DES24), en el orden de los componentes
            w = np.array(FIJOS[l])
        else:
            w = mezcla_pesos(y[idx][il_in], M) if len(cs) > 1 else np.ones(1)
            w = (1 - enc) * w + enc / len(cs)
        m_in = M @ w; yy = y[idx][il_in]
        k1 = factor_tweedie(yy, m_in)
        base_out = U_out[il_out] @ w
        f2 = np.zeros(il_out.sum())
        for nb in (True, False):
            s = nbv[idx][il_in] == nb
            ks = factor_tweedie(yy[s], m_in[s] * k1); n = int((yy[s] > 0).sum()); z = n / (n + K_NB)
            f2[nbv[objetivo][il_out] == nb] = k1 * (z * ks + 1 - z)
        res[l] = (il_out, base_out, k1, f2, w)
    out = {"sin": np.zeros(objetivo.sum()), "C1": np.zeros(objetivo.sum()), "C2": np.zeros(objetivo.sum())}
    for l, (il, b, k1, f2, w) in res.items():
        out["sin"][il] = b; out["C1"][il] = b * k1; out["C2"][il] = b * f2
    return out


def main():
    recs = []
    for r in RECETAS:
        cs, enc = r.split(":") if ":" in r else (r, "0")
        recs.append((cs.split("+"), -1.0 if enc == "fijo" else float(enc)))
    todos = sorted({c for cs, _ in recs for c in cs} | {"T2b"})
    R = {c: raw_de(c) for c in todos}
    if ("T2b", 0.0) not in [(tuple(cs)[0] if len(cs) == 1 else None, enc) for cs, enc in recs]:
        recs = [(["T2b"], 0.0)] + recs
    preds = {}
    for cs, enc in recs:
        nom = "+".join(cs) + ("_des24" if enc < 0 else (f"_e{int(enc * 100)}" if len(cs) > 1 else ""))
        P = {k: np.zeros(len(t)) for k in ("sin", "C1", "C2")}
        for j in np.unique(folds):
            ob = folds == j
            o = predecir(cs, enc, ~ob, ob, R)
            for k in P:
                P[k][ob] = o[k]
        preds[nom] = P
        print(nom, {k: round(metricas(t, v)["D2"], 4) for k, v in P.items()}, flush=True)
    res = {"fase": FASE, "metricas": {n: {k: metricas(t, v) for k, v in P.items()} for n, P in preds.items()}, "bootstrap_vs_T2b": {}}
    for n, P in preds.items():
        if n == "T2b":
            continue
        res["bootstrap_vs_T2b"][n] = {k: bootstrap_dif(t, P[k], preds["T2b"][k]) for k in ("C1", "C2")}
        if FASE == "pcv":
            for nb in (True, False):
                s = nbv == nb
                res["bootstrap_vs_T2b"][n]["C1_" + ("NB" if nb else "REN")] = bootstrap_dif(
                    t[s].reset_index(drop=True), P["C1"][s], preds["T2b"]["C1"][s])
        print(n, {k: (round(v["dif"], 4), [round(x, 4) for x in v["ic95"]]) for k, v in res["bootstrap_vs_T2b"][n].items()}, flush=True)
    guardar_json(res, ENTREGA / "evolucion" / SALIDA)


if __name__ == "__main__":
    main()
