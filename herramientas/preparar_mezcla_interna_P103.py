"""Contrato y ámbitos del selector común de mezcla; no implementa el selector.

Este paso enlaza componentes anteriores con sus q y grupos protegidos. No es
una prueba del flujo numérico de selección, que sigue pendiente para P104.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);a=importlib.util.module_from_spec(s);s.loader.exec_module(a);return a


p=load('p103_component_inputs',R/'herramientas/preparar_componentes_sin_G_P99.py')
scopes=load('p103_existing_inner_tables',R/'herramientas/preparar_seleccion_GLM_P84.py')
m=p.m;q=p.q;w=p.w;pd=p.pd;BASE=p.BASE
INNER=BASE/'P67_validacion_GLM_reporte_actual_20261027'
OUT=BASE/'P103_mezcla_interna_ambitos_20261027'
PLAN=R/'registro/semana2_mezcla_interna_ambitos_plan.json';INDEX=R/'registro/semana2_mezcla_interna_ambitos_actual.json'
DOC=R/'docs/semana2/PRIVADA_P103_MEZCLA_INTERNA_AMBITOS.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def verify_cache(frame,path):
    a=w.read(path)
    adverse=path.with_name('adverse_learning.json') if path.name=='learning.json' else path.with_name(path.name.replace('primary','adverse'))
    assert a==w.read(adverse)
    train=frame.loc[~frame.is_held]
    ids=m.p.b.digest(sorted(train.row_id));groups=m.p.b.digest(sorted(set(train.group_id)))
    assert a['fit_row_ids_digest']==ids and a['fit_groups_digest']==groups
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    for component in a['components'].values():assert component['fit_row_ids_digest']==ids and component['fit_groups_digest']==groups
    for stage in a['stages']:assert stage['training_row_ids_digest']==ids and stage['training_groups_digest']==groups
    return {'source':w.rel(path),'sha256':w.sha(path),'fit_ids_digest':ids,'fit_groups_digest':groups,'components':2,'Gstages':len(a['stages'])}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P102_execution']['state']=='TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent_path=R/'registro/semana2_centrado_fijo_validacion_plan.json';parent=w.read(parent_path);m.check_sources(parent)
    paths=[Path(__file__),Path(scopes.__file__),scopes.OUT/'bindings.json',R/'herramientas/preparar_GLM_reporte_actual_P66.py',
        R/'herramientas/validar_GLM_reporte_actual_P67.py',parent_path]
    for outer in range(5):
        paths.append(INNER/f'outer{outer}/inputs_committed.json')
        for member in range(5):
            paths += [INNER/f'outer{outer}/inner{member}/report_{name}.json' for name in ['primary','adverse']]
            for line in q.LINES:
                paths += [INNER/f'outer{outer}/inner{member}/{line}/base_{name}.json' for name in ['primary','adverse']]
                paths.append(scopes.OUT/f'inputs/o{outer}_i{member}_{line}.parquet')
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Only new component-to-inner-scope eligibility for a finite common source-mixture selector. No price applications, fitting, objective evaluation or numerical selection in this unit.',
        'need':'P102portable centering has negligible uncertain predictive change; P100droppingGand P98droppingtarget shapes fail. A fixed half-source allocation remains an unlearned risk-allocation choice. Test standard convex diversification with protected training-only selection before new source capacity.',
        'hypothesis':'A common training-selected mix may retain complementary source allocation with lower variance than per-line or public-tuned weights. Unknown benefit; prior source-only and fixed-mixture failures retained.',
        'future_configuration':{'weight_grid_A1S':[0.,.25,.5,.75,1.],
            'selector':'One common weight across three lines within EACH outer train. Minimize total originalT0 Tweedie1.5deviance over all five saved inner-held group folds. Roundoff ties1e-12*max(1,abs(minloss)): prefer0.5, then nearest0.5, then smaller weight. No grid extension after outcome.',
            'components':'Reuse own-scope P67inner and P65outer component shapes/levels, learned before the original half-mixture and independent of its weight. Do not borrow fullouter components inside inner learning.',
            'residual_stages':'For each nonhalf weight, relearn ALL original G stages sequentially on its OWNtrain mixture, K300 and original application year/business normalization unchanged. Mixture changes are row-dependent, so P101cell-scale invariance DOES NOT justify reusing G factors. Weight0.5 must reproduce/reuse exact original complete base by hashes.',
            'reporting':'All75 own-inner qtables and25 report objects from P84/P67, each excluding outer AND inner held groups. Same P64fullouter q/scenarios. Never reuse the P67row-wise crossfit q vector for a new inner training mask.',
            'final_algorithm':'After inner common-weight selection, apply it to full-outer own-scope components and fit G there unless exact0.5cache applies. Evaluate all five whole selectors. A future full-data producer must implement the same single full-target algorithm; no untested target-model ensemble added at delivery.',
            'no_other_changes':'Same original component A/E history/NCB K300, businessK400, source risks, target, calendar and Gfields/order/normalization. No P96capital, P102fixedcenter, line-specific weight or outer/public selection.'},
        'future_max_budget':{'new_native_fits':0,'new_component_fits':0,'inner_nonhalf_primary_Gstage_fits':400,'inner_nonhalf_adverse_Gstage_fits_separate':400,
            'final_primary_Gstage_fits_max':20,'final_adverse_Gstage_fits_separate_max':20,'primary_factor_constants_max':1890,'primary_nuisance_constants_max':1680,
            'primary_training_prediction_normalizers_max':1680,'all_adverse_parameters_separate':True,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0},
        'pending_numeric_proof':'P104must implement/synthetic-test full common-weight selector, correct new-Gtraining perweight, half-cache parity, outer/inner held poison, all inner losses and final price replay before any real fitting/scoring. This metadata binding does NOT certify that learning flow.',
        'future_acceptance':'All unchanged whole pooled/cohort/scenario/family16/level/influence criteria and separate own conditional transfer before CSV. No weaker threshold because of leaderboard position.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P103 registra solo el contrato/enlace para una selección interna común de mezcla fuente. Cuadrícula fija0/0,25/0,5/0,75/1de peso A1S, un peso para todos los ramos, elegido por cinco folds internos sobre T0; empates al50/50. Se reutilizan únicamente componentes propios del ámbito. Para pesos distintos de0,5 los factores G deben reaprenderse: la invariancia de P101 no se aplica a una mezcla que cambia por fila. El50/50 debe coincidir exactamente con los objetos completos guardados. Se enlazan75ámbitos internos y15exteriores sin aplicar modelos, ajustar o puntuar. El flujo numérico completo no está implementado: necesitará P104sintético y otro registro antes de ajustes reales. Sin público para elegir pesos, sin ampliar cuadrícula o elegir por ramo, sin nuevos árboles/CDF/2025/envíos; B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P103registered_before_weight_scope_binding_only','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P103-MEZCLA-PREVIO','P103: contrato de mezcla interna, sin ajustar o elegir pesos')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);m.check_sources(plan);binding=w.read(scopes.OUT/'bindings.json');records=[]
    for outer in range(5):
        frames={line:p.frame_for(line,outer) for line in q.LINES}
        for line in q.LINES:records.append({'kind':'outer','outer':outer,'line':line,**verify_cache(frames[line],p.OLD/f'{line}_{outer}/learning.json')})
        for member in range(5):
            tables={}
            for line in q.LINES:
                path=scopes.OUT/f'inputs/o{outer}_i{member}_{line}.parquet';assert binding['outputs'][w.rel(path)]==w.sha(path);tables[line]=pd.read_parquet(path)
            inner=scopes.inner_frames(frames,tables)
            report_path=INNER/f'outer{outer}/inner{member}/report_primary.json';report=w.read(report_path)
            assert report==w.read(report_path.with_name('report_adverse.json'))
            own_ids=sorted([rid for f in inner.values() for rid in f.loc[~f.is_held,'row_id']]);assert report['training_row_ids_digest']==m.p.b.digest(own_ids)
            for line,f in inner.items():
                assert set(f.group_id).isdisjoint(set(frames[line].loc[frames[line].is_held,'group_id']))
                path=INNER/f'outer{outer}/inner{member}/{line}/base_primary.json'
                records.append({'kind':'inner','outer':outer,'member':member,'line':line,'report_sha256':w.sha(report_path),**verify_cache(f,path)})
                if outer==member==0 and line=='motor':
                    wrong=f.copy();wrong['is_held']=~wrong.is_held
                    try:verify_cache(wrong,path)
                    except AssertionError:pass
                    else:raise AssertionError('Wrong scope must be rejected before model application')
    assert len(records)==90 and sum(z['components'] for z in records)==180
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P103ninety_component_scope_bindings_complete_numeric_selector_pending',
        'records':records,'wrong_scope_rejected_before_application':True,'numeric_learning_flow_implemented':False,'new_fits':0,'new_model_applications':0,'new_scores':0,'new_CDF_fits':0,'new_submissions':0})
    print(json.dumps({'scope_bindings':90,'component_objects':180,'numeric_selector_still_pending':True,'new_model_applications':0}))


def close():
    m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    next_unit='P104: implement exact finite common mixture-weight selector and full synthetic preflight per P103. Use all75saved own-inner q/scoped component caches, reuse0.5complete models; relearnGfor other weights because rowwise mixture changes are not cellwise scale changes. Verify whole outer/inner poison, objective/tie/cache parity and full replay without fitting. No real fit/score until separate evaluation registration. No grid/line/public rescue.'
    text='# P103: mezcla seleccionada dentro del entrenamiento\n\nCodex, '+utc()+'.\n\nQueda registrada una cuadrícula fija de cinco pesos y un selector común a todos los ramos, aprendido solo con los cinco folds internos. Se comprobó el enlace de75ámbitos internos y15exteriores:180componentes propios, claves/grupos/código/datos, reporte interno y qguardados. Un ámbito erróneo se rechazó antes de cualquier aplicación. No se repitieron curvas o la auditoría numérica histórica de q.\n\nLos componentes son anteriores a la mezcla y pueden reutilizarse en su ámbito; los factores G no pueden trasladarse a otro peso como si el cambio fuera una constante por celda. Deben reaprenderse para cada peso distinto de50/50; ese comparador debe reutilizarse exactamente. El resultado público no decide pesos, cuadrícula o umbrales.\n\nEste paso solo valida el enlace de artefactos. El selector, sus nuevas etapas G y su flujo numérico completo todavía no están implementados o probados. Se exige preflight sintético P104, luego registro separado de evaluación real con todas las guardas y transferencia antes de cualquier CSV. Cero ajustes, aplicaciones de modelos, scores, CDF o envíos. B00 y adversos preservados,2024abierto adaptativo, fuentes/snapshots/valoración/cola y búsqueda adaptativa siguen siendo límites; sin mejora privada demostrada o revisión independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'numeric_learning_flow_implemented':False,'new_fits':0,'new_model_applications':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P103-MEZCLA-RESULTADO','P103: ámbitos enlazados, selector numérico pendiente')}
    cut=R/'privado'/('corte_P103_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P103'),(R/'registro/semana2_mision_privada_actual.json','P103')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P103=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P103: mezcla interna, ámbitos\n\nCodex, '+receipt['utc']+'. Noventa ámbitos/180componentes enlazados sin aplicación, ajuste o score. Selector numérico aún pendiente, no certificado por metadatos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_inner_mix_scope_index':w.rel(INDEX),'week_2_private_inner_mix_scope_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
