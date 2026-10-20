"""Activa la captura de estimadores (captura.py) solo cuando CAPTURA_MODO vale «guardar» o «reproducir».

Esta carpeta se pone primera en PYTHONPATH únicamente para las corridas con captura. Sin esa variable no hace nada.
El sitecustomize del sistema en el entorno de referencia (Ubuntu 24.04, /etc/python3.13/sitecustomize.py) está vacío.
"""
import os

if os.environ.get("CAPTURA_MODO") in ("guardar", "reproducir"):
    import captura

    captura.instalar()
