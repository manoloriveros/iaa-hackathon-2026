"""Solo correspondencia documental y de nombres/tipos; no valores de filas."""
from pathlib import Path
from datetime import datetime, timezone
import sys, json, hashlib
ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F03_2023/f03_20261024_v1'
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pyarrow.parquet as pq

def main():
    r=json.loads((RUN/'dictionary_response.json').read_text(encoding='utf-8'))
    current=json.loads(next(x['text'] for x in r['content'] if x['type']=='text'))['pages']
    old=json.loads((ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json').read_text(encoding='utf-8'))['value']
    old=json.loads(next(x['text'] for x in old['content'] if x['type']=='text'))['pages']
    assert current==old
    schemas=[];comparison=[]
    tables=['policies_motor','policies_buildings','policies_contents','addresses','customers','claims']
    for market,base in [('developed',ROOT/'Hackaton/Semana 1/Datos'),('emerging',ROOT/'Hackaton/Semana 2/Datos/emerging')]:
        for table in tables:
            p=base/(table+'.parquet')
            if market=='emerging' and table=='policies_buildings':
                prior=json.loads((REPO/'privado/semana2/revision_F02_2023/f02_20261024_v1/policy_schema_only.json').read_text(encoding='utf-8'))
                cols=prior['columns'];method='reused F02 schema-only receipt'
            else:
                pf=pq.ParquetFile(p)
                cols=[{'name':f.name,'type':str(f.type)} for f in pf.schema_arrow]
                pf.close();method='schema_arrow only; no row/rowgroup-stat read'
            schemas.append({'market':market,'table':table,'path':p.relative_to(ROOT).as_posix(),'method':method,'columns':cols})
    for table in tables:
        a={x['name']:x['type'] for s in schemas if s['market']=='developed' and s['table']==table for x in s['columns']}
        b={x['name']:x['type'] for s in schemas if s['market']=='emerging' and s['table']==table for x in s['columns']}
        comparison.append({'table':table,'developed_only':sorted(a.keys()-b.keys()),'emerging_only':sorted(b.keys()-a.keys()),'common_type_differences':{k:[a[k],b[k]] for k in sorted(a.keys()&b.keys()) if a[k]!=b[k]}})
    receipt={'utc':datetime.now(timezone.utc).isoformat(),'scope':'F03 correspondence of schemas and dictionary, no policy/claim values any year read','dictionary_unchanged_from_archive':True,'dictionary_current_response_sha256':hashlib.sha256((RUN/'dictionary_response.json').read_bytes()).hexdigest(),'schemas':schemas,'comparison':comparison,'row_values_read':0,'rowgroup_statistics_consulted':False,'environment_note':'Initial direct import lacked pyarrow; reused installed local Preparación/.cache/parquet-reader, no dependency install. Initial attempt read no tables.'}
    with (RUN/'schema_dictionary_receipt.json').open('x',encoding='utf-8') as f:json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'comparison':comparison,'dictionary_unchanged':True,'row_values_read':0},ensure_ascii=True))

if __name__=='__main__':main()
