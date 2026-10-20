# Video script

Five-minute video for the final submission. The jury grades only the first five minutes, and the submission page asks for the approach, the results, the AI-assisted workflow and the adaptation to the new market. This script covers Part 1 in about 4:35 at 150 words per minute and leaves about 0:20 for the Week 2 adaptation, plus the time of slide 17, which the Week 2 slides replace; that part can only be recorded once Part 2 is over. A Spanish copy is in `GUION_VIDEO_ES.md`.

## What you need

- Slides: `docs/entrega/video/laminas_en.pdf` (17 slides at 1920 × 1080) or the PNG files in `docs/entrega/video/laminas/en/`. They are drawn from `docs/entrega/datos/cifras_entregables.json`, the same file behind the report and the dashboard.
- If any figure changes (a new forum post, a new swarm cycle, a different leaderboard position), regenerate before recording: `python herramientas/cifras_entregables.py --raiz <workspace> --salida docs/entrega/datos/cifras_entregables.json`, then `python herramientas/construir_entrega.py todo`.
- Optional live captures: the dashboard (`docs/entrega/panel_modelo.html`) for slide 15 and a terminal for slide 16.

## Scene by scene

| # | Time | Slide | Narration | On screen |
| --- | --- | --- | --- | --- |
| 1 | 0:00–0:14 | A risk premium for every policy period, built and challenged with AI | I'm Manuel Rodríguez, an actuary competing as an individual team. This model, the Per-peril blend, prices every 2025 policy period. It was built with AI and, just as deliberately, challenged with AI. | Cover with the three figures. If your camera is on, this is the moment to look at it. |
| 2 | 0:14–0:36 | The task: expected ultimate cost per policy period | The target is the expected ultimate cost of each period, net of excess and recoveries. Most periods cost nothing, so the score is a Tweedie D², where zero means charging everyone the average. A constant rate per line reaches 0.071; our model reaches 0.138 on 2024 and 0.12996 on the public leaderboard. | Point at the coloured squares, then at the three markers on the D² scale. |
| 3 | 0:36–0:47 | Six stages, each one checked | There are six stages, each one checked. The reporting delay enters exactly once, through the training exposure, and every stage leaves fingerprints that anyone can verify. | Follow the six boxes in order and pause on stage 3. |
| 4 | 0:47–1:06 | Data: fix what can be proven, declare what cannot | The eleven original files are never modified. AI audited all 105 columns and found real defects, such as identifiers without their leading zeros, exposure stored in days and 604 duplicate claims. Eight reversible rules fix them, and an independent rebuild matched 148 million cells. | Table first, then the claims flow at the bottom (163,150 to 160,432). |
| 5 | 1:06–1:16 | Part of 2024's claims was still unreported | At the end of 2024, only 56 percent of motor bodily injury had been reported. We train with that effective exposure as an offset, | Point at the two short bars, bodily injury and subsidence; the card on the right explains the offset. |
| 6 | 1:16–1:26 | With IBNR, 2024 is no longer an outlier | so 2024 no longer looks cheap: 454 observed, 584 with IBNR, in line with earlier years, and 595 predicted for 2025. | Motor panel: the grey drop to 454, the coloured point at 584, the hollow circle at 595. |
| 7 | 1:26–1:39 | The Per-peril blend: one model, ten components | Each line blends Tweedie total-cost models with per-peril frequency times severity. Each change was judged on 2023 and 2024, with and without the most extreme losses, under criteria written in advance. | Blue is frequency × severity, orange is total cost; then the three cards. |
| 8 | 1:39–2:00 | Fitted on past years, scored on a later full year | We validate the way a tariff is used: fit on past years, score a later full year. On 2024 the model explains about twice the deviance of a constant rate, and it wins in every line. After the choice, eleven pre-registered experiments, an IBNR backtest among them, tested it again. | Left, the three temporal cuts; right, grey against blue bars. |
| 9 | 2:00–2:15 | It ranks risk and stays calibrated | It ranks risk and stays calibrated. Scaling case reserves by twenty-five percent either way barely moves the score, but it moves the 2025 level by up to seven percent, so reserves stay among the limits. | In each panel the line is the prediction and the circles are observed cost. |
| 10 | 2:15–2:38 | AI was organised so that it never validated itself | Now the AI. Two assistants, Claude and Codex, worked in three independent lines: modelling, creative alternatives and challenge. Hypotheses went to a shared forum with their acceptance criterion before anything was computed, and failures were posted too. Kaggle was read through a read-only MCP connection. The decisions that reached the model went through my authorisation. | Trace sources → three lines → forum ← swarm, then the participant and the controls gate. |
| 11 | 2:38–2:53 | What AI did at each stage, and how it was checked | Every stage had its own check: a second implementation recomputed the data rules, a guard removed a variable that measured the claim itself, and an unsupported seventeen percent gain claimed by another AI tool was dropped. | Do not read the table aloud; rest on the 'How it was verified' column. |
| 12 | 2:53–3:01 | Local gains that the public score did not confirm | This is where the forum earned its keep: local scores kept rising while the public score fell. | Point at the shaded zone: orange rises, blue falls. |
| 13 | 3:01–3:22 | The forum's answer: judge the body, keep the tail | One line traced it to a few extreme claims and another turned that into a criterion. Without the costliest half percent of periods, local D² ranks candidates like the public score: 0.83 against 0.49. The two submissions that followed set the public maximum, and the second is the final model. | Grey candidates against the blue final model; compare 0.49 on the left with 0.83 on the right. |
| 14 | 3:22–3:43 | A swarm of agents audited the project every six hours | Three validation agents audited data, models and governance every six hours and raised twenty-one findings. One showed that the package could report success with missing files; it was fixed and tested with 36 adverse cases. Twelve remain open, each with its closure criterion, and two were accepted as declared limitations. | Bars by area and state, then the three cards, GOV-007 first. |
| 15 | 3:43–3:52 | A dashboard to check the numbers without reading code | An offline dashboard lets a human reviewer check the same numbers, chart by chart, with the table behind each one. | Optional: a 10 to 15 second live capture of docs/entrega/panel_modelo.html (open Validation, press Show table, switch to Español). |
| 16 | 3:52–4:11 | The delivered file can be rebuilt and checked | Forty-five control cases pass in three environments, and one command rebuilds the delivered file from the saved components, with the SHA-256 that Kaggle received. Retraining all thirty-six nodes from the originals gave the same file, and a replay from the saved models matched without refitting. | Table on the left, receipt on the right. Optional: show the command running in a terminal and cut to its receipt. |
| 17 | 4:11–4:35 | What we cannot prove yet, and how Week 2 will test it | Our limits are declared: one claims valuation, which leaves reserves as a material uncertainty; a 2025 level that is uncertain in buildings and, in one scenario, high in motor; and a lead over the previous submission that is not robust. For week two we freeze this model and adapt only where the new market's evidence demands it. | Limits on the left, Week 2 protocol on the right. After Part 2 this slide is replaced (see the Week 2 section). |

