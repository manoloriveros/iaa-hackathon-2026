"""Controles nuevos de ingreso; no entrena ni importa ejecutores históricos."""
from pathlib import Path
from unittest.mock import patch
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
from semana2 import entradas_g4_2023 as core

def verify(root,folder,manifest):
    root=Path(root);folder=Path(folder);folder.mkdir(exist_ok=True)
    checks=[]
    def rejected(label,fn):
        try:fn()
        except ValueError:checks.append({'check':label,'pass':True});return
        raise AssertionError('Contract accepted invalid case: '+label)
    fake=folder/'mixed_year_synthetic.parquet'
    pq.write_table(pa.Table.from_pandas(pd.DataFrame({'year':[2023,2024],'is_test':[False,False]}),preserve_index=False),fake)
    spec={'path':fake.relative_to(root).as_posix(),'sha256':core.sha(fake),'columns':['year','is_test'],'kind':'prepared'}
    with patch.object(pq,'read_table',side_effect=AssertionError('Decoded forbidden year')):
        rejected('mixed_year_rejected_before_decode',lambda:core.read_pinned(root,spec))
        bad={**spec,'sha256':'0'*64}
        rejected('changed_source_rejected_before_decode',lambda:core.read_pinned(root,bad))
    rejected('model_path_rejected',lambda:core.safe_path(root,'Hackaton/Repositorio_IAA2026/privado/models/fake.parquet'))
    rejected('prediction_path_rejected',lambda:core.safe_path(root,'Hackaton/Repositorio_IAA2026/privado/oof_2023.parquet'))
    meta=pd.DataFrame([{'market':'emerging','line':'buildings','row_id':'SYN-INGRESS-'+str(k),'year':2023,'is_test':False,'fold':k,
        'group_id':'SYN-G-'+str(k),'customer_id':'SYN-C-'+str(k),'address_id':'SYN-A-'+str(k),'policy_id':'SYN-P-'+str(k)} for k in range(5)])
    rejected('duplicate_key',lambda:core.validate_membership(pd.concat([meta,meta.iloc[[0]]],ignore_index=True)))
    crossed=meta.copy();crossed.loc[1,'group_id']=crossed.loc[0,'group_id']
    rejected('cross_fold_group',lambda:core.validate_membership(crossed))
    p=meta.iloc[:2].copy();p['period_start']='2023-01-01';p['period_end']='2023-12-31';p['exposure']=1.
    for name in core.STATIC:p[name]='synthetic_category' if name in ['x_property_type','x_region'] else 1.
    capital=meta.iloc[:2].copy();capital['sum_insured_original']=[200000.,300000000.];capital['written_premium_audit_only']=[200.,300.]
    data={'periods':p,'capital_audit':capital,'scope':{'excluded_folds':[3,4],'training_input_sha256':'a'*64}}
    rejected('capital_without_parameters',lambda:core.apply_frozen_capital(data))
    params={'excluded_folds':[3,4],'training_input_sha256':'a'*64,'threshold':1e7,'ppm_min':.5,'ppm_max':5.}
    rejected('capital_parameters_wrong_scope',lambda:core.apply_frozen_capital(data,{**params,'excluded_folds':[2,4]}))
    out=core.apply_frozen_capital(data,params)
    np.testing.assert_allclose(out.x_log_sum_insured,[np.log(200000),np.log(300000)],rtol=0,atol=1e-14)
    assert 'written_premium_audit_only' not in out;checks.append({'check':'frozen_capital_application_synthetic_only','pass':True})
    reads=[]
    for excluded in [[0],[0,1]]:
        held={manifest['fold_files'][str(f)][kind]['path'] for f in excluded for kind in ['periods','targets','claims','capital_audit']}
        real=core.read_pinned
        def spy(r,s,*a,**kw):
            assert s['path'] not in held,'Protected fold file opened'
            reads.append(s['path']);return real(r,s,*a,**kw)
        with patch.object(core,'read_pinned',spy):d=core.load_training_scope(root,manifest,excluded)
        assert not d['model_input_ready'] and not d['C0_present'] and d['capital_parameters_required']
        masked=core.masked_periods_for_future_C0(d)
        protected=masked.fold.isin(excluded)&masked.line.eq('buildings')
        assert masked.loc[protected,['period_start','period_end','exposure']].isna().all().all()
        allowed=masked.line.eq('buildings')&~masked.fold.isin(excluded)
        assert masked.loc[allowed,['period_start','period_end','exposure']].notna().all().all()
        checks.append({'check':'real_scope_reader_no_protected_value_files_'+str(excluded),'pass':True})
    assert len(manifest['scopes'])==15
    for scope in manifest['scopes'].values():
        assert set(scope['training_folds']).isdisjoint(scope['excluded_folds'])
        assert all(x['fold'] in scope['training_folds'] for x in scope['training_files'])
        assert not scope['C0_present'] and not scope['learned_objects_present']
    checks.append({'check':'all15_scope_file_lists_disjoint','pass':True})
    return {'scope':'Ingress contracts and logical scopes only; no model fitting or C0 estimation','checks':checks,
        'real_scope_views_checked':2,'protected_value_files_decoded':0,'model_fits':0,'C0_fits':0,'success':True}
