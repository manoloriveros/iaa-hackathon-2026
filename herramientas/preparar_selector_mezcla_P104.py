"""Selector común de cinco mezclas con reaprendizaje G propio y caché 50/50."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import importlib.util
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p104_protected_mix_scopes',R/'herramientas/preparar_mezcla_interna_P103.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
base=p.p.k;scopes=p.scopes;m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.p.np;BASE=p.BASE
GRID=[0.,.25,.5,.75,1.]
ORIGINAL_HALF_FORWARD=base.forward;ORIGINAL_HALF_LEARN=base.learn
OUT=BASE/'P104_selector_mezcla_preflight_20261027'
PLAN=R/'registro/semana2_selector_mezcla_preflight_plan.json';INDEX=R/'registro/semana2_selector_mezcla_preflight_actual.json'
DOC=R/'docs/semana2/PRIVADA_P104_SELECTOR_MEZCLA_PREFLIGHT.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def poison(frame):
    bad=frame.copy()
    for name in bad:
        if name not in ['row_id','line','group_id','fold','is_held','year','period_start','period_end']:
            bad[name]=bad[name].astype('object');bad.loc[bad.is_held,name]='INVALID_HELD'
    return bad


def scope_check(frame,artifact):
    train=frame.loc[~frame.is_held]
    assert set(train.group_id).isdisjoint(set(frame.loc[frame.is_held,'group_id']))
    ids=m.p.b.digest(sorted(train.row_id));groups=m.p.b.digest(sorted(set(train.group_id)))
    assert artifact['fit_row_ids_digest']==ids and artifact['fit_groups_digest']==groups
    for obj in artifact['components'].values():assert obj['fit_row_ids_digest']==ids and obj['fit_groups_digest']==groups
    return train


def mixture(frame,artifact,weight,ultimate=True):
    assert weight in GRID
    first,second,_=base.components(frame,artifact,ultimate)
    value=weight*first+(1.-weight)*second
    assert np.isfinite(value).all() and (value>0).all()
    return value


def forward(frame,artifact,ultimate=True):
    weight=artifact.get('mix_weight',.5);value=mixture(frame,artifact,weight,ultimate);norms={}
    for stage in artifact['stages']:
        value,norm=base.g.apply_stage(frame,value,stage);norms[stage['variable']]=norm
    return value,norms


def fit_weight(frame,line,cached,weight,folder):
    def produce():
        train=scope_check(frame,cached).copy()
        if weight==.5:
            dump(folder/'reused_half.json',{'author':'Codex','utc':utc(),'cached_model_digest':m.p.b.digest(cached),'new_G_fits':0})
            return cached
        # The typed held poison leaves object columns. Convert ONLY train T0.
        train['T0']=pd.to_numeric(train.T0,errors='raise').astype(float)
        artifact={'line':line,'contract':'Own_scope_components_common_mix_weight_original_G',
            'mix_weight':weight,'components':cached['components'],'fit_row_ids_digest':cached['fit_row_ids_digest'],
            'fit_groups_digest':cached['fit_groups_digest']}
        value=mixture(train,artifact,weight,False);stages=[];norms={}
        for index,variable in enumerate(base.g.STAGES[line]):
            def learn_stage():
                dump(folder/f'actual_G{index}_fit.json',{'author':'Codex','utc':utc(),'weight':weight,'variable':variable,
                    'fit_ids_digest':artifact['fit_row_ids_digest'],'input_base_digest':base.g.digest(value.tolist())})
                return base.g.fit_stage(train,value,variable)
            stage=m.once(folder,f'G{index}_{variable}',learn_stage)
            assert stage['training_row_ids_digest']==artifact['fit_row_ids_digest']
            assert stage['training_groups_digest']==artifact['fit_groups_digest']
            assert stage['training_label_digest']==base.g.digest(train.T0.tolist())
            assert stage['input_base_digest']==base.g.digest(value.tolist())
            value,norm=base.g.apply_stage(train,value,stage);stages.append(stage);norms[variable]=norm
        artifact.update(stages=stages,training_normalizers=norms)
        dump(folder/'raw_model_before_validation.json',artifact)
        return artifact
    return m.once(folder,'model',produce)


def new_constants(artifact):
    if artifact.get('mix_weight',.5)==.5:return 0
    return sum(len(s['factors'])+len(s['nuisance_year_business'])+len(artifact['training_normalizers'][s['variable']]) for s in artifact['stages'])


def choose(losses):
    assert len(losses)==len(GRID) and np.isfinite(losses).all()
    minimum=min(losses);tolerance=1e-12*max(1.,abs(minimum))
    eligible=[i for i,value in enumerate(losses) if value<=minimum+tolerance]
    index=min(eligible,key=lambda j:(abs(GRID[j]-.5),GRID[j]))
    return {'index':index,'weight':GRID[index],'losses':list(losses),'tie_tolerance':tolerance,
        'criterion':'Total originalT0Tweedie15over all5innerfolds/3lines; common weight. Ties nearesthalf then smaller.'}


def validation_loss(frame,artifact):
    held=frame.loc[frame.is_held]
    price,_=forward(held,artifact,True);mu=price*held.q_paired.to_numpy(float);y=held.T0.to_numpy(float)
    value=float(m.e.unit(y,mu).sum())
    scalar=math.fsum(4*float(a)/math.sqrt(float(b))+4*math.sqrt(float(b))-8*math.sqrt(float(a)) for a,b in zip(y,mu))
    assert math.isclose(value,scalar,rel_tol=3e-12,abs_tol=1e-7)
    return value


def train_bundle(frames,tables,inner_bases,outer_bases,folder,adverse=False):
    losses=[0.]*len(GRID);refs=[]
    for member in range(5):
        scoped=scopes.inner_frames(frames,tables[member])
        for line in q.LINES:
            fitting=poison(scoped[line]) if adverse else scoped[line]
            for j,weight in enumerate(GRID):
                relative=f'i{member}/w{int(weight*100):03d}/{line}'
                artifact=fit_weight(fitting,line,inner_bases[member][line],weight,folder/relative)
                refs.append({'relative':relative,'sha256':w.sha(folder/relative/'model.json')})
                losses[j]+=validation_loss(scoped[line],artifact)
    selection=choose(losses);models={}
    for line in q.LINES:
        models[line]=fit_weight(frames[line],line,outer_bases[line],selection['weight'],folder/'final'/line)
    artifacts=[w.read(folder/z['relative']/'model.json') for z in refs]+list(models.values())
    return {'selection':selection,'models':models,'inner_refs':refs,'actual_Gfit_calls':len(list(folder.rglob('actual_G*_fit.json'))),
        'new_closed_constants_including_train_prediction_normalizers':sum(new_constants(a) for a in artifacts),
        'contract':'P104common_nested_source_weight_full_G_relearning_no_source_or_q_learning'}


def replay_bundle(frames,tables,bundle,folder,quote_frames=None):
    refs={z['relative']:z['sha256'] for z in bundle['inner_refs']};losses=[0.]*len(GRID)
    for member in range(5):
        scoped=scopes.inner_frames(frames,tables[member])
        for line in q.LINES:
            for j,weight in enumerate(GRID):
                relative=f'i{member}/w{int(weight*100):03d}/{line}';path=folder/relative/'model.json'
                assert w.sha(path)==refs[relative];artifact=w.read(path);assert artifact.get('mix_weight',.5)==weight
                losses[j]+=validation_loss(scoped[line],artifact)
    assert choose(losses)==bundle['selection']
    quoting=frames if quote_frames is None else quote_frames
    return {line:forward(quoting[line].loc[quoting[line].is_held].drop(columns=['T0','reserve','q_paired']),bundle['models'][line],True)[0] for line in q.LINES}


def synthetic_frames():
    rng=np.random.default_rng(20261027104);n=600;i=np.arange(n);frames={}
    for line in q.LINES:
        frames[line]=pd.DataFrame({'row_id':[line+str(j) for j in i],'line':line,'group_id':['g'+str(j) for j in i],
            'fold':i%5,'is_held':i%5==0,'year':2023+(i//25)%2,'new_business':(i//50)%2,
            'T0':rng.gamma(2,100,n)*(rng.random(n)<.35),'reserve':0.,'exposure_calendar':rng.uniform(.2,1,n),
            'q_paired':rng.uniform(.3,1,n),'annual_A1S':np.exp(rng.normal(0,.4,n)),'annual_T2b':np.exp(rng.normal(5,.5,n)),
            'ncb_years':rng.integers(0,15,n),'prior_claims_5y':rng.integers(0,3,n),
            'gender':rng.choice(['F','M'],n),'works_from_home':rng.integers(0,2,n),'marketing_segment':rng.choice(['a','b','c'],n)})
    return frames


def synthetic_tables(frames):
    result={member:{} for member in range(5)}
    for member in range(5):
        for line,raw in frames.items():
            f=raw.loc[~raw.is_held].copy();member_ids=f.group_id.str[1:].astype(int)//5%5;held=member_ids.eq(member)
            train=f.loc[~held];alpha=.6+.1*math.tanh(float(pd.to_numeric(train.T0).mean())/100.)
            table=f[['row_id','year','group_id']].copy();table['is_held']=held.to_numpy()
            table['q_paired']=alpha*(.8+.2*f.exposure_calendar.to_numpy(float));result[member][line]=table
    return result


def synthetic_bases(frames,tables,folder,adverse=False):
    def original(frame,line,path):
        fitting=poison(frame) if adverse else frame
        train=fitting.loc[~fitting.is_held].copy();assert set(train.group_id).isdisjoint(set(fitting.loc[fitting.is_held,'group_id']))
        train['T0']=pd.to_numeric(train.T0,errors='raise').astype(float)
        return m.once(path,line,lambda:ORIGINAL_HALF_LEARN(train,line))
    full={line:original(frame,line,folder/'outer') for line,frame in frames.items()}
    inner={member:{} for member in range(5)}
    for member in range(5):
        scoped=scopes.inner_frames(frames,tables[member])
        for line in q.LINES:inner[member][line]=original(scoped[line],line,folder/f'i{member}')
    return inner,full


def synthetic():
    frames=synthetic_frames();bad={line:poison(frame) for line,frame in frames.items()}
    tables=synthetic_tables(frames);bad_tables=synthetic_tables(bad)
    assert all(tables[i][line].equals(bad_tables[i][line]) for i in range(5) for line in q.LINES)
    inner,full=synthetic_bases(frames,tables,OUT/'synthetic/primary_bases')
    bad_inner,bad_full=synthetic_bases(bad,bad_tables,OUT/'synthetic/adverse_bases',True)
    assert inner==bad_inner and full==bad_full
    first=m.once(OUT/'synthetic','primary_bundle',lambda:train_bundle(frames,tables,inner,full,OUT/'synthetic/primary_fits'))
    second=m.once(OUT/'synthetic','adverse_bundle',lambda:train_bundle(bad,bad_tables,bad_inner,bad_full,OUT/'synthetic/adverse_fits',True))
    assert first==second and 80<=first['actual_Gfit_calls']<=84
    controls=[]
    for line in q.LINES:
        held=frames[line].loc[frames[line].is_held];old=full[line]
        expected,norm=ORIGINAL_HALF_FORWARD(held,old,True);value,nn=forward(held,old,True)
        assert np.array_equal(value,expected) and norm==nn
        one,two,_=base.components(held,old,True)
        assert np.array_equal(mixture(held,old,0.,True),two) and np.array_equal(mixture(held,old,1.,True),one)
        # Mandatory nonhalf final-scope control, regardless of selected fixture weight.
        control=fit_weight(frames[line],line,old,.25,OUT/'synthetic/forced_nonhalf'/line)
        assert control['components']==old['components'] and control['mix_weight']==.25
        scope_check(frames[line],control);controls.append({'line':line,'half_original_price_and_norms_bit_exact':True,'endpoints_equal_component_risks':True,'forced_nonhalf_final_scope_exercised':True})
    assert choose([1.,1.,1.,1.,1.])['weight']==.5
    assert choose([1.,1.,2.,1.,1.])['weight']==.25 and choose([0.,1.,2.,1.,0.])['weight']==0.
    original=(base.g.fit_stage,base.core.fit_component,q.cost_curves)
    def reject(*args,**kwargs):raise AssertionError('Selector replay forbids all new G/component/report learning')
    try:
        base.g.fit_stage=reject;base.core.fit_component=reject;q.cost_curves=reject
        replay=replay_bundle(frames,tables,first,OUT/'synthetic/primary_fits')
        alternate=replay_bundle(bad,bad_tables,json.loads(json.dumps(second)),OUT/'synthetic/adverse_fits',quote_frames=frames)
        for line in q.LINES:
            expected=forward(frames[line].loc[frames[line].is_held].drop(columns=['T0','reserve','q_paired']),first['models'][line],True)[0]
            assert np.array_equal(replay[line],expected) and np.array_equal(alternate[line],expected)
    finally:base.g.fit_stage,base.core.fit_component,q.cost_curves=original
    return {'author':'Codex','utc':utc(),'controls':controls,'synthetic_selected_weight':first['selection']['weight'],
        'whole_outer_and_inner_learning_poison_exact':True,'all75inner_objectives_and_selector_replayed':True,
        'all3final_models_replayed_with_learning_blocked':True,'tie_controls_pass':True,
        'synthetic_original_primary_component_fits':36,'synthetic_original_adverse_component_fits_separate':36,
        'synthetic_original_primary_Gfits':24,'synthetic_original_adverse_Gfits_separate':24,
        'synthetic_new_primary_Gfits':first['actual_Gfit_calls'],'synthetic_new_adverse_Gfits_separate':second['actual_Gfit_calls'],
        'synthetic_forced_nonhalf_control_Gfits':4,'new_real_fits':0,'new_real_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(p.PLAN);m.check_sources(parent);assert w.read(p.OUT/'completion_receipt.json')['report_sha256']==w.sha(p.OUT/'report.json')
    paths=[Path(__file__),p.PLAN,p.OUT/'report.json',p.OUT/'completion_receipt.json',Path(base.__file__),Path(base.g.__file__),Path(scopes.__file__)]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Full synthetic common source-weight selector, numerical G relearning, half-cache parity and all loss/final replay. No real fitting or scoring.',
        'need':parent['need'],'hypothesis':parent['hypothesis'],'configuration':parent['future_configuration'],
        'preflight_criterion':'Fresh own-scope synthetic original components/Gcaches then ALL5weights/5innerfolds/3lines, primary/adverse exact under both outer and inner typed poison. Half fullforward/norm exact, endpoints component identity, compulsory nonhalf final control, scalar originalT0loss, tie tests, all75inner objectives/selector/final replay with learning blocked.',
        'future_budget':parent['future_max_budget'],'future_criterion':parent['future_acceptance'],
        'real_first_gate':'Before any nonhalf real Gfit: replay new half forward against ALL75P67inner saved models/prices and15P65outer saved prices/norms; abort on mismatch. Reuse P103scope receipts/P84tables by SHA, no CDF or old scope suite repetition.',
        'counters':'New real closed constants will count Gcategory factors+nuisanceyear/business+training prediction normalizers; these are not statistical degrees of freedom. Cached component/half parameters not counted again. Adverse counts separate.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P104 registra el flujo sintético completo del selector de mezcla P103. Se elige UNpeso común mediante todos los cinco folds internos y tres ramos; para cada peso no50/50 se reaprende G en su train propio, con componentes anteriores reutilizados y qpropio. El50/50 reutiliza exactamente el modelo completo. Se prueban veneno exterior e interior, todas las pérdidas, desempate, extremos y una rama final no50/50obligatoria; replay bloquea todo aprendizaje. La comparación real del50/50contra75internos/15exteriores será un guardián previo a otro ajuste, dentro de futura evaluación registrada. Cero ajuste/score real, fuente/CDF/2025/envíos; sin ampliar cuadrícula o elegir pesos por público. B00 preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P104registered_before_full_synthetic_weight_selector','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P104-MEZCLA-PREVIO','P104: selector completo de mezcla, antes de probar el flujo')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    m.check_sources(w.read(PLAN));dump(OUT/'synthetic.json',synthetic());m.check_sources(w.read(PLAN))
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P104full_synthetic_common_weight_selector_complete_real_eval_pending','synthetic_sha256':w.sha(OUT/'synthetic.json'),
        'new_real_fits':0,'new_real_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'synthetic_selector_pass':True,'new_real_fits':0,'new_real_scores':0}))


def close():
    m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json');synthetic_report=w.read(OUT/'synthetic.json')
    next_unit='P105: separately register complete real common-weight selector, first90half-forward parity checks against P67/P65saved prices/norms, then atmost400+20primary Gstagefits and separate adverse calls with exact cached components/half models. All old outer/cohort/stress/family/level/influence gates and full375inner-objective replay. No new source/CDF/weightgrid or line rescue; transfer and exactCSVadmission after full pass.'
    text='# P104: selector de mezcla, flujo sintético\n\nCodex, '+utc()+'.\n\nSe implementó la selección común de cinco pesos con los cinco folds internos y los tres ramos. Los componentes propios se conservan; cada peso distinto de50/50reaprende sus etapas G, y el50/50reutiliza el modelo anterior. Pasaron veneno exterior e interior antes del selector de entrenamiento, pérdida T0por suma escalar, desempates, identidad de extremos y control final no50/50. Los modelos/selección primarios y adversos coincidieron.\n\nSe reprodujeron las75pérdidas internas, selección y tres aplicaciones finales del fixture con todo aprendizaje bloqueado. El código nuevo coincide exactamente en precio y normalizadores con el productor anterior al50/50. La selección del fixture no elige el peso real. Los q sintéticos son nuisances de ámbito propio para el control; no sustituyen o certifican nuevamente el C0 real.\n\nAntes de ajustar G con datos reales, el futuro evaluador deberá conciliar los75modelos internos y15exteriores al50/50con sus precios/normas guardados. Luego necesita todas las guardas y transferencia propia antes de CSV. Cero ajustes o scores reales, fuente/CDF/2025/envíos. B00 y alternativas conservadas,2024abierto adaptativo; límites de fuentes, snapshots, cola/reservas y búsqueda permanecen, sin mejora privada acreditada ni revisión independiente.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'synthetic':w.rel(OUT/'synthetic.json'),'synthetic_sha256':w.sha(OUT/'synthetic.json'),'document':w.rel(DOC),'next_unit':next_unit,
        'synthetic_selected_weight_not_real_choice':synthetic_report['synthetic_selected_weight'],'new_real_fits':0,'new_real_scores':0,'new_source_fits':0,'new_CDF_fits':0,'new2025inference':0,'new_submissions':0,'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P104-MEZCLA-RESULTADO','P104: flujo numérico sintético de mezcla comprobado')}
    cut=R/'privado'/('corte_P104_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir();w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P104'),(R/'registro/semana2_mision_privada_actual.json','P104')]:w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P104=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P104: selector de mezcla, preflight\n\nCodex, '+receipt['utc']+'. Flujo numérico sintético completo, Gpropio, veneno integral,75pérdidas/selección/replay final pasaron. Cero ajustes/scores reales. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_mix_selector_preflight_index':w.rel(INDEX),'week_2_private_mix_selector_preflight_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');a=argparse.ArgumentParser(description=__doc__);a.add_argument('mode',choices=['register','run','close'])
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[a.parse_args().mode]()
