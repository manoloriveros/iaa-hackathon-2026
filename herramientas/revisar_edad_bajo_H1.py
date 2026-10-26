"""Disponibilidad y cambio del enlace/offset por edad; no se leen respuestas."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HET=BASE/'enlace_HET_20261026_v1'
OUT=BASE/'edad_H1_cambio_enlace_20261026_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd

sp=importlib.util.spec_from_file_location('ageH1_evidence_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
w=importlib.util.module_from_spec(sp);sp.loader.exec_module(w)


def main():
    assert not OUT.exists();OUT.mkdir()
    prices=pd.read_parquet(HET/'oof_2023_2024.parquet',columns=['row_id','line','year','new_business','fold','H1','G3']).set_index('row_id')
    paths=[Path(__file__),HET/'oof_2023_2024.parquet',HET/'report.json',BASE/'forma_ultima_PUL_20261026_v1/report.json',
           R/'registro/semana2_mision017_GLM_edad_NB_plan_v1.json',R/'herramientas/glm_edad_NB.py',
           BASE/'GLM_edad_NB_20261026_v1/synthetic.json',BASE/'GLM_edad_NB_20261026_v1/report.json']
    rows=[]
    for line in ['motor','buildings','contents']:
        agepath=BASE/f'GLM_edad_NB_20261026_v1/inputs_{line}_fold0.parquet';paths.append(agepath)
        age=pd.read_parquet(agepath,columns=['row_id','age_band']).set_index('row_id')
        for held in range(5):
            path=HET/f'inputs_{line}_fold{held}.parquet';paths.append(path)
            f=pd.read_parquet(path,columns=['row_id','line','year','fold','new_business','e_cost_scope','e_source_mix'])
            f=f.loc[f.fold.eq(held)&f.new_business.eq(1)].copy()
            f['age_band']=age.loc[f.row_id,'age_band'].to_numpy()
            f['completion_ratio']=f.e_source_mix.to_numpy()/f.e_cost_scope.to_numpy()
            f['price_offset_ratio']=prices.loc[f.row_id,'H1'].to_numpy()/prices.loc[f.row_id,'G3'].to_numpy()
            rows.append(f)
    data=pd.concat(rows,ignore_index=True)
    assert len(data)==15037 and data.row_id.is_unique
    cells=[]
    for (line,year,age),part in data.groupby(['line','year','age_band'],observed=True):
        q=part.completion_ratio.to_numpy();r=part.price_offset_ratio.to_numpy()
        cells.append({'line':line,'year':int(year),'age':str(age),'rows':len(part),
            'completion_ratio_quantiles':np.quantile(q,[0,.1,.5,.9,1]).tolist(),
            'fraction_completion_change_gt_factor1_05':float(np.mean(np.abs(np.log(q))>np.log(1.05))),
            'price_offset_ratio_quantiles':np.quantile(r,[0,.1,.5,.9,1]).tolist(),
            'fraction_price_offset_change_gt_factor1_01':float(np.mean(np.abs(np.log(r))>np.log(1.01)))})
    material=any(v['fraction_completion_change_gt_factor1_05']>=.05 for v in cells)
    assert material
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'new_link_offset_age_evidence_complete_without_outcomes',
        'rows_NB':len(data),'cells':cells,'material_observation_link_change':material,
        'not_evidence_of_new_age_effect_or_predictive_gain':True,'outcome_columns_read':False,
        'new_model_fits':0,'new_scores':0,'new_C0_fits':0,'new_final_test_prices':0,'new_submissions':0,
        'sources':{w.rel(p):w.sha(p) for p in paths},'2024_open':True,'B00_all_alternatives_preserved':True}
    (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf8')
    data.to_parquet(OUT/'NB_link_offset_age.parquet',index=False)
    old=w.read(R/'registro/semana2_mision017_GLM_edad_NB_plan_v1.json')
    config=dict(old['configuration']);config['offset']='log(saved outer H1observed-cost period price), already includes the changed risk-specific observation exposure exactly once; no extra exposure.'
    proposal={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'proposal_only_not_registered_for_fit',
        'hypothesis':'Age correction learned under the old global observation exposure failed. H1changed that exposure and offset materially in NB, including age cohorts. Retest the exact same standard GLM under this changed estimand/offset, not the same sources or a new age/penalty search.',
        'necessity_evidence':w.rel(OUT/'report.json'),'necessity_evidence_sha256':w.sha(OUT/'report.json'),
        'not_claimed':'No new age effect is established by the exposure-only audit. This is an exploratory next test, not a rescue of the old adverse result.',
        'model':'AGEH1: same5agebands,K300,objective,optimizer and year-nuisance as the archived standardGLM;15newtargetfits maximum. Offset H1, NB-only. RENunchanged.',
        'configuration':config,'criterion_combined_vs_G3':old['criterion'],'NB_addition_guard':old['NB_addition_guard'],
        'extra_guard':'Weighted2025NBincrement point nonnegative, A1original2024NBproxy point nonnegative; ESSfailure remains limitation. RENgain must not mask NBharm.',
        'combined_primary':'PUL3: PUL2renewals plus AGEH1NB. Compare combined vsG3and incremental NBvsH1/PUL2; do not choose after scoring.',
        'budget_if_registered':{'new_real_GLM_fits':15,'age_coefficients':75,'year_nuisance_intercepts':30,
             'new_source_fits':0,'new_C0_fits':0,'new_kappa_fits':0,'new_source_inference':0,'new_final_test_prices':0,'new_submissions':0},
        'before_fit':['Prepare15strictscopeinputs and validate H1/PUL2/C0/kappaancestry, protected membership and agekey alignment',
            'Verify exact archived GLMengine/config hashes; no need to rerun its unchanged synthetic optimizer suite',
            'Test the NEWH1/PUL2adapter with no-fit synthetic fixtures, zero-effectidentity and REN/NB routing; full numeric problem poisoning and independent math on newfits',
            'Freeze code/config/criterion/cost and forum before any new fit or score; preserve every old model/adverse result'],
        '2024_open':True,'B00_F3c_all_alternatives_preserved':True,'goal_achieved':False}
    pp=R/'registro/semana2_edad_H1_propuesta_v0.json';assert not pp.exists();pp.write_text(json.dumps(proposal,ensure_ascii=False,indent=2),encoding='utf8')
    stamp=datetime.now(timezone.utc);archive=OUT/'state_cuts'/stamp.strftime('%Y%m%dT%H%M%S%fZ');archive.mkdir(parents=True)
    next_unit='Implement AGEH1/PUL3adapter from proposal_v0. Reuse unchanged old ageNBGLMengine (5bands,K300) on NEWH1offset, preserve PUL2REN. First scope/ancestry and no-fit routing fixtures, then freeze recipe/criterion/cost/forum before15newfits. Keep old NBaddition, weightedNB and A1proxy guards; no depth/weight/band tuning or old-scope repeats.2024open;B00/F3c0.16914and quota preserved.'
    receipt={'author':'Codex','utc':stamp.isoformat(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'next_proposal':w.rel(pp),'next_proposal_sha256':w.sha(pp),
        'new_fits':0,'new_scores':0,'2024_open':True,'goal_achieved':False,'next_unit':next_unit}
    phase=R/'registro/semana2_mision017_fase2_actual.json'
    w.update(phase,{'utc':stamp.isoformat(),'age_H1_link_audit':receipt,'next_unit':next_unit,'active_execution':None,'active_jobs':[]},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025']
    own.update(age_H1_link_audit=receipt,next_unit=next_unit,active_jobs=[],goal_achieved=False)
    w.update(state,{'week_2_mission017_phase2_20261025':own,'week_2_mission017_phase2_execution':None},archive)
    note='\n\n## Edad NB bajo H1: cambio material de exposición y offset, 26 de octubre de 2026\n\n'
    note+='Codex, '+stamp.isoformat()+'. Se revisaron las 15.037 filas NB por ramo/año/banda de edad, leyendo solo claves, edad, exposiciones y precios guardados. '
    note+='No se leyeron respuestas ni se ajustó o puntuó un modelo. El cambio de completitud H1 supera el factor 1,05 en más del 5% de filas de varias cohortes de edad; los offsets también cambian. '
    note+='Esto acredita una entrada distinta de la antigua prueba G3, no la existencia de un efecto de edad o una mejora predictiva.\n\n'
    note+='Se propone AGEH1 con la receta GLM antigua exactamente igual, cinco bandas y K300, sobre el nuevo offset H1. PUL3 conservaría las renovaciones de PUL2 y cambiaría solo NB. '
    note+='La propuesta aún no autoriza ajuste: faltan adaptador, controles de ámbitos/ancestros, pruebas de rutas sin ajuste, receta congelada y comentario previo. '
    note+='Se conservan guardas NB, sensibilidad ponderada y proxy A1 para que el beneficio de REN no oculte daño en NB. '
    note+='No se repite la suite sintética del optimizador sin cambios; se verifica la conexión nueva.\n\n'
    note+='B00, F3c 0,16914, PUL2 y todos los resultados adversos permanecen.2024 abierto, cero envíos/cupos consumidos, meta 0,17 activa. '
    note+='Evidencia: '+w.rel(OUT/'report.json')+'; propuesta: '+w.rel(pp)+'.\n'
    doc=R/'docs/semana2/MISION017_EDAD_H1_CAMBIO_ENLACE.md';assert not doc.exists();doc.write_text(note,encoding='utf8')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    body=OUT/'forum_hallazgos.md';body.write_text(note,encoding='utf8')
    response=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
        '--id','COD-S2-20261026-MISION017-EDAD-H1-ENLACE','--asunto','Edad NB: H1 cambia exposición y offset; propuesta estándar sin ajustar',
        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    receipt.update(document=w.rel(doc),forum=json.loads(response.stdout))
    w.update(phase,{'age_H1_link_audit':receipt},archive/'post_forum')
    own=w.read(state)['week_2_mission017_phase2_20261025'];own['age_H1_link_audit']=receipt
    w.update(state,{'week_2_mission017_phase2_20261025':own},archive/'post_forum')
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_mission017_age_H1_evidence':w.rel(OUT/'report.json'),
        'week_2_mission017_age_H1_proposal':w.rel(pp)},archive/'post_forum')
    (OUT/'completion_receipt.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({'complete':True,'NB_rows':len(data),'age_cells':len(cells),'material_link_change':material,
                      'new_fits':0,'new_scores':0,'forum':receipt['forum'],'next_unit':next_unit},ensure_ascii=True))


if __name__=='__main__':main()
