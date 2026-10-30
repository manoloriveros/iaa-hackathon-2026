# Source package for my delivery notebooks

I keep the readable source embedded in my two standalone notebooks here. `week1/` rebuilds the S30 blend and applies the frozen S41 calibration. `week2/` reconstructs T2b, A1 and the F3c chain; the notebook then calculates the twenty commercial reference premiums.

The notebooks contain this code, their configurations and the input contract. Running them does not import this directory, clone the repository or load earlier fitted models or predictions.

I use neutral runtime names and English comments and docstrings in this package. Historical program paths and the actual authorship remain in the repository history and project records. Spanish internal field names and command options retain their frozen interfaces.

| File or directory | Purpose |
| --- | --- |
| `manifest.json` | Source locations and SHA-256 fingerprints for both notebooks |
| `week1/reproducir.py` | Dependency runner, artifact checks and final S30 fingerprint |
| `week1/src/datos/` | Original-data preparation, actuarial bases and F0 |
| `week1/src/modelos/` | Total-cost and frequency-severity models |
| `week1/src/linea_b/` | Frozen trend/severity extensions and blending |
| `week2/ml/` | Developed-market transfer and emerging-market calibration |
| `week2/noche/` | The separate A1 transfer structure |
| `week2/m017/` | Frozen F3c calibration and residual-factor chain |
| `week2/support/` | Explicit historical reconstruction steps; embedded under the historical runtime key `aux/` |
| Each `notebook_template.json` | Narrative, configuration and source placeholders for assembly |

I rebuild the output-free notebooks from the repository root with:

```powershell
python herramientas/build_delivery_notebooks.py --week both
```

The builder checks source fingerprints before embedding. It assembles notebooks without reading the bases or training models. A change to the source package requires a reviewed manifest update; a previous execution does not automatically certify changed model behavior.

The [notebook guide](../../notebooks/README.md) explains inputs, environment, runtime checks and the limits of the available execution evidence.
