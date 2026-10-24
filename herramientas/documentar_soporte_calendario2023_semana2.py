"""Lectura nueva de soporte y balance parcial, sin reajustar o puntuar."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import numpy as np
import pyarrow as pa
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    run=Path(sys.argv[1]).resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');NOW=datetime.now(timezone.utc).isoformat()
    assert r['failed']==v['failed']==0
    table=lambda name:pq.read_table(run/(name+'.parquet')).to_pandas()
    s=table('delay_support');c=table('calendar_profile');d=table('calendar_contrasts');cells=table('peril_business_cells')
    checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    check('No support fraction materially outside[0,1]',s.mature_fraction.between(-1e-10,1+1e-10).all())
    check('All2023 covered days have at least366days followup',c.min_maturity.eq(366).all())
    check('All observed losses are calendar2023',all(list(x)==[2023] for x in c.loss_calendar_years))
    check('All day365 exposure mature',np.allclose(s[s.threshold.eq(365)&~s.pooled_endpoint].mature_fraction,1,atol=1e-10,rtol=0))
    check('No newbusiness covered day reaches730days',s[s.business.eq(1)&s.threshold.eq(730)&~s.pooled_endpoint].mature_exposure.eq(0).all())
    check('C0 endpoints<=365havefullweightedcompletion',np.allclose(cells[cells.pooled_max_delay.le(365)][['count_weighted_completion','cost_weighted_completion']],1,rtol=0,atol=1e-10))
    mix=ROOT/p['mixture_run'];unique=[]
    for line in ['motor','buildings','contents']:
        allclaims=pd.concat([pq.read_table(mix/f'inputs_2023/{line}_fold{k}_fitclaims.parquet').to_pandas() for k in range(5)],ignore_index=True)
        check('Each observed claim appears in four training views '+line,allclaims.groupby('claim_id').size().eq(4).all())
        meta=['year','fold','group_id','x_new_business','T0_cents','delay','age','loss_date','report_date','peril']
        check('Repeated views have identical observed metadata '+line,allclaims.groupby('claim_id')[meta].nunique(dropna=False).eq(1).all().all())
        unique.append(allclaims.drop_duplicates('claim_id'))
    unique=pd.concat(unique,ignore_index=True)
    check('Unique observed claims4567, not five independent cohorts',len(unique)==4567 and unique.claim_id.nunique()==4567)
    profile=[]
    for (line,business),g in unique.groupby(['line','x_new_business']):
        profile.append({'line':line,'business':int(business),'unique_observed_claims':len(g),'unique_groups':int(g.group_id.nunique()),'net_cents':int(g.T0_cents.sum()),
            'observed_delay_max':int(g.delay.max()),'observed_delay_median':float(g.delay.median()),'reports_after365':int(g.delay.gt(365).sum()),'reports_after540':int(g.delay.gt(540).sum())})
    # Focal independent ratio checks complete the support readout; no old suite rerun.
    for idx,row in s.iterrows():
        g=unique[(unique.line==row.line)&unique.fold.ne(row.fold)&unique.x_new_business.eq(row.business)&unique.peril.eq(row.peril)]
        costs=int(g.T0_cents.sum());latecost=int(g.loc[g.delay.gt(row.threshold),'T0_cents'].sum())
        check('Observed cost share '+str(idx),pd.isna(row.observed_net_tail_share) if costs==0 else np.isclose(row.observed_net_tail_share,latecost/costs,rtol=1e-12,atol=1e-12))
        # Weight is fold-specific; never aggregate weights from different fitted views.
        fit=pq.read_table(mix/f'inputs_2023/{row.line}_fold{row.fold}_fitclaims.parquet').to_pandas() if idx%8==0 else fit
        gg=fit[fit.x_new_business.eq(row.business)&fit.peril.eq(row.peril)];weighted=gg.T0_cents*gg.severity_probability_weight
        check('Weighted observed cost share '+str(idx),pd.isna(row.weighted_cost_tail_share) if weighted.sum()==0 else np.isclose(row.weighted_cost_tail_share,weighted[gg.delay.gt(row.threshold)].sum()/weighted.sum(),rtol=1e-12,atol=1e-12))
    fixed=s[~s.pooled_endpoint];h540=fixed[fixed.threshold.eq(540)].groupby(['line','business']).mature_fraction.agg(['min','max']).reset_index()
    dd=d.groupby('line').agg(TV_min=('calendar_maturity_TV','min'),TV_max=('calendar_maturity_TV','max')).reset_index()
    endpoint=s[s.pooled_endpoint&s.business.eq(1)].groupby(['line','peril']).agg(delay_min=('threshold','min'),delay_max=('threshold','max'),risk_min=('reverse_risk_set','min'),risk_max=('reverse_risk_set','max'),events_min=('events_at_threshold','min'),events_max=('events_at_threshold','max'),maturity_min=('mature_fraction','min'),maturity_max=('mature_fraction','max')).reset_index()
    summary={'utc':NOW,'source_scope':'Each fold is a repeated training view, not an independent sample. Only unique observed2023 claims for full-cohort profile.',
        'full_observed_profile':profile,'calendar_TV':dd.to_dict('records'),'maturity540':h540.to_dict('records'),'new_business_endpoint_support':endpoint.to_dict('records'),
        'numerical_probability_overshoot_max':float(max(0,s.mature_fraction.max()-1)),
        'no_adopted_business_curve':True,'no_new_models_or_scores':True,'header_exposure_disclosed':True}
    for name,obj in [('readout.json',summary),('readout_reconciliation.json',{'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks})]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert all(x['pass'] for x in checks),[x for x in checks if not x['pass']]
    pq.write_table(pa.Table.from_pylist(profile),run/'unique_observed_profile.parquet')
    names={'motor':'Autos','buildings':'Edificios','contents':'Contenidos'}
    lines=[]
    for line in ['motor','buildings','contents']:
        row=dd[dd.line.eq(line)].iloc[0];renew=h540[h540.line.eq(line)&h540.business.eq(0)].iloc[0];new=h540[h540.line.eq(line)&h540.business.eq(1)].iloc[0]
        lines.append(f'| {names[line]} | {100*row.TV_min:.2f}–{100*row.TV_max:.2f}% | {100*renew["min"]:.2f}–{100*renew["max"]:.2f}% | {100*new["min"]:.2f}–{100*new["max"]:.2f}% |')
    observed=['| '+names[x['line']]+' | '+('Nuevo' if x['business'] else 'Renovación')+f' | {x["unique_observed_claims"]} | {x["observed_delay_max"]} | {x["reports_after365"]} | {x["reports_after540"]} |' for x in profile]
    doc=f'''# Soporte de calendario y reporte en 2023

Codex, corte UTC {NOW}. Diagnóstico registrado antes del cálculo, sin modelos, curvas nuevas, puntuaciones o remuestreo. Continúa la revisión de la mezcla C0, con B00 y todas las alternativas conservadas. Los cinco folds son los ya guardados.

## Qué aporta el calendario

Los 50.094 periodos corresponden al año de póliza 2023, con 30.869 componentes. En este corte sus días cubiertos y siniestros observados están todos en el calendario 2023. Al valorar a 31 de diciembre de 2024, cada día cubierto tiene al menos 366 días de maduración. Esto explica que las curvas congeladas cuyo último reporte está dentro de 365 días den completitud uno bajo su supuesto de cola. No demuestra que la cola real termine allí.

La exposición diaria respeta los extremos inclusivos. Cada periodo reparte su exposición nominal entre sus días cubiertos; no se equipara la exposición redondeada a un número entero de años. Se reconstruyó la masa con expansión diaria y suma por fold retenido, por otro método que las diferencias de intervalos del productor.

| Ramo | Distancia total entre calendarios por negocio | Exposición de renovación con ≥540 días | Exposición nueva con ≥540 días |
| --- | ---: | ---: | ---: |
{chr(10).join(lines)}

Los rangos recorren los cinco ajustes, con muestras solapadas. La distancia total es la mitad de la suma de diferencias absolutas entre masas normalizadas por edad; no es un test. El calendario de nuevo negocio dispone de menos seguimiento largo. Una diferencia entre completitudes de negocio puede existir aun usando exactamente la misma curva por peril, por esa composición de días. Esto no atribuye causalmente el deterioro de los modelos al calendario.

## La cola observada no identifica la que falta

| Ramo | Negocio | Siniestros únicos observados | Demora máxima, días | Reportes >365 días | Reportes >540 días |
| --- | --- | ---: | ---: | ---: | ---: |
{chr(10).join(observed)}

Esta tabla deduplica las vistas de ajuste: cada siniestro aparece en cuatro, no en cinco muestras independientes. Los máximos y proporciones describen reclamaciones conocidas al corte. No son probabilidades incondicionales de reporte ni estimaciones de siniestros aún desconocidos. La ausencia de cola observada en una celda no establece ausencia de riesgo futuro.

En lesiones corporales de autos, el extremo observado de las curvas agrupadas cambia entre 609 y 653 días según fold. Solo entre 4,27% y 11,19% de la exposición de autos nuevos tiene suficiente maduración para llegar al extremo correspondiente. El conjunto de riesgo inverso de ese negocio contiene de uno a cinco siniestros y no aporta eventos en ese extremo. Esto limita una curva separada; no prueba que la curva agrupada sea correcta. Riesgo inverso significa reclamaciones observadas con demora ≤d y seguimiento ≥d. No equivale al número de siniestros futuros potenciales ni a exposición asegurada.

Los anexos conservan todas las celdas por ramo, peril, negocio y fold, incluyendo las vacías, los puntos de 0, 30, 90, 180, 365, 540 y 730 días y el extremo congelado de cada curva. Se distinguen exposición suficientemente madura, reclamaciones con seguimiento, riesgo inverso, eventos exactos y costes observados después del punto. No se introduce un umbral de muestra suficiente ni se selecciona una nueva cola.

## Decisión y verificación

No se ajustará una curva de negocio o se añadirá complejidad de precios como consecuencia de este diagnóstico. La escasez y la censura siguen abiertas. El siguiente trabajo comprueba soporte técnico por coberturas antes de aceptar denominadores por peril; tampoco se interpretará una mezcla poblacional como cobertura individual. Un ensayo numérico futuro necesitará hipótesis y criterio previos y respetar las limitaciones de información.

Pasaron {r['passed']} controles del flujo descriptivo, {v['passed']} verificaciones y adversos nuevos, y {sum(x['pass'] for x in checks)} conciliaciones de lectura, con solapamiento. La segunda cuenta suma cada día por separado y reconstruye los conjuntos de riesgo con Python; las curvas se consultan por búsqueda bisect. Se probó el comando real con año sintético 2024 y se conservó su fallo esperado antes de salidas, sin usar datos reales de ese año. Los errores de redondeo máximos de fracciones alrededor de uno quedan en readout.json sin alterar cifras originales; son del orden de 1e-14. Revisión técnica propia, no profesional independiente. Cero ajustes, scores o bootstrap nuevos; contadores de precio 165/285 sin cambio.

## Exposición accidental y ámbito

Un inventario de encabezados del foro mostró un asunto de CLA-S2-20261024-006 con métricas de 2024. La guarda anterior fue insuficiente y no puede afirmarse ceguera completa tras esa lectura. Se registró antes del diagnóstico sin repetir cifras. No se abrió cuerpo, acta, predicción o ledger. El lector nuevo solo expone autor, ID y fecha y pasó una prueba con marcadores secretos en título y cuerpo, además del flujo real. Las cifras externas no se usan para decisiones de 2023. Esta unidad sigue el diagnóstico de datos ya previsto, sin entrenamiento, puntuación o selección adaptativa. La autorización anunciada en otro chat permanece sin verificar o invalidar; no abre otra tanda en esta tarea.

## Evidencia

Plan: [registro congelado](../../registro/semana2_soporte_calendario2023_plan_v1.json). Índice: [soporte actual](../../registro/semana2_soporte_calendario2023_actual.json). Productor: [auditor de calendario](../../src/semana2/auditar_soporte_calendario2023.py). Comprobador: [otra cuenta y adversos](../../herramientas/verificar_soporte_calendario2023_semana2.py). Lector: [índice del foro sin asuntos](../../herramientas/leer_foro_semana2_seguro.py). Balance: [corte parcial de la noche](BALANCE_NOCTURNO_PARCIAL_20261024.md).

Detalle restringido, recibos y hashes: `{rel(run)}`. Fuentes de la mezcla anterior en [su informe](MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md). Prácticas priorizadas: consideraciones profesionales §3.1 y §3.3, gobernanza §2.8 y documentación §§2–3; el enlace documental no certifica cumplimiento ni revisión humana.
'''
    docpath=REPO/'docs/semana2/SOPORTE_CALENDARIO_REPORTE_2023.md';assert not docpath.exists();docpath.write_text(doc,encoding='utf-8')
    balance=f'''# Balance parcial de la noche del 23 al 24 de octubre

Codex, corte UTC {NOW}. La ventana sigue hasta las 07:00 de Bogotá; este balance no es el cierre de la mañana. Hay siete unidades completas, incluyendo este diagnóstico sin ajustes. Todas las recetas, resultados adversos y alternativas de esta línea se conservan. B00 permanece como referencia. Ningún punto exploratorio de 2023 promueve una alternativa o congela la lista final.

| Trabajo terminado | Qué permite concluir | Qué permanece abierto |
| --- | --- | --- |
| B12 y GLM B13 sencillos, cinco folds guardados | Se dispone de referencias por ramo/negocio y efectos principales bajo el objetivo y exposición establecidos | Generalización temporal, concentración e incertidumbre de parámetros |
| Capital por fila y B14 | Hay trazabilidad y replay de la representación; 56 filas corregidas de 2023 tienen T0 cero | La escala económica no se prueba por quedar dentro del soporte o reproducir la fórmula |
| Clima y credibilidad B15–B18 | Clima futuro propuesto no entra como predictor prospectivo; las correcciones de autos nuevos no muestran mejora estable | Prior desarrollado no reconstruido de bruto aquí, incertidumbre de credibilidad, dependencia temporal |
| [Cola y nivel](SENSIBILIDAD_COLA_Y_NIVEL_2023.md) | Otra normalización mueve el nominal condicionado alrededor de 2,5% con score observado idéntico | Escala de último no identificada por D² observado |
| [Reservas y reportes tardíos](NIVEL_C0_REPORTES_Y_RESERVAS_2023.md) | B14 responde aproximadamente ±2,48% a reservas y −0,66% a una perturbación del estimador C0 | Son sensibilidades, no suficiencia de reservas ni intervalos estadísticos; pequeños puntos positivos invierten signo bajo influencia |
| [Mezcla por negocio](MEZCLA_C0_PERIL_Y_NEGOCIO_2023.md) | Se separaron composición de frecuencia y severidad; ambas variantes empeoran el punto frente a sus padres | Celdas escasas, costes concentrados, curvas por negocio y cobertura individual |
| [Calendario y soporte](SOPORTE_CALENDARIO_REPORTE_2023.md) | Se distinguen masa de exposición, maduración y riesgo inverso; nuevo negocio tiene bastante menos exposición madura a 540 días | Las demoras conocidas no identifican la cola aún desconocida ni validan una curva separada |

No hay una necesidad demostrada de precios más complejos que pueda resolver los límites de observación anteriores. La próxima unidad examinará cobertura técnica admisible y denominadores por peril, con datos de 2023, sin asumir que toda exposición cubre todo peril. Solo se abrirá otro ensayo si responde a un fallo concreto y se registra antes. No repetir entrenamiento, suites o remuestreo sobre las mismas fuentes por rutina.

El contador propio es 165 ajustes de precio y 285 constantes. Separados: 30 auxiliares de credibilidad anteriores, 75 curvas de reporte suplementarias (además de la preparación histórica) y 150 frecuencias/145 medias de mezcla. Este diagnóstico no añade ninguno. Los contadores no representan el trabajo de otros autores. Las verificaciones de Codex y colaboraciones entre IA no son revisión profesional independiente ni aprobación humana.

La instrucción humana de esta tarea mantiene 2024/test sin precios, predicciones, puntuaciones o lectura del ledger. Claude anunció apertura por autorización en otro chat, que aquí no se verifica ni invalida. Un título del foro reveló métricas de esa confirmación y se registró el incidente: no se mantiene una afirmación de ceguera completa. El lector corregido oculta asuntos y cuerpos; esas cifras no se usan para elegir en 2023. No hay segunda tanda, envíos, remoto, nuevos chats, delegación o cambios a otras automatizaciones.
'''
    balancepath=REPO/'docs/semana2/BALANCE_NOCTURNO_PARCIAL_20261024.md';assert not balancepath.exists();balancepath.write_text(balance,encoding='utf-8')
    warnings=[{'id':'SUPPORT-CALENDAR','status':'open','effect':'Newbusiness has less mature exposure at long delays; calendar differences do not identify causal price-model failure.'},
        {'id':'SUPPORT-TAIL','status':'open','effect':'Observed delay support and tiny newbusiness reverse risk near pooled endpoints do not identify unseen tail or justify separate business curves.'},
        {'id':'SUPPORT-COVERAGE','status':'open','effect':'Peril denominators still use broad line/business exposure. Review admissible technical coverage masks before more complexity; no structural zero inferred.'},
        {'id':'SUPPORT-EXPOSURE-2024','status':'open','effect':'External forum subject exposed2024 outcome metrics; no complete-blindness claim. Safe reader emits only author/id/UTC; no external outcome used in this data-only audit.'}]
    assessment={'author':'Codex','utc':NOW,'status':'descriptive_support_verified_no_curve_or_price_adoption','warnings':warnings,'professional_independent_validation':False}
    (run/'assessment.json').write_text(json.dumps(assessment,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    journal={'author':'Codex','utc':NOW,'decisions':[{'hypothesis':p['hypothesis'],'prior_criterion':p['decision_rule'],'sources':p['frozen_sources'],'result':'Different maturity calendars and sparse tail support; no new curve or price model. See readout.json.','verification':rel(run/'verification.json'),'consequence':'Keep pooled curves conditional and preserve alternatives; review coverage denominators before a new registered test.'},
        {'issue':'Forum subjects may contain confirmation outcomes','result':'One external2024 headline already seen; cannot undo or claim complete blindness.','control':'Safe inventory schema and title/body canary plus real CLI tested.','consequence':'No subjects/bodies/2024 artifacts; no outcomes used for2023 choices. Diagnostic only, zero fit/score.'}]}
    (run/'decision_journal.json').write_text(json.dumps(journal,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    idx={'id':p['id'],'author':'Codex','utc':NOW,'path_base':'workspace_root','status':assessment['status'],'run':rel(run),'documentation':rel(docpath),'partial_balance':rel(balancepath),
        'plan':rel(REPO/'registro/semana2_soporte_calendario2023_plan_v1.json'),'reference':'W2-B00','training_years':[],'audited_policy_years':[2023],'new_fits':0,'new_scores':0,'new_bootstrap':0,
        'forum_prior':'COD-S2-20261024-030','forum_result':'COD-S2-20261024-031','warnings':warnings,'external2024_subject_exposure_recorded':True,'ledger_read':False,'professional_independent_validation':False}
    for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest']:
        path=run/(name+'.json');idx[name]={'path':rel(path),'sha256':sha(path)}
    (run/'index_proposed.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=f'''La séptima unidad registrada en 030 terminó solo con datos de 2023 y sin ajustes, curvas nuevas, puntuaciones o remuestreo. Informe: `{rel(docpath)}`. Balance parcial: `{rel(balancepath)}`. B00, el catálogo principal y las sensibilidades anteriores se conservan.

Los días cubiertos y los siniestros de estos contratos están en el calendario 2023; todos sus días cubiertos tienen al menos 366 días de seguimiento al corte. A 540 días, la exposición suficientemente madura es alrededor de 52,33% en renovaciones frente a 26,54–27,33% en nuevo negocio, según ramo/fold. Los calendarios por negocio difieren alrededor de 25–26% en distancia total. Son perfiles de muestras solapadas, no pruebas causales ni nuevas probabilidades de reporte.

En lesiones corporales de autos, los extremos agrupados de 609–653 días dejan solo 4,27–11,19% de exposición nueva suficientemente madura. El conjunto de riesgo inverso nuevo contiene de uno a cinco siniestros y cero eventos en esos extremos. No se ajusta una curva separada. Las colas observadas y los ceros no identifican siniestros desconocidos o riesgo futuro nulo. Se conservan las 150 celdas y 1.200 puntos de soporte, y se deduplican 4.567 siniestros para el perfil general. No se mezcla el peso ajustado de un fold con otro.

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones y adversos y {sum(x['pass'] for x in checks)} conciliaciones focales, con solapamiento. La segunda cuenta expande días y usa Python/bisect; el comando real rechaza año sintético 2024 y conserva el fallo esperado. El lector del foro pasa pruebas de título/cuerpo secretos y flujo real. Son verificaciones propias, no revisión profesional independiente. Contador de precio sin cambio: 165 ajustes y 285 constantes, primeras etapas y auxiliares separados.

Se mantiene el incidente registrado en 030: un título ajeno mostró métricas de 2024; no se repiten ni se usan, y no se afirma ceguera completa. No se abrieron cuerpos, actas, predicciones o ledger; el lector solo muestra autor, ID y UTC. La instrucción de esta tarea mantiene 2024 cerrado y no abre otra confirmación. Siguiente unidad: revisar coberturas admisibles y denominadores por peril antes de proponer complejidad. Ninguna promoción, retiro de alternativas o lista final; programación hasta las 07:00 Bogotá sin cambios a otras continuaciones.
'''
    (ROOT/'Hackaton/Semana 2/Codex/soporte_calendario2023_resultado.md').write_text(body,encoding='utf-8')
    print(json.dumps({'documentation':rel(docpath),'balance':rel(balancepath),'readout_checks':len(checks),'failed':0,'full_observed_profile':profile}))

if __name__=='__main__':main()
