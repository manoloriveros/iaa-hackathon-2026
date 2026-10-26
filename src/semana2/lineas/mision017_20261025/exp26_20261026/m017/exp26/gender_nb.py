import numpy as np, pandas as pd
exec(open("f3_eval.py").read().split("K = 300")[0])
for k in ["DEV23_T2b","HOLD24_T2b"]:
    t=sets[k].copy(); f1,f2=f2_fit(t); t["m"]=f2_apply(t,f1,f2); t["m"]=nivel_celda(t,t.m.values)
    t["g"]=col(t,"gender"); t["fy"]=t.exposure>=0.9
    for l in ["motor","contents","buildings"]:
        s=t[t.line==l]
        g=s.groupby(["new_business","g"]).apply(lambda d: pd.Series({"A/E":d.y.sum()/d.m.sum(),"pos":(d.y>0).sum(),"rows":len(d)}),include_groups=False)
        print(k,l); print(g.round(3).unstack(1).to_string())
