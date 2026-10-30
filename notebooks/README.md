# How I reproduce both weeks

I provide two standalone notebooks containing source code and frozen configuration. They read the official competition Parquet inputs and create a fresh workspace. I do not need to clone this repository or provide previous fitted models, OOF tables or final predictions for these notebook workflows.

| Notebook | Inputs I attach | Output |
| --- | --- | --- |
| [Week 1](week1_developed_market.ipynb) | The eleven developed-market files from Part 1 | Final S41 CSV; S30 is reconstructed inside the temporary run |
| [Week 2](week2_emerging_market.ipynb) | Developed and emerging folders from Part 2, including expenses and reference policies | F3c CSV and the twenty commercial premiums |

The notebooks include 44 and 79 source files respectively. My Week 2 execution plan contains fourteen initial stages and thirty-four chain stages through F3c. The review record identifies the static syntax and entry-point checks; these do not replace execution.

I keep the readable English source package in [`src/runtime/`](../src/runtime/README.md). Its comments and docstrings explain the methods without naming individual AI tools. Neutral runtime names replace older assistant-specific names; the original authorship and paths remain in the historical record. Internal field names and command options retain their frozen interfaces.

## How I read or run a notebook

Each notebook opens with a guide linking its method, execution plan and output checks. I can read those sections without running training. The embedded source package preserves the individual programs; its source cells carry JupyterLab metadata to hide them initially, and I can expand them. GitHub may show all source cells.

For execution I follow the cells in order, including the embedded assignments. Those assignments register source text; the later recipe section writes the code into a fresh workspace and starts model training. Reading the notebook or inspecting its plan does not require pressing Run All.

The final exported filenames are `submission_week1_S41.csv` for Week 1 and `submission_week2_F3c.csv` plus `commercial_reference_premiums.csv` for Week 2. Each notebook prints `EXPORT`, the destination directory, before training. In Kaggle it defaults to a run-specific subdirectory of `/kaggle/working`; locally it defaults to the new run folder. I set `IAA_NOTEBOOK_EXPORT` when I need a persistent private destination.

## How I supply the inputs

In Kaggle I attach the competition data, select CPU and follow the cells in order. In my existing local workspace the notebooks find `RUTAS_PROYECTO.json` in the current directory or its parents. They use its Week 1 data route for the developed reference and its emerging-data route for Week 2. I can open the local notebooks without copying the bases into the repository.

The selection order is an explicit market variable, then `IAA_DATA_ROOT`, then the workspace routes, then Kaggle's input mount. A wrong explicit path stops the notebook; it does not silently select another folder. Discovery requires exactly one matching directory and rejects an emerging folder as developed input.

For another local checkout, or when more than one input matches, I set the input variables before starting the kernel:

```powershell
$env:IAA_W1_DATA = 'C:/path/to/week1/parquet'
$env:IAA_W2_DEVELOPED = 'C:/path/to/week2/developed'
$env:IAA_W2_EMERGING = 'C:/path/to/week2/emerging'
$env:IAA_NOTEBOOK_WORK = 'C:/path/to/temporary_runs'
$env:IAA_NOTEBOOK_EXPORT = 'C:/path/to/private_exports'
```

I use paths to the Parquet directories themselves. Week 1 requires eleven files; emerging requires thirteen. The notebooks check required names, template IDs and input fingerprints before modelling. I keep the markets separate because their identifiers are not interchangeable.

As alternatives to individual market paths, I can set `IAA_DATA_ROOT` to a common parent containing the official data folders, or `IAA_PROJECT_ROOT` to my workspace containing `RUTAS_PROYECTO.json` when the kernel starts elsewhere. These variables do not download or redistribute data. The [input contract](../registro/contrato_entradas_notebooks.json) contains file names, sizes and the SHA-256 fingerprints archived during the official downloads. The notebooks stop on any mismatch; they do not assume that displaying a calculated hash proves the input version.

I check both developed and emerging template IDs for Week 2. A successful preflight writes `input_manifest.json` into the new run folder, with resolved directories, fingerprints and template counts. The notebooks reject temporary or export directories inside their input folders.

Alternatively, I can set the variables in an extra configuration cell before the notebook's existing import and path cells. I replace the example paths with directories on my machine:

```python
import os

# Week 1
os.environ["IAA_W1_DATA"] = "C:/path/to/week1/parquet"

# Week 2
os.environ["IAA_W2_DEVELOPED"] = "C:/path/to/week2/developed"
os.environ["IAA_W2_EMERGING"] = "C:/path/to/week2/emerging"

# Optional locations shared by both notebooks
os.environ["IAA_NOTEBOOK_WORK"] = "C:/path/to/temporary_runs"
os.environ["IAA_NOTEBOOK_EXPORT"] = "C:/path/to/private_exports"
```

