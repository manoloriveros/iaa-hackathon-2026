# How I reproduce both weeks

I provide two standalone notebooks containing source code and frozen configuration. They read the official competition Parquet inputs and create a fresh workspace. I do not need to clone this repository or provide previous fitted models, OOF tables or final predictions for these notebook workflows.

| Notebook | Inputs I attach | Output |
| --- | --- | --- |
| `week1_developed_market.ipynb` | The eleven developed-market files from Part 1 | S30 and final S41 CSVs |
| `week2_emerging_market.ipynb` | Developed and emerging folders from Part 2, including expenses and reference policies | F3c CSV and the twenty commercial premiums |

The notebooks include 44 and 79 source files respectively. My Week 2 execution plan contains fourteen initial stages and thirty-four chain stages through F3c. The review record identifies the static syntax and entry-point checks; these do not replace execution.

## How I supply the inputs

In Kaggle I attach the competition data, select CPU and follow the cells in order. Automatic discovery requires one matching input folder. For a local run, or when more than one input matches, I set the input variables before starting the kernel:

```powershell
$env:IAA_W1_DATA = 'C:/path/to/week1/parquet'
$env:IAA_W2_DEVELOPED = 'C:/path/to/week2/developed'
$env:IAA_W2_EMERGING = 'C:/path/to/week2/emerging'
$env:IAA_NOTEBOOK_WORK = 'C:/path/to/temporary_runs'
$env:IAA_NOTEBOOK_EXPORT = 'C:/path/to/private_exports'
```

I use paths to the Parquet directories themselves. Week 1 requires eleven files; emerging requires thirteen. The notebooks check required names, template IDs and input fingerprints before modelling. I keep the markets separate because their identifiers are not interchangeable.

## Environment and resources

The reference package versions are declared in each notebook's `REFERENCE` mapping and optional installation cell. For Week 1 the final S30/S41 route uses NumPy, pandas, SciPy, scikit-learn, LightGBM, CatBoost and PyArrow. The fixed Week 2 route declares its own subset. Some embedded historical alternatives import other packages inside functions; their presence does not mean those alternatives are run by the final recipe.

If I need the optional installation cell, I run it once, restart the kernel, set `INSTALL_REFERENCE_PACKAGES` back to `False` and then run the notebook. I retain environment differences in the output record and rely on the final fingerprint checks rather than assume numerical identity across versions.

The historical Week 1 reference environment declared Ubuntu, Python 3.13.16, two cores and 8 GB. Its larger reconstruction including S22 took 10.6 hours; the notebook runs the 30-node S30 graph. I have not established hosted Kaggle runtime, peak storage or memory. A long local reconstruction is not a guarantee that it will fit a hosted session.

Intermediate data, models and logs use a new temporary directory. It does not persist automatically. I choose sufficient local storage and preserve a failed run before investigating it. Final outputs use the configured private export folder or Kaggle working storage. Row-level results remain restricted under the competition rules.

## What my local checks established

Week 1 rebuilt CAP01 and the complete F0 content from the originals. The confirmation audit flag uses a retrospective rule inferred from the historical matrix; it matched this dataset but does not recover the original decision process and is excluded from predictors. A resumed local execution completed all thirty S30 nodes and produced the historical S30/S41 CSV hashes. The runner returned code 3 with 160 intermediate differences. Three feature-table fingerprints remain unexplained; small numeric differences in other arrays and prediction tables do not remove that limitation.

Week 2 rebuilt the chain from originals with forty-eight successful stage receipts and produced the historical F3c CSV. An interrupted stage was preserved and rerun in an isolated copy. The twenty-one A1 transfer tables matched their historical keys and values; the commercial calculation is included in the notebook.

I have not established one uninterrupted Run All, a hosted Kaggle run or independent professional review. I retain the exact local receipts and source hashes in `registro/notebooks_kaggle_actual.json` in my repository.

## Where I keep the original workflow

The notebook builders in `herramientas/` are development aids; the notebooks do not call them. I document the original repository routes in `docs/REPRODUCCION_COMPLETA.md` and `docs/REENTRENAMIENTO_ORIGINALES.md`. My local input paths do not need to reproduce the authors' historical machine paths: the runners supply the required runtime bindings.

I keep notebook outputs cleared in Git. Running a notebook, submitting its CSV and publishing code are separate actions with their own competition requirements.
