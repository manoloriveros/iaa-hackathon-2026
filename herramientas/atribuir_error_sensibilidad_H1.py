"""Diagnóstico descriptivo de nivel/forma; nunca genera precios oracle válidos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';P3=BASE/'sensibilidad_congelada_media_H1_20261026_v1'
OUT=BASE/'atribucion_error_P3a_H1_20261026_v1';PLAN=R/'registro/semana2_atribucion_error_P3a_H1_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd


sp=importlib.util.spec_from_file_location('H1_frozen_attribution_helpers',R/'herramientas/sensibilidad_congelada_media_H1.py')
m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);w=m.w


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def analytic_terms(y,mu):
    root=np.sqrt(mu);A=math.fsum((y/root).tolist());B=math.fsum(root.tolist());C=math.fsum(np.sqrt(y).tolist())
    assert A>0 and B>0
    current=4*A+4*B-8*C
    lower_bound=8*math.sqrt(A*B)-8*C
    regret=current-lower_bound
    assert regret>=-1e-7
    return {'observed_deviance':current,'best_scale_lower_bound_not_validated':lower_bound,'scale_regret':regret,
            'diagnostic_held_optimal_multiplier_NOT_FOR_PREDICTION':A/B}


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    files=[Path(__file__),Path(m.__file__),P3/'report.json',P3/'held_frozen_scenario_prices.parquet',m.TARGET,
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json']
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'descriptive_loss_decomposition_not_a_price_candidate',
          'motivation':'P3afixed-price aggregate gains coexist with adverse motorNB2023cells. A/Eis closer to1there but Tweedie loss worsens. Distinguish total scale from relative allocation before another model change.',
          'scope':'All48declared line/year/NBcells across all4P3ascenarios, not only adverse cells.',
          'mathematics':'For fixedmu,p=1.5, A=sum(y/sqrt(mu)),B=sum(sqrt(mu)),C=sum(sqrt(y)). D(mu)=4A+4B-8C; inf_over_scaleD=8sqrt(AB)-8C. Gain=relative_shape_gain+(baseline_scale_regret-candidate_scale_regret). The minimizing multiplierA/Buses held labels and is diagnostic only.',
          'restrictions':['No oracle-scaled price vector, model candidate, CSV, CVgain or deployment adjustment is produced',
                          'No bootstrap/CI or model selection approval from the best-scale lower bound',
                          'Do not treat this held-label lower bound as independent or prospective performance; no threshold relaxation',
                          'Relative-shape term is invariant to common scale, not a pure rank/Gini metric'],
          'readout':'Allcells and terms normalized by their existing cellnull; verify exact additivity and agreement with the recorded P3adifference. Retain computed diagnostic multiplier as explicit evidence marked inadmissible for pricing.',
          'budget':{'new_pricing_model_fits':0,'new_C0_fits':0,'new_source_inference':0,'new_prices':0,'new_bootstraps':0,
                    'diagnostic_held_optimum_scalars_not_pricing_parameters':96,'new_submissions':0},
          'limits':['Descriptive/adaptive analysis of inspected held outcomes; does not identify a causal error or a better model',
                    'A new simpler hypothesis, if warranted, must be separately preregistered and learned without held labels'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro un diagnóstico descriptivo antes de otra receta: descomponer la pérdida en nivel y reparto relativo para las48celdas de los cuatro escenarios P3a. '
                    'La motivación es que en autosNB2023el A/Ese acerca a1pero empeora Tweedie. Se usará la identidad analítica D=4A+4B-8C y el límite de mejor escala8sqrt(AB)-8C. '
                    'Ese límite y A/Busan etiquetas retenidas: son oracles descriptivos, inadmisibles para precios, validación o promoción. '
                    'No se crearán precios recalibrados, candidatos, bootstrap o envíos. Se informarán todas las celdas y se comprobará aditividad, sin escoger un multiplicador para2025. '
                    'B00/alternativas intactos,2024abierto; prioridad privada y H1diferido. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-P3A-ATRIBUCION-PREVIO',
                        '--asunto','P3a: atribución descriptiva de nivel y forma registrada, sin precios oracle',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'new_prices':0,'forum':json.loads(res.stdout)}))


def run():
    assert not (OUT/'report.json').exists() and not (OUT/'started.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==h for p,h in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    f=pd.read_parquet(P3/'held_frozen_scenario_prices.parquet');target=pd.read_parquet(m.TARGET,columns=['row_id','T0','T1_reserve075','T1_reserve125']).set_index('row_id').loc[f.row_id]
    prior=w.read(P3/'report.json');rows=[];maxerror=0.
    for name in m.SCENARIOS:
        y=target['T1_reserve075' if name=='RESERVE075' else 'T1_reserve125' if name=='RESERVE125' else 'T0'].to_numpy(float)
        oldcells={(z['line'],z['year'],z['NB']):z for z in prior['results'][name]['cells']}
        for (line,year,nb),ii in f.groupby(['line','year','new_business']).groups.items():
            ii=np.asarray(list(ii));yy=y[ii];base=f[name+'_B'].to_numpy()[ii];candidate=f[name+'_C'].to_numpy()[ii]
            a=analytic_terms(yy,base);b=analytic_terms(yy,candidate)
            den=float(m.unit(yy,np.full(len(yy),yy.mean())).sum());assert den>0
            shape=a['best_scale_lower_bound_not_validated']-b['best_scale_lower_bound_not_validated']
            level=a['scale_regret']-b['scale_regret'];delta=a['observed_deviance']-b['observed_deviance']
            assert abs(delta-shape-level)<1e-7
            expected=oldcells[(line,int(year),int(nb))]['delta_cell_null']
            error=abs(delta/den-expected);maxerror=max(maxerror,error);assert error<1e-10
            rows.append({'scenario':name,'line':line,'year':int(year),'NB':int(nb),'rows':len(ii),
                         'observed_delta_cell':delta/den,'relative_shape_component_descriptive':shape/den,
                         'scale_regret_component_descriptive':level/den,'base_diagnostic_NOT_VALIDATION':a,
                         'candidate_diagnostic_NOT_VALIDATION':b,'oracle_multipliers_inadmissible_for_prices':True})
    assert len(rows)==48
    assert all(w.sha(ROOT/path)==h for path,h in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'descriptive_level_shape_attribution_complete',
            'cells':rows,'max_recorded_delta_abs_error':maxerror,'diagnostic_held_optimum_scalar_values':96,
            'new_pricing_model_fits':0,'new_C0_fits':0,'new_source_inference':0,'new_prices':0,'new_bootstraps':0,'new_submissions':0,
            'no_oracle_price_candidate_or_validation_claim':True,'submission_allowed':False,'formal_promotion':False,
            'limits':plan['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'adverse_cells':[{'scenario':c['scenario'],'line':c['line'],'year':c['year'],'NB':c['NB'],
                                      'observed_delta':c['observed_delta_cell'],'relative_shape':c['relative_shape_component_descriptive'],
                                      'scale_regret':c['scale_regret_component_descriptive']} for c in rows if c['observed_delta_cell']<-.001],
                      'cells':48,'max_identity_error':maxerror,'new_prices':0,'new_submissions':0},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('mode',choices=['register','run']);args=parser.parse_args();{'register':register,'run':run}[args.mode]()
