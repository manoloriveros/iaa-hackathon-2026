"""Lectura financiera y acta focal, sin nuevos scores ni ajuste."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import sys

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(path,x):
    with path.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2,default=str);f.write('\n')


def main(run):
    run=run.resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json')
    assert r['failed']==v['failed']==0
    now=datetime.now(timezone.utc).isoformat();checks=[]
    def check(name,ok):checks.append({'name':name,'pass':bool(ok)});assert ok,name
    c=pq.read_table(run/'claims_original_selected_2023.parquet').to_pandas()
    a=c[c.included_in_T0].copy();period=pq.read_table(run/'period_reconciliation_2023.parquet').to_pandas()
    s=pq.read_table(run/'selection_reasons.parquet').to_pandas()
    def summary(frame):
        return {'groups_with_claims':int(frame.group_id.nunique()),'claims':len(frame),
                'closed':int(frame.status.eq('closed').sum()),'open':int(frame.status.eq('open').sum()),
                'late_gt365':int(frame.late_gt365.sum()),'reports_in_2024':int(frame.report_date.dt.year.eq(2024).sum()),
                'closed_with_reserve':int(frame.closed_with_reserve.sum()),
                **{m+'_cents':int(frame[m+'_cents'].sum()) for m in ['paid','incurred','recoveries','reserve','T0']},
                'reserve075_quarter_cent_units':int(frame.reserve075_quarter_cent_units.sum()),
                'reserve125_quarter_cent_units':int(frame.reserve125_quarter_cent_units.sum()),
                'delay_min':int(frame.delay_days.min()) if len(frame) else None,
                'delay_max':int(frame.delay_days.max()) if len(frame) else None}
    cohorts={'all_selected':summary(a)}
    for scope,line in [('buildings','buildings'),('motor_new','motor')]:
        groups=set(s.loc[s.reason.eq('OOF_top5_adverse_'+scope),'group_id'])
        cohorts['OOF_top5_'+scope]=summary(a[a.group_id.isin(groups)&a.line.eq(line)])
    main_group=s.loc[s.reason.eq('OOF_top5_adverse_motor_new')&s['rank'].eq(1),'group_id'].iloc[0]
    m=a[a.group_id.eq(main_group)&a.line.eq('motor')]
    check('Dominant motor component is one selected claim',len(m)==1)
    main=m.iloc[0]
    mainfact={key:str(main[key]) if key.endswith('_date') else main[key].item() if hasattr(main[key],'item') else main[key]
              for key in ['line','status','peril','paid_cents','incurred_cents','recoveries_cents','reserve_cents','T0_cents','delay_days','age_days','loss_date','report_date','fold']}
    check('Main motor fully paid not a case reserve',mainfact['status']=='closed' and mainfact['reserve_cents']==0 and mainfact['paid_cents']==mainfact['T0_cents'])
    check('Main motor report below365day threshold',mainfact['delay_days']==58 and not bool(main.late_gt365))
    check('All selected source identity balances',cohorts['all_selected']['T0_cents']==cohorts['all_selected']['paid_cents']+cohorts['all_selected']['reserve_cents']-cohorts['all_selected']['recoveries_cents'])
    for label,z in cohorts.items():
        check('Cash decomposition '+label,z['T0_cents']==z['paid_cents']+z['reserve_cents']-z['recoveries_cents'])
        check('Reserve075 identity '+label,z['reserve075_quarter_cent_units']==4*z['T0_cents']-z['reserve_cents'])
        check('Reserve125 identity '+label,z['reserve125_quarter_cent_units']==4*z['T0_cents']+z['reserve_cents'])
    check('Zero discarded periods',len(period)==r['selected_periods'])
    check('Selected union not sum of overlapping reasons',period.group_id.nunique()==r['selected_groups']==s.group_id.nunique())
    check('Producer and verifier new fits scores bootstrap zero',all(r[k]==v[k]==0 for k in ['new_fits','new_scores','new_bootstrap']))
    totals=cohorts['all_selected'];byline=[dict(line=line,**summary(g)) for line,g in a.groupby('line',sort=True)]
    openitems=a[a.status.eq('open')][['line','peril','T0_cents','paid_cents','reserve_cents','delay_days']].to_dict('records')
    readout={'author':'Codex','utc':now,'selected_groups':r['selected_groups'],'selected_periods':r['selected_periods'],
             'cohorts_overlap_do_not_sum':True,'cohorts':cohorts,'by_line':byline,'dominant_motor':mainfact,
             'open_claims_no_ids':openitems,'raw_cache_differences_found':False,
             'reserve_share_selected':totals['reserve_cents']/totals['T0_cents'],
             'mechanical_total_relative_change_reserve075_125':0.25*totals['reserve_cents']/totals['T0_cents'],
             'reserve_adequacy_verified':False,'new_target_or_price_adopted':False,
             'financial_snapshot_is_not_ultimate_or_transaction_history':True}
    dump(run/'readout.json',readout)
    dump(run/'readout_reconciliation.json',{'utc':now,'passed':len(checks),'failed':0,'checks':checks})
    warnings=[{'id':'B19-TRACE-SNAPSHOT','status':'open','effect':'Raw and cached selected claims agree at a single valuation, not independent transaction evidence, reserve adequacy or ultimate verification.'},
              {'id':'B19-TRACE-SELECTION','status':'open','effect':'Twelve groups selected by earlier B19 influence, not random or representative. No absence of late>365 selected losses can close C0 reporting-tail uncertainty.'},
              {'id':'B19-TRACE-PAID-TAIL','status':'open','effect':'Dominant motornew loss fully paid/closed and not affected by simple current-reserve multiplier. Valid heavy losses retained; no model promotion or deletion from this source audit.'}]
    assessment={'author':'Codex','utc':now,'status':'selected_source_trace_reconciled_ultimate_and_model_questions_open',
                'warnings':warnings,'source_trace_condition_partially_addressed_not_automatically_closed':True,
                'new_fits':0,'new_scores':0,'professional_independent_validation':False}
    dump(run/'assessment.json',assessment)
    nextstep='Audit saved standard ridgeB20 contraction, calibration and fixed B19-selected component predictions against B19 with a prior diagnostic plan, without refit/bootstrap/2024. Reconcile concurrent work first. No new price recipe warranted by a source error in this slice.'
    journal={'author':'Codex','utc':now,'decisions':[{'hypothesis':p['hypothesis'],'criterion_before':p['criteria'],
              'source_hashes':p['frozen_sources'],'result':readout,'verification':rel(run/'verification.json'),
              'consequence':'Retain every valid costly record, T0/C0, B00 and all alternatives. Source agreement does not prove reserves or ultimate. No new recipe or score. Review saved standard ridge mechanisms next if not already complete.'}],
              'next_artifact_diagnostic':nextstep}
    dump(run/'decision_journal.json',journal)
    def cu(value):return f'{value/100:,.2f}'.replace(',','_').replace('.',',').replace('_','.')
    table='\n'.join('| '+z['line']+' | '+str(z['claims'])+' | '+cu(z['paid_cents'])+' | '+cu(z['reserve_cents'])+' | '+cu(z['recoveries_cents'])+' | '+cu(z['T0_cents'])+' |' for z in byline)
    document=f'''# Trazabilidad de los siniestros que influyen en B19

Codex, corte UTC {now}. Se cotejaron {r['selected_groups']} componentes, {r['selected_periods']} periodos y {len(a)} siniestros aceptados de 2023 contra los originales. Pagos, recuperaciones, fechas, estado y asignación al periodo coinciden con los artefactos usados. El siniestro que más pesa en el deterioro de autos nuevos está cerrado y totalmente pagado. No aparece un error de origen que justifique quitarlo o modificar el objetivo.

## Qué se revisó

La selección fue registrada en el comentario 038 antes del cálculo: unión de los cinco componentes OOF más adversos de edificios y autos nuevos, y el de mayor influencia absoluta sobre cobertura de cada uno de los diez ajustes guardados de esos ramos. La unión contiene doce grupos; las razones de selección se solapan y no se suman como muestras distintas. Se conservaron todos sus periodos, incluidos los de coste cero y otros ramos. La selección es posterior a resultados de B19 y no representa al portafolio completo.

Los originales se consultaron con filtros por póliza y fecha de pérdida/periodo de 2023. La valoración fija del 31 de diciembre de 2024 admite reportes posteriores a 2023 sobre esos siniestros. No se consultaron precios, predicciones, scores, test, SEL01 o ledger de 2024. No hubo ajustes, nuevos modelos, predicciones, scores o bootstrap. B00 y todas las alternativas permanecen guardados; el catálogo activo de otras continuaciones no se sustituye.

## Pagado y reserva tienen efectos distintos

| Ramo, solo selección revisada | Siniestros | Pagado CU | Reserva CU | Recuperaciones CU | T0 neto CU |
| --- | ---: | ---: | ---: | ---: | ---: |
{table}

La selección suma {cu(totals['T0_cents'])} CU de T0, con {cu(totals['reserve_cents'])} CU de reserva, {readout['reserve_share_selected']*100:.2f}% del neto. Hay {totals['closed']} cerrados y {totals['open']} abiertos. No aparecen recuperaciones, reservas en cerrados o recuperaciones superiores a pagos en estos doce casos. No hay rechazados dentro de esta selección; eso no modifica su exclusión del objetivo general.

El componente principal de autos nuevos es una lesión corporal de 136.767,16 CU, pagada por completo y cerrada: pérdida el 1 de diciembre de 2023, reporte el 28 de enero de 2024, retraso de 58 días. No es una reserva abierta ni un reporte de más de 365 días. Multiplicar su reserva actual por 0,75 o 1,25 deja ese T0 observado igual. No prueba ausencia de incertidumbre en último, reaperturas o recuperación futura; tampoco resuelve la incertidumbre del vínculo C0 o los siniestros aún no reportados.

En los cinco incendios OOF más adversos de edificios hay un abierto con 149.180,40 CU de incurrido neto: 75.091,19 pagados y 74.089,21 de reserva. Los otros cuatro están cerrados, pagados y sin reserva actual. El incendio de 286.093,00 CU, que más influye sobre el coeficiente AD en cuatro ajustes, también está cerrado, sin reserva y reportado a los 14 días. El otro abierto de la selección es una lesión corporal de autos de 18.915,80 CU, con 3.961,29 pagados y 14.954,51 de reserva.

## Fechas y composición del objetivo

Los retrasos van de {totals['delay_min']} a {totals['delay_max']} días. Ninguno supera 365; {totals['reports_in_2024']} se reportaron durante 2024 por pérdidas de 2023. Son conceptos diferentes: año de reporte y demora superior a un año no se sustituyen. Cada siniestro seleccionado se asigna a un único intervalo original y coincide con el componente/fold guardado. Los veinte periodos concilian en centavos tanto T0 como reserva, incluyendo ceros. Esto no vuelve prospectivo el corte de valoración o la formación histórica de grupos.

El [diccionario oficial archivado](../../../Semana%202/Codex/fuentes_variables_ultimo/data_description_response.json) define pagado neto de franquicia e incurrido como pagado más estimación de caso. Se conserva `reserva = incurrido − pagado` y `T0 = incurrido − recuperaciones = pagado − recuperaciones + reserva`. Restar otra vez franquicia o sumar otra vez reserva duplicaría el ajuste. Los cálculos usan enteros de centavos y unidades de cuarto de centavo para el estrés 0,75/1,25, sin redondeo intermedio.

Aplicado solo a esta selección, el estrés mecánico cambia el total en ±{cu(totals['reserve_cents']/4)} CU, aproximadamente ±{readout['mechanical_total_relative_change_reserve075_125']*100:.2f}%. No es una estimación de adecuación, intervalo estadístico, nuevo objetivo o resultado de modelos reentrenados. Su efecto observado es cero en el siniestro principal de autos. No se extrapola ese porcentaje al resto del portafolio, a C0 o a 2025.

## Verificación y límites

Pasaron {r['passed']} controles del productor, {v['passed']} comprobaciones por otro método y {len(checks)} conciliaciones de lectura, con solapamiento. El revisor propio usa Decimal, diccionarios y datetime para reconstruir selección, importes, intervalos y balances; no reutiliza las funciones del productor para esas cuentas. Adversos de año, duplicado, identidad y orden de fechas fallan como corresponde. Una invocación real del productor con reserva sintética alterada en un centavo falla antes de la conciliación, sin ajustes o scores.

Se conservan dos fallos del comprobador: la primera construcción de una fecha sintética mezcló date y Timestamp; la segunda no resolvió el argumento relativo de la corrida antes de crear la ruta del fixture. Se corrigió solo el comprobador y se completó su tercera invocación. Las fuentes, el productor congelado y el plan no cambiaron. Esos intentos no son pases de verificación ni errores hallados en los siniestros. No se repitieron las suites GLM, remuestreo o entrenamiento anteriores.

El original y su copia son una sola fuente administrativa, no evidencia externa de transacciones ni revisión profesional independiente. Faltan movimientos históricos, fundamento actuarial de las estimaciones de caso, reaperturas y coste último. Se mantiene abierta la suficiencia de reservas y la cola no observada. No se elimina un coste válido porque concentre error; las conclusiones de B19 siguen siendo exploratorias tras búsqueda adaptativa. La exposición previa de un asunto externo se conserva declarada, sin usar sus cifras ni afirmar ceguera completa.

## Decisión y continuación

No se cambia T0/C0, una cobertura, un grupo o un modelo. Se documenta como conciliada la trazabilidad de esta selección, sin cerrar automáticamente las advertencias generales. Antes de otra tanda procede revisar la contracción y el nivel del GLM estándar regularizado B20 ya guardado frente a B19, sobre estos grupos fijados y solo 2023, con plan de diagnóstico previo y sin reajustar. La concordancia de origen no justifica más complejidad por sí sola.

Kaggle MCP releyó la [discusión 752144](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/discussion/752144): contenido semántico sin cambios, mismo mensaje y tres respuestas, sin nuevo anuncio de corrección del HOST. Se conservó un recibo de consulta; no se duplicó la fuente, repitió el cotejo de test o intentó un envío.

El [plan](../../registro/semana2_b19_traza2023_plan_v1.json), el índice `registro/semana2_b19_traza_actual.json` y la corrida privada contienen fuentes con SHA, razones de selección, conciliación por fila y comprobaciones. Las prácticas de Documentación IAA §2 y Gobernanza §§2.8–2.10 se aplican a linaje, límites y evidencia propia; no certifican aprobación humana. Foro 038/039. Sin remoto, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. La ventana nocturna termina a las 07:00 Bogotá.
'''
    doc=REPO/'docs/archivo/semana2/TRAZABILIDAD_SINIESTROS_B19_2023.md'
    with doc.open('x',encoding='utf-8') as f:f.write(document)
    body=f'''La revisión de 038 terminó con doce componentes, veinte periodos y doce siniestros aceptados de 2023. Originales y copia guardada coinciden en campos, centavos, asignación única y balances T0/reserva. No se cambió ningún dato, T0/C0 o modelo; B00 y todas las alternativas conservados. Informe: `Hackaton/Repositorio_IAA2026/docs/archivo/semana2/TRAZABILIDAD_SINIESTROS_B19_2023.md`.

El siniestro principal de autos nuevos, lesiones corporales y 136.767,16 CU, está cerrado, totalmente pagado, sin reserva/recuperaciones, con demora de 58 días. No se explica por una reserva abierta o un reporte superior a 365 días; su T0 no cambia con el multiplicador mecánico de reserva actual. La incertidumbre de C0, reapertura o último permanece. No se borra un coste válido por su influencia en el score.

En los cinco incendios OOF más adversos de edificios hay uno abierto de 149.180,40 CU, con 74.089,21 de reserva. Los otros cuatro están cerrados y pagados. El incendio de 286.093 CU que lidera la influencia local en cuatro ajustes está cerrado y se reportó a los 14 días. Otro abierto de autos tiene 18.915,80 CU y 14.954,51 de reserva. En los doce casos la reserva suma {cu(totals['reserve_cents'])} CU, {readout['reserve_share_selected']*100:.2f}% del neto; la selección no representa al portafolio.

No hay reportes de más de 365 días entre los doce; dos reportes son de 2024 por pérdidas de 2023. Se conservó valoración al 31-12-2024, sin precios, predicciones, scores o ledger de ese año. El archivo de siniestros es un snapshot, no movimientos históricos ni prueba independiente de suficiencia o último. No se cierran automáticamente esas carencias.

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones por otro método y {len(checks)} conciliaciones, con solapamiento. El flujo real rechaza la reserva sintética alterada en un centavo. Se archivan dos fallos previos del comprobador, por tipo de fecha del adverso y ruta relativa; solo se corrigió ese comprobador, sin modificar productor/plan/fuentes ni repetir suites GLM o bootstrap. Cero ajustes, nuevos modelos, predicciones, scores o remuestreos.

Próximo paso propuesto: auditar contracción y nivel de B20 estándar ya guardado frente a B19 sobre estos componentes fijados, con receta de diagnóstico previa, solo 2023 y sin reajustar. No promover, retirar, fijar lista final o añadir complejidad por esta conciliación. Kaggle 752144 conserva su contenido previo, sin fuente duplicada, nuevo cotejo o envío. Exposición anterior de un asunto externo declarada, sin uso de cifras o afirmación de ceguera completa. Revisión propia, no profesional independiente. Catálogo/contador activos y trabajo ajeno preservados; sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones.
'''
    with (ROOT/'Hackaton/Semana 2/Codex/traza_b19_2023_resultado.md').open('x',encoding='utf-8') as f:f.write(body)
    i={'id':p['id'],'author':'Codex','utc':now,'path_base':'workspace_root','status':assessment['status'],
       'run':rel(run),'documentation':rel(doc),'plan':rel(REPO/'registro/semana2_b19_traza2023_plan_v1.json'),
       'audited_policy_years':[2023],'selected_groups':r['selected_groups'],'selected_periods':r['selected_periods'],'accepted_claims':len(a),
       'reference':'W2-B00','all_alternatives_preserved':True,'new_fits':0,'new_models':0,'new_predictions':0,'new_scores':0,'new_bootstrap':0,
       'warnings':warnings,'forum_prior':p['forum_prior'],'forum_result':p['forum_result'],
       'ledger_read':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False,
       'next_artifact_diagnostic':nextstep}
    for key in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','incident_check']:
        path=run/(key+'.json');i[key]={'path':rel(path),'sha256':sha(path)}
    dump(run/'index_proposed.json',i)
    print(json.dumps({'documentation':rel(doc),'readout_checks':len(checks),'new_fits':0,'new_scores':0},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',required=True);main(Path(parser.parse_args().run))
