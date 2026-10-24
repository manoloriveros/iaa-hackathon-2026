"""Diagnóstico de ajuste frente a OOF de la tanda congelada, sin nuevos modelos."""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import importlib.util
import json
import sys

REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('dev2023_checker',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
checker=importlib.util.module_from_spec(spec);sys.modules[spec.name]=checker;spec.loader.exec_module(checker)
np,pd,pq,joblib=checker.np,checker.pd,checker.pq,checker.joblib
ap=argparse.ArgumentParser();ap.add_argument('--run',required=True);args=ap.parse_args()
run=Path(args.run).resolve();run.relative_to(REPO/'privado/semana2/desarrollo2023')
report=checker.read(run/'report.json');plan=checker.read(run/'plan_snapshot.json')
for cls in [checker.TweedieRegressor,checker.SimpleImputer,checker.StandardScaler,checker.OneHotEncoder,
            checker.ColumnTransformer,checker.Pipeline,checker.lgb.LGBMRegressor,checker.lgb.LGBMModel]:
    cls.fit=checker.forbid_fit
    if hasattr(cls,'fit_transform'):cls.fit_transform=checker.forbid_fit
oof=pq.read_table(run/'oof_2023.parquet').to_pandas();assert oof.year.eq(2023).all()
nodes=[];aggregate={x['id']:{'rows':0,'observed_total':0.,'predicted_total':0.,'deviance_sum':0.} for x in plan['models']}
for line in ['motor','buildings','contents']:
    frame=pq.read_table(run/f'inputs_2023/{line}.parquet').to_pandas();assert frame.year.eq(2023).all()
    for fold in range(5):
        link=pq.read_table(run/f'links_2023/{line}_fold{fold}.parquet').to_pandas()
        data=frame.merge(link[checker.KEY+['e_cost_mix_1.0']],on=checker.KEY,validate='one_to_one')
        fit=data.loc[data.fold.ne(fold)]
        for item in plan['models']:
            mid=item['id'];node=f'{mid}_{line}_fold{fold}';bundle=joblib.load(run/'models'/node/'bundle.joblib')
            with checker.threadpool_limits(limits=2):pred=checker.predict(bundle,fit)*fit['e_cost_mix_1.0'].to_numpy()
            loss=float(checker.dev(fit.T0,pred).sum());null=float(checker.dev(fit.T0,np.full(len(fit),fit.T0.mean())).sum())
            receipt=checker.read(run/'models'/node/'receipt.json')
            nodes.append({'node':node,'model_id':mid,'line':line,'fold':fold,'training_rows':len(fit),
                'training_D2':1-loss/null,'training_actual_over_expected':float(fit.T0.sum()/pred.sum()),
                'training_deviance_sum':loss,'largest_training_loss_fraction':float(fit.T0.max()/fit.T0.sum()),
                'unknown_categorical_cells_in_validation':sum(receipt['unknown_category_rows'].values())})
            a=aggregate[mid];a['rows']+=len(fit);a['observed_total']+=float(fit.T0.sum());a['predicted_total']+=float(pred.sum());a['deviance_sum']+=loss
summaries=[]
for mid,a in aggregate.items():
    assert a['rows']==4*50094
    base=next(x for x in report['summary'] if x['model_id']==mid)
    a['D2']=1-a['deviance_sum']/(4*base['null_deviance_sum'])
    a['actual_over_expected']=a['observed_total']/a['predicted_total']
    folds=[x['D2'] for x in checker.read(run/'diagnostics/segments.json') if x['model_id']==mid and x['segment']=='fold']
    summaries.append({'model_id':mid,'training_repeated_rows':a,'OOF_D2':base['D2'],
        'OOF_actual_over_expected':base['actual_over_expected'],
        'fold_D2_mean':float(np.mean(folds)),'fold_D2_sample_std':float(np.std(folds,ddof=1)),
        'fold_D2_min':min(folds),'fold_D2_max':max(folds),
        'scope':'Each source row appears in four training folds; training score is in-sample diagnostic only'})
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source':str(Path(__file__).relative_to(ROOT)),
        'source_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'source_run':str(run.relative_to(ROOT)),
        'fit_calls':0,'new_recipes_or_models':0,'year':2023,'nodes':nodes,'summary':summaries,
        'interpretation':'Training-vs-heldout gap is evidence consistent with overfit, not causal isolation of depth, rounds, penalties or rare claims. No rescaling, stage selection or retuning applied.',
        'consumer_2024_predictions_or_scores':0}
out=run/'diagnostics/fit_vs_oof.json'
with out.open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
print(json.dumps({'summary':summaries,'nodes':len(nodes),'fit_calls':0},ensure_ascii=True))
