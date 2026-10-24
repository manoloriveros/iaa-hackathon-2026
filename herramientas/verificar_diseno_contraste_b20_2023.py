"""Comprueba contrato y grafo hipotético; cero ajuste de parámetros reales."""
from pathlib import Path
from datetime import datetime, timezone
from copy import deepcopy
from itertools import combinations
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_diseno_contraste_20261024_v1'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def structural_errors(p):
    errors = []
    v, c, a = p['validation_design'], p['contrast'], p['acceptance']
    if v['years'] != [2023] or not p['2024_test_closed'] or p['ledger_read']:
        errors.append('scope')
    if c['control_L']['b'] != 1 or c['candidate_S']['b_bounds'] != [0., 1.]:
        errors.append('contrast')
    if c['additional_free_parameters_vs_L'] != 1 or not c['one_candidate_only']:
        errors.append('capacity')
    required = {'B20 buildings GLM', 'imputer', 'scaler', 'OHE', 'reporting curves',
                'frequency/severity mixture weights', 'all learned C0 parameters'}
    if set(v['inner_learned_objects_exclude_both']) != required:
        errors.append('ancestors')
    expected = {tuple(sorted(set(range(5))-set(pair))) for pair in combinations(range(5),2)}
    if {tuple(x) for x in v['inner_training_fold_sets']} != expected:
        errors.append('inner_scopes')
    if not a['all_conditions_conjunctive'] or not a['stop_if_any_fail_or_unknown']:
        errors.append('failure_rule')
    if any(p['resources']['current'].values()) or p['promotion']:
        errors.append('current_execution')
    return errors


def tail_pass(cell, rule):
    required = ['positive_groups', 'largest_cost_group_share', 'cost_concentration_equivalent_groups']
    if any(cell.get(x) is None for x in required):
        return False
    return (cell['positive_groups'] >= rule['positive_groups_min']
            and 0 <= cell['largest_cost_group_share'] <= rule['largest_cost_group_share_max']
            and cell['cost_concentration_equivalent_groups'] >= rule['cost_concentration_equivalent_groups_min'])


def graph():
    nodes = []
    for k in range(5):
        train = sorted(set(range(5))-{k})
        for j in train:
            inner = sorted(set(train)-{j})
            nodes.append({'outer_eval': k, 'inner_eval': j, 'base_label_ancestors': inner,
                          'C0_label_ancestors': inner, 'transform_label_ancestors': inner,
                          'calibration_label_ancestors': train,
                          'saved_outer_base_and_C0_label_ancestors': train})
    return nodes


def graph_valid(nodes):
    for x in nodes:
        k, j = x['outer_eval'], x['inner_eval']
        if k == j:
            return False
        for key in ['base_label_ancestors', 'C0_label_ancestors', 'transform_label_ancestors']:
            if set(x[key]) != set(range(5))-{k,j}:
                return False
        for key in ['calibration_label_ancestors', 'saved_outer_base_and_C0_label_ancestors']:
            if set(x[key]) != set(range(5))-{k}:
                return False
    return len(nodes) == 20


