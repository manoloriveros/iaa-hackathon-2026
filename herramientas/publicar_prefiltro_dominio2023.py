"""Foro propio de diagnóstico de atributos; escritor común y recibos exclusivos."""
from pathlib import Path
import sys,json,subprocess,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/prefiltro_dominio2023_v3'
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('kind',choices=['prior','result']);p.add_argument('--subject',required=True);p.add_argument('--body',type=Path,required=True);a=p.parse_args();receipt=OUT/f'forum_{a.kind}_receipt.json';assert not receipt.exists();ident='COD-S2-20261025-DOMINIO-'+('PREVIO' if a.kind=='prior' else 'RESULTADO')+'-V3'
 result=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',ident,'--asunto',a.subject,'--cuerpo',str(a.body)],capture_output=True,text=True,encoding='utf8',check=True);data=json.loads(result.stdout)
 with receipt.open('x',encoding='utf8') as h:json.dump(data,h,ensure_ascii=False,indent=2)
 print(json.dumps(data))
