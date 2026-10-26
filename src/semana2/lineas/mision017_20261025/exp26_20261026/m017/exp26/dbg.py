exec(open("/home/claude/m017/exp26/ridge_glm.py").read().split("LAMS =")[0])
tr = sets["DEV23_T2b"].copy(); f1, f2 = f2_fit(tr); tr["m"] = nivel_celda(tr, f2_apply(tr, f1, f2))
l = "contents"; trl = tr[tr.line == l]; cats_ = {}; Xa = design(trl, l, allcols); Xa = Xa - Xa.mean()
print(Xa.shape, Xa.isna().sum().sum(), np.abs(Xa.values).max())
for lam in (300, 3000):
    b0, bb = fit_ridge(trl.y.values, trl.m.values, Xa, lam)
    f = np.exp(b0 + Xa.values @ bb)
    print(lam, "b0", b0, "max|b|", np.abs(bb).max(), "f range", f.min(), f.max(), "insample gain", d2u(trl, nivel_celda(trl, trl.m.values * f)) - d2u(trl, trl.m.values))
