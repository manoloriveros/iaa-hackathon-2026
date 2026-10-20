"""Regresión de Pool previos a captura: solo dobles, sin importar ni cargar modelos.

Uso: python herramientas/probar_pool_sin_huella.py --salida=<json>
Los casos válidos llegan a un doble de _cargar_meta que interrumpe antes de cualquier acceso a estimadores.
"""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import os
import sys
import types
from contextlib import nullcontext
from datetime import datetime, timezone
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--salida", type=Path, required=True)
    args = parser.parse_args()
    repo = Path(__file__).resolve().parent.parent
    fuente = repo / "herramientas/captura_modelos/captura.py"
    raw = fuente.read_bytes()
    if args.salida.exists():
        parser.error("La salida ya existe; conservar el recibo anterior y usar otro destino.")
    fixtures = args.salida.with_name(args.salida.stem + "_fixtures")
    fixtures.mkdir(parents=True, exist_ok=False)
    # Los eventos de cada rechazo se conservan junto al recibo, fuera de Git al usar la ruta indicada por el plan.
    with nullcontext(str(fixtures.resolve())) as tmp:
        # La carga del módulo completo no instala ganchos ni importa CatBoost. Los dobles reciben solo dos filas.
        variables = {k: os.environ.get(k) for k in ("CAPTURA_MODO", "CAPTURA_DIR", "CAPTURA_REPO")}
        os.environ.update(CAPTURA_MODO="reproducir", CAPTURA_DIR=tmp, CAPTURA_REPO=tmp)
        try:
            spec = importlib.util.spec_from_file_location("captura_bajo_prueba_pool", fuente)
            capa = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(capa)
        finally:
            for k, value in variables.items():
                if value is None:
                    os.environ.pop(k, None)
                else:
                    os.environ[k] = value
        calls = {"buscar": 0, "cargar_modelo": 0, "fit_original": 0, "params": 0, "getters": 0}

        class BusquedaInterceptada(Exception):
            pass

        def cargar_meta(*a, **kw):
            calls["buscar"] += 1
            raise BusquedaInterceptada("Doble: búsqueda interceptada antes de archivos o deserialización.")

        capa._cargar_meta = cargar_meta

        class Pool:
            def __init__(self, data, label=None, *a, **kw):
                self.data, self.label = data, label

            def num_row(self):
                calls["getters"] += 1
                return 2

            def num_col(self):
                calls["getters"] += 1
                return 1

            def get_feature_names(self):
                calls["getters"] += 1
                return ["x"]

            def get_label(self):
                calls["getters"] += 1
                return self.label

            def get_baseline(self):
                calls["getters"] += 1
                return [[0.0], [0.0]]

        class Modelo:
            def get_params(self):
                calls["params"] += 1
                return {"iterations": 1}

            def fit(self, *a, **kw):
                calls["fit_original"] += 1
                raise AssertionError("Prohibido ajustar en esta prueba.")

            def load_model(self, *a, **kw):
                calls["cargar_modelo"] += 1
                raise AssertionError("Prohibido cargar un modelo en esta prueba.")

        def nuevo():
            return Pool([[1.0], [2.0]], [0.0, 1.0], weight=[1.0, 1.0])

        # Se construyen antes de instalar el envoltorio de Pool.
        previos = [nuevo() for _ in range(5)]
        capa._envolver_catboost(types.SimpleNamespace(Pool=Pool, CatBoostRegressor=Modelo))
        cases = []

        def caso(nombre, call, rechaza):
            antes = dict(calls)
            error = None
            try:
                call()
            except (capa.NoHayEstimador, BusquedaInterceptada) as exc:
                error = exc
            delta = {k: calls[k] - antes[k] for k in calls}
            if rechaza:
                ok = isinstance(error, capa.NoHayEstimador) and all(v == 0 for v in delta.values())
            else:
                ok = isinstance(error, BusquedaInterceptada) and delta["buscar"] == 1 and delta["cargar_modelo"] == delta["fit_original"] == 0
            cases.append({"id": nombre, "esperado": "rechazo_previo" if rechaza else "solo_busqueda_doble",
                          "conforme": ok, "llamadas": delta, "error": type(error).__name__, "mensaje": str(error)})

        caso("entrenamiento_previo", lambda: Modelo().fit(previos[0]), True)
        caso("validacion_previa_directa", lambda: Modelo().fit(nuevo(), eval_set=previos[1]), True)
        caso("validacion_previa_lista", lambda: Modelo().fit(nuevo(), eval_set=[nuevo(), previos[2]]), True)
        caso("validacion_previa_tupla", lambda: Modelo().fit(nuevo(), eval_set=(nuevo(), previos[3])), True)
        # La guarda revisa todos los argumentos posicionales sin depender del índice que ocupe eval_set.
        caso("validacion_previa_posicional", lambda: Modelo().fit(nuevo(), None, None, None, None, None, previos[4]), True)
        for name, fingerprint in (("huella_vacia", {}), ("huella_parcial", {"X": "a" * 24, "y": "b" * 24}),
                                  ("huella_tipo_incorrecto", "a" * 24),
                                  ("huella_digest_invalido", {"X": "z" * 24, "y": "b" * 24, "resto": "c" * 24})):
            pool = nuevo()
            pool._captura_huella = fingerprint
            caso(name, lambda pool=pool: Modelo().fit(pool), True)
        incomplete = nuevo()
        incomplete._captura_huella.pop("resto")
        caso("validacion_huella_incompleta", lambda: Modelo().fit(nuevo(), eval_set=[incomplete]), True)
        caso("entrenamiento_capturado", lambda: Modelo().fit(nuevo()), False)
        caso("validacion_capturada_directa", lambda: Modelo().fit(nuevo(), eval_set=nuevo()), False)
        caso("validacion_capturada_lista", lambda: Modelo().fit(nuevo(), eval_set=[nuevo(), nuevo()]), False)
        caso("matriz_sin_pool", lambda: Modelo().fit([[1.0], [2.0]], [0.0, 1.0]), False)
        events = [json.loads(line) for f in Path(tmp).glob("*/eventos.jsonl") for line in f.read_text(encoding="utf-8").splitlines()]
        assert len(events) == 10 and all(e.get("rechazado") is True for e in events)
        assert fuente.read_bytes() == raw, "Fuente cambió durante la prueba."
        assert not {"catboost", "lightgbm", "torch"}.intersection(sys.modules), "Se importó una biblioteca de modelos."
        result = {"autor": "Codex", "utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
                  "version_captura": capa.VERSION, "captura_sha256": hashlib.sha256(raw).hexdigest(),
                  "casos": cases, "conformes": sum(c["conforme"] for c in cases), "total": len(cases),
                  "eventos": events, "llamadas_totales": calls,
                  "alcance": "Módulo completo, envoltorio real de CatBoost y dobles de Pool/Modelo/búsqueda. No es CLI de reproducción ni prueba con CatBoost real.",
                  "modelos_importados": 0, "modelos_cargados": 0, "ajustes": 0, "inferencias": 0, "Kaggle": 0}
        args.salida.parent.mkdir(parents=True, exist_ok=True)
        with args.salida.open("x", encoding="utf-8") as f:
            json.dump(result, f, ensure_ascii=False, indent=2)
            f.write("\n")
        print(json.dumps({"conformes": result["conformes"], "total": result["total"], "captura_sha256": result["captura_sha256"], "llamadas": calls}))
        return 0 if result["conformes"] == result["total"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
