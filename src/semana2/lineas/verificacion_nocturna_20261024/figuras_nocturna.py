"""Figuras de la verificación de la tanda nocturna (Claude, 24-10-2026). Lee evidencia_nocturna.json y tablas/*.csv de la misma carpeta."""
from __future__ import annotations

import json
import pathlib

import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

AQUI = pathlib.Path(__file__).resolve().parent
S1, S2, S3, S4 = '#2a78d6', '#eb6834', '#1baf7a', '#8e6cc6'
GRIS, TINTA, TINTA2, REJILLA = '#9aa0a6', '#1f2328', '#57606a', '#e6e8eb'
RAMO = {'motor': 'Autos', 'buildings': 'Edificios', 'contents': 'Contenidos'}
plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9.5, 'axes.edgecolor': '#c9ced4', 'axes.labelcolor': TINTA2,
                     'xtick.color': TINTA2, 'ytick.color': TINTA2, 'axes.grid': True, 'grid.color': REJILLA,
                     'grid.linewidth': 0.6, 'axes.axisbelow': True, 'axes.spines.top': False, 'axes.spines.right': False,
                     'legend.frameon': False, 'savefig.dpi': 160})


def titulo(fig, t, s):
    fig.text(0.01, 0.985, t, ha='left', va='top', fontsize=12, color=TINTA, weight='bold')
    fig.text(0.01, 0.935, s, ha='left', va='top', fontsize=9.5, color=TINTA2)


def fig1_concordancia(ev):
    """Recalculado frente a publicado: D² global y de nuevo negocio de las recetas del foro, y las deltas de los pares."""
    f = ev['detalle']['VN04']['frente_al_foro']
    pares = ev['detalle']['VN10']
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.6))
    ax = axes[0]
    pts = []
    for k, v in f.items():
        if 'coincide' in v and isinstance(v.get('publicado'), dict) and 'D2' in v['publicado']:
            pts.append((v['publicado']['D2'], v['recalculado']['D2'], 'D² global'))
            if 'D2_nb' in v['publicado']:
                pts.append((v['publicado']['D2_nb'], v['recalculado']['D2_nb'], 'D² nuevo negocio'))
            if 'D2_mnb' in v['publicado']:
                pts.append((v['publicado']['D2_mnb'], v['recalculado']['D2_mnb'], 'D² autos nuevos'))
    df = pd.DataFrame(pts, columns=['publicado', 'recalculado', 'tipo'])
    for tipo, col in [('D² global', S1), ('D² nuevo negocio', S2), ('D² autos nuevos', S3)]:
        d = df[df.tipo == tipo]
        ax.scatter(d.publicado, d.recalculado, s=34, color=col, label=f'{tipo} ({len(d)})', zorder=3, edgecolor='white', linewidth=0.8)
    lim = (min(df.publicado.min(), df.recalculado.min()) - 0.01, max(df.publicado.max(), df.recalculado.max()) + 0.01)
    ax.plot(lim, lim, color=GRIS, linewidth=1, zorder=1)
    ax.set_xlim(lim); ax.set_ylim(lim)
    ax.set_xlabel('publicado en el foro (017, 019, 021)'); ax.set_ylabel('recalculado desde los OOF congelados')
    ax.legend(loc='upper left', fontsize=8.5)
    ax.set_title(f'{len(df)} valores de D²: todos sobre la diagonal', fontsize=10, color=TINTA, loc='left')
    ax = axes[1]
    filas = []
    for k in ['dev5', 'dev6', 'dev7']:
        for nombre, v in pares[k]['pares'].items():
            filas.append((nombre.replace('W2-', ''), v['recalculado']['delta_D2'], v['recalculado']['inferior95'], v['recalculado']['superior95'], v['recalculado']['delta_tras_retirar'], v['publicado'][0]))
    y = np.arange(len(filas))
    for i, (nombre, d, lo, hi, tr, pub) in enumerate(filas):
        ax.plot([lo, hi], [i, i], color=S1, linewidth=2, solid_capstyle='round', zorder=2)
        ax.scatter([d], [i], color=S1, s=36, zorder=4, edgecolor='white', linewidth=0.8)
        ax.scatter([tr], [i], color=S2, s=36, marker='D', zorder=4, edgecolor='white', linewidth=0.8)
    ax.axvline(0, color=GRIS, linewidth=1)
    ax.set_yticks(y); ax.set_yticklabels([f[0] for f in filas], fontsize=8.5)
    ax.invert_yaxis()
    ax.set_xlabel('delta D² (candidato frente a referencia)')
    ax.scatter([], [], color=S1, s=36, label='delta e intervalo exploratorio 95 %'); ax.scatter([], [], color=S2, marker='D', s=36, label='delta tras retirar 31 grupos')
    ax.legend(loc='lower right', fontsize=8.5)
    ax.set_title('Once pares: replicados con la misma semilla', fontsize=10, color=TINTA, loc='left')
    titulo(fig, 'Lo que Codex publicó se recalcula desde sus OOF congelados', 'Izquierda: D² de las tablas del foro. Derecha: delta D², intervalo por remuestreo de 2.000 componentes y delta tras retirar 31 grupos favorables.')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(AQUI / 'fig1_concordancia.png'); plt.close(fig)


