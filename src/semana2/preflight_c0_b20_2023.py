"""Preflight de procedencia y pertenencias; no reestima C0 ni produce precios."""
from pathlib import Path
from datetime import datetime,timezone
from collections import defaultdict,Counter
from itertools import combinations
import ast
import hashlib
import json
import math
import sys

REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()


def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def main():
    pp=Path(sys.argv[1]).resolve();p=read(pp);out=ROOT/p['output_run']
    assert not (out/'report.json').exists(),'Preflight existente.'
    assert sha(Path(__file__))==p['producer_sha256'] and sha(ROOT/p['scope_module'])==p['scope_module_sha256']
    for x in p['frozen_sources']:assert sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256']
    forum=(ROOT/'Hackaton/Semana 2/Foro/FORO.md').read_bytes()
    assert forum.count(('<!-- aporte:'+p['forum_prior']+' -->').encode())==1
    from ambitos_c0_b20_2023 import key,validate_periods,select_scope,membership_digest
    frozen={x['path']:ROOT/x['snapshot'] for x in p['frozen_sources']}
    path=lambda value:frozen[value]
    cols=['market','line','row_id','year','is_test','fold','group_id','customer_id','address_id']
    periods=[]
    for line,source in p['period_metadata_files'].items():
        rows=pq.read_table(path(source),columns=cols).to_pylist()
        assert all(x['line']==line for x in rows)
        periods+=rows
    validate_periods(periods)
    assert len(periods)==50094 and len({x['group_id'] for x in periods})==30869
    pm={key(x):x for x in periods};building=[x for x in periods if x['line']=='buildings']
    rowids_unique=len({x['row_id'] for x in periods})==len(periods)
    scopes=[];claim_union={};scope_claims={};claim_appearances=defaultdict(set);perilset=set(p['building_perils'])
    for scope in p['outer_scopes']:
        k=scope['outer_fold'];f=scope['files'];fit,held=select_scope(periods,[k])
        claims=pq.read_table(path(f['reporting_fit_claims.parquet'])).to_pylist()
        weights=pq.read_table(path(f['severity_fit_weights.parquet'])).to_pylist()
        assert all(x['year']==2023 and x['fold']!=k and x['fold']==pm[key(x)]['fold'] for x in claims)
        ck=lambda x:(x['market'],x['line'],x['claim_id'])
        cm={ck(x):x for x in claims};wm={ck(x):x for x in weights}
        assert len(cm)==len(claims)==len(weights)==len(wm) and set(cm)==set(wm)
        for ident,row in cm.items():
            assert ident not in claim_union or claim_union[ident]==row
            claim_union[ident]=row
            claim_appearances[ident].add(k)
        for ident,row in wm.items():
            assert all(row[z]==cm[ident][z] for z in ['market','line','row_id','fold','year','peril'])
            assert math.isfinite(row['severity_probability_weight']) and row['severity_probability_weight']>=0
        bc=[x for x in claims if x['line']=='buildings'];scope_claims[k]=bc
        fitkeys={key(x) for x in fit};heldkeys={key(x) for x in held}
        assert all(key(x) in fitkeys and key(x) not in heldkeys for x in bc)
        models=read(path(f['reporting_models.json']));shares=read(path(f['peril_cost_shares_buildings.json']))['1.0']
        assert set(shares)==perilset and all(math.isfinite(v) and v>=0 for v in shares.values())
        assert math.isclose(math.fsum(shares.values()),1,abs_tol=1e-12)
        counts=Counter(x['peril'] for x in bc)
        assert set(counts)==perilset
        for peril in sorted(perilset):
            m=models['buildings|'+peril]
            assert m['n']==counts[peril] and m['n']>=5
            ws=math.fsum(x['severity_probability_weight'] for x in weights if x['line']=='buildings' and x['peril']==peril)
            assert math.isclose(ws,m['n'],rel_tol=1e-11,abs_tol=1e-9)
            assert sum(m['events'])==m['n'] and len(m['count_cdf'])==len(m['delay_days'])==len(m['count_mass'])
            for curve in [m['count_cdf'],m['cost_cdf']['1.0']]:
                assert all(math.isfinite(v) and 0<=v<=1+1e-12 for v in curve)
                assert all(a<=b+1e-12 for a,b in zip(curve,curve[1:])) and abs(curve[-1]-1)<1e-10
            assert m['mean_net_mark']['1.0']>0
        link=pq.read_table(path(f['link_2023']),columns=['market','line','row_id','year','is_test','exposure','e_cost_mix_1.0']).to_pylist()
        cached=pq.read_table(path(f['B20_input_2023']),columns=cols+['exposure','e_cost_mix_1.0']).to_pylist()
        lm={key(x):x for x in link};cache={key(x):x for x in cached}
        assert len(lm)==len(link)==len(cache)==len(cached)==len(building)==12580 and set(lm)==set(cache)=={key(x) for x in building}
        for ident,row in cache.items():
            assert row['year']==2023 and not row['is_test'] and lm[ident]['year']==2023 and not lm[ident]['is_test']
            assert all(row[z]==pm[ident][z] for z in cols)
            assert row['exposure']==lm[ident]['exposure'] and row['e_cost_mix_1.0']==lm[ident]['e_cost_mix_1.0']
            assert math.isfinite(row['e_cost_mix_1.0']) and row['e_cost_mix_1.0']>0
        receipt=read(path(f['B20_receipt']))
        assert receipt['fold']==k and receipt['line']=='buildings' and receipt['fit_rows']==len(fit)
        weightsum=math.fsum(math.sqrt(cache[key(x)]['e_cost_mix_1.0']) for x in fit)
        assert math.isclose(weightsum,receipt['fit_weight_sum'],rel_tol=1e-12,abs_tol=1e-8)
        scopes.append({'outer_fold':k,'fit_periods':len(fit),'heldout_periods':len(held),'fit_groups':len({x['group_id'] for x in fit}),
            'heldout_groups':len({x['group_id'] for x in held}),'fit_claims_all_lines':len(claims),'fit_claims_buildings':len(bc),
            'building_claims_by_peril':dict(sorted(counts.items())),'fit_membership_sha256':membership_digest(fit),
            'heldout_membership_sha256':membership_digest(held),'customer_overlap':0,'address_overlap':0,'group_overlap':0,
            'C0_link_matches_B20_cache':True,'receipt_weight_sum_matches':True,'existing_outer_exclusion_reconciled':True})
    # Metadata inventory only: no estimator or future C0 value is created.
    union_building=[x for x in claim_union.values() if x['line']=='buildings']
    for ident,claim in claim_union.items():
        assert claim_appearances[ident]==set(range(5))-{claim['fold']}
    planned=[]
    for a,b in combinations(range(5),2):
        fit,held=select_scope(periods,[a,b]);claims=[x for x in union_building if x['fold'] not in [a,b]]
        counts=Counter(x['peril'] for x in claims)
        planned.append({'excluded_folds':[a,b],'training_folds':sorted(set(range(5))-{a,b}),
            'fit_periods':len(fit),'heldout_periods':len(held),'fit_groups':len({x['group_id'] for x in fit}),
            'fit_membership_sha256':membership_digest(fit),'heldout_membership_sha256':membership_digest(held),
            'claims_by_peril':{name:counts[name] for name in sorted(perilset)},
            'reporting_min5_notifications_met':all(counts[name]>=5 for name in perilset),
            'C0_parameters_exist_for_this_scope':False,'numeric_C0_fitted':False,'support_gate':'failed'})
    reuse=[]
    for k in range(5):
        for j in range(5):
            if k==j:continue
            seen_inner=sum(x['fold']==j for x in scope_claims[k])
            seen_outer=sum(x['fold']==k for x in scope_claims[j])
            reuse.append({'outer_fold':k,'inner_eval_fold':j,
                'required_training_folds':sorted(set(range(5))-{k,j}),
                'using_outer_C0_for_inner_sees_inner_claims':seen_inner,
                'using_inner_existing_OOF_C0_sees_outer_claims':seen_outer,
                'both_existing_reuses_invalid':seen_inner>0 and seen_outer>0})
    code=path(p['C0_code']).read_text(encoding='utf-8-sig');tree=ast.parse(code)
    functions={n.name:n for n in ast.walk(tree) if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef))}
    assert {'fit_reporting','average_completion','run'}<=set(functions)
    getlines=lambda name:{'start':functions[name].lineno,'end':functions[name].end_lineno}
    dependencies=[
        {'node':'count_delay_curve','learned_from':['training delay','training valuation-age truncation'], 'code_function':'fit_reporting','must_exclude_both_folds':True},
        {'node':'claim_probability_weights','learned_from':['count delay masses','training counts per delay'],'code_function':'fit_reporting','must_exclude_both_folds':True},
        {'node':'cost_curve_and_mean_mark_rho1','learned_from':['training T0 marks','claim probability weights'],'code_function':'fit_reporting','must_exclude_both_folds':True},
        {'node':'frequency_per_peril','learned_from':['training notification counts','training exposure times count completion'],'code_function':'run','must_exclude_both_folds':True},
        {'node':'peril_cost_mixture','learned_from':['frequency per peril','mean mark per peril'],'code_function':'run','must_exclude_both_folds':True},
        {'node':'period_completion','learned_from':['frozen scoped cost curve','period dates','fixed valuation date'],'code_function':'average_completion','must_exclude_both_folds':True},
        {'node':'C0_effective_exposure','learned_from':['nominal exposure','period cost completion','scoped peril mixture'],'code_function':'run','must_exclude_both_folds':True}]
    report={'id':p['id'],'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_plan_sha256':sha(pp),
        'periods':len(periods),'groups':len({x['group_id'] for x in periods}),'building_periods':len(building),
        'row_id_globally_unique_in_saved2023':rowids_unique,'future_keys_must_be_composite':True,
        'existing_outer_scopes_reconciled':len(scopes),'planned_inner_unique_scopes':len(planned),'ordered_inner_cases':len(reuse),
        'unsafe_existing_reuse_cases':sum(x['both_existing_reuses_invalid'] for x in reuse),
        'building_perils':sorted(perilset),'building_claims_in_union':len(union_building),
        'claims_union_all_lines':len(claim_union),'min_planned_notifications_by_peril':{name:min(x['claims_by_peril'][name] for x in planned) for name in sorted(perilset)},
        'all_planned_reporting_min5_met':all(x['reporting_min5_notifications_met'] for x in planned),
        'resource_enumeration':{'hypothetical_only':True,'unique_inner_B20_buildings_fits':10,'outer_saved_models_reused':5,
            'slope_fits':5,'level_constants':5,'C0_scope_workflows':10,'building_reporting_peril_calls':60,
            'derived_frequency_constants':60,'mean_marks_returned_with_reporting_call':60,'normalized_six_entry_mixture_vectors':10,
            'mean_marks_not_additional_Gamma_or_model_fits':True,'base_reserve_rho':1.0,'calibration_beta_unestimated':True},
        'C0_numeric_core_implemented_here':False,'learned_object_poisoning_tested':False,'metadata_scope_selector_only':True,
        'current_support_gate':'failed','fit_authorized':False,'can_execute':False,
        'new_fits':0,'new_inference':0,'new_C0_values':0,'parameters_estimated':0,'new_bootstrap':0,
        '2024_test_closed':True,'ledger_read':False,'reference':'W2-B00','promotion':False,'all_alternatives_preserved':True,
        'professional_independent_validation':False,
        'limits':['Scope reconciliation uses saved metadata/code/receipts, not raw transaction or ultimate validation.',
            'Current outer scope isolation does not supply nested learned objects.',
            'Count minima do not prove timing/mark stability or failed risk-tail support.',
            'Metadata-only selector is not a fitted C0 adapter or proof of fitted-object poisoning invariance.',
            'Calibration-beta and reserve-rho namespaces must stay separate; valuation date unchanged.']}
    dump(out/'observed_outer_scopes.json',scopes);dump(out/'planned_inner_scopes.json',planned)
    dump(out/'unsafe_cache_reuse.json',reuse)
    dump(out/'C0_dependency_inventory.json',{'dependencies':dependencies,'code_ranges':{k:getlines(k) for k in ['fit_reporting','average_completion','run']},
        'parameter_namespace':p['parameter_namespace'],'fixed_valuation_date':'2024-12-31','no_2024_policy_data_read':True})
    dump(out/'report.json',report)
    print(json.dumps({k:report[k] for k in ['existing_outer_scopes_reconciled','planned_inner_unique_scopes','unsafe_existing_reuse_cases','building_claims_in_union','min_planned_notifications_by_peril','current_support_gate','new_fits']}))


if __name__=='__main__':main()
