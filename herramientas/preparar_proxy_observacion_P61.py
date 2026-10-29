"""Identifica FSp/T2b y conecta un proxy de mezcla por peril con curvas P50."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p61_existing_standard_price',R/'herramientas/validar_mezcla_estandar_P55.py')
v=importlib.util.module_from_spec(s);s.loader.exec_module(v)
k=v.k;m=v.m;q=m.q;w=m.w;np=m.np;pd=m.pd;BASE=m.BASE
RAW=BASE/'P59_crossfit_preflight_20261027';REPORTING=m.REPORTING;SCENARIO=v.SCENARIO
OUT=BASE/'P61_proxy_observacion_20261027'
PLAN=R/'registro/semana2_proxy_observacion_preflight_plan.json';INDEX=R/'registro/semana2_proxy_observacion_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P61_PROXY_FSP_OBSERVACION.md'
CASES=['NOMINAL','RESERVE075','RESERVE125','TAIL005','TAIL010']


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,z):return m.dump(p,z)


def row_q(periods,rates,curves,perils,tail=0.):
    # Explicit projection prevents any target, reserve or price-field access.
    p=periods[['period_start','period_end','exposure_calendar']].copy()
    assert curves['bucket_days']==q.BUCKET and rates.shape==(len(p),len(perils))
    assert np.isfinite(rates).all() and (rates>0).all()
    qq=np.column_stack([q.effective(p,curves['curves'][name])/p.exposure_calendar.to_numpy(float) for name in perils])
    qq*=1-tail*np.array([name in ['bodily_injury','subsidence'] for name in perils])
    assert np.isfinite(qq).all() and (qq>=-1e-12).all() and (qq<=1+1e-10).all()
    result=np.sum(rates*qq,axis=1)/rates.sum(axis=1)
    assert np.isfinite(result).all() and (result>0).all() and (result<=1+1e-10).all()
    return result


def curves_path(outer,case):
    return (SCENARIO/f'{case}_outer{outer}/primary_curves.json' if case.startswith('RESERVE') else REPORTING/f'outer{outer}/cost_curves.json')


def synthetic():
    rng=np.random.default_rng(2026102761);n=480;records=[]
    for line in q.LINES:
        year=2023+(np.arange(n)//5)%2
        f=pd.DataFrame({'row_id':['s'+str(i) for i in range(n)],'group_id':['g'+str(i) for i in range(n)],
            'is_held':np.arange(n)%5==0,'year':year,'new_business':(np.arange(n)//10)%2,
            'T0':rng.gamma(2,70,n)*(rng.random(n)<.4),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.3,n)),
            'annual_T2b':np.exp(rng.normal(4,.3,n)),'prior_claims_5y':rng.integers(0,3,n),'ncb_years':rng.integers(0,15,n),
            'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n),
            'period_start':pd.to_datetime(np.where(year==2023,'2023-01-01','2024-01-01')),
            'period_end':pd.to_datetime(np.where(year==2023,'2023-12-31','2024-12-31'))})
        f['exposure_calendar']=(f.period_end-f.period_start).dt.days.add(1)/365.
        perils=q.PERILS[line];curves={'bucket_days':7,'curves':{name:np.linspace(.03+.01*j,1.,261).tolist() for j,name in enumerate(perils)}}
        rates=np.exp(rng.normal(4,.7,(n,len(perils))));f['q_paired']=row_q(f,rates,curves,perils)
        rounded=np.round(f.exposure_calendar.to_numpy(),4);period=rates*rounded[:,None]
        assert np.allclose(f.q_paired,row_q(f,period,curves,perils),rtol=2e-15,atol=2e-15)
        bad=f.copy();bad.loc[bad.is_held,['T0','reserve']]=-1e30
        assert np.array_equal(f.q_paired,row_q(bad,rates,curves,perils))
        for i in [0,n//2,n-1]:
            qq=[]
            for name in perils:
                c=curves['curves'][name];days=pd.date_range(f.period_start.iloc[i],f.period_end.iloc[i])
                qq.append(math.fsum(c[min((q.CUT-day).days//7,len(c)-1)] for day in days)/len(days))
            scalar=math.fsum(float(a)*float(b) for a,b in zip(rates[i],qq))/math.fsum(rates[i].tolist())
            assert math.isclose(scalar,f.q_paired.iloc[i],rel_tol=2e-12,abs_tol=1e-13)
        folder=OUT/'synthetic'/line;a=m.once(folder,'primary',lambda:k.learn(f,line));aa=m.once(folder,'adverse',lambda:k.learn(bad,line));assert a==aa
        held=f.loc[f.is_held];u,norm=k.forward(held,a,True);bh=bad.loc[bad.is_held].copy();bh['q_paired']=np.nan
        uu,nn=k.forward(bh,json.loads(json.dumps(aa)),True);assert np.array_equal(u,uu) and norm==nn
        records.append({'line':line,'period_vs_annual_proxy_weights_cancel_exposure':True,'daily_scalar_completion_match':True,
            'target_payload_not_accessed_by_link':True,'actual_price_learning_poison_invariance':True,'JSON_ultimate_forward_exact':True})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_closed_learners':3,'synthetic_adverse_closed_learners_separate':3,
        'synthetic_primary_components':6,'synthetic_adverse_components_separate':6,'synthetic_CDF_fits':0,'real_fits':0,'real_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    paths=[Path(__file__),Path(k.__file__),Path(k.core.__file__),Path(k.core.b.__file__),Path(k.g.__file__),Path(q.__file__),
        R/'herramientas/auditar_cache_T2b_P21.py',BASE/'P21_cache_T2b_20261026/report.json',
        R/'herramientas/contrastar_FSp_REN_G3_prod.py',R/'herramientas/contrastar_FSp_REN_contra_G3.py',
        R/'herramientas/recuperar_productor_FSp_MC.py',R/'herramientas/recuperar_productor_FSp_edificios.py',
        R/'herramientas/preparar_recuentos_fuente2024.py',R/'src/semana2/fuente_f2_2024_cb.py',
        BASE/'FSp_REN_G3_prod_contraste_20261026_v1/preflight.json',
        BASE/'FSp_MC_recuperacion_20261026_v1/productor/report.json',BASE/'FSp_edificios_productor_20261026_v1/report.json',
        RAW/'report.json',RAW/'completion_receipt.json',m.P1/'report.json',BASE/'P41_grafo_fuente_recuperada_20261026/report.json',
        BASE/'P60_validacion_crossfit_GLM_20261027/completion_receipt.json',SCENARIO/'branch_report.json']
    branch=w.read(SCENARIO/'branch_report.json');canon={p['path']:p['sha256'] for p in w.read(m.P1/'report.json')['outputs']}
    for line in q.LINES:
        p=m.P1/f'canonical_{line}.parquet';assert w.sha(p)==canon[w.rel(p)];paths += [p,RAW/f'canonical_{line}.parquet']
    for outer in range(5):
        paths.append(REPORTING/f'outer{outer}/scope.json')
        for case in ['NOMINAL','RESERVE075','RESERVE125']:
            p=curves_path(outer,case)
            if case.startswith('RESERVE'):assert w.sha(p)==branch['outputs'][w.rel(p)]
            paths.append(p)
    OUT.mkdir();(OUT/'registered_code.py').write_bytes(Path(__file__).read_bytes())
    plan={'author':'Codex','utc':utc(),'scope':'Source identity/units review plus new adapter preflight, no real price learning or scoring.',
        'correction':'P60followup tentatively named canonical f/s as ORIGINALT2bperil fields. Reused P21evidence says originalT2bcache has ONLYannualtotal risk. Static chain shows f/scome from FSpPRODcomponents via exposure rescaling, NOTa T2bdecomposition. No historical values or model outputs are rewritten.',
        'unit_contract':'FSpf is period count PROXYalready containing calendar exposure. Canonical f=f_prod*rounded_exposure/calendar_exposure; s is observed positive mark CU. Thus f*s is period cost PROXYand (f*s)/rounded_exposure annual cost PROXY. Original frequency likelihood used source cost completion, not independent event-count completion; ultimate frequency/severity is NOTidentified.',
        'source_ancestry':'FSpPRODfixed developed2021-2024labels/counts/marks and mature1095day developed reporting; no emergingcost labels in coefficient fitting. Target categories/notification history/climate2023-2024are conditional supplied covariates, with previous availability limits. Reuse P41and producer receipts; no repeated source/matrix/weather audit.',
        'observation_hypothesis':'A FIXED FSpcost-proxy composition can be borrowed as an alternative row-specific observation profile for BOTHunchanged P54A1S/T2bprice components under P50costCDFs. This is a distinct modeling assumption, NOTthe identified peril composition of either total-price model or a proved correction.',
        'formula':'qrow_i=sum_p r_ip*(E_cost_peril_ip/calendar_exposure_i)/sum_p r_ip, with fixed nominal annual FSpcostproxy r=(f*s)/rounded_exposure. Calendar enters price once via P54. Per-row common exposure scaling cancels from weights. No targetkappa/shares fitted or selected. Reserve scenarios change saved per-perilCDFonly; proxyweights and final nominal ultimate prices stayfixed. Tailscales BI/subsidence completion by.95/.90.',
        'new_recipe_if_later_registered':'Exactly P55fixed50/50A1S/T2bclosed learner with same shapes/levels/residuals and source inputs. ONLYobservation qchanges from common line mixture to fixed rowFSpPROXY. No GLM, newtrees, newpriceblend, alpha/field/weight search or independent perillabel claim. All original global/cohort/family16/scenario/level/influence/transfer guards apply unchanged.',
        'budget':{'synthetic_primary_closed_learners':3,'synthetic_adverse_closed_learners_separate':3,'synthetic_primary_components':6,'synthetic_adverse_components_separate':6,
            'new_CDF_fits':0,'new_real_price_fits':0,'new_source_inference':0,'derived_historical_proxy_tables':3,'historical_row_completion_applications':75,
            'new_price_scores':0,'new2025inference':0,'new_submissions':0},
        'sources':{w.rel(p):w.sha(p) for p in set(paths)},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P61registra una corrección de procedencia y un preflight nuevo, sin repetir P21/P41/P46: T2bsolo aporta tasa anual total; las columnas f/sdel P1son FSpPROD, cuya fya contiene exposición del periodo. Su producto no es una descomposición identificada de T2b. La nueva hipótesis será usar explícitamente esa composición como PROXYde observación bajo las curvas P50nuevas, manteniendo intacta la base estándar P55y sin GLM. El calendario de precio entra una vez y la exposición común se cancela al ponderar. Tres flujos sintéticos primarios/3adversos; se prepararán solo perfiles/enlaces históricos, cero ajustes/scoring real/CDFnuevas/2025/envíos. No se cambia receta antes de otra inscripción predictiva completa. B00/F3c/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P61registered_before_new_proxy_adapter','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P61-PROXY-PREVIO','P61: FSp no es T2b; unidades y proxy de observación antes de probar')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    assert (OUT/'registered_code.py').read_bytes()==Path(__file__).read_bytes()
    cached=w.read(BASE/'P21_cache_T2b_20261026/report.json')
    assert all(not z['peril_outputs_available'] for z in cached['results'])
    dump(OUT/'synthetic.json',synthetic());outputs={};bindings=[]
    for line in q.LINES:
        perils=q.PERILS[line];raw=pd.read_parquet(RAW/f'canonical_{line}.parquet')
        original=pd.read_parquet(m.P1/f'canonical_{line}.parquet',columns=['row_id','year','exposure']+[prefix+p for prefix in ['f_','s_'] for p in perils]).set_index('row_id').loc[raw.row_id]
        assert original.index.is_unique and np.array_equal(original.year,raw.year) and original.exposure.gt(0).all()
        period=np.column_stack([original['f_'+p].to_numpy(float)*original['s_'+p].to_numpy(float) for p in perils])
        rates=period/original.exposure.to_numpy(float)[:,None]
        assert np.isfinite(rates).all() and (rates>0).all()
        profile=raw[['row_id','year']].copy()
        for j,p in enumerate(perils):profile['FSp_annual_cost_proxy_'+p]=rates[:,j]
        path=OUT/f'FSp_proxy_{line}.parquet';profile.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
        for outer in range(5):
            scope=w.read(REPORTING/f'outer{outer}/scope.json')
            assert set(raw.loc[raw.fold.ne(outer),'row_id']).issubset(set(scope['training_row_ids']))
            f=raw.copy();f['is_held']=f.fold.eq(outer)
            for case in CASES:
                curves=w.read(curves_path(outer,case));tail=.05 if case=='TAIL005' else .1 if case=='TAIL010' else 0.
                value=row_q(raw,rates,curves,perils,tail)
                assert np.allclose(value,row_q(raw,period,curves,perils,tail),rtol=3e-15,atol=3e-15)
                f['q_'+case]=value
            f['q_paired']=f.q_NOMINAL.to_numpy()
            path=OUT/f'input_{line}_{outer}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
            bindings.append({'line':line,'outer':outer,'rows':len(f),'training_rows':int((~f.is_held).sum()),
                'proxy_source':'FSpPROD_NOT_T2bdecomposition','peril_profiles':len(perils),'all5case_completions_finite_positive':True})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P61source_units_and_new_observation_adapter_complete',
        'plan_sha256':w.sha(PLAN),'original_T2b_peril_decomposition_available':False,'canonical_f_s_are_FSp_period_proxies':True,
        'units':'annual CUproxy=(canonicalFSpf*canonicalFSps)/rounded_exposure; not identified ultimate frequency/severity',
        'bindings':bindings,'outputs':outputs,'derived_historical_proxy_tables':3,'row_completion_applications':75,
        'new_real_price_fits':0,'new_CDF_fits':0,'new_source_model_inference':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','T2b_peril_decomposition':False,'actual_proxy':'FSp','historical_bindings':15,'new_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');assert d['plan_sha256']==w.sha(PLAN)
    assert all(w.sha(ROOT/p)==value for p,value in d['outputs'].items())
    next_unit='P62: separately preregister complete standard P55fixed-half learner with ONLYthe observation-link substitution to explicit fixedFSpPROXYcomposition under savedP50/P52costCDFs.15primary+15adverse closed learners (30+30components,20+20residual stages), no GLM/source/CDFfits. Keep all unchanged global/cohort/family16/scenario/level/influence/transfer gates and full ultimateforward. Not a T2bdecomposition or identified truth; no automatic CSVor public tuning.'
    text='# P61: procedencia de FSp y nuevo enlace de observación\n\nCodex, '+utc()+'. La referencia P60pedía revisar tentativamente un perfil T2bpor peril. La evidencia guardada P21y el código separan dos cosas: T2baporta una tasa anual total, sin salidas por peril; las columnas f/sdel canónico proceden de FSpPROD. No se repitió aquella auditoría ni se renombraron sus valores como T2b.\n\n'
    text+='En FSp, fya incluye exposición del periodo y srepresenta una marca positiva observada. El canónico reescala fpor exposición redondeada/calendario; por eso(f·s)/exposición redondeada es un proxy anual monetario. La frecuencia se ajustó con completitud de coste: no identifica una frecuencia/severidad últimas independientes. La procedencia desarrollada de respuestas/reportes y los límites de covariables/historia/clima quedan explícitos, sin nueva revisión masiva del linaje.\n\n'
    text+='La hipótesis nueva toma ese perfil como PROXYde composición para ponderar las curvas de coste P50, común a los dos componentes de precio A1S/T2b. No se afirma que descomponga sus totales o sea la composición real. El marco conserva calendario una vez y distingue curvas nominales/reservas/cola por SHA. Pasaron3flujos sintéticos primarios/3adversos, anualización/exposición cancelada, cálculo diario escalar y replay final. Se prepararon3tablas históricas y75enlaces de completitud; cero ajustes reales/CDF/scoring/2025/envíos.\n\n'
    text+='Las recetas P55-P60no cambiaron: sus precios usaban tasas totales A1S/T2b, sin tratar f/scomo sus componentes. Persisten qpor peril compartido entre líneas donde el nombre coincide, préstamo entre mercados, marcas/censura, maestros sin fecha y fuente2024condicional. B00/F3c y todas las alternativas se conservan;2024es desarrollo adaptativo, sin mejora privada establecida o revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nPlan/evidencia: '+w.rel(PLAN)+'; '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'T2b_peril_decomposition_available':False,'profile_source':'FSpPRODexplicit_cost_PROXY',
        'new_real_price_fits':0,'new_CDF_fits':0,'new_source_inference':0,'new_scores':0,'new2025inference':0,'new_submissions':0,
        'next_unit':next_unit,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P61-PROXY-RESULTADO','P61: FSp/T2b diferenciados y enlace proxy comprobado, sin nuevos precios')}
    archive=R/'privado'/('corte_P61_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P61'),(R/'registro/semana2_mision_privada_actual.json','P61')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P61=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    w.update(R/'registro/semana2_contadores_propios_actual.json',{'phase2_private_P61_proxy_observation_preflight':w.read(OUT/'synthetic.json')},archive)
    note='\n\n## Privada P61: identidad FSp/T2b y enlace proxy\n\nCodex, '+receipt['utc']+'.T2bsin descomposición por peril; f/sdel canónico son proxies FSpde periodo. Enlace nuevo con curvas P50probado sintéticamente,15entradas históricas/75completitudes sin ajustes o scores reales. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_proxy_observation_preflight_index':w.rel(INDEX),'week_2_private_proxy_observation_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_scores':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['register','run','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
