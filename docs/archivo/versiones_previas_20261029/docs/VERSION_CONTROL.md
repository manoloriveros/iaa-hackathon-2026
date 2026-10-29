# Version control

This repository is the version-controlled code repository requested by §2.4.b of the specific competition rules, and it covers both parts of the IAA AI Hackathon 2026. The Submissions page asks for code "maintained using version control so that the development of the solution can be understood and reproduced". This page explains how to read the history, how the record before and between commits was kept, what is deliberately left out of Git and how a submitted file points back to the code that produced it. A Spanish working guide with the full plan is in [CONTROL_DE_VERSIONES.md](../../../CONTROL_DE_VERSIONES.md).

Status on 26 October 2026: Git had 7 commits from 19 and 20 October and more than a thousand files were waiting to be committed. The procedure below was adopted that day; while `auditar` still lists uncommitted files or missing tags, it is not complete. `python herramientas/versionado.py auditar` reports, at any moment, which of the tags named on this page do not exist yet and how many files are still uncommitted, so this page cannot drift silently from the repository.

## Reading the history

Start with `git log --oneline --decorate`, or `git log --format=fuller` to see both dates of each commit. Commits are grouped by theme, and from 26 October each message ends with three trailers:

| Trailer | Meaning |
| --- | --- |
| `Refs:` | Forum contributions (`CLA-…`, `COD-…`) and decisions (`D…`) that motivated or document the change |
| `Asistido-por:` | The AI assistant that drafted or ran the change (Codex, Claude) |
| `Revision-humana:` | Who reviewed it, or `pendiente` while the human review is open |

`git log --format='%h %as %s%n%(trailers)'` prints them. Milestones are marked with annotated tags:

| Tag | Milestone | When the tag is created |
| --- | --- | --- |
| `semana1-revision-20261019` | First reproducible package of Part 1, prepared for human review | 19 October |
| `parte1-mezcla-por-peligro` | The per-peril blend (S30 in code) declared the final model, with the first report and dashboard (decision D99, 20 October) | 26 October, on the 20 October commit |
| `parte1-entrega-final-S41` | Final Part 1 submission S41: level calibration with a pre-registered credibility rule, sensitivity batteries, reproduction and deliverables | When the 20 to 26 October work is committed, on the last commit holding Part 1 files |
| `parte2-entrega-final` | Final Part 2 submission and the code that produces it | When the final Part 2 submission is selected |
| `entrega-final` | The commit given in the final submission form, covering both parts | After the last submission, before the form |

## Before and between commits

Preparation started on 12 October, the competition opened on 16 October and Git was initialised on 19 October, when the first reproducible package was committed. The earlier work was not turned into commits with invented dates. It is kept as it was produced: a decision log, a shared forum where most hypotheses were posted with their acceptance criterion before being computed (the exceptions, such as revisions made after seeing the leaderboard, are recorded as such), and run manifests with the SHA-256 of their inputs and outputs. [docs/expediente/](../../../expediente) exports that record with synthetic identifiers masked.

Between 20 and 26 October the work moved faster than the commits: results were recorded in receipts under `registro/` and in the forum, but files were not committed. The audit of 26 October found the gap, and the pending files are committed in chronological order, one commit per day and theme. In those commits the author date is the last modification time of the newest file in the group, and the commit date is the real date of the reconstruction; each message says so and notes that only the final version of each file is kept. Git shows both dates, and GitHub shows "authored" and "committed" separately when they differ. Every receipt inside those commits keeps its own UTC time and fingerprints, so the order of events can be checked against the forum.

Code that ran outside the repository folder, in the working folders of Part 1 and of the Part 2 work lines, was copied unchanged into `src/semana1/` and `src/semana2/lineas/`, keeping each file's modification time so that it enters the reconstruction on the day it was written. Each of those folders has an `ORIGEN.json` with the source path, modification time and SHA-256 of every file it holds and of the later updates.

## Every submission points to a commit

From 26 October, a file is submitted to Kaggle only after the code that produced it has been committed, and the receipt of the submission carries a version stamp:

```text
python herramientas/versionado.py sello src/semana2 --exigir-limpio
```

The stamp records the commit and the nearest tag, and fails if a listed path does not exist, is ignored by Git, has no committed files or has uncommitted changes. Scripts can call `sello_version()` from the same module. Part 1 is rebuilt from the original data with `reproducir.py` and `herramientas/regenerar_s41.py`, as the README explains.

## What is not versioned, and why

§2.5.b of the specific rules forbids redistributing the competition data, so the data stay out of Git. By project policy, row-level predictions and trained models stay out too, together with the `privado/` folder that holds them locally; the only CSV files in Git are the recipe tables under `receta/` and the indexes of the working record. Receipts keep the SHA-256 of what was left out. Three controls help keep it that way:

| Control | What it does |
| --- | --- |
| Pre-commit hook (`herramientas/git_hooks/pre-commit`) | Stops a commit with data or artifact files, unknown binaries, files over 10 MB, credentials in a known format, or tables with 200 or more distinct identifiers shaped like the competition's |
| `versionado.py auditar` and `vigia` | Review pending changes, code still outside the repository and every blob in the history; `vigia` flags when uncommitted work should be committed |
| `.gitignore` | Excludes data, predictions, models, environments and `privado/` |

These checks catch the usual cases; they are not a guarantee, and each commit is still reviewed. On 26 October the audit reviewed the 567 blobs of the history and found none of those patterns.

## License

The code and documentation are released under the MIT License ([LICENSE](../../../../LICENSE)); [NOTICE.md](../../../../NOTICE.md) lists what the license does not cover, starting with the competition data. The repository stays private until the close of Part 2 and is opened afterwards.

## Verify it yourself

```text
git log --format=fuller --decorate
git tag -n1
python herramientas/versionado.py auditar --salida -
python reproducir.py plan --objetivo=S30
```

For the final submission form, `versionado.py empaquetar --ref entrega-final` also produces a Git bundle with the full history and a ZIP of the delivered tree, both checked and listed with their SHA-256 in a manifest.
