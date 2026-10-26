import numpy as np, pandas as pd
exec(open("f3_eval.py").read().split("K = 300")[0])
for k in ["DEV23_T2b","HOLD24_T2b"]:
    t=sets[k].copy(); t["m"]=nivel_celda(t,t.m.values)
    t["rid"]=t.index.str[1:].astype(int)
    t["pid"]=pd.Series(col(t,"policy_id"),index=t.index).str.extract(r"(\d+)")[0].astype(float).values
    t["cid"]=pd.to_numeric(t.customer_id,errors="coerce")
    t["aid"]=pd.Series(col(t,"address_id"),index=t.index).str.extract(r"(\d+)")[0].astype(float).values
    for l in ["motor","buildings","contents"]:
        s=t[t.line==l]
        out=[]
        for v in ["rid","pid","cid","aid"]:
            q=pd.qcut(s[v].rank(method="first"),5,labels=False)
            ae=(s.y.groupby(q).sum()/s.m.groupby(q).sum()).round(2).tolist()
            out.append(f"{v}:{ae}")
        print(k,l," | ".join(out))
