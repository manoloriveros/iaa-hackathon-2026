"""Captura y reproducción de estimadores de la receta sin modificar sus scripts.

Lo activa sitecustomize.py (en esta misma carpeta, que debe ir primero en PYTHONPATH) cuando la variable
CAPTURA_MODO vale «guardar» o «reproducir». Los scripts de src/ y reproducir.py se ejecutan sin cambios.

guardar     Cada ajuste se ejecuta como siempre. Al terminar, el estimador completo se escribe en
            CAPTURA_DIR/<nodo>/: LightGBM en texto con todas las iteraciones y la mejor iteración aparte, CatBoost en
            .cbm, coeficientes GLM en .npy a precisión completa, la red Tweedie con su state_dict y los codificadores de
            su preparación (medianas, columnas de faltantes, QuantileTransformer y categorías raras). Guardar no consume
            números aleatorios ni cambia el estado del modelo.
reproducir  Cada ajuste se sustituye por la carga del estimador guardado con la misma clave. Si no hay estimador para
            esa clave, el proceso se detiene con error: en este modo nunca se ajusta nada.

La clave es el SHA-256 de los parámetros y de todas las entradas del ajuste: los valores de la matriz de predictores (con
las categorías de cada columna categórica y su orden), etiquetas, offsets o baseline, pesos, nombres y tipos de columnas,
conjuntos de validación y parada temprana. No depende del orden de las llamadas ni de que un nodo se haya reanudado. En modo
reproducir, cualquier entrada distinta da otra clave y el proceso se detiene por estimador ausente. Cada guardado o carga
deja una línea en CAPTURA_DIR/<nodo>/eventos.jsonl con la clave, el archivo y su SHA-256, y la ficha de cada estimador
guarda además las huellas parciales de sus entradas. Dos ajustes con la misma clave que producen estimadores distintos se
registran como «duplicado_distinto».

Versión 1.1 (19 de octubre de 2026): la 1.0 resumía los marcos de datos y los Pool de CatBoost por forma, columnas y tipos,
sin sus valores ni los pesos del Pool (COD-20261019-117). Los estimadores capturados con la 1.0 se conservan aparte y sus
nodos se vuelven a capturar con la 1.1.

Versión 1.1.1 (19 de octubre de 2026): en modo reproducir se rechaza cualquier Pool de entrenamiento o validación sin
huella completa, incluido un Pool creado antes de instalar la captura. El rechazo precede a la búsqueda y carga del modelo.

Versión 1.1.2 (20 de octubre de 2026, GOV-008): la clave de CatBoost.fit incluye los argumentos posicionales (por ejemplo
sample_weight o eval_set pasados por posición) y la de lightgbm.train los posicionales y las opciones distintas de callbacks
(valid_names, feval, init_model…). Se añaden a la clave solo cuando existen, así que las llamadas sin ellos, que son todas
las de la receta, conservan exactamente la clave de las versiones 1.1 y 1.1.1. Un objeto sin representación estable (una
función, por ejemplo) produce una clave distinta en cada ejecución: el modo reproducir se detiene en lugar de cargar otro
estimador.

Variables: CAPTURA_MODO, CAPTURA_DIR (carpeta raíz de capturas), CAPTURA_REPO (raíz del repositorio, para identificar
el nodo de la receta a partir de la orden).
"""
from __future__ import annotations

import hashlib
import importlib.abc
import json
import os
import pickle
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

VERSION = "1.1.2"
MODO = os.environ.get("CAPTURA_MODO", "")
RAIZ = Path(os.environ.get("CAPTURA_DIR", "capturas"))
REPO = Path(os.environ.get("CAPTURA_REPO", ".")).resolve()
_ORDEN = {"n": 0}


class NoHayEstimador(RuntimeError):
    pass


