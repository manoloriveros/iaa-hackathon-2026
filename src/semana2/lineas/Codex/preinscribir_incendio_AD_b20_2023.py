"""Preinscribe alcance focal distinto de las bandas concurrentes; no calcula modelos."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def main():
    now=datetime.now(timezone.utc).isoformat();identifier='S2-B20-INCENDIO-AD2023-v1-20261024'
    night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=json.loads(before.decode('utf-8-sig'))
    assert n['confirmation_2024_open'] is False and not any(x['id']==identifier for x in n['completed_units'])
    prep=REPO/'privado/semana2/desarrollo2023/preinscripcion_incendio_AD_20261024';prep.mkdir()
    (prep/'night_before.json').write_bytes(before)
    paths=[]
    for name in ['semana2_b20_contraccion_actual.json','semana2_b20_atribucion_actual.json','semana2_desarrollo2023_actual.json','semana2_contadores_propios_actual.json']:
        source=REPO/'registro'/name;target=prep/name;target.write_bytes(source.read_bytes());paths.append(target)
    if n.get('current_unit') and n['current_unit'].get('plan'):
        source=ROOT/n['current_unit']['plan'];target=prep/'concurrent_plan_cut.json';target.write_bytes(source.read_bytes());paths.append(target)
    a=REPO/'privado/semana2/desarrollo2023/b20_atribucion_20261024_v1a'
    c=REPO/'privado/semana2/desarrollo2023/contraccion_b20_20261024T023428Z_7f3565db'
    t=REPO/'privado/semana2/desarrollo2023/traza_b19_20261024T021036Z_fe5038de'
    s=REPO/'privado/semana2/desarrollo2023/estabilidad_b19_20261024T014815Z_9b2b1803'
    code=REPO/'src/semana2/diagnosticar_incendio_AD_b20_2023.py'
    paths.extend([code,a/'row_attribution_2023.parquet',a/'group_attribution_2023.parquet',a/'report.json',a/'verification_corrected.json',
                  c/'coefficients_original_scale.parquet',c/'focused_interpretation_receipt.json',c/'verification.json',t/'selection_reasons.parquet',
                  s/'training_group_local_influence.parquet',REPO/'privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/inputs_2023/claims_2023.parquet'])
    frames=[]
    for fold in range(5):
        f=REPO/f'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214/inputs_2023/buildings_fold{fold}.parquet';frames.append(rel(f));paths.append(f)
    p={'id':identifier,'author':'Codex','registered_utc':now,'path_base':'workspace_root',
       'authorization_literal':'Revisar concentración de la mejora de B20 en ese incendio y la inestabilidad de AD en edificios; solo artefactos2023 sin reentrenar, conservarB00, decisiones enforo y2024cerrado.',
       'hypothesis':'The93.9% is a share of a selected net gain, not global or gross improvement. Distinguish the fixed fire row and its fullcomponent, then inspect AD training composition and stored coefficients without assigning causality or refitting.',
       'fixed_cases':'Primary=priorB19rank1adversebuilding component, secondary=priorB19rank2adversebuilding component, from the same frozen selection. No reselection by B20 gains, new group ranking or changed31group analysis.',
       'concentration':'Compute explicit net/gross positive denominators by rows and completecomponents globally and in fixed12groups20periods. Two prespecified evaluation exclusions: fixed fire row or fullcomponent; reuse savedpredictions and gain, recalculate common null only for those descriptive exclusions. No physical deletion, newcandidate score, CI/bootstrap or promotion.',
       'AD_diagnostic':'Reuse originalscale AD coefficients of B19/B20 across5overlappingfolds. Tabulate12580building rows and acceptedclaim cashcosts by ADno/yes/missing, business, peril and fit/heldout view in eachfold. Nominal and fixed effectiveC0 exposure are denominators, not fitted rates or adopted prices. Retain zero/missing cells and allperils; no flagmask.',
       'influence_limits':'Check fixedfire membership in eachfit and reuse existing B19local H^-1G values only for those two components. No newHessian/modelprediction, no B20localinfluence inference, no combineddeletionbeta estimate. Heldoutfire cannot directly affect its ownfit; fold differences omit many components, notjust thisfire.',
       'verification':'Dictionary/mathfsum/Decimal money-conservation for AD/peril cells, sklearn generaldeviance for exactly the declared fixedrow/component exclusions, explicit sign/null and zero-net ratio guards. Adverse year/key/cost/ADflag and one real CLI syntheticyear source failure before outputs. Do not repeat prior suites/resampling or training.',
       'code':rel(code),'row_attribution':rel(a/'row_attribution_2023.parquet'),'group_attribution':rel(a/'group_attribution_2023.parquet'),
       'coefficients':rel(c/'coefficients_original_scale.parquet'),'selection_reasons':rel(t/'selection_reasons.parquet'),
       'B19_local_influence':rel(s/'training_group_local_influence.parquet'),'claims_2023':rel(paths[-1]),'building_frames':frames,
       'resources':'One finite localunit up to45min;0fits/model loads/newpricepredictions/bootstrap/newrecipes; no2024/test/SEL01/actas/ledger/remote/submissions/delegation/otherautomationchanges.',
       'reference':'W2-B00','all_alternatives_preserved':True,'new_fits':0,'new_price_predictions':0,'new_bootstrap':0,
       'forum_prior':'COD-S2-20261024-043','forum_result':'COD-S2-20261024-044',
       'concurrent_current_unit_cut':n.get('current_unit'),'registration_mode':'current_unit' if n.get('current_unit') is None else 'parallel_artifact_diagnostic',
       'complete_blindness_claim_allowed':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False,'ledger_read':False,
       'frozen_sources':[{'path':rel(x),'sha256':sha(x)} for x in paths]}
    # claims path is explicit: paths also contains copied metadata and per-fold frames.
    p['claims_2023']=rel(REPO/'privado/semana2/desarrollo2023/mezcla_20261024T004833Z_e8ff18e0/inputs_2023/claims_2023.parquet')
    plan=REPO/'registro/semana2_b20_incendio_AD2023_plan_v1.json'
    with plan.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
    body=ROOT/'Hackaton/Semana 2/Codex/incendio_AD_b20_2023_preinscripcion.md'
    text='''Antes de calcular se registra `semana2_b20_incendio_AD2023_plan_v1.json`, en respuesta a la instrucción directa del participante y al resultado 042. El 93,9% corresponde a ganancia neta de la selección previa, no a todo B20 o a mejora bruta. Se fija el mismo incendio (primer grupo adverso de B19 en edificios), su componente completo y el segundo incendio ya destacado. No se seleccionan por una nueva ganancia de B20.

Se separarán denominadores netos y brutos positivos, por fila y por componente, en global y en los doce grupos/veinte periodos anteriores. Dos sensibilidades descriptivas de evaluación quedan fijadas: omitir del cálculo la fila del incendio o su componente completo. Se conservan precios y registros; se reutilizan pérdidas guardadas y solo se recalcula el nulo común de esos subconjuntos. No nuevos aspirantes, retirada optimizada de grupos, intervalos, bootstrap o lista final.

Para AD de edificios se reutilizan betas en escala original de B19/B20 y las cinco vistas guardadas de 2023. Se tabularán filas, exposición nominal/C0 y coste de todos los perils por AD sí/no/ausente, negocio y ámbito de ajuste/retención. No se interpreta AD como filtro de todo T0 ni se adoptan tasas por esas celdas. Se comprueba en qué ajustes están los dos incendios y se reutiliza únicamente su influencia local ya guardada de B19. Esa aproximación no es la influencia de B20, un reajuste, una beta tras borrado o una explicación causal del fold negativo. Ningún grupo entrena el modelo que le da su predicción OOF.

La unidad concurrente de bandas de calibración tiene otro alcance: no se repiten sus bandas, replays o recalibración. Las fuentes son archivos inmutables; los índices y el plan concurrente se copian como cortes para no confundir cambios de puntero con datos alterados. Cuenta por otro método, controles adversos y un fallo real con año sintético deben conservarse, sin repetir suites ya terminadas.

Cero entrenamiento, cargas de modelos, nuevas predicciones o recetas de precio. B00, todas las alternativas, T0/C0 y siniestros se conservan. Solo 2023, con 2024/test/SEL01/actas/precios/scores/ledger cerrados. Exposición previa de asunto externo declarada, sin usar cifras ni afirmar ceguera completa. Exploración tras búsqueda adaptativa y revisión propia, no profesional independiente. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Kaggle 752144 no cambió semánticamente en esta consulta; no se duplica fuente o cotejo de test.
'''
    with body.open('x',encoding='utf-8') as f:f.write(text)
    entry={'id':identifier,'plan':rel(plan),'status':'preregistered_fixed_fire_AD_artifact_diagnostic','forum_prior':p['forum_prior']}
    if n.get('current_unit') is None:n['current_unit']=entry;n['status']='fixed_fire_AD_diagnostic_in_progress'
    else:n.setdefault('parallel_artifact_diagnostics',{})[identifier]=entry
    n['updated_utc']=now;tmp=night.with_name(night.name+'.incendioADpre.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    assert night.read_bytes()==before,'Concurrent change; retain plan/body, retry continuity only'
    os.replace(tmp,night)
    print(json.dumps({'plan':rel(plan),'sha256':sha(plan),'sources':len(paths),'mode':p['registration_mode']}))


if __name__=='__main__':main()
