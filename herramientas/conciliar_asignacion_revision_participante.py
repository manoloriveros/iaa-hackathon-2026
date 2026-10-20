"""Seguimiento puntual de los tres comparadores Series.equals del auditor integral."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json
import numpy as np
import pyarrow.parquet as pq

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
WEEK=ROOT/'Hackaton/Semana 1'
OUT=REPO/'privado/revision_participante_20261019_asignacion'
def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def main():
    OUT.mkdir(exist_ok=False)
    idx=read(WEEK/'Limpieza/current_dataset.json');cat=read(ROOT/idx['catalog_workspace_relative'])
    cp=ROOT/cat['claims']['workspace_relative_path']
    ap=WEEK/'Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0/tables/asignacion_por_siniestro.parquet'
    paths=[Path(__file__),cp,ap]+[ROOT/cat['policies_'+l]['workspace_relative_path'] for l in ['motor','buildings','contents']]
    before={str(p.relative_to(ROOT)):sha(p) for p in paths}
    claims=pq.read_table(cp,columns=['claim_id','policy_id','line','loss_date']).to_pandas()
    assigned=pq.read_table(ap,columns=['claim_id','row_id']).to_pandas().set_index('claim_id')
    checks=[]
    for l in ['motor','buildings','contents']:
        p=pq.read_table(ROOT/cat['policies_'+l]['workspace_relative_path'],columns=['policy_id','row_id','period_start','period_end']).to_pandas()
        c=claims[claims.line==l];m=c.merge(p,on='policy_id',how='inner')
        m=m[(m.loss_date>=m.period_start)&(m.loss_date<=m.period_end)]
        actual=c.claim_id.map(m.set_index('claim_id').row_id).fillna('<sin_periodo>')
        expected=c.claim_id.map(assigned.row_id).fillna('<sin_periodo>')
        mismatch=np.asarray(actual.astype(str))!=np.asarray(expected.astype(str))
        checks.append({'control':'Asignación alternativa coincide '+l,'pasa':bool(not mismatch.any() and m.claim_id.is_unique),'filas':len(c),'diferencias_valor':int(mismatch.sum()),'duplicados_asignacion':int(m.claim_id.duplicated().sum()),'equals_estricto':bool(actual.equals(expected)),'tipo_calculado':repr(actual.dtype),'tipo_referencia':repr(expected.dtype),'indices_iguales':actual.index.equals(expected.index)})
    stable=all(sha(ROOT/p)==h for p,h in before.items())
    out={'autor':'Codex','utc':datetime.now(timezone.utc).isoformat(),'sustituye_solo_tres_controles':'privado/revision_participante_20261019_r3/resultado.json','controles':checks,'fuentes':before,'fuentes_estables':stable,'alcance':'Cotejo por valor e índice; las diferencias de dtype se informan sin tratarlas como asignaciones distintas. No crea T0 ni cambia el sistema.'}
    (OUT/'resultado.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(out,ensure_ascii=False),flush=True)
if __name__=='__main__':main()
