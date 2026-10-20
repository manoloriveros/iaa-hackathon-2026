"""Pruebas de la capa de captura (herramientas/captura_modelos): nominales y adversas, con datos sintéticos.

Comprueba que guardar no cambia ningún resultado, que reproducir da vectores idénticos sin ajustar, y que reproducir se
detiene cuando cambia cualquier entrada de un ajuste (un valor de un predictor en dos filas, el orden de las categorías,
los pesos de un Pool de CatBoost, la entrada de un GLM o de la preparación de la red) o cuando el estimador falta o fue
alterado. Usa scripts sintéticos con los nombres que activan los parches de __main__ (severidad_cfs.py y mlp_tweedie.py)
escritos en una carpeta temporal; no lee datos del concurso.
Uso: python herramientas/probar_captura.py [--salida=<json>] [--compatibilidad=<captura.py de una versión anterior>]
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
CAPA = REPO / "herramientas" / "captura_modelos"

SCRIPT_ARBOLES = r'''
import os, sys, numpy as np, pandas as pd, lightgbm as lgb
from catboost import CatBoostRegressor, Pool

def glm_gamma(Z, y, w, iters=50):
    X = np.column_stack([np.ones(len(y)), Z]); beta = np.zeros(X.shape[1]); beta[0] = np.log(np.average(y, weights=w))
    for _ in range(iters):
        eta = X @ beta; mu = np.exp(eta); z = eta + (y - mu) / mu
        new = np.linalg.solve((X * w[:, None]).T @ X, (X * w[:, None]).T @ z)
        if np.max(np.abs(new - beta)) < 1e-9: beta = new; break
        beta = new
    return beta

def main():
    v = os.environ.get("VARIANTE", "")
    rng = np.random.default_rng(0); n = 8000
    cats = list("xyzw")
    X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n), "c": pd.Categorical(rng.choice(cats, n), categories=cats)})
    off = rng.uniform(0.2, 1, n); y = rng.poisson(off * np.exp(0.3 * X.a - 0.2 * X.b)).astype(float)
    # las variantes cambian solo la matriz de predictores, después de fijar etiquetas y offsets
    if v == "predictor_dos_filas":
        X.loc[[0, 1], "a"] = X.loc[[0, 1], "a"] + 0.5
    if v == "orden_categorias":
        X["c"] = X["c"].cat.reorder_categories(list("wzyx"))
    tr = np.arange(n) < 6000; cal = ~tr
    base = float(np.log(y[tr].sum() / off[tr].sum()))
    params = dict(objective="tweedie", tweedie_variance_power=1.5, learning_rate=0.05, num_leaves=7, num_threads=2, verbose=-1, seed=1,
                  bagging_fraction=0.8, bagging_freq=1)
    dtr = lgb.Dataset(X[tr], label=y[tr], init_score=np.log(off[tr]) + base, free_raw_data=False)
    dv = lgb.Dataset(X[cal], label=y[cal], init_score=np.log(off[cal]) + base, reference=dtr)
    b = lgb.train(params, dtr, num_boost_round=600, valid_sets=[dv], callbacks=[lgb.early_stopping(30, verbose=False)])
    p1 = b.predict(X[cal], raw_score=True, num_iteration=b.best_iteration or b.current_iteration())
    w = np.ones(int(tr.sum())) * (1.5 if v == "peso_pool" else 1.0)
    m = CatBoostRegressor(loss_function="Poisson", iterations=150, learning_rate=0.1, depth=4, thread_count=2, random_seed=3, verbose=0,
                          boost_from_average=False)
    m.fit(Pool(X[tr], y[tr], cat_features=["c"], baseline=np.log(off[tr]) + base, weight=w))
    p2 = m.predict(Pool(X[cal], cat_features=["c"]), prediction_type="RawFormulaVal")
    if not os.environ.get("SIN_POSICIONAL"):
        # GOV-008: CatBoost con marco de datos y sample_weight por posición (X, y, cat_features, text, embedding, graph, sample_weight)
        w2 = np.ones(int(tr.sum()))
        if v == "peso_posicional":
            w2[:10] = 2.0
        m2 = CatBoostRegressor(loss_function="Poisson", iterations=60, learning_rate=0.1, depth=3, thread_count=2, random_seed=4, verbose=0)
        m2.fit(X[tr], y[tr], ["c"], None, None, None, w2)
        p2 = np.concatenate([p2, m2.predict(X[cal])])
    pos = y > 0
    Z = np.column_stack([X.a.values, X.b.values])[pos]
    if v == "glm":
        Z = Z.copy(); Z[0, 0] += 0.25
    beta = glm_gamma(Z, y[pos] + 0.5, np.ones(pos.sum()))
    np.save(sys.argv[1], np.concatenate([p1, p2, beta]))

if __name__ == "__main__":
    main()
'''

SCRIPT_RED = r'''
import os, sys, numpy as np, pandas as pd, torch
from sklearn.preprocessing import QuantileTransformer
from torch import nn
torch.set_num_threads(2)
__CUERPO__
def main():
    v = os.environ.get("VARIANTE", "")
    rng = np.random.default_rng(0); n = 5000
    X = pd.DataFrame({"a": rng.normal(size=n), "b": np.where(rng.random(n) < 0.05, np.nan, rng.normal(size=n)),
                      "c": pd.Categorical(rng.choice(list("xyzwv"), n, p=[.4, .3, .2, .095, .005]))})
    if v == "prep":
        X.loc[[3, 4], "b"] = 9.0
    off = rng.uniform(0.2, 1, n); y = rng.poisson(off * np.exp(0.3 * X.a.fillna(0))).astype(float) * 1000
    tr = np.arange(n) < 3500; cal = (np.arange(n) >= 3500) & (np.arange(n) < 4200); ev = np.arange(n) >= 4200
    num, codes, cards = prep(X, tr)
    logoff = np.log(off) + float(np.log(y[tr].sum() / off[tr].sum()))
    net, be = train(num, codes, cards, y, logoff, np.flatnonzero(tr), np.flatnonzero(cal), epochs=4, seed=5, width=16, drop=0.1, lr=1e-3,
                    bs=512, patience=2, wd=1e-4)
    np.save(sys.argv[1], np.concatenate([predict(net, num, codes, logoff, np.flatnonzero(ev)), [be]]))

if __name__ == "__main__":
    main()
'''


def correr(carpeta: Path, script: str, salida: str, modo: str | None, capturas: Path, variante: str = "", capa: Path = CAPA, extra: dict | None = None):
    env = dict(os.environ)
    env.pop("CAPTURA_MODO", None)
    if modo:
        env.update({"PYTHONPATH": str(capa), "CAPTURA_MODO": modo, "CAPTURA_DIR": str(capturas), "CAPTURA_REPO": str(REPO)})
    env["VARIANTE"] = variante
    env.update(extra or {})
    p = subprocess.run([sys.executable, script, salida], cwd=str(carpeta), env=env, capture_output=True, text=True)
    ultima = (p.stderr.strip().splitlines() or [""])[-1]
    return p.returncode, ultima


def main():
    import numpy as np
    o = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    tmp = Path(tempfile.mkdtemp(prefix="probar_captura_"))
    fuente = (REPO / "src" / "modelos" / "mlp_tweedie.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def prep("):fuente.index("def main():")]
    (tmp / "severidad_cfs.py").write_text(SCRIPT_ARBOLES, encoding="utf-8")
    (tmp / "mlp_tweedie.py").write_text(SCRIPT_RED.replace("__CUERPO__", cuerpo), encoding="utf-8")
    casos = []

    def caso(nombre, esperado, rc, msg, tipo=None):
        import re
        hallado = re.search(r"no hay estimador (\w+)", msg)
        hallado = hallado.group(1) if hallado else ("alterado" if "no coincide con el SHA-256" in msg else None)
        ok = (rc == 0) if esperado == "pasa" else (rc != 0 and "REPRODUCIR" in msg and (tipo is None or hallado == tipo))
        casos.append({"caso": nombre, "esperado": esperado, "estimador_que_debe_detenerlo": tipo, "detenido_en": hallado, "rc": rc,
                      "mensaje": msg[-300:], "conforme": bool(ok)})

    for script in ("severidad_cfs.py", "mlp_tweedie.py"):
        cap = tmp / f"cap_{Path(script).stem}"
        rc0, m0 = correr(tmp, script, "sin.npy", None, cap)
        rc1, m1 = correr(tmp, script, "gua.npy", "guardar", cap)
        rc2, m2 = correr(tmp, script, "rep.npy", "reproducir", cap)
        igual_gua = rc0 == 0 and rc1 == 0 and np.array_equal(np.load(tmp / "sin.npy"), np.load(tmp / "gua.npy"))
        igual_rep = rc2 == 0 and np.array_equal(np.load(tmp / "gua.npy"), np.load(tmp / "rep.npy"))
        caso(f"{script}: guardar no cambia el resultado", "pasa", 0 if igual_gua else 1, m1)
        caso(f"{script}: reproducir da el mismo vector", "pasa", 0 if igual_rep else 1, m2)
        eventos = [json.loads(l) for d in cap.glob("*/eventos.jsonl") for l in d.read_text(encoding="utf-8").splitlines()]
        ajustes_en_reproducir = [e for e in eventos if e.get("modo") == "reproducir" and e.get("evento") not in ("cargado", "proceso")]
        caso(f"{script}: reproducir no guarda ni ajusta nada", "pasa", 0 if not ajustes_en_reproducir else 1, json.dumps(ajustes_en_reproducir)[:300])
        variantes = ({"predictor_dos_filas": "lgb", "orden_categorias": "lgb", "peso_pool": "cb", "peso_posicional": "cb", "glm": "glm"} if script == "severidad_cfs.py"
                     else {"prep": "prep"})
        for v, tipo in variantes.items():
            rc, m = correr(tmp, script, f"adv_{v}.npy", "reproducir", cap, v)
            caso(f"{script}: entrada cambiada ({v}) se rechaza en su estimador", "falla", rc, m, tipo)
        # estimador ausente y estimador alterado
        archivos = sorted(p for p in cap.glob("*/*") if p.suffix in (".txt", ".cbm", ".npy", ".pt", ".pkl"))
        objetivo = archivos[0]
        respaldo = objetivo.read_bytes()
        objetivo.unlink()
        rc, m = correr(tmp, script, "adv_falta.npy", "reproducir", cap)
        caso(f"{script}: estimador ausente ({objetivo.name.split('_')[0]}) se rechaza", "falla", rc, m, objetivo.name.split("_")[0])
        objetivo.write_bytes(respaldo + b" ")
        rc, m = correr(tmp, script, "adv_alterado.npy", "reproducir", cap)
        caso(f"{script}: estimador alterado se rechaza", "falla", rc, m, "alterado")
        objetivo.write_bytes(respaldo)
    anterior = o.get("compatibilidad")
    if anterior:
        # claves de la receta: guardar con una versión anterior y reproducir con la actual (llamadas sin posicionales extra)
        capa_ant = tmp / "capa_anterior"
        capa_ant.mkdir()
        shutil.copy2(anterior, capa_ant / "captura.py")
        shutil.copy2(CAPA / "sitecustomize.py", capa_ant / "sitecustomize.py")
        ver_ant = [l for l in Path(anterior).read_text(encoding="utf-8").splitlines() if l.startswith("VERSION")][0]
        for script in ("severidad_cfs.py", "mlp_tweedie.py"):
            cap = tmp / f"cap_compat_{Path(script).stem}"
            rc1, m1 = correr(tmp, script, "c_gua.npy", "guardar", cap, capa=capa_ant, extra={"SIN_POSICIONAL": "1"})
            rc2, m2 = correr(tmp, script, "c_rep.npy", "reproducir", cap, extra={"SIN_POSICIONAL": "1"})
            igual = rc1 == 0 and rc2 == 0 and np.array_equal(np.load(tmp / "c_gua.npy"), np.load(tmp / "c_rep.npy"))
            caso(f"{script}: estimadores guardados con {ver_ant} se cargan con la versión actual (mismas claves)", "pasa", 0 if igual else 1, m2 or m1)
    res = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": sys.version.split()[0],
           "captura_sha256": __import__("hashlib").sha256((CAPA / "captura.py").read_bytes()).hexdigest(),
           "captura_version": [l.split("=", 1)[1].strip().strip('"') for l in (CAPA / "captura.py").read_text(encoding="utf-8").splitlines() if l.startswith("VERSION")][0],
           "casos": casos, "conformes": sum(c["conforme"] for c in casos), "total": len(casos)}
    shutil.rmtree(tmp, ignore_errors=True)
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if o.get("salida"):
        Path(o["salida"]).write_text(texto, encoding="utf-8")
    print(texto)
    raise SystemExit(0 if res["conformes"] == res["total"] else 1)


if __name__ == "__main__":
    main()
