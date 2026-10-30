"""Fit a CPU PyTorch MLP with embeddings and power-1.5 Tweedie loss.

log(mu)=network(x)+log(effective exposure)+base. Fit numeric quantile-to-normal
transforms within training folds and add missingness indicators. Use categorical
embeddings, the 15,000 motor cap/uniform surcharge and motor F3 contract. A zero
final layer initializes predictions at the line mean rate. Stop V23 on calibration,
compare on selection, reuse its epoch count for V24/production and average seeds.
Usage: python mlp_tweedie.py <name> <line> [--semillas=3] [--v24] [--prod]
       [--ancho=128] [--drop=0.1] [--lr=0.001]
"""
from __future__ import annotations

import json
import sys
import time

import numpy as np
import pandas as pd
import torch
from sklearn.preprocessing import QuantileTransformer
from torch import nn

from comun import WORK, d2, to_model_frame
from experimentos import features, load

torch.set_num_threads(2)
CAPS = {"motor": 15000.0}


def prep(X: pd.DataFrame, fit_mask: np.ndarray):
    cats = [c for c in X.columns if isinstance(X[c].dtype, pd.CategoricalDtype)]
    nums = [c for c in X.columns if c not in cats]
    num = X[nums].astype("float64").values
    miss = np.isnan(num)
    med = np.nanmedian(num[fit_mask], axis=0)
    med = np.where(np.isnan(med), 0.0, med)
    num = np.where(miss, med, num)
    qt = QuantileTransformer(n_quantiles=200, output_distribution="normal", subsample=200000, random_state=0)
    qt.fit(num[fit_mask])
    num = qt.transform(num).astype("float32")
    keep_miss = miss[fit_mask].mean(axis=0) > 0.001
    num = np.concatenate([num, miss[:, keep_miss].astype("float32")], axis=1)
    codes = np.stack([X[c].cat.codes.values.astype("int64") + 1 for c in cats], axis=1) if cats else np.zeros((len(X), 0), "int64")
    cards = [len(X[c].cat.categories) + 1 for c in cats]
    for j in range(len(cats)):
        # Missing or rare training categories (<30 rows) map to unknown index 0.
        cnt = np.bincount(codes[fit_mask, j], minlength=cards[j])
        codes[:, j] = np.where(cnt[codes[:, j]] < 30, 0, codes[:, j])
    return num, codes, cards


