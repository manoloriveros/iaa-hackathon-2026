"""Acta enmendada de la puerta 2024 bajo S2-SELECCION-v2-20261024 (enmienda humana explícita de SEL01).

No reabre 2024 ni lee etiquetas: aplica la regla enmendada a las cifras del acta original (puerta_2024_resultado.json,
SHA comprobado), que se conserva intacta. Cambio único en la decisión de promoción: la salvaguarda de cliente nuevo exige
solo diferencia puntual >= 0; el límite inferior del 95 % se sigue informando como diagnóstico, sin veto.
Promoción secuencial igual que en v1: titular R0; A1 frente a R0; después A2 frente al titular vigente.
Escribe salidas/conf/puerta_2024_acta_enmendada.json.
"""
import hashlib, json, pathlib

R = pathlib.Path('/home/claude/noche'); C = R / 'salidas/conf'
SHA_ACTA = 'b3faaecee9b96b15d3399e7e9f2a3bb99429ddffac2ef780690565f3a449b080'
fa = C / 'puerta_2024_resultado.json'
assert hashlib.sha256(fa.read_bytes()).hexdigest() == SHA_ACTA, 'acta original cambiada'
acta = json.load(open(fa)); pol = json.load(open(R / 'preinscripcion/politica_seleccion_v2_20261024.json'))
pre = json.load(open(R / 'preinscripcion/preinscripcion_puerta_2024.json'))
delta = pre['delta_min']; sg = {a['aspirante']: a for a in acta['actas']}


def pasa_v2(a):
    s = a['salvaguardas']
    cn = s['cliente_nuevo']['diff'] >= pol['cambios']['salvaguarda_cliente_nuevo']['v2']['diferencia_puntual_min']
    esc = all(v['pasa'] for v in s['escenarios'].values()); seg = all(v['pasa'] for v in s['segmentos'].values())
    inf = s['influencia']['pasa']; niv = a['nivel_2025']['condicion_cumplida']
    return {'cliente_nuevo_diferencia_puntual': cn, 'cliente_nuevo_limite95_diagnostico': s['cliente_nuevo']['lower95'],
            'escenarios': esc, 'segmentos': seg, 'influencia': inf, 'nivel_2025': niv, 'pasa_todas': bool(cn and esc and seg and inf and niv)}


titular = 'R0'; pasos = []
# paso 1: A1 frente a R0 (salvaguardas ya medidas en el acta)
p = acta['pares']['A1-R0']; v = pasa_v2(sg['A1'])
prom = p['lower'] > delta and v['pasa_todas']
pasos.append({'aspirante': 'A1', 'titular': 'R0', 'par': p, 'primaria_pasa': p['lower'] > delta, 'salvaguardas_v2': v, 'promueve': prom})
if prom: titular = 'A1'
# paso 2: A2 frente al titular vigente
k = f'A2-{titular}'; p = acta['pares'][k]
paso = {'aspirante': 'A2', 'titular': titular, 'par': p, 'primaria_pasa': p['lower'] > delta}
if titular == 'R0':
    paso['salvaguardas_v2'] = pasa_v2(sg['A2']); paso['promueve'] = paso['primaria_pasa'] and paso['salvaguardas_v2']['pasa_todas']
else:
    paso['salvaguardas_v2'] = 'no se evalúan: la primaria no pasa' if not paso['primaria_pasa'] else 'faltan salvaguardas frente a A1 en el acta'
    paso['promueve'] = False if not paso['primaria_pasa'] else None
pasos.append(paso)
if paso['promueve']: titular = 'A2'
out = {'politica': pol['id'], 'acta_original_sha256': SHA_ACTA, 'titular_v1': acta['titular_final'], 'pasos': pasos, 'titular_v2': titular,
       'reabre_2024': False, 'nuevas_lecturas_de_etiquetas': 0,
       'advertencia': 'Enmienda decidida después de conocer el acta; no restaura una confirmación intacta de 2024.'}
json.dump(out, open(C / 'puerta_2024_acta_enmendada.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
