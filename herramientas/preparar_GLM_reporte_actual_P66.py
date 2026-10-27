"""Preflight del GLM estándar cross-fit con el enlace P64/P65 actual."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util
import argparse
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(s);s.loader.exec_module(v);return v
x=load('p66_existing_crossfit',R/'herramientas/preparar_crossfit_GLM_P59.py')
t=load('p66_current_reporting',R/'herramientas/validar_reporte_por_ramo_P65.py')
g=x.g;k=x.k;m=x.m;q=x.q;w=x.w;np=x.np;pd=x.pd;BASE=x.BASE
OUT=BASE/'P66_GLM_reporte_actual_preflight_20261027'
PLAN=R/'registro/semana2_GLM_reporte_actual_preflight_plan.json';INDEX=R/'registro/semana2_GLM_reporte_actual_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P66_GLM_REPORTE_ACTUAL_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def proxy_columns(line):return ['FSp_annual_cost_proxy_'+name for name in q.PERILS[line]]


def raw_frame(frame,line):
    z=x.raw_frame(frame,line)
    for name in proxy_columns(line):z[name]=frame[name].to_numpy(float)
    assert not any(name.startswith(('q_','baseline_','e_cost')) or name=='is_held' for name in z)
    return z


def reporting(source,claims,frames,ids):
    # No exterior cap, curve, target-peril share or fitted price enters this scope.
    pooled=q.pool_claims(source,claims,ids)
    parent={'tmax_days':int(pooled.window.max()),'records':[{'peril':name,'cap_CDF_weight_p995':float(np.quantile(z.net.to_numpy(float),.995))} for name,z in pooled.groupby('peril',sort=True)]}
    curves={line:t.t.line_curves(pooled,line,parent) for line in q.LINES}
    return {'line_curves':curves,'parent_caps':parent,'training_row_ids_digest':m.p.b.digest(sorted(ids))}


def with_q(frame,line,report):
    z=frame.copy();z['q_paired']=t.u.row_q(z,z[proxy_columns(line)].to_numpy(float),report['line_curves'][line],q.PERILS[line]);return z


def build_inner(frames,source,claims,outer,partition,folder):
    pieces={line:[] for line in frames};records=[]
    for member in range(5):
        ids={rid for line,f in frames.items() for rid in f.loc[f.fold.ne(outer)&f.group_id.map(partition).ne(member),'row_id']}
        local=folder/f'inner{member}'
        primary=m.once(local,'report_primary',lambda:reporting(source,claims,frames,ids))
        adverse=m.once(local,'report_adverse',lambda:reporting(source,x.poisoned_claims(claims,ids),frames,ids));assert primary==adverse
        assert sum(len(z['curves']) for z in primary['line_curves'].values())==15
        for line,raw in frames.items():
            f=raw.loc[raw.fold.ne(outer)].copy().reset_index(drop=True);f['is_held']=f.group_id.map(partition).eq(member)
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            f=with_q(f,line,primary);destination=local/line
            a=m.once(destination,'base_primary',lambda:k.learn(f,line));b=m.once(destination,'base_adverse',lambda:k.learn(x.cost_poison(f),line));assert a==b
            assert a['fit_row_ids_digest']==m.p.b.digest(sorted(f.loc[~f.is_held,'row_id']))
            held=f.loc[f.is_held].copy();value,norm=k.forward(held,a,True);poison=x.cost_poison(f).loc[f.is_held].copy();poison['q_paired']=np.nan
            other,nn=k.forward(poison,json.loads(json.dumps(b)),True);assert np.array_equal(value,other) and norm==nn
            held['baseline_ultimate']=value;held['baseline_observed']=value*held.q_paired.to_numpy();held['crossfit_member']=member;held['is_held']=False
            pieces[line].append(held)
            record={'outer':outer,'member':member,'line':line,'training_rows':int((~f.is_held).sum()),'OOFrows':len(held),
                'base_training_row_ids_digest':a['fit_row_ids_digest'],'report_training_row_ids_digest':primary['training_row_ids_digest'],
                'base_constants':k.constant_counts(a),'actual_report_and_price_poison_invariance':True,'ultimate_normalizers':norm}
            dump(destination/'committed.json',{'record':record,'outputs':{w.rel(path):w.sha(path) for path in destination.iterdir() if path.is_file()}})
            records.append(record)
    result={}
    for line,raw in frames.items():
        z=pd.concat(pieces[line]);expected=raw.loc[raw.fold.ne(outer),'row_id'];assert z.row_id.is_unique and set(z.row_id)==set(expected)
        z=z.set_index('row_id',drop=False).loc[expected].reset_index(drop=True)
        assert z.groupby('group_id').crossfit_member.nunique().max()==1 and not z.is_held.any();result[line]=z
    return result,records


def synthetic():
    rng=np.random.default_rng(2026102766);n=600;frames={};target=[];source=[]
    for line in q.LINES:
        i=np.arange(n);year=2023+(i//5)%2
        f=pd.DataFrame({'row_id':[line+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],'fold':i%5,'year':year,'new_business':(i//10)%2,
            'T0':np.round(rng.gamma(2,90,n)*(rng.random(n)<.5),2),'reserve':0.,'annual_A1S':np.exp(rng.normal(0,.3,n)),'annual_T2b':np.exp(rng.normal(4,.3,n)),
            'prior_claims_5y':rng.integers(0,3,n),'ncb_years':rng.integers(0,15,n),'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),
            'marketing_segment':rng.choice(['a','b','c'],n),'period_start':pd.to_datetime(np.where(year==2023,'2023-01-01','2024-01-01')),
            'period_end':pd.to_datetime(np.where(year==2023,'2023-12-31','2024-12-31'))})
        f['exposure_calendar']=(f.period_end-f.period_start).dt.days.add(1)/365.
        for name in g.NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in g.CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        for name in proxy_columns(line):f[name]=np.exp(rng.normal(3,.5,n))
        frames[line]=raw_frame(f,line)
        claims=f[['row_id','line','period_start','T0']].rename(columns={'period_start':'loss_date'}).copy();claims['claim_id']='T'+claims.row_id
        claims['peril']=rng.choice(q.PERILS[line],n);claims['report_date']=claims.loss_date+pd.to_timedelta(rng.integers(0,71,n),unit='D')
        claims['T0_cents']=np.rint(claims.T0*100).astype('int64');claims['reserve_cents']=0;claims['included_in_T0']=True;target.append(claims.drop(columns='T0'))
        for peril in q.PERILS[line]:
            for j in range(12):
                loss=pd.Timestamp('2020-01-01')+pd.Timedelta(days=j*30)
                source.append({'claim_id':line+peril+str(j),'line':line,'peril':peril,'loss_date':loss,'report_date':loss+pd.Timedelta(days=j*10),'net':float(100+j*10),'market':'source'})
    source=pd.DataFrame(source);target=pd.concat(target,ignore_index=True);outer=0;folder=OUT/'synthetic/outer0'
    partition=pd.Series({'g'+str(i):(i//5)%5 for i in range(n) if i%5!=outer})
    oof,records=build_inner(frames,source,target,outer,partition,folder)
    ids={rid for f in frames.values() for rid in f.loc[f.fold.ne(outer),'row_id']}
    primary=m.once(folder,'outer_report_primary',lambda:reporting(source,target,frames,ids))
    adverse=m.once(folder,'outer_report_adverse',lambda:reporting(source,x.poisoned_claims(target,ids),frames,ids));assert primary==adverse
    final_records=[]
    for line,raw in frames.items():
        f=with_q(raw,line,primary);f['is_held']=f.fold.eq(outer);local=folder/line
        a=m.once(local,'outer_base_primary',lambda:k.learn(f,line));b=m.once(local,'outer_base_adverse',lambda:k.learn(x.cost_poison(f),line));assert a==b
        held=f.loc[f.is_held].copy();value,_=k.forward(held,a,True);held['baseline_ultimate']=value;held['baseline_observed']=value*held.q_paired.to_numpy();held['crossfit_member']=-1
        final=pd.concat([oof[line],held],ignore_index=True);assert len(final)==len(raw) and final.row_id.is_unique
        model=m.once(local,'GLM_primary',lambda:g.fit(final,line,local/'GLM_primary_raw.json'))
        bad=m.once(local,'GLM_adverse',lambda:g.fit(g.poison(final,line),line,local/'GLM_adverse_raw.json'));assert model==bad
        assert not model['warnings'] and model['gradient_inf']<1e-5
        value,rel=g.forward(held,model);replay,other=g.forward(held,json.loads(json.dumps(bad)));assert np.array_equal(value,replay) and np.array_equal(rel,other)
        final_records.append({'line':line,'whole_report_base_GLM_flow_poison_invariance':True,'OOFtraining_rows':len(oof[line]),'outer_held_rows':len(held),'JSON_replay_exact':True,'gradient_inf':model['gradient_inf']})
    return {'author':'Codex','utc':utc(),'records':final_records,'synthetic_primary_line_CDFs':90,'synthetic_adverse_line_CDFs_separate':90,
        'synthetic_primary_cap_vectors':6,'synthetic_adverse_cap_vectors_separate':6,'synthetic_primary_base_learners':18,'synthetic_adverse_base_learners_separate':18,
        'synthetic_primary_components':36,'synthetic_adverse_components_separate':36,'synthetic_primary_residual_stages':24,'synthetic_adverse_residual_stages_separate':24,
        'synthetic_primary_GLMfits':3,'synthetic_adverse_GLMfits_separate':3,'real_fits':0,'real_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    prior=w.read(t.PLAN);m.check_sources(prior);assert w.read(t.OUT/'completion_receipt.json')['report_sha256']==w.sha(t.OUT/'report.json')
    paths=[Path(__file__),Path(x.__file__),Path(g.__file__),Path(k.__file__),Path(k.core.__file__),Path(k.core.b.__file__),Path(k.g.__file__),Path(t.t.__file__),
        t.PLAN,t.OUT/'report.json',t.OUT/'replay_report.json',t.OUT/'completion_receipt.json',q.CLAIMS,q.SOURCE_CLAIMS,x.PLAN,x.OUT/'report.json',x.OUT/'completion_receipt.json',
        R/'privado/intel_modelado_20261027_0.json',R/'privado/intel_modelado_20261027_1.json']
    for line in q.LINES:paths.extend([x.OUT/f'canonical_{line}.parquet',t.u.OUT/f'FSp_proxy_{line}.parquet'])
    paths.extend(m.P1/f'inner_groups_outer{outer}.parquet' for outer in range(5))
    sources=dict(prior['sources']);sources.update({w.rel(path):w.sha(path) for path in paths})
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Full synthetic preflight and real strict raw/proxy/partition joins only. ZEROreal curve/base/GLMfits or scores. Separate full evaluation registration required.',
        'need':'P62/P65fix the old common-line observation mismatch and recover P55loss but lack robust gain. P57/P60GLMtests used that materially different old observation contract; their failure does not establish failure under the current rowproxy/line curves. Test the SAMEstandard GLM after correcting that dependency, before any new capacity or field/hyperparameter search.',
        'hypothesis':'A fixed P56GLM with cross-fitted current-observation offsets may provide stable residual risk information. This is uncertain and adaptive; no claim that reporting caused the earlier GLMloss.',
        'architecture':'Same P60standard cross-fit layout and unchanged P56fields/alpha1. In every outer-training set, all5saved inner global-group folds get OWN pooled-peril p995caps then OWN15line/peril costCDFs and P54base. Fixed source-only FSpPROXYrow compositions. Each trainrow gets one OOFoffset. ONEGLMperline fits those train offsets; outerheld uses exact saved full-outerP65base. No inherited outercaps/CDFs/targetmeans for innerlearning, no targetfold mean.',
        'fields':{'numeric':g.NUM,'categorical':g.CAT,'parameters':g.PARAMS,'proxy_columns_are_reporting_only':True},
        'outer_and_inner':'Same saved outer0..4/inner0..4global component groups. Future full-data production innerhashseed5frozen by P59;80percent inner base/100percent full base scale mismatch remains part of algorithm, not a guarantee.',
        'preflight_criterion':'Whole synthetic report/base/GLMheld-payload invariance and JSONreplay, exact key/row/year/proxy joins, no inherited q/baseline flags in rawframes. Previous P64independent scalar curve/daily math receipts reused because those pure functions are unchanged.',
        'future_budget':{'primary_inner_reporting_scopes':25,'adverse_inner_reporting_scopes_separate':25,'primary_inner_line_CDFs':375,'adverse_inner_line_CDFs_separate':375,
            'primary_cap_vectors':25,'adverse_cap_vectors_separate':25,'primary_base_learners':75,'adverse_base_learners_separate':75,'primary_components':150,'adverse_components_separate':150,
            'primary_shared_residual_stages':100,'adverse_shared_residual_stages_separate':100,'primary_GLMfits':15,'adverse_GLMfits_separate':15,'new_source_fits':0,'outer_base_refits':0,'new2025inference':0,'new_submissions':0},
        'future_criterion':'Every unchanged P65global/cohort/family16/scenario/level/influence guard plus existing GLMconvergence. Pooled failure rejects admission, transfer=None. Pooled pass needs OWN2023-only conditional-transfer whole algorithm before any CSVadmission.',
        'intel':'Official MCPquery found4administrative/data topics and returned empty notebook search. No new public modeling recipe or leaderboard solution was imported. Not evidence that no public notebooks exist anywhere.',
        'limits':['Corrected observation may not improve GLMgeneralization. Fixed previous failures remain and no alpha/field rescue or publicprobe is authorized by them.',
            'Adaptive2023/2024, source2024conditional, borrowed proxy, ultimate-tail/reserve/market/undatedmaster assumptions and conditional bootstrap remain.'],
        'sources':sources,'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P66registra un preflight nuevo del mismo GLMP56/P60, campos y alpha1sin cambios, sobre el enlace de observaciónP64/P65que recuperó la pérdidaP55. No se infiere que mejore ni se repite el mismo experimento: qycurvas internas serán ahora proxyFSppor fila y15estratos ramo/peril, con topes aprendidos SOLOen cada ámbito interior. Toda base OOFexcluye ambos retenidos; el exteriorP65se usa solo en su retenido. Flujo sintético completo, unión real estricta sin q/base heredados; cero ajustes o scores reales. Una evaluación posterior exige25reportes/375CDFy75bases primarios/adversos separados,15+15GLM, todas las guardas intactas y transferencia propia si pasa. Sin nuevos árboles/variables/hiperparámetros/2025/envíos. B00preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P66registered_before_current_report_GLM_preflight','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P66-GLM-PREVIO','P66: mismo GLM estándar con observación actual y offsets protegidos')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    dump(OUT/'synthetic.json',synthetic());outputs={};bindings=[]
    for line in q.LINES:
        f=pd.read_parquet(x.OUT/f'canonical_{line}.parquet');profile=pd.read_parquet(t.u.OUT/f'FSp_proxy_{line}.parquet').set_index('row_id').loc[f.row_id]
        assert profile.index.is_unique and np.array_equal(profile.year,f.year)
        for name in proxy_columns(line):f[name]=profile[name].to_numpy(float)
        f=raw_frame(f,line);assert np.isfinite(f[proxy_columns(line)].to_numpy(float)).all() and (f[proxy_columns(line)].to_numpy(float)>0).all()
        path=OUT/f'canonical_{line}.parquet';f.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
        for outer in range(5):
            groups=pd.read_parquet(m.P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
            assert groups.index.is_unique and f.loc[f.fold.ne(outer),'group_id'].isin(groups.index).all()
            bindings.append({'line':line,'outer':outer,'rows':len(f),'held_rows':int(f.fold.eq(outer).sum()),'saved_inner_group_mapping_complete':True,'raw_target_and_source_keys_unchanged':True})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P66full_synthetic_and_real_raw_proxy_preflight_passed','plan_sha256':w.sha(PLAN),'bindings':bindings,'outputs':outputs,
        'real_price_fits':0,'real_CDF_fits':0,'real_GLMfits':0,'new_scores':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'preflight':'passed','real_bindings':15,'synthetic_GLMprimary':3,'synthetic_GLMadverse_separate':3,'new_real_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN));assert all(w.sha(ROOT/path)==value for path,value in d['outputs'].items())
    next_unit='P67: register and commit the complete SAMEalpha1GLM with current P64/P65observation and all5saved inner group offsets. Pin every new inner report/base artifact, use fullouterP65ONLYon held.25report scopes/375lineCDFs/75baselearners/15GLMprimary plus separate actual adverse fits. Every previous gate unchanged; no new source trees, tuned fields/alpha or publicprobe.'
    text='# P66: GLM estándar con el reporte actual, preflight\n\nCodex, '+utc()+'. El mismo GLM de efectos principales y alpha1se conecta al reporte actual por fila y ramo/peril. Los resultados adversos anteriores siguen vigentes; la nueva dependencia de observación justifica una prueba distinta y no demuestra mejora.\n\n'
    text+='Pasó un flujo exterior sintético con cinco particiones interiores:90curvas primarias/90adversas,18bases primarias/18adversas (36+36componentes,24+24etapas) y3GLMprimarios/3adversos. Cada topede coste, curva y base interior excluyó tanto el retenido exterior como el interior. La alteración real de etiquetas/fechas/perils/covariables retenidas y el replayJSONcoincidieron. Se reutilizó la matemática escalarP64sin repetir su suite.\n\n'
    text+='Se enlazaron15ámbitos reales con las claves y particiones guardadas; los campos raw no contienen q, precios base o banderas heredadas. Los perfilesFSpse guardan solo para reporte, fuera del diseño delGLM. No se ajustaron ni puntuaron modelos reales, CDFo2025; ningún envío. Faltan evaluación completa y transferencia si pasa. Persisten límites de mercado/cola/reservas, fuente2024condicional y búsqueda adaptativa; no validación independiente. B00/F3cyalternativas conservados,2024abierto.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'real_price_fits':0,'real_CDF_fits':0,'real_GLMfits':0,'new_scores':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P66-GLM-RESULTADO','P66: flujo GLM con reporte actual protegido, sin ajuste real')}
    archive=R/'privado'/('corte_P66_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P66'),(R/'registro/semana2_mision_privada_actual.json','P66')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    counts=R/'registro/semana2_contadores_propios_actual.json';w.update(counts,{'phase2_private_P66_GLM_current_preflight':{**receipt,'synthetic':w.read(OUT/'synthetic.json')}},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P66=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P66: GLM con reporte actual, preflight\n\nCodex, '+receipt['utc']+'.Flujo completo sintético y15enlaces estrictos pasaron; cero ajustes o scores reales/envíos. Misma recetaGLM, sin rescatar hiperparámetros. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_GLM_current_reporting_preflight_index':w.rel(INDEX),'week_2_private_GLM_current_reporting_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
