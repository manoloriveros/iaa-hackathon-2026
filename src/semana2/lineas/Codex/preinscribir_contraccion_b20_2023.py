"""Diagnóstico preinscrito con grupos fijos y fuentes guardadas; cero ajustes."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def main():
    now=datetime.now(timezone.utc).isoformat();identifier='S2-B20-CONTRACCION2023-v1-20261024'
    night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=json.loads(before.decode('utf-8-sig'))
    assert not any(x['id']==identifier for x in n['completed_units']) and n['confirmation_2024_open'] is False
    old=REPO/'privado/semana2/desarrollo2023/dev8_20261024T013001Z_e8a35214';new=REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1'
    trace=REPO/'privado/semana2/desarrollo2023/traza_b19_20261024T021036Z_fe5038de'
    code=REPO/'src/semana2/diagnosticar_contraccion_b20_2023.py';helper=REPO/'src/semana2/diagnosticar_estabilidad_b19_2023.py'
    paths=[code,helper,old/'plan_snapshot.json',new/'plan_snapshot.json',new/'report.json',new/'verification.json',new/'fixture_checks.json',
           old/'oof_2023.parquet',new/'new_oof_2023.parquet',trace/'period_reconciliation_2023.parquet',trace/'selection_reasons.parquet',trace/'readout.json',
           REPO/'registro/semana2_glm_ridge_actual.json',REPO/'registro/semana2_b19_traza_actual.json']
    for line in ['motor','buildings','contents']:
        for fold in range(5):paths.extend([old/f'models/W2-B19_{line}_fold{fold}/bundle.joblib',new/f'models/{line}_fold{fold}/bundle.joblib',old/f'inputs_2023/{line}_fold{fold}.parquet'])
    folder=ROOT/'Hackaton/Semana 2/Codex'
    for name,source in [('nocturno_antes_contraccion_b20.json',night),('catalogo_antes_contraccion_b20.json',REPO/'registro/semana2_desarrollo2023_actual.json'),('contadores_antes_contraccion_b20.json',REPO/'registro/semana2_contadores_propios_actual.json')]:
        target=folder/name
        with target.open('xb') as f:f.write(source.read_bytes())
        if source!=night:paths.append(target)
    p={'id':identifier,'author':'Codex','registered_utc':now,'path_base':'workspace_root',
       'authorization_literal':'Revisar contracción y nivel de B20 frente a B19 sobre los mismos grupos; solo artefactos2023 sin reentrenar, conservar B00, registrar y publicar resultados, mantener2024 cerrado.',
       'hypothesis':'Joint ridge shrinkage may stabilize coverage coefficients while changing intercept, other effects and the level of existing predictions. Check those mechanisms on the fixed12groups/20periods; a norm reduction need not contract every coordinate or improve each group.',
       'fixed_selection':'Exactly the20 period keys and12 groups in the completed B19source trace. No reselection, extra group ranking, group removal, new cold split or resampling. Top5 priorB19adverse building and motornew scopes only as fixed overlapping readouts.',
       'criterion_before':'Same seven features/learned transform state, references, T0/C0/folds; compare standardized joint L2 and coordinate exceptions, rawscale coverage/newbusiness ratios and five-fold dispersion descriptively. Native replay only existing20heldout rows per model. Preserve any adverse shrinkage/level results; no promotion or new alpha.',
       'decomposition':'For each of20 fixed OOF rows with identical transformedZ, log(rate20/rate19)=delta_intercept+Zcoverage*delta_beta_coverage+Znewbusiness*delta_beta_newbusiness+Zother*delta_beta_other. Actual saved models only, no altered-coefficient prediction/counterfactual score. Contributions depend on common centering/reference and are not causal.',
       'level':'Existing OOF observed-bridge and conditional nominal2023 totals, global/line/fold/business/line-business context plus fixedcohorts. Distinguish a changed intercept from aggregate calibration. No normalized price or recalibration adopted.',
       'influence_readout':'Sum saved deviance19-deviance20 over the fixed20rows/full12components and compare with existing saved global net gain, no newly ranked favorable31 or new globalD2/CI. Net share can exceed100%; no probability or representative-sample claim.',
       'verification':'Separate math.fsum/dictionaries for levels/group attribution, rawscale manual linear predictor with training medians/category coding for selected20rows, native replay and term identity by another method; bad year/keys/C0, mismatchedtransform guards, blocked fit methods; one actual CLI poisoned-C0 source fails before model loading/decomposition. Do not repeat completed542/48 suite or bootstrap.',
       'code':rel(code),'coefficient_helper':rel(helper),'b19_run':rel(old),'b20_run':rel(new),
       'b19_oof':rel(old/'oof_2023.parquet'),'b20_oof':rel(new/'new_oof_2023.parquet'),
       'fixed_periods':rel(trace/'period_reconciliation_2023.parquet'),'selection_reasons':rel(trace/'selection_reasons.parquet'),
       'resources':'One finite local unit up to45min, zero training/newmodels/newprice recipes/bootstrap. Thirty savedbundles,15common transforms,20heldout native replays permodel only. No2024/test,ledger,SEL01,remote,submissions,newchats,delegation or otherautomation changes.',
       'known_previous_B20_global_delta_vs_B19':0.006912091600965537,
       'limits':'2023 adaptive research; selected groups chosen from priorB19 losses/influence, overlappingfolds notindependent CI; samebasis standardizednorm notcoordinatewise guarantees, onehot ridge depends on reference. Prior external2024 subject exposure disclosed, no fullblindness claim or use.',
       'reference':'W2-B00','all_alternatives_preserved':True,'forum_prior':'COD-S2-20261024-040','forum_result':'COD-S2-20261024-041',
       'continuity_registration_mode':'current_unit' if n.get('current_unit') is None else 'parallel_artifact_diagnostic',
       'completed_units_at_start':len(n['completed_units']),'concurrent_unit_at_start':n.get('current_unit'),
       'new_fits':0,'new_models':0,'new_price_predictions':0,'new_bootstrap':0,'ledger_read':False,'professional_independent_validation':False,
       'frozen_sources':[{'path':rel(path),'sha256':sha(path)} for path in paths]}
    plan=REPO/'registro/semana2_b20_contraccion2023_plan_v1.json'
    with plan.open('x',encoding='utf-8') as f:json.dump(p,f,ensure_ascii=False,indent=2);f.write('\n')
    text='''Respondo a la instrucción directa del participante y al siguiente paso de 039. Antes de calcular se registra `semana2_b20_contraccion2023_plan_v1.json`, con fuentes y SHA, hipótesis, criterio y configuración del diagnóstico. Se comparan únicamente artefactos B20/B19 guardados de 2023, sin ajustar modelos o C0, buscar alpha, producir una receta o repetir las suites ya completas.

Los doce componentes y veinte periodos son exactamente los de la traza terminada, sin nueva selección. La penalización de B20 afecta todos los coeficientes estandarizados y categorías, con intercepto libre; se comparará la norma conjunta, las coordenadas que crecen y los efectos de cobertura/nuevo negocio en escala original y referencias comunes. La contracción global no garantiza la individual. Los cinco ajustes solapan; su dispersión no es un intervalo independiente.

Para esos veinte registros se descompone el cambio real del logaritmo de la tasa en intercepto, cobertura, nuevo negocio y otros efectos, con las transformaciones entrenadas idénticas. Se hará replay nativo focal de las predicciones existentes, sin precios de coeficientes alterados. Se leerá el nivel observado y nominal condicional por ramo/fold/negocio, separando intercepto de calibración agregada. Se sumarán las desviaciones ya guardadas de los mismos grupos y se atribuirá su parte de la ganancia global neta ya existente; no se recalculan D² global, intervalos, bootstrap o retirada de 31 grupos.

La cuenta por otro método usará fsum/diccionarios y predictores lineales manuales en escala original. Se probarán guardas de año, claves, C0 y transformación, además de un fallo real por C0 sintético incompatible. Si surge un deterioro o un coeficiente crece, se conserva como evidencia; no se cambia el criterio para favorecer B20. No promover, retirar, congelar lista final o adoptar un factor de nivel.

B00, B19, B20 y todas las alternativas se conservan. 2024/test, precios, predicciones, scores, SEL01 y ledger siguen cerrados en este trabajo. Exposición previa de un título externo declarada, sin uso de cifras o afirmación de ceguera completa. Conclusiones exploratorias tras búsqueda adaptativa y revisión propia, no profesional independiente. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. La consulta pública de Kaggle 752144 de este ciclo no mostró cambios semánticos: no se duplica fuente, cotejo de test o envío.
'''
    with (folder/'contraccion_b20_2023_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(text)
    entry={'id':identifier,'plan':rel(plan),'status':'preregistered_saved_artifacts_no_refit','forum_preregistration':p['forum_prior']}
    if n.get('current_unit') is None:n['current_unit']=entry;n['status']='B20_saved_contraction_level_diagnostic_in_progress'
    else:n.setdefault('parallel_artifact_diagnostics',{})[identifier]=entry
    n['updated_utc']=now;tmp=night.with_name(night.name+'.contraccionb20pre.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    assert night.read_bytes()==before,'Concurrencia; plan conservado, no sobrescribir continuidad'
    os.replace(tmp,night)
    print(json.dumps({'plan':rel(plan),'sha256':sha(plan),'sources':len(paths),'prior_completed':len(n['completed_units']),'mode':p['continuity_registration_mode']}))


if __name__=='__main__':main()
