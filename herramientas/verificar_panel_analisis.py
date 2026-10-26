"""Cotejo separado de agregados con filas auditadas, objetivos previos y originales.

No importa funciones del productor. Usa sumas Python/Decimal y verificación
de intervalos por búsqueda binaria, frente al join relacional del productor.
"""
from __future__ import annotations
import bisect
import hashlib
import json
import math
import sys
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import pyarrow.parquet as pq


def main():
    data_path=REPO/'docs/entrega/analisis/datos_panel.json'
    d=json.loads(data_path.read_text(encoding='utf-8'))
    run=ROOT/d['private_run']
    p=pq.read_table(run/'periodos_auditados.parquet').to_pandas()
    c=pq.read_table(run/'siniestros_auditados.parquet').to_pandas()
    checks=[]
    def check(name,ok,detail=None):
        checks.append({'control':name,'pasa':bool(ok),'detalle':detail})
        if not ok:
            raise AssertionError(name)
    for x in d['sources']:
        digest=hashlib.sha256((ROOT/x['ruta']).read_bytes()).hexdigest()
        check('Fuente inalterada '+x['ruta'],digest==x['sha256'])
    for row in d['portfolio']:
        mask=(p.market==row['market'])&(p.line==row['line'])&(p.year==row['year'])
        g=p.loc[mask]
        tag=f"{row['market']}/{row['line']}/{row['year']}"
        check(tag+' filas',len(g)==row['rows'])
        # Los enteros de diezmilésimas y los centavos evitan cancelación flotante.
        exp=sum(round(float(x)*10000) for x in g.exposure)/10000
        check(tag+' exposición por enteros',abs(exp-row['exposure'])<1e-8)
        check(tag+' exposición original fsum',abs(math.fsum(g.exposure_raw)-row['exposure_raw'])<1e-8)
        check(tag+' cambios exposición',sum(bool(x) for x in g.exposure_changed)==row['exposure_changed'])
        check(tag+' cliente conocido',sum(bool(x) for x in g.known_customer)==row['known_customers'])
        if row['is_test']:
            check(tag+' etiquetas ausentes',g.T0_cents.isna().all() and row['T0_cents'] is None and row['positive_periods'] is None)
        else:
            for col in ['T0_cents','paid_cents','incurred_cents','recoveries_cents','reserve_cents','accepted','positive','open']:
                check(tag+' suma escalar '+col,sum(int(x) for x in g[col])==row[col])
            check(tag+' periodos con coste',sum(int(x)>0 for x in g.T0_cents)==row['positive_periods'])
            check(tag+' identidad contable',row['T0_cents']==row['incurred_cents']-row['recoveries_cents'] and row['reserve_cents']==row['incurred_cents']-row['paid_cents'])
            a=c.loc[(c.market==row['market'])&(c.line==row['line'])&(c.year==row['year'])&c.included]
            check(tag+' conciliación siniestros-periodos',sum(int(x) for x in a.T0_cents)==row['T0_cents'] and len(a)==row['accepted'])
            check(tag+' identidad frecuencia positiva × severidad',math.isclose((row['positive']/exp)*(row['T0_cents']/100/row['positive']),row['T0_cents']/100/exp,rel_tol=1e-12))
    # Asignación alternativa: intervalos ordenados y búsqueda binaria por fecha.
    intervals={}
    ordered=p[['market','line','policy_id','period_start','period_end','row_id']].sort_values(['market','line','policy_id','period_start'])
    for market,line,policy,start,end,row in ordered.itertuples(index=False,name=None):
        key=(market,line,policy)
        if key not in intervals:
            intervals[key]=([],[],[])
        starts,ends,ids=intervals[key]
        starts.append(start);ends.append(end);ids.append(row)
    del ordered
    maps={}
    for market,rel in [('developed','Hackaton/Semana 1/Datos'),('emerging','Hackaton/Semana 2/Datos/emerging')]:
        raw=pq.read_table(ROOT/rel/'claims.parquet').to_pandas().set_index('claim_id')
        audit=c.loc[c.market==market]
        retained=set(audit.claim_id)
        original_columns=[x for x in raw.columns]
        # Verifica que cada copia excluida coincide con un registro retenido.
        excluded=raw.loc[~raw.index.isin(retained)]
        if len(excluded):
            payloads=set(pd.util.hash_pandas_object(raw.loc[list(retained),original_columns],index=False).tolist())
            check(market+' copias excluidas coinciden',all(x in payloads for x in pd.util.hash_pandas_object(excluded,index=False)))
        money_total=0
        for x in audit.itertuples(index=False):
            r=raw.loc[x.claim_id]
            starts,ends,ids=intervals[(market,x.line,r.policy_id)]
            date=pd.Timestamp(r.loss_date)
            i=bisect.bisect_right(starts,date)-1
            matched=ids[i] if i>=0 and date<=ends[i] else None
            maps[(market,x.claim_id)]=matched
            if pd.isna(x.row_id):
                if matched is not None or not date<starts[0]:
                    raise AssertionError('Fuera de cobertura mal clasificado')
            elif matched!=x.row_id:
                raise AssertionError('Asignación por búsqueda binaria difiere')
            observed=int((Decimal(str(r.incurred_to_date))-Decimal(str(r.recoveries)))*100)
            if observed!=x.T0_cents:
                raise AssertionError('Dinero Decimal del original difiere')
            if matched is not None and r.status!='repudiated':
                money_total+=observed
        check(market+' asignación alternativa todos los siniestros',True,{'filas':len(audit)})
        check(market+' dinero original Decimal',money_total==sum(x['T0_cents'] or 0 for x in d['portfolio'] if x['market']==market))
    for q in d['quality']:
        check(q['market']+' partición disjunta',q['raw_claims']==q['duplicate_copies']+q['precoverage']+q['repudiated_assigned']+q['included'])
    for row in d['perils']:
        a=c.loc[(c.market==row['market'])&(c.line==row['line'])&(c.year==row['year'])&(c.peril==row['peril'])&c.included]
        tag=f"Peligro {row['market']}/{row['line']}/{row['year']}/{row['peril']}"
        check(tag+' conteo y dinero',len(a)==row['claims'] and sum(int(x) for x in a.T0_cents)==row['T0_cents'])
        delays=sorted(int(x) for x in a.delay_days)
        def quantile(q):
            h=(len(delays)-1)*q;i=int(h)
            return delays[i]+(h-i)*(delays[min(i+1,len(delays)-1)]-delays[i])
        check(tag+' percentiles interpolados por escalar',math.isclose(quantile(.5),row['delay_median'],abs_tol=1e-10) and math.isclose(quantile(.9),row['delay_p90'],abs_tol=1e-10))
    # Los faltantes se recomputan desde la fuente, sin usar funciones de generación.
    lookup={(x['market'],x['line'],x['year'],x['table'],x['field']):x for x in d['missingness']}
    for market,rel in [('developed','Hackaton/Semana 1/Datos'),('emerging','Hackaton/Semana 2/Datos/emerging')]:
        masters={}
        for origin,key in [('customers','customer_id'),('addresses','address_id')]:
            frame=pq.read_table(ROOT/rel/(origin+'.parquet')).to_pandas()
            if origin=='customers':
                frame[key]=frame[key].astype('string').str.zfill(8)
            masters[origin]=frame.set_index(key)
        verified=0
        for line in ['motor','buildings','contents']:
            for kind in ['policies','test']:
                f=pq.read_table(ROOT/rel/(kind+'_'+line+'.parquet')).to_pandas()
                f['year']=pd.to_datetime(f.period_start).dt.year
                f['customer_id']=f.customer_id.astype('string').str.zfill(8)
                for year,g in f.groupby('year'):
                    for origin,frame in [('policies',g),('customers',masters['customers'].reindex(g.customer_id)),('addresses',masters['addresses'].reindex(g.address_id))]:
                        for field in frame.columns:
                            k=(market,line,int(year),origin,field)
                            if k not in lookup:
                                continue
                            old=lookup[k]
                            check('Nulos '+ '/'.join(map(str,k)),len(frame)==old['n'] and int(frame[field].isna().sum())==old['missing'])
                            verified+=1
        check(market+' comprobaciones de faltantes',verified>0,verified)
    # Evitar IDs por fila en el archivo público de agregados.
    check('Agregados sin listas de IDs por fila',not any(k in data_path.read_text(encoding='utf-8') for k in ['"claim_id":','"row_id":','"policy_id":','"customer_id":','"address_id":']))
    receipt={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'data_sha256':hashlib.sha256(data_path.read_bytes()).hexdigest(),
        'metodo':'Sumas escalares, Decimal de originales, intervalos por búsqueda binaria y nulos recalculados',
        'passed':len(checks),'failed':0,'professional_independent_validation':False,'checks':checks}
    (run/'validacion_separada.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='checks'},ensure_ascii=False))


if __name__=='__main__':
    main()
