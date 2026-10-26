"""Comparación de consultas públicas nuevas con las fuentes archivadas propias."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');BASE=R/'privado/semana2/robustez2023/mision017_20261025_v1';OUT=BASE/'public_refresh3';p=OUT/'comparison_receipt.json';assert not p.exists()
def read(p):return json.loads(p.read_text(encoding='utf-8-sig'))
def unwrap(v):
 if v.get('status')=='fulfilled':v=v['value']
 assert not v.get('isError');return json.loads(next(x['text'] for x in v['content'] if x['type']=='text'))
topics=unwrap(read(OUT/'observation_topics.json'));oldtopics=unwrap(read(BASE/'public_refresh/live_0.json'));dictionary=unwrap(read(OUT/'observation_dictionary.json'));evaluation=unwrap(read(OUT/'observation_evaluation.json'));content=dictionary['pages'][0]['content'];digest=hashlib.sha256(content.encode()).hexdigest();previous=read(BASE/'public_refresh/comparison_receipt.json')['live_data_description_sha256']
report={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source':'KaggleMCP public competition topics Recent page1,evaluation,data-description','topics_and_comment_metadata_unchanged':topics==oldtopics,'topic_count':topics['total_count'],'dictionary_current_sha256':digest,'dictionary_previous_sha256':previous,'dictionary_semantically_unchanged':digest==previous,'evaluation_content_sha256':hashlib.sha256(evaluation['pages'][0]['content'].encode()).hexdigest(),'new_temporal_climate_admission':False,'no_new_training_source_or_C0_or_price_score':True,'new_fits':0,'raw_observations_retained_as_read_receipts_not_new_document_editions':True}
assert report['topics_and_comment_metadata_unchanged'] and report['dictionary_semantically_unchanged']
with p.open('x',encoding='utf-8') as h:json.dump(report,h,ensure_ascii=False,indent=2)
print(json.dumps(report))
