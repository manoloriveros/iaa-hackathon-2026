"""Auditoría del encargo del 19-oct-2026. Solo lee productos; escribe evidencia nueva.

No importa productores, entrena, predice ni cambia la receta. Las sumas por fila
se calculan en memoria y solo se conservan agregados, controles y hashes.
"""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, platform, subprocess, sys
import numpy as np
import pandas as pd
import pyarrow
import pyarrow.parquet as pq

REPO = Path(__file__).resolve().parents[1]
ROOT = REPO.parents[1]
WEEK = ROOT / 'Hackaton/Semana 1'
OUT = REPO / 'privado/revision_participante_20261019_r3'
SOURCES, CHECKS, DETAILS = {}, [], {}

def sha(p):
    with Path(p).open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def source(p):
    p = Path(p).resolve()
    if str(p) not in SOURCES:
        SOURCES[str(p)] = sha(p)
    return p

def read(p):
    return json.loads(source(p).read_text(encoding='utf-8-sig'))

def table(p, columns=None):
    return pq.read_table(source(p), columns=columns).to_pandas()

def ck(name, ok, detail=None):
    CHECKS.append({'control': name, 'pasa': bool(ok), 'detalle': detail})

def dump(p, obj):
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=str)+'\n', encoding='utf-8')

def d2(y, mu):
    # Forma cerrada independiente para p=1,5: 4*(sqrt(mu)+y/sqrt(mu)-2*sqrt(y)).
    y, mu = np.asarray(y, float), np.asarray(mu, float)
    dev = 4*(np.sqrt(mu)+y/np.sqrt(mu)-2*np.sqrt(y))
    null = 4*(np.sqrt(y.mean())+y/np.sqrt(y.mean())-2*np.sqrt(y))
    return float(1-dev.sum()/null.sum())