## Week 2 slot, about 0:44

Record it only with results that exist. Replace slide 17 with two slides built from the new market's data, using the same tools:

1. One slide on what changed in the new market: the differences found in contract, units, perils, claims development and features, each next to the response the protocol foresaw (recalibrate, refit severities, re-estimate the chain-ladder, update the feature contract).
2. Another on what the adaptation achieved: D² of the frozen model on the new market against the adapted one, calibration by decile, the Week 2 public score, and what the forum and the validation swarm found during the week.

Narration guide (fill in the brackets with measured values only): "In the new market we first scored the frozen model: [D²]. The main differences were [list]. Following the protocol we [response], which moved D² to [value]. The forum ran [n] new contrasts and the swarm raised [n] findings; [one example]. The limits declared in Part 1 [which ones were tested and how]."

If the slot needs more than a minute, shorten scenes 9 and 12 first: their content is also in the report.

## Where each figure on screen comes from

| Figure | Value today | Key in `cifras_entregables.json` |
| --- | --- | --- |
| Public score of the final model | 0.12996 | `s30.publico` |
| Kaggle submission | 57371361 | `s30.envio_kaggle` |
| Out-of-sample D² on 2024 | 0.13788 | `validacion.d2_recalculado.V24.agregado` |
| Constant rate per line, 2024 | 0.07094 | `validacion.referencia_m00.V24.agregado` |
| 2025 periods predicted | 626,639 | `s30.filas` |
| Motor bodily injury reported by end of 2024 | 56% | `ibnr.completitud_2024_por_peligro` |
| Motor premium 2024: observed / with IBNR; 2025 prediction | 454 / 584; 595 | `ibnr.prima_riesgo_por_anio` |
| Rank correlation with the public score: body / full | 0.83 / 0.49 | `publico_vs_local` |
| Forum posts and hours | 217 · 54.1 | `foro.aportes, foro.horas` |
| Swarm findings: total / open | 21 / 12 | `validacion_ia.hallazgos, validacion_ia.abiertos` |
| 2025 level change with case reserves ×0.75 or ×1.25 (largest line) | 6.8% | `reservas_acotacion.nivel_max_con_b_075_125` |
| Control cases passed | 45/45 · 45/45 · 45/45 | `controles_paquete.baterias` |

## Before recording

- Check the public score and the leaderboard position on the day; the cover takes both from the data file.
- Keep a calm pace, about 150 words per minute. The whole video should stay under 4:55.
- Say decisions in the first person and name AI tools as tools ("two assistants, Claude and Codex").
- Do not show credentials, tokens, row-level data or private conversations. The slides and the dashboard show aggregates only.
- Export at 1920 × 1080 (MP4, H.264), with captions if the editor allows it, and watch the result once at normal speed against the report.
- Upload it where the final submission form asks; the form link has not been published yet.