def fig2_credibilidad(ev):
    d = ev['detalle']['VN14']
    fig, axes = plt.subplots(1, 3, figsize=(10.5, 4.3), sharey=False)
    for ax, l in zip(axes, ['motor', 'buildings', 'contents']):
        x = np.arange(5)
        ax.plot(x, d[l]['rel_em_por_fold'], color=S2, marker='o', linewidth=2, label='relatividad emergente (solo 2023, fold de ajuste)')
        ax.plot(x, d[l]['rel_cred_por_fold'], color=S1, marker='o', linewidth=2, label='relatividad creíble')
        ax.plot(x, d[l]['c_por_fold'], color=S4, marker='s', linewidth=2, label='c = creíble / emergente')
        ax.axhline(d[l]['c_claude_todo_2023'], color=S4, linestyle='--', linewidth=1.2, label='c de Claude con todo 2023')
        ax.axhline(1, color=GRIS, linewidth=0.8)
        nb = d['nuevo_negocio_2023'][l]
        ax.set_title(f"{RAMO[l]}: {nb['filas_con_coste']} siniestros NB en 2023", fontsize=10, color=TINTA, loc='left')
        ax.set_xticks(x); ax.set_xticklabels([f'fold {i}' for i in x]); ax.set_ylim(0.5, 1.8)
        if l == 'motor':
            ax.set_ylabel('relatividad nuevo negocio / renovación')
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, loc='lower center', ncol=4, fontsize=8.5, bbox_to_anchor=(0.5, 0.0))
    titulo(fig, 'La relatividad creíble es estable; el factor c oscila con el fold en hogar', 'Valores de dev6 (report.json de Codex; c comprobado en el OOF). El desarrollado fija el nivel creíble; el emergente de cada fold depende de pocos siniestros.')
    fig.tight_layout(rect=(0, 0.08, 1, 0.9))
    fig.savefig(AQUI / 'fig2_credibilidad.png'); plt.close(fig)


def fig3_folds(ev):
    d = ev['detalle']['VN15']
    modelos = ['W2-B00', 'W2-B12', 'W2-B13', 'W2-B08', 'W2-B14', 'W2-B15', 'W2-B16', 'W2-B17', 'W2-B18']
    fig, ax = plt.subplots(figsize=(10.5, 4.6))
    x = np.arange(5)
    colores = {'W2-B00': GRIS, 'W2-B12': S3, 'W2-B13': S1, 'W2-B08': S2, 'W2-B14': S1, 'W2-B15': S4, 'W2-B16': S4, 'W2-B17': S4, 'W2-B18': S4}
    estilos = {'W2-B14': '--', 'W2-B16': ':', 'W2-B17': '-.', 'W2-B18': (0, (1, 1))}
    for mo in modelos:
        y = [d[mo][f'fold{f}']['D2'] for f in x]
        ax.plot(x, y, color=colores[mo], linestyle=estilos.get(mo, '-'), marker='o', markersize=4, linewidth=1.8 if mo in ('W2-B00', 'W2-B13', 'W2-B08') else 1.2, label=mo.replace('W2-', ''))
    ax.set_xticks(x); ax.set_xticklabels([f'fold {i}' for i in x]); ax.set_ylabel('D² Tweedie 1,5 en el fold evaluado')
    ax.legend(ncol=5, fontsize=8.5, loc='lower center')
    titulo(fig, 'El D² cambia más de un fold a otro que de una receta a otra', f"B13 supera a B00 en {d['B13_supera_a_B00_en_folds']} de 5 folds y B08 supera a B13 en {d['B08_supera_a_B13_en_folds']} de 5; por eso los intervalos exploratorios cruzan cero.")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(AQUI / 'fig3_folds.png'); plt.close(fig)


