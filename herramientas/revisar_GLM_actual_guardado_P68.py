"""Coeficientes y contribuciones del GLM P67 guardado, sin ajuste o remuestreo."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p68_current_saved_GLM',R/'herramientas/validar_GLM_reporte_actual_P67.py')
p=importlib.util.module_from_spec(s);s.loader.exec_module(p)
g=p.g;m=p.m;q=p.q;w=p.w;pd=p.pd;np=p.np;BASE=p.BASE
OLD=BASE/'P60_validacion_crossfit_GLM_20261027';CURRENT=p.OUT;CONTROL=p.t.OUT
OUT=BASE/'P68_GLM_actual_guardado_20261027'
PLAN=R/'registro/semana2_GLM_actual_diagnostico_plan.json';INDEX=R/'registro/semana2_GLM_actual_diagnostico_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P68_GLM_ACTUAL_GUARDADO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def masses(values):
    z=np.sort(np.asarray(values,float))[::-1];assert (z>=0).all() and np.isfinite(z).all();total=math.fsum(z.tolist())
    return {'total':total,'top_shares':{str(k):float(z[:k].sum()/total) if total else None for k in [1,5,10]}}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    parent=w.read(p.PLAN);m.check_sources(parent);p.verify_inputs()
    paths=[Path(__file__),p.PLAN,CURRENT/'input_report.json',OLD/'report.json',OLD/'completion_receipt.json',CONTROL/'report.json',CONTROL/'POOLED_prices.parquet']
    for folder in [CURRENT,OLD]:
        assert w.read(folder/'replay_report.json')['report_sha256']==w.sha(folder/'report.json')
        paths += [folder/'report.json',folder/'replay_report.json',folder/'completion_receipt.json',folder/'POOLED_prices.parquet']
        for line in q.LINES:
            for outer in range(5):paths += [folder/f'{line}_{outer}/learning.json']
    for line in q.LINES:
        for outer in range(5):paths += [CURRENT/f'input_{line}_{outer}.parquet',CURRENT/f'{line}_{outer}/committed.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'NEWP67saved coefficients and held predictions vs P60/P65;15new training applications of P67only. No repeat of P58category-support counts or old suites.',
        'known_outcomes':'P67/P65/P60whole scores, gates and P67solver outcome already read. Adaptive descriptive analysis, not an independent or blind test.',
        'questions':['Do the current GLMcoefficients remain unstable or amplify source risk despite the changed observation? Inspect all numeric/missing/categorical contrasts in original units, common reference levels across both sets.',
            'Does the current GLMimprove its own OOF-offset training yet deteriorate vs full-outerP65held? This has a training-size/normalizer shift and is not proof of ordinary overfit or causality.',
            'How concentrated are training cost and row-gradient-norm contributions, and held positive/negative loss increments? These are descriptive contributions, not Hessian influence or deletion experiments.'],
        'configuration':{'scopes':'All3lines*5folds, all line/year/NBheld cells','coef_reference':'Lexically first categorical level shared across all10P60/P67models perline; preserve all levels/fields. Numeric coefficient divided by saved scale; risk elasticity=1+original-unit risk coefficient.',
            'concentration':'Fixed top1/5/10groups for cost and sum of per-row gradient norms, and signed held loss masses. No removing groups or computing leave-out scores.',
            'tail_description':'Positive training T0p995, fraction of uncapped cost above that descriptive fixed threshold. No capped price/model or selected threshold.'},
        'criterion':'Exact key/label/control price joins, original-unit coefficient maps, held loss sums equal saved whole-score differences, and saved row/fold/group exclusion. No admission, alpha/field selection, candidate production or fit from this diagnosis.',
        'budget':{'new_fits':0,'new_CDF_fits':0,'new_resampling':0,'new_training_model_applications':15,'new2025inference':0,'new_submissions':0},
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P68registra revisión nueva de P67guardado frente aP60ybaseP65, después de conocer sus resultados. Todos los15coeficientes/contrastes y celdas,15aplicaciones SOLOa entrenamiento con offsetsOOF, contribuciones de coste/gradiente por grupo y pérdidas retenidas. Se declara cambio64%/80%de base y normalizadores; no causalidad u overfit probado. No repetir soporteP58o suites, ajustar, remuestrear, rescatar campos/alpha o producir precios2025. Una descripciónp995no es una receta o precio capado. B00conservado y2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P68registered_before_new_saved_analysis','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P68-REVISION-PREVIO','P68: GLM actual guardado, coeficientes y contribuciones sin ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan)
    assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    def reject(*args,**kwargs):raise AssertionError('P68cannot fit or resample')
    g.fit=reject;g.TweedieRegressor.fit=reject;q.cost_curves=reject;p.u.reporting=reject;p.u.t.t.line_curves=reject
    models={name:{line:[w.read(folder/f'{line}_{outer}/learning.json') for outer in range(5)] for line in q.LINES} for name,folder in [('P60',OLD),('P67',CURRENT)]}
    common={line:{name:sorted(set.intersection(*(set(a['preprocess']['levels'][name]) for family in models.values() for a in family[line])))[0] for name in g.CAT[line]} for line in q.LINES}
    coefficients=[];scopes=[]
    for family,lines in models.items():
        for line,aa in lines.items():
            for outer,a in enumerate(aa):
                pre=a['preprocess'];lookup=dict(zip(pre['columns'],a['coef']));n=len(pre['numeric'])
                for j,name in enumerate(pre['numeric']):
                    coefficients.append({'family':family,'line':line,'outer':outer,'parameter':name,'value':a['coef'][j]/pre['scale'][j]})
                    coefficients.append({'family':family,'line':line,'outer':outer,'parameter':name+'__missing','value':a['coef'][n+j]})
                for name,levels in pre['levels'].items():
                    reference=common[line][name]
                    for level in levels:coefficients.append({'family':family,'line':line,'outer':outer,'parameter':name+'='+level+' relative '+reference,'value':lookup[name+'='+level]-lookup[name+'='+reference]})
    for line in q.LINES:
        for outer in range(5):
            a=models['P67'][line][outer];f=p.frame_for(line,outer);train=f.loc[~f.is_held];held=f.loc[f.is_held]
            assert f.row_id.is_unique and np.array_equal(f.is_held,f.fold.eq(outer)) and set(train.group_id).isdisjoint(set(held.group_id))
            x,_=g.design(train,line,a['preprocess']);relative=np.exp(x@np.asarray(a['coef'])+a['intercept'])
            mu=train.baseline_observed.to_numpy(float)*relative;y=train.T0.to_numpy(float);base=train.baseline_observed.to_numpy(float)
            gain=m.e.unit(y,base)-m.e.unit(y,mu);den=math.fsum(m.e.unit(y,np.full(len(y),y.mean())).tolist())
            gradient_scalar=np.sqrt(base)*(np.sqrt(relative)-(y/base)/np.sqrt(relative))/np.sqrt(base).sum()
            row_norm=np.abs(gradient_scalar)*np.sqrt(1+np.sum(x*x,axis=1))
            temp=pd.DataFrame({'group':train.group_id.to_numpy(),'cost':y,'gradient_norm_sum':row_norm});by=temp.groupby('group').sum()
            cap=float(np.quantile(y[y>0],.995));tail=float(y[y>cap].sum()/y.sum())
            prices=pd.read_parquet(CURRENT/f'{line}_{outer}/prices.parquet').set_index('row_id').loc[held.row_id]
            saved_base=pd.read_parquet(CONTROL/f'{line}_{outer}/prices.parquet').set_index('row_id').loc[held.row_id]
            assert np.array_equal(held.baseline_ultimate,saved_base.ultimate) and np.array_equal(prices.row_id if 'row_id' in prices else prices.index,held.row_id)
            assert np.array_equal(held.T0,prices.T0) and np.allclose(held.baseline_observed,saved_base.new_nominal,rtol=2e-15)
            hy=held.T0.to_numpy(float);hg=m.e.unit(hy,held.baseline_observed.to_numpy(float))-m.e.unit(hy,prices.new_nominal.to_numpy(float))
            hd=math.fsum(m.e.unit(hy,np.full(len(hy),hy.mean())).tolist())
            scopes.append({'line':line,'outer':outer,'train_rows':len(train),'held_rows':len(held),'train_delta_vs_own_OOFbase':math.fsum(gain.tolist())/den,
                'held_delta_vs_P65':math.fsum(hg.tolist())/hd,'risk_elasticity':1+a['coef'][0]/a['preprocess']['scale'][0],
                'training_group_cost_mass':masses(by.cost),'training_group_sum_row_gradient_norm_mass':masses(by.gradient_norm_sum),
                'descriptive_positive_T0_p995':cap,'fraction_uncapped_cost_above_p995':tail})
    current=pd.read_parquet(CURRENT/'POOLED_prices.parquet');control=pd.read_parquet(CONTROL/'POOLED_prices.parquet');old=pd.read_parquet(OLD/'POOLED_prices.parquet')
    for name in ['row_id','group_id','line','year','new_business','fold','T0','old_nominal']:
        assert np.array_equal(current[name],control[name]) and np.array_equal(current[name],old[name]),name
    yy=current.T0.to_numpy(float);null=math.fsum(m.e.unit(yy,np.full(len(yy),yy.mean())).tolist())
    f=current[['row_id','group_id','line','year','new_business','fold']].copy()
    f['P67_minus_P65']=(m.e.unit(yy,control.new_nominal.to_numpy())-m.e.unit(yy,current.new_nominal.to_numpy()))/null
    f['P67_minus_P60']=(m.e.unit(yy,old.new_nominal.to_numpy())-m.e.unit(yy,current.new_nominal.to_numpy()))/null
    point={name:math.fsum(f[name].tolist()) for name in ['P67_minus_P65','P67_minus_P60']}
    ref=w.read(CURRENT/'report.json')['results']['POOLED']['NOMINAL']['delta']
    for name,folder in [('P67_minus_P65',CONTROL),('P67_minus_P60',OLD)]:assert math.isclose(point[name],ref-w.read(folder/'report.json')['results']['POOLED']['NOMINAL']['delta'],abs_tol=1e-13)
    cells=[]
    for keys,z in f.groupby(['line','year','new_business'],sort=True):cells.append({'line':keys[0],'year':int(keys[1]),'NB':int(keys[2]),'rows':len(z),**{name:math.fsum(z[name].tolist()) for name in point}})
    by=f.groupby('group_id').P67_minus_P65.sum();held_masses={'positive':masses(by[by>0]),'negative':masses(-by[by<0])}
    assert math.isclose(held_masses['positive']['total']-held_masses['negative']['total'],point['P67_minus_P65'],abs_tol=1e-13)
    coef=pd.DataFrame(coefficients);stability=[]
    for keys,z in coef.groupby(['family','line','parameter'],sort=True):stability.append({'family':keys[0],'line':keys[1],'parameter':keys[2],'folds':len(z),'min':float(z.value.min()),'max':float(z.value.max()),'sd':float(z.value.std(ddof=0))})
    coef.to_parquet(OUT/'coefficients.parquet',index=False);f.to_parquet(OUT/'paired_rows.parquet',index=False)
    m.check_sources(plan);report={'author':'Codex','utc':utc(),'status':'P68new_saved_GLM_comparison_complete','scopes':scopes,'coefficient_stability':stability,'held_cells':cells,'held_group_loss_masses':held_masses,'paired_points_no_new_intervals':point,
        'training_positive_scopes':sum(z['train_delta_vs_own_OOFbase']>0 for z in scopes),'held_positive_scopes':sum(z['held_delta_vs_P65']>0 for z in scopes),
        'limits':['Training offsets use64percent/full held80percent base fits and different batch normalizers; descriptive gap does not prove overfit or its cause.','Gradient norm sums are a diagnostic of objective contributions, not a case-deletion influence estimate.','Folds overlap, outcomes already seen, no new interval, independent validation or model admission.'],**plan['budget']}
    dump(OUT/'report.json',report);print(json.dumps({key:report[key] for key in ['training_positive_scopes','held_positive_scopes','paired_points_no_new_intervals','held_group_loss_masses']}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='Review NEWP68training gradient/cost concentration and fixed-coefficient contrasts before choosing a standard bounded-influence SHAPE estimator plus exact uncapped Tweedie level, or another concrete mechanism. This is NOTa registered recipe: freeze objective/threshold/config/cost/criteria and synthetic full flow before any real fit. Do not tune alpha/fields, delete claims, alter T0evaluation or submit a probe.'
    text='# P68: GLM actual guardado, coeficientes y contribuciones\n\nCodex, '+utc()+f". P67mejora su propio entrenamiento con offsetsOOFen{d['training_positive_scopes']}de15ámbitos y supera aP65en{d['held_positive_scopes']}de15retenidos. Diferencia global P67menosP65={d['paired_points_no_new_intervals']['P67_minus_P65']:+.7f}; frente aP60={d['paired_points_no_new_intervals']['P67_minus_P60']:+.7f}. Puntos sin nuevo intervalo.\n\n"
    text+='Se guardan TODOSlos coeficientes/contrastes en unidades originales y las pérdidas de todas las celdas, sin seleccionar variables.15aplicaciones nuevas al entrenamiento, no ajustes. Las basesOOFusan64%frente a80%enretenido y normalizadores propios; esta brecha no identifica causalmente sobreajuste. Las contribuciones por norma del gradiente y coste se agregan por grupo, sin borrar siniestros ni simular precios capados.\n\n'
    text+='| Ramo | Fold | Δ entrenamiento | Δ retenido | Elasticidad riesgo | Coste top1 grupo | Gradiente top1 grupo | Coste sobrep995 |\n|---|---|---|---|---|---|---|---|\n'
    for z in d['scopes']:text+=f"| {z['line']} | {z['outer']} | {z['train_delta_vs_own_OOFbase']:+.5f} | {z['held_delta_vs_P65']:+.5f} | {z['risk_elasticity']:.4f} | {z['training_group_cost_mass']['top_shares']['1']:.3f} | {z['training_group_sum_row_gradient_norm_mass']['top_shares']['1']:.3f} | {z['fraction_uncapped_cost_above_p995']:.3f} |\n"
    text+='\nNo se repitieron soportes de categoríaP58, suites o remuestreos. No hay campos/alphaelegidos ni receta posterior admitida. Se mantiene el rechazoP67ycuota;B00/F3cyalternativas conservados,2024abierto adaptativo, reservas/cola/mercado/fuente2024condicional sin certificar. No mejora privada acreditada o revisión profesional independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),
        'training_positive_scopes':d['training_positive_scopes'],'held_positive_scopes':d['held_positive_scopes'],'paired_points_no_new_intervals':d['paired_points_no_new_intervals'],
        'next_unit':next_unit,**w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P68-REVISION-RESULTADO','P68: GLM actual, contribuciones y límites antes de otra receta')}
    archive=R/'privado'/('corte_P68_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P68'),(R/'registro/semana2_mision_privada_actual.json','P68')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P68=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P68: GLM actual guardado\n\nCodex, '+receipt['utc']+'.Coeficientes y contribuciones nuevas,15aplicaciones de entrenamiento; cero ajustes/CDF/remuestreo/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_current_GLM_diagnostic_index':w.rel(INDEX),'week_2_private_current_GLM_diagnostic_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
