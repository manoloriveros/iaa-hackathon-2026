"""Verificación específica de scopes y fixtures de metadatos, sin C0 numérico."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
from itertools import combinations
from copy import deepcopy
import hashlib
import json
import math
import sys

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    output=RUN/'verification.json';assert not output.exists(),'Verificación existente.'
    p=read(RUN/'plan_snapshot.json');r=read(RUN/'report.json');checks=[]
    def check(name,value):checks.append({'name':name,'pass':bool(value)})
    frozen={}
    for x in p['frozen_sources']:
        check('SourceSHA '+x['path'],sha(ROOT/x['path'])==x['sha256'])
        check('SnapshotSHA '+x['path'],sha(ROOT/x['snapshot'])==x['sha256'])
        frozen[x['path']]=ROOT/x['snapshot']
    columns=['market','line','row_id','year','is_test','fold','group_id','customer_id','address_id']
    rows=[]
    for path in p['period_metadata_files'].values():rows+=pq.read_table(frozen[path],columns=columns).to_pylist()
    key=lambda x:(x['market'],x['line'],x['row_id'])
    bykey={key(x):x for x in rows}
    check('Full2023periodinventory',len(rows)==len(bykey)==r['periods']==50094
          and all(x['year']==2023 and not x['is_test'] for x in rows))
    for field in ['group_id','customer_id','address_id']:
        locations=defaultdict(set)
        for x in rows:locations[x[field]].add(x['fold'])
        check('Globalfoldisolation '+field,all(len(x)==1 for x in locations.values()))
    check('Globalrowidsunique',len({x['row_id'] for x in rows})==len(rows)==50094 and r['row_id_globally_unique_in_saved2023'])
    building=[x for x in rows if x['line']=='buildings'];claimsets={};claimunion={}
    observed=read(RUN/'observed_outer_scopes.json')
    for cfg in p['outer_scopes']:
        k=cfg['outer_fold'];f=cfg['files'];obs=next(x for x in observed if x['outer_fold']==k)
        expectedfit={key(x) for x in building if x['fold']!=k};expectedheld={key(x) for x in building if x['fold']==k}
        check('Outerpartition '+str(k),len(expectedfit)==obs['fit_periods'] and len(expectedheld)==obs['heldout_periods']
              and not expectedfit&expectedheld and len(expectedfit|expectedheld)==12580)
        allclaims=pq.read_table(frozen[f['reporting_fit_claims.parquet']]).to_pylist()
        check('Allclaims2023scope '+str(k),all(x['year']==2023 and x['fold']!=k and key(x) in bykey
              and x['fold']==bykey[key(x)]['fold'] for x in allclaims))
        claims=[x for x in allclaims if x['line']=='buildings'];claimsets[k]=claims
        for x in claims:claimunion[(x['market'],x['line'],x['claim_id'])]=x
        check('Buildingclaimsubset '+str(k),all(key(x) in expectedfit for x in claims) and len(claims)==obs['fit_claims_buildings'])
        weights=pq.read_table(frozen[f['severity_fit_weights.parquet']]).to_pylist()
        claimkeys={(x['market'],x['line'],x['claim_id']) for x in allclaims}
        weightkeys={(x['market'],x['line'],x['claim_id']) for x in weights}
        check('Allweightidentities '+str(k),len(allclaims)==len(weights)==len(claimkeys)==len(weightkeys) and claimkeys==weightkeys)
        models=read(frozen[f['reporting_models.json']]);shares=read(frozen[f['peril_cost_shares_buildings.json']])['1.0']
        for peril in p['building_perils']:
            selected=[x for x in claims if x['peril']==peril];m=models['buildings|'+peril]
            check('Storedcurveclaimcount '+str(k)+'/'+peril,len(selected)==m['n']==obs['building_claims_by_peril'][peril] and m['n']>=5)
            check('Storedweightnormalization '+str(k)+'/'+peril,math.isclose(math.fsum(x['severity_probability_weight'] for x in weights
                if x['line']=='buildings' and x['peril']==peril),len(selected),abs_tol=1e-8,rel_tol=1e-10))
            check('Storedcdfdimensions '+str(k)+'/'+peril,len(m['events'])==len(m['delay_days'])==len(m['risk_set'])
                ==len(m['count_cdf'])==len(m['count_mass'])==len(m['cost_cdf']['1.0']) and sum(m['events'])==m['n'])
            diff=[m['count_cdf'][i]-(m['count_cdf'][i-1] if i else 0.) for i in range(len(m['count_cdf']))]
            check('Masscdfidentity '+str(k)+'/'+peril,all(math.isclose(a,b,abs_tol=1e-10) for a,b in zip(diff,m['count_mass'])))
        check('Sixperilsharevector '+str(k),set(shares)==set(p['building_perils']) and all(v>=0 for v in shares.values()) and abs(sum(shares.values())-1)<1e-12)
        links=pq.read_table(frozen[f['link_2023']],columns=['market','line','row_id','year','is_test','exposure','e_cost_mix_1.0']).to_pylist()
        cached=pq.read_table(frozen[f['B20_input_2023']],columns=columns+['exposure','e_cost_mix_1.0']).to_pylist()
        lm={key(x):x for x in links};cm={key(x):x for x in cached}
        check('FullC0linkcachekeys '+str(k),set(lm)==set(cm)==expectedfit|expectedheld and len(links)==len(cached)==12580)
        check('Only2023linkcache '+str(k),all(x['year']==2023 and not x['is_test'] for x in links+cached))
        check('ExactstoredC0 '+str(k),all(cm[z]['e_cost_mix_1.0']==lm[z]['e_cost_mix_1.0'] and cm[z]['exposure']==lm[z]['exposure'] for z in lm))
        receipt=read(frozen[f['B20_receipt']])
        check('B20receiptfitcount '+str(k),receipt['fit_rows']==len(expectedfit))
        check('B20receiptweights '+str(k),math.isclose(math.fsum(math.sqrt(cm[z]['e_cost_mix_1.0']) for z in expectedfit),receipt['fit_weight_sum'],rel_tol=1e-12,abs_tol=1e-8))
    for fold in range(5):
        ids={(x['market'],x['line'],x['claim_id']) for x in claimsets[fold]}
        expected={ident for ident,x in claimunion.items() if x['fold']!=fold}
        check('Exactbuildingclaimunioncomplement '+str(fold),ids==expected)
    planned=read(RUN/'planned_inner_scopes.json')
    check('Tenuniqueplannedscopes',len(planned)==10 and {tuple(x['excluded_folds']) for x in planned}==set(combinations(range(5),2)))
    for scope in planned:
        excluded=set(scope['excluded_folds']);wanted=[x for x in building if x['fold'] not in excluded]
        counts=Counter(x['peril'] for x in claimunion.values() if x['fold'] not in excluded)
        label='/'.join(map(str,sorted(excluded)))
        check('Plannedperiodcounts '+label,len(wanted)==scope['fit_periods'])
        check('Plannedclaimcounts '+label,all(scope['claims_by_peril'][name]==counts[name] for name in p['building_perils']))
        check('Plannednotfitted '+label,not scope['numeric_C0_fitted'] and not scope['C0_parameters_exist_for_this_scope'] and scope['support_gate']=='failed')
    reuse=read(RUN/'unsafe_cache_reuse.json')
    check('Twentyorderedcases',len(reuse)==20)
    for x in reuse:
        k,j=x['outer_fold'],x['inner_eval_fold']
        check('Unsafeactualmemberships '+str(k)+'/'+str(j),x['using_outer_C0_for_inner_sees_inner_claims']==sum(y['fold']==j for y in claimsets[k])>0
            and x['using_inner_existing_OOF_C0_sees_outer_claims']==sum(y['fold']==k for y in claimsets[j])>0)
    check('Prospective60callsnotfitsdone',r['resource_enumeration']['building_reporting_peril_calls']==10*len(p['building_perils'])==60)
    check('Perilminimum14to122',r['min_planned_notifications_by_peril']=={name:min(s['claims_by_peril'][name] for s in planned) for name in p['building_perils']})
    sys.path.insert(0,str(REPO/'src/semana2'))
    from ambitos_c0_b20_2023 import validate_periods,select_scope,membership_digest
    toy=[{'market':'fixture','line':'buildings','row_id':'r'+str(k),'year':2023,'is_test':False,'fold':k,
          'group_id':'g'+str(k),'customer_id':'c'+str(k),'address_id':'a'+str(k)} for k in range(5)]
    fixtures=[]
    def fixture(name,condition):
        fixtures.append({'name':name,'pass':bool(condition)});check('Metadatafixture '+name,condition)
    fixture('validonefoldscope',len(select_scope(toy,[0])[0])==4)
    fixture('validtwofoldscope',len(select_scope(toy,[0,1])[0])==3)
    for name,mutate in [('other_year',lambda d:d[0].update(year=2024)),('testrow',lambda d:d[0].update(is_test=True)),
        ('badfold',lambda d:d[0].update(fold=5)),('duplicatekey',lambda d:d.append(dict(d[0]))),
        ('groupcrossing',lambda d:d[1].update(group_id=d[0]['group_id'])),
        ('customercrossing',lambda d:d[1].update(customer_id=d[0]['customer_id'])),
        ('addresscrossing',lambda d:d[1].update(address_id=d[0]['address_id']))]:
        sample=deepcopy(toy);mutate(sample)
        try:validate_periods(sample)
        except (ValueError,KeyError):rejected=True
        else:rejected=False
        fixture('reject_'+name,rejected)
    for name,excluded in [('duplicatefold',[0,0]),('threefolds',[0,1,2]),('unknownfold',[0,5])]:
        try:select_scope(toy,excluded)
        except ValueError:rejected=True
        else:rejected=False
        fixture('reject_'+name,rejected)
    collision=deepcopy(toy);collision.append({'market':'fixture','line':'motor','row_id':'r0','year':2023,'is_test':False,'fold':4,
        'group_id':'g-new','customer_id':'c-new','address_id':'a-new'})
    fit,_=select_scope(collision,[4]);fitkeys={key(x) for x in fit}
    fixture('compositekeyrejectscollidingclaim',key(collision[-1]) not in fitkeys and collision[-1]['row_id'] in {x['row_id'] for x in fit})
    poisoned=[dict(x,T0=1e99,reserve=9e99) for x in toy]
    fixture('selector_not_label_dependent',membership_digest(select_scope(toy,[0,1])[0])==membership_digest(select_scope(poisoned,[0,1])[0]))
    check('Namespacesdeclaredseparate',p['parameter_namespace']['reserve_rho']==1 and 'unestimated' in p['parameter_namespace']['calibration_beta'])
    check('No fittedobjectinvarianceclaim',not r['learned_object_poisoning_tested'] and not r['C0_numeric_core_implemented_here'])
    check('Supportfailedandclosed',r['current_support_gate']=='failed' and not r['fit_authorized'] and not r['can_execute']
        and r['2024_test_closed'] and not r['ledger_read'] and not r['promotion'])
    check('Noestimationorinference',all(r[x]==0 for x in ['new_fits','new_inference','new_C0_values','parameters_estimated','new_bootstrap']))
    result={'id':p['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'passed':sum(x['pass'] for x in checks),
        'failed':sum(not x['pass'] for x in checks),'checks':checks,'checker_sha256':sha(Path(__file__)),
        'metadata_fixture_count':len(fixtures),'metadata_fixtures':fixtures,
        'not_a_test_of_fitted_C0_poisoning':True,'support_gate':'failed','new_fits':0,'new_inference':0,'new_C0_values':0,
        'professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','metadata_fixture_count','support_gate','new_fits']}))
    return bool(result['failed'])


if __name__=='__main__':main()
