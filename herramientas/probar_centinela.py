"""Pruebas del centinela de ajustes (herramientas/centinela_ajustes) con datos sintéticos.

Comprueba cuatro cosas. Con la captura y el centinela, el modo reproducir da exactamente los vectores guardados, sin
ningún bloqueo, y deja los eventos que prueban que el centinela estuvo activo. Fuera del modo reproducir el centinela no
hace nada. Un entrenamiento que esquiva los envoltorios de la captura (interfaz scikit-learn de LightGBM,
lightgbm.engine.train, CatBoostClassifier, un bucle de PyTorch con backward y un QuantileTransformer ajustado aparte)
corre en silencio con la captura sola y se detiene con CentinelaAjuste cuando el centinela está activo. Reutiliza los
scripts sintéticos de probar_captura.py y una receta mínima propia para que la captura identifique los nodos; no lee
datos del concurso.
Uso: python herramientas/probar_centinela.py [--salida=<json>]
"""
from __future__ import annotations

import hashlib
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
CENTINELA = REPO / "herramientas" / "centinela_ajustes"
sys.path.insert(0, str(REPO / "herramientas"))
from probar_captura import SCRIPT_ARBOLES, SCRIPT_RED  # noqa: E402

SCRIPT_FUGA = r'''
import os, sys, numpy as np, pandas as pd
v = os.environ.get("VARIANTE", "")
rng = np.random.default_rng(1); n = 3000
X = pd.DataFrame({"a": rng.normal(size=n), "b": rng.normal(size=n)})
y = rng.poisson(np.exp(0.3 * X.a)).astype(float)
if v == "lgb_sklearn":
    import lightgbm as lgb
    p = lgb.LGBMRegressor(n_estimators=20, num_leaves=7, verbose=-1, n_jobs=2).fit(X, y).predict(X)
elif v == "lgb_engine":
    import lightgbm as lgb
    from lightgbm.engine import train as entrenar  # referencia directa, no pasa por lightgbm.train
    p = entrenar({"objective": "poisson", "verbose": -1, "num_threads": 2}, lgb.Dataset(X, label=y), num_boost_round=20).predict(X)
elif v == "cb_clasificador":
    from catboost import CatBoostClassifier
    p = CatBoostClassifier(iterations=20, depth=3, verbose=0, thread_count=2).fit(X, (y > 0).astype(int)).predict_proba(X)[:, 1]
elif v == "torch_backward":
    import torch
    torch.manual_seed(0)
    w = torch.zeros(2, requires_grad=True); opt = torch.optim.SGD([w], lr=0.01)
    t = torch.tensor(X.values, dtype=torch.float32); yt = torch.tensor(y, dtype=torch.float32)
    for _ in range(5):
        opt.zero_grad(); loss = (torch.exp(t @ w) - yt * (t @ w)).mean(); loss.backward(); opt.step()
    p = w.detach().numpy()
elif v == "qt_fit":
    from sklearn.preprocessing import QuantileTransformer
    p = QuantileTransformer(n_quantiles=50, random_state=0).fit_transform(X.values)[:, 0]
np.save(sys.argv[1], np.asarray(p, dtype="float64"))
'''

FUGAS = ("lgb_sklearn", "lgb_engine", "cb_clasificador", "torch_backward", "qt_fit")


def correr(carpeta: Path, script: str, salida: str, modo: str | None, capturas: Path, repo: Path, centinela: bool, variante: str = ""):
    env = dict(os.environ)
    for k in ("CAPTURA_MODO", "PYTHONPATH"):
        env.pop(k, None)
    rutas = [str(CAPA)] if modo else []
    if centinela:
        rutas.append(str(CENTINELA))
    if rutas:
        env["PYTHONPATH"] = os.pathsep.join(rutas)
    if modo:
        env.update({"CAPTURA_MODO": modo, "CAPTURA_DIR": str(capturas), "CAPTURA_REPO": str(repo)})
    env["VARIANTE"] = variante
    p = subprocess.run([sys.executable, script, salida], cwd=str(carpeta), env=env, capture_output=True, text=True)
    return p.returncode, (p.stderr.strip().splitlines() or [""])[-1]


def eventos(cap: Path):
    return [json.loads(l) for d in sorted(cap.glob("*/eventos.jsonl")) for l in d.read_text(encoding="utf-8").splitlines()]


