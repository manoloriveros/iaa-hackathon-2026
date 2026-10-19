"""Copia los artefactos guardados necesarios para S30/S22 a la carpeta común.

No estima ni entrena; exige bytes exactos antes y después de cada copia.
Los archivos restringidos se guardan bajo privado/, excluido de Git.
"""
import argparse
import hashlib
import json
import shutil
from datetime import datetime, timezone
from pathlib import Path
from inventario import localizar

REPO = Path(__file__).resolve().parents[1]


def sha(p):
    h = hashlib.sha256()
    with p.open("rb") as f:
        for b in iter(lambda:f.read(1024*1024),b""):
            h.update(b)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--semana1",type=Path,required=True)
    args=ap.parse_args()
    s=args.semana1.resolve()
    dst=REPO/"privado/artefactos_s30_s22"
    recipe=json.loads((REPO/"receta/receta.json").read_text(encoding="utf-8"))
    expected=json.loads((REPO/"receta/huellas_esperadas.json").read_text(encoding="utf-8"))
    nodes={n["id"]:n for n in recipe["nodos"]}
    direct=sorted({n for t in recipe["objetivos"].values() for n in nodes[t["nodo"]]["requiere"]})
    refs=sorted({r for n in direct for r in nodes[n]["verificar"] if r.endswith(".parquet")})
    sources=[s/"Modelos_claude",s/"Modelos_claude_b"]
    todo=[]
    for rel in refs:
        p=localizar(rel,sources)
        if p is None:
            raise FileNotFoundError(rel)
        todo.append((rel,p,expected["salidas"][rel]["sha256"]))
    for line in ("motor","buildings","contents"):
        rel=f"insumos/exposicion_{line}.parquet"
        p=s/"Modelos_claude"/rel
        todo.append((rel,p,expected["mezcla"][rel]["sha256"]))
    rel="Datos/sample_submission.parquet"
    todo.append((rel,s/rel,expected["entradas"][rel]["sha256"]))
    # Revisión completa antes de la primera copia.
    for rel,p,h in todo:
        if sha(p)!=h:
            raise ValueError(f"Origen no conforme: {p}")
        out=dst/rel
        if out.exists() and sha(out)!=h:
            raise ValueError(f"Copia privada alterada: {out}; revisar sin sobrescribir")
    filas=[]
    for rel,p,h in todo:
        out=dst/rel
        out.parent.mkdir(parents=True,exist_ok=True)
        if not out.exists():
            shutil.copyfile(p,out)
        if sha(out)!=h:
            raise ValueError(f"Copia no conforme: {rel}")
        filas.append({"ruta_privada":rel,"origen_historico":str(p.relative_to(s)),"sha256":h,"bytes":out.stat().st_size})
    manifest={"utc":datetime.now(timezone.utc).isoformat(),"carpeta":"privado/artefactos_s30_s22","archivos":filas,
              "cantidad":len(filas),"bytes":sum(f["bytes"] for f in filas),"estimaciones_nuevas":0,"modelos_entrenados":0,
              "nota":"Predicciones de componentes guardadas, no checkpoints de reentrenamiento completo. Datos originales compartidos permanecen en Semana 1/Datos."}
    for p in (dst/"manifest.json",REPO/"registro/artefactos_mezcla.json"):
        p.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:manifest[k] for k in ("cantidad","bytes","carpeta","estimaciones_nuevas")},ensure_ascii=False))


if __name__=="__main__":
    main()
