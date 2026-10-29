"""Add reader navigation without changing executable notebook cells.

The notebook builders apply this after assembling the frozen source package.
Applying it to a final notebook is idempotent and does not run model code.
"""
from __future__ import annotations

TAG = 'reader-guide'


def strip_presentation(notebook):
    """Remove inserted guide cells before positional builder templates are used."""
    notebook['cells'] = [c for c in notebook['cells']
                         if TAG not in c.get('metadata', {}).get('tags', [])]


def markdown(text):
    return {'cell_type': 'markdown', 'metadata': {'tags': [TAG]},
            'source': (text.strip() + '\n').splitlines(True)}


def improve_presentation(notebook, week):
    """Insert the run guide and tag embedded sources for JupyterLab folding."""
    if week not in (1, 2):
        raise ValueError('week must be 1 or 2')
    code_before = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
    strip_presentation(notebook)
    first = week == 1
    model = 'S41' if first else 'F3c'
    inputs = ('11 developed-market Parquet files from Part 1' if first else
              '11 developed-market and 13 emerging-market Parquet files from Part 2')
    files = ('`submission_week1_S41.csv`' if first else
             '`submission_week2_F3c.csv` and `commercial_reference_premiums.csv`')
    method = '#approach-and-limitations' if first else '#modeling-and-evidence'
    workspace = '#dependencies-and-workspace' if first else '#dependencies-and-run-workspace'
    plan = '#inspect-the-dependency-graph' if first else '#inspect-the-execution-plan'
    run = '#materialize-and-run-the-frozen-recipe' if first else '#run-the-frozen-stages'
    output = '#apply-the-s41-level-factors-and-check-the-output' if first else '#check-and-save-the-risk-premium-csv'
    evidence = (
        'My resumed local reconstruction recovered the historical S41 CSV. It also reported '
        '160 intermediate differences, including three unexplained feature-table fingerprints.'
        if first else
        'My resumed local reconstruction completed the 48 stages through F3c and recovered '
        'the historical F3c CSV. The twenty reference premiums are calculated separately below.'
    )
    notebook['cells'].insert(1, markdown(f'''## Notebook guide

| Purpose | What I reconstruct |
| --- | --- |
| Selected recipe | {model}, my Week {week} submission |
| Required inputs | {inputs} |
| Final exports | {files} |
| External model or repository download | None; source and frozen configuration are embedded |

For a first reading, I follow the [method]({method}), [execution plan]({plan}) and [output checks]({output}). The [embedded source package](#embedded-source-package) preserves the individual programs for inspection. Its source cells are marked as hidden in JupyterLab's presentation metadata; I can expand them. GitHub may display them in full.

For execution, I attach the data, check [dependencies and storage]({workspace}) and run cells in order. The later [recipe execution]({run}) trains models and can take hours. Reading the notebook does not require starting that execution.

{evidence} I have not established a hosted Kaggle execution or an uninterrupted Run All of this adapted notebook. AI-assisted reconstruction is distinct from independent professional review.
'''))
    for i, c in enumerate(notebook['cells']):
        if c['cell_type'] == 'markdown' and ''.join(c['source']).startswith('### Embedded source:'):
            notebook['cells'].insert(i, markdown('''## Embedded source package

I keep the source files below as text assignments. Running these cells registers the code in memory; the later execution section writes it into the new workspace and starts the recipe. I retain the original program boundaries, authorship and frozen configuration. No past row-level predictions or fitted models are embedded.
'''))
            break
    for c in notebook['cells']:
        if c['cell_type'] == 'code' and ''.join(c['source']).startswith('SOURCES['):
            metadata = c.setdefault('metadata', {})
            tags = metadata.setdefault('tags', [])
            if 'embedded-source' not in tags:
                tags.append('embedded-source')
            metadata.setdefault('jupyter', {})['source_hidden'] = True
    continuation = (
        'For Week 1, return code 3 means that the historical final CSV matched while '
        'intermediate artifacts differed. I preserve and inspect the difference report. '
        'Within the same session the runner can reuse completed nodes after its hash checks; '
        'a new notebook session creates a new run folder.' if first else
        'For Week 2, a failed stage stops execution and leaves its log and receipt. '
        'This notebook does not automatically resume the chain. I preserve the failed '
        'run before starting a fresh one or investigating a separate recovery.'
    )
    outputs = markdown(f'''## Outputs and troubleshooting

After the final checks pass, I find {files} in the `EXPORT` directory printed near the beginning. Without an override, Kaggle exports to a run-specific subdirectory of `/kaggle/working`; local execution exports beneath the new run directory. I can set `IAA_NOTEBOOK_EXPORT` before starting to choose a persistent private destination. I keep row-level outputs private.

| If execution stops | What I check |
| --- | --- |
| Missing or ambiguous input directory | The explicit market path, required filenames and attached competition data |
| Missing library or version mismatch | The optional installation cell, kernel restart and reference environment |
| Failed model stage | The stage's log and receipt under the printed run directory |
| Final fingerprint mismatch | Environment and generated artifacts; I retain the file and investigate the difference |

{continuation}

I do not bypass a failed fingerprint check or interpret a resumed run as an uninterrupted execution. A schema-valid CSV and an exact historical file match answer different questions.
''')
    for i, c in enumerate(notebook['cells']):
        if c['cell_type'] == 'markdown' and ''.join(c['source']).startswith('## License and materials'):
            notebook['cells'].insert(i, outputs)
            break
    else:
        notebook['cells'].append(outputs)
    code_after = [''.join(c['source']) for c in notebook['cells'] if c['cell_type'] == 'code']
    if code_before != code_after:
        raise AssertionError('Presentation must preserve executable cells exactly')
