"""Cierre y continuidad de una incertidumbre nueva, sin reentrenar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HOME=BASE/'A1S_nucleo_20261026_v1'
OUT=HOME/'source_tail_seed_audit'
sp=importlib.util.spec_from_file_location('tail_close_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd


def main():
    assert not (OUT/'completion_receipt.json').exists()
    report=w.read(OUT/'report.json');source=w.read(HOME/'source_models/report.json')
    assert all(w.sha(ROOT/p)==v for p,v in report['sources'].items())
    math=[]
    for line in ['motor','buildings','contents']:
        rows=pd.read_parquet(HOME/f'rows_s1_{line}.parquet',columns=['T0'])
        group=pd.read_parquet(HOME/f'partition_source/folds_{line}.parquet',columns=['source_group'])
        codes,groups=pd.factorize(group.source_group,sort=True)
        for seed in [11,12,13]:
            folder=HOME/f'source_models/{line}_seed{seed}_full'
            for kind in ['source','target']:
                name=kind+'_components.parquet'
                assert w.sha(folder/name)==source['applications'][folder.name]['outputs'][name]
            f=pd.read_parquet(folder/'source_components.parquet',columns=['conditional_source_mu'])
            y=rows.T0.to_numpy(float);mu=f.conditional_source_mu.to_numpy(float)
            a=y/np.sqrt(mu);b=np.sqrt(y*y/mu)
            assert np.allclose(a,b,rtol=1e-14,atol=1e-13)
            summed=np.bincount(codes,weights=a,minlength=len(groups))
            top=np.sort(summed)[-31:].sum()/summed.sum()
            recorded=next(x for x in report['source_tail'] if x['line']==line and x['seed']==seed)
            assert abs(top-recorded['top31_group_score_mass_share'])<1e-13
            math.append({'line':line,'seed':seed,'pinned_component_hashes':True,
                         'equivalent_scalar_expression_and_bincount_group_sum':True})
    (OUT/'integrity_and_independent_math.json').write_text(json.dumps({'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'checks':math,'new_fits':0,'new_model_inference':0,'new_scores':0},ensure_ascii=False,indent=2),encoding='utf8')
    public={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'read_only':True,
        'tool':'Kaggle MCP list_competition_topics Recent and search_notebooks ScoreDescending Everyone pageSize10',
        'competition':'iaa-ai-assisted-hackathon-2026-part-2','topics':[{'id':752091,'last_comment':'2026-10-24T03:12:10.750Z'},
            {'id':752144,'last_comment':'2026-10-24T02:57:36.893333300Z'}],
        'public_notebook_search_response':{},'new_semantic_evidence_found':False,
        'no_additional_topic_body_read_or_post':True,'new_submissions':0,'limitation':'Read-only current response, not guarantee of exhaustive public notebook availability.'}
    (OUT/'public_intel_receipt.json').write_text(json.dumps(public,ensure_ascii=False,indent=2),encoding='utf8')
    proposal_path=R/'registro/semana2_mision017_residuo_acotado_propuesta_v0.json'
    assert not proposal_path.exists()
    proposal={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'proposal_not_registered_for_fit',
        'necessity':'New full-core transfer and a two-slope standard GLM both failed. Existing source A1S tail audit does not justify removing or capping claims. Investigate a minimal additive target correction to the existing G3/T2b risk before deeper or new source architectures.',
        'uncertainty':'Whether small nonlinear main effects in the target covariates add stable information beyond the source risk and existing categorical corrections; no claim this already fixes the support/transfer problem.',
        'primary_candidate':'DT1 only; additive shallow LightGBM Tweedie residual on G3, not another source A1S mixture.',
        'model_class':'Boosted decision stumps, max_depth1/num_leaves2. No interactions, no hyperparameter grid or early stopping on held labels.',
        'parameters':{'objective':'tweedie','tweedie_variance_power':1.5,'learning_rate':.01,'num_leaves':2,'max_depth':1,
            'min_data_in_leaf':1000,'lambda_l2':100.,'max_delta_step':.1,'feature_fraction':1.,'bagging_fraction':1.,
            'cat_smooth':50,'min_data_per_group':1000,'boost_from_average':False,
            'seed':2026102613,'deterministic':True,'force_row_wise':True,'num_threads':2,'verbosity':-1},
        'fixed_rounds':60,'features':'Frozen A1S official-policy/master/history matrix, excluding raw A1S price disagreement. Optional log(G3/e_cost) must be decided in final preregistration, not after scoring. Do not add tariffs/contacts/renewal outcomes or2025claim labels.',
        'initialization':'Training-only four Tweedie-optimal year/business nuisance levels added to log(G3) init_score; nuisance never transferred. Raw stump delta only, prediction-only year/business normalization preserves G3totals.',
        'bound_pending_real_flow_verification':'If every final leaf output obeys learning_rate*max_delta_step=.001 and no hidden initial tree bias,60rounds imply abs(raw_delta)<=.06 and normalized ratios within exp(+/- .12). Verify actual saved trees and full fit/predict flow before any contest fit.',
        'technical_source':'https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#max_delta_step',
        'data':'Official historical2023/2024 and existing global group folds. Source-derived category schema fixed. Same saved outer C0/e_cost, no internal early-stopping selection and no C0reuse as independent inner validation.',
        'budget_if_registered':{'target_price_model_fits':15,'nuisance_closed_levels':60,'source_fits':0,'new_C0_fits':0,
                              'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0},
        'criterion':'Reuse unchanged delta>=.002, lower95>0,>=4positivefolds, bothyears>=0, post31>=0, worst line/year/business cell>=-.001; full-cell/cohort/level sensitivity, no formal promotion or automatic upload.',
        'before_fit_required':['Inspect prior B03/B05/T9 designs to confirm actual change and avoid duplicate training',
            'Finalize feature list without held labels; prepare schema/key/C0-membership checks',
            'Implement producer with immutable source hashes and persisted model/invocation checkpoints',
            'Synthetic complete estimator held-payload invariance, optimizer-free replay, saved tree-depth/leaf-output bound and independent metric/exposure checks',
            'Register final recipe/configuration/criterion/cost and forum comment before any contest fit or score'],
        '2024_open':True,'B00_F3c_all_alternatives_preserved':True,'goal_achieved':False}
    proposal_path.write_text(json.dumps(proposal,ensure_ascii=False,indent=2),encoding='utf8')
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Prepare DT1 bounded additive target residual proposal; first compare prior B03/B05/T9 recipes to avoid duplicates, finalize features and verify complete synthetic tree/output bound. No contest fit or score until final recipe/criterion/cost/forum registration. Do not repeat A1S/GLM/seed/tail audits.2024open;B00/F3c0.16914and quota preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':'new_A1S_tail_seed_diagnostic_complete_no_fit',
        'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'independent_checks':w.rel(OUT/'integrity_and_independent_math.json'),'public_intel':w.rel(OUT/'public_intel_receipt.json'),
        'new_model_fits':0,'new_C0_fits':0,'new_inference':0,'new_price_scores':0,'new_submissions':0,
        'next_proposal':w.rel(proposal_path),'next_proposal_sha256':w.sha(proposal_path),'next_unit':next_unit,
        '2024_open':True,'goal_achieved':False}
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'A1S_tail_seed_audit':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(A1S_tail_seed_audit=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_A1S_tail_seed_audit':w.rel(OUT/'report.json'),
             'week_2_mission017_bounded_residual_proposal':w.rel(proposal_path)},archive)
    ranges={line:[min(x['top31_group_score_mass_share'] for x in report['source_tail'] if x['line']==line),
                  max(x['top31_group_score_mass_share'] for x in report['source_tail'] if x['line']==line)]
            for line in ['motor','buildings','contents']}
    note='\n\n## Fuente A1S: cola, semillas y siguiente mecanismo, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. La auditoría usa únicamente las salidas nuevas A1S ya guardadas; cero ajustes, inferencias, curvas, calibraciones o scores nuevos. '
    note+='Los 31 grupos fuente con mayor masa y/sqrt(mu) aportan entre '+f'{100*ranges["motor"][0]:.2f}–{100*ranges["motor"][1]:.2f}% en autos, '
    note+=f'{100*ranges["buildings"][0]:.2f}–{100*ranges["buildings"][1]:.2f}% en edificios y {100*ranges["contents"][0]:.2f}–{100*ranges["contents"][1]:.2f}% en contenidos. '
    note+='Es una descripción del score de nivel dentro del ajuste fuente, no influencia causal ni validación independiente. No justifica recortar siniestros o repetir fuente con un cap arbitrario.\n\n'
    note+='En los componentes de 2025, la razón máximo/mínimo entre semillas tiene medianas entre 1,073 y 1,106 según ramo/negocio; percentiles 99 entre 1,269 y 1,516, con máximo 3,185 en una renovación de autos. '
    note+='Las semillas son perturbaciones correlacionadas, no intervalos de confianza; no se selecciona una semilla ni se crea un precio final con este diagnóstico. '
    note+='Se cotejaron hashes originales de componentes, fórmula escalar equivalente y agregación independiente por bincount para las nueve combinaciones.\n\n'
    note+='Consulta pública actual de Kaggle: solo aparecen los dos temas ya conocidos y la búsqueda de notebooks devuelve objeto vacío; no se encontró aclaración o notebook nuevo, sin afirmar búsqueda exhaustiva. '
    note+='Se conserva el recibo de lectura, sin publicación externa.\n\n'
    note+='Se prepara DT1 como propuesta, todavía sin registrar para ajuste: corrección aditiva de árboles de una división, pequeña y acotada, sobre G3/T2b. '
    note+='El siguiente paso debe demostrar que difiere materialmente de B03/B05/T9, cerrar variables y verificar con datos sintéticos el flujo y la cota de salida antes de congelar y registrar cualquier ajuste real. '
    note+='La documentación de LightGBM 4.6.0 relaciona el límite final de cada hoja con learning_rate*max_delta_step; la cota del flujo propuesto sigue pendiente de verificación de implementación. '
    note+='Fuente técnica: https://lightgbm.readthedocs.io/en/v4.6.0/Parameters.html#max_delta_step.\n\n'
    note+='B00, F3c 0,16914 y todos los adversos/alternativas permanecen.2024 abierto y adaptativo. No hay envío nuevo; la meta 0,17 sigue activa. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'; propuesta: '+w.rel(proposal_path)+'.\n'
    doc=R/'docs/semana2/MISION017_A1S_COLA_SEMILLAS_Y_CONTINUIDAD.md'
    assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_resultados.md';body.write_text(note,encoding='utf8')
    result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-A1S-COLA-SEMILLAS','--asunto','A1S: cola y semillas revisadas; siguiente propuesta aditiva acotada',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(forum=json.loads(result.stdout),document=w.rel(doc))
    w.update(phase,{'A1S_tail_seed_audit':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['A1S_tail_seed_audit']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'complete':True,'source_top31_score_mass_ranges':ranges,'new_fits':0,'forum':receipt['forum'],'next_unit':next_unit},ensure_ascii=True))


if __name__=='__main__':main()
