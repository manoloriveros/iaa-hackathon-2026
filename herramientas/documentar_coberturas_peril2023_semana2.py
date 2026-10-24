"""Conclusión de cobertura: distinguir controles correctos de hipótesis rechazada."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    run=Path(sys.argv[1]).resolve();p=read(run/'plan_snapshot.json');r=read(run/'report.json');v=read(run/'verification.json');NOW=datetime.now(timezone.utc).isoformat()
    assert r['failed']==v['failed']==0
    den=pq.read_table(run/'denominators_and_numerators.parquet').to_pandas();cat=pq.read_table(run/'coverage_categories.parquet').to_pandas();conf=read(run/'full_cohort_candidate_conflicts.json');checks=[]
    def check(n,x):checks.append({'name':n,'pass':bool(x)})
    for cell in den.itertuples(index=False):
        g=cat[cat.line.eq(cell.line)&cat.fold.eq(cell.fold)&cat.business.eq(cell.business)&cat.peril.eq(cell.peril)]
        for field,parts in g.groupby('coverage_field'):
            ident=cell.line+str(cell.fold)+str(cell.business)+cell.peril+field
            check('Category nominal partition '+ident,np.isclose(parts.nominal_exposure.sum(),cell.nominal_all,rtol=1e-12,atol=1e-8))
            check('Category count/cost partition '+ident,np.isclose(parts.count_effective_exposure.sum(),cell.count_all,rtol=1e-12,atol=1e-8) and np.isclose(parts.cost_effective_exposure.sum(),cell.cost_all,rtol=1e-12,atol=1e-8))
            check('Category observed numerator partition '+ident,parts.claims.sum()==cell.observed_claims and parts.net_cents.sum()==cell.all_net_cents)
        check('Denominator-only inverse identity '+cell.line+str(cell.fold)+str(cell.business)+cell.peril,cell.candidate_denominator_zero if pd.isna(cell.inverse_denominator_factor_not_a_fitted_rate) else np.isclose(cell.count_retained_fraction*cell.inverse_denominator_factor_not_a_fitted_rate,1,rtol=0,atol=1e-12))
    outside=[x for x in conf if x['position']=='outside_candidate' and x['rule_changed']]
    home=[x for x in outside if x['line']!='motor'];motor=[x for x in outside if x['line']=='motor']
    check('Home masks refuted by canonical positive costs',sum(x['positive_claims'] for x in home)==30 and sum(x['net_cents'] for x in home)==2904506 and all(x['statuses']=={'closed':x['claims']} for x in home))
    check('Motor conventional masks have no observed outside claims',sum(x['claims'] for x in motor)==0)
    check('Nothing discarded from canonical target',r['claims']==4567 and all(x['all_net_cents']==x['candidate_net_cents']+x['outside_net_cents'] for x in den.to_dict('records')))
    check('Bicycle audit is categorical not mask',cat.coverage_field.eq('bicycle_cover').sum()==80 and den[den.line.eq('contents')&den.peril.eq('theft')].count_retained_fraction.eq(1).all())
    archived=ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json';page=json.loads(read(archived)['value']['content'][0]['text'])['pages'][0];text=page['content']
    terms=['cover_type','accidental_damage_cover','bicycle_cover','third_party_only','glass_hail']
    check('Dictionary fields/category names present',all(term in text for term in terms))
    evidence={'source_archive':rel(archived),'sha256':sha(archived),'page_name':page['name'],'fields_checked':terms,
        'interpretation':'Archived data description enumerates categories, optional covers and peril labels. No complete policy-wording/coverage-peril crosswalk is supplied by these field descriptions. Candidate masks remain hypotheses.',
        'bicycle_limit':'Optional bicycle cover is not a declared row-level exposure mask for the whole theft peril.'}
    (run/'dictionary_scope_evidence.json').write_text(json.dumps(evidence,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    ranges=den[den.count_retained_fraction.lt(1-1e-10)].groupby(['line','peril']).agg(retained_min=('count_retained_fraction','min'),retained_max=('count_retained_fraction','max'),inverse_min=('inverse_denominator_factor_not_a_fitted_rate','min'),inverse_max=('inverse_denominator_factor_not_a_fitted_rate','max')).reset_index().to_dict('records')
    summary={'utc':NOW,'outside_candidate':outside,'denominator_ranges':ranges,'home_outside_positive_claims':30,'home_outside_net_CU':29045.06,
        'motor_observed_compatibility_not_contract_approval':True,'no_adopted_masks':True,'no_fits_scores_or_bootstrap':True}
    result={'utc':NOW,'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks}
    for name,obj in [('readout.json',summary),('readout_reconciliation.json',result)]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
    assert result['failed']==0,[x for x in checks if not x['pass']]
    names={'motor':'Autos','buildings':'Edificios','contents':'Contenidos'};rows=[]
    for x in ranges:
        outsidecell=next(y for y in outside if y['line']==x['line'] and y['peril']==x['peril'])
        rows.append(f'| {names[x["line"]]} | {x["peril"]} | {100*x["retained_min"]:.2f}–{100*x["retained_max"]:.2f}% | {x["inverse_min"]:.3f}–{x["inverse_max"]:.3f} | {outsidecell["positive_claims"]} |')
    doc=f'''# Coberturas y denominadores de exposición por peril

Codex, corte UTC {NOW}. Diagnóstico preinscrito solo con pólizas de 2023. Se conservan B00, todas las alternativas y las curvas congeladas de cada fold. No se entrenó, predijo o puntuó un modelo nuevo.

## La exclusión de daño accidental en hogar no concuerda con el objetivo

Con la bandera accidental_damage_cover desactivada existen seis siniestros de daño accidental en edificios, con 3.175,58 CU netos, y 24 en contenidos, con 25.869,48 CU. Los treinta están cerrados, tienen coste positivo y pertenecen al objetivo canónico; no son reclamaciones repudiadas de coste cero. Su asociación con periodo, póliza, fold y fechas fue comprobada.

Por tanto, esa bandera no se impondrá como máscara de exposición cero para este peril bajo T0. El resultado establece una incompatibilidad entre esa interpretación del campo y los datos modelados; no determina si hay errores, extensiones contractuales, una clasificación más amplia del peril u otra semántica. No se cambian status, banderas, costes o asignaciones, ni se eliminan los treinta siniestros para hacer encajar la hipótesis.

## Cuánto cambiaría el denominador

Para cada ramo, negocio y fold de ajuste se comparan:

`D_all = Σ exposición_nominal × qN_peril`

`D_candidate = Σ máscara_candidata × exposición_nominal × qN_peril`

La exposición nominal viene de F0 con sus correcciones conservadas. qN es la completitud de conteo aprendida sin el fold retenido; qC se conserva aparte para coste. Contar pólizas no sustituye a sumar exposición, ni qC sustituye a qN en una frecuencia. Las máscaras son hipótesis previas: en autos, comprehensive para daño propio/glass_hail y comprehensive o third_party_fire_theft para robo; en hogar, la bandera activa para daño accidental. El resto mantiene toda exposición.

| Ramo | Peril con máscara candidata | D_candidate / D_all | D_all / D_candidate | Siniestros positivos únicos fuera |
| --- | --- | ---: | ---: | ---: |
{chr(10).join(rows)}

Los rangos incluyen negocios y cinco ajustes solapados. Las cifras inversas son razones de denominadores, no tasas estimadas ni factores de precio adoptados. Si se redujera únicamente D dejando el mismo numerador, la frecuencia n/D subiría por esa razón. Esto no corrige una incompatibilidad entre ambos conjuntos. No se estimó una frecuencia nueva ni se aplicó esa razón a predicciones.

## Qué respalda la información de cobertura

En autos no hay reclamaciones observadas fuera de las tres máscaras convencionales contrastadas. Es una condición compatible con una sensibilidad futura, no un contrato validado o prueba de riesgo futuro nulo. Las descripciones oficiales archivadas enumeran categorías de cobertura y causas; no proporcionan en esos campos una matriz contractual completa. Glass_hail además reúne dos causas bajo una etiqueta. No se adopta una exclusión automática para autos con esta evidencia.

Bicycle_cover se describe como cobertura opcional de bicicleta, mientras theft es un peril más amplio. Se auditan sus dos categorías sin transformar la bandera en una máscara para todo robo o daño accidental. La ausencia de la extensión de bicicleta no convierte toda exposición a robo en cero.

El denominador amplio actual sigue siendo una aproximación explícita y condicionada. Una eventual estimación por peril tendría que mantener coherentes el conjunto de siniestros, la exposición realmente cubierta y la composición de costes de cada fila. Cambiar solo el denominador de una tasa agregada y mantener una mezcla igual para todos no incorpora por sí mismo la cobertura individual. Tampoco es correcto usar cero reclamaciones de una celda para deducir su exclusión contractual.

## Decisión y próximo ensayo justificable

No se integra ninguna máscara ni se cambia C0, el objetivo o B00. La máscara dura de daño accidental en hogar queda bloqueada por costes positivos fuera; autos queda como hipótesis compatible pero sin validación contractual. Se conservan todos los resultados adversos y los 4.567 siniestros, con 15.297.103,84 CU netos en total.

El siguiente ensayo justificable es un GLM estándar con las coberturas admisibles como efectos principales, manteniendo T0 y C0 sin ceros impuestos: cover_type en autos y accidental_damage_cover en hogar. Responde a una omisión concreta del GLM reducido B14, no a una necesidad de árboles o interacciones. Todavía no está ajustado ni puntuado; cualquier ejecución exige su propia receta, configuración y comentario previo. No se elige un peso, una mezcla o una lista final con este diagnóstico.

## Verificación y alcance

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones y adversos focales y {result['passed']} conciliaciones de lectura, con solapamiento. Son controles técnicos; la hipótesis de la máscara de hogar falló. La cuenta separada usa diccionarios de claves y math.fsum para nominal, conteos y costes, contrasta cada categoría y conserva centavos. Los dos comandos adversos reales rechazan año sintético 2024 o cobertura ausente antes de salidas; sus fallos esperados permanecen archivados. No se repiten suites de precios o bootstrap anteriores.

Se auditaron 50.094 periodos, 30.869 componentes, 150 celdas de denominadores y 430 por categoría de cobertura. Los siniestros retenidos no entran en las vistas de ajuste. El perfil global es descriptivo y deduplicado. El contador propio sigue en 165 ajustes de precio y 285 constantes, con primeras etapas y auxiliares separados, sin incremento en esta unidad.

2024 sigue cerrado para este trabajo: no se abrieron actas, predicciones, scores o ledger, ni se hicieron precios de ese año o test. Se conserva la exposición previa de un título ajeno con métricas de confirmación, sin repetirlas o usarlas; no se afirma ceguera completa. El lector del foro solo muestra autor, ID y UTC. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Revisión técnica propia, no profesional independiente ni aprobación humana.

## Evidencia y continuidad

[Plan congelado](../../registro/semana2_coberturas_peril2023_plan_v1.json), [índice de esta revisión](../../registro/semana2_coberturas_peril2023_actual.json), [productor](../../src/semana2/auditar_coberturas_peril2023.py), [segunda cuenta y adversos](../../herramientas/verificar_coberturas_peril2023_semana2.py). Evidencia restringida y hashes: `{rel(run)}`; descripción oficial archivada en `Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json`.

Antecedente: [calendario y soporte](SOPORTE_CALENDARIO_REPORTE_2023.md). [Balance parcial de la noche](BALANCE_NOCTURNO_PARCIAL_20261024.md). La revisión aplica las prioridades de propósito/límites, segmentos y trazabilidad de las prácticas IAA del proyecto sin convertir documentación o controles propios en certificación.
'''
    docpath=REPO/'docs/semana2/COBERTURAS_Y_DENOMINADORES_PERIL_2023.md';assert not docpath.exists();docpath.write_text(doc,encoding='utf-8')
    warnings=[{'id':'COV-HOME-POSITIVE-OUTSIDE','status':'open','effect':'30closed positive accidental_damage claims and29045.06CU outside flag-based home mask. Do not exclude exposure/claims or enforce structuralzero under currentT0.'},
        {'id':'COV-MOTOR-CONTRACT','status':'open','effect':'No observed motor claim outside conventional mask in2023 is necessary compatibility only, not complete contract mapping or future no-risk proof.'},
        {'id':'COV-NUMERATOR-DENOMINATOR','status':'open','effect':'Changing denominator alone with broad numerator is incoherent for home candidate; row-specific cost composition is not achieved by aggregate rate shrink/normalization.'},
        {'id':'COV-BICYCLE','status':'open','effect':'Optional bicycle cover is not a mask for all theft. No crosswalk or structuralzero inferred.'}]
    assessment={'author':'Codex','utc':NOW,'status':'coverage_audit_verified_home_structural_mask_rejected_no_change_adopted','warnings':warnings,'new_fits_scores':0,'professional_independent_validation':False}
    journal={'author':'Codex','utc':NOW,'decisions':[{'hypothesis':p['hypothesis'],'prior_criterion':p['criterion'],'sources':p['frozen_sources'],'result':summary,'technical_verification':rel(run/'verification.json'),
        'decision':'Keep all targets/curves/B00/alternatives. Reject hardhome mask under current data; motor compatibility remains conditional. Category effect in a simple GLM is a future test, not yet executed.','professional_independent_validation':False}]}
    for name,obj in [('assessment.json',assessment),('decision_journal.json',journal)]:
        (run/name).write_text(json.dumps(obj,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    idx={'id':p['id'],'author':'Codex','utc':NOW,'path_base':'workspace_root','status':assessment['status'],'run':rel(run),'documentation':rel(docpath),
        'plan':rel(REPO/'registro/semana2_coberturas_peril2023_plan_v1.json'),'audited_policy_years':[2023],'new_fits':0,'new_scores':0,'new_bootstrap':0,
        'reference':'W2-B00','all_alternatives_preserved':True,'forum_prior':p['forum_prior'],'forum_result':'COD-S2-20261024-033','warnings':warnings,
        'home_outside_positive_claims':30,'home_outside_net_CU':29045.06,'ledger_read':False,'external2024_subject_exposure_previously_disclosed':True,
        'professional_independent_validation':False,'future_standard_GLM_coverage_effect_not_yet_preregistered_or_executed':True}
    for name in ['report','verification','readout','readout_reconciliation','assessment','decision_journal','manifest','dictionary_scope_evidence']:
        path=run/(name+'.json');idx[name]={'path':rel(path),'sha256':sha(path)}
    (run/'index_proposed.json').write_text(json.dumps(idx,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    body=f'''La revisión registrada en 032 terminó solo en 2023, sin ajustes, puntuaciones o remuestreo. B00 y todas las alternativas siguen intactos. Informe: `{rel(docpath)}`. Se conservan 50.094 periodos, 30.869 componentes y 4.567 siniestros con su objetivo neto completo.

La máscara de daño accidental de hogar no concuerda con T0: seis siniestros de edificios (3.175,58 CU) y 24 de contenidos (25.869,48 CU) tienen bandera desactivada, están cerrados y tienen coste positivo. No se borran ni se cambia su status para encajar la regla. No se restringe ese denominador ni se adopta una exclusión estructural. La semántica causal/contractual queda abierta.

Las máscaras convencionales de autos no dejan reclamaciones fuera en 2023; esto es compatibilidad observada, no validación del contrato o riesgo futuro nulo. El diccionario archivado no aporta una matriz contractual completa en sus descripciones de campo. Bicycle_cover queda solo como categoría: no se equipara con todo robo. Se publican todas las categorías, ceros y contradicciones.

La exposición retenida por las máscaras candidatas es aproximadamente 76,3–79,6% en daño propio/glass_hail de autos, 88,6–90,1% en robo, 38,7–40,3% en daño accidental de edificios y 43,4–45,3% en contenidos. Las razones inversas son de denominadores, no factores de precio ni nuevos ajustes. Reducir solo exposición sin conciliar numerador, coste y composición por fila no corrige C0. Los denominadores amplios actuales siguen siendo aproximaciones condicionadas, no coberturas individuales probadas.

Pasaron {r['passed']} controles del productor, {v['passed']} verificaciones y adversos focales y {result['passed']} conciliaciones, con solapamiento. La implementación separada usa claves, bucles y fsum; el flujo real rechaza año sintético 2024 y cobertura ausente, conservando los fallos esperados. La corrección técnica no convierte la hipótesis de hogar fallida en validada. Contador propio de precio sin cambio: 165 ajustes/285 constantes; etapas y auxiliares separados. Revisión propia, no profesional independiente.

Próximo ensayo justificable: GLM sencillo con cobertura como efecto principal (cover_type en autos y bandera de daño accidental en hogar), manteniendo T0/C0 y sin ceros impuestos. Todavía no está preinscrito, ajustado o puntuado; exigirá receta y comentario previo. No hay promoción, retiro o lista final. Se mantiene 2024 cerrado en este trabajo, sin ledger, actas, precios/predicciones/scores o test. Se conserva el incidente previo de título externo con métricas, sin repetirlas, usarlas o afirmar ceguera completa. Sin remoto, envíos, chats nuevos, delegación o cambios a otras automatizaciones.
'''
    (ROOT/'Hackaton/Semana 2/Codex/coberturas_peril2023_resultado.md').write_text(body,encoding='utf-8')
    print(json.dumps({'documentation':rel(docpath),'readout_checks':result['passed'],'failed':0,'home_outside_claims':30,'home_outside_CU':29045.06,'new_fits_scores':0}))

if __name__=='__main__':main()
