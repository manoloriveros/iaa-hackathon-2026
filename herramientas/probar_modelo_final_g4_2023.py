"""Prueba focal del nuevo ámbito final/tres ramos; no repite la suite histórica."""
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import joblib
from semana2 import modelo_final_g4_2023 as core


def verify(folder,recipe):
    folder=Path(folder);folder.mkdir()
    checks=[];versions={'generated_fixture':'a'*64};fit_receipts=[]
    for line in core.LINES:
        records=[]
        for i in range(120):
            key='SYN-G4-FINAL-'+line+'-'+str(i)
            r=dict(market='emerging',line=line,row_id=key,year=2023,is_test=False,policy_id=key+'P',customer_id=key+'C',
                address_id=key+'A',group_id=key+'G',fold=i%5,period_start=pd.Timestamp('2023-01-01'),
                period_end=pd.Timestamp('2023-12-31'),exposure=1.,x_new_business=float(i%2),T0=(1000+i*3)/100.)
            for name in recipe['features_by_line'][line]['numeric']:
                r.setdefault(name,float(2+i%5))
            for name in recipe['features_by_line'][line]['categorical']:
                r[name]='comprehensive' if name=='x_cover_type' else 'house' if name=='x_property_type' else 'R1'
            records.append(r)
        static=pd.DataFrame(records)
        if line!='motor':static['x_accidental_damage_cover']=np.arange(120)%2
        coverage=static[core.ingress.META+['period_start','period_end','exposure','x_new_business']].copy()
        col='cover_type' if line=='motor' else 'accidental_damage_cover'
        coverage[col]=static['x_'+col]
        claims=static[core.ingress.META].copy();claims['claim_id']=static.row_id+'CL';claims['included_in_T0']=True
        claims['peril']=[core.PERILS[line][i%len(core.PERILS[line])] for i in range(120)]
        claims['loss_date']=pd.Timestamp('2023-01-01')+pd.to_timedelta(np.arange(120)*3,unit='D')
        age=(pd.Timestamp(core.kernel.VALUATION)-claims.loss_date).dt.days.to_numpy()
        delay=np.minimum(age,(np.arange(120)%8)*80)
        claims['report_date']=claims.loss_date+pd.to_timedelta(delay,unit='D')
        claims['T0_cents']=np.rint(static.T0*100).astype('int64')
        frame,cc=core.assemble_training(static,coverage,claims,line,recipe['features_by_line'][line])
        capital=None
        raw=frame[['row_id','period_start','period_end']].copy()
        raw['sum_insured']=1000000. if line=='buildings' else 100000.
        raw['written_premium']=1000. if line=='buildings' else 100.
        if line!='motor':
            capital,population=core.fit_capital_final(frame,raw,line,versions)
            frame,_=core.apply_capital(frame,raw,capital)
            assert len(population)==120
        c0=core.fit_c0_final(frame,cc,line,versions)
        e,c0check=core.training_c0(frame,c0)
        bundle,receipt=core.fit_glm_final(frame,e,recipe,line,capital,c0)
        state=core.learned_state_digest(bundle)
        path=folder/(line+'.joblib');joblib.dump(bundle,path,compress=3)
        rawq=pd.DataFrame({'row_id':['SYN-G4-QUOTE-'+line+str(i) for i in range(20)],'policy_id':'QP',
            'customer_id':'QC','address_id':['QA'+str(i) for i in range(20)],'period_start':pd.Timestamp('2025-01-01'),
            'period_end':pd.Timestamp('2025-12-31'),'exposure':1.,'new_business':np.arange(20)%2,
            'ncb_years':3.,'vehicle_age':4.,'vehicle_value_group':3.,'driver_age_band':'R1','cover_type':'comprehensive',
            'sum_insured':1000000. if line=='buildings' else 100000.,'written_premium':1000. if line=='buildings' else 100.,
            'accidental_damage_cover':np.arange(20)%2,'high_value_items':2.})
        rawq.loc[0,'exposure']=365.
        rawq.loc[1,'exposure']=round(365/360,4)
        addresses=pd.DataFrame({'address_id':['QA'+str(i) for i in range(20)],'region':'R1','property_type':'house',
            'year_built':1980.,'flood_zone':2.,'bedrooms':3.})
        quote,audit=core.quote_features(rawq,addresses,line,recipe['features_by_line'][line],capital)
        pred,_=core.predict_quotes(bundle,quote)
        assert len(pred)==20 and np.isfinite(pred.prediction).all() and pred.prediction.gt(0).all()
        assert state==core.learned_state_digest(bundle)
        with patch.object(core.TweedieRegressor,'fit',side_effect=AssertionError('Replay fit')), \
             patch.object(core,'fit_c0_final',side_effect=AssertionError('Replay C0')), \
             patch.object(core,'fit_capital_final',side_effect=AssertionError('Replay capital')):
            replay,_=core.predict_quotes(joblib.load(path),quote)
        assert pred.equals(replay)
        assert audit['exposure_rules']['days_stored_as_years']==1 and audit['exposure_rules']['basis_360']==1
        checks.append({'check':'synthetic_final_scope_full_chain_'+line,'pass':True})
        fit_receipts.append({'line':line,'GLM':receipt,'C0':c0check})
        forbidden=frame.copy();forbidden['year']=2024
        try:core.assert_train(forbidden,line)
        except ValueError:checks.append({'check':'reject_non2023_training_'+line,'pass':True})
        else:raise AssertionError('Accepted forbidden training year')
        if line!='motor':
            wrong=dict(capital);wrong['excluded_folds']=[0]
            try:core.apply_capital(quote,rawq,wrong)
            except ValueError:checks.append({'check':'reject_outer_capital_as_final_'+line,'pass':True})
            else:raise AssertionError('Accepted exterior capital')
    return {'success':True,'checks':checks,'synthetic_GLM_fits':3,'synthetic_reporting_fits':15,
        'synthetic_frequency_constants':15,'real_fits':0,'fit_receipts':fit_receipts,'no_2024_policy_rows_read':True}