def fig4_b19_b20(ev):
    """B19 y B20 frente a B14: pares con intervalo, nivel (A/E por ramo) y razones de cobertura por fold."""
    pares = ev['detalle']['VN24']['pares']; nivel = ev['detalle']['VN23']['nivel']; rz = {l: ev['detalle']['VN25']['ramos'][l]['razones'] for l in ['motor', 'buildings', 'contents']}
    fig, axes = plt.subplots(1, 3, figsize=(13, 5), gridspec_kw=dict(width_ratios=[1.25, 1, 1.1]))
    ax = axes[0]
    orden = ['W2-B19 / W2-B14', 'W2-B19 / W2-B00', 'W2-B20 / W2-B19', 'W2-B20 / W2-B14', 'W2-B20 / W2-B00']
    for i, k in enumerate(orden):
        r = pares[k]['recalculado']
        ax.plot([r['inferior95'], r['superior95']], [i, i], color=S1, linewidth=2, solid_capstyle='round', zorder=2)
        ax.scatter([r['delta_D2']], [i], color=S1, s=40, zorder=4, edgecolor='white', linewidth=0.8)
        ax.scatter([r['delta_tras_retirar']], [i], color=S2, s=40, marker='D', zorder=4, edgecolor='white', linewidth=0.8)
    ax.axvline(0, color=GRIS, linewidth=1)
    ax.set_yticks(range(len(orden))); ax.set_yticklabels([k.replace('W2-', '') for k in orden], fontsize=8.5); ax.invert_yaxis()
    ax.set_xlabel('delta D² (candidato frente a referencia)')
    ax.scatter([], [], color=S1, s=40, label='delta e intervalo exploratorio 95 %'); ax.scatter([], [], color=S2, marker='D', s=40, label='tras retirar 31 grupos favorables')
    ax.legend(loc='upper center', bbox_to_anchor=(0.5, -0.16), fontsize=8, ncol=1); ax.set_title('Cinco pares nuevos: se invierten o cruzan cero', fontsize=10, color=TINTA, loc='left')
    ax = axes[1]
    modelos = ['W2-B14', 'W2-B19', 'W2-B20']; col = {'W2-B14': GRIS, 'W2-B19': S1, 'W2-B20': S2}
    x = np.arange(4); anch = 0.26
    for j, mo in enumerate(modelos):
        vals = [nivel[mo]['AE']] + [nivel[mo]['AE_por_ramo'][l] for l in ['motor', 'buildings', 'contents']]
        ax.bar(x + (j - 1) * anch, vals, width=anch - 0.03, color=col[mo], label=mo.replace('W2-', ''), zorder=3)
    ax.axhline(1, color=TINTA2, linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels(['Global', 'Autos', 'Edificios', 'Contenidos'], fontsize=8.5); ax.set_ylim(0.9, 1.06); ax.set_ylabel('A/E = observado / predicho (OOF 2023)')
    ax.legend(fontsize=8.5, loc='upper left'); ax.set_title(f"Nivel: B20 predice {abs(nivel['W2-B20']['nominal_pct_vs_B14']) * 100:.1f} % menos que B14".replace('.', ','), fontsize=10, color=TINTA, loc='left')
    ax = axes[2]
    xf = np.arange(5)
    ax.plot(xf, rz['buildings']['AD'], color=S1, marker='o', linewidth=1.8, label='Edificios AD sí/no, B19')
    ax.plot(xf, rz['buildings']['AD_B20'], color=S1, marker='o', linewidth=1.2, linestyle='--', label='Edificios AD sí/no, B20')
    ax.plot(xf, rz['motor']['TPO'], color=S2, marker='s', linewidth=1.8, label='Autos TPO/comprehensive, B19')
    ax.plot(xf, rz['motor']['TPO_B20'], color=S2, marker='s', linewidth=1.2, linestyle='--', label='Autos TPO/comprehensive, B20')
    ax.plot(xf, rz['contents']['AD'], color=S3, marker='^', linewidth=1.8, label='Contenidos AD sí/no, B19')
    ax.axhline(1, color=GRIS, linewidth=0.8)
    ax.set_xticks(xf); ax.set_xticklabels([f'fold {i}' for i in xf], fontsize=8.5); ax.set_ylabel('razón condicional de tasa (replay)')
    ax.set_ylim(0.5, 1.75); ax.legend(fontsize=7.5, loc='upper left', ncol=1); ax.set_title('AD en edificios cambia de signo entre folds', fontsize=10, color=TINTA, loc='left')
    titulo(fig, 'B19 empeora, B20 recupera con un intervalo que no lo sostiene y un nivel 2 % más bajo', 'Recalculado desde los OOF congelados de dev8 y ridge20 y desde el replay propio de los 15 GLM de cada receta (VN23–VN25). Mismas 50.094 filas y 30.869 componentes de 2023.')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(AQUI / 'fig4_b19_b20.png'); plt.close(fig)


def fig5_influencia(ev):
    """Influencia de componentes en B19 (037): retiros de evaluación por bloques y los dos componentes destacados."""
    d = ev['detalle']['VN26']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5))
    ax = axes[0]
    ks = [1, 5, 10, 31]; x = np.arange(len(ks)); anch = 0.2
    series = [('buildings', 'adverse', S1, 'Edificios, retirar adversos'), ('buildings', 'favorable', S1, 'Edificios, retirar favorables'), ('motor_new', 'adverse', S2, 'Autos nuevos, retirar adversos'), ('motor_new', 'favorable', S2, 'Autos nuevos, retirar favorables')]
    for j, (amb, dirn, c, lab) in enumerate(series):
        vals = [d[amb]['retiros'][f'{dirn} {k}']['delta_ambito'] for k in ks]
        ax.bar(x + (j - 1.5) * anch, vals, width=anch - 0.03, color=c, alpha=1 if dirn == 'adverse' else 0.45, label=lab, zorder=3)
    ax.axhline(0, color=TINTA2, linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels([f'{k} grupo{"s" if k > 1 else ""}' for k in ks]); ax.set_ylabel('delta D² B19 − B14 tras retirar de la evaluación')
    ax.legend(fontsize=8, loc='upper center', bbox_to_anchor=(0.5, -0.12), ncol=2); ax.set_title('Retirar adversos cambia el signo; retirar favorables lo agrava', fontsize=10, color=TINTA, loc='left')
    ax = axes[1]
    bi = d['componente_lesiones_corporales']; fr = d['componente_incendio_286093']
    ax.plot(bi['folds_de_ajuste'], bi['delta_log_TPO'], color=S2, marker='s', linewidth=1.8, label='lesiones corporales 136.767 CU: Δ log-coef. TPO')
    ax.plot(bi['folds_de_ajuste'], bi['delta_log_NB'], color=S2, marker='s', linewidth=1.2, linestyle='--', label='lesiones corporales: Δ log-coef. nuevo negocio')
    ax.plot(fr['folds_de_ajuste'], fr['delta_log_AD'], color=S1, marker='o', linewidth=1.8, label='incendio 286.093 CU: Δ log-coef. AD')
    ax.axhline(0, color=GRIS, linewidth=0.8)
    ax.set_xticks(range(5)); ax.set_xticklabels([f'ajuste {i}' for i in range(5)]); ax.set_ylabel('cambio local aproximado del coeficiente (H⁻¹G_g)')
    ax.set_ylim(-0.27, 0.03); ax.legend(fontsize=8, loc='upper right'); ax.set_title('Influencia local en los ajustes donde participa cada componente', fontsize=10, color=TINTA, loc='left')
    ge, gm = f"{d['buildings']['grupos']:,}".replace(',', '.'), f"{d['motor_new']['grupos']:,}".replace(',', '.')
    titulo(fig, 'Un siniestro de autos nuevos y cinco incendios de edificios mueven los resultados de B19', f"Izquierda: {ge} componentes en edificios y {gm} en autos nuevos, retiros ordenados por pérdida OOF (037). Derecha: H⁻¹G_g desde mi replay de B19, sin reentrenar.")
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(AQUI / 'fig5_influencia.png'); plt.close(fig)


def fig6_atribucion_bandas(ev):
    """Cuánta ganancia de B20 queda al retirar los grupos más favorables (B20-ATTR) y A/E por banda de tasa (B20-BANDS)."""
    d31 = ev['detalle']['VN31']; d33 = ev['detalle']['VN33']
    fig, axes = plt.subplots(1, 2, figsize=(12, 5), gridspec_kw=dict(width_ratios=[1.1, 1]))
    ax = axes[0]
    col = {'W2-B19': S1, 'W2-B14': S2, 'W2-B00': S4}
    for ref in ['W2-B19', 'W2-B14', 'W2-B00']:
        cum = np.asarray(d31['curvas_acumuladas'][ref][:120]); total = d31[ref]['ganancia_total']
        resto = total - np.concatenate([[0.0], cum])
        ax.plot(np.arange(len(resto)), resto / 1000, color=col[ref], linewidth=2, label=f"frente a {ref.replace('W2-', '')}")
        k = d31[ref]['primer_prefijo_adverso']
        ax.scatter([k], [resto[k] / 1000], color=col[ref], s=42, zorder=4, edgecolor='white', linewidth=0.8)
        off = {'W2-B14': (-6, -16), 'W2-B19': (6, 6), 'W2-B00': (10, 14)}[ref]
        ax.annotate(f'{k} grupos', (k, resto[k] / 1000), textcoords='offset points', xytext=off, fontsize=8, color=col[ref])
    ax.axhline(0, color=TINTA2, linewidth=0.8); ax.axvline(31, color=GRIS, linewidth=1, linestyle='--')
    ax.text(32, ax.get_ylim()[1] * 0.92, '31 grupos (0,1 %)', fontsize=8, color=TINTA2)
    ax.set_xlabel('grupos más favorables a B20 retirados de la evaluación'); ax.set_ylabel('ganancia de desviancia restante (miles)')
    ax.legend(fontsize=8.5, loc='upper right'); ax.set_title('Pocos componentes sostienen la ventaja de B20', fontsize=10, color=TINTA, loc='left')
    ax = axes[1]
    x = np.arange(5); anch = 0.13
    for i, l in enumerate(['motor', 'buildings', 'contents']):
        c = [S2, S1, S3][i]
        ae19 = [d33['celdas'][f'{l}_{b}']['AE_B19'] for b in range(1, 6)]; ae20 = [d33['celdas'][f'{l}_{b}']['AE_B20'] for b in range(1, 6)]
        ax.bar(x + (2 * i - 2.5) * anch, ae19, width=anch - 0.02, color=c, alpha=0.4, label=f'{RAMO[l]} B19', zorder=3)
        ax.bar(x + (2 * i - 1.5) * anch, ae20, width=anch - 0.02, color=c, label=f'{RAMO[l]} B20', zorder=3)
    ax.axhline(1, color=TINTA2, linewidth=0.8)
    ax.set_xticks(x); ax.set_xticklabels([f'banda {b}' for b in range(1, 6)], fontsize=8.5); ax.set_ylabel('A/E = observado / predicho (OOF 2023)')
    ax.legend(fontsize=7.5, ncol=3, loc='upper right'); ax.set_ylim(0, 2.6); ax.set_title('Quintiles de tasa de ajuste: el A/E global de 1,01 esconde esto', fontsize=10, color=TINTA, loc='left')
    titulo(fig, 'La ventaja de B20 se concentra en pocos grupos y su calibración cambia mucho por banda', 'Izquierda: ganancia restante al retirar los k grupos más favorables a B20; el punto es el primer k que invierte el signo (VN31). Derecha: A/E por quintil de tasa de ajuste (VN33).')
    fig.tight_layout(rect=(0, 0, 1, 0.9))
    fig.savefig(AQUI / 'fig6_atribucion_bandas.png'); plt.close(fig)


def main():
    ev = json.loads((AQUI / 'evidencia_nocturna.json').read_text(encoding='utf-8'))
    fig1_concordancia(ev); fig2_credibilidad(ev); fig3_folds(ev); fig4_b19_b20(ev); fig5_influencia(ev); fig6_atribucion_bandas(ev)
    print('figuras escritas')


if __name__ == '__main__':
    main()
