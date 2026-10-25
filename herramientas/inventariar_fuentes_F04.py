"""Petición solo de metadatos al catálogo oficial; nunca descarga datos."""
from pathlib import Path
from datetime import datetime,timezone
import json,sys
ROOT=Path(__file__).resolve().parents[3]
RUN=ROOT/'Hackaton/Repositorio_IAA2026/privado/semana2/revision_F04_2023/f04_20261024_v1'
sys.path.insert(0,str(ROOT/'.agents/skills/kaggle'))
from shared import credentials,mcp_client

def main():
    credentials.load_configured_env_file()
    result=mcp_client.request('list_competition_data_files',{'competitionName':'iaa-ai-assisted-hackathon-2026-part-2','pageSize':200},token=mcp_client.resolve_token(),timeout=30)
    assert result.ok,'Catalog request did not succeed; no content downloaded'
    data=result.data;assert isinstance(data,dict) and 'files' in data,'Catalog format unexpected'
    files=[{k:v for k,v in f.items() if k in ['name','total_bytes','creation_date']} for f in data['files']]
    obj={'author':'Codex','utc':datetime.now(timezone.utc).isoformat(),'source':'Kaggle official MCP list_competition_data_files','scope':'Metadata only; no downloads or Parquet row reads','competition':'iaa-ai-assisted-hackathon-2026-part-2','request_page_size':200,'files':files,'has_more_pages':bool(data.get('next_page_token')),'new_fits':0}
    with (RUN/'official_file_inventory.json').open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'files':len(files),'has_more_pages':obj['has_more_pages'],'names':[f['name'] for f in files]},ensure_ascii=True))

if __name__=='__main__':main()
