"""Whitelists de artefactos finales; no ejecuta ni ajusta modelos."""
from pathlib import Path
import json,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as ingress
RUN=REPO/'privado/semana2/modelo_final_g4_2023/final_20261024_v1'
rel=lambda p:p.relative_to(ROOT).as_posix()

def main():
    result=json.loads((RUN/'ready_current.json').read_text(encoding='utf-8'));out=ROOT/result['out']
    plan=json.loads((REPO/'registro/semana2_g4_modelo_final_plan_v1.json').read_text(encoding='utf-8'))
    files=[];branches=[]
    for line in ['motor','buildings','contents']:
        model=out/'models'/(line+'.joblib');quotes=out/'quotes'/(line+'_2025.parquet')
        branches.append({'line':line,'model':rel(model),'quotes':rel(quotes)})
        files.extend([model,quotes])
    files += [ROOT/result['CSV']['path']]+[ROOT/x['path'] for x in plan['frozen_code']]
    files += [REPO/'herramientas/reproducir_csv_final_g4_sin_ajuste.py']
    manifest={'scope':'Exact independent-process disk replay,not refitting or independent professional validation',
        'CSV':result['CSV']['path'],'branches':branches,'files':[{'path':rel(p),'sha256':ingress.sha(p)} for p in files]}
    path=RUN/'replay_manifest.json'
    with path.open('x',encoding='utf-8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'manifest':rel(path),'files':len(files),'models':3,'CSV_rows':result['CSV']['rows']},ensure_ascii=True))

if __name__=='__main__':main()
