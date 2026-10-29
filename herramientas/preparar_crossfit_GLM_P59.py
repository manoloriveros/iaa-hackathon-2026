"""Preflight integral de calibración cross-fit: reporte, base y GLM protegidos."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import hashlib
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p59_existing_offset',R/'herramientas/validar_GLM_offset_P57.py')
t=importlib.util.module_from_spec(s);s.loader.exec_module(t)
g=t.g;k=g.k;m=t.m;q=m.q;w=t.w;np=t.np;pd=t.pd;BASE=t.BASE
OUT=BASE/'P59_crossfit_preflight_20261027'
PLAN=R/'registro/semana2_crossfit_GLM_preflight_plan.json';INDEX=R/'registro/semana2_crossfit_GLM_preflight_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P59_CROSSFIT_GLM_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(p,v):return m.dump(p,v)


def inner_fold(seed,group):
    return int(hashlib.sha256(f'H1-NEST-v1|{seed}|{group}'.encode('utf8')).hexdigest()[:16],16)%5


def raw_frame(f,line):
    columns=['row_id','line','year','group_id','fold','new_business','T0','reserve','period_start','period_end',
        'exposure_calendar','annual_A1S','annual_T2b','prior_claims_5y']+(['ncb_years'] if line=='motor' else [])
    columns+=k.g.STAGES[line]+g.NUM[line]+g.CAT[line]
    columns=list(dict.fromkeys(columns));result=f[columns].copy()
    assert not any(c.startswith(('baseline_','q_','e_cost')) or c=='is_held' for c in result)
    return result


def poisoned_claims(claims,ids):
    z=claims.copy();protected=~z.row_id.isin(ids)
    for name in ['peril','loss_date','report_date']:
        z[name]=z[name].astype('object');z.loc[protected,name]='INVALID_PROTECTED'
    z.loc[protected,['T0_cents','reserve_cents']]=-10**12
    return z


def reporting(source,claims,frames,ids):
    # Scope keys are applied BEFORE parsing targets/perils/dates or fitting the cost-weight cap.
    selected=q.pool_claims(source,claims,ids);curves=q.cost_curves(selected)
    target=m.selected_claims(claims,ids,1.);shares={}
    for line,f in frames.items():
        train=f.loc[f.row_id.isin(ids)].copy();sel=target.loc[target.line.eq(line)]
        vector=m.train_shares(train,sel,curves,q.PERILS[line]);shares[line]=dict(zip(q.PERILS[line],vector.tolist()))
    return {'curves':curves,'shares':shares,'training_row_ids_digest':m.p.b.digest(sorted(ids))}


def with_q(f,line,report):
    z=f.copy();shares=np.array([report['shares'][line][p] for p in q.PERILS[line]])
    z['q_paired']=m.apply_q(z,report['curves'],q.PERILS[line],shares);return z


def cost_poison(f):
    z=f.copy();z.loc[z.is_held,['T0','reserve']]=-1e30;return z


def build_inner(frames,source,claims,outer,partition,folder):
    """Exactly five scoped reports and15base learners, each with a real adverse fit."""
    pieces={line:[] for line in frames};records=[]
    for member in range(5):
        ids=set()
        for line,f in frames.items():
            train=f.fold.ne(outer)&f.group_id.map(partition).ne(member)
            ids.update(f.loc[train,'row_id'])
        local=folder/f'inner{member}'
        primary=m.once(local,'report_primary',lambda:reporting(source,claims,frames,ids))
        bad=poisoned_claims(claims,ids)
        adverse=m.once(local,'report_adverse',lambda:reporting(source,bad,frames,ids));assert primary==adverse
        assert primary['training_row_ids_digest']==m.p.b.digest(sorted(ids)) and len(primary['curves']['curves'])==11
        for line,raw in frames.items():
            f=raw.loc[raw.fold.ne(outer)].copy().reset_index(drop=True)
            f['is_held']=f.group_id.map(partition).eq(member)
            assert set(f.loc[~f.is_held,'row_id']).issubset(ids)
            assert set(f.loc[~f.is_held,'group_id']).isdisjoint(set(f.loc[f.is_held,'group_id']))
            f=with_q(f,line,primary);destination=local/line
            a=m.once(destination,'base_primary',lambda:k.learn(f,line))
            aa=m.once(destination,'base_adverse',lambda:k.learn(cost_poison(f),line));assert a==aa
            assert a['fit_row_ids_digest']==m.p.b.digest(sorted(f.loc[~f.is_held,'row_id']))
            held=f.loc[f.is_held].copy();u,norm=k.forward(held,a,True)
            bh=cost_poison(f).loc[f.is_held].copy();bh['q_paired']=np.nan;uu,nn=k.forward(bh,aa,True)
            assert np.array_equal(u,uu) and norm==nn
            held['baseline_ultimate']=u;held['baseline_observed']=u*held.q_paired.to_numpy();held['crossfit_member']=member
            held['is_held']=False;pieces[line].append(held)
            record={'outer':outer,'member':member,'line':line,'base_training_rows':int((~f.is_held).sum()),'OOFrows':len(held),
                'training_row_ids_digest':a['fit_row_ids_digest'],'report_training_row_ids_digest':primary['training_row_ids_digest'],
                'base_constants':k.constant_counts(a),'report_and_base_actual_poison_invariance':True,'ultimate_normalizers':norm}
            dump(destination/'committed.json',{'record':record,'outputs':{w.rel(p):w.sha(p) for p in destination.iterdir() if p.is_file()}})
            records.append(record)
    result={}
    for line,raw in frames.items():
        z=pd.concat(pieces[line]);expected=raw.loc[raw.fold.ne(outer),'row_id']
        assert z.row_id.is_unique and set(z.row_id)==set(expected)
        z=z.set_index('row_id',drop=False).loc[expected].reset_index(drop=True)
        assert z.groupby('group_id').crossfit_member.nunique().max()==1 and not z.is_held.any()
        result[line]=z
    return result,records


def synthetic():
    rng=np.random.default_rng(2026102759);n=600;frames={};target=[]
    for line in q.LINES:
        i=np.arange(n);year=2023+(i//5)%2
        f=pd.DataFrame({'row_id':[line+str(j) for j in i],'line':line,'year':year,'group_id':['g'+str(j) for j in i],
            'fold':i%5,'new_business':(i//10)%2,'T0':np.round(rng.gamma(2,80,n)*(rng.random(n)<.5),2),'reserve':0.,
            'period_start':pd.to_datetime(np.where(year==2023,'2023-01-01','2024-01-01')),
            'period_end':pd.to_datetime(np.where(year==2023,'2023-12-31','2024-12-31')),
            'annual_A1S':np.exp(rng.normal(0,.3,n)),'annual_T2b':np.exp(rng.normal(4,.3,n)),
            'prior_claims_5y':rng.integers(0,3,n),'ncb_years':rng.integers(0,15,n),
            'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
        f['exposure_calendar']=(f.period_end-f.period_start).dt.days.add(1)/365.
        for name in g.NUM[line]:f[name]=rng.choice([0.,10.,100.],n)
        for name in g.CAT[line]:
            if name!='new_business':f[name]=rng.choice(['a','b','c'],n)
        frames[line]=raw_frame(f,line)
        claims=f[['row_id','line','period_start','T0']].rename(columns={'period_start':'loss_date'}).copy()
        claims['claim_id']='T'+claims.row_id;claims['peril']=rng.choice(q.PERILS[line],n)
        claims['report_date']=claims.loss_date+pd.to_timedelta(rng.integers(0,71,n),unit='D')
        claims['T0_cents']=np.rint(claims.T0*100).astype('int64');claims['reserve_cents']=0;claims['included_in_T0']=True
        target.append(claims.drop(columns='T0'))
    target=pd.concat(target,ignore_index=True);allperils=sorted({p for v in q.PERILS.values() for p in v});rows=[]
    for j,peril in enumerate(allperils):
        for i in range(8):
            loss=pd.Timestamp('2018-01-01')+pd.Timedelta(days=i*180)
            rows.append({'claim_id':'SRC'+str(j*8+i).zfill(7),'line':next(line for line in q.LINES if peril in q.PERILS[line]),'peril':peril,'loss_date':loss,
                'report_date':loss+pd.Timedelta(days=[0,7,30,120][i%4]),'net':float(50+20*i),'market':'source'})
    source=pd.DataFrame(rows);records=[]
    for outer in [0,1]:
        folder=OUT/'synthetic'/f'outer{outer}'
        groups=pd.Series({str('g'+str(i)):(i//5)%5 for i in range(n) if i%5!=outer})
        oof,rr=build_inner(frames,source,target,outer,groups,folder);ids={rid for f in frames.values() for rid in f.loc[f.fold.ne(outer),'row_id']}
        report=m.once(folder,'outer_report_primary',lambda:reporting(source,target,frames,ids))
        adverse_report=m.once(folder,'outer_report_adverse',lambda:reporting(source,poisoned_claims(target,ids),frames,ids));assert report==adverse_report
        for line,raw in frames.items():
            f=with_q(raw,line,report);f['is_held']=f.fold.eq(outer);local=folder/line
            base=m.once(local,'outer_base_primary',lambda:k.learn(f,line));badbase=m.once(local,'outer_base_adverse',lambda:k.learn(cost_poison(f),line));assert base==badbase
            held=f.loc[f.is_held].copy();u,_=k.forward(held,base,True);held['baseline_ultimate']=u;held['baseline_observed']=u*held.q_paired.to_numpy();held['crossfit_member']=-1
            final=pd.concat([oof[line],held],ignore_index=True);assert len(final)==n
            primary=m.once(local,'GLM_primary',lambda:g.fit(final,line,local/'GLM_primary_raw.json'))
            adverse=m.once(local,'GLM_adverse',lambda:g.fit(g.poison(final,line),line,local/'GLM_adverse_raw.json'));assert primary==adverse
            assert not primary['warnings'] and primary['gradient_inf']<1e-5
            predicted,relative=g.forward(held,primary);other,rel=g.forward(held,json.loads(json.dumps(primary)))
            assert np.array_equal(predicted,other) and np.array_equal(relative,rel)
            records.append({'outer':outer,'line':line,'OOFtraining_rows':len(oof[line]),'outer_held_rows':len(held),
                'all_learning_ancestry_exclusions':True,'actual_whole_composition_poison_invariance':True,'JSON_final_forward_exact':True})
    return {'author':'Codex','utc':utc(),'records':records,'synthetic_primary_cost_CDF_estimators':132,
        'synthetic_adverse_cost_CDF_estimators_separate':132,'synthetic_primary_base_learners':36,
        'synthetic_adverse_base_learners_separate':36,'synthetic_primary_components':72,'synthetic_adverse_components_separate':72,
        'synthetic_primary_shared_residual_stages':48,'synthetic_adverse_shared_residual_stages_separate':48,
        'synthetic_primary_GLMfits':6,'synthetic_adverse_GLMfits_separate':6,'real_fits':0,'real_scores':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=BASE/'P58_diagnostico_GLM_20261027';assert (parent/'completion_receipt.json').exists()
    paths=[Path(__file__),Path(t.__file__),Path(g.__file__),Path(k.__file__),Path(k.core.__file__),Path(k.core.b.__file__),
        Path(k.g.__file__),Path(m.__file__),Path(q.__file__),Path(w.__file__),q.SOURCE_CLAIMS,q.CLAIMS,
        parent/'report.json',parent/'completion_receipt.json',g.PLAN,g.OUT/'completion_receipt.json',
        m.P1/'report.json',R/'herramientas/preflight_anidado_H1.py',R/'registro/semana2_mision_privada_plan_v1.json',
        BASE/'A1S_nucleo_20261026_v1/source_models/report.json',R/'registro/semana2_mision017_A1S_fuente_plan_v1.json']
    for line in q.LINES:
        for outer in range(5):
            paths += [g.OUT/f'input_{line}_{outer}.parquet',g.v.OUT/f'{line}_{outer}/learning.json',g.v.OUT/f'{line}_{outer}/committed.json']
    paths += [m.P1/f'inner_groups_outer{outer}.parquet' for outer in range(5)]
    OUT.mkdir();(OUT/'registered_code.py').write_bytes(Path(__file__).read_bytes())
    plan={'author':'Codex','utc':utc(),'scope':'Synthetic end-to-end report/base/GLMflow plus raw real input/partition binding ONLY. No real costcurve/base/GLMfit or score in P59.',
        'hypothesis':'P58documented in-sample/held discrepancy. Cross-fitted offsets may reduce dependence on in-sample P54base fits; this is a standard stacking design, not a proved explanation or gain.',
        'reference':'https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html',
        'architecture':'Inside each existing global outer training set, use all5SAVEDinner group folds. Eachinner source+targettraining costCDFand target-peril shares exclude BOTHouterheld and innerheld. Learn P54base on owninnertraining, apply to innerheld to fill exactly one OOFoffset per outer-training row. Fit ONEP56GLMperline on these OOFoffsets, same fields/alpha1. Apply it to the saved full-outer P55base on outerheld. No mean5models or selected weights. All targets/exposure/source-only coefficients unchanged.',
        'source_ancestry':'Whitelist raw source/covariate fields, stripping inherited q, costexposure, P55prices/normalizers and held markers before ANYinner learning. Outer P55base may be reused ONLYfor finalouterheld prediction, never inner OOFtraining. No source price refits.',
        'partitions':'Existing5global outerfolds and inner_groups_outer0..4 unchanged. Final production uses identical H1-NEST-v1hash with fixed seed5 for its innergroups, recorded BEFOREpricefitting. Perouter training64percent/outerbase80percent; productioninner80percent/fullbase100percent. Same1.25training-size ratio, no guarantee of equality of performance.',
        'current_synthetic_budget':{'outer_cases':2,'primary_costCDF_estimators':132,'adverse_costCDF_estimators_separate':132,
            'primary_base_learners':36,'adverse_base_learners_separate':36,'primary_components':72,'adverse_components_separate':72,
            'primary_shared_residual_stages':48,'adverse_shared_residual_stages_separate':48,'primary_GLMfits':6,'adverse_GLMfits_separate':6},
        'future_real_budget':{'inner_report_scopes':25,'primary_costCDF_estimators':275,'adverse_costCDF_estimators_separate':275,
            'primary_target_share_vectors':75,'adverse_target_share_vectors_separate':75,'primary_share_coordinates':375,'adverse_share_coordinates_separate':375,
            'primary_inner_base_learners':75,'adverse_inner_base_learners_separate':75,'primary_components':150,'adverse_components_separate':150,
            'primary_shared_residual_stages':100,'adverse_shared_residual_stages_separate':100,
            'primary_GLMfits':15,'adverse_GLMfits_separate':15,'outer_base_refits':0,'source_price_refits':0,
            'new2025inference':0,'new_submissions':0},
        'before_real_learning':'A separate cost/config/criterion registration, forum and commit for the exact complete algorithm. Keep every unchanged global/cohort/family16/scenario/level/influence/transfer/convergence guard; no admission from fixture/support metadata. Reuse saved support only by exact membership digest, not a repeated audit.',
        'limits':['Adaptive2023/2024, source2024conditional and supplied snapshots/reporting/ultimate-tail assumptions unchanged.',
            'OOFvsfull base training sizes and batch normalizers differ as explicitly modeled; no claim cross-fitting alone proves private gain.',
            'Independent physical per-row peril mixture not established; currentcommon costqassumption remains. No professional independent validation.'],
        'sources':{w.rel(p):w.sha(p) for p in paths},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P59registra antes del fixture el flujo estándar de calibración cross-fit: cinco particiones interiores guardadas, curva y cuotas propias sin grupos exteriores/interiores retenidos, base P54propia y un offset OOFpor fila para el GLM P56fijo. La base exterior P55solo se usa al predecir su retenido. Ningún q/precio exterior entra en el aprendizaje interior. Producción futura: interior80%/base100%con semilla hash5fijada ahora; evaluación64%/80%, sin media5modelos. Dos casos sintéticos exteriores:132CDFprimarias/132adversas,36bases/36adversas,72componentes/72adversos y6GLM/6adversos. Se comprobará el aprendizaje numérico real del fixture, no solo metadatos. P59real solo enlaza fuentes/particiones y reutiliza soporte por digest; cero ajuste real/score/2025/envío. Hipótesis de mejora no establecida, B00/F3c/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P59registered_before_end_to_end_synthetic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P59-CROSSFIT-PREVIO','P59: flujo cross-fit con curvas propias, antes del fixture numérico')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    assert (OUT/'registered_code.py').read_bytes()==Path(__file__).read_bytes()
    dump(OUT/'synthetic.json',synthetic());frames={};outputs={};bindings=[]
    support=w.read(m.P1/'report.json');lookup={(a['outer'],a['member'],a['line']):a for a in support['scopes']}
    for line in q.LINES:
        first=raw_frame(pd.read_parquet(g.OUT/f'input_{line}_0.parquet'),line)
        for outer in range(1,5):
            other=raw_frame(pd.read_parquet(g.OUT/f'input_{line}_{outer}.parquet'),line)
            assert first.equals(other),'Raw source/features differ between parent scopes'
        inherited=pd.read_parquet(g.OUT/f'input_{line}_0.parquet');bad=inherited.copy()
        for name in ['baseline_ultimate','baseline_observed','q_paired']:bad[name]='INVALID_INHERITED'
        assert raw_frame(bad,line).equals(first)
        frames[line]=first;path=OUT/f'canonical_{line}.parquet';first.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
    allrows=pd.concat(list(frames.values()),ignore_index=True);assert len(allrows)==109296 and allrows.row_id.is_unique
    groups=allrows[['group_id','fold']].drop_duplicates().sort_values('group_id')
    final=groups.copy();final['inner_fold']=[inner_fold(5,str(group)) for group in final.group_id]
    path=OUT/'production_inner_groups_seed5.parquet';final.to_parquet(path,index=False);outputs[w.rel(path)]=w.sha(path)
    for outer in range(5):
        inner=pd.read_parquet(m.P1/f'inner_groups_outer{outer}.parquet').set_index('group_id').inner_fold
        assert all(int(value)==inner_fold(outer,str(group)) for group,value in inner.items())
        for member in range(5):
            for line,f in frames.items():
                training=f.fold.ne(outer)&f.group_id.map(inner).ne(member);held=f.fold.ne(outer)&f.group_id.map(inner).eq(member)
                assert set(f.loc[training,'group_id']).isdisjoint(set(f.loc[~training,'group_id']))
                parent=lookup[(outer,member,line)];digest=m.p.b.digest(sorted(f.loc[training,'row_id']))
                assert digest==parent['training_row_digest'] and parent['numerical_support_passed']
                bindings.append({'outer':outer,'member':member,'line':line,'training_rows':int(training.sum()),'innerheld_rows':int(held.sum()),
                    'training_row_ids_digest':digest,'saved_numerical_support_reused_by_exact_keys':True})
    assert len(bindings)==75;m.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P59numeric_synthetic_and_real_membership_preflight_complete','plan_sha256':w.sha(PLAN),
        'bindings':bindings,'outputs':outputs,'real_fits':0,'real_scores':0,'new2025inference':0,'new_submissions':0,
        'stripped_parent_target_objects_poison_invariant':True,'production_hash_seed5_frozen':True,'new_support_audit':False})
    print(json.dumps({'preflight':'passed','real_bindings':75,'synthetic_outer_cases':2,'real_fits':0,'new_scores':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');assert d['plan_sha256']==w.sha(PLAN)
    assert all(w.sha(ROOT/p)==vv for p,vv in d['outputs'].items());fixture=w.read(OUT/'synthetic.json')
    next_unit='P60: register and commit complete cross-fitted P56GLM validation using P59raw canonical data/partitions.25OWNinner reports(275+275CDFs),75+75base learners(150+150components,100+100residual stages),15+15GLMs. Reuse P55outer base ONLYfor outerheldapplication; no source refits, no inherited outerq/base in innertrain. Preserve ALLoriginal gates, convergence and own conditional-transfer requirement. Freeze final production innerhashseed5, no mean5models or public tuning.'
    text='# P59: flujo completo de calibración fuera del grupo\n\nCodex, '+utc()+'. Se comprobó el flujo numérico sintético de reporte, cuotas, base y GLMen dos particiones exteriores, con las cinco interiores en cada una. Todos los controles adversos conservaron objetos y predicciones; la serialización final fue exacta.\n\n'
    text+='El GLM aprende de una predicción base por fila que excluyó su grupo, y se aplica sobre la base exterior completa. Cada curva/cuota/base interior tiene sus propios grupos permitidos: no se reutilizan objetos exteriores con ancestros protegidos. Los precios y qheredados se eliminaron antes del enlace interior; contaminar esos campos no cambió el canónico. El diseño sigue la idea estándar de [stacking con predicciones cruzadas](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.StackingRegressor.html), sin prometer una ganancia.\n\n'
    text+='Fixture:132CDFprimarias y132adversas,36bases/36adversas (72+72componentes y48+48etapas residuales),6GLM/6adversos. Real:75enlaces interiores por claves idénticas al soporte guardado, sin repetir esa auditoría o equipararla a credibilidad; cero curvas/precios ajustados o scores reales. Se guardó ahora la partición interior final con semilla5, sin seleccionar por resultados. Los tamaños64%/80%de evaluación y80%/100%de producción conservan la proporción1,25, sin garantía de igualdad de error.\n\n'
    text+='Permanecen fuente2024condicional, maestros sin fecha, qcomún por ramo y cola/reservas.2023/2024son desarrollo adaptativo, no confirmación independiente o mejora privada establecida. B00/F3c/adversos conservados, cero inferencias2025o envíos.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'real_fits':0,'real_scores':0,'new2025inference':0,'new_submissions':0,'next_unit':next_unit,
        'production_hash_seed':5,'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P59-CROSSFIT-RESULTADO','P59: flujo numérico cross-fit comprobado, sin ajustar datos reales')}
    archive=R/'privado'/('corte_P59_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir()
    w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P59'),(R/'registro/semana2_mision_privada_actual.json','P59')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P59=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    w.update(R/'registro/semana2_contadores_propios_actual.json',{'phase2_private_P59_crossfit_preflight':fixture},archive)
    note='\n\n## Privada P59: cross-fit integral, preflight\n\nCodex, '+receipt['utc']+'.Fixture numérico integral y75enlaces reales por claves pasaron; cero ajuste/score real/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_crossfit_GLM_preflight_index':w.rel(INDEX),'week_2_private_crossfit_GLM_preflight_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');p=argparse.ArgumentParser(description=__doc__);p.add_argument('mode',choices=['register','run','close']);args=p.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