class Net(nn.Module):
    def __init__(self, n_num, cards, width=128, drop=0.1):
        super().__init__()
        dims = [min(12, int(np.ceil(c ** 0.5)) + 1) for c in cards]
        self.embs = nn.ModuleList([nn.Embedding(c, d) for c, d in zip(cards, dims)])
        d_in = n_num + sum(dims)
        self.mlp = nn.Sequential(nn.Linear(d_in, width), nn.SiLU(), nn.Dropout(drop), nn.Linear(width, width // 2), nn.SiLU(),
                                 nn.Dropout(drop), nn.Linear(width // 2, 1))
        nn.init.zeros_(self.mlp[-1].weight)
        nn.init.zeros_(self.mlp[-1].bias)

    def forward(self, xn, xc):
        parts = [xn] + [e(xc[:, i]) for i, e in enumerate(self.embs)]
        return self.mlp(torch.cat(parts, dim=1)).squeeze(1)


def tweedie_loss(eta, y):
    # Power-1.5 Tweedie deviance up to constants: 2*y*exp(-eta/2) + 2*exp(eta/2).
    return (2.0 * y * torch.exp(-0.5 * eta) + 2.0 * torch.exp(0.5 * eta)).mean()


def train(num, codes, cards, y, logoff, idx_tr, idx_cal=None, epochs=40, seed=0, width=128, drop=0.1, lr=1e-3, bs=2048, patience=4, wd=1e-5):
    torch.manual_seed(seed)
    rng = np.random.default_rng(seed)
    net = Net(num.shape[1], cards, width, drop)
    opt = torch.optim.AdamW(net.parameters(), lr=lr, weight_decay=wd)
    xn = torch.from_numpy(num); xc = torch.from_numpy(codes)
    yt = torch.from_numpy(y.astype("float32")); lo = torch.from_numpy(logoff.astype("float32"))
    best, best_ep, best_state, bad = np.inf, 0, None, 0
    for ep in range(epochs):
        net.train()
        perm = rng.permutation(idx_tr)
        for s in range(0, len(perm), bs):
            b = torch.from_numpy(perm[s:s + bs])
            eta = net(xn[b], xc[b]) + lo[b]
            loss = tweedie_loss(eta, yt[b])
            opt.zero_grad(); loss.backward(); opt.step()
        if idx_cal is not None:
            net.eval()
            with torch.no_grad():
                b = torch.from_numpy(idx_cal)
                vl = float(tweedie_loss(net(xn[b], xc[b]) + lo[b], yt[b]))
            if vl < best - 1e-7:
                best, best_ep, bad = vl, ep + 1, 0
                best_state = {k: v.clone() for k, v in net.state_dict().items()}
            else:
                bad += 1
                if bad >= patience:
                    break
    if best_state is not None:
        net.load_state_dict(best_state)
    return net, best_ep


def predict(net, num, codes, logoff, idx):
    net.eval()
    out = []
    with torch.no_grad():
        for s in range(0, len(idx), 65536):
            b = torch.from_numpy(idx[s:s + 65536])
            out.append((net(torch.from_numpy(num)[b], torch.from_numpy(codes)[b]) + torch.from_numpy(logoff.astype("float32"))[b]).numpy())
    return np.exp(np.concatenate(out).astype("float64"))


def main():
    name, line = sys.argv[1], sys.argv[2]
    opts = dict((a[2:].split("=") + ["1"])[:2] for a in sys.argv[3:] if a.startswith("--"))
    seeds = int(opts.get("semillas", 3)); width = int(opts.get("ancho", 128)); drop = float(opts.get("drop", 0.1)); lr = float(opts.get("lr", 1e-3))
    bs = int(opts.get("bs", 2048)); pat = int(opts.get("pac", 4)); wd = float(opts.get("wd", 1e-5))
    t0 = time.time()
    df = load(line)
    feats = features(line, df, "F01234" if line == "motor" else "F0124")
    if line != "motor" and "f3s2" in opts:
        # Seven approved household customer F3 features (D80).
        feats += [c for c in ["prior_claims_5y", "credit_band", "missed_payments_12m", "household_size", "years_at_address", "marital_status", "licence_points"] if c in df.columns]
    X = to_model_frame(df, feats)
    y = df["T0"].fillna(0).values
    off = df["e_ef_coste"].values
    expo = df["exposure"].values
    yr = df.year.values
    cap = CAPS.get(line)
    out = WORK / name
    out.mkdir(parents=True, exist_ok=True)
    rep = {"line": line, "seeds": seeds, "width": width, "drop": drop, "lr": lr, "bs": bs, "wd": wd, "f3s2": "f3s2" in opts}

    def fold(tr_mask, ev_mask, cal_mask, ev_off, epochs_fixed=None):
        num, codes, cards = prep(X, tr_mask)
        yt = np.minimum(y, cap) if cap else y.copy()
        loading = y[tr_mask].sum() / yt[tr_mask].sum() if cap else 1.0
        base = float(np.log(yt[tr_mask].sum() / off[tr_mask].sum()))
        logoff = np.log(np.where(ev_mask, ev_off, off)) + base
        idx_tr = np.flatnonzero(tr_mask); idx_ev = np.flatnonzero(ev_mask)
        idx_cal = np.flatnonzero(cal_mask) if cal_mask is not None else None
        mu = np.zeros(len(idx_ev)); eps = []
        for s in range(seeds):
            net, be = train(num, codes, cards, yt, logoff, idx_tr, idx_cal, epochs=(80 if epochs_fixed is None else epochs_fixed), seed=20261017 + s,
                            width=width, drop=drop, lr=lr, bs=bs, patience=(pat if epochs_fixed is None else 10 ** 6), wd=wd)
            eps.append(be if epochs_fixed is None else epochs_fixed)
            mu += predict(net, num, codes, logoff, idx_ev) * loading / seeds
            print(name, "semilla", s, "épocas", eps[-1], round(time.time() - t0), flush=True)
        return mu, eps

    tr = yr <= 2022; cal = (yr == 2023) & (df.cal_half.values == 0); sel = (yr == 2023) & (df.cal_half.values == 1)
    mu, eps = fold(tr, sel, cal, off)
    ep_fix = int(round(np.mean(eps)))
    rep["epocas_v23"] = eps
    rep["d2_sel"] = round(d2(y[sel], mu), 5)
    print(name, json.dumps(rep), flush=True)
    pd.DataFrame({"row_id": df.row_id[sel].astype(str).values, "line": line, "y": y[sel], "mu": mu}).to_parquet(WORK / f"sel_{name}.parquet", index=False)
    if "v24" in opts:
        ev = yr == 2024
        mu24, _ = fold(yr <= 2023, ev, None, off, epochs_fixed=ep_fix)
        rep["d2_v24"] = round(d2(y[ev], mu24), 5)
        pd.DataFrame({"row_id": df.row_id[ev].astype(str).values, "line": line, "y": y[ev], "mu": mu24}).to_parquet(out / "v24.parquet", index=False)
        print(name, json.dumps(rep), flush=True)
    if "prod" in opts:
        te = yr == 2025
        mu25, _ = fold(yr <= 2024, te, None, expo, epochs_fixed=ep_fix)
        rep["pred_2025_total_CU"] = round(float(mu25.sum()), 2)
        pd.DataFrame({"row_id": df.row_id[te].astype(str).values, "line": line, "prediction": mu25}).to_parquet(out / "prediccion_2025.parquet", index=False)
    rep["secs"] = round(time.time() - t0)
    (out / "resumen.json").write_text(json.dumps(rep, indent=1))
    print(name, json.dumps(rep), flush=True)


if __name__ == "__main__":
    main()
