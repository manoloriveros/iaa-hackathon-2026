"""Centinela de ajustes para la réplica desde estimadores congelados (Claude, versión 1.0, 20 de octubre de 2026).

Solo actúa con CAPTURA_MODO=reproducir. La captura (herramientas/captura_modelos) sustituye cada ajuste conocido de la
receta por la carga de su estimador guardado, pero un entrenamiento que no pasara por sus envoltorios correría en
silencio. Este módulo cierra ese hueco: hace fallar con CentinelaAjuste cualquier entrenamiento real de las cuatro
bibliotecas que usa la receta.

  LightGBM      Booster.update (cada iteración de boosting, la use lgb.train o la interfaz scikit-learn)
  CatBoost      _CatBoostBase._train (el entrenamiento de CatBoostRegressor, CatBoostClassifier y CatBoost)
  PyTorch       Tensor.backward y torch.autograd.backward (sin gradientes no hay entrenamiento de la red)
  scikit-learn  QuantileTransformer.fit (el codificador de la red; fit_transform pasa por fit)

Los GLM gamma por IRLS son numpy puro y no se pueden bloquear sin tocar numpy; su control es que el número de cargas
de la réplica coincida con el de estimadores guardados por la corrida que los ajustó. Cargar y predecir no llama a
ninguna de las funciones bloqueadas, así que el centinela no cambia ningún resultado: solo convierte un ajuste
inesperado en un error.

Python importa este archivo como usercustomize, después de sitecustomize, cuando su carpeta está en PYTHONPATH:
  PYTHONPATH=herramientas/centinela_ajustes python herramientas/reproducir_capturado.py reproducir ...
reproducir_capturado.py antepone captura_modelos, así que los procesos de la receta cargan primero la captura y después
el centinela. Python no importa usercustomize con -s, -I ni dentro de un entorno virtual sin paquetes del sistema; por eso
cada proceso con nodo de la receta deja un evento «centinela» en CAPTURA_DIR/<nodo>/eventos.jsonl y otro
«centinela_aplicado» por biblioteca bloqueada. Un nodo de la réplica sin esos eventos no tuvo centinela.
"""
import os
import sys

VERSION_CENTINELA = "1.0"


class CentinelaAjuste(RuntimeError):
    pass


def _instalar():
    import importlib.abc

    try:
        import captura  # ya importado por el sitecustomize de captura_modelos en modo reproducir
    except Exception:  # noqa: BLE001
        captura = None

    def evento(fila):
        if captura is not None and not str(getattr(captura, "NODO", "_sin_nodo")).startswith("_sin_nodo"):
            captura._evento({**fila, "centinela_version": VERSION_CENTINELA})

    def bloquear(nombre):
        def f(*args, **kwargs):
            evento({"evento": "centinela_bloqueo", "funcion": nombre})
            raise CentinelaAjuste(f"CENTINELA: se llamó a {nombre} en modo reproducir; la réplica no puede ajustar nada")
        f._centinela = True
        return f

    def lgb(mod):
        mod.basic.Booster.update = bloquear("lightgbm.basic.Booster.update")
        return ["lightgbm.basic.Booster.update"]

    def cb(mod):
        mod.core._CatBoostBase._train = bloquear("catboost.core._CatBoostBase._train")
        return ["catboost.core._CatBoostBase._train"]

    def tor(mod):
        mod.Tensor.backward = bloquear("torch.Tensor.backward")
        mod.autograd.backward = bloquear("torch.autograd.backward")
        return ["torch.Tensor.backward", "torch.autograd.backward"]

    def skl(mod):
        mod.QuantileTransformer.fit = bloquear("sklearn.preprocessing.QuantileTransformer.fit")
        return ["sklearn.preprocessing.QuantileTransformer.fit"]

    post = {"lightgbm": lgb, "catboost": cb, "torch": tor, "sklearn.preprocessing": skl}

    def aplicar(nombre, mod):
        bloqueadas = post[nombre](mod)
        evento({"evento": "centinela_aplicado", "biblioteca": nombre, "funciones": bloqueadas})

    class Buscador(importlib.abc.MetaPathFinder):
        def __init__(self):
            self.buscando = set()

        def find_spec(self, name, path, target=None):
            # La captura también intercepta lightgbm y catboost recorriendo sys.meta_path; sin esta guarda de reentrada
            # los dos buscadores se llamarían el uno al otro sin fin.
            if name not in post or name in self.buscando:
                return None
            self.buscando.add(name)
            try:
                for f in sys.meta_path:
                    if f is self or not hasattr(f, "find_spec"):
                        continue
                    spec = f.find_spec(name, path, target)
                    if spec is not None:
                        break
                else:
                    return None
            finally:
                self.buscando.discard(name)
            cargador = spec.loader
            ejecutar = cargador.exec_module

            def exec_module(module, _ejecutar=ejecutar, _n=name):
                _ejecutar(module)
                aplicar(_n, module)
            cargador.exec_module = exec_module
            return spec

    sys.meta_path.insert(0, Buscador())
    for nombre in post:
        if nombre in sys.modules:
            aplicar(nombre, sys.modules[nombre])
    evento({"evento": "centinela", "bibliotecas": sorted(post), "argv": sys.argv})


if os.environ.get("CAPTURA_MODO") == "reproducir":
    _instalar()
