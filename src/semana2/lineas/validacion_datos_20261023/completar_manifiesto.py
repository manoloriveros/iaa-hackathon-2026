"""Añade al manifiesto de la validación las huellas de los documentos y del tablero (lo que validar_datos_s2.py no escribe)."""
import hashlib
import json
import pathlib

D = pathlib.Path(__file__).resolve().parent
m = json.loads((D / 'manifiesto.json').read_text(encoding='utf-8'))
docs = ['INFORME.md', 'aporte_CLA-S2-20261023-004.md', 'cifras_informe.json', 'verificar_informe.py', 'verificacion_informe.json',
        'construir_tablero.py', 'tablero.html', 'completar_manifiesto.py', 'parche_20261024.py']
for n in list(m['salidas']):
    m['salidas'][n] = hashlib.sha256((D / n).read_bytes()).hexdigest() if isinstance(m['salidas'][n], str) else dict(m['salidas'][n], sha256=hashlib.sha256((D / n).read_bytes()).hexdigest())
m['documentos'] = {n: dict(sha256=hashlib.sha256((D / n).read_bytes()).hexdigest(), bytes=(D / n).stat().st_size) for n in docs}
m['nota_documentos'] = ('Las huellas de documentos se añadieron después de la corrida con completar_manifiesto.py, que también refresca las de salidas (INFORME.md se terminó de escribir después de la corrida); verificacion_informe.json '
                        'lleva la hora de su ejecución, así que su huella cambia al repetir el verificador aunque el resultado sea el mismo.')
(D / 'manifiesto.json').write_text(json.dumps(m, ensure_ascii=False, indent=1), encoding='utf-8')
print(json.dumps({k: v['sha256'][:16] for k, v in m['documentos'].items()}, indent=0))
print(list(m.keys()))
