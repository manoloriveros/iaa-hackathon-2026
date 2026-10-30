import numpy as np, pandas as pd, json
exec(open("forma_local.py").read().split("A = np.round")[0].replace('print(k, len(t)', '0 and print(k, len(t)'))
te = b[b.conjunto == "test"].copy(); te["cel"] = te.line + "_" + te.new_business.astype(int).astype(str); n25 = te.cel.value_counts(normalize=True)
# 2024 proxy: average A1 and T2b after matching each line's prediction total.
h = sets["HOLD24_T2b"].copy(); a1 = sets["HOLD24_A1"].m.reindex(h.index)
tot = h.groupby("line").m.transform("sum") / a1.groupby(h.line).transform("sum")
h["m"] = 0.5 * h.m + 0.5 * a1 * tot; sets["HOLD24_mezcla"] = h
def aplicar(t, acel):
    t = t.copy(); t["cel"] = t.line + "_" + t.new_business.astype(int).astype(str); out = t.m.values.copy()
    for c, a in acel.items():
        i = (t.cel == c).values; e = t.exposure.values[i] * t.c_fila.values[i]; r = t.m.values[i] / e; gm = t.m.values[i].sum() / e.sum()
        mm = e * gm * (r / gm) ** a; out[i] = mm * t.m.values[i].sum() / mm.sum()
    return out
def d2w(t, m, w):
    y = t.y.values; return 1 - (dev(y, m) * w).sum() / (dev(y, np.full(len(y), y.mean())) * w).sum()
REGLA = {"motor_1": 0.5, "motor_0": 0.85}
out = {}
for k, t in sets.items():
    if k == "HOLD24_R0": continue
    cel = t.line + "_" + t.new_business.astype(int).astype(str); n = cel.value_counts(normalize=True); w = cel.map(n25 / n).values
    # Match both predictions to their cell-optimal levels to inspect shape alone.
    def nivel(m):
        m = m.copy()
        for c in cel.unique():
            i = (cel == c).values; m[i] = m[i] * kopt(t.y.values[i], m[i])
        return m
    m0 = nivel(t.m.values); m1 = nivel(aplicar(t, REGLA))
    out[k] = {"D2_base_comp2025": round(d2w(t, m0, w), 5), "D2_forma_comp2025": round(d2w(t, m1, w), 5),
              "ganancia_comp2025": round(d2w(t, m1, w) - d2w(t, m0, w), 5),
              "ganancia_comp_propia": round(d2w(t, m1, np.ones(len(t))) - d2w(t, m0, np.ones(len(t))), 5)}
print(json.dumps(out, indent=1))
# Inspect observed/expected by motor NCB and business status using 2023-2024 T2b.
pm = pd.concat([pd.read_parquet(f"datos/emerging/policies_motor.parquet", columns=["row_id", "ncb_years", "years_licensed", "driver_age_band"])]).set_index("row_id")
t = pd.concat([sets["DEV23_T2b"], sets["HOLD24_T2b"]]); t = t[t.line == "motor"].join(pm)
t["ncb"] = pd.cut(t.ncb_years, [-1, 0, 2, 5, 9, 99], labels=["0", "1-2", "3-5", "6-9", "10+"])
t["dec"] = t.groupby("new_business").m.transform(lambda s: pd.qcut(s / t.loc[s.index, "exposure"], 5, labels=False))
for nb in (False, True):
    g = t[t.new_business == nb]; k = g.y.sum() / g.m.sum()
    print("NB" if nb else "REN", "A/E por quintil de tasa predicha:", (g.groupby("dec").y.sum() / g.groupby("dec").m.sum() / k).round(2).tolist())
    print("   A/E por NCB:", (g.groupby("ncb", observed=True).y.sum() / g.groupby("ncb", observed=True).m.sum() / k).round(2).to_dict(), g.groupby("ncb", observed=True).size().to_dict())
