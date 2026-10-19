"""Verifica expediente, enlaces, huellas del paquete y exclusión de datos en Git."""
import hashlib
import json
import re
import subprocess
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

REPO=Path(__file__).resolve().parents[1]


def leer(p):return json.loads(p.read_text(encoding="utf-8"))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


class Links(HTMLParser):
    def __init__(self):super().__init__();self.hrefs=[];self.ids=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if "id" in a:self.ids.append(a["id"])
        if tag=="a" and "href" in a:self.hrefs.append(a["href"])


def main():
    checks=[]
    def ck(nombre,ok,detalle=None):checks.append({"control":nombre,"pasa":bool(ok),"detalle":detalle})
    d=leer(REPO/"registro/panel_datos.json")
    parser=Links();parser.feed((REPO/"docs/panel_revision.html").read_text(encoding="utf-8"))
    ck("IDs HTML únicos",len(parser.ids)==len(set(parser.ids)))
    hrefs=parser.hrefs+[x["evidencia"].removeprefix("docs/") if x["evidencia"].startswith("docs/") else "../"+x["evidencia"] for x in leer(REPO/"registro/requisitos.json")["requisitos"]]
    for x in d["validaciones"]:
        hrefs.append(x["fuente"].removeprefix("docs/") if x["fuente"].startswith("docs/") else "../"+x["fuente"])
    for href in sorted(set(hrefs)):
        u=urlsplit(href)
        if u.scheme:continue
        if not u.path:
            ck("Ancla "+href,u.fragment in parser.ids)
        else:
            ck("Enlace "+href,(REPO/"docs"/unquote(u.path)).resolve().is_file())
    pack=leer(REPO/"receta/codigo.json")["paquete"]
    for name,v in pack["archivos"].items():ck("SHA paquete "+name,sha(REPO/name)==v["sha256"])
    suite=leer(REPO/"docs/controles/20261019_windows_v12_lf/resultado.json")
    ck("45 casos finales del código actual",suite["todos_pasan"] and suite["pasan"]==45 and suite["etapas_reales_invocadas"]==0)
    ck("SHA orquestador probado",suite["paquete"]["reproducir.py"]==sha(REPO/"reproducir.py"))
    ck("44 fuentes de modelo sin cambio",leer(REPO/"registro/integridad_codigo_modelo.json")["coinciden"]==44)
    replay=leer(REPO/"docs/evidencia/replay_windows.json")
    ck("Replay: CSV exactos y código 3",replay["csv_exactos"] and replay["codigo_salida"]==3)
    ck("Replay usa orquestador actual",replay["codigo_sha256"]==sha(REPO/"reproducir.py"))
    ck("Replay usa escritor LF actual",replay["wrapper_LF_sha256"]==sha(REPO/"herramientas/ejecutar_csv_lf.py"))
    ck("Dos CSV pasan preflight",all(x["pasa"] for x in d["preflight"]) and len(d["preflight"])==2)
    ck("Once originales íntegros",all(x["coincide"] for x in d["tablas"]) and len(d["tablas"])==11)
    ck("Diccionario 107",len(d["diccionario"])==107)
    ck("Sin aprobación humana inventada",leer(REPO/"registro/revision_humana.json")["estado"]=="pendiente")
    pdf=leer(REPO/"registro/verificacion_pdf.json")
    ck("Informe dentro del límite de cinco páginas",1 <= pdf["paginas"] <= 5)
    ck("PDF corresponde al informe actual",pdf["fuente_sha256"]==sha(REPO/"docs/INFORME_SEMANA1.md") and pdf["pdf_sha256"]==sha(REPO/"docs/informe_semana1.pdf"))
    tracked=subprocess.check_output(["git","ls-files","-z","--cached"],cwd=REPO).decode("utf-8").split("\0")
    secret_patterns=[r"gh[pousr]_[A-Za-z0-9]{30,}",r"github_pat_[A-Za-z0-9_]{30,}",r"sk-[A-Za-z0-9_-]{24,}",r"AKIA[0-9A-Z]{16}",r"-----BEGIN (?:RSA |OPENSSH )?PRIVATE KEY-----"]
    forbidden=[];secrets=[]
    for rel in filter(None,tracked):
        p=REPO/rel
        if rel.startswith("privado/") or p.suffix.lower() in {".parquet",".csv",".npy",".npz",".pkl",".joblib",".cbm",".pt",".pth",".pem",".key"} or p.name.startswith(".env"):
            forbidden.append(rel)
        if p.is_file() and p.suffix in {".json",".md",".py",".html",".txt",".log",".jsonl"}:
            text=p.read_text(encoding="utf-8",errors="replace")
            if any(re.search(pat,text) for pat in secret_patterns):secrets.append(rel)
    ck("Git sin archivos de datos o checkpoints",not forbidden,forbidden)
    ck("Git sin patrones de credenciales",not secrets,secrets)
    copied_ids=[]
    for p in (REPO/"docs/evidencia").glob("*.md"):
        if re.search(r"\b[MCBPA]\d{7,12}\b",p.read_text(encoding="utf-8")):copied_ids.append(p.name)
    ck("Copias documentales sin identificadores de filas",not copied_ids,copied_ids)
    status={"utc":datetime.now(timezone.utc).isoformat(),"controles":len(checks),"pasan":sum(x["pasa"] for x in checks),"fallan":[x for x in checks if not x["pasa"]],"resultados":checks,
            "alcance":"Expediente de preparación; no afirma cierre del concurso, revisión humana ni reentrenamiento completo.","archivos_git_revisados":len(list(filter(None,tracked)))}
    (REPO/"registro/verificacion_expediente.json").write_text(json.dumps(status,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:status[k] for k in ("controles","pasan","fallan","archivos_git_revisados")},ensure_ascii=False))
    raise SystemExit(0 if not status["fallan"] else 1)


if __name__=="__main__":main()
