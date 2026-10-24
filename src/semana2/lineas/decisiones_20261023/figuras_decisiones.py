"""Figuras de las decisiones de semana 2 (Claude, 23-10-2026). Lee evidencia_decisiones.json y la tabla de capital."""
from __future__ import annotations

import json
import pathlib

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
from matplotlib.ticker import NullFormatter, NullLocator

S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
GRIS, TINTA, TINTA2, REJILLA = '#9aa0a6', '#1f2328', '#57606a', '#e6e8eb'
RAMO = {'motor': 'Autos', 'buildings': 'Edificios', 'contents': 'Contenidos'}
PELIGRO = {'storm': 'tormenta', 'fire': 'incendio', 'flood': 'inundación', 'escape_of_water': 'escape de agua'}


def coma(x, d=2):
    return f'{x:.{d}f}'.replace('.', ',')
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5, 'axes.edgecolor': '#c9ced4', 'axes.labelcolor': TINTA2,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.grid': True, 'grid.color': REJILLA,
                     'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.spines.top': False, 'axes.spines.right': False,
                     'legend.frameon': False, 'savefig.dpi': 160})


def titulo(fig, t, s):
    fig.text(0.01, 0.985, t, ha='left', va='top', fontsize=12, color=TINTA, weight='bold')
    fig.text(0.01, 0.935, s, ha='left', va='top', fontsize=9.5, color=TINTA2)


def fig_capital(out, privado, E):
    cap = pq.read_table(privado / 'capital_caps2_01.parquet').to_pandas()
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.6))
    rng = np.random.default_rng(20261023)
    ev = json.loads((out / 'evidencia_decisiones.json').read_text(encoding='utf-8'))['capital']
    for ax, l in zip(axs, ['buildings', 'contents']):
        t = pd.concat([E.pol[l], E.test[l]], ignore_index=True)
        nor = t[t.sum_insured <= ev[l]['umbral']]
        idx = rng.choice(len(nor), size=min(4000, len(nor)), replace=False)
        nor = nor.iloc[idx]
        ax.scatter(nor.sum_insured, 1000 * nor.written_premium / nor.sum_insured, s=4, color=GRIS, alpha=0.35, lw=0,
                   label='Capital normal (muestra)')
        c = cap[cap.line == l]
        ax.scatter(c.sum_insured_raw, c.ppm_raw, s=9, color=S2, lw=0, label='Escala dudosa, capital leído')
        ax.scatter(c.sum_insured_model, c.ppm_model, s=9, color=S1, lw=0, label='Las mismas filas, capital entre mil')
        ax.axhspan(ev[l]['ppm_normal_min'], ev[l]['ppm_normal_max'], color=S1, alpha=0.06, lw=0)
        ax.axvline(ev[l]['umbral'], color=TINTA2, lw=0.8, ls='--')
        ax.text(ev[l]['umbral'] * 1.15, 0.05, f"umbral\n{ev[l]['umbral'] / 1e6:.0f} M CU", fontsize=8, color=TINTA2, va='center')
        ax.set_xscale('log')
        ax.set_yscale('log')
        for a in (ax.xaxis, ax.yaxis):
            a.set_minor_locator(NullLocator())
            a.set_minor_formatter(NullFormatter())
        ax.set_xlabel('Capital asegurado (CU, escala log)')
        ax.set_ylabel('Prima escrita por mil de capital (escala log)')
        ax.set_title(f"{RAMO[l]}: {ev[l]['pasan']} filas divididas, {ev[l]['no_pasan']} fuera", loc='left', fontsize=10, color=TINTA)
    axs[0].legend(loc='lower left', fontsize=8, markerscale=1.8)
    titulo(fig, 'CAPS2-01: el capital entre mil devuelve la prima por mil a la nube normal',
           'Cada fila por encima del umbral queda debajo del mínimo normal con el capital leído y dentro del rango normal (franja azul) al dividirlo.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig1_capital.png')
    plt.close(fig)


