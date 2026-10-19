"""Registra código de proceso real y comparación de la mezcla congelada, sin ajuste.
Se reanuda la carpeta ya producida; no reconstruye componentes.
"""
import hashlib
import json
import os
import platform
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
import numpy as np
import pandas as pd

REPO=Path(__file__).resolve().parents[1]
ROOT=REPO.parents[1]
WORK=REPO/"privado/replay_windows_v12_lf"
EVID=REPO/"docs/evidencia"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def main():
    cmd=[sys.executable,str(REPO/"reproducir.py"),"mezcla","--semana1=privado/artefactos_s30_s22", "--artefactos=privado/artefactos_s30_s22",
         "--trabajo=privado/replay_windows_v12_lf","--continuar-si-difiere"]
    run=subprocess.run(cmd,cwd=REPO,env=dict(os.environ,PYTHONUTF8="1"),capture_output=True,text=True,encoding="utf-8",errors="replace")
    EVID.mkdir(parents=True,exist_ok=True)
    (EVID/"replay_windows.stdout.txt").write_text(run.stdout,encoding="utf-8")
    (EVID/"replay_windows.stderr.txt").write_text(run.stderr,encoding="utf-8")
    last=json.loads((WORK/"registro.jsonl").read_text(encoding="utf-8").splitlines()[-1])
    dif=[]
    for name,folder in (("S30","Modelos_claude_b/runs/S30_claude_b"),("S22","Modelos_claude/runs/S22_claude_propio")):
        orig=ROOT/"Hackaton/Semana 1"/folder/"prediccion_2025.parquet"
        new=WORK/"work"/Path(folder).name/"prediccion_2025.parquet"
        a,b=pd.read_parquet(orig),pd.read_parquet(new)
        for c in a.select_dtypes(include="number").columns:
            x,y=a[c].to_numpy(float),b[c].to_numpy(float)
            delta=np.abs(x-y)
            dif.append({"candidato":name,"columna":c,"filas":len(x),"diferentes":int(np.sum(delta!=0)),
                        "max_abs":float(np.max(delta)),"max_rel":float(np.max(delta/np.maximum(np.abs(x),1e-300)))})
    result={"utc":datetime.now(timezone.utc).isoformat(),"estado":last["estado"],"codigo_salida":run.returncode,
            "csv_exactos":all(x["coincide"] for x in last["objetivos"].values()),"objetivos":last["objetivos"],
            "diferencias_intermedias":dif,"recibo_completo":last,"python":platform.python_version(),"numpy":np.__version__,"pandas":pd.__version__,
            "codigo_sha256":sha(REPO/"reproducir.py"),"wrapper_LF_sha256":sha(REPO/"herramientas/ejecutar_csv_lf.py"),
            "alcance":"Reanudación y cotejo de mezcla real desde componentes guardados en carpeta común; no entrenamiento completo. Código de subprocess, no del envoltorio PowerShell."}
    (EVID/"replay_windows.json").write_text(json.dumps(result,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:result[k] for k in ("codigo_salida","csv_exactos","estado","diferencias_intermedias")},ensure_ascii=False))
    raise SystemExit(0 if run.returncode==3 and result["csv_exactos"] else 1)


if __name__=="__main__":
    main()
