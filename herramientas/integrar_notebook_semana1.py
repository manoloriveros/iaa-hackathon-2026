"""Embed the S30/S41 recipe without embedding row-level audit ledgers."""
from __future__ import annotations
import json
import sys
from pathlib import Path
from presentacion_notebooks import improve_presentation, strip_presentation
from entradas_notebooks import apply_input_contract

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
NB = R/'notebooks/week1_developed_market.ipynb'

def cell(kind, text):
    d = {'cell_type': kind, 'metadata': {}, 'source': text.splitlines(True)}
    if kind == 'code': d.update(execution_count=None, outputs=[])
    return d
def read(p): return json.loads(p.read_text(encoding='utf-8'))
def source_literal(text):
    for quote in ("'''", '"""'):
        if quote not in text:
            return quote + text.replace('\\', '\\\\') + quote
    return '(' + '\n'.join(repr(line) for line in text.splitlines(True)) + ')'

nb = read(NB)
strip_presentation(nb)
nb['cells'] = [c for c in nb['cells'] if not ''.join(c['source']).startswith(('## Optional dependency installation', 'INSTALL_REFERENCE_PACKAGES ='))][:6]
nb['cells'][0]['source'] = ('''# Week 1: pricing in the developed market\n\nI am Manuel Rodríguez, an actuarial student and individual participant in the IAA AI Hackathon 2026. In this notebook I explain and reconstruct my Week 1 risk-premium model, developed with AI assistance.\n\nI estimate the expected ultimate claim cost for each 2025 policy period in motor, buildings and contents. The target is net of excess and recoveries and excludes declined claims. It is a period risk premium, not a commercial premium. Claims valued at the end of 2024 do not reveal the full ultimate cost, so the development assumptions and their sensitivity matter.\n''').splitlines(True)
nb['cells'][3:3] = [cell('markdown', '''## Optional dependency installation\n\nKaggle usually includes these libraries. If the environment does not match the recorded reference, set the switch to `True` and run this cell with Internet enabled. Restart the kernel after installation, set the switch back to `False`, and run from the top. Keep the same Kaggle session so the installed packages remain available. The reference versions may not support every Kaggle Python image.\n'''), cell('code', '''INSTALL_REFERENCE_PACKAGES = False\nif INSTALL_REFERENCE_PACKAGES:\n    import subprocess, sys\n    subprocess.check_call([sys.executable, "-m", "pip", "install", "numpy==2.5.3", "pandas==3.0.5", "scipy==1.18.1", "scikit-learn==1.9.1", "lightgbm==4.7.0", "catboost==1.2.10", "pyarrow==26.0.0"])\n    raise RuntimeError("Packages installed. Restart the kernel, turn installation off, and run all cells again.")\n''')]
nb['cells'][1]['source'] = ('''## Scope and reproducibility\n\nI rebuild the historical S30 models and apply the S41 public-probe level factors from the official original Parquet files. All source code, parameters and aggregate verification hashes used below are embedded in this notebook; no team files, models or predictions are required. The complete adapted notebook has not yet been verified end to end on Kaggle.\n\nThe original F0 construction used restricted row-level decision ledgers for two audit-only capital flags. Both are excluded from every model. I reconstruct CAP01 directly from the original data and its frozen rule. For the other flag, I use a rule inferred after inspecting the historical matrix: a normal period in the same policy and, for buildings, the same address. The rule exactly matched the historical flag on this data; it is a retrospective reconstruction, not the recovered decision process or proof that the rule generalizes. I verify the complete F0 content hashes before training and check the final CSV separately.\n\nAttach the Part 1 competition files and run in order. I keep intermediate data, models and logs in a fresh temporary directory outside `/kaggle/working`; only the final CSV goes into `/kaggle/working`. The temporary directory does not persist with the notebook output. Input files remain read-only, and the row-level final CSV must remain private under the competition rules.\n''').splitlines(True)
nb['cells'].append(cell('markdown', '''## Approach and limitations\n\nI assign claims using policy, line and occurrence date, then build observed net costs and reporting-development adjustments. S30 combines total-cost Tweedie models with peril frequency times severity; its level uses historical temporal cuts. S41 applies three frozen credibility-weighted factors obtained from public leaderboard probes. Since the public leaderboard informed those factors, it is not an independent test of their level.\n\nCase reserves and unreported claims remain uncertain. The historical temporal cuts informed model decisions; feature availability at quote time still needs confirmation. Claude developed the main modeling line, while Codex contributed data rules, reconstruction and checks under my direction. This is self-reproduction, not independent actuarial review.\n\nThe embedded source retains the historical programs and their stage boundaries. Each source is written into a fresh working directory at runtime; the notebook does not fetch a repository or execute a team file.\n'''))
nb['cells'].append(cell('markdown', r'''## From claims to a risk premium

Each prediction is the expected ultimate cost for one policy period, in the competition's fictional currency. It is already a period amount. The target is not the insurer's written premium and it should not be multiplied by exposure a second time when interpreting the output.

I first join each claim to a period using its line, policy identifier and occurrence date. A policy can have more than one period, so an identifier-only join can duplicate or misassign cost. I exclude declined claims and use incurred cost less recoveries for accepted, uniquely assigned claims. The valuation is a snapshot at the end of 2024: open claims may develop further, and some claims have not yet been reported.

I estimate reporting completeness by peril from a count development model. For training, the recipe reduces a period's effective exposure according to that completeness. It does not also inflate the observed label for the same unreported claims. This offset is a modeling assumption, not proof that case reserves are sufficient or that the development pattern will remain stable.

## Validation and information timing

The 2023 cut trains on earlier years and separates customers for calibration and selection. The 2024 cut trains on 2021–2023 and evaluates the next year. The 2025 fit uses the permitted 2021–2024 history. These historical cuts helped choose the model, so I do not describe them as untouched final tests.

The feature contract distinguishes policy and property attributes, prior claims history, prior-year weather, conditional customer attributes and existing pricing information. It excludes the current-period service-contact and renewal outcome fields and the audit flags from predictors. History features are cut at the start of the policy year. Whether every retained field is actually available at a real quote remains an open question.

## Models, aggregation and calibration

I combine total-cost Tweedie models with peril-specific frequency multiplied by severity. In motor the final weights are 40% total cost and 60% frequency–severity; the same split applies to buildings. In contents the split is 30% and 70%. Component predictions are normalized to a line-level reference before blending. The recipe applies the historical shape and exposure adjustments and then calibrates the 2025 level from the two historical cuts.

For Tweedie power 1.5, a constant multiplier that minimizes deviance over a fixed set of positive predictions is `sum(y / sqrt(mu)) / sum(sqrt(mu))`. S41 adds one fixed multiplier per line. Those factors were derived from six public leaderboard probes and a credibility rule specified before their scores were observed. They use information from the public part of 2025, so I do not treat that score as a blind evaluation. The exact factors, rather than their rounded presentation values, are embedded in the final cell.

## How to read the run

The source cells below preserve the original program structure, including the data producer, actuarial bases, feature contract, model stages and blend. The execution cell materializes them inside a fresh run folder and saves logs and a receipt for each node. If a stage fails, inspect its log before rerunning. Code 3 reports a matching final S30 CSV with intermediate content differences; it is not a clean match for every artifact. A different final CSV hash stops the run. The final check also enforces the template's identifiers, their order and positive finite predictions.
'''))
nb['cells'].append(cell('markdown', '''## Interpreting the metric\n\nFor nonnegative observed cost `y` and positive prediction `mu`, Tweedie deviance at power 1.5 is `4 * (y / sqrt(mu) + sqrt(mu) - 2 * sqrt(y))`. The local D² is one minus the total model deviance divided by the deviance of the constant mean prediction. Higher is better; a negative value means worse than that constant on the evaluated rows. The observed target is still a valuation proxy for ultimate cost. I do not claim this local calculation proves every detail of Kaggle's unpublished evaluator.\n\nA score measures one aspect of the exercise. I also examine portfolio slices, large claims, reserve assumptions and whether the input fields exist at quote time. None of those checks turns an adaptive development cut into an independent professional review.\n'''))
nb['cells'].append(cell('code', '''from sklearn.metrics import mean_tweedie_deviance, d2_tweedie_score\n# A small synthetic calculation, including a zero-cost observation.\ny_demo = np.array([0.0, 0.25, 2.0, 100.0])\nmu_demo = np.array([0.1, 0.3, 1.5, 25.0])\nd_demo = 4 * (y_demo / np.sqrt(mu_demo) + np.sqrt(mu_demo) - 2 * np.sqrt(y_demo))\nnull_demo = 4 * (y_demo / np.sqrt(y_demo.mean()) + np.sqrt(y_demo.mean()) - 2 * np.sqrt(y_demo))\nassert np.isclose(d_demo.mean(), mean_tweedie_deviance(y_demo, mu_demo, power=1.5), rtol=1e-13)\nassert np.isclose(1 - d_demo.sum() / null_demo.sum(), d2_tweedie_score(y_demo, mu_demo, power=1.5), rtol=1e-13)\nprint("The formula agrees with the local scikit-learn calculation.")\n'''))
nb['cells'].append(cell('markdown', '''## Dependencies and workspace\n\nThe historical reference used Python 3.13.16, NumPy 2.5.3, pandas 3.0.5, SciPy 1.18.1, scikit-learn 1.9.1, LightGBM 4.7.0, CatBoost 1.2.10 and PyArrow 26.0.0. Check the installed versions below; if needed install compatible versions separately and restart the kernel. Installation may require Internet.\n\nThe historical 36-node reconstruction, which also included the S22 backup, recorded about 10.6 hours on two cores. This notebook runs the 30-node S30 dependency graph; its time on hosted Kaggle has not been measured. [Kaggle's notebook documentation](https://www.kaggle.com/docs/notebooks), consulted on 28 October 2026, describes a 12-hour CPU session and 20 GB of saved working storage. Execution speed and disk use vary, so the available margin is not guaranteed. A hosted end-to-end run is still needed to establish whether this recipe finishes there.\n'''))
nb['cells'].append(cell('code', '''import json, shutil, subprocess, time, uuid\nfrom datetime import datetime, timezone\nfrom importlib import metadata\nREFERENCE = {"numpy": "2.5.3", "pandas": "3.0.5", "scipy": "1.18.1", "scikit-learn": "1.9.1", "lightgbm": "4.7.0", "catboost": "1.2.10", "pyarrow": "26.0.0"}\ninstalled = {name: metadata.version(name) for name in REFERENCE}\nprint("Installed:", installed, "Reference:", REFERENCE)\nif installed != REFERENCE: print("Environment differs from the reference; verify output identity.")\nimport tempfile\nRUN_ROOT = Path(os.environ.get("IAA_NOTEBOOK_WORK", tempfile.gettempdir()))\nRUN = RUN_ROOT / ("iaa_week1_" + uuid.uuid4().hex[:12])\nRUN.mkdir(parents=True, exist_ok=False)\nEXPORT_ROOT = Path(os.environ.get("IAA_NOTEBOOK_EXPORT", "/kaggle/working" if Path("/kaggle/working").is_dir() else str(RUN)))\nEXPORT = EXPORT_ROOT / (RUN.name + "_exports")\nEXPORT.mkdir(parents=True, exist_ok=False)\nprint("Final outputs:", EXPORT)\nPACKAGE = RUN / "embedded_code"\nPACKAGE.mkdir()\nSOURCES = {}\nprint("New run:", RUN)\n'''))