def fig_clima(out, ev):
    c = ev['clima']
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), gridspec_kw=dict(width_ratios=[1, 1.15]))
    ax = axs[0]
    vs = list(c['persistencia'].keys())
    nombres = {'hail_days': 'Días de granizo', 'wind_exposure_index': 'Exposición al viento', 'freezing_days': 'Días de helada',
               'dry_summer_index': 'Sequía estival', 'wildfire_index': 'Índice forestal', 'rainfall_mm': 'Lluvia anual',
               'mean_temperature_c': 'Temperatura media'}
    orden = sorted(vs, key=lambda v: min(c['persistencia'][v]['r_2023_2024'], c['persistencia'][v]['r_2024_2025']))
    y = np.arange(len(orden))
    a = [c['persistencia'][v]['r_2023_2024'] for v in orden]
    b = [c['persistencia'][v]['r_2024_2025'] for v in orden]
    ax.scatter(a, y, color=S1, s=26, zorder=3, label='2023 → 2024')
    ax.scatter(b, y, color=S2, s=26, zorder=3, label='2024 → 2025')
    for yi, ai, bi in zip(y, a, b):
        ax.plot([ai, bi], [yi, yi], color=GRIS, lw=1, zorder=2)
    ax.axvline(c['umbral'], color=TINTA2, lw=0.8, ls='--')
    ax.text(c['umbral'] - 0.02, -0.6, 'umbral 0,80', fontsize=8, color=TINTA2, ha='right', va='center')
    ax.set_yticks(y)
    ax.set_yticklabels([nombres[v] + (' ✓' if c['persistencia'][v]['persistente'] else '') for v in orden])
    ax.set_xlim(-0.35, 1.0)
    ax.set_ylim(-1.0, len(orden) - 0.5)
    ax.set_xlabel('Correlación entre direcciones de un año al siguiente')
    ax.set_title('Qué variables se repiten de un año a otro', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='upper left', fontsize=8)
    ax = axs[1]
    comp = [r for r in c['comprobacion'] if r['mercado'] == 'developed']
    et = [f"{RAMO[r['ramo']]}: {PELIGRO[r['peligro']]}\n({nombres[r['variable']].lower()})" for r in comp]
    y = np.arange(len(comp))
    ax.scatter([r['razon_alto_bajo_propio'] for r in comp], y + 0.12, color=S2, s=26, zorder=3, label='Clima del propio año')
    ax.scatter([r['razon_alto_bajo_bloque'] for r in comp], y - 0.12, color=S1, s=26, zorder=3, label='Clima de los otros años (bloque)')
    ax.axvline(1, color=TINTA2, lw=0.8)
    ax.set_xscale('log')
    ax.xaxis.set_minor_locator(NullLocator())
    ax.xaxis.set_minor_formatter(NullFormatter())
    ax.set_xticks([0.8, 1, 1.5, 2, 3])
    ax.set_xticklabels(['0,8', '1', '1,5', '2', '3'])
    ax.set_yticks(y)
    ax.set_yticklabels(et, fontsize=8)
    ax.set_xlabel('Frecuencia tercil alto / tercil bajo, desarrollado 2021-2023')
    ax.set_title('El bloque conserva el gradiente del clima del año', loc='left', fontsize=10, color=TINTA)
    ax.legend(loc='upper right', fontsize=8)
    titulo(fig, 'CLIMA-S2-01: solo entran viento, índice forestal y lluvia, medidos en otro año',
           'Las variables persistentes se comportan como un atributo de la dirección; granizo, sequía, heladas y temperatura cambian demasiado.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig2_clima.png')
    plt.close(fig)


def fig_nb(out, ev):
    cr = ev['nuevo_negocio']['credibilidad']['principal']
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
    for ax, comp, nombre, tau in [(axs[0], 'f', 'Frecuencia', cr['tau_f']), (axs[1], 's', 'Severidad', cr['tau_s'])]:
        for i, l in enumerate(['motor', 'buildings', 'contents']):
            x = cr['ramos'][l]
            for dx, k, col, lab in [(-0.18, 'em', S2, 'Emergente 2023'), (0.0, 'dev', S1, 'Desarrollado 2021-2023')]:
                th, se = x[f'theta_{comp}_{k}'], x[f'se_{comp}_{k}']
                ax.errorbar(i + dx, np.exp(th), yerr=[[np.exp(th) - np.exp(th - 1.96 * se)], [np.exp(th + 1.96 * se) - np.exp(th)]],
                            fmt='o', color=col, ms=5, lw=1.2, capsize=3, label=lab if i == 0 else None)
            z = x[f'Z_{comp}']
            thc = z * x[f'theta_{comp}_em'] + (1 - z) * x[f'theta_{comp}_dev']
            ax.plot(i + 0.18, np.exp(thc), marker='D', color=S3, ms=6, ls='none', label='Creíble' if i == 0 else None)
            ax.text(i + 0.25, np.exp(thc), f'Z = {coma(z)}', fontsize=8, color=TINTA2, va='center')
        ax.axhline(1, color=TINTA2, lw=0.8)
        ax.set_yscale('log')
        ax.yaxis.set_minor_locator(NullLocator())
        ax.yaxis.set_minor_formatter(NullFormatter())
        ax.set_yticks([0.6, 0.8, 1, 1.25, 1.5, 2])
        ax.set_yticklabels(['0,6', '0,8', '1', '1,25', '1,5', '2'])
        ax.set_xticks(range(3))
        ax.set_xticklabels([RAMO[l] for l in ['motor', 'buildings', 'contents']])
        ax.set_xlim(-0.5, 2.7)
        ax.set_title(f'{nombre}: τ = {coma(tau, 3)}', loc='left', fontsize=10, color=TINTA)
    axs[0].set_ylabel('Nuevo negocio / renovación, neto de covariables')
    axs[0].legend(loc='lower left', fontsize=8)
    titulo(fig, 'NB-CRED-01: el nivel del nuevo negocio se apoya sobre todo en el desarrollado',
           'Intervalos del 95 % con errores robustos por cliente. En la severidad τ es cero: la de autos emergente la explican cinco siniestros.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig3_nuevo_negocio.png')
    plt.close(fig)


