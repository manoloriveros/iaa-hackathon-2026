"""Añadir un aporte propio con recibo; no lee ni muestra cuerpos ajenos."""
from pathlib import Path
import argparse,json,subprocess,sys
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('cycle',type=int);p.add_argument('kind',choices=['prior','result','correction']);p.add_argument('--subject',required=True);p.add_argument('--body',type=Path,required=True);a=p.parse_args();out=R/f'privado/semana2/robustez2023/ciclo{a.cycle}_20261025_v1';receipt=out/f'forum_{a.kind}_receipt.json';assert not receipt.exists();suffix={'prior':'PREVIO','result':'RESULTADO','correction':'CORRECCION'}[a.kind];ident=f'COD-S2-20261025-ROBUSTEZ{a.cycle}-{suffix}'
 r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',ident,'--asunto',a.subject,'--cuerpo',str(a.body)],check=True,capture_output=True,text=True,encoding='utf-8');obj=json.loads(r.stdout)
 with receipt.open('x',encoding='utf-8') as h:json.dump(obj,h,ensure_ascii=False,indent=2)
 print(json.dumps(obj))