def _ahora():
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _sha(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _nodo_de_argv() -> str:
    """Identifica el nodo de la receta por el script y los argumentos con que se lanzó el proceso."""
    argv = list(sys.argv)
    if not argv or not argv[0]:
        return "_sin_nodo"
    try:
        script = Path(argv[0]).resolve()
        receta = json.loads((REPO / "receta" / "receta.json").read_text(encoding="utf-8"))
    except Exception:
        return "_sin_nodo"
    for n in receta["nodos"]:
        if (REPO / n["script"]).resolve() != script:
            continue
        esperados = [str(REPO / a) if a.startswith("receta/") else a for a in n["args"]]
        if esperados == argv[1:]:
            return n["id"]
    return "_sin_nodo_" + script.stem


NODO = _nodo_de_argv()
DIR = RAIZ / NODO


def _dig(h, x):
    """Huella de un valor de entrada: parámetros, arreglos, marcos (forma, columnas y tipos) y conjuntos de datos."""
    import numpy as np
    if x is None or isinstance(x, (str, bool, int, float)):
        h.update(f"{type(x).__name__}:{x!r}|".encode())
        return
    if isinstance(x, (list, tuple)):
        h.update(f"{type(x).__name__}[".encode())
        for v in x:
            _dig(h, v)
        h.update(b"]")
        return
    if isinstance(x, dict):
        h.update(b"{")
        for k in sorted(x, key=str):
            h.update(f"{k}=".encode())
            _dig(h, x[k])
        h.update(b"}")
        return
    try:
        import pandas as pd
        if isinstance(x, pd.DataFrame):
            h.update(_huella_df(x).encode())
            return
        if isinstance(x, pd.Series):
            x = x.to_frame()
            h.update(_huella_df(x).encode())
            return
    except ImportError:
        pass
    if isinstance(x, np.generic):
        h.update(f"{x.dtype.str}:{x.item()!r}|".encode())
        return
    if isinstance(x, np.ndarray):
        a = np.ascontiguousarray(x)
        h.update(f"{a.dtype.str}|{a.shape}|".encode())
        h.update(repr(a.tolist()).encode() if a.dtype.kind == "O" else a.tobytes())
        return
    h.update(f"{type(x).__name__}:{x!r}|".encode())


def _huella_df(df) -> str:
    """Huella de contenido de un marco: forma, columnas, tipos, categorías (con su orden) y valores fila a fila."""
    import pandas as pd
    h = hashlib.sha256()
    h.update(f"DF{df.shape}|{list(map(str, df.columns))}|{[str(t) for t in df.dtypes]}|".encode())
    for c in df.columns:
        s = df[c]
        if isinstance(s.dtype, pd.CategoricalDtype):
            h.update(f"{c}:cats={list(map(str, s.cat.categories))}:ordered={s.cat.ordered}|".encode())
    h.update(pd.util.hash_pandas_object(df, index=False).values.tobytes())
    return h.hexdigest()


def _clave(*partes) -> str:
    h = hashlib.sha256()
    for p in partes:
        _dig(h, p)
    return h.hexdigest()[:24]


def _evento(fila: dict):
    DIR.mkdir(parents=True, exist_ok=True)
    _ORDEN["n"] += 1
    fila = {"utc": _ahora(), "nodo": NODO, "modo": MODO, "orden_en_proceso": _ORDEN["n"], "pid": os.getpid(), **fila}
    with open(DIR / "eventos.jsonl", "a", encoding="utf-8") as f:
        f.write(json.dumps(fila, ensure_ascii=False, default=str) + "\n")


def _escribir(ruta: Path, datos: bytes, tipo: str, clave: str, meta: dict):
    """Escribe un estimador; si ya existía con esa clave, compara y registra si es idéntico o distinto."""
    DIR.mkdir(parents=True, exist_ok=True)
    nuevo_sha = hashlib.sha256(datos).hexdigest()
    if ruta.exists():
        viejo = _sha(ruta)
        if viejo == nuevo_sha:
            _evento({"evento": "duplicado_identico", "tipo": tipo, "clave": clave, "archivo": ruta.name, "sha256": nuevo_sha})
            return
        k = 1
        while ruta.with_name(f"{ruta.stem}.dup{k}{ruta.suffix}").exists():
            k += 1
        ruta = ruta.with_name(f"{ruta.stem}.dup{k}{ruta.suffix}")
        _evento({"evento": "duplicado_distinto", "tipo": tipo, "clave": clave, "archivo": ruta.name, "sha256": nuevo_sha, "sha256_previo": viejo})
    tmp = ruta.with_name(ruta.name + ".tmp")
    tmp.write_bytes(datos)
    tmp.replace(ruta)
    m = ruta.with_suffix(".json") if ruta.suffix != ".json" else ruta.with_name(ruta.stem + ".meta.json")
    meta = {"tipo": tipo, "clave": clave, "archivo": ruta.name, "sha256": nuevo_sha, "bytes": len(datos), "nodo": NODO, "utc": _ahora(),
            "captura_version": VERSION, **meta}
    m.write_text(json.dumps(meta, ensure_ascii=False, indent=1, default=str), encoding="utf-8")
    _evento({"evento": "guardado", "tipo": tipo, "clave": clave, "archivo": ruta.name, "sha256": nuevo_sha, "bytes": len(datos)})


def _cargar_meta(tipo: str, clave: str, ext: str) -> tuple[Path, dict]:
    ruta = DIR / f"{tipo}_{clave}{ext}"
    if not ruta.exists():
        _evento({"evento": "falta_estimador", "tipo": tipo, "clave": clave, "archivo": ruta.name})
        raise NoHayEstimador(f"REPRODUCIR: no hay estimador {tipo} con clave {clave} en {DIR}; en este modo no se ajusta")
    meta = json.loads(ruta.with_suffix(".json").read_text(encoding="utf-8"))
    sha = _sha(ruta)
    if sha != meta["sha256"]:
        raise NoHayEstimador(f"REPRODUCIR: {ruta} no coincide con el SHA-256 de su ficha")
    _evento({"evento": "cargado", "tipo": tipo, "clave": clave, "archivo": ruta.name, "sha256": sha})
    return ruta, meta


# ---------------------------------------------------------------- LightGBM

def _params_json(p):
    return {str(k): (v.item() if hasattr(v, "item") else v) for k, v in dict(p).items()}


def _envolver_lgb(mod):
    orig = mod.train
    if getattr(orig, "_captura", False):
        return

    def train(params, train_set, num_boost_round=100, valid_sets=None, *args, **kwargs):
        callbacks = kwargs.get("callbacks")
        vs = list(valid_sets or [])
        partes = [dict(params), num_boost_round]
        huellas = {"params": _clave(dict(params), num_boost_round)}
        for i, ds in enumerate([train_set] + vs):
            datos = [ds.data, ds.label, ds.init_score, ds.weight, ds.categorical_feature, ds.feature_name, ds.params]
            partes += datos
            huellas[f"conjunto_{i}"] = {k: _clave(v) for k, v in zip(("X", "y", "offset", "peso", "categoricas", "nombres", "params_dataset"), datos)}
        partes.append([(type(c).__name__, getattr(c, "stopping_rounds", None), getattr(c, "min_delta", None)) for c in (callbacks or [])])
        extra = {k: v for k, v in kwargs.items() if k != "callbacks"}
        if args or extra:
            # 1.1.2: solo si existen, para que las llamadas sin ellos conserven la clave de 1.1 y 1.1.1
            partes.append(["extra_1_1_2", list(args), extra])
        clave = _clave(*partes)
        if MODO == "reproducir":
            ruta, meta = _cargar_meta("lgb", clave, ".txt")
            b = mod.Booster(model_str=ruta.read_text(encoding="utf-8"))
            b.best_iteration = int(meta["best_iteration"])
            return b
        t0 = time.time()
        b = orig(params, train_set, num_boost_round, valid_sets, *args, **kwargs)
        texto = b.model_to_string(num_iteration=-1)
        meta = {"best_iteration": int(b.best_iteration), "current_iteration": int(b.current_iteration()), "num_trees": int(b.num_trees()),
                "params": _params_json(params), "num_boost_round": int(num_boost_round), "segundos_ajuste": round(time.time() - t0, 2),
                "n_filas": int(getattr(train_set.data, "shape", [0])[0]), "columnas": list(map(str, getattr(train_set.data, "columns", []))),
                "valid_sets": len(vs), "parada_temprana": partes[-1], "huellas_entradas": huellas}
        _escribir(DIR / f"lgb_{clave}.txt", texto.encode("utf-8"), "lgb", clave, meta)
        return b

    train._captura = True
    mod.train = train


# ---------------------------------------------------------------- CatBoost

def _envolver_catboost(mod):
    cls = mod.CatBoostRegressor
    orig = cls.fit
    if getattr(orig, "_captura", False):
        return
    import numpy as np
    pool_init = mod.Pool.__init__

    def init_pool(self, data, label=None, *args, **kwargs):
        # huella de todo lo que entra en el Pool (valores de la matriz, etiquetas, categóricas, baseline, pesos y demás
        # argumentos), calculada antes de que CatBoost convierta los datos
        self._captura_huella = {"X": _clave(data), "y": _clave(label), "resto": _clave(list(args), kwargs)}
        pool_init(self, data, label, *args, **kwargs)

    init_pool._captura = True
    mod.Pool.__init__ = init_pool

    def huella_pool(p):
        if isinstance(p, mod.Pool):
            return [p.num_row(), p.num_col(), list(map(str, p.get_feature_names())), np.asarray(p.get_label(), dtype="float64"), p.get_baseline(),
                    getattr(p, "_captura_huella", None)]
        return [p]

    def exigir_huella_pool(p, entrada):
        if isinstance(p, mod.Pool):
            huella = getattr(p, "_captura_huella", None)
            completa = isinstance(huella, dict) and all(
                isinstance(huella.get(k), str) and len(huella[k]) == 24
                and all(c in "0123456789abcdef" for c in huella[k])
                for k in ("X", "y", "resto")
            )
            if not completa:
                _evento({"evento": "pool_sin_huella", "entrada": entrada, "rechazado": True,
                         "detalle": "Pool sin huella completa; pudo construirse antes de instalar la captura"})
                raise NoHayEstimador(
                    f"REPRODUCIR: Pool en {entrada} sin huella completa de entradas; "
                    "se rechaza antes de buscar o cargar el estimador"
                )
        elif isinstance(p, (list, tuple)):
            for i, valor in enumerate(p):
                exigir_huella_pool(valor, f"{entrada}[{i}]")
        elif isinstance(p, dict):
            for k, valor in p.items():
                exigir_huella_pool(valor, f"{entrada}[{k!r}]")

    def fit(self, X, y=None, *args, **kwargs):
        if MODO == "reproducir":
            # Antes de calcular claves o consultar estimadores, incluso si eval_set llegó por posición o en una lista.
            exigir_huella_pool(X, "entrenamiento")
            exigir_huella_pool(y, "y")
            exigir_huella_pool(args, "argumentos")
            exigir_huella_pool(kwargs, "opciones")
        ev = kwargs.get("eval_set")
        partes = [self.get_params(), huella_pool(X), y, huella_pool(ev) if ev is not None else None,
                  {k: v for k, v in kwargs.items() if k != "eval_set"}]
        if args:
            # 1.1.2 (GOV-008): posicionales con la huella de cada Pool; solo si existen, para conservar las claves anteriores
            partes.append(["posicionales_1_1_2", [huella_pool(a) for a in args]])
        if isinstance(X, mod.Pool) and getattr(X, "_captura_huella", None) is None:
            _evento({"evento": "pool_sin_huella", "detalle": "el Pool se construyó antes de instalar la captura"})
        clave = _clave(*partes)
        huellas = {"params": _clave(self.get_params()), "entrenamiento": getattr(X, "_captura_huella", None),
                   "validacion": getattr(ev, "_captura_huella", None) if ev is not None else None}
        if MODO == "reproducir":
            ruta, meta = _cargar_meta("cb", clave, ".cbm")
            self.load_model(str(ruta), format="cbm")
            bi = meta.get("best_iteration")
            self.get_best_iteration = (lambda bi=bi: bi)
            return self
        t0 = time.time()
        r = orig(self, X, y, *args, **kwargs)
        tmp = DIR / f"_cb_{clave}.tmp.cbm"
        DIR.mkdir(parents=True, exist_ok=True)
        self.save_model(str(tmp), format="cbm")
        datos = tmp.read_bytes()
        tmp.unlink()
        bi = self.get_best_iteration()
        meta = {"best_iteration": None if bi is None else int(bi), "tree_count": int(self.tree_count_), "params": _params_json(self.get_params()),
                "segundos_ajuste": round(time.time() - t0, 2), "n_filas": huella_pool(X)[0] if isinstance(X, mod.Pool) else None,
                "con_validacion": ev is not None, "huellas_entradas": huellas}
        _escribir(DIR / f"cb_{clave}.cbm", datos, "cb", clave, meta)
        return r

    fit._captura = True
    cls.fit = fit


# ---------------------------------------------------------------- GLM gamma por IRLS (severidad_cfs.py y severidad_cfs3.py)

def _envolver_glm(nombre):
    import numpy as np

    def fabrica(orig):
        if getattr(orig, "_captura", False):
            return orig

        def f(*args, **kwargs):
            clave = _clave(nombre, list(args), kwargs)
            if MODO == "reproducir":
                ruta, meta = _cargar_meta("glm", clave, ".npy")
                return np.load(ruta)
            beta = orig(*args, **kwargs)
            import io
            buf = io.BytesIO()
            np.save(buf, np.asarray(beta))
            meta = {"funcion": nombre, "coeficientes": [float(b).hex() for b in np.ravel(beta)], "coeficientes_decimal": [repr(float(b)) for b in np.ravel(beta)],
                    "n_obs": int(np.asarray(args[1]).shape[0]) if len(args) > 1 else None}
            _escribir(DIR / f"glm_{clave}.npy", buf.getvalue(), "glm", clave, meta)
            return beta

        f._captura = True
        f.__module__ = orig.__module__
        return f
    return fabrica


# ---------------------------------------------------------------- red Tweedie (mlp_tweedie.py)

def _aplicar_codificadores(X, enc):
    """Transformación de prep() con los codificadores guardados, sin estimar nada."""
    import numpy as np
    cats, nums = enc["cats"], enc["nums"]
    num = X[nums].astype("float64").values
    miss = np.isnan(num)
    num = np.where(miss, enc["med"], num)
    num = enc["qt"].transform(num).astype("float32")
    num = np.concatenate([num, miss[:, enc["keep_miss"]].astype("float32")], axis=1)
    codes = np.stack([X[c].cat.codes.values.astype("int64") + 1 for c in cats], axis=1) if cats else np.zeros((len(X), 0), "int64")
    cards = [len(X[c].cat.categories) + 1 for c in cats]
    for j in range(len(cats)):
        raro = enc["raros"][j]
        codes[:, j] = np.where(raro[codes[:, j]], 0, codes[:, j])
    return num, codes, cards


def _envolver_prep(orig):
    import numpy as np
    if getattr(orig, "_captura", False):
        return orig

    def prep(X, fit_mask):
        clave = _clave("prep", X, np.asarray(fit_mask))
        if MODO == "reproducir":
            ruta, meta = _cargar_meta("prep", clave, ".pkl")
            return _aplicar_codificadores(X, pickle.loads(ruta.read_bytes()))
        capt = {}

        def traza(frame, event, arg):
            if event == "call" and frame.f_code is orig.__code__:
                def local(fr, ev, a):
                    if ev == "return":
                        capt.update({k: fr.f_locals.get(k) for k in ("med", "keep_miss", "qt", "cats", "nums")})
                    return local
                return local
            return None
        previa = sys.gettrace()
        sys.settrace(traza)
        try:
            out = orig(X, fit_mask)
        finally:
            sys.settrace(previa)
        raros = []
        for c in capt["cats"]:
            c0 = X[c].cat.codes.values.astype("int64") + 1
            cnt = np.bincount(c0[np.asarray(fit_mask)], minlength=len(X[c].cat.categories) + 1)
            raros.append(cnt < 30)
        enc = {"med": capt["med"], "keep_miss": capt["keep_miss"], "qt": capt["qt"], "cats": list(capt["cats"]), "nums": list(capt["nums"]), "raros": raros}
        # comprobación: los codificadores guardados reproducen exactamente la salida de prep()
        rep = _aplicar_codificadores(X, enc)
        igual = bool(np.array_equal(rep[0], out[0]) and np.array_equal(rep[1], out[1]) and list(rep[2]) == list(out[2]))
        meta = {"columnas_numericas": enc["nums"], "columnas_categoricas": enc["cats"], "faltantes_conservados": int(np.sum(enc["keep_miss"])),
                "reaplicacion_identica": igual}
        _escribir(DIR / f"prep_{clave}.pkl", pickle.dumps(enc, protocol=5), "prep", clave, meta)
        if not igual:
            _evento({"evento": "codificadores_no_reproducen", "clave": clave})
        return out

    prep._captura = True
    prep.__module__ = orig.__module__
    return prep


def _envolver_train_red(orig):
    import numpy as np
    if getattr(orig, "_captura", False):
        return orig

    def train(num, codes, cards, y, logoff, idx_tr, idx_cal=None, epochs=40, seed=0, width=128, drop=0.1, lr=1e-3, bs=2048, patience=4, wd=1e-5):
        import torch
        clave = _clave("train", num, codes, list(cards), y, logoff, idx_tr, idx_cal, epochs, seed, width, drop, lr, bs, patience, wd)
        principal = sys.modules["__main__"]
        if MODO == "reproducir":
            ruta, meta = _cargar_meta("mlp", clave, ".pt")
            net = principal.Net(num.shape[1], list(cards), width, drop)
            net.load_state_dict(torch.load(str(ruta), weights_only=True))
            return net, int(meta["best_ep"])
        t0 = time.time()
        net, best_ep = orig(num, codes, cards, y, logoff, idx_tr, idx_cal, epochs, seed, width, drop, lr, bs, patience, wd)
        import io
        buf = io.BytesIO()
        torch.save({k: v.detach().clone() for k, v in net.state_dict().items()}, buf)
        meta = {"best_ep": int(best_ep), "n_num": int(num.shape[1]), "cards": list(map(int, cards)), "width": width, "drop": drop, "seed": seed,
                "epochs": epochs, "patience": patience, "segundos_ajuste": round(time.time() - t0, 2)}
        _escribir(DIR / f"mlp_{clave}.pt", buf.getvalue(), "mlp", clave, meta)
        return net, best_ep

    train._captura = True
    train.__module__ = orig.__module__
    return train


# ---------------------------------------------------------------- instalación

_POST_IMPORT = {
    "lightgbm": _envolver_lgb,
    "catboost": _envolver_catboost,
    "severidad_cfs": lambda m: setattr(m, "glm_gamma", _envolver_glm("glm_gamma")(m.glm_gamma)),
}
_EN_MAIN = {
    "severidad_cfs.py": {"glm_gamma": _envolver_glm("glm_gamma")},
    "severidad_cfs3.py": {"glm_gamma_ridge": _envolver_glm("glm_gamma_ridge")},
    "mlp_tweedie.py": {"prep": _envolver_prep, "train": _envolver_train_red},
}


class _Buscador(importlib.abc.MetaPathFinder):
    def find_spec(self, name, path, target=None):
        if name not in _POST_IMPORT:
            return None
        for f in sys.meta_path:
            if f is self or not hasattr(f, "find_spec"):
                continue
            spec = f.find_spec(name, path, target)
            if spec is not None:
                break
        else:
            return None
        cargador = spec.loader
        ejecutar = cargador.exec_module

        def exec_module(module, _ejecutar=ejecutar, _n=name):
            _ejecutar(module)
            _POST_IMPORT[_n](module)
        cargador.exec_module = exec_module
        return spec


def _parchear_main(envoltorios: dict):
    pendientes = dict(envoltorios)

    def local(frame, event, arg):
        if event == "line" and pendientes:
            g = frame.f_globals
            for n in list(pendientes):
                f = g.get(n)
                if callable(f) and getattr(f, "__module__", None) == "__main__" and not getattr(f, "_captura", False):
                    g[n] = pendientes.pop(n)(f)
            if not pendientes:
                sys.settrace(None)
                return None
        return local

    def global_(frame, event, arg):
        if event == "call" and frame.f_code.co_name == "<module>" and frame.f_globals.get("__name__") == "__main__":
            return local
        return None
    sys.settrace(global_)


def instalar():
    if MODO not in ("guardar", "reproducir"):
        return
    sys.meta_path.insert(0, _Buscador())
    script = Path(sys.argv[0]).name if sys.argv and sys.argv[0] else ""
    if script in _EN_MAIN:
        _parchear_main(_EN_MAIN[script])
    if not NODO.startswith("_sin_nodo"):
        _evento({"evento": "proceso", "argv": sys.argv, "python": sys.version.split()[0], "captura_version": VERSION})