def fig_diagnostico(out, ev):
    d = ev['diagnostico_oof']['recetas']
    recetas = ['W2-B00', 'W2-B03', 'W2-B05', 'W2-B06', 'W2-B07', 'W2-B08', 'W2-B09']
    fig, axs = plt.subplots(1, 2, figsize=(10.5, 4.4), sharey=True)
    for ax, sufijo, nombre in [(axs[0], '', 'Todas las filas de 2023'), (axs[1], '_sin_01', 'Sin el 0,1 % de filas con mayor coste')]:
        y = np.arange(len(recetas))
        for dy, v, col, lab in [(0.18, 'guardada', GRIS, 'Receta guardada'), (0.0, 'emergente', S2, 'Nivel NB solo emergente (Z = 1)'),
                                (-0.18, 'credibilidad', S3, 'Nivel NB creíble')]:
            ax.scatter([d[r][v][f'D2_mezcla_2025{sufijo}'] for r in recetas], y + dy, color=col, s=24, zorder=3, label=lab)
        ax.set_yticks(y)
        ax.set_yticklabels(recetas)
        ax.invert_yaxis()
        ax.set_xlabel('D² con la mezcla de 2025 (nuevo negocio al 77 %)')
        ax.set_title(nombre, loc='left', fontsize=10, color=TINTA)
    axs[0].legend(loc='lower left', fontsize=8)
    titulo(fig, 'Diagnóstico en los OOF de 2023: corregir el nivel del nuevo negocio pesa más que cualquier receta',
           'Con todas las filas gana el nivel solo emergente en las recetas que no distinguen el nuevo negocio; sin las 51 filas más caras gana el creíble.')
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    fig.savefig(out / 'fig4_diagnostico_2023.png')
    plt.close(fig)


def fig_gasto(out, ev):
    t = pd.DataFrame(ev['gasto_fijo']['referencias']).sort_values('exposure').reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.2))
    y = np.arange(len(t))
    ax.scatter(t.F_entero_por_fila_termino_F, y, color=S2, s=24, zorder=3, label='F entero en cada fila')
    ax.scatter(t.F_por_poliza_y_anio_termino_F, y, color=GRIS, s=18, zorder=3, marker='s', label='F entero por póliza y año')
    ax.scatter(t.F_por_exposicion_termino_F, y, color=S1, s=24, zorder=4, label='F × exposición (decisión)')
    for yi, (_, r) in zip(y, t.iterrows()):
        ax.plot([r.F_por_exposicion_termino_F, r.F_entero_por_fila_termino_F], [yi, yi], color=REJILLA, lw=1.5, zorder=1)
    ax.set_yticks(y)
    ax.set_yticklabels([f"{r.row_id}  ({RAMO[r.line].lower()}, {r.channel}, e = {coma(r.exposure)})" for _, r in t.iterrows()], fontsize=8)
    ax.set_xlabel('Parte de la prima comercial que paga el gasto fijo: F / (1 - v - c - t - m), en CU')
    ax.legend(loc='center left', bbox_to_anchor=(0.02, 0.55), fontsize=8)
    titulo(fig, 'GASTO-F-01: con F × exposición las referencias de año casi completo apenas cambian',
           'Las diferencias se concentran en tres filas: dos tramos de pólizas con otra fila en 2025 y una póliza nueva de cuatro meses.')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(out / 'fig5_gasto_fijo.png')
    plt.close(fig)


def dibujar(out: pathlib.Path, privado: pathlib.Path, E):
    ev = json.loads((out / 'evidencia_decisiones.json').read_text(encoding='utf-8'))
    fig_capital(out, privado, E)
    fig_clima(out, ev)
    fig_nb(out, ev)
    fig_diagnostico(out, ev)
    fig_gasto(out, ev)