def main():
    OUT.mkdir(exist_ok=False)
    source(Path(__file__))
    plan = read(REPO/'registro/revision_participante_20261019_plan.json')
    dump(OUT/'plan.json', plan)
    manifest = read(ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json')
    originals=[]
    for v in manifest['files']:
        p=WEEK/'Datos'/Path(v['path']).name
        got=sha(source(p)); ok=got==v['sha256']
        ck('Original '+p.name,ok)
        originals.append({'archivo':p.name,'sha256':got,'coincide':ok,'filas':pq.read_metadata(p).num_rows})
    DETAILS['originales']=originals
    idx=read(WEEK/'Limpieza/current_dataset.json')
    catalog=read(ROOT/idx['catalog_workspace_relative'])
    for name,v in catalog.items():
        ck('Capa activa '+name,sha(source(ROOT/v['workspace_relative_path']))==v['sha256'])
    claims=table(ROOT/catalog['claims']['workspace_relative_path'])
    raw=table(WEEK/'Datos/claims.parquet')
    ck('DUP01 copias estrictas',len(raw)-len(raw.drop_duplicates(subset=[c for c in raw if c!='claim_id']))==604)
    a=claims[raw.columns].set_index('claim_id').sort_index()
    b=raw.set_index('claim_id').loc[a.index].sort_index()
    ck('Siniestros retenidos conservan valores originales',a.equals(b))
    ck('Identificadores de siniestro únicos',claims.claim_id.is_unique)
    bases=WEEK/'Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0/tables'
    t0=table(bases/'t0_por_row_id.parquet').set_index('row_id')
    assignment=table(bases/'asignacion_por_siniestro.parquet').set_index('claim_id')
    ck('D67 claves únicas',t0.index.is_unique and assignment.index.is_unique)
    conciliation=[]
    target_reference=[]
    for line in ['motor','buildings','contents']:
        p=table(ROOT/catalog['policies_'+line]['workspace_relative_path'],['row_id','policy_id','period_start','period_end','exposure'])
        ck('Pólizas únicas '+line,p.row_id.is_unique)
        c=claims[claims.line==line].copy()
        q=c.merge(p,on='policy_id',how='inner')
        q=q[(q.loss_date>=q.period_start)&(q.loss_date<=q.period_end)]
        ck('Asignación temporal única '+line,q.claim_id.is_unique)
        actual=c.claim_id.map(q.set_index('claim_id').row_id).fillna('<sin_periodo>')
        expected=c.claim_id.map(assignment.row_id).fillna('<sin_periodo>')
        ck('Asignación alternativa coincide '+line,actual.equals(expected))
        unmatched=c[~c.claim_id.isin(q.claim_id)]
        ck('No asignados pertenecen a prehistoria '+line,unmatched.audit_pre00.all(),len(unmatched))
        accepted=q[q.status.isin(['open','closed'])].copy()
        accepted['net']=accepted.incurred_to_date-accepted.recoveries
        accepted['reserve_calc']=accepted.incurred_to_date-accepted.paid_to_date
        ck('Costes netos válidos '+line,np.isfinite(accepted.net).all() and (accepted.net>=0).all())
        agg=accepted.groupby('row_id').agg(T0=('net','sum'),reserve=('reserve_calc','sum'),n_accepted=('claim_id','size'))
        rec=p[['row_id']].set_index('row_id').join(agg).fillna(0)
        orig=t0.loc[rec.index]
        errors={k:float(np.max(np.abs(rec[k].to_numpy()-orig[k].to_numpy()))) for k in ['T0','reserve','n_accepted']}
        ck('T0 y reservas por fila '+line,max(errors.values())<=1e-6,errors)
        ck('Exposición preparada válida '+line,np.isfinite(p.exposure).all() and (p.exposure>0).all() and (p.exposure<=1.01).all())
        conciliation.append({'ramo':line,'periodos':len(p),'aceptados':len(accepted),'sin_periodo':len(unmatched),'T0':float(rec.T0.sum()),'reserva':float(rec.reserve.sum()),'max_error':errors})
        target_reference.append(rec)
    independent_t0=pd.concat(target_reference)
    DETAILS['conciliacion']=conciliation
    del raw,a,b,q,p
    f0dir=WEEK/'Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca'
    contract=read(f0dir/'contrato_disponibilidad.json')
    partitions=table(f0dir/'tables/particiones.parquet').set_index('row_id')
    ck('Particiones únicas',partitions.index.is_unique)
    halves={'eval_calibracion':set(),'eval_seleccion':set()}
    f0_details=[]; ids_test=[]; cap_ids=[]
    for line in ['motor','buildings','contents']:
        cols=['row_id','customer_id','address_id','year','is_test','exposure','e_ef_coste','T0']
        if line!='motor': cols+=['sum_insured','sum_insured_raw','audit_capital_scale_adjusted','audit_capital_scale_confirmed']
        f=table(f0dir/f'tables/f0_{line}.parquet',cols).set_index('row_id')
        ck('F0 claves únicas '+line,f.index.is_unique)
        tr=f[~f.is_test];test=f[f.is_test]
        ck('F0 objetivo concilia '+line,np.allclose(tr.T0,independent_t0.loc[tr.index].T0,rtol=0,atol=1e-6))
        ck('Test sin etiquetas '+line,test.T0.isna().all())
        ck('Exposición efectiva permitida '+line,((f.e_ef_coste>0)&(f.e_ef_coste<=f.exposure+1e-10)).all())
        ck('Test usa exposición nominal '+line,np.allclose(test.exposure,test.e_ef_coste,rtol=0,atol=1e-10))
        part=partitions.loc[f.index]
        ck('Cortes sin años posteriores '+line,((part.loc[part.V23=='train','year']<2023).all() and (part.loc[part.V24=='train','year']<2024).all() and (part.loc[part.PROD=='train','year']<2025).all()))
        for half in halves:
            halves[half].update(f.loc[part.V23==half,'customer_id'].tolist())
        ids_test.extend(test.index.tolist())
        conditional={c:v['motivo'] for c,v in contract['columnas'][line].items() if v['bloque']=='F3'}
        row={'ramo':line,'train':len(tr),'test':len(test),'F3':conditional}
        if line!='motor':
            adj=f.audit_capital_scale_adjusted.astype(bool);unconfirmed=adj & ~f.audit_capital_scale_confirmed.astype(bool)
            limit=1e7 if line=='buildings' else 1e6
            exp=np.where(f.sum_insured_raw>limit,f.sum_insured_raw/1000,f.sum_insured_raw)
            ck('Capital F0 sigue regla declarada '+line,np.allclose(f.sum_insured,exp,rtol=0,atol=1e-6,equal_nan=True))
            row.update(ajustados=int(adj.sum()),sin_confirmacion=int(unconfirmed.sum()),sin_confirmacion_test=int((unconfirmed&f.is_test).sum()))
            cap_ids.extend(f.index[unconfirmed&f.is_test].tolist())
        f0_details.append(row)
    overlap=len(halves['eval_calibracion']&halves['eval_seleccion'])
    ck('V23 clientes separados entre mitades en todos los ramos',overlap==0,overlap)
    DETAILS['F0']=f0_details
    sample=table(WEEK/'Datos/sample_submission.parquet',['row_id']).row_id
    ck('Sample y F0 test misma población',len(sample)==len(ids_test)==len(set(ids_test)) and set(sample)==set(ids_test))
    tests=pd.concat([table(WEEK/f'Datos/test_{l}.parquet',['row_id']).assign(line=l) for l in ['motor','buildings','contents']]).set_index('row_id')
    ck('Test originales y sample misma población',tests.index.is_unique and set(tests.index)==set(sample))
    candidates={}; prod=[]
    for name in ['S30','S22']:
        rec=read(REPO/f'docs/evidencia/recibo_{name}.json')
        p=source(REPO/f'privado/predicciones/{name}.csv')
        df=pd.read_csv(p,dtype={'row_id':str})
        ck(name+' CSV contrato',list(df)==['row_id','prediction'] and df.row_id.is_unique and df.row_id.equals(sample) and np.isfinite(df.prediction).all() and (df.prediction>0).all())
        ck(name+' CSV SHA recibo',sha(p)==rec['sha256'])
        ck(name+' recibo completo',rec['kaggle_status']=='COMPLETE')
        candidates[name]=df.set_index('row_id').prediction
        for line,g in df.set_index('row_id').join(tests).groupby('line'):
            prod.append({'candidato':name,'ramo':line,'filas':len(g),'total':float(g.prediction.sum()),'min':float(g.prediction.min()),'max':float(g.prediction.max())})
    DETAILS['produccion']=prod
    DETAILS['capitales_test']={k:{'filas':len(cap_ids),'total_predicho':float(v.loc[cap_ids].sum()),'fraccion_total':float(v.loc[cap_ids].sum()/v.sum())} for k,v in candidates.items()}
    mix=read(REPO/'registro/artefactos_mezcla.json')
    for v in mix['archivos']:
        ck('Componente guardado '+v['ruta_privada'],sha(source(REPO/mix['carpeta']/v['ruta_privada']))==v['sha256'])
    print('Datos, objetivo, archivos y componentes cotejados.',flush=True)
    n48=WEEK/'Modelado_codex/nocturna_20261017_N01/S30_S31_review_N48/S30'
    old=read(n48/'result.json');pred=table(n48/'aligned_predictions.parquet')
    ck('Predicciones históricas congeladas',sha(n48/'aligned_predictions.parquet')==old['aligned_predictions_sha256'])
    ck('Comparación tiene claves únicas',not pred.duplicated(['corte','row_id']).any())
    ck('Comparación usa T0 reconstruido',np.allclose(pred.T0,independent_t0.loc[pred.row_id].T0,rtol=0,atol=1e-6))
    ck('Comparación usa reservas reconstruidas',np.allclose(pred.case_reserve,independent_t0.loc[pred.row_id].reserve,rtol=0,atol=1e-6))
    metrics=[]
    for r in old['reports']:
        sel=pred.corte.eq(r['cut'])
        if r['scope'] not in ('global','portfolio'):sel &= pred.line.eq(r['scope'])
        if r['semester']!='all':sel &= pred.semester.eq(r['semester'])
        z=pred[sel];k={'reserve075':-.25,'nominal':0,'reserve125':.25}[r['scenario']]
        assert len(z)==r['rows'], (r['cut'],r['scope'],r['semester'],len(z),r['rows'])
        y=z.T0+k*z.case_reserve
        scores={n:d2(y,z[col]) for n,col in [('S22','S22'),('S30','candidate')]}
        delta=scores['S30']-scores['S22']
        err=max(abs(scores['S22']-r['D2']['S22']),abs(scores['S30']-r['D2']['candidate']),abs(delta-r['gain']))
        ck('D2 '+str((r['cut'],r['scope'],r['semester'],r['scenario'])),len(z)==r['rows'] and err<1e-12,err)
        metrics.append({'corte':r['cut'],'ramo':r['scope'],'semestre':r['semester'],'escenario':r['scenario'],'filas':len(z),**scores,'ganancia':delta,'observado_sobre_S30':float(y.sum()/z.candidate.sum())})
    z=pred[pred.corte=='V24'];y=z.T0.to_numpy();a=z.S22.to_numpy();b=z.candidate.to_numpy()
    # Influencia a denominador nulo fijo, sin volver a estimar o seleccionar.
    null=4*(np.sqrt(y.mean())+y/np.sqrt(y.mean())-2*np.sqrt(y));diff=4*(np.sqrt(a)+y/np.sqrt(a)-np.sqrt(b)-y/np.sqrt(b))
    infl=pd.DataFrame({'customer':z.customer_id.to_numpy(),'delta':diff/null.sum()}).groupby('customer').delta.sum()
    DETAILS['influencia_V24']={'ganancia':float(infl.sum()),'diez_clientes_mas_favorables':float(infl.nlargest(10).sum()),'diez_mas_adversos':float(infl.nsmallest(10).sum()),'sin_ids':True}
    DETAILS['metricas']=metrics
    DETAILS['criterio_historico']={'pasa':old['passes_statistical_gate'],'componentes':old['statistical_gate'],'region':old['exact_region'],'intervalos_recibidos':[r for r in old['reports'] if r['cut']=='V24' and r['scope'] in ('global','portfolio') and r['semester']=='all' and r['scenario']=='nominal']}
    # Contraste con implementación publicada, solo sobre las mismas predicciones fijas.
    from sklearn.metrics import d2_tweedie_score
    lib=float(d2_tweedie_score(y,b,power=1.5));own=d2(y,b)
    ck('D2 p1.5 concuerda con sklearn',abs(lib-own)<1e-12,{'propio':own,'sklearn':lib})
    recipe=read(REPO/'receta/receta.json');code=read(REPO/'receta/codigo.json')
    for rel,v in {**code['archivos'],**code['paquete']['archivos']}.items():
        ck('Código '+rel,sha(source(REPO/rel))==v['sha256'])
    nodes={n['id']:n for n in recipe['nodos']};seen=set();graph=[]
    for n in recipe['nodos']:
        ck('Dependencias ordenadas '+n['id'],set(n['requiere'])<=seen and (REPO/n['script']).exists())
        seen.add(n['id']);graph.append({'nodo':n['id'],'salidas':len(n['salidas']),'verificadas':len(n.get('verificar',[])),'excluidas':sorted(set(n['salidas'])-set(n.get('verificar',[])))})
    def ancestors(n):
        return {n}.union(*(ancestors(x) for x in nodes[n]['requiere']))
    DETAILS['receta']={'nodos':len(nodes),'por_objetivo':{k:len(ancestors(v['nodo'])) for k,v in recipe['objetivos'].items()},'cobertura':graph}
    cli=read(REPO/'docs/controles/20261019_windows_v12_lf/resultado.json')
    ck('Recibo histórico CLI vinculado al código actual',all(sha(source(REPO/p))==v for p,v in cli['paquete'].items()))
    DETAILS['CLI_historico']={k:cli[k] for k in ['utc','casos','pasan','etapas_reales_invocadas','alcance']}
    DETAILS['CLI_historico']['repetidos_en_esta_revision']=0
    replay=read(REPO/'docs/evidencia/replay_windows.json');DETAILS['replay_recibido']=replay
    refs=read(REPO/'registro/fuentes.json');changes=[]
    for r in refs:
        p=ROOT/r['ruta_original'];actual=sha(source(p)) if p.exists() else None
        if actual!=r['sha256']:changes.append({'nombre':r['nombre'],'ruta':r['ruta_original'],'antes':r['sha256'],'actual':actual})
    DETAILS['fuentes_panel_con_cambios']=changes
    reqs=read(REPO/'registro/requisitos.json')['requisitos']
    for r in reqs:ck('Referencia requisito '+r['id'],(REPO/r['evidencia']).exists())
    human=read(REPO/'registro/revision_humana.json');ck('Autoría humana no inventada',human['revisor'] is None and human['decision'] is None)
    tracked=subprocess.check_output(['git','-C',str(REPO),'ls-files','-z']).decode().split('\0')
    forbidden=[x for x in tracked if x and (x.startswith('privado/') or Path(x).suffix.lower() in {'.parquet','.csv','.pkl','.pickle','.joblib','.cbm','.pt','.pth','.npy','.npz','.pem','.key'} and not x.startswith('receta/'))]
    ck('Índice Git sin artefactos restringidos por ruta/extensión',not forbidden,forbidden)
    DETAILS['git']={'head':subprocess.check_output(['git','-C',str(REPO),'rev-parse','HEAD']).decode().strip(),'archivos_tracked':len([x for x in tracked if x]),'alcance':'Índice actual y rutas/extensiones. No auditoría de secretos de todo el historial ni verificación remota de permisos.'}
    print('Métricas y gobernanza cotejadas.',flush=True)
    stability=[]
    for p,before in SOURCES.items():
        after=sha(p);stability.append({'ruta':str(Path(p).relative_to(ROOT)).replace('\\','/'),'sha256':before,'estable':before==after})
    ck('Fuentes estables durante la auditoría',all(x['estable'] for x in stability))
    result={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'tipo':'revision_IA_desde_perspectiva_participante','revision_humana':False,'reproduccion_completa':False,'entrenamientos':0,'inferencias':0,'mezclas':0,'envios':0,'delegaciones':0,'entorno':{'python':platform.python_version(),'numpy':np.__version__,'pandas':pd.__version__,'pyarrow':pyarrow.__version__},'controles':CHECKS,'detalle':DETAILS,'fuentes':stability}
    result['resumen']={'total':len(CHECKS),'pasan':sum(x['pasa'] for x in CHECKS),'no_pasan':[x for x in CHECKS if not x['pasa']],'fuentes':len(stability)}
    dump(OUT/'resultado.json',result)
    dump(OUT/'COMPLETE.json',{'utc':result['utc'],'resultado_sha256':sha(OUT/'resultado.json'),'alcance':'Completó auditoría; no es aprobación del sistema.'})
    print(json.dumps(result['resumen'],ensure_ascii=False),flush=True)

if __name__=='__main__':
    main()
