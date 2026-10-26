import sys
sys.argv = ["construir_F4b.py"]
src = open("construir_F4b.py").read().split("# --- nivel creíble")[0]
exec(src)
res = {}
for k_ in ["DEV23_T2b", "HOLD24_T2b", "HOLD24_A1", "HOLD24_mezcla"]:
    s_ = sets[k_].copy(); m2 = transformar(s_); w = pesos(s_)
    m3 = factores(s_, forma(s_, m2)); m4 = factores(s_, forma(s_, blend_local(s_, m2)))
    r = {"ALLu": d2u(s_, nivel_celda(s_, m4)) - d2u(s_, nivel_celda(s_, m3)), "w2025": d2w(s_, nivel_celda(s_, m4), w) - d2w(s_, nivel_celda(s_, m3), w)}
    for l in ["motor", "contents"]:
        for seg, sel in (("REN", ~s_.new_business.values.astype(bool)), ("NB", s_.new_business.values.astype(bool))):
            j = (s_.line == l).values & sel; tt = s_[j]
            r[f"{l}_{seg}"] = d2u(tt, nivel_celda(tt, m4[j])) - d2u(tt, nivel_celda(tt, m3[j]))
    res[k_] = {k: round(v, 5) for k, v in r.items()}
print(pd.DataFrame(res).to_string())