def main():
    import numpy as np
    o = dict(a[2:].split("=", 1) for a in sys.argv[1:] if a.startswith("--") and "=" in a)
    tmp = Path(tempfile.mkdtemp(prefix="probar_centinela_"))
    fuente = (REPO / "src" / "modelos" / "mlp_tweedie.py").read_text(encoding="utf-8")
    cuerpo = fuente[fuente.index("def prep("):fuente.index("def main():")]
    scripts = {"severidad_cfs.py": SCRIPT_ARBOLES, "mlp_tweedie.py": SCRIPT_RED.replace("__CUERPO__", cuerpo), "fuga.py": SCRIPT_FUGA}
    for nombre, texto in scripts.items():
        (tmp / nombre).write_text(texto, encoding="utf-8")
    # receta mínima: un nodo por script (una entrada por cada salida usada, todas con el mismo id), para que la captura
    # guarde y busque en la misma carpeta y el centinela escriba sus eventos
    salidas = ["sin.npy", "gua.npy", "rep.npy", "rep_c.npy", "gua_c.npy"] + [f"{f}_{m}.npy" for f in FUGAS for m in ("solo", "cent")]
    nodos = [{"id": "sint_" + Path(s).stem, "script": s, "args": [x]} for s in scripts for x in salidas]
    (tmp / "receta").mkdir()
    (tmp / "receta" / "receta.json").write_text(json.dumps({"nodos": nodos}), encoding="utf-8")
    casos = []

    def caso(nombre, ok, detalle=""):
        casos.append({"caso": nombre, "conforme": bool(ok), "detalle": str(detalle)[-300:]})

    for script in ("severidad_cfs.py", "mlp_tweedie.py"):
        st = Path(script).stem
        cap = tmp / f"cap_{st}"
        r0 = correr(tmp, script, "sin.npy", None, cap, tmp, False)
        r1 = correr(tmp, script, "gua.npy", "guardar", cap, tmp, False)
        r2 = correr(tmp, script, "rep_c.npy", "reproducir", cap, tmp, True)
        r3 = correr(tmp, script, "gua_c.npy", "guardar", tmp / f"cap2_{st}", tmp, True)
        base = np.load(tmp / "sin.npy") if r0[0] == 0 else None
        igual = lambda f: base is not None and (tmp / f).exists() and np.array_equal(base, np.load(tmp / f))  # noqa: E731
        caso(f"{script}: reproducir con centinela da el vector guardado", r1[0] == 0 and r2[0] == 0 and igual("gua.npy") and igual("rep_c.npy"), r2[1])
        caso(f"{script}: con centinela en PYTHONPATH, guardar ajusta igual que sin captura", r3[0] == 0 and igual("gua_c.npy"), r3[1])
        ev = [e for e in eventos(cap) if e.get("modo") == "reproducir"]
        cent = [e for e in ev if e["evento"] == "centinela"]
        aplic = sorted({e["biblioteca"] for e in ev if e["evento"] == "centinela_aplicado"})
        bloqueos = [e for e in ev if e["evento"] == "centinela_bloqueo"]
        otros = [e for e in ev if e["evento"] not in ("proceso", "cargado", "centinela", "centinela_aplicado")]
        esperadas = ["catboost", "lightgbm", "sklearn.preprocessing"] if script == "severidad_cfs.py" else ["sklearn.preprocessing", "torch"]
        caso(f"{script}: el centinela deja su evento y se aplica a {', '.join(esperadas)}", len(cent) == 1 and all(b in aplic for b in esperadas),
             json.dumps({"centinela": len(cent), "aplicado": aplic}))
        caso(f"{script}: reproducir con centinela no bloquea, no guarda ni ajusta nada", not bloqueos and not otros, json.dumps(bloqueos + otros)[:300])
        sin_cent = [e for e in eventos(tmp / f"cap2_{st}") if e["evento"].startswith("centinela")]
        caso(f"{script}: fuera de reproducir el centinela no actúa", not sin_cent, json.dumps(sin_cent)[:300])
    capf = tmp / "cap_fuga"
    for f in FUGAS:
        rs = correr(tmp, "fuga.py", f"{f}_solo.npy", "reproducir", capf, tmp, False, f)
        rc = correr(tmp, "fuga.py", f"{f}_cent.npy", "reproducir", capf, tmp, True, f)
        caso(f"fuga {f}: con la captura sola el ajuste pasa en silencio", rs[0] == 0 and (tmp / f"{f}_solo.npy").exists(), rs[1])
        caso(f"fuga {f}: con el centinela se detiene con CentinelaAjuste", rc[0] != 0 and "CENTINELA" in rc[1] and not (tmp / f"{f}_cent.npy").exists(), rc[1])
    bloqueos = {e["funcion"] for e in eventos(capf) if e["evento"] == "centinela_bloqueo"}
    caso("fugas: cada bloqueo queda registrado en eventos.jsonl", len(bloqueos) >= 4, sorted(bloqueos))
    res = {"utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "python": sys.version.split()[0],
           "centinela_sha256": hashlib.sha256((CENTINELA / "usercustomize.py").read_bytes()).hexdigest(),
           "captura_sha256": hashlib.sha256((CAPA / "captura.py").read_bytes()).hexdigest(),
           "casos": casos, "conformes": sum(c["conforme"] for c in casos), "total": len(casos)}
    shutil.rmtree(tmp, ignore_errors=True)
    texto = json.dumps(res, ensure_ascii=False, indent=1)
    if o.get("salida"):
        Path(o["salida"]).write_text(texto, encoding="utf-8")
    print(texto)
    raise SystemExit(0 if res["conformes"] == res["total"] else 1)


if __name__ == "__main__":
    main()
