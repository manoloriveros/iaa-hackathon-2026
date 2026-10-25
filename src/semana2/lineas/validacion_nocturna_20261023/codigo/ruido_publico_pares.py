"""¿Cuánto ruido tiene la diferencia de D² público entre dos envíos muy parecidos?

Sustituto: 2024 (ya abierto), con las dos mezclas a igual nivel por ramo (la enviada primero y la robusta), igual que en
produccion_robusta.py. Se toman 2.000 subconjuntos al azar del tamaño del público de 2025 (un tercio de 209.063 filas,
con reemplazo desde las 59.202 de 2024, porque el público de 2025 es mayor que todo 2024) y se mide la diferencia de D²
en cada uno. Así se ve qué tan probable es ver −0,00043 en el público si la diferencia de fondo es la medida en 2024.
Escribe salidas/robustez/ruido_publico_pares.json.
"""
import io, contextlib, json, pathlib, runpy, sys
import numpy as np, pandas as pd
sys.path.insert(0, str(pathlib.Path(__file__).parent))
import marco as M

R = pathlib.Path('/home/claude/noche')
with contextlib.redirect_stdout(io.StringIO()):
    g = runpy.run_path(str(R / 'codigo/produccion_robusta.py'))
P4 = g['P4']; y = g['y4']; comp = g['comp4']
old, new = P4['mezcla_vieja'], P4['mezcla_nueva']
n_pub = round(209063 / 3)
K = comp.max() + 1; rows_by = pd.Series(np.arange(len(y))).groupby(comp).apply(np.array).values
rng = np.random.default_rng(2026102402); diffs = []
mean_rows = len(y) / K; n_comp = int(round(n_pub / mean_rows))
for _ in range(2000):  # remuestreo por componentes cliente-dirección hasta el tamaño del público 2025
    ii = np.concatenate([rows_by[k] for k in rng.integers(0, K, n_comp)])
    diffs.append(M.d2(y[ii], new[ii]) - M.d2(y[ii], old[ii]))
d = np.array(diffs); full = float(M.d2(y, new) - M.d2(y, old))
out = {'diferencia_2024_completo': round(full, 6), 'filas_publico_2025': n_pub, 'sd_diferencia_publico': round(float(d.std()), 6),
       'p05_p50_p95': [round(float(q), 6) for q in np.quantile(d, [0.05, 0.5, 0.95])],
       'prob_ver_menor_o_igual_a_menos_0_00043': round(float((d <= -0.00043).mean()), 3),
       'diferencia_publica_observada': round(0.15347 - 0.15390, 5)}
json.dump(out, open(R / 'salidas/robustez/ruido_publico_pares.json', 'w'), indent=1, ensure_ascii=False)
print(json.dumps(out, indent=1, ensure_ascii=False))
