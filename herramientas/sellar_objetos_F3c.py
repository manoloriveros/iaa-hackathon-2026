"""Sello de objetos de producción y evaluación; no ajusta ni infiere precios."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json
R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
OLD=R/'privado/semana2/mision017_fase2/F3c_validacion_completa_20261027'
OUT=R/'privado/semana2/cierre_F3c_20261028';LEGACY=R/'privado/reentrenamiento_completo_20261026/corrida'
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p):
    h=hashlib.sha256()
    with p.open('rb') as stream:
        for block in iter(lambda:stream.read(1<<20),b''):h.update(block)
    return h.hexdigest()
def main():
    audit=read(OUT/'audit.json');assert audit['decision']['reference_file_can_be_sealed'];records=[]
    for rec in read(OLD/'original18_source_schemas.json')['records']:
        path=R/rec['path'];assert sha(path)==rec['sha256']
        records.append({'role':'production_A1_'+rec['family'],'line':rec['line'],'seed':rec['seed'],'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':rec['sha256']})
    comparison=read(LEGACY.parent/'comparacion_final.json')['model_text'];expected={comparison['prod_'+line]['new_sha256']:line for line in ['motor','buildings','contents']};found=set()
    for path in (LEGACY/'ml').rglob('*.txt'):
        digest=sha(path)
        if digest in expected:
            line=expected[digest];found.add(line);records.append({'role':'production_T2b_retrained','line':line,'path':str(path.relative_to(ROOT)).replace('\\','/'),'sha256':digest,'historical_model_text_bytes_exact':comparison['prod_'+line]['bytes_exact'],'same_final_CSV_proven_by_existing_reproduction':True})
    assert found=={'motor','buildings','contents'}
    temporal=[]
    for line in ['motor','buildings','contents']:
        for tag in ['baseline','poison2024']:
            for family in ['N0','F1']:
                namespace='source_original_history' if family=='F1' else 'source'
                for seed in [11,12,13]:
                    recpath=OLD/namespace/line/tag/f'{family}_seed{seed}'/'complete.json';rec=read(recpath)
                    assert sha(ROOT/rec['model'])==rec['model_sha256'] and sha(ROOT/rec['raw'])==rec['raw_sha256']
                    temporal.append({'line':line,'tag':tag,'family':family,'seed':seed,'receipt':str(recpath.relative_to(ROOT)).replace('\\','/'),'receipt_sha256':sha(recpath),'model':rec['model'],'model_sha256':rec['model_sha256'],'raw':rec['raw'],'raw_sha256':rec['raw_sha256'],'arguments_sha256':rec['arguments_sha256']})
    result={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'candidate_sha256':audit['candidate_sha256'],'audit_sha256':sha(OUT/'audit.json'),'production_models':records,'production_model_roles':21,'temporal_models_and_replays':temporal,'temporal_objects':36,
        'interpretation':'Reproduced T2b model text differs from historical model text; do not claim byte-identical learner text across environments. Final CSV is byte-identical by the archived full reproduction. This seal adds object hashes, no model runs or scores.',
        'new_fits':0,'new_inferences':0,'new_submissions':0,'private_superiority_established':False,'code_sha256':sha(Path(__file__))}
    with (OUT/'model_objects_seal.json').open('x',encoding='utf8') as stream:json.dump(result,stream,indent=2)
    print(json.dumps({'production_models_verified':len(records),'temporal_objects_verified':len(temporal),'new_fits':0,'new_inferences':0}))
if __name__=='__main__':main()
