"""Build the first, explicitly incomplete, standalone notebook drafts."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'notebooks'
OUT.mkdir(exist_ok=True)

def md(source):
    return {'cell_type': 'markdown', 'metadata': {}, 'source': source.splitlines(True)}

def code(source):
    return {'cell_type': 'code', 'execution_count': None, 'metadata': {}, 'outputs': [], 'source': source.splitlines(True)}

common_imports = '''import os, sys, hashlib, importlib.metadata
from pathlib import Path
import numpy as np
import pandas as pd
import pyarrow.parquet as pq

for package in ("numpy", "pandas", "pyarrow"):
    print(f"{package}: {importlib.metadata.version(package)}")
print("Python:", sys.version)
'''

helpers = '''LINES = ("motor", "buildings", "contents")
BASE_FILES = ["addresses.parquet", "claims.parquet", "customers.parquet",
              "weather.parquet", "sample_submission.parquet"] + [
    f"{prefix}_{line}.parquet" for prefix in ("policies", "test") for line in LINES]

def find_market(market, required, override):
    if override:
        candidates = [Path(override)]
    else:
        candidates = [p for p in Path("/kaggle/input").rglob(market) if p.is_dir()]
    candidates = [p for p in candidates if all((p / name).is_file() for name in required)]
    if len(candidates) != 1:
        raise RuntimeError(f"Expected exactly one {market} folder with the required files; "
                           f"found {candidates}. Set the override above explicitly.")
    return candidates[0]

def inventory(folder, filenames):
    rows = []
    for name in filenames:
        path = folder / name
        pf = pq.ParquetFile(path)
        digest = hashlib.sha256()
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
        rows.append({"file": name, "rows": pf.metadata.num_rows,
                     "columns": len(pf.schema_arrow), "bytes": path.stat().st_size,
                     "sha256": digest.hexdigest()})
    return pd.DataFrame(rows)

def check_template(folder):
    sample = pd.read_parquet(folder / "sample_submission.parquet")
    test = pd.concat([pd.read_parquet(folder / f"test_{line}.parquet", columns=["row_id"])
                      for line in LINES], ignore_index=True)
    assert "row_id" in sample.columns and sample.row_id.notna().all()
    assert test.row_id.notna().all() and test.row_id.is_unique and sample.row_id.is_unique
    assert len(sample) == len(test) and sample.row_id.equals(test.row_id), "Template and test IDs/order differ"
    print(f"Template matches the concatenated test IDs in order: {len(test):,} rows")
    return sample
'''

intro = '''## Status of this draft

This notebook is the first part of my reproducibility work. It checks the official inputs and the submission template. **It does not yet train the historical models or generate the final predictions.** I will add the frozen transformations, model stages, calibration and output checks before calling it an end-to-end reproduction. There are no private model files, team scripts or predictions bundled here.

The only external inputs in this draft are the competition Parquet files attached through Kaggle. I do not redistribute them. Run the cells in order with Internet off; the checks need NumPy, pandas and PyArrow, normally available in the Kaggle image. The versions are printed below. The full training environment still needs to be pinned and tested on Kaggle.
'''

w1 = [md('''# Week 1: pricing in the developed market

I estimate the expected ultimate claim cost for each 2025 policy period in motor, buildings and contents. The target is net of excess and recoveries and excludes declined claims. It is a period risk premium, not a commercial premium. Claims valued at the end of 2024 do not reveal the full ultimate cost, so the development assumptions and their sensitivity matter.
'''), md(intro), md('''## Attach the competition data

In Kaggle, add the IAA AI-Assisted Hackathon 2026 Part 1 competition as an input. Its archived file listing places the files in `public/`. The search below also supports Kaggle's competition mount prefix. If more than one matching folder is attached, set `DEVELOPED_DIR` to its exact path. Local testing may set `IAA_W1_DATA` to the directory containing the Parquet files.
'''), code(common_imports + '''
DEVELOPED_DIR = os.environ.get("IAA_W1_DATA", "")  # e.g. /kaggle/input/competitions/iaa-ai-assisted-hackathon-2026-part-1/public
'''), code(helpers), code('''developed = find_market("public", BASE_FILES, DEVELOPED_DIR)
print("Developed data:", developed)
display(inventory(developed, BASE_FILES))
sample = check_template(developed)
'''), md('''## Reading the data safely

I use `policy_id`, the line of business and occurrence date together to assign claims to a covered period. A policy can span multiple periods, so an ID-only join is unsafe. I keep the original files read-only and retain the input hashes above for a reproducible run. I also check whether each feature would be available when a price is quoted.

My historical approach combines total-cost Tweedie models and per-peril frequency and severity models. The S30 blend is followed by S41 line-level factors derived from public leaderboard probes. The latter are historical calibration inputs, not an independent test. I still need to embed the original data corrections, model code, frozen configuration and S41 calibration into this notebook and test the whole chain.
''')]

w2 = [md('''# Week 2: adapting pricing to the emerging market

I estimate the 2025 ultimate cost for each emerging-market policy period. The developed market provides a reference; I keep joins within each market. The separate commercial premium exercise applies expense assumptions to twenty reference policies and does not change the risk-premium submission.
'''), md(intro), md('''## Attach the competition data

Add the IAA AI-Assisted Hackathon 2026 Part 2 competition as an input. The archived listing contains `developed/` and `emerging/` folders. The developed folder is the historical reference from Part 1. If the search finds multiple matches, set the corresponding path explicitly. Local tests can set `IAA_W2_DEVELOPED` and `IAA_W2_EMERGING`.
'''), code(common_imports + '''
DEVELOPED_DIR = os.environ.get("IAA_W2_DEVELOPED", "")  # e.g. /kaggle/input/competitions/iaa-ai-assisted-hackathon-2026-part-2/developed
EMERGING_DIR = os.environ.get("IAA_W2_EMERGING", "")  # e.g. /kaggle/input/competitions/iaa-ai-assisted-hackathon-2026-part-2/emerging
'''), code(helpers), code('''emerging_files = BASE_FILES + ["expenses.parquet", "reference_policies.parquet"]
developed = find_market("developed", BASE_FILES, DEVELOPED_DIR)
emerging = find_market("emerging", emerging_files, EMERGING_DIR)
for name, folder, files in (("developed", developed, BASE_FILES), ("emerging", emerging, emerging_files)):
    print(name, folder)
    display(inventory(folder, files))
sample = check_template(emerging)
'''), md('''## How I frame the adaptation

The emerging training periods cover 2023–2024 and claims are valued at 31 December 2024. Observed incurred claims are an imperfect proxy for ultimate losses. I preserve market boundaries and assign claims by line, policy and occurrence date, not policy ID alone.

The historical F3c chain combines developed-market and emerging-market models and uses fixed historical public-probe constants. A local reconstruction retrained the chain from the original data, but it included two explicitly restored source segments. I still need to embed that chain and the commercial premium calculation here, document those restorations and verify the outputs on Kaggle. F3c is the documented submission reference; no new model selection follows from this draft.
''')]

for name, cells in [('week1_developed_market.ipynb', w1), ('week2_emerging_market.ipynb', w2)]:
    if (OUT / name).exists():
        raise FileExistsError(f'Refusing to overwrite an existing notebook: {OUT / name}')
    nb = {'cells': cells, 'metadata': {'kernelspec': {'display_name': 'Python 3', 'language': 'python', 'name': 'python3'}, 'language_info': {'name': 'python'}}, 'nbformat': 4, 'nbformat_minor': 4}
    (OUT / name).write_text(json.dumps(nb, ensure_ascii=False, indent=1) + '\n', encoding='utf-8')
    print(OUT / name)
