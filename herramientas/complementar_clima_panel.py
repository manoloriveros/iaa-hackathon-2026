"""Añade el control de clima al corte EDA, conservando el agregado base y su SHA.

El join es address_id + año dentro de mercado; no convierte clima 2025 en
información disponible al cotizar. Los controles usan además conteos Arrow.
"""
from __future__ import annotations
import hashlib
import json
import sys
from datetime import datetime,timezone
from pathlib import Path
REPO=Path(__file__).resolve().parents[1];ROOT=REPO.parents[1]
sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
import pandas as pd
import pyarrow as pa
import pyarrow.compute as pc
import pyarrow.parquet as pq


def main():
    target=REPO/'docs/entrega/analisis/datos_panel.json';raw=target.read_bytes();d=json.loads(raw)
    if d.get('climate_extension'):
        raise ValueError('El clima ya está integrado; regenerar base antes de repetir esta ampliación.')
    run=ROOT/d['private_run'];base_sha=hashlib.sha256(raw).hexdigest()
    (run/'datos_antes_clima.json').write_bytes(raw)
    p=pq.read_table(run/'periodos_auditados.parquet',columns=['market','line','year','address_id']).to_pandas()
    checks=[];coverage=[];extra=[]
    def check(label,ok,detail=None):
        checks.append({'control':label,'pasa':bool(ok),'detalle':detail})
        if not ok:raise AssertionError(label)
    for market,rel in [('developed','Hackaton/Semana 1/Datos'),('emerging','Hackaton/Semana 2/Datos/emerging')]:
        weather=pq.read_table(ROOT/rel/'weather.parquet').to_pandas()
        check(market+' clima clave única',not weather.duplicated(['address_id','year']).any())
        fields=[x for x in weather.columns if x not in ['address_id','year']]
        j=p.loc[p.market.eq(market)].merge(weather,on=['address_id','year'],how='left',validate='many_to_one',indicator=True)
        check(market+' clima sin expansión',len(j)==int(p.market.eq(market).sum()))
        for (line,year),g in j.groupby(['line','year']):
            matched=int(g._merge.eq('both').sum())
            coverage.append({'market':market,'line':line,'year':int(year),'rows':len(g),'matched':matched})
            check(f'{market}/{line}/{year}: cobertura clima',matched==len(g),matched)
            arrow=pa.Table.from_pandas(g[fields],preserve_index=False)
            for field in fields:
                n=int(g[field].isna().sum())
                check(f'{market}/{line}/{year}/{field}: nulos Arrow',int(pc.sum(pc.is_null(arrow[field])).as_py())==n)
                extra.append({'market':market,'line':line,'year':int(year),'table':'weather','field':field,'n':len(g),'missing':n})
    d['missingness'].extend(extra)
    d['climate_coverage']=coverage
    d['climate_extension']={'base_data_sha256':base_sha,'utc':datetime.now(timezone.utc).isoformat(),'controls':len(checks),'failed':0,
        'code':'herramientas/complementar_clima_panel.py','code_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'interpretation':'Clima de 2025 presente en archivo; disponibilidad al cotizar sin confirmar.'}
    d['sources'].append({'ruta':Path(__file__).relative_to(ROOT).as_posix(),'sha256':d['climate_extension']['code_sha256'],'rol':'ampliacion_clima'})
    encoded=json.dumps(d,ensure_ascii=False,indent=1,allow_nan=False)+'\n'
    target.write_text(encoded,encoding='utf-8');(run/'agregados_con_clima.json').write_text(encoded,encoding='utf-8')
    receipt={'base_data_sha256':base_sha,'final_data_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'controls':checks,'passed':len(checks),'failed':0}
    (run/'validacion_clima.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({k:v for k,v in receipt.items() if k!='controls'}))


if __name__=='__main__':main()
