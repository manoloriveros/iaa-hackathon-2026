"""Preflight de curvas por ramo/peril, con pesos y precios fuente congelados."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1]; ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p64_fixed_proxy',R/'herramientas/validar_proxy_observacion_P62.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
u=p.u;m=p.m;k=p.k;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
OUT=BASE/'P64_reporte_por_ramo_preflight_20261027'
PLAN=R/'registro/semana2_reporte_por_ramo_preflight_plan.json';INDEX=R/'registro/semana2_reporte_por_ramo_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P64_REPORTE_POR_RAMO_PREFLIGHT.md'
BRANCHES={'NOMINAL':1.,'RESERVE075':.75,'RESERVE125':1.25}


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def line_curves(claims,line,parent):
    """Same reverse product limit; only risk/event sets split by line.

    Reuse the exact pooled-peril cap and common support grid. No new cap tuning,
    different bucket, mixture smoothing, price clipping or tail extrapolator.
    """
    z=claims.loc[claims.line.eq(line)];caps={v['peril']:v['cap_CDF_weight_p995'] for v in parent['records']}
    size=parent['tmax_days']//q.BUCKET+1;curves={};records=[]
    for peril in q.PERILS[line]:
        g=z.loc[z.peril.eq(peril)];assert len(g)>0
        weight=np.minimum(g.net.to_numpy(float),caps[peril]);assert np.isfinite(weight).all() and (weight>=0).all() and weight.sum()>0
        db=g.delay.to_numpy(int)//q.BUCKET;wb=g.window.to_numpy(int)//q.BUCKET
        assert (db<=wb).all() and (wb<size).all()
        mass=np.bincount(db,weights=weight,minlength=size)[:size]
        end=np.bincount(wb+1,weights=weight,minlength=size+1)[:size]
        risk=np.cumsum(mass)-np.cumsum(end)
        hazard=np.divide(mass,np.maximum(risk,1e-9),out=np.zeros_like(mass),where=risk>0)
        assert np.isfinite(hazard).all() and (hazard>=-1e-12).all() and (hazard<=1+1e-10).all()
        hazard=np.clip(hazard,0,1);survival=np.cumprod((1-hazard)[::-1])[::-1];cdf=np.r_[survival[1:],1.]
        assert np.isfinite(cdf).all() and (np.diff(cdf)>=-1e-12).all() and cdf[-1]==1.
        curves[peril]=cdf.tolist();total=math.fsum(weight.tolist())
        records.append({'line':line,'peril':peril,'claims':len(g),'target_training_claims':int(g.market.eq('target_train').sum()),
            'cap_CDF_weight_p995':caps[peril],'cost_CDF_weight_sum':total,'cost_weight_ESS':total**2/math.fsum((weight**2).tolist())})
    return {'bucket_days':q.BUCKET,'tmax_days':parent['tmax_days'],'curves':curves,'records':records,
        'weights':'Exact saved pooled-peril cap, same whole-scope grid; risk sets restricted to line/peril.'}


def synthetic():
    rng=np.random.default_rng(2026102764);source=[];target=[];n=240
    for line in q.LINES:
        for j,peril in enumerate(q.PERILS[line]):
            for i in range(12):
                source.append({'claim_id':line+peril+str(i),'line':line,'peril':peril,'loss_date':pd.Timestamp('2021-01-01')+pd.Timedelta(days=i*7),
                    'report_date':pd.Timestamp('2021-01-01')+pd.Timedelta(days=i*7+i*13+j*3),'net':float(100+i*40),'market':'source'})
    source=pd.DataFrame(source);target=pd.DataFrame({'row_id':['h','t'],'claim_id':['h','t'],'line':'motor','peril':'theft',
        'loss_date':pd.to_datetime(['2024-02-01','2023-01-01']),'report_date':pd.to_datetime(['2024-02-20','2023-03-01']),
        'T0_cents':[50000,20000],'reserve_cents':[10000,5000],'included_in_T0':True})
    selected=m.selected_claims(target,{'t'},1.);pool=q.pool_claims(source,selected,{'t'});parent=q.cost_curves(pool)
    bad=target.copy()
    for name in ['line','peril','loss_date','report_date']:
        bad[name]=bad[name].astype('object');bad.loc[bad.row_id.eq('h'),name]='INVALID_PROTECTED'
    bad.loc[bad.row_id.eq('h'),['T0_cents','reserve_cents']]=-1e30
    poisoned=q.pool_claims(source,m.selected_claims(bad,{'t'},1.),{'t'});assert pool.equals(poisoned)
    results=[]
    for line in q.LINES:
        a=line_curves(pool,line,parent);b=line_curves(poisoned,line,parent);assert a==b
        # Independent scalar risk-set product at every bucket of the new stratum.
        for rec in a['records']:
            g=pool.loc[pool.line.eq(line)&pool.peril.eq(rec['peril'])];ww=np.minimum(g.net.to_numpy(float),rec['cap_CDF_weight_p995'])
            db=g.delay.to_numpy(int)//q.BUCKET;wb=g.window.to_numpy(int)//q.BUCKET;hh=[]
            for bucket in range(len(a['curves'][rec['peril']])):
                risk=math.fsum(ww[(db<=bucket)&(wb>=bucket)].tolist());mass=math.fsum(ww[db==bucket].tolist());hh.append(mass/risk if risk>0 else 0.)
            scalar=[math.prod(1-v for v in hh[bucket+1:]) for bucket in range(len(hh))]
            assert np.allclose(scalar,a['curves'][rec['peril']],rtol=1e-12,atol=1e-12)
        year=2023+(np.arange(n)//5)%2
        f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],'is_held':np.arange(n)%5==0,
            'year':year,'new_business':(np.arange(n)//10)%2,'T0':rng.gamma(2,100,n)*(rng.random(n)<.4),'reserve':0.,
            'annual_A1S':np.exp(rng.normal(0,.3,n)),'annual_T2b':np.exp(rng.normal(4,.3,n)),'prior_claims_5y':rng.integers(0,3,n),
            'ncb_years':rng.integers(0,15,n),'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),
            'marketing_segment':rng.choice(['a','b','c'],n),'period_start':pd.to_datetime(np.where(year==2023,'2023-01-01','2024-01-01')),
            'period_end':pd.to_datetime(np.where(year==2023,'2023-12-31','2024-12-31'))})
        f['exposure_calendar']=(f.period_end-f.period_start).dt.days.add(1)/365.;rates=np.exp(rng.normal(4,.5,(n,len(q.PERILS[line]))))
        f['q_paired']=u.row_q(f,rates,a,q.PERILS[line]);poison=f.copy();poison.loc[poison.is_held,['T0','reserve']]=-1e30
        artifact=m.once(OUT/'synthetic'/line,'primary',lambda:k.learn(f,line));other=m.once(OUT/'synthetic'/line,'adverse',lambda:k.learn(poison,line));assert artifact==other
        value,norm=k.forward(f.loc[f.is_held],artifact,True);h=poison.loc[poison.is_held].copy();h['q_paired']=np.nan
        replay,nn=k.forward(h,json.loads(json.dumps(other)),True);assert np.array_equal(value,replay) and norm==nn
        results.append({'line':line,'all_scalar_curve_buckets_match':True,'held_claim_payload_poison_invariant':True,'price_learning_and_JSON_forward_invariant':True})
    return {'author':'Codex','utc':utc(),'results':results,'synthetic_primary_curve_strata':15,'synthetic_adverse_curve_strata_separate':15,
        'synthetic_parent_pooled_curves':11,'synthetic_primary_closed_learners':3,'synthetic_adverse_closed_learners_separate':3,'real_price_fits':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    diag=BASE/'P63_revision_proxy_guardado_20261027';assert w.read(diag/'completion_receipt.json')['report_sha256']==w.sha(diag/'report.json')
    prior=w.read(p.PLAN);m.check_sources(prior);OUT.mkdir()
    paths=[Path(__file__),q.CLAIMS,q.SOURCE_CLAIMS,diag/'report.json',diag/'completion_receipt.json',p.PLAN,p.OUT/'report.json',p.OUT/'completion_receipt.json']
    sources={**prior['sources'],**w.read(u.OUT/'report.json')['outputs']};sources.update({w.rel(path):w.sha(path) for path in paths})
    plan={'author':'Codex','utc':utc(),'hypothesis':'A single standard categorical stratum for line/peril may avoid borrowing different reporting risk sets across shared peril names. P63source mature flood/water contrasts motivate a finite test, not a causal claim or known improvement.',
        'one_change':'Relative to P62only reporting risk/event sets are split uniformly by line/peril (15instead of11strata). Keep EXACT saved pooled-peril p995caps, global grid, reverse-product estimator/buckets, source/target keys, cost/reserve definitions and fixed rowFSpPROXYweights. No line/peril chosen by score, new price architecture, prior or tuned hyperparameter.',
        'scope':'Preflight only: synthetic full numerical flow and real scoped reporting objects/links. No real price learner, new price score,2025inference or upload. Separate P65registration/commit/forum before any predictive fit.',
        'configuration':{'lines':q.LINES,'perils':q.PERILS,'bucket_days':q.BUCKET,'branches':BRANCHES,'proxy':'Exact nominal P61FSpannual costPROXYfor BOTHunchanged P54price components','calendar':'Inclusive once; qby per-row proxy and per-line reporting; tails .05/.10only BI/subsidence, nominalweights fixed.',
            'primary_real_curve_strata':225,'adverse_real_curve_strata_separate':225,'primary_curve_objects':45,'adverse_curve_objects_separate':45,'historical_qvectors':75},
        'preflight_criterion':'Held target payload exclusion before any parse; all primary/adverse curves identical; independent scalar risk-set/products and daily-calendar sums; all qfinite positive<=1; all historical keys/groups/years unchanged. Report support/ESS without inventing credibility; old insufficient support/transport limits persist.',
        'future_acceptance':'Exactly every P62pooled/scenario/cohort/family16/level/influence gate. Any pooled failure prevents admission, transfer unmeasured. Pooled pass needs OWN2023conditional transfer, no copied outer objects or automatic upload.',
        'budget':{'new_real_price_fits':0,'new_source_fits':0,'new_scores':0,'new2025inference':0,'new_submissions':0},
        'sources':sources,'limits':['Same-name line contrasts are descriptive developed conditional1095evidence; market/time/mark/valuation differences remain.','Stratification lowers effective reporting support and does not identify emerging ultimate tails.','Adaptive2023/2024/source2024conditional, borrowed FSpcomposition, undatedmasters and future weather restrictions remain.'],
        '2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P64registra antes de recalcular curvas un único cambio estándar: separar por ramo/peril los conjuntos de riesgo/evento de reporte, uniformemente en15estratos. P63muestra diferencias descriptivas fuente por ramo, especialmente flood/agua, sin probar mejora emergente. Se mantienen exactamente topesP50/P52por peril, rejilla/estimador, claves protegidas, proxyFSpnominal y arquitecturaP54.225curvas primarias/225adversas en45+45objetos;75enlaces históricos. Preflight sintético completo y veneno retenido, sin precios reales/scores. La evaluación predictiva requerirá otra inscripción con todas las guardas y transferencia si pasa. No se seleccionan celdas o perils por resultado ni se supone credibilidad. B00preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P64registered_before_stratified_reporting','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P64-RAMO-PREVIO','P64: reporte por ramo/peril, cambio estándar antes de recalcular')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());target=pd.read_parquet(q.CLAIMS);outputs={};records=[];frames={}
    for line in q.LINES:
        for outer in range(5):frames[(line,outer)]=pd.read_parquet(u.OUT/f'input_{line}_{outer}.parquet')
    for outer in range(5):
        train_ids=set().union(*(set(frames[(line,outer)].loc[~frames[(line,outer)].is_held,'row_id']) for line in q.LINES))
        protected=~target.row_id.isin(train_ids);bad=target.copy()
        for name in ['line','peril','loss_date','report_date']:
            bad[name]=bad[name].astype('object');bad.loc[protected,name]='INVALID_PROTECTED'
        bad.loc[protected,['T0_cents','reserve_cents']]=-1e30
        for case,branch in BRANCHES.items():
            source=m.source_branch(branch);parent=w.read(u.curves_path(outer,case))
            selected=m.selected_claims(target,train_ids,branch);claims=q.pool_claims(source,selected,train_ids)
            adverse=q.pool_claims(source,m.selected_claims(bad,train_ids,branch),train_ids);assert claims.equals(adverse)
            for line in q.LINES:
                folder=OUT/f'{case}_outer{outer}'/line
                a=m.once(folder,'primary_curves',lambda:line_curves(claims,line,parent))
                b=m.once(folder,'adverse_curves',lambda:line_curves(adverse,line,parent));assert a==b
                assert set(a['curves'])==set(q.PERILS[line]);outputs.update({w.rel(path):w.sha(path) for path in folder.iterdir() if path.is_file()})
                records.append({'outer':outer,'case':case,'line':line,'curve_strata':len(a['curves']),'primary_adverse_exact':True,'support':a['records']})
        for line in q.LINES:
            f=frames[(line,outer)];profile=pd.read_parquet(u.OUT/f'FSp_proxy_{line}.parquet').set_index('row_id').loc[f.row_id]
            assert profile.index.is_unique and np.array_equal(profile.year,f.year)
            rates=profile[['FSp_annual_cost_proxy_'+name for name in q.PERILS[line]]].to_numpy(float)
            for case in u.CASES:
                source_case=case if case.startswith('RESERVE') else 'NOMINAL';a=w.read(OUT/f'{source_case}_outer{outer}'/line/'primary_curves.json')
                tail=.05 if case=='TAIL005' else .1 if case=='TAIL010' else 0.;f['q_'+case]=u.row_q(f,rates,a,q.PERILS[line],tail)
            f['q_paired']=f.q_NOMINAL.to_numpy()
            for pos in [0,len(f)//2,len(f)-1]:
                a=w.read(OUT/f'NOMINAL_outer{outer}'/line/'primary_curves.json');qq=[]
                for name in q.PERILS[line]:
                    curve=a['curves'][name];values=[curve[min((q.CUT-day).days//q.BUCKET,len(curve)-1)] for day in pd.date_range(f.period_start.iloc[pos],f.period_end.iloc[pos])]
                    qq.append(math.fsum(values)/len(values))
                scalar=math.fsum(float(x)*float(y) for x,y in zip(rates[pos],qq))/math.fsum(rates[pos].tolist())
                assert math.isclose(scalar,float(f.q_paired.iloc[pos]),rel_tol=2e-12,abs_tol=1e-13)
            path=OUT/f'input_{line}_{outer}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
    m.check_sources(plan);report={'author':'Codex','utc':utc(),'status':'P64stratified_reporting_and_full_synthetic_flow_passed','plan_sha256':w.sha(PLAN),
        'records':records,'outputs':outputs,'primary_real_curve_strata':225,'adverse_real_curve_strata_separate':225,'historical_bindings':15,'historical_qvectors':75,
        'independent_real_daily_checks':45,'support_is_not_credibility':True,**plan['budget']}
    dump(OUT/'report.json',report);print(json.dumps({key:report[key] for key in ['status','primary_real_curve_strata','adverse_real_curve_strata_separate','historical_bindings','new_real_price_fits','new_scores']}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    assert all(w.sha(ROOT/path)==value for path,value in d['outputs'].items())
    next_unit='P65: register and commit complete unchanged P54price learner with P64line/peril reporting and fixed FSpPROXYrow weights. Same all gates;15primary/15adverse whole learners, zero source/report refits. No CSVuntil pooled plus OWNconditional transfer and exact-file admission.'
    text='# P64: reporte por ramo/peril, preflight\n\nCodex, '+utc()+'. Se separaron uniformemente15estratos de reporte por ramo/peril, manteniendo topes de coste por peril y rejilla ya guardados. Este cambio estándar evita imponer conjuntos de riesgo idénticos a ramos distintos; no prueba transportabilidad o mejora.\n\n'
    text+='225curvas primarias y225adversas,45+45objetos, idénticas tras alterar campos protegidos antes del parseo;75vectores qy15enlaces históricos. El flujo sintético recorrió15curvas primarias/15adversas,3aprendices cerrados primarios/3adversos y serialización sin divergencias. Productos de riesgo escalares y45sumas diarias históricas independientes coincidieron. Se guardan recuentos/ESSpor estrato sin convertirlos en credibilidad.\n\n'
    text+='No se ajustaron modelos de precio reales o fuentes ni se puntuó. La composición sigue siendo un proxyFSp prestado para ambos componentes de precio. Persisten reservas/cola, mercado/tiempo, fuente2024condicional y búsqueda adaptativa; no validación independiente. B00/F3cyalternativas conservados,2024abierto.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'next_unit':next_unit,'primary_real_curve_strata':225,'adverse_real_curve_strata_separate':225,**w.read(PLAN)['budget'],
        '2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P64-RAMO-RESULTADO','P64: curvas por ramo protegidas, aún sin puntuación')}
    archive=R/'privado'/('corte_P64_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P64'),(R/'registro/semana2_mision_privada_actual.json','P64')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    counts=R/'registro/semana2_contadores_propios_actual.json';w.update(counts,{'phase2_private_P64_reporting_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P64=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P64: reporte estándar por ramo/peril\n\nCodex, '+receipt['utc']+'.225curvas primarias/225adversas y15enlaces, veneno retenido y flujo sintético completo pasaron. Cero precios reales/scoring/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_line_reporting_preflight_index':w.rel(INDEX),'week_2_private_line_reporting_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_price_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
