"""Índice sin asuntos ni cuerpos: un título también puede revelar confirmación."""
from pathlib import Path
import json,re,sys

HEADER=re.compile(r'^## ([^|\r\n]+) \| ([A-Z0-9-]+) \| (\d{4}-\d{2}-\d{2}T[0-9:+.-]+) \|',re.M)

def inventory(text):
    return [{'author':m.group(1).strip(),'id':m.group(2),'utc':m.group(3)} for m in HEADER.finditer(text)]

def main():
    root=Path(__file__).resolve().parents[3]
    path=root/'Hackaton/Semana 2/Foro/FORO.md'
    print(json.dumps(inventory(path.read_text(encoding='utf-8-sig'))[-int(sys.argv[1] if len(sys.argv)>1 else 10):],ensure_ascii=True))

if __name__=='__main__':main()
