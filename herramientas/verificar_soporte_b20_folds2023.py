"""Cotejo específico del soporte con centavos/diccionarios y reglas racionales."""
from pathlib import Path
from datetime import datetime, timezone
from collections import defaultdict
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_soporte_folds_20261024_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def cents(value):
    d=Decimal(str(value))*100
    result=int(d.to_integral_value())
    if abs(d-result)>Decimal('.00001') or result<0:
        raise ValueError('Coste no representable en centavos sin modificación material.')
    return result


def stats(rows):
    costs=defaultdict(int)
    for row in rows:
        costs[row['group_id']]+=cents(row['T0'])
    total=sum(costs.values());sq=sum(x*x for x in costs.values())
    return {'rows':len(rows),'groups':len(costs),'positive_rows':sum(cents(x['T0'])>0 for x in rows),
            'positive_groups':sum(x>0 for x in costs.values()),'observed_total':total/100,
            'largest_group_cost_share':Fraction(max(costs.values()),total) if total else None,
            'cost_concentration_equivalent_groups':Fraction(total*total,sq) if sq else None}


def gate(s,rule):
    tests=[]
    for field,bound,op in [('positive_groups','positive_groups_min','ge'),
        ('largest_group_cost_share','largest_cost_group_share_max','le'),
        ('cost_concentration_equivalent_groups','cost_concentration_equivalent_groups_min','ge')]:
        value=s[field];limit=Fraction(str(rule[bound]))
        tests.append(None if value is None else value>=limit if op=='ge' else value<=limit)
    return tests


def near(a,b):
    if a is None or b is None:
        return a is None and b is None
    return math.isclose(float(a),float(b),rel_tol=1e-10,abs_tol=1e-6)