def main():
    output = RUN / 'verification.json'
    assert not output.exists(), 'Recibo existente: no repetir.'
    p = read(RUN / 'plan_snapshot.json')
    checkrows = []

    def check(name, value, kind='documentary'):
        checkrows.append({'name': name, 'pass': bool(value), 'kind': kind})

    frozen = {}
    for x in p['frozen_sources']:
        check('Frozen source ' + x['path'], sha(ROOT / x['path']) == x['sha256'])
        check('Snapshot ' + x['path'], sha(ROOT / x['snapshot']) == x['sha256'])
        check('Only aggregate JSON/Markdown ' + x['path'], Path(x['path']).suffix in ['.json','.md']
              and '2024' not in x['path'].lower() and 'test' not in x['path'].lower())
        frozen[x['path']] = ROOT / x['snapshot']
    load = lambda path: read(frozen[path])
    pointer = lambda d: load(d['path'] if isinstance(d, dict) else d)
    sources = {key: load(path) for key,path in p['source_indices'].items()}
    for key, idx in sources.items():
        v = pointer(idx['verification'])
        check('Final stored receipt ' + key, v['failed'] == 0)
    band = pointer(sources['calibration']['readout'])
    b1 = next(x for x in band['rows'] if x['line'] == 'buildings' and x['band'] == 1)
    b5 = next(x for x in band['rows'] if x['line'] == 'buildings' and x['band'] == 5)
    # Existing receipt and design use different names for the same statistic.
    b1 = b1 | {'largest_cost_group_share':b1['largest_group_cost_share']}
    b5 = b5 | {'largest_cost_group_share':b5['largest_group_cost_share']}
    for field in ['positive_groups', 'largest_cost_group_share', 'cost_concentration_equivalent_groups']:
        check('Known band1 support ' + field, b1[field] == p['support']['known_screen'][0][field])
        check('Known band5 support ' + field, b5[field] == p['support']['known_screen'][1][field])
    check('Current pooled screen correctly fails', not tail_pass(b1,p['support']['pooled_tail'])
          and tail_pass(b5,p['support']['pooled_tail']))
    check('Known concentrated fold fails', p['support']['known_screen'][2]['largest_cost_group_share_rounded']
          > p['support']['fold_tail']['largest_cost_group_share_max'])
    check('Mechanism not assumed true', p['current_conclusion'].startswith('A concrete falsifiable hypothesis')
          and len(p['mechanism']['not_established']) == 4)
    check('Baseline design valid', not structural_errors(p))
    for name, mutate in [
        ('other_year', lambda d: d['validation_design'].update(years=[2023,2024])),
        ('open_test', lambda d: d.update(**{'2024_test_closed':False})),
        ('wrong_control', lambda d: d['contrast']['control_L'].update(b=.9)),
        ('extra_parameter', lambda d: d['contrast'].update(additional_free_parameters_vs_L=2)),
        ('missing_C0_ancestor', lambda d: d['validation_design']['inner_learned_objects_exclude_both'].remove('all learned C0 parameters')),
        ('skip_failure', lambda d: d['acceptance'].update(stop_if_any_fail_or_unknown=False)),
        ('current_fit', lambda d: d['resources']['current'].update(new_calibration_fits=1)),
        ('promotion', lambda d: d.update(promotion=True))]:
        d = deepcopy(p)
        mutate(d)
        check('Reject synthetic ' + name, bool(structural_errors(d)), 'adverse')
    good = {'positive_groups':50, 'largest_cost_group_share':.20, 'cost_concentration_equivalent_groups':10.}
    rule = p['support']['pooled_tail']
    check('Support equality allowed', tail_pass(good,rule), 'boundary')
    for name, key, value in [('few_positive','positive_groups',49),('concentrated','largest_cost_group_share',.2001),
                              ('few_equivalent','cost_concentration_equivalent_groups',9.999),
                              ('undefined','largest_cost_group_share',None)]:
        d = good | {key:value}
        check('Reject support ' + name, not tail_pass(d,rule), 'adverse')
    g = graph()
    check('Twenty nested scopes', graph_valid(g), 'dependency_graph')
    unique = {tuple(x['base_label_ancestors']) for x in g}
    check('Ten cached triple scopes', len(unique) == 10 == p['resources']['future_only_if_gates_pass']['unique_inner_B20_buildings_fits'], 'dependency_graph')
    for k in range(5):
        check('Outer labels excluded in all ancestors fold' + str(k), all(k not in x[key]
              for x in g if x['outer_eval'] == k for key in ['base_label_ancestors','C0_label_ancestors',
              'transform_label_ancestors','calibration_label_ancestors','saved_outer_base_and_C0_label_ancestors']), 'dependency_graph')
    for key in ['base_label_ancestors','C0_label_ancestors','transform_label_ancestors']:
        poisoned = deepcopy(g)
        poisoned[0][key].append(poisoned[0]['outer_eval'])
        check('Reject outer ancestry leak ' + key, not graph_valid(poisoned), 'adverse')
    poisoned = deepcopy(g)
    poisoned[0]['C0_label_ancestors'].append(poisoned[0]['inner_eval'])
    check('Reject inner C0 leakage', not graph_valid(poisoned), 'adverse')
    # Fixed algebraic examples only. No parameter search, estimators or real rows.
    d15 = lambda y,mu: 4*y/math.sqrt(mu)+4*math.sqrt(mu)-8*math.sqrt(y)
    for e,y,r in [(4.,0.,3.),(.25,8.,5.),(9.,28.,2.)]:
        check('Observed-unit/rate identity '+str(e), math.isclose(d15(y,e*r),math.sqrt(e)*d15(y/e,r),abs_tol=1e-11), 'algebra_fixture')
    h, y = [9.,16.], [0.,28.]
    check('Fixed intercept score zero', sum(math.sqrt(x)-yy/math.sqrt(x) for x,yy in zip(h,y)) == 0, 'algebra_fixture')
    check('Zero score does not force AE1', sum(y)/sum(h) == 1.12, 'algebra_fixture')
    check('b1 recovers raw rate at a0', math.isclose(7.*math.exp(math.log(12.)-math.log(7.)),12.), 'algebra_fixture')
    check('b0 loses all nominal relativities', 7.*math.exp(0*2.) == 7.*math.exp(0*(-3.)), 'algebra_fixture')
    check('No current execution eligible', not read(RUN/'current_readiness.json')['can_execute']
          and not read(RUN/'current_readiness.json')['fit_authorized'])
    check('Decision journal ten entries', len(read(RUN/'decision_journal.json')['decisions']) == 10)
    check('Policy unchanged in design', p['reference']=='W2-B00' and p['all_alternatives_preserved'] and not p['promotion'])
    check('Exposure and review declared', p['prior_external2024_header_exposure_disclosed']
          and not p['complete_blindness_claim_allowed'] and not p['professional_independent_validation'])
    (RUN/'nested_scope_graph.json').write_text(json.dumps({'hypothetical_only':True,'nodes':g},indent=2)+'\n',encoding='utf-8')
    result = {'id':p['id'], 'author':'Codex', 'utc':datetime.now(timezone.utc).isoformat(),
              'passed':sum(x['pass'] for x in checkrows),'failed':sum(not x['pass'] for x in checkrows),
              'checks':checkrows,'checker_sha256':sha(Path(__file__)),
              'design_validity_is_not_fit_eligibility':True, 'current_support_gate':'failed',
              'parameters_estimated':0,'new_fits':0,'new_inference':0,'new_bootstrap':0,
              'prior_checker_attempt_failure':'verification_attempt1_failure.json',
              'repair':'Explicit field-name mapping only; no design/source/threshold changes.',
              'professional_independent_validation':False}
    output.write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['passed','failed','current_support_gate','new_fits','parameters_estimated']}))
    return bool(result['failed'])


if __name__ == '__main__':
    raise SystemExit(main())
