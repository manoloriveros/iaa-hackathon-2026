"""Construye y guarda las matrices con variables adicionales por ramo en WORK/feat_<ramo>.parquet."""
import sys, time
from comun import LINES, WORK, build_extra
WORK.mkdir(parents=True, exist_ok=True)
for line in (sys.argv[1:] or LINES):
    t = time.time()
    df = build_extra(line)
    df.to_parquet(WORK / f"feat_{line}.parquet", index=False)
    extra = [c for c in df.columns if c.startswith(("f1x_", "addr_notif")) or c.endswith("_mprev") or c in ("prem_rel", "log_prem_rel")]
    print(line, df.shape, f"{time.time()-t:.0f}s", extra, flush=True)
