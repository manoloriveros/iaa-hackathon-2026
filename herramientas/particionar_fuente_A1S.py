"""Partición fuente por componentes cliente/dirección, sin leer respuestas."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import json
import sys

ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';HOME=R/'privado/semana2/mision017_fase2/A1S_nucleo_20261026_v1'
OUT=HOME/'partition_source'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd


def writer():
    spec=importlib.util.spec_from_file_location('A1S_partition_writer',R/'herramientas/registrar_avance_mision017_fase2.py')
    w=importlib.util.module_from_spec(spec);spec.loader.exec_module(w);return w


def components(customer,address):
    customers=pd.Index(pd.unique(customer)).sort_values();addresses=pd.Index(pd.unique(address)).sort_values()
    ci=customers.get_indexer(customer);ai=addresses.get_indexer(address)+len(customers)
    par=np.arange(len(customers)+len(addresses),dtype='int64')
    def find(i):
        while par[i]!=i:
            par[i]=par[par[i]];i=par[i]
        return i
    for c,a in zip(ci,ai):
        rc,ra=find(c),find(a)
        if rc!=ra:par[max(rc,ra)]=min(rc,ra)
    root=np.array([find(i) for i in ci]);assert (root<len(customers)).all()
    canonical=customers.to_numpy()[root]
    return canonical


def main():
    assert not OUT.exists();OUT.mkdir();w=writer()
    # Transitivity and namespace separation, without data or models.
    c=np.array(['x','y','y','z']);a=np.array(['x','x','q','z'])
    g=components(c,a);assert g[0]==g[1]==g[2] and g[3]!=g[0]
    reverse=components(c[::-1],a[::-1])[::-1];assert np.array_equal(g,reverse)
    paths=[Path(__file__),HOME/'report.json'];frames=[]
    for line in ['motor','buildings','contents']:
        path=HOME/f'rows_s1_{line}.parquet';paths.append(path)
        # No T0, e_cost or any response is loaded to choose the partition.
        f=pd.read_parquet(path,columns=['row_id','customer_id','address_id','year'])
        f['line']=line;f['customer_canonical']=f.customer_id.astype(str).str.zfill(8)
        assert f.customer_canonical.notna().all() and f.address_id.notna().all();frames.append(f)
    before={w.rel(p):w.sha(p) for p in paths};f=pd.concat(frames,ignore_index=True)
    group=components(f.customer_canonical.to_numpy(),f.address_id.astype(str).to_numpy())
    f['source_group']='source|'+pd.Series(group).astype(str)
    sizes=f.source_group.value_counts().rename_axis('group').reset_index(name='rows')
    sizes=sizes.sort_values(['rows','group'],ascending=[False,True],kind='stable')
    totals=np.zeros(5,dtype='int64');assignment={}
    for key,count in zip(sizes.group,sizes.rows):
        fold=int(np.argmin(totals));assignment[key]=fold;totals[fold]+=int(count)
    f['fold']=f.source_group.map(assignment).astype('int8')
    # Inner held fold is selected by unlabeled size only, before any model/score.
    held=int(np.argmin(np.abs(totals/len(f)-.2)))
    f['internal_validation']=f.fold.eq(held)
    assert f.groupby('customer_canonical').source_group.nunique().max()==1
    assert f.groupby('address_id').source_group.nunique().max()==1
    assert f.groupby('source_group').fold.nunique().max()==1
    byline=[];outputs={}
    for line in ['motor','buildings','contents']:
        p=f.loc[f.line.eq(line)].copy();mask=p.internal_validation
        assert .05<float(mask.mean())<.45,'Unusable validation fraction; no labels consulted.'
        assert not set(p.loc[mask,'customer_canonical']).intersection(p.loc[~mask,'customer_canonical'])
        assert not set(p.loc[mask,'address_id']).intersection(p.loc[~mask,'address_id'])
        path=OUT/f'folds_{line}.parquet';p.to_parquet(path,index=False)
        outputs[path.name]={'sha256':w.sha(path),'rows':len(p)}
        byline.append({'line':line,'rows':len(p),'training_rows':int((~mask).sum()),'validation_rows':int(mask.sum()),'validation_fraction':float(mask.mean())})
    assert before=={w.rel(p):w.sha(p) for p in paths}
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'status':'source_partition_complete_no_labels_or_fit',
        'group_definition':'Connected components of canonical8digit customer and separate address namespace across all3source lines',
        'assignment':'Deterministic greedy5fold by descending component size, lexical canonical group tie-break; held fold closest20%unlabeled row count, tie lowest index',
        'rows':len(f),'groups':len(sizes),'largest_component_rows':int(sizes.rows.max()),'largest_component_fraction':float(sizes.rows.max()/len(f)),
        'fold_rows':totals.tolist(),'inner_held_fold':held,'by_line':byline,
        'all_shared_customer_address_edges_protected':True,'transitive_and_reversal_synthetic_passed':True,
        'responses_read':False,'new_model_fits':0,'new_C0_fits':0,'new_scores':0,
        'conditional_offset_limit':'The existing source-only reporting exposure was learned on the whole source. Source inner early stopping is conditional on it, not independent end-to-end validation. Target held groups remain independent of source training labels.',
        'sources':before,'outputs':outputs,'2024_open':True,'B00_all_alternatives_preserved':True}
    (OUT/'report.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf8')
    print(json.dumps({k:result[k] for k in ['status','rows','groups','largest_component_fraction','fold_rows','inner_held_fold','by_line','new_model_fits']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf-8');main()
