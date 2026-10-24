"""Casos adversos de asignación, unidades y aislamiento de entidades."""
from pathlib import Path
import importlib.util
import json

REPO = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('s2prep', REPO/'src/semana2/preparar_base.py')
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)
pd, np = m.pd, m.np
results = []


def check(name, ok):
    results.append({'name': name, 'pass': bool(ok)})
    assert ok, name


def rejects(name, callback, expected):
    try:
        callback()
    except ValueError as exc:
        check(name, expected in str(exc))
    else:
        check(name, False)


f = pd.DataFrame({'period_start': ['2023-01-01', '2023-01-01', '2024-01-01'],
    'period_end': ['2023-01-01', '2023-12-31', '2024-12-31'], 'exposure': [1.0, 1.0139, 1.0027]})
e = m.reconcile_exposure(f)
check('Inclusive one-day exposure', e.exposure.iloc[0] == 0.0027)
check('360 basis reconciles, original retained', e.exposure.iloc[1] == 1 and e.exposure_original.iloc[1] == 1.0139)
check('Leap-year 366 days not clipped to one', e.exposure.iloc[2] == 1.0027)
rejects('Unexplained exposure blocks', lambda: m.reconcile_exposure(f.assign(exposure=[2.3456, 1.0139, 1.0027])), 'sin explicar')

p = pd.DataFrame({'market': ['emerging']*2, 'line': ['motor']*2, 'policy_id': ['P']*2,
    'row_id': ['A','B'], 'period_start': pd.to_datetime(['2023-01-01','2023-07-01']),
    'period_end': pd.to_datetime(['2023-06-30','2023-12-31'])})
c = pd.DataFrame({'market': ['emerging']*4, 'line':['motor']*4,'policy_id':['P']*4,
    'claim_id':['C1','C2','C3','C4'],'loss_date':['2023-06-30','2023-07-01','2022-12-31','2023-04-01'],
    'report_date':['2023-07-02']*4,'status':['closed','open','closed','repudiated'],
    'paid_to_date':[50.,50.,50.,0.], 'incurred_to_date':[100.,100.,100.,0.], 'recoveries':[20.,20.,20.,0.]})
a = m.assign_claims(c,p)
check('Inclusive adjacent boundaries map correctly', a.row_id.iloc[:2].tolist()==['A','B'])
check('Before first coverage remains unassigned', bool(a.audit_precoverage.iloc[2]) and pd.isna(a.row_id.iloc[2]))
check('Repudiated claim excluded even if matched', a.row_id.iloc[3]=='A' and not a.included_in_T0.iloc[3])
check('Recoveries deducted once, excess not repeated', a.T0_cents.iloc[0]==8000 and a.reserve_cents.iloc[0]==5000)
bad = p.copy(); bad.loc[1,'period_start']=pd.Timestamp('2023-06-30')
rejects('Ambiguous coverage blocks', lambda:m.assign_claims(c,bad), 'ambigua')
gap = p.copy(); gap.loc[0,'period_end']=pd.Timestamp('2023-06-29')
rejects('Gap is not relabelled prehistory', lambda:m.assign_claims(c,gap), 'sin explicación')
rejects('Duplicate claim ID blocks', lambda:m.assign_claims(pd.concat([c,c.iloc[:1]],ignore_index=True),p), 'duplicado')
foreign = p.copy(); foreign['market']='developed'; foreign['row_id']=['D1','D2']
am = m.assign_claims(c, pd.concat([p,foreign],ignore_index=True))
check('Same identifiers in other market do not cross', am.row_id.iloc[:2].tolist()==['A','B'])

parts = pd.DataFrame({'market':['emerging']*4, 'line':['motor','buildings','contents','motor'],
    'row_id':['R1','R2','R3','T1'],'policy_id':['P1','P2','P3','P4'],
    'customer_id':['C1','C2','C3','C1'],'address_id':['A1','A1','A2','A2'],
    'period_start':pd.to_datetime(['2023-01-01','2024-01-01','2023-01-01','2025-01-01']),
    'period_end':pd.to_datetime(['2023-12-31','2024-12-30','2023-12-31','2025-12-31']),
    'year':[2023,2024,2023,2025],'is_test':[False,False,False,True]})
v, nodes = m.make_partitions(parts,'fixed-seed',5)
check('Shared address across lines stays together', v.group_id.iloc[0]==v.group_id.iloc[1])
check('Future test bridge does not merge training groups', v.group_id.iloc[0]!=v.group_id.iloc[2] and pd.isna(v.group_id.iloc[3]))
v2,_ = m.make_partitions(parts.assign(T0=[1e9,0,17,999]),'fixed-seed',5)
check('Groups/folds invariant to labels', v[['row_id','group_id','fold']].equals(v2[['row_id','group_id','fold']]))
v3,_ = m.make_partitions(parts.sample(frac=1,random_state=42).reset_index(drop=True),'fixed-seed',5)
left=v.set_index('row_id')[['group_id','fold']].sort_index()
right=v3.set_index('row_id')[['group_id','fold']].sort_index()
check('Groups/folds invariant to input order',left.equals(right))

target_periods = pd.DataFrame({'market':['emerging']*3,'line':['motor']*3,'row_id':['A','B','T'],
    'policy_id':['P']*3,'customer_id':['C']*3,'address_id':['X']*3,'year':[2023,2023,2025],
    'is_test':[False,False,True],'exposure':[.5,.5,1.]})
t=m.make_targets(target_periods,a)
check('Only accepted assigned claims enter T0', t.T0.iloc[:2].tolist()==[80.,80.])
check('Test is unlabelled, not a zero target', pd.isna(t.T0.iloc[2]) and pd.isna(t.n_accepted.iloc[2]))
check('Reserve stress changes reserve only',t.T1_reserve075.iloc[0]==67.5 and t.T1_reserve125.iloc[0]==92.5)

print(json.dumps({'checks':results,'passed':len(results),'failed':0},ensure_ascii=True))
