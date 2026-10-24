"""Lectura del OOF congelado de 2023, sin ajustes ni nuevas predicciones."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util,sys,json,uuid
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
spec=importlib.util.spec_from_file_location('stability_check',REPO/'herramientas/verificar_desarrollo2023_semana2.py')
c=importlib.util.module_from_spec(spec);sys.modules[spec.name]=c;spec.loader.exec_module(c)
np,pd,pq=c.np,c.pd,c.pq
idx=c.read(REPO/'registro/semana2_desarrollo2023_actual.json');run=ROOT/idx['run']
oof=pq.read_table(run/'oof_2023.parquet',filters=[('year','=',2023)]).to_pandas();assert oof.year.eq(2023).all()
ref=oof[oof.model_id.eq('W2-B00')].sort_values(c.KEY).reset_index(drop=True)
null=c.dev(ref.T0,np.repeat(ref.T0.mean(),len(ref))).sum()
out=run.parent/('revision_estabilidad_'+datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')+'_'+uuid.uuid4().hex[:8]);out.mkdir()
rows=[];influence=[]
for mid in ['W2-B00','W2-B03','W2-B05','W2-B06','W2-B07','W2-B08','W2-B09']:
    p=oof[oof.model_id.eq(mid)].sort_values(c.KEY).reset_index(drop=True);assert p[c.KEY].equals(ref[c.KEY])
    for dims in [['fold'],['x_new_business'],['line','x_new_business'],['fold','x_new_business'],['line','fold','x_new_business']]:
        for key,sub in p.groupby(dims,observed=True):
            rr=ref.loc[sub.index];y=sub.T0.to_numpy();mu=sub.prediction.to_numpy();den=c.dev(y,np.repeat(y.mean(),len(y))).sum()
            a=c.dev(rr.T0,rr.prediction).sum()-c.dev(y,mu).sum()
            rows.append({'model_id':mid,'dimensions':dims,'key':[str(k) for k in key],'rows':len(sub),'groups':sub.group_id.nunique(),
              'positive_rows':int(sub.T0.gt(0).sum()),'exposure':float(sub.exposure.sum()),'observed':float(y.sum()),'predicted':float(mu.sum()),
              'reference_predicted':float(rr.prediction.sum()),'A_over_E':float(y.sum()/mu.sum()),
              'D2':float(1-c.dev(y,mu).sum()/den),'delta_D2':float(a/den),'contribution_global_delta':float(a/null)})
    if mid in ['W2-B08','W2-B09']:
        gain=ref.unit_deviance-p.unit_deviance
        gp=p.assign(gain=gain).groupby('group_id',observed=True).agg(gain=('gain','sum'),rows=('T0','size'),y=('T0','sum'))
        order=gp.sort_values('gain',ascending=False,kind='stable');flip=np.flatnonzero(order.gain.cumsum().to_numpy()>=gp.gain.sum())
        influence.append({'model_id':mid,'minimum_favorable_groups_to_flip':int(flip[0]+1) if len(flip) else None,
          'top31_gain_share':float(order.gain.iloc[:31].sum()/gp.gain.sum()),'top31_cost_share':float(order.y.iloc[:31].sum()/gp.y.sum())})
        gp.to_parquet(out/f'{mid}_influence.parquet')
result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source_run':idx['run'],'source_oof_sha256':c.sha(run/'oof_2023.parquet'),
 'code_sha256':c.sha(Path(__file__)),'segments':rows,'influence':influence,'fit_calls':0,'new_predictions':0,'year':2023,'confirmation_2024_open':False,
 'limits':['Overlapping folds and adaptive exploration; fold dispersion is not independent replication.',
           'Group-removal and composition diagnosis keep models fixed; no retraining stability conclusion.']}
(out/'report.json').write_text(json.dumps(result,indent=2)+'\n',encoding='utf-8');(out/'code_snapshot.py').write_bytes(Path(__file__).read_bytes())
print(json.dumps({'review':str(out.relative_to(ROOT)).replace('\\','/'),'influence':influence,
 'B08_folds':[x for x in rows if x['model_id']=='W2-B08' and x['dimensions']==['fold']],
 'new_by_line':[x for x in rows if x['model_id'] in ['W2-B08','W2-B09'] and x['dimensions']==['line','x_new_business'] and x['key'][1]=='1']}))
