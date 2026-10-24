"""Controles de capital/tiempo y adaptación de NB-CRED-01 a ajuste2023 por fold."""
from pathlib import Path
import importlib.util,sys,json,hashlib,types
REPO=Path(__file__).resolve().parents[2];ROOT=REPO.parents[1]
s=importlib.util.spec_from_file_location('cred6_utils',REPO/'src/semana2/entrenar_desarrollo2023.py')
u=importlib.util.module_from_spec(s);sys.modules[s.name]=u;s.loader.exec_module(u)
np,pd,pq=u.np,u.pd,u.pq

def capital_frame(frame,raw,fold,threshold):
    u.assert_2023(frame);u.require(frame.line.nunique()==1,'Capital mezcla ramos')
    q=raw[['row_id','sum_insured','written_premium']].copy();u.require(q.row_id.is_unique and set(q.row_id)==set(frame.row_id),'Capital IDs distintos')
    out=frame.merge(q,on='row_id',validate='one_to_one');fit=out[out.fold.ne(fold)]
    normal=fit[fit.sum_insured.gt(0)&fit.sum_insured.le(threshold)];ppm=1000*normal.written_premium/normal.sum_insured
    u.require(len(normal)>0 and np.isfinite(ppm).all() and ppm.gt(0).all(),'Prima por mil de ajuste inválida')
    lo,hi=float(ppm.min()),float(ppm.max());suspect=out.sum_insured.gt(threshold)
    own=1000*out.written_premium/out.sum_insured;passed=suspect&own.lt(lo)&(own*1000).between(lo,hi)
    out['audit_capital_suspect']=suspect;out['audit_capital_pass']=passed
    out.loc[suspect,'x_log_sum_insured']=np.where(passed[suspect],np.log(out.loc[suspect,'sum_insured']/1000),np.nan)
    record={'line':str(frame.line.iloc[0]),'fold':int(fold),'fit_normal_rows':len(normal),'fit_ppm_min':lo,'fit_ppm_max':hi,
      'suspect_rows':int(suspect.sum()),'passed_rows':int(passed.sum()),'passed_fit':int((passed&out.fold.ne(fold)).sum()),'passed_validation':int((passed&out.fold.eq(fold)).sum()),
      'normal_fit_row_ids_sha256':hashlib.sha256('\n'.join(sorted(normal.row_id)).encode()).hexdigest()}
    return out,record

def weather_guard(quote_dates,source_years,selector_years,available):
    q=pd.to_datetime(quote_dates);years=np.asarray(source_years)
    u.require(len(q)==len(years) and len(q)>0,'Clima dimensiones inválidas')
    u.require(len(selector_years)>0 and max(selector_years)<int(q.dt.year.min()),'Selector de clima depende del futuro')
    u.require(np.isfinite(years).all() and (years<q.dt.year.to_numpy()).all(),'Medida anual no disponible al cotizar')
    u.require(np.asarray(available,dtype=bool).shape==years.shape and np.asarray(available,dtype=bool).all(),'No hay clima histórico completo, sin backfill futuro')
    return True

def load_author(plan):
    folder=ROOT/'Hackaton/Semana 2/Claude/decisiones_20261023'
    for it in plan['frozen_received_sources']:u.require(u.sha(ROOT/it['path'])==it['sha256'],'Fuente recibida cambiada')
    sys.dont_write_bytecode=True;sys.path.insert(0,str(folder))
    spec=importlib.util.spec_from_file_location('claude_nb_helpers_frozen',folder/'aplicar_decisiones.py')
    author=importlib.util.module_from_spec(spec);sys.modules[spec.name]=author;spec.loader.exec_module(author)
    evidence=u.read(folder/'evidencia_decisiones.json')['nuevo_negocio'];coef=pd.read_csv(folder/'tablas/coeficientes_glm_nb.csv')
    prior={}
    for line in u.LINES:
        d={'f':{},'fse':{},'s':{},'sse':{}}
        for _,r in coef[coef.ramo.eq(line)&coef.beta_dev.notna()&coef.se_dev.notna()].iterrows():
            d[r.componente][r.nivel]=float(r.beta_dev);d[r.componente+'se'][r.nivel]=float(r.se_dev)
        u.require(all('nb' in d[k] for k in ['f','s','fse','sse']),'Prior sin relatividad');prior[line]=d
    return author,evidence,prior

