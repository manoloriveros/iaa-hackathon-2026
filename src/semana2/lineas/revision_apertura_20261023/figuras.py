"""Figuras de la revision de apertura (lee solo tablas/ y evidencia.json de la misma carpeta)."""
from __future__ import annotations

import json
import pathlib
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib.ticker import NullFormatter, NullLocator

SURF, INK, INK2, MUTED, GRID, BASE = '#fcfcfb', '#0b0b0b', '#52514e', '#898781', '#e1e0d9', '#c3c2b7'
S1, S2, S3 = '#2a78d6', '#eb6834', '#1baf7a'
RAMO = {'motor': ('Autos', S1, 'o'), 'buildings': ('Edificios', S2, 's'), 'contents': ('Contenidos', S3, '^')}
PELIGRO = {'own_damage': 'Daños propios', 'third_party_prop': 'Daños a terceros', 'bodily_injury': 'Lesiones corporales',
           'theft': 'Robo', 'glass_hail': 'Lunas y granizo', 'storm': 'Tormenta', 'flood': 'Inundación',
           'escape_of_water': 'Escape de agua', 'subsidence': 'Hundimiento', 'fire': 'Incendio',
           'accidental_damage': 'Daños accidentales'}

plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5, 'axes.edgecolor': BASE, 'axes.labelcolor': INK2,
                     'xtick.color': MUTED, 'ytick.color': INK2, 'axes.titlecolor': INK, 'figure.facecolor': SURF,
                     'axes.facecolor': SURF, 'savefig.facecolor': SURF, 'axes.spines.top': False,
                     'axes.spines.right': False, 'axes.grid': True, 'grid.color': GRID, 'grid.linewidth': 0.6,
                     'legend.frameon': False})


def ratio_axis(ax, lo, hi):
    ax.set_xscale('log')
    ticks = [t for t in [0.25, 0.4, 0.5, 0.6, 0.8, 1, 1.25, 1.5, 2, 2.5, 3] if lo <= t <= hi]
    ax.set_xticks(ticks)
    ax.set_xticklabels([f'{t:g}'.replace('.', ',') for t in ticks])
    ax.set_xlim(lo, hi)
    ax.xaxis.set_minor_locator(NullLocator()); ax.xaxis.set_minor_formatter(NullFormatter())
    ax.axvline(1, color=BASE, lw=1.2, zorder=1)


def fig1(folder: pathlib.Path):
    r = pd.read_csv(folder / 'tablas' / 'razones_peligro.csv')
    r = r[r.anio == 2023].copy()
    orden = {'motor': 0, 'buildings': 1, 'contents': 2}
    r['o'] = r.ramo.map(orden)
    r = r.sort_values(['o', 'razon_frecuencia'], ascending=[False, True]).reset_index(drop=True)
    fig, ax = plt.subplots(figsize=(9.2, 6.4))
    y = np.arange(len(r))
    for i, row in r.iterrows():
        ax.plot([row.razon_frecuencia, row.razon_severidad], [i, i], color=GRID, lw=2, zorder=2)
    ax.scatter(r.razon_frecuencia, y, s=58, color=S1, zorder=3, label='Frecuencia emergente / desarrollada',
               edgecolor=SURF, linewidth=1.5)
    ax.scatter(r.razon_severidad, y, s=58, color=S2, marker='s', zorder=3, label='Severidad emergente / desarrollada',
               edgecolor=SURF, linewidth=1.5)
    labels = [f"{RAMO[a][0]} · {PELIGRO[b]}  ({int(n)})" for a, b, n in zip(r.ramo, r.peligro, r.siniestros_emergente)]
    ax.set_yticks(y)
    ax.set_yticklabels(labels)
    ax.grid(axis='y', visible=False)
    ratio_axis(ax, 0.35, 3.0)
    for i, row in r.iterrows():
        if row.peligro in ('fire', 'glass_hail', 'bodily_injury', 'escape_of_water') and row.ramo != 'contents':
            ax.annotate(f'{row.razon_frecuencia:.2f}'.replace('.', ','), (row.razon_frecuencia, i), xytext=(7, -3),
                        textcoords='offset points', color=INK2, fontsize=8.5)
            ax.annotate(f'{row.razon_severidad:.2f}'.replace('.', ','), (row.razon_severidad, i), xytext=(-27, -3),
                        textcoords='offset points', color=INK2, fontsize=8.5)
    ax.set_xlabel('Razón emergente / desarrollado (escala logarítmica; 1 = igual)')
    fig.text(0.01, 0.975, 'Qué cambia por peligro: ocurrencias de 2023 valoradas al 31-12-2024 en los dos mercados',
             fontsize=11.5, color=INK, va='top')
    fig.text(0.01, 0.94, 'Entre paréntesis, siniestros aceptados del emergente. Exposición en días/365; '
             'el desarrollado excluye las 604 copias DUP01.', fontsize=8.5, color=INK2, va='top')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, 1.07), ncol=2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(folder / 'fig1_peligros_mercados.png', dpi=160)
    plt.close(fig)


