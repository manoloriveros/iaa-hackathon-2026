"""Añadir aportes propios de la comparación pública con el bloqueo común del foro."""
from pathlib import Path
import sys,json,subprocess,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['prior','ready','result']);p.add_argument('--subject',required=True);p.add_argument('--body',type=Path,required=True);a=p.parse_args();receipt=OUT/f'forum_{a.kind}_receipt.json';assert not receipt.exists();ident='COD-S2-20261025-HOGAR-PUBLICO-'+{'prior':'PREVIO','ready':'LISTO','result':'RESULTADO'}[a.kind]
 r=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',ident,'--asunto',a.subject,'--cuerpo',str(a.body)],check=True,capture_output=True,text=True,encoding='utf-8');data=json.loads(r.stdout)
 with receipt.open('x',encoding='utf-8') as h:json.dump(data,h,ensure_ascii=False,indent=2)
 print(json.dumps(data))