paths = [R/'reproducir.py', R/'herramientas/huella.py', R/'herramientas/etapas_datos.py', R/'herramientas/ejecutar_csv_lf.py', R/'herramientas/inventario.py']
for sub in ('src/modelos', 'src/linea_b', 'src/datos'):
    paths.extend(sorted((R/sub).glob('*.py')))
paths.append(R/'src/datos/n62_codex/rebuild_base.py')

f0_rel = 'Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/tables/'
sys.path.insert(0, str(R/'herramientas'))
import huella
original_digest = huella._parquet_digest
source = (R/'herramientas/huella.py').read_text(encoding='utf-8')
ns = {'__name__': 'embedded_huella'}
exec(compile(source, 'embedded_huella.py', 'exec'), ns)
expected = read(R/'receta/huellas_esperadas.json')

f0_original = (R/'src/datos/construir_f0.py').read_text(encoding='utf-8')
start = f0_original.index('        self.branch_index = json.loads(')
end = f0_original.index('        factors = pd.read_csv(', start)
substitute = '''        # The historical ledgers are not redistributed. This is an explicit retrospective\n        # reconstruction of the audit flags, not the original authorization process.\n        self.branch_index = {"workspace_relative_run": "audit-ledger-not-included"}\n        self.cap01_index = {"workspace_relative_run": current["workspace_relative_run"]}\n        self.d66_index = {"workspace_relative_run": "audit-ledger-not-included"}\n        reconstructed = json.loads((ROOT / current["workspace_relative_run"] / "evidence/cap01_row_ids.json").read_text(encoding="utf-8"))\n        self.cap01_ids = {str(row) for rows in reconstructed.values() for row in rows}\n        self.confirmed_ids = set()\n        for line, threshold in (("buildings", 10000000), ("contents", 1000000)):\n            frames = [read_table(ROOT / self.catalog[f"{kind}_{line}"]["workspace_relative_path"], columns=["row_id", "policy_id", "address_id", "sum_insured"]) for kind in ("policies", "test")]\n            rows = pd.concat(frames, ignore_index=True)\n            normal = rows.sum_insured.le(threshold)\n            grouping = [rows.policy_id, rows.address_id] if line == "buildings" else rows.policy_id\n            has_normal = normal.groupby(grouping, dropna=False).transform("sum").gt(0)\n            self.confirmed_ids.update(rows.loc[rows.sum_insured.gt(threshold) & has_normal, "row_id"].astype(str))\n        self.check("K03_CAP01", "CAP01 identifiers reconstructed from originals", len(self.cap01_ids) == 2073)\n        self.check("K03_RECONSTRUCTED", "Retrospective reconstruction of confirmation flag", len(self.confirmed_ids) == 1305)\n\n'''
f0_changed = f0_original[:start] + substitute + f0_original[end:]
stage = (R/'herramientas/etapas_datos.py').read_text(encoding='utf-8')
start = stage.index('    # decisiones congeladas que solo alimentan marcas audit_* de F0')
end = stage.index('    # 01. bases actuariales', start)
stage = stage[:start] + '    # Restricted audit ledgers are deliberately not copied into this run.\n\n' + stage[end:]
stage = stage.replace('        datos.symlink_to(capa / "data")', '        shutil.copytree(capa / "data", datos) if sys.platform == "win32" else datos.symlink_to(capa / "data", target_is_directory=True)')
stage = stage.replace('        alias.symlink_to(bases.name)', '        shutil.copytree(bases, alias) if sys.platform == "win32" else alias.symlink_to(bases.name, target_is_directory=True)')
stage = stage.replace('        alias.symlink_to(f0.name)', '        shutil.copytree(f0, alias) if sys.platform == "win32" else alias.symlink_to(f0.name, target_is_directory=True)')
assert 'copy' in stage

