"""Búsqueda F04 de procedencia: catálogos, nombres y hashes de cuatro alias, sin filas."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F04_2023/f04_20261024_v1'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
    return h.hexdigest()

def content(p):return json.loads(next(x['text'] for x in read(p)['content'] if x['type']=='text'))

def main():
    inv=read(RUN/'official_file_inventory.json');assert not inv['has_more_pages']
    old=read(REPO/'privado/semana2/desarrollo2023/fuentes_nuevas2023_20261024_v1/official_file_inventory.json')['response']
    a={x['name']:x for x in old['files']};b={x['name']:x for x in inv['files']}
    comparison={'old_files':len(a),'current_files':len(b),'names_added':sorted(b.keys()-a.keys()),'names_removed':sorted(a.keys()-b.keys()),'changed_size':[k for k in a.keys()&b.keys() if int(a[k]['total_bytes'])!=int(b[k]['total_bytes'])],'changed_creation_date':[k for k in a.keys()&b.keys() if a[k]['creation_date']!=b[k]['creation_date']]}
    current=content(RUN/'dictionary_response.json')['pages']
    previous=read(ROOT/'Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json')['value']
    previous=json.loads(next(x['text'] for x in previous['content'] if x['type']=='text'))['pages']
    assert current==previous
    local=[]
    for path in [ROOT/'Hackaton/Semana 2/Datos',ROOT/'Hackaton/Semana 2/Datos/emerging']:
        local.append({'directory':rel(path),'method':'direct child names/sizes only; no data read','files':[{'name':p.name,'bytes':p.stat().st_size} for p in sorted(path.iterdir()) if p.is_file()]})
    # The root also contains legacy files. Resolve this distinct candidate ambiguity only,
    # reusing historical baseline hashes, without rehashing active verified originals.
    history=ROOT/'Preparación/artifacts/verification/iaa_launch_20261016/data_manifest.json'
    baseline={Path(x['path']).name:x for x in read(history)['files']}
    aliases=[]
    for name in ['claims.parquet','policies_motor.parquet','policies_buildings.parquet','policies_contents.parquet']:
        p=ROOT/'Hackaton/Semana 2/Datos'/name
        h=digest(p)
        aliases.append({'path':rel(p),'method':'opaque streamed SHA256 only, no Parquet decode','sha256':h,'historical_developed_sha256':baseline[name]['sha256'],'matches_historical_developed':h==baseline[name]['sha256']})
    f03=read(REPO/'privado/semana2/revision_F03_2023/f03_20261024_v1/schema_dictionary_receipt.json')
    claim_schema=next(x for x in f03['schemas'] if x['market']=='emerging' and x['table']=='claims')
    topics=content(RUN/'competition_topics_response.json')
    folder=content(RUN/'data_folder_topic_752091_response.json')['forum_topic']
    host=[{'id':x['id'],'utc':x['post_date'],'author_type':x['author_type'],'author':x['author']['display_name'],'text':x['raw_markdown']} for x in folder['comments'] if x.get('author_type')=='HOST']
    assert any(x['id']==3543802 for x in host)
    result={'id':'S2-F04-FUENTES2023-v1-20261024','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'official_catalog_comparison':comparison,'dictionary_unchanged':True,'local_data_inventories':local,'legacy_root_training_aliases':aliases,'historical_baseline_manifest':rel(history),'claim_schema_reused_from_F03':claim_schema,'claim_schema_newly_read':False,'topics_returned':len(topics.get('topics',[])),'topic_total_count':topics.get('total_count'),'host_data_folder_notice':host,'row_values_decoded':0,'new_active_original_hash_sweep':False,'byte_identity_originals_reused_from':'registro/semana2_contenido_oficial_actual.json','new_claim_movements_located':False,'new_emerging2023_cohort_located':False,'search_absence_is_scoped_not_universal':True}
    with (RUN/'search_evidence.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'catalog':comparison,'root_claim_policy_aliases_developed':[x['matches_historical_developed'] for x in aliases],'host_notice_ids':[x['id'] for x in host],'topics':result['topics_returned'],'dictionary_unchanged':True,'row_values_decoded':0},ensure_ascii=True))

if __name__=='__main__':main()
