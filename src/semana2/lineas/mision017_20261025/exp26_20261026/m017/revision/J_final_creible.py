"""J, tarea 4: reconstrucción propia de final_creible_2025.csv (construir_final.py, modo creíble) para comparar con F3."""
import sys, json, numpy as np, pandas as pd
sys.path.insert(0, "/home/claude/m017/revision")
from J_lib import *

fin = json.load(open(R + "final_salida.txt"))
g = PRE["base"]["g"]
ser = series()
pool = pd.concat([ser["DEV23_T2b"], ser["HOLD24_T2b"]])
T2 = TransfF2(pool)
ser2 = {}
for k, s in ser.items():
    s2 = s.copy(); s2["m"] = T2(s, s.m.values); ser2[k] = s2
F2 = leer_pred(R + "F2_ncb_previos_2025.csv"); t = test_df(F2.row_id.values); c = celda(t)
m = F2.prediction.values.copy(); res = {"a": {}, "razon": {}}
for cc in ["motor_1", "buildings_1", "contents_1"]:
    a = fin["forma"][cc]["a_cred"]
    rs = []
    for k, s in ser2.items():
        cs = celda(s); j = cs == cc; mm = forma(s, s.m.values, cc, a)
        rs.append(kopt(s.y.values[j], mm[j]) / kopt(s.y.values[j], s.m.values[j]))
    r = float(np.mean(rs)); res["a"][cc] = a; res["razon"][cc] = r
    res.setdefault("razon_dif_autor", {})[cc] = r - fin["forma"][cc]["razon_cred"]
    m2 = forma(t, m, cc, a); i = c == cc; m[i] = m2[i] * r
cred = {s: fin["nivel"]["cred"][s] for s in CELS}
for cc in CELS: m[c == cc] *= cred[cc] / g
out = F2.copy(); out["prediction"] = m
p = R + "revision/J_final_creible_2025.csv"; out.to_csv(p, index=False, float_format="%.6f", lineterminator="\n")
res["sha256"] = sha(p); res["sha_autor"] = fin["final_creible_2025.csv"]["sha256"]; res["igual"] = res["sha256"] == res["sha_autor"]
res["total"] = float(m.sum()); res["total_autor"] = fin["final_creible_2025.csv"]["total"]
json.dump(res, open(R + "revision/J_final_creible.json", "w"), indent=1, ensure_ascii=False)
print(json.dumps(res, indent=1, ensure_ascii=False))
