"""Historias, comparaciones de ampliaciones y propuesta, con dos figuras estándar."""
from pathlib import Path
import html
import json
import sys
import review_endorsements as a
import clean_data as c
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter


def n(x, dec=0):
    return f'{float(x):,.{dec}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def main(out):
    assert not (out/'manifest.json').exists()
    read = lambda name: pd.read_parquet(out/'tables'/(name+'.parquet'))
    h, f = read('all_policy_histories'), read('assessment_2')
    peers, stats = read('other_original_2022_2023_triads'), read('peer_statistics')
    s = json.loads((out/'summary.json').read_text('utf-8'))
    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    for col, pid in enumerate(a.PIDS):
        g = h.loc[h.policy_id.eq(pid)].sort_values('period_start')
        rec = f.loc[f.policy_id.eq(pid)].iloc[0]
        x = np.arange(4)
        observed = g.sum_insured.to_numpy()
        hypothetical = observed.copy()
        hypothetical[0] /= 1000
        ax = axes[0, col]
        ax.plot(x, observed, 'o-', color='#596878', label='Capital vigente, sin cambios')
        ax.scatter([0], [hypothetical[0]], marker='D', s=80, facecolors='none', edgecolors='#b46a21', label='2021 /1000, solo hipótesis')
        ax.set_yscale('log')
        ax.set_ylim(15000, 60000000)
        ax.set_title(pid+' · escala vigente y alternativa')
        ax.set_ylabel('Capital CU, eje logarítmico')
        ax.set_xticks(x, ['2021', '2022 inicial', '2022 ampliado', '2023 renovación'])
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: n(v)))
        for j, value in enumerate(observed):
            ax.annotate(n(value), (j, value), xytext=(0, 10 if j != 2 else 20), textcoords='offset points', ha='center', fontsize=9)
        ax.legend(frameon=False, fontsize=8, loc='upper right')
        ax = axes[1, col]
        ax.plot(x, hypothetical, 'o-', color='#176477', label='Trayectoria con 2021 /1000 hipotético')
        ax.scatter([0], [hypothetical[0]], s=90, marker='D', color='#b46a21', zorder=4)
        ax.set_title('Ampliación y renovación se conservan completas')
        ax.set_ylabel('Capital CU, eje lineal')
        ax.set_xticks(x, ['2021 hipotético', '2022 inicial', '2022 ampliado', '2023 renovación'])
        ax.set_ylim(20000, 44000)
        ax.yaxis.set_major_formatter(FuncFormatter(lambda v, pos: n(v)))
        for j, value in enumerate(hypothetical):
            ax.annotate(n(value)+(' (hip.)' if j == 0 else ''), (j, value), xytext=(0, 10), textcoords='offset points', ha='center', fontsize=10)
        ax.text(.02, .02, f'Ampliación +{n(rec.midterm_growth_pct,2)}% · renovación {n(rec.renewal_vs_endorsed_pct,2)}%', transform=ax.transAxes, fontsize=10)
    for ax in axes.flat:
        ax.spines[['top', 'right']].set_visible(False)
        ax.grid(axis='y', alpha=.15)
        ax.tick_params(axis='x', labelsize=8)
    fig.suptitle('Dos pólizas de contenidos: distinguir escala 2021 de cambios de capital 2022/2023', fontsize=15)
    fig.tight_layout(rect=[0, 0, 1, .96])
    fig.savefig(out/'figures/histories.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8))
    configs = [('endorsement_growth_pct', 'Aumento durante 2022, %'), ('renewal_vs_endorsed_pct', 'Renovación / ampliación, cambio %'), ('renewal_vs_baseline_pct', 'Enero 2023 / inicio 2022, cambio %')]
    for ax, (metric, label) in zip(axes, configs):
        ax.hist(peers[metric], bins=28, color='#a9c4ce', edgecolor='white', label='Otras 2.305 pólizas originales')
        field = 'midterm_growth_pct' if metric == 'endorsement_growth_pct' else ('renewal_vs_2022_baseline_pct' if metric == 'renewal_vs_baseline_pct' else metric)
        for pid, color, style in [(a.PIDS[0], '#a95b16', '-'), (a.PIDS[1], '#1e4766', '--')]:
            value = f.loc[f.policy_id.eq(pid), field].iloc[0]
            ax.axvline(value, color=color, linestyle=style, linewidth=2, label=pid+': '+n(value, 2)+'%')
        ax.set_xlabel(label)
        ax.set_ylabel('Pólizas')
        ax.spines[['top', 'right']].set_visible(False)
        ax.legend(frameon=False, fontsize=8)
    fig.suptitle('Comparación descriptiva: cohorte original 2022/2023, sin las dos pólizas revisadas', fontsize=14)
    fig.text(.5, .01, 'Criterios exploratorios definidos tras observar los casos. No prueba contractual ni validación independiente.', ha='center', fontsize=10)
    fig.tight_layout(rect=[0, .05, 1, .93])
    fig.savefig(out/'figures/peer_comparison.png', dpi=150, bbox_inches='tight')
    plt.close(fig)
    def table(frame, cols=None):
        return '<div class="scroll">'+(frame[cols] if cols else frame).to_html(index=False, border=0, na_rep='Sin dato', float_format=lambda x: n(x, 4))+'</div>'
    sections = []
    def section(title, body):
        sections.append('<section><h2>'+title+'</h2>'+body+'</section>')
    section('La propuesta tras revisar las ampliaciones', '''<p>Los dos capitales de 2021 son candidatos a una corrección manual retrospectiva /1000: C00502745, de 27.200.000 a 27.200 CU, y C00399729, de 25.700.000 a 25.700 CU. La propuesta afecta exclusivamente esas dos celdas; las ampliaciones de 39.400/37.700 y renovaciones de 28.300/26.700 se conservarían.</p><p>Ambas filas siguen pendientes entre las 421 actuales. No se modifica dato, índice de datos, protocolo 1.9, predictor o regla operativa. Esta revisión aporta una justificación nueva que separa los cambios de nivel dentro del contrato de la hipótesis de unidad de otro periodo.</p><div class="note">Las dos siguen sin cumplir DIST01-R: la primera referencia completa sigue siendo la ampliación de 2022, incompatible con una trayectoria suave. La propuesta manual reconoce expresamente ese salto, no oculta la referencia ni declara superada la regla anterior. Requeriría una autorización separada.</div><p><a href="tables/proposed_manual_scale_changes_NOT_APPLIED.csv">Las dos propuestas sin aplicar</a> · <a href="proposal.json">Motivos, alternativas y límites</a> · <a href="protocol.json">Criterio de esta revisión</a></p>''')
    section('Ocho periodos, dos historias completas', '<p>Fuente: catálogo retrospectivo CAP05R y las tablas originales. Las ocho filas pertenecen a train; no hay filas de test 2025 para estas pólizas. Se releen todos los campos, con originales archivados.</p><img src="figures/histories.png" alt="Capitales vigentes en eje logarítmico y trayectoria con solo 2021 dividido hipotéticamente por mil, manteniendo ampliación y renovación">')
    for pid in a.PIDS:
        g = h.loc[h.policy_id.eq(pid)].sort_values('period_start').copy()
        q = f.loc[f.policy_id.eq(pid)].iloc[0]
        view = g[['row_id', 'period_start', 'period_end', 'sum_insured', 'exposure', 'renewal_count', 'renewal_decision', 'written_premium', 'security_level', 'high_value_items']].copy()
        for col in ['period_start', 'period_end']:
            view[col] = view[col].dt.strftime('%Y-%m-%d')
        history = table(view)
        first = g.iloc[0]
        different = read('all_adjacent_field_changes').loc[lambda x: x.policy_id.eq(pid)]
        body = f'''<p>Cliente {html.escape(first.customer_id)}, dirección {html.escape(first.address_id)}. Contenidos de un arrendatario; no se está valorando el edificio. Edad observada {int(first.policyholder_age)}→{int(g.iloc[-1].policyholder_age)}, renovación {int(first.renewal_count)}→{int(g.iloc[-1].renewal_count)}.</p>{history}
<p>La ampliación aumenta el límite de {n(q.immediate_2022_CU)} a {n(q.endorsed_2022_CU)} CU (+{n(q.midterm_growth_pct,2)}%). La fila inicial de 2022 termina con mid_term_change y la siguiente comienza al día siguiente, con el mismo contador de renovaciones. En enero de 2023 el contador sube una unidad y el capital baja a {n(q.renewal_2023_CU)} CU ({n(q.renewal_vs_endorsed_pct,2)}% frente a la ampliación).</p>
<p>Si se dividiera solo 2021 por mil, el paso al inicio de 2022 sería +{n(q.growth_2021hyp_to_2022_pct,2)}%, y el inicio de 2023 quedaría +{n(q.renewal_vs_2022_baseline_pct,2)}% sobre la base inicial de 2022. El cambio en dos años sería +{n(q.two_year_base_growth_pct,2)}%. La ampliación intermedia seguiría visible, sin suavizarse.</p>
<p>La primera referencia completa de 2022 está a {int(q.nearest_complete_reference_gap_days)} días; el hipotético 2021 es {n(100*q.hypothesis_to_endorsed_ratio,2)}% de ese límite, fuera de la banda 90–110%. La renovación de 2023 está a 730 días. Se registra toda esa evidencia; no se escoge solo la fecha favorable.</p>
<p>El contexto ausente en la primera fila de 2022 es {html.escape(q.immediate_2022_missing_fields)}. Los demás campos D34 conocidos coinciden, y el campo está informado en 2021, la ampliación y 2023. Esos vecinos no demuestran el valor intermedio: el nulo se conserva.</p>
<p>Hay {int(q.total_observed_covered_days)} días cubiertos observados, sin huecos o solapes en estos ocho registros. La última fila termina por lapsed_by_customer en 2023; no aparecen periodos posteriores de la misma póliza ni otra póliza de estos clientes en las seis tablas. Ausencia en el archivo no demuestra ausencia de seguro fuera de esta aseguradora.</p>
<details><summary>Todos los cambios de campo entre periodos</summary>{table(different)}</details>'''
        if pid == 'C50633171':
            body += '<p>Se mantienen cobertura accidental=true, trabajo en casa=true, sin inquilinos adicionales ni bicicletas, exceso voluntario 0 CU y obligatorio 350. high_value_items es 0 en las otras tres filas, desconocido en la inicial de 2022. La ampliación no viene acompañada de un cambio conocido en esas coberturas.</p>'
        else:
            body += '<p>Se mantienen cobertura accidental=false, trabajo en casa=false, sin inquilinos adicionales ni bicicletas, bienes de valor=0, exceso voluntario 250 CU y obligatorio 350. security_level es alarm_and_locks en las otras tres filas y desconocido en la inicial de 2022.</p>'
        section(pid, body)
    section('Qué aportan las renovaciones de otras pólizas', f'''<p>Se definió una cohorte exploratoria después de ver ambos casos: una fila 2022 marcada mid_term_change, su siguiente segmento contiguo del mismo año y una renovación contigua de 01-01-2023. Las tres filas deben tener capital original entre 1 y 1.000.000 CU, mismo cliente/dirección y ningún cambio conocido entre los campos D34; no ser alta nueva, conservar el contador dentro de 2022 y aumentarlo una unidad en 2023. El umbral de un millón es el filtro histórico de anomalías, no un máximo contractual. No se exigió aumento grande ni reversión para seleccionar.</p><p>Se obtienen {s['ordinary_triads_including_focus']:,} tríos, incluidos los dos casos. Las estadísticas y gráficos usan solo las otras {s['other_original_triads']:,} pólizas: {s['other_triads_all_D34_known']:,} tienen todos los campos D34 informados en los tres periodos, las demás conservan incertidumbre. En {s['other_triads_growth20_drop10_return_within10pct']:,} hay aumento superior a 20%, caída superior a 10% y renovación a menos de 10% de la base previa. Todos los datos de capital del grupo son originales, sin reparaciones usadas como referencias.</p><img src="figures/peer_comparison.png" alt="Distribuciones de cambios de capital en otras 2305 pólizas originales frente a las dos focales">{table(stats)}<p>Además, {s['other_triads_original_complete_normal_2021']:,} tienen un predecesor 2021 original habitual y completo con contexto conocido compatible. Es un apoyo de coherencia interna del recorrido por renovaciones. La selección se diseñó tras observar los casos; no es prueba contractual, muestra independiente ni porcentaje de probabilidad de error.</p><h3>Seis ejemplos reales ajenos a los dos casos</h3>{table(read('other_policy_examples'), ['policy_id','baseline_row_id','endorsed_row_id','renewed_row_id','baseline_CU','endorsed_CU','renewed_CU','endorsement_growth_pct','renewal_vs_baseline_pct'])}<p><a href="tables/other_original_2022_2023_triads.csv">Los 2.305 tríos comparables</a> · <a href="tables/peer_statistics.csv">Estadísticas descriptivas</a></p>'''.replace('2,307', '2.307').replace('2,305', '2.305').replace('1,991', '1.991').replace('2,300', '2.300').replace('2,193', '2.193'))
    section('Lectura para el seguro y la tarifa', '''<p>sum_insured es el límite de contenidos de cada periodo. Una subida de límite puede elevar la pérdida potencial cubierta y afectar la prima, sin que el coste esperado crezca en igual proporción. El importe de 2022 no debe trasladarse a 2021; una renovación puede registrar un límite distinto. No hay documento de suplemento, inventario de bienes ni explicación contractual del descenso posterior.</p><p>Las filas de 2022 dividen un mismo año, con exposiciones 0,3370+0,6630=1,0000 y 0,6959+0,3041=1,0000. El capital es un límite, no un flujo: no se suma, pondera por exposición o anualiza para reconstruir un capital contractual.</p><p>La prima escrita sube al ampliarse el límite: C50633171 pasa de 92,73 a 114,77 CU y C56600576 de 97,89 a 106,50. En 2023 figuran 111,00 y 95,50 CU. La fuente solo dice prima cobrada con la tarificación vigente; no aclara aquí su convención anual/prorrateada. Las duraciones y otros factores cambian. Estos importes son descriptivos y no prueban la unidad del capital ni deben dividirse por exposición para decidir esta reparación.</p><p>No hay expedientes de siniestro para ninguna de las dos pólizas, ni en originales ni tras DUP01/PRE00. La falta de siniestros observados no implica riesgo cero ni confirma el límite. No se toca el objetivo; un futuro ensamblado deberá seguir asignando por fecha de ocurrencia al periodo exacto. renewal_decision y contactos se consultan como diagnóstico; no se aprueba convertirlos en predictores.</p><details><summary>Maestros de contexto, sin valoración contractual fechada</summary>'''+table(read('address_context'))+table(read('customer_context'))+'''<p>Los maestros aportan ubicación, vivienda y cliente; no registran el inventario de bienes ni el suplemento de 2022. soil_type de A9652261 permanece ausente. El historial de servicio y el contador no certifican la edad contractual a cada renovación.</p></details>''')
    section('Tratamiento propuesto y alternativas', '''<ol><li>Mantener ahora los dos registros pendientes y sus valores vigentes. Registrar la hipótesis de unidad separada de la variación contractual.</li><li>Proponer una excepción manual retrospectiva MANUAL_ENDORSE01-R, limitada a C00502745 y C00399729: dividir exclusivamente sus capitales 2021 por mil. El respaldo usa renovaciones futuras de train 2022/2023; no depende de test 2025.</li><li>Conservar 39.400/37.700 en las ampliaciones y 28.300/26.700 al renovar. No copiar, interpolar o forzar una senda suave. Conservar high_value_items y security_level ausentes en sus filas respectivas.</li><li>Si el participante autoriza aplicar la propuesta, crear otra capa con bitácora y reversión, y verificar solo esas dos celdas. Los pendientes pasarían de 421 a 419 exclusivamente después de esa operación; hoy siguen en 421. No ampliar automáticamente el criterio a otros casos.</li></ol><p>Recomiendo esa revisión manual de escala para las dos filas, por la coherencia de las bases anuales y la evidencia de que las ampliaciones y retornos ocurren en otros registros originales. La observación de 2021 sigue siendo incierta: la unidad y la causa del retorno requieren la fuente para confirmación contractual. La regla candidata no aporta por sí sola aprobación para backtests causales.</p><details><summary>Escenarios ilustrativos y por qué se rechazan copias o suavizados</summary>'''+table(read('scenarios_NOT_APPLIED'))+'</details>')
    section('Fuentes, comprobaciones y límites', '''<p>Datos del catálogo CAP05R, originales Parquet y diccionario archivado del concurso. Los ocho periodos y todos sus campos se conservan, junto con 421 pendientes, originales y todos los archivos del catálogo; se comparan hashes antes/después. El protocolo 1.9 y ambos índices de datos permanecen iguales. No se crea otra capa, marca de auditoría o predictor.</p><p><a href="tables/all_policy_histories.csv">Historial completo, CSV</a> · <a href="tables/all_original_policy_histories.parquet">Originales de las ocho filas</a> · <a href="tables/transition_comparisons.csv">Comparaciones de cada transición</a> · <a href="tables/all_adjacent_field_changes.csv">Todos los campos que cambian</a> · <a href="evidence/data-description.md">Diccionario archivado</a> · <a href="summary.json">Resumen estructurado</a> · <a href="verification.json">Controles propios</a> · <a href="manifest.json">Manifiesto SHA256</a></p><p>La IA preparó análisis, código y comprobaciones propias; no hay revisión independiente. Los gráficos se inspeccionan como archivos, sin atribuir renderizado de navegador. Sin entrenamiento, proveedor externo, publicación, contacto a terceros o delegación. IAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2 y §§3.5–3.6 orientan trazabilidad y responsabilidad; son referencias educativas, no certificación.</p>''')
    report = '''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Dos capitales pendientes: ampliaciones y renovaciones</title><style>body{font:16px/1.65 system-ui,sans-serif;color:#193245;background:#eef3f6;margin:0}main{max-width:1450px;margin:auto;padding:24px}header,section{background:white;border-radius:12px;padding:24px;margin-bottom:18px}header{background:#17394d;color:white}h1{font-size:30px;line-height:1.3}h2{font-size:24px}h3{font-size:19px}img{max-width:100%;height:auto}table{border-collapse:collapse;font-size:13px;width:100%}th,td{padding:9px;border-bottom:1px solid #dce5ea;white-space:nowrap;text-align:left}th{background:#edf3f6;position:sticky;top:0}.scroll{overflow:auto;max-height:600px}.note{border-left:4px solid #b47725;background:#fff5e2;padding:12px 18px}details{margin:15px 0}summary{cursor:pointer;color:#176477}a{color:#007d72}</style></head><body><main><header><h1>C50633171 y C56600576: ampliaciones y renovaciones</h1><p>Ocho periodos de train · Dos propuestas manuales sin aplicar · 421 pendientes conservados</p><p>Se distingue la hipótesis /1000 de 2021 de las ampliaciones y límites observados de 2022/2023.</p></header>'''+''.join(sections)+'</main></body></html>'
    (out/'informe.html').write_text(report, encoding='utf-8')
    c.dump(out/'figure_specifications.json', {'figures': ['figures/histories.png','figures/peer_comparison.png'],
        'history_labels': a.PIDS, 'history_rows': 8, 'only_hypothetical_values': {'C00502745': 27200, 'C00399729': 25700},
        'peer_rows_excluding_focus': len(peers), 'real_browser_rendering_verified': False})
    print(json.dumps({'report': str(out/'informe.html'), 'figures': 2}))


if __name__ == '__main__':
    main(Path(sys.argv[1]).resolve())