If I install packages and restart the kernel, I rerun this configuration cell. Automatic discovery only works for the expected attached competition folders; an explicit path also supports a different local folder name.

## How I check the data connection without training

With pandas and PyArrow available, I can run the same input-resolution and validation code from the repository root:

```powershell
python herramientas/entradas_notebooks.py --week both
```

If my terminal starts outside the workspace, I add `--project-root C:/path/to/workspace`. For a separate data tree I use `--data-root C:/path/to/official_data`. An optional `--receipt privado/input_preflight.json` saves the result outside the input folders. This command reads the bases, checks fingerprints and template IDs, and does not train models or generate predictions. The notebook embeds the same runtime code and its contract, so it does not import this repository tool during execution.

## Environment and resources

The reference package versions are declared in each notebook's `REFERENCE` mapping and optional installation cell. For Week 1 the final S30/S41 route uses NumPy, pandas, SciPy, scikit-learn, LightGBM, CatBoost and PyArrow. The fixed Week 2 route declares its own subset. Some embedded historical alternatives import other packages inside functions; their presence does not mean those alternatives are run by the final recipe.

If I need the optional installation cell, I run it once, restart the kernel, set `INSTALL_REFERENCE_PACKAGES` back to `False` and then run the notebook. I retain environment differences in the output record and rely on the final fingerprint checks rather than assume numerical identity across versions.

The historical Week 1 reference environment declared Ubuntu, Python 3.13.16, two cores and 8 GB. Its larger reconstruction including S22 took 10.6 hours; the notebook runs the 30-node S30 graph. I have not established hosted Kaggle runtime, peak storage or memory. A long local reconstruction is not a guarantee that it will fit a hosted session.

Intermediate data, models and logs use a new temporary directory. It does not persist automatically. I choose sufficient local storage and preserve a failed run before investigating it. Final outputs use the configured private export folder or Kaggle working storage. Row-level results remain restricted under the competition rules.

## My latest execution and source checks

A fresh local execution of the preceding frozen Week 2 edition completed all 91 code cells and 48 stages, reproducing the F3c CSV byte for byte. Its twenty commercial premiums and fixed-expense sensitivities matched the report source. The fresh S41 execution is still running; I retain its actual status in the [execution index](../registro/ejecucion_notebooks_actual.json).

For this English edition, I reviewed 469 comment/docstring items across the 123 embedded sources. Their executable structures match the frozen sources after removing documentation and normalizing the declared runtime-name changes. Separate checks rebuilt Week 1 data through F0 from the originals and resolved all 30 and 48 stage paths. These checks do not constitute another full Run All of the edited edition. The [source review](../registro/documentacion_codigo_actual.json) records that distinction.

## Earlier local reconstruction evidence

Week 1 rebuilt CAP01 and the complete F0 content from the originals. The confirmation audit flag uses a retrospective rule inferred from the historical matrix; it matched this dataset but does not recover the original decision process and is excluded from predictors. A resumed local execution completed all thirty S30 nodes and produced the historical S30/S41 CSV hashes. The runner returned code 3 with 160 intermediate differences. Three feature-table fingerprints remain unexplained; small numeric differences in other arrays and prediction tables do not remove that limitation.

Week 2 rebuilt the chain from originals with forty-eight successful stage receipts and produced the historical F3c CSV. An interrupted stage was preserved and rerun in an isolated copy. The twenty-one A1 transfer tables matched their historical keys and values; the commercial calculation is included in the notebook.

Those earlier executions used separate or resumed branches. They are retained separately from the fresh execution above. Hosted Kaggle execution and independent professional review remain unverified. I keep the historical receipts and source hashes in `registro/notebooks_kaggle_actual.json`.

## Where I keep the original workflow

The builder `herramientas/build_delivery_notebooks.py --week both` assembles the notebooks from the pinned English sources and templates in `src/runtime/`. It does not train models, and the notebooks do not call it. The two `integrar_notebook_semana*.py` entry points call this same builder. I retain the original routes in `docs/REPRODUCCION_COMPLETA.md` and `docs/REENTRENAMIENTO_ORIGINALES.md`; runtime bindings supply the isolated paths.

I keep notebook outputs cleared in Git. Running a notebook, submitting its CSV and publishing code are separate actions with their own competition requirements.

## If execution stops

| Symptom | What I inspect |
| --- | --- |
| Missing or ambiguous inputs | The explicit market path, filenames and attached data |
| Import or dependency error | The reference versions, installation output and kernel restart |
| Stage failure | The stage log and receipt in the printed run directory |
| Historical fingerprint mismatch | The generated file, environment and intermediate differences |

I preserve a failed run rather than overwrite its evidence. Week 1 supports the documented checks before reusing completed nodes in the same run. Week 2 starts a fresh chain and does not automatically resume. I do not bypass a hash failure to label a run an exact reproduction.
