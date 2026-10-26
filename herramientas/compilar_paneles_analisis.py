"""Regenera los dos HTML desde sus plantillas y agregados existentes, sin leer filas."""
from __future__ import annotations
import importlib.util
import json
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]


def main():
    ent=REPO/'docs/entrega'
    data=json.loads((ent/'analisis/datos_panel.json').read_text(encoding='utf-8'))
    encoded=json.dumps(data,ensure_ascii=False,allow_nan=False).replace('</','<\\/')
    template=(ent/'web/comparacion_plantilla.html').read_text(encoding='utf-8')
    (ent/'panel_analisis.html').write_text(template.replace('__ANALYSIS_DATA__',encoded),encoding='utf-8')
    spec=importlib.util.spec_from_file_location('entrega_builder',REPO/'herramientas/construir_entrega.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    css,js,cifras=module.recursos()
    template=(ent/'web/panel_plantilla.html').read_text(encoding='utf-8')
    old=template.replace('/*__CSS__*/',css).replace('/*__JS__*/',js).replace('/*__CIFRAS__*/','window.CIFRAS='+cifras.replace('</','<\\/')+';')
    (ent/'panel_modelo.html').write_text(old,encoding='utf-8')
    print('Dos paneles compilados. Sin entrenamiento ni lectura de datos por fila.')


if __name__=='__main__':
    main()
