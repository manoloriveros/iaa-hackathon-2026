"""Mismo adaptador de validación aplicado al ámbito final2023, sin C0nuevo."""
from pathlib import Path
import numpy as np,pandas as pd,joblib
from scipy import sparse,optimize
from sklearn.preprocessing import OneHotEncoder
from . import modelo_profesor_comun2023 as core
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
TEACHERS={
 'motor':R/'privado/semana2/robustez2023/ciclo6_20261025_v1/teachers/W2-COD-R32_motor.joblib',
 'buildings':R/'privado/semana2/robustez2023/ciclo7_20261025_v1/teachers/W2-COD-R35_buildings.joblib',
 'contents':R/'privado/semana2/robustez2023/ciclo6_20261025_v1/teachers/W2-COD-R32_contents.joblib'}


def fit_adapter(frame,line,teacher):
    core.guard(frame,line);f=core.features(frame,line)
    original=joblib.hash(teacher);a=core.teacher_rate(teacher,f)
    encoder=OneHotEncoder(drop='first',handle_unknown='ignore',min_frequency=50,sparse_output=True);encoder.fit(f[['x_region']])
    x=core.adapter_matrix(f,encoder);e=f['e_cost_mix_1.0'].to_numpy(float);y=f.T0.to_numpy(float)/e;w=np.sqrt(e);w=w/w.sum()
    offset=np.log(a);beta=np.zeros(x.shape[1]);beta[-1]=np.log(np.sum(w*y/np.sqrt(a))/np.sum(w*np.sqrt(a)))
    penalty=np.r_[np.ones(x.shape[1]-1),0.]
    def objective(coef):
        eta=offset+x@coef;smu=np.exp(eta/2);inv=np.exp(-eta/2)
        loss=2*np.dot(w,y*inv+smu-2*np.sqrt(y))+.5*np.dot(penalty*coef,coef)
        grad=np.asarray(x.T@(w*(smu-y*inv))).ravel()+penalty*coef
        return float(loss),grad
    result=optimize.minimize(objective,beta,jac=True,method='L-BFGS-B',options={'maxiter':3000,'gtol':1e-7,'ftol':1e-14,'maxls':50})
    value,g=objective(result.x);core.base.require(result.success and np.abs(g).max()<=1e-4,'Adaptadorfinal no convergió')
    core.base.require(joblib.hash(teacher)==original,'Profesor alterado')
    return ({'model_id':'W2-COD-R35-FINAL','line':line,'held_fold':None,'teacher':teacher,'region_encoder':encoder,'coef':result.x},
      {'line':line,'fit_rows':len(f),'n_iter':int(result.nit),'max_abs_gradient':float(np.abs(g).max()),'objective':value,
       'teacher_unchanged':True,'scope':'all_emerging2023_final_for2025','new_price_fits':1})


def fit_final(frame,line):
    teacher=joblib.load(TEACHERS[line])
    core.base.require(teacher['line']==line,'Profesor de otro ramo')
    if line=='buildings':
        core.base.require('x_construction_type' not in teacher['columns'] and 'x_construction_type' not in teacher['parent']['columns'],'Construcción ambigua en profesor final')
    return fit_adapter(frame,line,teacher)


POLICY_EXTRAS={
 'motor':['years_licensed','engine_size_cc','named_young_driver','driver_assist','voluntary_excess','compulsory_excess','body_type','transmission','fuel_type','overnight_parking','vehicle_use'],
 'buildings':['smoke_alarms','voluntary_excess','compulsory_excess','construction_type','occupancy'],
 'contents':['bicycle_cover','voluntary_excess','compulsory_excess','security_level','tenure']}


def enrich_quotes(frozen,raw,addresses,line):
    core.guard(frozen,line,training=False)
    core.base.require(not raw.row_id.duplicated().any() and set(raw.row_id)==set(frozen.row_id),'Cobertura2025discrepante')
    core.base.require(pd.to_datetime(raw.period_start).dt.year.eq(2025).all() and pd.to_datetime(raw.period_end).dt.year.eq(2025).all(),'Solo cotizaciones2025')
    datecheck=frozen[['row_id','period_start','period_end']].merge(raw[['row_id','period_start','period_end']],on='row_id',validate='one_to_one',suffixes=('_saved','_raw'))
    for c in ['period_start','period_end']:core.base.require(pd.to_datetime(datecheck[c+'_saved']).eq(pd.to_datetime(datecheck[c+'_raw'])).all(),'Fechas2025 cambiaron')
    extra=raw[['row_id']+POLICY_EXTRAS[line]].rename(columns={c:'x_'+c for c in POLICY_EXTRAS[line]})
    out=frozen.merge(extra,on='row_id',how='left',validate='one_to_one')
    if line!='motor':
        acols=['address_id','distance_to_river_km','elevation_m','roof_type','soil_type']+(['basement'] if line=='contents' else [])
        a=addresses[acols].rename(columns={c:'x_'+c for c in acols if c!='address_id'})
        out=out.merge(a,on='address_id',how='left',validate='many_to_one',indicator=True)
        core.base.require(out['_merge'].eq('both').all(),'Dirección2025no enlazada');out=out.drop(columns='_merge')
        if line=='buildings':
            out['x_construction_type']=out.x_construction_type.replace({'BRK':'brick','STN':'stone','WOD':'timber','MIX':'mixed_or_nonstandard'})
    # Todos los campos originales, incluidos capital/exposición/cobertura, siguen idénticos por clave.
    a=frozen.sort_values(core.KEY).reset_index(drop=True);b=out.sort_values(core.KEY).reset_index(drop=True)
    for c in frozen.columns:core.base.require(a[c].equals(b[c]),'Columna original cambió: '+c)
    return core.features(out,line)
