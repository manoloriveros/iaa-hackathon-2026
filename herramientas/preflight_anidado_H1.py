"""Particiones y soporte para la media H1; no ajusta curvas ni precios."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
import os
import subprocess
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
BASE=R/'privado/semana2/mision017_fase2';HET=BASE/'enlace_HET_20261026_v1'
HOME=BASE/'A1S_nucleo_20261026_v1';BRIDGE=BASE/'puente_ultimo_observado_H1_20261026_v1'
OUT=BASE/'preflight_anidado_H1_20261026_v1';PLAN=R/'registro/semana2_preflight_anidado_H1_plan_v1.json'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'));sys.stdout.reconfigure(encoding='utf8')
import numpy as np
import pandas as pd


def load(name,path):
    sp=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);return m


h=load('nested_preflight_saved_components',R/'herramientas/contrastar_enlace_HET.py');w=h.w;b=h.b
CLAIMS=b.BASE/'claim_assignment_audit.parquet'


def dump(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)


def inner_fold(outer,group):
    key=f'H1-NEST-v1|{outer}|{group}'.encode('utf8')
    return int(hashlib.sha256(key).hexdigest()[:16],16)%5


def register():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir()
    files=[Path(__file__),Path(h.__file__),Path(b.__file__),Path(b.v.__file__),CLAIMS,
           BRIDGE/'report.json',BRIDGE/'held_production_bridge_prices.parquet',
           R/'registro/semana2_mision_privada_plan_v1.json',R/'registro/semana2_control_entregas_codex_actual.json']
    for line in h.LINES:
        files.append(HOME/f'rows_s2_{line}.parquet')
        for outer in range(5):files += [HET/f'inputs_{line}_fold{outer}.parquet',BRIDGE/f'bridge_{line}_fold{outer}.parquet']
    plan={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'type':'nested_membership_support_preflight_only',
          'motivation':'Complete five-member mean has not been evaluated. Exact ultimate-to-observed bridge now passed; establish protected nested scopes and support before any additional estimation.',
          'outer_groups':'Existing five connected customer/address component folds; unchanged. All historical2023/2024 held rows remain for scoring.',
          'inner_assignment':'For each outer, assign only outer-training groups: int(SHA256(UTF8(H1-NEST-v1|outer|group))[:16],16)mod5. Same group assignment across lines. No outcomes, premiums or public scores enter the assignment.',
          'member_training':'For each outer k and member j, use only groups with outer_fold!=k and inner_fold!=j. Outer held groups never enter member C0, shapes, levels or stages. Inner-excluded groups are not used to choose weights or any recipe. Five cost-member ratios are equally averaged.',
          'proposed_exact_algorithm':'Fixed protected outerS2ultimate base from P0. For each member refit standard G3/H1 closed calibrations under its own training C0; obtain ultimate H1/G3 ratio on outer held covariates with calendar exposure and ultimate prediction normalizers. Candidate observed=B_S2ultimate*mean_j(ratio_j)*q_source_outer; baseline=B_S2ultimate*q_global_outer. Outer common observation adapters are evaluation-only, already protected, never reused as an inner-independent learner.',
          'canonical_inputs':'Keep only keys/metadata, target for training-selection-after-keyfilter, frozen source f/s and annualT2b, and required shape/stage covariates. Strip inherited C0q/exposures, kappas, base_N3/G3 or other learned target prices from member inputs. Calendar and original rounded exposure remain separately explicit.',
          'preflight_checks':['Source-only f/s and annualrates identical across saved outer input copies',
                              'Global customer/address components and outer folds consistent across lines',
                              'Every inner train set disjoint from outer held and its own excluded inner groups',
                              'Training key selection before interpreting claim costs/perils/dates',
                              'At least5notifications per required peril, positive reserve075/100/125mark sums and no negative marks, valid reporting delays/truncation',
                              'Both business training cells have positive costs for existing closed estimators'],
          'support_interpretation':'Numerical minimum from current fit_reporting, not actuarial credibility or proof of private accuracy. Report raw per-peril dominant-group cost share without inventing a new threshold.',
          'failure_policy':'Keep all failed scopes and do not change hash salt, regroup, relax thresholds, borrow protected claims or silently omit a member. No estimation under this preflight.',
          'potential_learning_budget_not_authorized_by_this_preflight':{'line_outer_member_scopes':75,'primary_reporting_peril_fits':375,
                                                                        'adverse_whole_learning_reporting_peril_fits_separate':375,
                                                                        'primary_G3_H1_closed_scope_learning_calls':150,'new_source_model_fits':0},
          'current_budget':{'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,'new_source_inference':0,'new_price_predictions':0,'new_scores':0,'new_submissions':0},
          'limits':['Nested training uses about64percent of all target rows; final five-fold production members use80percent, so training-size mismatch remains',
                    '2023/2024already inspected adaptively; nested evaluation cannot restore a pristine holdout',
                    'S2is a complete feasible proxy, not delivered F3c historical replay','Fixed risk-dependent observation profile/ultimate/tail/reserve assumptions and inadequate weightedESS persist'],
          '2024_open':True,'B00_all_alternatives_preserved':True,'submission_allowed':False,
          'sources':{w.rel(p):w.sha(p) for p in files}}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md'
    body.write_text('Codex. Registro P1, únicamente particiones y soporte para un promedio H1 de cinco miembros. Se conservan los folds externos globales; '
                    'los grupos internos se asignan mediante SHA256 con salH1-NEST-v1 y módulo5, antes de ver su soporte o cualquier score. '
                    'Cada miembro excluye tanto el grupo externo como su parte interna. Se eliminarán de las entradas los precios y exposiciones C0 heredados. '
                    'Se comprobarán los mínimos numéricos de notificaciones/marcas por peril, sin ajustar curvas o modelos, y se guardarán fallos sin cambiar la partición. '
                    'La receta prevista usa S2último protegido y la media de cocientes H1último/G3último, con el puente exterior ya comprobado. '
                    'Ese adaptador exterior es solo de evaluación y no demuestra independencia interna. Antes de aprender requerirá código, controles, criterio y coste congelados aparte. '
                    'Cero precios, scores, C0, ajustes o envíos nuevos. B00/alternativas intactos,2024abierto adaptativo; prioridad privada. Plan: '+w.rel(PLAN)+'.',encoding='utf8')
    res=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex',
                        '--id','COD-S2-20261026-PRIVADA-ANIDADO-H1-PREFLIGHT-PREVIO',
                        '--asunto','P1 privado: particiones y soporte anidado H1 registrados, sin ajustes',
                        '--cuerpo',str(body)],check=True,capture_output=True,text=True,encoding='utf8')
    dump(OUT/'registration.json',{'plan_sha256':w.sha(PLAN),'forum':json.loads(res.stdout)})
    print(json.dumps({'registered':True,'new_fits':0,'forum':json.loads(res.stdout)}))


def run():
    assert not (OUT/'started.json').exists() and not (OUT/'report.json').exists()
    plan=w.read(PLAN);assert w.sha(PLAN)==w.read(OUT/'registration.json')['plan_sha256']
    assert all(w.sha(ROOT/p)==v for p,v in plan['sources'].items())
    dump(OUT/'started.json',{'utc':datetime.now(timezone.utc).isoformat(),'pid':os.getpid()})
    frames={};perils={};outputs=[]
    for line in h.LINES:
        f=pd.read_parquet(HET/f'inputs_{line}_fold0.parquet')
        pp=sorted(c.removeprefix('f_') for c in f if c.startswith('f_'));perils[line]=pp
        keep=['row_id','line','year','group_id','fold','new_business','exposure','T0','reserve','annual_raw_T2b','prior_claims_5y']
        if line=='motor':keep.append('ncb_years')
        keep+=h.g.STAGES[line]+[z+p for z in ['f_','s_'] for p in pp]
        keep=list(dict.fromkeys(keep));canonical=f[keep].copy()
        for outer in range(1,5):
            other=pd.read_parquet(HET/f'inputs_{line}_fold{outer}.parquet',columns=keep).set_index('row_id').loc[canonical.row_id].reset_index()
            for column in keep:
                assert canonical[column].reset_index(drop=True).equals(other[column].reset_index(drop=True)),(line,outer,column)
        md=pd.read_parquet(HOME/f'rows_s2_{line}.parquet').set_index('row_id').loc[canonical.row_id]
        assert not md.is_test.any() and np.array_equal(md.exposure_model,canonical.exposure)
        assert np.array_equal(np.round(md.exposure_calendar.to_numpy(),4),canonical.exposure.to_numpy())
        for col in ['customer_id','address_id','period_start','period_end','exposure_calendar','is_test']:
            canonical[col]=md[col].to_numpy()
        assert canonical.year.isin([2023,2024]).all() and canonical.row_id.is_unique
        assert not any(c.startswith(('q_','e_','y_','n_')) or c in ['base_N3','baseline_G3','e_cost_scope'] for c in canonical.columns)
        path=OUT/f'canonical_{line}.parquet';canonical.to_parquet(path,index=False)
        outputs.append({'path':w.rel(path),'sha256':w.sha(path),'rows':len(canonical)})
        frames[line]=canonical
    allrows=pd.concat(list(frames.values()),ignore_index=True);assert len(allrows)==109296 and allrows.row_id.is_unique
    for col in ['group_id','customer_id','address_id']:
        assert allrows.groupby(col).fold.nunique().max()==1
    for col in ['customer_id','address_id']:assert allrows.groupby(col).group_id.nunique().max()==1
    groups=allrows[['group_id','fold']].drop_duplicates().sort_values('group_id').reset_index(drop=True)
    inner={}
    for outer in range(5):
        assignments=groups.loc[groups.fold.ne(outer)].copy()
        assignments['inner_fold']=[inner_fold(outer,str(v)) for v in assignments.group_id]
        assert set(assignments.inner_fold)==set(range(5))
        assignments['outer_held']=outer
        path=OUT/f'inner_groups_outer{outer}.parquet';assignments.to_parquet(path,index=False)
        inner[outer]=assignments.set_index('group_id').inner_fold
        outputs.append({'path':w.rel(path),'sha256':w.sha(path),'groups':len(assignments)})
    claims=pd.read_parquet(CLAIMS);scopes=[];failures=[]
    for outer in range(5):
        for member in range(5):
            for line,f in frames.items():
                innerid=f.group_id.map(inner[outer])
                training=f.fold.ne(outer)&innerid.ne(member)
                held=f.fold.eq(outer);excluded=f.fold.ne(outer)&innerid.eq(member)
                train_groups=set(f.loc[training,'group_id']);held_groups=set(f.loc[held,'group_id'])
                assert not train_groups.intersection(held_groups) and not train_groups.intersection(f.loc[excluded,'group_id'])
                keys=set(f.loc[training,'row_id'])
                # This key filter is applied before any protected cost/date/peril interpretation.
                selected=claims.loc[claims.line.eq(line)&claims.row_id.isin(keys)].copy()
                selected=selected.loc[selected.included_in_T0].copy()
                assert set(selected.row_id).issubset(keys)
                selected['group_id']=selected.row_id.map(f.set_index('row_id').group_id)
                counts=selected.groupby('peril').size().to_dict();checks=[];peril_rows=[]
                for peril in perils[line]:
                    c=selected.loc[selected.peril.eq(peril)]
                    marks={str(z):(c.T0_cents.to_numpy(float)+(z-1)*c.reserve_cents.to_numpy(float))/100 for z in [.75,1.,1.25]}
                    valid_marks=all(np.isfinite(v).all() and (v>=0).all() and v.sum()>0 for v in marks.values())
                    if len(c):
                        loss=pd.to_datetime(c.loss_date);report=pd.to_datetime(c.report_date)
                        delay=(report-loss).dt.days;age=(pd.Timestamp('2024-12-31')-loss).dt.days
                        valid_dates=bool((delay>=0).all() and (age>=delay).all())
                    else:valid_dates=False
                    ok=len(c)>=5 and valid_marks and valid_dates
                    total=float(c.T0_cents.sum());bygroup=c.groupby('group_id').T0_cents.sum()
                    share=float(bygroup.max()/total) if total>0 else None
                    item={'peril':peril,'notifications':len(c),'minimum5_passed':len(c)>=5,
                          'all_three_mark_branches_valid':bool(valid_marks),'dates_valid':valid_dates,
                          'max_training_group_raw_net_share':share,'numerical_support_passed':ok}
                    peril_rows.append(item);checks.append(ok)
                business={str(nb):int((f.loc[training&f.new_business.eq(nb),'T0']>0).sum()) for nb in [0,1]}
                scope={'outer':outer,'member':member,'line':line,'training_rows':int(training.sum()),'outer_held_rows':int(held.sum()),
                       'inner_excluded_rows':int(excluded.sum()),'training_row_digest':b.digest(sorted(keys)),
                       'training_group_digest':b.digest(sorted(train_groups)),'outer_held_group_digest':b.digest(sorted(held_groups)),
                       'perils':peril_rows,'positive_training_rows_by_business':business,
                       'numerical_support_passed':all(checks) and min(business.values())>0,'protected_ancestry_disjoint':True}
                scopes.append(scope)
                if not scope['numerical_support_passed']:failures.append(scope)
    assert len(scopes)==75
    assert all(w.sha(ROOT/path)==v for path,v in plan['sources'].items())
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'nested_membership_support_preflight_complete',
            'all75scopes_numerically_supported':not failures,'scopes':scopes,'failed_scopes':failures,'outputs':outputs,
            'perils':perils,'partition_rule':plan['inner_assignment'],'inherited_target_learned_prices_q_and_exposures_removed':True,
            'source_profile_cross_outer_copies_exact':True,'global_customer_address_membership_consistent':True,
            'minimum_notification_count':min(z['notifications'] for s in scopes for z in s['perils']),
            'minimum_notifications_is_not_credibility':True,'new_model_fits':0,'new_C0_fits':0,'new_calibration_fits':0,
            'new_source_inference':0,'new_price_predictions':0,'new_scores':0,'new_submissions':0,
            'scope_fit_authorized_by_this_report':False,'limits':plan['limits'],'2024_open':True,
            'B00_all_alternatives_preserved':True,'submission_allowed':False,'goal_achieved':False,'plan_sha256':w.sha(PLAN)}
    dump(OUT/'report.json',report)
    print(json.dumps({'scopes':75,'all_numerically_supported':not failures,'minimum_notifications':report['minimum_notification_count'],
                      'failed':[{'outer':s['outer'],'member':s['member'],'line':s['line'],'perils':[z for z in s['perils'] if not z['numerical_support_passed']]} for s in failures],
                      'new_fits':0,'new_scores':0},ensure_ascii=True))


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('mode',choices=['register','run']);a=p.parse_args();{'register':register,'run':run}[a.mode]()
