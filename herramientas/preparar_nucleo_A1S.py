"""Insumos de una alternativa A1 verificable, sin ajustar ni certificar el legado."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';BASE=R/'privado/semana2/mision017_fase2'
OUT=BASE/'A1S_nucleo_20261026_v1'
LEGACY=ROOT/'Hackaton/Semana 2/Claude/validacion_nocturna_20261023/codigo'
RAW={'s1':ROOT/'Hackaton/Semana 1/Datos','s2':ROOT/'Hackaton/Semana 2/Datos/emerging'}
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd


def load(name,path):
    s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m


w=load('writer_A1S_inputs',R/'herramientas/registrar_avance_mision017_fase2.py')
features=load('legacy_A1_pure_features',LEGACY/'variables.py')


class RestrictedReadPandas:
    """Route only the four inspected master-table reads; no filesystem aliases."""
    def __init__(self):
        self.allowed={features.R/f'datos/{mk}/{name}.parquet':path/f'{name}.parquet'
                      for mk,path in RAW.items() for name in ['customers','addresses']}
        self.access=[]
    def __getattr__(self,name):
        if name=='read_parquet':return self.read_parquet
        return getattr(pd,name)
    def read_parquet(self,path,*args,**kwargs):
        path=Path(path);assert path in self.allowed,'Unexpected legacy I/O: '+str(path)
        actual=self.allowed[path];self.access.append(w.rel(actual))
        return pd.read_parquet(actual,*args,**kwargs)


def dump(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf8')


def notifications(raw,source):
    c=pd.read_parquet(raw/'claims.parquet',columns=['claim_id','policy_id','line','report_date'])
    if source:
        copies=c.claim_id.str.len().eq(11);assert int(copies.sum())==604
        c=c.loc[~copies].copy()  # Existing duplicate audit identifies these exact copies.
    c['report_date']=pd.to_datetime(c.report_date)
    assert c.report_date.le('2024-12-31').all()
    return c


def history(base,events):
    f=base[['row_id','policy_id','period_start']].copy()
    f['period_start']=pd.to_datetime(f.period_start)
    f['known_end']=f.period_start.where(f.period_start.le('2024-12-31'),pd.Timestamp('2024-12-31'))
    m=f[['row_id','policy_id','known_end']].merge(events[['policy_id','report_date']],on='policy_id',how='inner')
    m=m.loc[m.report_date.lt(m.known_end)]
    count=f.row_id.map(m.groupby('row_id').size()).fillna(0).to_numpy(float)
    first=f.groupby('policy_id').period_start.min()
    years=((f.known_end-f.policy_id.map(first)).dt.days/365.25).clip(lower=0).to_numpy(float)
    assert np.isfinite(count).all() and np.isfinite(years).all()
    # Direct filtering for an independently selected sample, including future.
    sample=np.unique(np.r_[np.linspace(0,len(f)-1,32,dtype=int),np.flatnonzero(f.period_start.dt.year.eq(2025))[:8]])
    for i in sample:
        expected=int((events.policy_id.eq(f.policy_id.iloc[i])&events.report_date.lt(f.known_end.iloc[i])).sum())
        assert expected==count[i]
    return count,years


def main():
    assert not OUT.exists();OUT.mkdir()
    router=RestrictedReadPandas();features.pd=router
    paths=[Path(__file__),LEGACY/'variables.py',LEGACY/'desarrollado_gbm.py',LEGACY/'evaluar_final.py',
           LEGACY/'base_mercado.py',LEGACY/'reporte.py',LEGACY/'ultimo_mercado.py',LEGACY/'conf_insumos.py',
           BASE/'fuente_f2_2024_v2/report.json',R/'src/semana2/fuente_f2_2024_cb.py']
    for raw in RAW.values():paths+=[raw/f'{name}.parquet' for name in ['customers','addresses','claims','policies_motor','policies_buildings','policies_contents']]
    paths+=[RAW['s2']/f'test_{line}.parquet' for line in ['motor','buildings','contents']]
    for line in ['motor','buildings','contents']:paths.append(BASE/f'fuente_f2_2024_v2/{line}.parquet')
    sources={w.rel(path):w.sha(path) for path in paths};dump(OUT/'sources_before.json',sources)
    source_events=notifications(RAW['s1'],True);target_events=notifications(RAW['s2'],False)
    results=[];outputs={}
    oldlog=w.read(LEGACY.parent/'salidas/s1__log_base.json')
    for line in ['motor','buildings','contents']:
        source=pd.read_parquet(RAW['s1']/f'policies_{line}.parquet');source['is_test']=False
        target=pd.read_parquet(RAW['s2']/f'policies_{line}.parquet');target['is_test']=False
        test=pd.read_parquet(RAW['s2']/f'test_{line}.parquet');test['is_test']=True
        target=pd.concat([target,test],ignore_index=True)
        cached=pd.read_parquet(BASE/f'fuente_f2_2024_v2/{line}.parquet',columns=['row_id','T0','T0_cents','e_cost','year'])
        assert np.array_equal(source.row_id,cached.row_id) and abs(cached.T0.sum()-oldlog[f'{line}_t0'])<.011
        frames={}
        for mk,base,events in [('s1',source,source_events),('s2',target,target_events)]:
            base=base.copy();base['period_start']=pd.to_datetime(base.period_start);base['period_end']=pd.to_datetime(base.period_end)
            base['year']=base.period_start.dt.year;base['exposure_calendar']=((base.period_end-base.period_start).dt.days+1)/365.
            base['exposure_model']=base.exposure_calendar.round(4)
            assert base.year.isin([2021,2022,2023,2024] if mk=='s1' else [2023,2024,2025]).all()
            X,cols,_=features.features(base,line,mk)
            X['exposure_model']=base.exposure_model.to_numpy()
            h,years=history(base,events.loc[events.line.eq(line)])
            X['f1_siniestros_previos']=h;X['f1_anios_observados']=years
            rows=base[['row_id','customer_id','address_id','policy_id','year','period_start','period_end','is_test','new_business','exposure_model','exposure_calendar']].copy()
            if mk=='s1':
                rows['T0']=cached.T0.to_numpy();rows['T0_cents']=cached.T0_cents.to_numpy();rows['e_cost']=cached.e_cost.to_numpy()
                assert rows.e_cost.gt(0).all() and np.isfinite(rows.e_cost).all()
            frames[mk]=(X,rows)
        cols=[c for c in frames['s1'][0] if c in frames['s2'][0] and not(line=='motor' and c=='make_model')]
        assert 'region' not in cols and all(c not in cols for c in ['written_premium','discount_applied','customer_service_contacts','renewal_decision','gender','surname'])
        assert len(set(cols))==len(cols)
        cats=[c for c in cols if str(frames['s1'][0][c].dtype)=='category'];levels={c:frames['s1'][0][c].cat.categories.tolist() for c in cats}
        for mk,(frame,rows) in frames.items():
            X=frame[cols].copy()
            for c in cats:
                values=X[c].astype('string');X[c]=pd.Categorical(values.where(values.isin(levels[c]),'missing'),categories=levels[c])
            for c in cols:
                if c not in cats:X[c]=pd.to_numeric(X[c],errors='coerce').astype('float64')
            assert len(X)==len(rows) and rows.row_id.is_unique and not np.isinf(X.select_dtypes('number').to_numpy()).any()
            mpath=OUT/f'matrix_{mk}_{line}.parquet';rpath=OUT/f'rows_{mk}_{line}.parquet'
            X.to_parquet(mpath,index=False);rows.to_parquet(rpath,index=False)
            outputs[mpath.name]={'sha256':w.sha(mpath),'rows':len(X),'features':cols}
            outputs[rpath.name]={'sha256':w.sha(rpath),'rows':len(rows)}
        results.append({'line':line,'source_rows':len(source),'target_rows':len(target),'features':cols,'categorical_levels_source_only':levels,
                        'source_T0_matches_original_aggregate_to_cent':True,'new_C0_fits':0})
        print(json.dumps({'inputs_ready':line,'source_rows':len(source),'target_rows':len(target),'features':len(cols),'fits':0}),flush=True)
    assert sources=={w.rel(path):w.sha(path) for path in paths}
    report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'A1S_inputs_ready_no_fit',
        'candidate':'New source-safe A1-style alternative; not exact A1fixF1b3n replay or certification',
        'results':results,'source_observation_link':'Reuse exact cached source-only e_cost and T0, no pooled-market curves or new C0',
        'source_feature_implementation':'Inspected legacy variables.features through four allowlisted master-table paths, source-only categories',
        'history':'All notification dates, no eventual claim-status feature; end=min(inception,2024-12-31); observed years capped at same end and nonnegative',
        'differences_from_legacy':['Source-only existing observation contract replaces unverified full F_coste pipeline',
            'All notified past claims instead of eventual accepted status', 'Known-cut elapsed-history exposure, not future calendar years',
            'No claim to neutral-level reproduction of missing b3seedmodels'],
        'legacy_curve_ancestry_limit':'Provided reporting/exposure code allows both-market curves; full cost-curve artifact and original models/rounds missing in checked received sources. Independence of a frozen legacy source object from held target claims is not established. Production training on all target trainingdata remains legitimate.',
        'planned_source_family':{'seeds':[11,12,13],'years':[2021,2022,2023,2024],'loss':'Tweedie1.5','no_new_family_or_feature_search':True,
            'if_registered_fit_budget':{'source_internal_earlystop_fits':9,'source_full_refits':9,'total_real_fit_calls':18},
            'missing_original_round_metadata_means_new_source_only_earlystop_needed':True},
        'new_model_fits':0,'new_C0_fits':0,'new_scores':0,'new_price_predictions':0,'new_submissions':0,
        'do_not_fit_before_recipe_criterion_cost_and_forum_registration':True,'router_master_reads':router.access,
        'sources':sources,'outputs':outputs,'2024_open':True,'B00_all_alternatives_preserved':True,
        'limits':['Undated customer/address master vintages','Source-only maturity1095and case-reserve adequacy assumptions','Retrospective source2024availability, not prospective historical forecasting']}
    dump(OUT/'report.json',report)
    print(json.dumps({'status':report['status'],'new_fits':0,'new_C0':0,'new_scores':0,'total_future_source_fit_budget_if_registered':18}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
