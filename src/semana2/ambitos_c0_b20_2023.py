"""Contrato puro de pertenencia para preflight; no importa estimadores o datos."""
import hashlib
import json

KEY=('market','line','row_id')


def key(row):
    return tuple(row[x] for x in KEY)


def validate_periods(rows):
    if not rows or any(r['year']!=2023 or r.get('is_test',False) or r['fold'] not in range(5) for r in rows):
        raise ValueError('Solo periodos2023, sin test y con folds0..4.')
    if len({key(r) for r in rows})!=len(rows):
        raise ValueError('Claves compuestas repetidas.')
    for field in ['group_id','customer_id','address_id']:
        seen={}
        for r in rows:
            value=r[field]
            if value in seen and seen[value]!=r['fold']:
                raise ValueError('Cruce de folds en '+field)
            seen[value]=r['fold']


def select_scope(rows,excluded,line='buildings'):
    validate_periods(rows)
    if len(excluded) not in [1,2] or len(set(excluded))!=len(excluded) or any(x not in range(5) for x in excluded):
        raise ValueError('Excluir uno o dos folds distintos; no redefine particiones.')
    fit=[r for r in rows if r['line']==line and r['fold'] not in excluded]
    held=[r for r in rows if r['line']==line and r['fold'] in excluded]
    if not fit or not held:
        raise ValueError('Ámbito vacío.')
    for field in ['group_id','customer_id','address_id']:
        if {r[field] for r in fit}&{r[field] for r in held}:
            raise ValueError('Solapamiento en '+field)
    return fit,held


def membership_digest(rows):
    # Explicit composites and scope fields; no price, loss or learned parameter.
    records=sorted([*[str(r[k]) for k in KEY],str(r['fold']),str(r['group_id']),
                    str(r['customer_id']),str(r['address_id'])] for r in rows)
    return hashlib.sha256(json.dumps(records,ensure_ascii=False,separators=(',',':')).encode()).hexdigest()
