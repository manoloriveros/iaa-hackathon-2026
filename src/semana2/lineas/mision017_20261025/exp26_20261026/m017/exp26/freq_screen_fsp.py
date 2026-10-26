exec(open("/home/claude/m017/exp26/lib26.py").read())
import sys
NS = pd.concat([pd.read_parquet(f"/home/claude/ml2/trabajo/base_emerging_{l}.parquet", columns=["row_id", "n_sin"]) for l in ["motor", "buildings", "contents"]]).set_index("row_id").n_sin
EXCL = {"row_id","policy_id","customer_id","address_id","period_start","period_end","exposure","written_premium","customer_service_contacts",
        "renewal_decision","surname","date_of_birth","customer_since_year","y","line","occupation","new_business","renewal_count"}
allcols = [c for c in list(dict.fromkeys(list(pol.columns) + list(cu.columns) + list(ad.columns))) if c not in EXCL] + ["occ"]
LINE = sys.argv[1]; NPERM = int(sys.argv[2]) if len(sys.argv) > 2 else 50
def bins(v):
    s = pd.Series(v)
    try: sf = s.astype(float); num = True
    except Exception: num = False
    if num and sf.nunique() > 12:
        q = np.unique(np.nanquantile(sf, [0.2, 0.4, 0.6, 0.8])); return np.array([str(x) for x in np.digitize(sf.fillna(-9e9), q)], dtype=object)
    return np.array([str(x) for x in v], dtype=object)
S = {}
for k in ("DEV23_T2b", "HOLD24_T2b"):
    t = sets[k]; t = t[t.line == LINE].copy(); f1, f2 = f2_fit(sets[k]); 
    t["m"] = f2_apply(t, f1, f2) if False else t.m.values
    t["n"] = NS.reindex(t.index).fillna(0).values
    fp = pd.read_parquet(f"/home/claude/ml2/trabajo/pred/fsp/{LINE}.parquet").set_index("row_id").loc[t.index]
    per = [c_[2:] for c_ in fp.columns if c_.startswith("f_")]
    cn = pd.read_parquet(f"/home/claude/ml2/trabajo/conteos_emerging_{LINE}.parquet").set_index("row_id").loc[t.index]
    ef = sum(fp[f"f_{p}"].values * fp[f"cp_{p}"].values * (cn[f"n_{p}"].sum() / (fp[f"f_{p}"] * fp[f"cp_{p}"]).sum()) for p in per)
    c = celda(t); t["mf"] = 0.0
    for cc in np.unique(c): i = c == cc; t.loc[i, "mf"] = ef[i] / ef[i].sum() * t.n.values[i].sum()
    S[k] = t
cust = {k: S[k].customer_id.values for k in S}
def pdev(n, mu): return 2 * np.sum(np.where(n > 0, n * np.log(np.maximum(n, 1e-12) / mu), 0) - (n - mu))
def gain(vtr, vte, tr, te, K=50):
    # factor de frecuencia por nivel con credibilidad tipo Bühlmann en conteos
    d = pd.DataFrame({"v": vtr, "n": tr.n.values, "e": tr.mf.values}).groupby("v").sum()
    f = (d.n + K) / (d.e + K)
    ff = pd.Series(vte).map(f).fillna(1.0).values
    mu = te.mf.values * ff; mu *= te.n.sum() / mu.sum()
    return (pdev(te.n.values, te.mf.values) - pdev(te.n.values, mu)) / pdev(te.n.values, np.full(len(te), te.n.mean()))
rng = np.random.default_rng(11)
rows = []
for cname in allcols:
    try:
        vals = {k: bins(_col(S[k], cname)) for k in S}
    except Exception: continue
    if len(np.unique(vals["DEV23_T2b"])) < 2 or len(np.unique(vals["DEV23_T2b"])) > 80: continue
    g = [gain(vals["DEV23_T2b"], vals["HOLD24_T2b"], S["DEV23_T2b"], S["HOLD24_T2b"]), gain(vals["HOLD24_T2b"], vals["DEV23_T2b"], S["HOLD24_T2b"], S["DEV23_T2b"])]
    real = min(g)
    # nulo: permutar valores entre clientes (valor fijo por cliente entre años)
    allc = np.unique(np.concatenate([cust[k] for k in S]))
    mp = {}
    for k in S:
        for cid, v in zip(cust[k], vals[k]): mp.setdefault(cid, v)
    base_v = np.array([mp[c_] for c_ in allc], dtype=object)
    null = []
    for p in range(NPERM):
        perm = dict(zip(allc, rng.permutation(base_v)))
        v23 = np.array([perm[c_] for c_ in cust["DEV23_T2b"]], dtype=object); v24 = np.array([perm[c_] for c_ in cust["HOLD24_T2b"]], dtype=object)
        null.append(min(gain(v23, v24, S["DEV23_T2b"], S["HOLD24_T2b"]), gain(v24, v23, S["HOLD24_T2b"], S["DEV23_T2b"])))
    null = np.array(null)
    rows.append(dict(var=cname, lev=len(np.unique(vals["DEV23_T2b"])), g23_24=g[0], g24_23=g[1], mn=real, null95=np.quantile(null, 0.95), p=(1 + (null >= real).sum()) / (1 + len(null))))
    print(rows[-1], flush=True)
r = pd.DataFrame(rows).sort_values("p"); r.to_csv(f"exp26/freq_screen_fsp_{LINE}.csv", index=False)
print(r.round(5).to_string())