def fig2(folder: pathlib.Path):
    d = pd.read_csv(folder / 'tablas' / 'relatividades_oneway.csv')
    pv = d.pivot_table(index=['ramo', 'factor', 'nivel'], columns='mercado', values=['relatividad', 'siniestros']).dropna()
    pv.columns = [f'{a}_{b}' for a, b in pv.columns]
    pv = pv.reset_index()
    pv = pv[pv.siniestros_emerging >= 100]
    k = pd.read_csv(folder / 'tablas' / 'retrasos_ks_2023.csv')
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.4, 5.0))
    for l, (name, col, mk) in RAMO.items():
        s = pv[pv.ramo == l]
        a1.scatter(s.relatividad_developed, s.relatividad_emerging, s=46, color=col, marker=mk, label=name,
                   edgecolor=SURF, linewidth=1.2, zorder=3)
        t = k[k.ramo == l]
        a2.scatter(t.mediana_desarrollado, t.mediana_emergente, s=52, color=col, marker=mk, label=name,
                   edgecolor=SURF, linewidth=1.2, zorder=3)
    lim = (0.4, 2.8)
    a1.plot(lim, lim, color=BASE, lw=1.2, zorder=1)
    a1.set_xscale('log'); a1.set_yscale('log')
    ticks = [0.5, 0.7, 1, 1.4, 2, 2.5]
    for f in (a1.set_xticks, a1.set_yticks):
        f(ticks)
    a1.set_xticklabels([f'{t:g}'.replace('.', ',') for t in ticks]); a1.set_yticklabels([f'{t:g}'.replace('.', ',') for t in ticks])
    a1.set_xlim(lim); a1.set_ylim(lim)
    for ax_ in (a1.xaxis, a1.yaxis):
        ax_.set_minor_locator(NullLocator()); ax_.set_minor_formatter(NullFormatter())
    for _, row in pv[pv.factor == 'ncb_g'].iterrows():
        if row.nivel in ('0', '1-2'):
            off, ha = ((-8, 8), 'right') if row.nivel == '0' else ((8, -13), 'left')
            a1.annotate(f'NCB {row.nivel}', (row.relatividad_developed, row.relatividad_emerging), xytext=off,
                        textcoords='offset points', color=INK2, fontsize=8.5, ha=ha)
    a1.set_xlabel('Relatividad de frecuencia en el desarrollado')
    a1.set_ylabel('Relatividad de frecuencia en el emergente')
    a1.set_title('Relatividades one-way, 2023-2024\n(niveles con 100 o más siniestros emergentes)', loc='left', fontsize=10)
    a1.legend(loc='upper left', fontsize=8.5)
    lim2 = (2.5, 200)
    a2.plot(lim2, lim2, color=BASE, lw=1.2, zorder=1)
    a2.set_xscale('log'); a2.set_yscale('log')
    t2 = [3, 5, 10, 20, 50, 100, 200]
    a2.set_xticks(t2); a2.set_yticks(t2)
    a2.set_xticklabels([str(t) for t in t2]); a2.set_yticklabels([str(t) for t in t2])
    a2.set_xlim(lim2); a2.set_ylim(lim2)
    for ax_ in (a2.xaxis, a2.yaxis):
        ax_.set_minor_locator(NullLocator()); ax_.set_minor_formatter(NullFormatter())
    for _, row in k.iterrows():
        if row.peligro in ('bodily_injury', 'subsidence'):
            a2.annotate(PELIGRO[row.peligro], (row.mediana_desarrollado, row.mediana_emergente), xytext=(-8, 9),
                        textcoords='offset points', color=INK2, fontsize=8.5, ha='right')
    a2.set_xlabel('Mediana de días hasta el reporte, desarrollado')
    a2.set_ylabel('Mediana de días hasta el reporte, emergente')
    a2.set_title(f'Retraso de reporte por peligro, ocurrencias 2023\n(KS: p mínimo {k.p_valor.min():.2f} en {len(k)} peligros)'.replace('.', ','),
                 loc='left', fontsize=10)
    fig.suptitle('Lo que se puede trasladar: la forma de las tarifas y el patrón de reporte', x=0.01, ha='left',
                 fontsize=11.5, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    fig.savefig(folder / 'fig2_lo_que_se_traslada.png', dpi=160)
    plt.close(fig)


def fig3(folder: pathlib.Path):
    ev = json.loads((folder / 'evidencia.json').read_text(encoding='utf-8'))
    nb = ev['nuevo_negocio']
    fig, (a0, a1) = plt.subplots(1, 2, figsize=(10.4, 4.6), gridspec_kw={'width_ratios': [1, 1.35]})
    years = ['2023', '2024', '2025']
    w = 0.26
    for j, (l, (name, col, mk)) in enumerate(RAMO.items()):
        vals = [nb[l]['cuota_nb_filas'][y] * 100 for y in years]
        xs = np.arange(3) + (j - 1) * (w + 0.02)
        a0.bar(xs, vals, width=w, color=col, label=name, zorder=3)
    for i, y in enumerate(years):
        v = np.mean([nb[l]['cuota_nb_filas'][y] * 100 for l in RAMO])
        a0.annotate(f'{v:.0f} %', (i, v), xytext=(0, 4), textcoords='offset points', ha='center', color=INK2, fontsize=9)
    a0.set_xticks(range(3)); a0.set_xticklabels(['2023', '2024', '2025 (test)'])
    a0.set_ylim(0, 100); a0.set_ylabel('Filas de nuevo negocio (%)')
    a0.grid(axis='x', visible=False)
    a0.set_title('El test de 2025 es sobre todo cartera nueva\n(88-91 % empieza en enero: cartera de un broker)', loc='left', fontsize=10)
    a0.legend(loc='upper left', fontsize=8.5)
    sh24 = np.mean([nb[l]['cuota_nb_exposicion_2024'] for l in RAMO])
    sh25 = np.mean([nb[l]['cuota_nb_exposicion_2025'] for l in RAMO])
    rr = np.linspace(0.7, 1.6, 100)
    a1.plot(rr, ((1 - sh25) + sh25 * rr) / ((1 - sh24) + sh24 * rr), color=MUTED, lw=2, zorder=2)
    a1.axhline(1, color=BASE, lw=1); a1.axvline(1, color=BASE, lw=1)
    for l, (name, col, mk) in RAMO.items():
        for src, fill in (('emerging', col), ('developed', SURF)):
            rel = nb[l][f'rel_nb_{src}']['frecuencia']
            eff = ((1 - nb[l]['cuota_nb_exposicion_2025']) + nb[l]['cuota_nb_exposicion_2025'] * rel) / \
                  ((1 - nb[l]['cuota_nb_exposicion_2024']) + nb[l]['cuota_nb_exposicion_2024'] * rel)
            a1.scatter([rel], [eff], s=64, marker=mk, color=fill, edgecolor=col, linewidth=1.8, zorder=4)
            n = nb[l][f'rel_nb_{src}']['siniestros_nb']
            pos = {('motor', 'emerging'): ((9, -4), 'left'), ('motor', 'developed'): ((9, 3), 'left'),
                   ('contents', 'emerging'): ((-9, 6), 'right'), ('contents', 'developed'): ((-9, -1), 'right'),
                   ('buildings', 'emerging'): ((9, -4), 'left'), ('buildings', 'developed'): ((-9, -1), 'right')}
            off, ha = pos[(l, src)]
            a1.annotate(f"{name} {'em.' if src == 'emerging' else 'des.'} ({n})", (rel, eff), xytext=off,
                        textcoords='offset points', ha=ha, color=INK2, fontsize=8)
    a1.set_xlabel('Relatividad de frecuencia del nuevo negocio (bruta, 2023-2024)')
    a1.set_ylabel('Frecuencia media 2025 / mezcla de 2024')
    a1.set_title('Cuánto mueve esa relatividad el nivel de 2025\n(relleno: emergente; hueco: desarrollado; entre paréntesis, siniestros NB)',
                 loc='left', fontsize=10)
    yt = [0.8, 0.9, 1.0, 1.1, 1.2, 1.3, 1.4]
    a1.set_yticks(yt); a1.set_yticklabels([f'{t:.1f}'.replace('.', ',') for t in yt])
    xt = [0.8, 1.0, 1.2, 1.4, 1.6]
    a1.set_xticks(xt); a1.set_xticklabels([f'{t:.1f}'.replace('.', ',') for t in xt])
    fig.suptitle(f'Nuevo negocio: {sh24*100:.0f} % de la exposición en 2024 y {sh25*100:.0f} % en 2025'.replace('.', ','),
                 x=0.01, ha='left', fontsize=11.5, color=INK)
    fig.tight_layout(rect=(0, 0, 1, 0.94))
    fig.savefig(folder / 'fig3_nuevo_negocio_nivel.png', dpi=160)
    plt.close(fig)


if __name__ == '__main__':
    folder = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else pathlib.Path(__file__).resolve().parent
    fig1(folder)
    fig2(folder)
    fig3(folder)
    print('ok')
