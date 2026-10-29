# How I maintain and deliver the code

I use Git to preserve the development of both weeks, identify the code behind each submission and explain changes. The competition rubric asks for a structured, version-controlled repository, so I provide its history and reproduction instructions as well as the final files. My [Spanish guide](CONTROL_DE_VERSIONES.md) covers the same process.

I group changes by topic and retain authorship. Commit messages identify project references, AI assistance and the actual human-review status. I do not rewrite history or change dates to suggest that a reconstructed record was committed contemporaneously. The 26 October reconstruction recovered final file versions, not every intermediate revision.

Before associating a CSV with a submission, I identify the producing code's commit and working-tree state. [versionado.py](../herramientas/versionado.py) supports auditing, source incorporation and version seals. Historical results retain their original versions and fingerprints.

## My final delivery check

My `entrega-codigo-20261029` package includes both notebooks, frozen recipes, the code for both weeks and current documentation. I retain earlier proposals in `docs/archivo` with their path and version map. My [synchronisation record](../registro/sincronizacion_github_actual.json) identifies the content checks and remote confirmation.

The earlier snapshot in [revision_entrega_actual.json](../registro/revision_entrega_actual.json) described the remote version from 26 October. I preserve that dated evidence separately from this package.

My project policy keeps the repository private until Part 2 closes and plans MIT publication afterwards. I must resolve judges' access before sending the form. I do not assume a private URL is accessible or that there is an extra submission window after closing.

I include code, notebooks with cleared outputs, frozen configuration, documentation, licensing and shareable provenance. I exclude competition inputs, row-level predictions, fitted models, credentials and private conversations. [NOTICE.md](../NOTICE.md) explains the licensing boundary.

I use the content guard and Git hooks as automated checks with a recorded scope and date. They do not replace inspection of the files actually released. For a read-only review I use:

```text
git status --short
git log -5 --format=fuller
git tag --list
python herramientas/versionado.py auditar
```

I preserve the earlier detailed diagnosis in the [previous Spanish guide](archivo/versiones_previas_20261029/docs/CONTROL_DE_VERSIONES.md). The final form requires a repository URL; a release tag is my traceability measure, not a separate form field.