def auxiliary_fit(author,evidence,raw,frame,claims,line,fold):
    u.assert_2023(frame);u.require(frame.fold.ne(fold).all(),'Retenido en credibilidad')
    u.require(set(raw.row_id)==set(frame.row_id),'Auxiliar recibe filas fuera del ajuste')
    p=raw.copy();p['period_start']=pd.to_datetime(p.period_start);p['period_end']=pd.to_datetime(p.period_end);p['year']=2023
    p['dias']=(p.period_end-p.period_start).dt.days+1;p['e']=p.dias/365
    meta=frame.set_index('row_id');p['n']=p.row_id.map(meta.n_positive);p['group_id']=p.row_id.map(meta.group_id)
    p['t0p']=p.row_id.map(meta.T0);p['t0']=p.t0p
    master=pq.read_table(ROOT/'Hackaton/Semana 2/Datos/emerging/addresses.parquet').to_pandas()
    market=types.SimpleNamespace(pol={line:p},addresses=master)
    prepared=author.preparar(market,line,[2023],None)
    median=None;center=0.
    if line!='motor':
        capital=prepared.row_id.map(meta.x_log_sum_insured);median=float(capital.median());u.require(np.isfinite(median),'Capital auxiliar sin mediana')
        prepared['log_si_raw']=capital.fillna(median);center=float(prepared.log_si_raw.mean());prepared['log_si']=prepared.log_si_raw-center
    prepared['nb']=prepared.new_business.astype(float);prepared['source_customer_id']=prepared.customer_id
    # The author's numerical solver clusters by customer_id. Here the explicit alias is the saved graph component.
    prepared['customer_id']=prepared.group_id
    refs=evidence['referencias'][line];region_ref=str(prepared.region.astype(str).value_counts().idxmax());season=np.array(evidence['indice_estacional_desarrollado'][line],float)
    u.require(np.isfinite(season).all() and (season>0).all(),'Estacionalidad prior inválida')
    prepared['e_s']=author.exposicion_mensual(prepared,[2023])@season
    sev=claims[claims.line.eq(line)&claims.row_id.isin(prepared.row_id)&claims.included_in_T0&claims.T0_cents.gt(0)].copy()
    sev['net']=sev.T0_cents/100;sev['customer_id']=sev.row_id.map(meta.group_id)
    u.require(int(prepared.n.sum())==len(sev),'Conteos no concilian con positivos asignados')
    original=author.gr.ajustar;captures=[]
    def audited(X,y,offset,family,cluster,**kwargs):
        r=original(X,y,offset,family,cluster,**kwargs)
        eta=np.asarray(X,dtype=float)@r['beta']+(np.zeros(len(y)) if offset is None else offset);mu=np.exp(eta)
        score=(np.asarray(y)-mu) if family=='poisson' else (np.asarray(y)-mu)/mu
        gradient=np.asarray(X,dtype=float).T@score/len(y)
        u.require(r['convergio'] and np.isfinite(mu).all() and (mu>0).all() and np.max(np.abs(gradient))<=1e-4,'Auxiliar no supera convergencia/score')
        u.require(np.allclose(mu,r['mu'],rtol=1e-10,atol=1e-8),'Clipping de medias activo')
        captures.append({'family':family,'beta':r['beta'].tolist(),'se':r['se'].tolist(),'clusters':r['clusters'],'rows':len(y),'columns':X.shape[1],
          'iterations':r['iteraciones'],'converged':r['convergio'],'mean_score_max':float(np.abs(gradient).max()),'score_threshold':1e-4,'ridge':1e-8})
        return r
    author.gr.ajustar=audited
    try:fit=author.ajustar_mercado(prepared,sev[['row_id','customer_id','net']],line,refs,center,region_ref,season,[2023])
    finally:author.gr.ajustar=original
    detail={'line':line,'fold':fold,'references':refs,'region_reference':region_ref,'capital_median_log':median,'capital_center':center,'seasonality':season.tolist(),
      'fit_rows':len(prepared),'fit_groups':prepared.group_id.nunique(),'fit_rows_sha256':hashlib.sha256('\n'.join(sorted(prepared.row_id)).encode()).hexdigest(),
      'customer_alias_is_graph_component':True,'estimates':captures,'frequency_names':list(fit['f']),'severity_names':list(fit['s']),'fit_summary':fit}
    return fit,detail,prepared,sev[['row_id','customer_id','net']]
