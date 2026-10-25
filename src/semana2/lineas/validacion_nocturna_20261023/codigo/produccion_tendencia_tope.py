"""Producciones 2025 con la tendencia estimada sobre siniestros topados a 250.000 CU (regla TEN-N2).

TEN-N2: la tendencia anual por ramo se estima con el índice del desarrollado 2021-2024 (relatividades fijas, e_ef) con
cada siniestro topado a 250.000 CU; el exceso sobre el tope se trata como carga estable y no entra en la tendencia. Motivo:
en autos 2023 un solo siniestro de lesiones de 11,9 M CU (10 % del coste del año) movía la tendencia de +3,5 % a +4,3 %.
Factor = (1 + t)^años, con los años entre el punto medio de la experiencia emergente 2023-2024 y el de 2025
(tendencia_opciones.json). Se aplica a A1fix y A1fixF1 (salidas/correccion). Sin enviar.
"""
import hashlib, json, pathlib
import pandas as pd

R = pathlib.Path('/home/claude/noche'); S = R / 'salidas/correccion'
tt = json.load(open(R / 'salidas/produccion/tendencia_tope.json'))
to = json.load(open(R / 'salidas/produccion/tendencia_opciones.json'))
fac = {k: (1 + tt[l]['tope_250k']['tendencia_21_24']) ** to[l]['anios'] for k, l in (('M', 'motor'), ('B', 'buildings'), ('C', 'contents'))}
info = {'regla': 'TEN-N2', 'factores': {k: round(v, 4) for k, v in fac.items()}, 'factores_exactos': fac,
        'tendencias': {l: tt[l]['tope_250k']['tendencia_21_24'] for l in ('motor', 'buildings', 'contents')},
        'anios': {l: to[l]['anios'] for l in ('motor', 'buildings', 'contents')}}
for base in ('A1fix', 'A1fixF1'):
    d = pd.read_csv(S / f'{base}_2025.csv')
    f = d.row_id.str[0].map(fac); assert f.notna().all()
    d['prediction'] = d.prediction * f
    assert len(d) == 209063 and d.row_id.is_unique and (d.prediction > 0).all()
    p = S / f'{base}Tc_2025.csv'; d.to_csv(p, index=False, float_format='%.6f', lineterminator='\n')
    info[f'{base}Tc'] = {'sha256': hashlib.sha256(p.read_bytes()).hexdigest(), 'total': round(float(d.prediction.sum()), 2),
                         'por_ramo': {k: round(float(d.prediction[d.row_id.str[0] == k].sum()), 2) for k in 'MBC'}}
json.dump(info, open(S / 'produccion_tendencia_tope.json', 'w'), indent=1)
print(json.dumps(info, indent=1))