for p in paths:
    rel = p.relative_to(R).as_posix()
    text = source if rel == 'herramientas/huella.py' else stage if rel == 'herramientas/etapas_datos.py' else f0_changed if rel == 'src/datos/construir_f0.py' else p.read_text(encoding='utf-8')
    if rel == 'src/datos/n62_codex/rebuild_base.py':
        needle = " assert set(caps)==set(rules['CAP01']['approved_sets'])"
        assert text.count(needle) == 1
        text = text.replace(needle, needle + "\n dump(out/'evidence/cap01_row_ids.json',{key:sorted(value) for key,value in caps.items()})")
    nb['cells'].append(cell('markdown', f'### Embedded source: `{rel}`\n\nThis is stored in the notebook and materialized inside the new run.\n'))
    nb['cells'].append(cell('code', f'SOURCES[{rel!r}] = {source_literal(text)}\n'))

datafiles = {}
for p in sorted((R/'receta').rglob('*.json')):
    if p.name == 'semana2_constantes_historicas.json': continue
    rel = p.relative_to(R).as_posix()
    datafiles[rel] = json.dumps(expected, ensure_ascii=False, indent=1) if p.name == 'huellas_esperadas.json' else p.read_text(encoding='utf-8')
datafiles['src/datos/n62_codex/rules.json'] = (R/'src/datos/n62_codex/rules.json').read_text(encoding='utf-8')
nb['cells'].append(cell('markdown', '''## Materialize and run the frozen recipe\n\nI reconstruct the cleaned tables, actuarial bases and F0, then train the 30 S30 stages. The full F0 content and feature-block contract are checked against the original fingerprints, including both reconstructed audit flags. Matching the confirmation flag on this dataset does not recover or independently validate the original audit decisions. The runner records intermediate differences and insists on the historical S30 CSV hash. Its return code 3 means that the final CSV matches while some intermediate hashes differ. I investigate those differences separately; a matching final CSV does not establish equality of every intermediate artifact.\n\nIf a run is interrupted, the same run folder can reuse completed nodes only after checking their required hashes. In the same session, rerun the execution cell and inspect the log if the runner stops on partial outputs. Starting a fresh session creates a fresh run folder; retaining or transferring any checkpoint is a separate operation subject to the competition's data rules.\n'''))
nb['cells'].append(cell('code', f'DATAFILES = {datafiles!r}\n'))
nb['cells'].append(cell('markdown', '''### Inspect the dependency graph\n\nEach row is a stage needed for S30. The `requires` column shows which earlier stages supply its inputs. This graph is frozen; inspecting it does not train a model. The data-building stages precede the first row.\n'''))
nb['cells'].append(cell('code', '''recipe = json.loads(DATAFILES["receta/receta.json"])\nnodes = {node["id"]: node for node in recipe["nodos"]}\nneeded, stack = set(), [recipe["objetivos"]["S30"]["nodo"]]\nwhile stack:\n    current = stack.pop()\n    if current not in needed:\n        needed.add(current)\n        stack.extend(nodes[current]["requiere"])\nkinds = {"variables": "features", "seleccion_v23": "2023 selection", "produccion": "production", "partes": "peril components", "severidad": "severity", "linea_b": "trend-adjusted severity", "mezcla": "blend"}\ngraph = [{"stage": node["id"], "kind": kinds[node["etapa"]], "requires": ", ".join(node["requiere"]), "source": node["script"]} for node in recipe["nodos"] if node["id"] in needed]\nprint(f"Stages in the S30 graph: {len(graph)}")\ndisplay(pd.DataFrame(graph))\n'''))
nb['cells'].append(cell('code', '''for rel, text in {**SOURCES, **DATAFILES}.items():\n    dest = PACKAGE / rel\n    dest.parent.mkdir(parents=True, exist_ok=True)\n    if rel.endswith(".py"): compile(text, str(dest), "exec")\n    dest.write_text(text, encoding="utf-8", newline="\\n")\nwork = RUN / "run"\nwork_dir = work / "work"\nwork_dir.mkdir(parents=True, exist_ok=True)\nconfig = PACKAGE / "receta/especificaciones/cfg_total.json"\nwork_config = work_dir / "cfg_total.json"\nif work_config.exists() and work_config.read_bytes() != config.read_bytes():\n    raise RuntimeError(f"Existing configuration differs: {work_config}")\nif not work_config.exists():\n    shutil.copyfile(config, work_config)\ncmd = [sys.executable, "-X", "utf8", str(PACKAGE / "reproducir.py"), "todo", "--objetivo=S30", f"--semana1={developed.parent}", f"--originales={developed}", f"--trabajo={work}", "--continuar-si-difiere"]\nprint("Starting S30. Logs and receipts are in", work)\nresult = subprocess.run(cmd, cwd=RUN, env=dict(os.environ, PYTHONUTF8="1", PYTHONHASHSEED="0", OMP_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2", MKL_NUM_THREADS="2"))\nif result.returncode not in (0, 3): raise RuntimeError(f"S30 run failed with code {result.returncode}; inspect {work / 'registros'}")\nprint("Runner return code:", result.returncode)\n'''))
factors = read(R/'registro/sonda_nivel_D100_resolucion.json')['resolucion']['S41']['factores_aplicados']
nb['cells'].append(cell('markdown', '''## Apply the S41 level factors and check the output\n\nThe three exact factors below are frozen from the historical credibility rule. I apply them to the newly generated six-decimal S30 CSV, preserving the template order. A hash comparison checks the final file against the historical S41 receipt.\n'''))
nb['cells'].append(cell('code', f'''factors = {factors!r}\ns30 = work / "work/S30_claude_b/S30_claude_b.csv"\npred = pd.read_csv(s30, dtype={{"row_id": str}})\nline_lookup = pd.concat([pd.read_parquet(developed / f"test_{{line}}.parquet", columns=["row_id"]).assign(line=line) for line in LINES]).set_index("row_id").line\nlabels = line_lookup.reindex(pred.row_id).to_numpy()\nassert pd.notna(labels).all()\nfor line, factor in factors.items():\n    pred.loc[labels == line, "prediction"] *= factor\nexpected_ids = pd.read_parquet(developed / "sample_submission.parquet", columns=["row_id"]).row_id.astype(str)\nassert list(pred.columns) == ["row_id", "prediction"] and pred.row_id.is_unique and pred.row_id.equals(expected_ids)\nassert np.isfinite(pred.prediction).all() and (pred.prediction > 0).all()\nout = RUN / "submission_week1_S41_candidate.csv"\npred.to_csv(out, index=False, float_format="%.6f", lineterminator="\\n")\nh = hashlib.sha256(out.read_bytes()).hexdigest()\nexpected_sha = "d8661c2874e9112bd3dd62ea4470a465ee309832dee53fd9dcaa4144dac643a5"\nprint("S41 SHA-256:", h, "matches historical:", h == expected_sha)\nif h != expected_sha:\n    raise RuntimeError(f"S41 differs from the historical CSV. Preserve and investigate {{out}} before treating this as an exact reproduction.")\nfinal_output = EXPORT / "submission_week1_S41.csv"\nshutil.copyfile(out, final_output)\nprint("Output:", final_output)\n'''))
license_text = (R/'LICENSE').read_text(encoding='utf-8').strip()
nb['cells'].append(cell('markdown', '## License and materials\n\nMy project code and documentation are covered by the MIT License below. Competition data and third-party packages retain their own terms and are not included in that license.\n\n' + license_text + '\n'))
apply_input_contract(nb, 1)
improve_presentation(nb, 1)
NB.write_text(json.dumps(nb, ensure_ascii=False, indent=1)+'\n', encoding='utf-8')
print('Embedded',len(paths),'sources in',NB,NB.stat().st_size)