def main():
    output=RUN/'verification.json'
    assert not output.exists(),'No repetir verificación terminada.'
    p=read(RUN/'plan_snapshot.json');r=read(RUN/'report.json')
    checks=[]
    def check(name,value):
        checks.append({'name':name,'pass':bool(value)})
    snapshots={}
    for item in p['frozen_sources']:
        check('Current source '+item['path'],sha(ROOT/item['path'])==item['sha256'])
        check('Snapshot '+item['path'],sha(ROOT/item['snapshot'])==item['sha256'])
        snapshots[item['path']]=ROOT/item['snapshot']
    source=lambda key:snapshots[p['artifacts'][key]]
    held=pq.read_table(source('heldout_bands_2023.parquet'),columns=
                       ['line','market','row_id','year','fold','group_id','T0','band']).to_pylist()
    check('Full original50094rows',len(held)==50094)
    check('Only original2023scope',all(x['year']==2023 and x['fold'] in range(5) and x['band'] in range(1,6) for x in held))
    keys={(x['market'],x['line'],x['row_id']) for x in held}
    check('No duplicate/excludedperiods',len(keys)==50094)
    groupfold=defaultdict(set)
    for row in held:groupfold[row['group_id']].add(row['fold'])
    check('All30869groupssinglefold',len(groupfold)==30869 and all(len(v)==1 for v in groupfold.values()))
    foldrows=read(RUN/'fold_cell_audit.json');poolrows=read(RUN/'pooled_cell_audit.json')
    independently={}
    for cell in foldrows+poolrows:
        subset=[x for x in held if x['line']==cell['line'] and x['band']==cell['band']
                and ('fold' not in cell or x['fold']==cell['fold'])]
        s=stats(subset);ident=cell['line']+'|'+str(cell.get('fold','pooled'))+'|'+str(cell['band'])
        independently[ident]=s
        for field,value in s.items():check('Exactcell '+ident+' '+field,near(cell[field],value))
        if cell['eligibility_gate']:
            rule=p['gate']['fold_tail' if 'fold' in cell else 'pooled_tail']
            result=gate(s,rule)
            check('Rational threshold verdict '+ident,[x['pass'] for x in cell['verdict']['criteria']]==result)
            check('Conjunctive verdict '+ident,cell['verdict']['pass']==all(x is True for x in result))
        else:
            check('No thresholds outside preregistered scope '+ident,cell['verdict'] is None)
    check('75heldout+15pooled cells',len(foldrows)==75 and len(poolrows)==15)
    check('Bandpartitionallrows',sum(x['rows'] for x in foldrows)==50094)
    check('Wholecostconserved',near(sum(x['observed_total'] for x in foldrows),15297103.84))
    targets=[x for x in foldrows if x['eligibility_gate']]
    failing=[x for x in targets if not x['verdict']['pass']]
    check('10gates5fail',len(targets)==10 and len(failing)==r['fold_gate_failed']==5)
    check('Failedfolds1to4',sorted({x['fold'] for x in failing})==r['failed_folds']==[1,2,3,4])
    check('Allfoldpositivecountsadequate',all(x['positive_groups']>=p['gate']['fold_tail']['positive_groups_min'] for x in targets))
    check('Fiveconcentrationdualbreaches',all(x['verdict']['breaches']==['largest_group_cost_share','cost_concentration_equivalent_groups'] for x in failing))
    for k in range(5):
        both=[x['verdict']['pass'] for x in targets if x['fold']==k]
        check('Foldbothpassonlyzero '+str(k),all(both)==(k==0))
    # Saved outer training rates remain in-sample; no inference or inner fit.
    fit=pq.read_table(source('training_rate_replays_2023.parquet'),columns=
        ['line','year','fold','model_fold','group_id','T0','annual_rate','band'],filters=[('line','==','buildings')]).to_pylist()
    cuts=read(source('band_cuts.json'))
    proxy=read(RUN/'outer_training_proxy.json')
    for q in proxy:
        k=q['fold'];f=[x for x in fit if x['model_fold']==k];s=stats(f)
        for field in ['rows','groups','positive_groups']:
            check('Outerproxy '+str(k)+' '+field,s[field]==q[field])
        check('Outerproxy scope '+str(k),set(x['fold'] for x in f)==set(range(5))-{k}
              and all(x['year']==2023 and x['fold']!=k for x in f))
        rates=sorted(x['annual_rate'] for x in f)
        p20=rates[(len(rates)+4)//5-1];p80=rates[(len(rates)*4+4)//5-1]
        check('OuterproxyP20 '+str(k),near(p20,q['P20_rate']))
        check('OuterproxyP80 '+str(k),near(p80,q['P80_rate']))
        check('Outerproxylogspan '+str(k),near(math.log(p80/p20),q['log_P80_minus_P20']))
        check('Nevercloseinnergate '+str(k),not q['proves_inner_gate'] and q['kind']=='outer_in_sample_proxy_not_inner_oof')
        for tail in q['tail_cells']:
            ts=stats([x for x in f if x['band']==tail['band']])
            for field in ['rows','groups','positive_groups','observed_total','largest_group_cost_share','cost_concentration_equivalent_groups']:
                check('Outerproxytail '+str(k)+'/'+str(tail['band'])+' '+field,near(ts[field],tail[field]))
    check('Fit replay50320notindependent',len(fit)==r['outer_proxy_rows_not_independent']==50320)
    designidx=read(snapshots[p['indices']['design']])
    design=read(snapshots[designidx['plan']])
    for field in ['fold_tail','pooled_tail','inner_calibration_each_outer_scope']:
        check('Unchanged threshold '+field,p['gate'][field]==design['support'][field])
    # Boundary cases only; no actual-data deletion or statistical resampling.
    base={'positive_groups':10,'largest_group_cost_share':Fraction(1,2),
          'cost_concentration_equivalent_groups':Fraction(3)}
    rule=p['gate']['fold_tail']
    check('Equalityaccepted',gate(base,rule)==[True,True,True])
    for field,value,index in [('positive_groups',9,0),('largest_group_cost_share',Fraction(5001,10000),1),
                             ('cost_concentration_equivalent_groups',Fraction(29999,10000),2)]:
        d=base|{field:value};check('Boundaryfails '+field,gate(d,rule)[index] is False)
    undefined=base|{'largest_group_cost_share':None}
    check('Undefinedblocks',not all(x is True for x in gate(undefined,rule)))
    check('EmptyzeroT0supportundefined',stats([])['largest_group_cost_share'] is None)
    check('Costrepresentationrejectsnegative',cents(0.)==0)
    try:cents(-1.)
    except ValueError:rejected=True
    else:rejected=False
    check('Negativecostrejected',rejected)
    check('No new work/thresholdchange/exclusion',all(r[x]==0 for x in ['new_fits','new_inference','new_bootstrap','new_recipes','parameters_estimated','claims_or_groups_excluded'])
          and not r['thresholds_relaxed'])
    check('No eligibility/promotion',r['support_gate']=='failed' and not r['fit_authorized'] and not r['can_execute']
          and not r['inner_oof_support_established'] and not r['promotion'])
    check('Closed scope',r['2024_test_closed'] and not r['ledger_read'] and r['reference']=='W2-B00' and r['all_alternatives_preserved'])
    result={'id':p['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
            'passed':sum(x['pass'] for x in checks),'failed':sum(not x['pass'] for x in checks),'checks':checks,
            'checker_sha256':sha(Path(__file__)),'methods':'Original cents and dictionaries; exact Fraction rule comparisons; saved-rate order statistics only.',
            'new_fits':0,'new_inference':0,'new_bootstrap':0,'parameters_estimated':0,
            'support_gate':'failed','professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','support_gate','new_fits']}))
    return bool(result['failed'])


if __name__=='__main__':
    raise SystemExit(main())
