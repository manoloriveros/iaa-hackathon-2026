# My IAA AI Hackathon 2026 project

I am Manuel Rodríguez, an individual participant. I built a pricing workflow for a developed market and adapted it to an emerging market with less history and a large new-business intake. I used Claude and Codex to explore data, implement alternatives, challenge decisions and prepare documentation. I made the delivery choices; checks performed by AI retain that attribution. My [Spanish overview](README.es.md) covers the same project.

I estimate the expected ultimate claim cost for each 2025 policy period, net of excess and recoveries and excluding declined claims. The prediction covers the row's period. I then use the supplied expense assumptions to calculate commercial premiums for the twenty reference policies.

## Reproduce my two submissions

I provide two standalone notebooks containing source code and frozen configuration. They read the official competition inputs, create a fresh workspace and do not download my repository or load previous models or predictions.

| Market | Notebook | Output I reconstruct |
| --- | --- | --- |
| Developed | [week1_developed_market.ipynb](notebooks/week1_developed_market.ipynb) | S30 blend and S41 level calibration |
| Emerging | [week2_emerging_market.ipynb](notebooks/week2_emerging_market.ipynb) | F3c and the twenty commercial reference premiums |

I start with the [notebook guide](notebooks/README.md) for inputs, environment, resources and checks. In Kaggle I attach the corresponding competition data, select CPU and run the cells in order. I can also supply local input directories using the documented environment variables. Intermediate data, models and logs remain in temporary storage. Row-level outputs remain restricted.

Both recipes reproduced the historical final CSV hashes in resumed local runs. Week 1 retains intermediate differences, including three feature-table fingerprints whose cause was not established. Week 2 reproduced the F3c CSV exactly. I have not established a hosted Kaggle run or a single uninterrupted Run All for both notebooks. I retain these limits and the interruption receipts in the [reproduction record](registro/notebooks_kaggle_actual.json). These AI-assisted checks are not independent professional review.

## My delivery video

I provide my [English video, 4:59](https://www.youtube.com/watch?v=AYLkpDmZfZo) as the Video Demo Link. The [video record](registro/video_entrega_actual.json) identifies my selected local version and the scope of the link check.

## My final choices

For Week 1 I chose S41: the S30 per-peril blend with its documented 2025 credibility-based level adjustment. I retained the later experiments and adverse findings rather than selecting solely on the highest public score. I describe the model in [MODELO_FINAL_S41.md](docs/MODELO_FINAL_S41.md) and record my choice in [DECISION_FINAL_S41.md](docs/DECISION_FINAL_S41.md).

For Week 2 I confirmed F3c on 28 October. I combine information transferred from the developed market with the available emerging-market information and a documented residual calibration. The later F3c-R comparison failed the joint registered criteria, so I retained F3c. The [decision record](registro/semana2_decision_final_F3c_20261028.json) and [comparison close](docs/semana2/F3C_REGULARIZADO_CIERRE_20261028.md) preserve that scope. My choice does not establish private-leaderboard superiority or operational tariff approval.

## How I used AI

I used assistants to propose data rules, write code, challenge predictor availability, compare recipes and build verification tools. I kept hypotheses, sources, corrections and adverse outcomes in the project record. I also used AI for explanation, translation and audiovisual preparation. I did not measure a time saving that I can substantiate.

I distinguish my decisions from automated checks and independent review. A calculation repeated by another AI session remains an AI-assisted technical check. I explain the contributions and verification in [AI_WORKFLOW_EN.md](docs/entrega/AI_WORKFLOW_EN.md).

## Navigate the project

| What I need | Entry point |
| --- | --- |
| Current methods and decisions | [Documentation guide](docs/README.md) |
| Final form, local files and access checks | [Submission guide](docs/entrega/FORMULARIO_FINAL.md) |
| Original reproduction workflows | [Week 1](docs/REPRODUCCION_COMPLETA.md) and [Week 2](docs/REENTRENAMIENTO_ORIGINALES.md) |
| Version history and delivery access | [Version control](docs/VERSION_CONTROL.md) |
| Earlier proposals and reviews | [Document archive](docs/archivo/README.md) |

In my local workspace, `Hackaton/Entrega_final` collects the current Spanish report, both CSVs, notebooks and my selected English voice-only video. Competition inputs, row-level outputs and the report containing individual reference premiums stay outside Git. [NOTICE.md](NOTICE.md) explains the scope of the MIT license.

I identify this code package with the `entrega-codigo-20261029` tag. My [synchronisation record](registro/sincronizacion_github_actual.json) records the checks and remote confirmation. I keep the repository private until the planned opening after the competition closes; judges' access still needs confirmation. My [delivery review](registro/revision_entrega_actual.json) retains the reproduction limits and the outstanding English report.
