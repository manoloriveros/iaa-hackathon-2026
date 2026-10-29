"""Diagnostico finito de salidas P110 guardadas, sin ajuste o remuestreo."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
sys.path.insert(0,str(R/'herramientas'))
import validar_Poisson_destino_P110 as p
k=p.k;w=p.w;pd=p.pd;np=p.np
OUT=p.BASE/'P111_diagnostico_numero_coste_20261027'
PLAN=R/'registro/semana2_diagnostico_numero_coste_plan.json'
INDEX=R/'registro/semana2_diagnostico_numero_coste_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P111_DIAGNOSTICO_NUMERO_COSTE.md'
dump=p.dump;utc=p.utc


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(p.OUT/'completion_receipt.json')['report_sha256']==w.sha(p.OUT/'report.json')
    paths=[Path(__file__),Path(p.__file__),p.PLAN,p.OUT/'report.json',p.OUT/'replay_report.json',
        p.OUT/'completion_receipt.json',p.OUT/'matched_null_report.json',p.OUT/'POOLED_prices.parquet',p.OUT/'POOLED_group_influence.parquet',
        p.BASE/'P28_fuente_frecuencia_marca_20261026/report.json']
    paths += list(p.OUT.glob('*_*/learning.json'))
    assert len(list(p.OUT.glob('*_*/learning.json')))==15
    OUT.mkdir()
    plan={'author':'Codex','utc':utc(),'need':'P110cost fails every fold/year, while motor/buildings held count loss improves slightly vs matched null. Separate saved count/mark/price evidence before proposing another model.',
        'scope':'Only saved P110OOFprices/count means/labels, models as coefficient metadata, and saved influence; no model inference, fit, exposure update, CDF, new candidate prices or resampling.',
        'configuration':{'cells':'Every line/year/business and line/fold/year/business, no outcome-based deletion or regrouping.',
            'reported_mark_identity':'Actual reported cost/event=sum(T0)/sum(N); model counterpart=sum(observed cost quote)/sum(observed count mean). Their ratio equals costAE/countAE, descriptive snapshot ratio, not ultimate severity.',
            'losses':'Reconcile saved primary and matched-null cost gains by scalar arithmetic; accepted-count Poisson loss gains separate. Wholegroup sums and signs, no confidence band beyond saved P110intervals.',
            'influence':'All saved customer/address groups; report joint count/cost gain quadrants and the existing top31gain-removal diagnostic. No remove/reweight/refit proposal.',
            'coefficients':'All P110columns across5folds, report presence, signs and ranges. Standardized coefficients/categorical coding are conditional, not causal effects or feature selection.'},
        'criterion':'All109296saved rows unique; primary and matched-null deltas reconcile within numerical precision; all12coarse cells and60fine cells retained. Independent identity for snapshot mark ratios; no new fitted/quoted models.',
        'decision_rule':'No promotion or parameter rescue from diagnostics. A business-specific mean-mark story requires same direction across BOTHyears/folds; if it reverses, do not call a fixed NBlevel alone a resolved mechanism. State competing causes/uncertainty before a next recipe.',
        'sources':{w.rel(path):w.sha(path) for path in paths},'new_fits':0,'new_model_inference':0,'new_scores_for_new_candidates':0,
        'new_resampling':0,'new2025inference':0,'new_submissions':0,'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False}
    dump(PLAN,plan)
    body=OUT/'forum_previo.md';body.write_text('Codex. P111 registra un diagnóstico de las salidas ya guardadas de P110, sin ajustar, inferir modelos o remuestrear. Se conservarán todas las celdas por ramo/año/negocio/fold y todos los grupos; se contrastarán las pérdidas de número y coste, el cociente descriptivo de coste por evento reportado y la estabilidad de coeficientes. Se comprobarán los agregados por sumas escalares. Un desajuste de coste por evento puede mezclar severidad, composición, demoras, reservas y azar; no identifica su causa ni el último. Si la dirección cambia entre años, no se declarará resuelta con un nivel fijo de nuevo negocio. Nada de selección de campos, supresión de siniestros, rescates por ramo o nuevo CSV. B00 intacto, privada prioritaria. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':'P111registered_before_saved_output_diagnostic','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P111-DIAGNOSTICO-PREVIO','P111: separar evidencia de número y coste sin ajustar')}
    dump(OUT/'registration.json',receipt);dump(INDEX,receipt);print(json.dumps(receipt))


def cell_record(frame,key,columns):
    values=dict(zip(columns,key if isinstance(key,tuple) else [key]))
    values={name:int(value) if isinstance(value,(np.integer,int)) else value for name,value in values.items()}
    actual=float(frame.T0.sum());events=int(frame.n_accepted.sum())
    quoted=float(frame.new_nominal.sum());expected=float(frame.count_prediction.sum())
    actual_mark=actual/events if events>0 else None;model_mark=quoted/expected
    cost_ae=actual/quoted;count_ae=events/expected
    ratio=actual_mark/model_mark if events>0 else None
    if events>0:assert math.isclose(ratio,cost_ae/count_ae,rel_tol=3e-14)
    return {**values,'rows':len(frame),'groups':int(frame.group_id.nunique()),'events':events,'cost_AE':cost_ae,'count_AE':count_ae,
        'actual_reported_cost_per_event':actual_mark,'model_reported_cost_per_event':model_mark,'reported_mark_ratio':ratio,
        'cost_gain_vs_ref':float(frame.cost_gain_ref.sum()),'cost_gain_vs_null':float(frame.cost_gain_null.sum()),
        'count_gain_vs_null':float(frame.count_gain_null.sum())}


def run():
    plan=w.read(PLAN);p.m.check_sources(plan)
    # Metadata only: prevent accidental estimator, calibration, or forward calls.
    def reject(*args,**kwargs):raise AssertionError('P111 permits only saved output diagnostics')
    k.fit=reject;k.forward=reject;k.cost_level=reject;k.PoissonRegressor.fit=reject
    f=pd.read_parquet(p.OUT/'POOLED_prices.parquet');assert len(f)==109296 and f.row_id.is_unique and f.year.isin([2023,2024]).all()
    y=f.T0.to_numpy(float);old=f.old_nominal.to_numpy(float);new=f.new_nominal.to_numpy(float);null=f.null_new_nominal.to_numpy(float)
    unit=p.m.e.unit
    f['cost_gain_ref']=unit(y,old)-unit(y,new);f['cost_gain_null']=unit(y,null)-unit(y,new)
    n=f.n_accepted.to_numpy(float);mean=f.count_prediction.to_numpy(float);constant=f.null_count_prediction.to_numpy(float)
    from scipy.special import xlogy
    f['count_gain_null']=2*(xlogy(n,n/constant)-n+constant)-2*(xlogy(n,n/mean)-n+mean)
    denominator=math.fsum(unit(y,np.full(len(y),y.mean())).tolist())
    delta=math.fsum(f.cost_gain_ref.tolist())/denominator;matched=math.fsum(f.cost_gain_null.tolist())/denominator
    report=w.read(p.OUT/'report.json');nominal=report['results']['POOLED']['NOMINAL']
    assert math.isclose(delta,nominal['delta'],rel_tol=2e-12,abs_tol=2e-14)
    assert math.isclose(matched,report['matched_nominal']['delta_vs_matched_null'],rel_tol=2e-12,abs_tol=2e-14)
    coarse=[cell_record(group,key,['line','year','new_business']) for key,group in f.groupby(['line','year','new_business'],sort=True)]
    fine=[cell_record(group,key,['line','fold','year','new_business']) for key,group in f.groupby(['line','fold','year','new_business'],sort=True)]
    assert len(coarse)==12 and len(fine)==60
    pd.DataFrame(coarse).to_csv(OUT/'reported_mark_cells.csv',index=False);pd.DataFrame(fine).to_csv(OUT/'reported_mark_fold_cells.csv',index=False)
    grouped=f.groupby('group_id',sort=True)[['cost_gain_ref','cost_gain_null','count_gain_null']].sum()
    saved=pd.read_parquet(p.OUT/'POOLED_group_influence.parquet').set_index('group_id').loc[grouped.index]
    assert np.allclose(grouped.cost_gain_ref,saved.NOMINAL,rtol=2e-11,atol=1e-10)
    post31=(math.fsum(grouped.cost_gain_ref.tolist())-math.fsum(np.sort(grouped.cost_gain_ref.to_numpy())[::-1][:31].tolist()))/denominator
    assert math.isclose(post31,nominal['post31_delta'],rel_tol=2e-12,abs_tol=2e-14)
    quadrants=[]
    for count_positive in [False,True]:
        for cost_positive in [False,True]:
            mask=grouped.count_gain_null.gt(0).eq(count_positive)&grouped.cost_gain_null.gt(0).eq(cost_positive)
            z=grouped.loc[mask];quadrants.append({'count_gain_positive':count_positive,'cost_gain_positive':cost_positive,
                'groups':len(z),'cost_gain':float(z.cost_gain_null.sum()),'count_gain':float(z.count_gain_null.sum())})
    coeff=[]
    for line in p.q.LINES:
        models=[w.read(p.OUT/f'{line}_{fold}/learning.json') for fold in range(5)]
        names=sorted(set(name for model in models for name in model['preprocess']['columns']))
        for name in names:
            values=[model['coef'][model['preprocess']['columns'].index(name)] for model in models if name in model['preprocess']['columns']]
            coeff.append({'line':line,'column':name,'present_folds':len(values),'min':min(values),'max':max(values),
                'sign_reversal':min(values)<-1e-8 and max(values)>1e-8})
    pd.DataFrame(coeff).to_csv(OUT/'coefficient_stability.csv',index=False)
    contrasts=[]
    for line in p.q.LINES:
        ratios={}
        for year in [2023,2024]:
            a=next(record for record in coarse if record['line']==line and record['year']==year and record['new_business']==1)
            b=next(record for record in coarse if record['line']==line and record['year']==year and record['new_business']==0)
            ratios[year]=a['reported_mark_ratio']/b['reported_mark_ratio']
        contrasts.append({'line':line,'NB_to_renewal_relative_reported_mark_ratio':ratios,
            'same_direction_both_years':(ratios[2023]>1)==(ratios[2024]>1)})
    p.m.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P111saved_count_cost_mismatch_diagnosed_no_new_model',
        'primary_delta_scalar':delta,'matched_delta_scalar':matched,'post31_scalar':post31,
        'matched_null_delta_vs_ref':delta-matched,'cells':coarse,'fine_cell_count':len(fine),'joint_group_gain_quadrants':quadrants,
        'business_mark_contrasts':contrasts,'coefficient_columns':len(coeff),'coefficient_sign_reversals':sum(record['sign_reversal'] for record in coeff),
        'new_fits':0,'new_model_inference':0,'new_resampling':0,'new2025inference':0,'new_submissions':0})
    print(json.dumps({'diagnostic_complete':True,'matched_null_delta_vs_ref':delta-matched,'business_mark_contrasts':contrasts,'new_fits':0}))


def close():
    plan=w.read(PLAN);p.m.check_sources(plan);d=w.read(OUT/'report.json')
    next_unit='Review actual currently consumed cost/weather/rating source contracts against the P111year-dependent reported mark mismatch before proposing another model. Separate business effects from year/composition effects using the saved diagnostic; fixed NBlevel alone is not a resolved mechanism. Existing source P28GLM source gate passed vs native context, so do not assert capacity underfit from target failure alone. Review availability/transport and exposure/mark composition with new P110evidence; no repeated F05audit or alpha/line/weight rescue. Any next standard recipe needs a concrete new difference and preflight/preregistration before fit.'
    text='# P111: diferencia entre número y coste\n\nCodex, '+utc()+'.\n\nSe conciliaron por sumas escalares los resultados P110. El null emparejado ya pierde '+f"{d['matched_null_delta_vs_ref']:+.7f}"+' D2 frente a la referencia; la corrección de frecuencia añade '+f"{d['matched_delta_scalar']:+.7f}"+'. El intervalo de esta diferencia con el null incluye cero, por lo que no se atribuye con certeza un efecto negativo aislado al Poisson. La pérdida principal se conserva en todos los folds y ambos años.\n\n'
    reversals=[record['line'] for record in d['business_mark_contrasts'] if not record['same_direction_both_years']]
    text+='En autos nuevos de 2023 el A/E de número es aproximadamente1,04 y el de coste1,42: el cociente descriptivo de coste por evento reportado es aproximadamente1,38 veces el implícito en el modelo. En 2024 ese cociente es aproximadamente0,96. Ramos donde la dirección relativa nuevo/renovación cambia entre años: '+(', '.join(reversals) if reversals else 'ninguno')+'. Los cocientes por ramo/año/negocio quedan completos en el informe; un nivel fijo de nuevo negocio no queda identificado como solución general. Se conservaron las12celdas y60subceldas por fold, todos los grupos y todos los coeficientes, sin elegir campos o eliminar siniestros.\n\n'
    text+='Estos cocientes mezclan severidad observada, composición, notificación, reservas y variación muestral. No son severidades últimas identificadas ni pruebas causales. Los puntos de recuento mejoran ligeramente en autos/edificios y empeoran en contenidos, sin una nueva banda de significación; no bastan para predecir mejor coste. El preflight fuente P28 había superado su comparación contextual con árboles anteriores, por lo que este fallo destino tampoco prueba por sí solo falta de capacidad del GLM fuente.\n\n'
    text+='No se ajustó, infirió o puntuó ningún candidato nuevo, ni se remuestreó. Se bloquearon estimadores y forward durante el diagnóstico. B00, F3c y todas las alternativas se conservan; prioridad privada y 2024 adaptativo, sin nueva evidencia de mejora privada.\n\nPróximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),
        'document':w.rel(DOC),'next_unit':next_unit,'new_fits':0,'new_model_inference':0,'new_resampling':0,'new2025inference':0,'new_submissions':0,
        '2024_open':True,'goal_achieved':False,'forum':k.p108.p107.previous.post(body,'COD-S2-20261027-PRIVADA-P111-DIAGNOSTICO-RESULTADO','P111: el desajuste de coste por evento cambia con el año')}
    archive=R/'privado'/('corte_P111_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P111'),(R/'registro/semana2_mision_privada_actual.json','P111')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    path=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(path)['week_2_mission017_phase2_20261025'];own.update(private_P111=receipt,next_unit=next_unit)
    w.update(path,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P111: número y coste observados\n\nCodex, '+receipt['utc']+'. Diagnóstico nuevo de salidas P110, sin ajuste/inferencia/remuestreo. Ramos con cambio de dirección NB/renovación entre años: '+(', '.join(reversals) if reversals else 'ninguno')+'. No se propone nivel fijo como solución general acreditada. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_count_cost_diagnostic_index':w.rel(INDEX),'week_2_private_count_cost_diagnostic_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','run','close']);{'register':register,'run':run,'close':close}[parser.parse_args().mode]()
