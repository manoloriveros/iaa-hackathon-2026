"""Ablación del enlace H1, sin la forma FSp REN ni aprendizaje nuevo."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import os
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'
OUT = BASE/'transferencia_H1_solo_20261026_v1'
PLAN = R/'registro/semana2_transferencia_H1_solo_plan_v1.json'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd
from threadpoolctl import threadpool_limits

sp = importlib.util.spec_from_file_location('H1_saved_transfer_statistics', R/'herramientas/auditar_transferencia_PUL2.py')
t = importlib.util.module_from_spec(sp); sp.loader.exec_module(t)
w = t.w


def dump(path, value):
    with path.open('x', encoding='utf8') as f:
        json.dump(value, f, ensure_ascii=False, indent=2)


def register():
    assert not OUT.exists() and not PLAN.exists(); OUT.mkdir()
    files = [Path(__file__), Path(t.__file__), Path(t.stats.__file__),
             t.PUL/'oof_2023_2024.parquet', t.PUL/'report.json', t.HET/'report.json',
             t.SBASE/'oof_2023_2024.parquet', t.SBASE/'report.json',
             BASE/'transferencia_PUL2_20261026_v1/report.json',
             BASE/'sensibilidad_observacion_PUL2_20261026_v2/report.json',
             BASE/'FSp_REN_G3_prod_contraste_20261026_v1/A1_original2024_proxy_prices.parquet']
    plan = {'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
            'type':'standard_H1_only_cross_base_ablation_no_admission',
            'motivation':'The local H1 correction has positive post31; adding REN FSp ultimate shape creates concentration failures in PUL2. Isolate H1 rather than tune REN powers or add capacity.',
            'primary_base':'S2 source-safe frozen complete-core ensemble',
            'secondary_bases':['S0 source-safe A1S calibrated','S1 fixed half A1S half T2b'],
            'conditional_auxiliary':'Original A1 2024 only; original observation ancestry not fully independent and not a full F3c replay',
            'operator':'T_base_i = base_i * saved_H1_i / saved_G3_i; same own-held scope, no new REN normalization or FSp shape, no tunable weight or level.',
            'comparators':'Same base uncorrected; report previously completed full PUL2 operator by reference only, no rerun or rescoring.',
            'response_metric':'Unchanged T0 period costs; Tweedie D2 power1.5,109296 held2023/2024 rows in existing global5folds.',
            'criterion':'Diagnostic readiness: positive point/lower95, both years positive, at least4positive folds, nonnegative post31 and no cell loss beyond.001. Formal minimum gain.002 remains unchanged and must be reported separately, never relaxed. Report every declared base even if adverse. No admission or upload from this audit.',
            'bootstrap':{'replicates':2000,'seed':2026102614,'unit':'saved connected global components','joint_three_bases':True,'family_interval':'exploratory Bonferroni3'},
            'level_sensitivity':[.95,1.,1.05],
            'controls':['Exact shared row/order/target/year/group/fold/cell alignment',
                        'Independent log-domain multiplication on sampled real rows',
                        'Key-shuffled real flow must recover identical prices',
                        'G3 operator algebra recovers cached H1 within floating error, with no repeated base statistics',
                        'Pin completed samefold learning/report sources, unchanged hashes; no fit or new inference'],
            'budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,
                      'new_adjusted_historical_price_rows':3*109296+59202,'new_prediction_normalizers':0,'new_final_test_prices':0,'new_CSVs':0,'new_submissions':0},
            'limits':['Adaptive ablation after inspecting PUL2 concentration; intervals are exploratory, not independent confirmation',
                      'Operator transfer assumes a proportional correction; not a complete F3c held replay or nested ensemble validation',
                      'No identification of true ultimate shares, late claims or reserve adequacy; weightedESS failure persists',
                      'Prior PUL2 adverse results and failed age extensions remain intact'],
            '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
            'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN, plan)
    body = OUT/'forum_previo.md'
    body.write_text('Codex. Registro una ablación finita de H1 sin forma FSp de renovaciones. La motivación concreta es el contraste de concentración: '
                    'H1 mantuvo mejora post31 y PUL2 no. Se multiplicarán las bases guardadas S0/S1/S2 por H1/G3, con S2 principal y A1 original2024 como proxy condicional aparte. '
                    'No se ajustarán pesos, niveles, modelos, C0 o normalizadores. Se reportarán todas las bases, intervalos conjuntos por grupos, años/folds/celdas y concentración. '
                    'El mínimo formal de ganancia0,002 sigue vigente; esta revisión no equivale a admisión aunque los controles descriptivos pasen. '
                    'Se reutilizan por referencia los resultados PUL2, sin repetir sus suites. La transferencia no suple el replay completo F3c o validación anidada, '
                    'y la revisión es adaptativa. B00, F3c0,16914 y alternativas se conservan;2024abierto, cero envíos. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res = subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                          '--id','COD-S2-20261026-MISION017-H1-SOLO-PREVIO',
                          '--asunto','Ablación H1 sola registrada: comprobar transferencia sin forma REN',
                          '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(res.stdout)}))


def correction(base, profiles):
    assert base.row_id.is_unique and profiles.row_id.is_unique
    f = base[['row_id','base']].merge(profiles[['row_id','H1','G3']], on='row_id',validate='one_to_one',how='left',sort=False)
    assert np.array_equal(base.row_id, f.row_id) and f[['base','H1','G3']].notna().all().all()
    assert np.isfinite(f[['base','H1','G3']]).all().all() and f[['base','H1','G3']].gt(0).all().all()
    return f.base.to_numpy()*(f.H1.to_numpy()/f.G3.to_numpy())


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan = w.read(PLAN); assert w.sha(PLAN) == w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==h for p,h in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    p = pd.read_parquet(t.PUL/'oof_2023_2024.parquet')
    bases = pd.read_parquet(t.SBASE/'oof_2023_2024.parquet').set_index('row_id').loc[p.row_id]
    assert len(p)==109296 and p.row_id.is_unique and set(p.year)=={2023,2024}
    for c in ['T0','year','fold','group_id','new_business']:
        assert np.array_equal(p[c],bases[c])
    identity=correction(p[['row_id','G3']].rename(columns={'G3':'base'}),p)
    assert np.allclose(identity,p.H1.to_numpy(),rtol=2e-15,atol=1e-10)
    checks=[]
    for name in ['S0','S1','S2']:
        p[name]=bases[name].to_numpy()
        base=p[['row_id',name]].rename(columns={name:'base'})
        pred=correction(base,p)
        shuffled=correction(base,p.sample(frac=1,random_state=261026))
        assert np.array_equal(pred,shuffled)
        ix=np.unique(np.linspace(0,len(p)-1,256,dtype=int))
        independent=np.array([math.exp(math.log(base.base.iloc[j])+math.log(p.H1.iloc[j])-math.log(p.G3.iloc[j])) for j in ix])
        assert np.allclose(pred[ix],independent,rtol=2e-14,atol=1e-10)
        p['T_'+name]=pred
        checks.append({'base':name,'exact_keys_target_fold_group_cell_alignment':True,
                       'shuffled_profile_keys_exact':True,'independent_log_domain_max_relative_error':float(np.max(np.abs(pred[ix]-independent)/pred[ix]))})
    raw=pd.read_parquet(BASE/'FSp_REN_G3_prod_contraste_20261026_v1/A1_original2024_proxy_prices.parquet',columns=['row_id','A1'])
    a=p.loc[p.year.eq(2024),['row_id','line','year','new_business','fold','group_id','T0','H1','G3']].merge(raw,on='row_id',validate='one_to_one')
    assert len(a)==59202
    a['T_A1']=correction(a[['row_id','A1']].rename(columns={'A1':'base'}),a)
    p.to_parquet(OUT/'held_proxy_prices_all_years.parquet',index=False)
    a.to_parquet(OUT/'held_A1_2024_proxy_prices.parquet',index=False)
    # Use exactly the previous numerical metric/bootstrap helper, with a new destination.
    t.OUT=OUT
    with threadpool_limits(limits=2):
        full=t.metrics(p,['S0','S1','S2'],plan,'source_safe_bases')
        conditional=t.metrics(a,['A1'],plan,'conditional_A1_2024')
    for row in list(full.values())+list(conditional.values()):
        row['worst_cell_delta']=min(z['delta_cell_null'] for z in row['cells'])
        row['descriptive_all_checks_passed']=all(row['direction_coherence'].values()) and row['worst_cell_delta']>=-.001
        row['formal_minimum_gain002_passed']=row['delta']>=.002
    assert all(w.sha(ROOT/path)==h for path,h in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'H1_only_transfer_ablation_complete',
            'source_safe_bases':full,'conditional_A1_2024':conditional,'numeric_controls':checks,
            'G3_identity_matches_saved_H1':True,'new_model_fits':0,'new_C0_fits':0,'new_calibrations':0,'new_source_inference':0,
            'new_prediction_normalizers':0,'new_final_test_prices':0,'new_CSVs':0,'new_submissions':0,
            'submission_allowed':False,'formal_promotion':False,'not_full_F3c_validation':True,
            'limits':plan['limits'],'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'bases':{name:{k:x[k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta','direction_coherence','descriptive_all_checks_passed','formal_minimum_gain002_passed']} for name,x in full.items()},
                      'conditional_A1_2024':{k:conditional['A1'][k] for k in ['delta','bootstrap95','post31_delta','worst_cell_delta']},
                      'new_fits':0,'new_submissions':0},ensure_ascii=True))


if __name__ == '__main__':
    parser=argparse.ArgumentParser(); parser.add_argument('mode',choices=['register','run']); args=parser.parse_args()
    {'register':register,'run':run}[args.mode]()
