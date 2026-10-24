"""Audita umbrales fijos sobre celdas B20 guardadas, sin predictor o fit."""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
import hashlib
import json
import math
import sys

REPO=Path(__file__).resolve().parents[2]
ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq

read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p,d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def clean(x):
    return None if isinstance(x,float) and not math.isfinite(x) else x


def classify(cell,rule):
    fields=[('positive_groups','positive_groups_min','min'),
            ('largest_group_cost_share','largest_cost_group_share_max','max'),
            ('cost_concentration_equivalent_groups','cost_concentration_equivalent_groups_min','min')]
    criteria=[]
    for field,limit,direction in fields:
        value=clean(cell[field]);bound=rule[limit]
        passed=None if value is None else (value>=bound if direction=='min' else value<=bound)
        criteria.append({'statistic':field,'value':value,'relation':'>=' if direction=='min' else '<=',
                         'threshold':bound,'pass':passed})
    return {'pass':all(x['pass'] is True for x in criteria),
            'breaches':[x['statistic'] for x in criteria if x['pass'] is False],
            'unknown':[x['statistic'] for x in criteria if x['pass'] is None], 'criteria':criteria}


def main():
    planpath=Path(sys.argv[1]).resolve();p=read(planpath);out=ROOT/p['output_run']
    assert not (out/'report.json').exists(),'No repetir auditoría terminada.'
    assert sha(Path(__file__))==p['producer_sha256']
    for x in p['frozen_sources']:
        assert sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256']
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    assert forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1
    frozen={x['path']:ROOT/x['snapshot'] for x in p['frozen_sources']}
    source=lambda name:frozen[p['artifacts'][name]]
    cells=pq.read_table(source('calibration_cells_2023.parquet')).to_pylist()
    selected=[{k:clean(v) for k,v in x.items()} for x in cells
              if x['cohort']=='heldout' and x['model_id']=='W2-B20' and x['dimension'] in ['line_fold','line']]
    folds=sorted([x for x in selected if x['dimension']=='line_fold'],key=lambda x:(x['label'],x['band']))
    pooled=sorted([x for x in selected if x['dimension']=='line'],key=lambda x:(x['label'],x['band']))
    assert len(folds)==75 and len(pooled)==15
    assert {x['label'] for x in folds}=={line+'|'+str(k) for line in ['motor','buildings','contents'] for k in range(5)}
    assert all(sum(x['label']==line+'|'+str(k) for x in folds)==5 for line in ['motor','buildings','contents'] for k in range(5))
    rows=[]
    for cell in folds:
        line,fold=cell['label'].split('|')
        target=line=='buildings' and cell['band'] in p['gate']['heldout_bands']
        rows.append({'line':line,'fold':int(fold),**cell,'eligibility_gate':target,
                     'verdict':classify(cell,p['gate']['fold_tail']) if target else None})
    pooledrows=[]
    for cell in pooled:
        target=cell['label']=='buildings' and cell['band'] in p['gate']['heldout_bands']
        pooledrows.append({'line':cell['label'],**cell,'eligibility_gate':target,
                          'verdict':classify(cell,p['gate']['pooled_tail']) if target else None})
    targets=[x for x in rows if x['eligibility_gate']]
    pt=[x for x in pooledrows if x['eligibility_gate']]
    assert len(targets)==10 and len(pt)==2
    # No model prediction: inspect only previously saved training-rate replay.
    fields=['line','year','fold','model_fold','group_id','T0','annual_rate','band']
    fit=pq.read_table(source('training_rate_replays_2023.parquet'),columns=fields,
                      filters=[('line','==','buildings')]).to_pylist()
    assert len(fit)==4*12580 and all(x['year']==2023 and x['fold']!=x['model_fold'] for x in fit)
    cuts=read(source('band_cuts.json'))
    proxies=[]
    for k in range(5):
        f=[x for x in fit if x['model_fold']==k]
        g=defaultdict(list)
        for x in f:
            assert x['T0']>=0 and x['annual_rate']>0 and math.isfinite(x['annual_rate'])
            g[x['group_id']].append(x['T0'])
        totals=[math.fsum(v) for v in g.values()]
        cut=next(x for x in cuts if x['line']=='buildings' and x['fold']==k)
        width=math.log(cut['edges'][3])-math.log(cut['edges'][0])
        tail=[{key:clean(value) for key,value in x.items()} for x in cells if x['cohort']=='fit'
              and x['model_id']=='W2-B20' and x['dimension']=='line_fold' and x['label']=='buildings|'+str(k)
              and x['band'] in [1,5]]
        proxies.append({'fold':k,'kind':'outer_in_sample_proxy_not_inner_oof','rows':len(f),'groups':len(g),
                        'positive_groups':sum(x>0 for x in totals),'source_fold_set':sorted({x['fold'] for x in f}),
                        'P20_rate':cut['edges'][0],'P80_rate':cut['edges'][3],'log_P80_minus_P20':width,
                        'inner_spread_requirement':p['gate']['inner_calibration_each_outer_scope']['log_rate_p80_minus_p20_min'],
                        'tail_cells':tail,'proves_inner_gate':False})
    failures=[x for x in targets if not x['verdict']['pass']]
    breaches={key:sum(key in x['verdict']['breaches'] for x in targets) for key in
              ['positive_groups','largest_group_cost_share','cost_concentration_equivalent_groups']}
    result={'id':p['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
            'source_plan_sha256':sha(planpath),'inventory_cells':75,'pooled_inventory_cells':15,
            'fold_gate_cells':10,'fold_gate_passed':10-len(failures),'fold_gate_failed':len(failures),
            'failed_folds':sorted({x['fold'] for x in failures}),'breaches_by_statistic':breaches,
            'pooled_gate_passed':sum(x['verdict']['pass'] for x in pt),
            'pooled_gate_failed':sum(not x['verdict']['pass'] for x in pt),
            'support_gate':'failed' if failures or any(not x['verdict']['pass'] for x in pt) else 'not_ready_inner_evidence_missing',
            'thresholds':p['gate'],'fit_authorized':False,'can_execute':False,
            'missing_evidence':p['missing_evidence'],'inner_oof_support_established':False,
            'outer_proxy_rows_not_independent':len(fit),'new_fits':0,'new_inference':0,'parameters_estimated':0,
            'new_bootstrap':0,'new_recipes':0,'claims_or_groups_excluded':0,'thresholds_relaxed':False,
            '2024_test_closed':True,'ledger_read':False,'reference':'W2-B00','promotion':False,
            'all_alternatives_preserved':True,'professional_independent_validation':False}
    dump(out/'fold_cell_audit.json',rows)
    dump(out/'pooled_cell_audit.json',pooledrows)
    dump(out/'outer_training_proxy.json',proxies)
    dump(out/'report.json',result)
    for x in p['frozen_sources']:
        assert sha(ROOT/x['path'])==x['sha256']
    print(json.dumps({k:result[k] for k in ['fold_gate_cells','fold_gate_passed','fold_gate_failed','failed_folds','breaches_by_statistic','support_gate','new_fits']}))


if __name__=='__main__':
    main()
