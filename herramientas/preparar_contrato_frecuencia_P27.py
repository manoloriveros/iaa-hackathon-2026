"""Preflight nuevo de respuestas y pesos número/marca, sin ajustar ni puntuar."""
from datetime import datetime, timezone
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import sys

ROOT = Path('C:/dev/Hakaton'); R = ROOT/'Hackaton/Repositorio_IAA2026'
BASE = R/'privado/semana2/mision017_fase2'; HOME = BASE/'A1S_nucleo_20261026_v1'
COUNTS = BASE/'recuentos_fuente2024_v1'; LINKS = BASE/'recuentos_fuente2024_rkm_reuse_v1'
OUT = BASE/'P27_contrato_frecuencia_20261026'
INDEX = R/'registro/semana2_contrato_frecuencia_privada_actual.json'
DOC = R/'docs/semana2/PRIVADA_P27_CONTRATO_FRECUENCIA_MARCA.md'
sys.path.insert(0, str(ROOT/'Preparación/.cache/parquet-reader'))
import numpy as np
import pandas as pd
from sklearn.metrics import mean_poisson_deviance, mean_tweedie_deviance
sp = importlib.util.spec_from_file_location('p27_writer', R/'herramientas/registrar_avance_mision017_fase2.py')
w = importlib.util.module_from_spec(sp); sp.loader.exec_module(w)


def dump(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf8') as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)


def transformed_mark(n, cost, en, ec):
    assert all(np.isfinite(v).all() and (v >= 0).all() for v in [n, cost, en, ec])
    assert not ((n == 0)&(cost > 0)).any()
    assert not ((n > 0)&(en == 0)).any()
    assert not ((cost > 0)&(ec == 0)).any()
    assert not ((ec > 0)&(en == 0)).any()
    selected = (n > 0)&(en > 0)&(ec > 0)
    ratio = ec[selected]/en[selected]
    y = cost[selected]/(n[selected]*ratio)
    weight = n[selected]*np.sqrt(ratio)
    assert np.isfinite(y).all() and np.isfinite(weight).all() and (weight > 0).all()
    return selected, ratio, y, weight


def synthetic():
    n = np.array([0., 1., 2., 4., 1.]); en = np.array([.2, .3, .5, .8, 1.])
    rate = np.array([.1, .7, .5, 1., 2.]); ratio = np.array([.7, .8, 1.1, .6, 1.])
    cost = np.array([0., 0., 400., 800., 100.]); ec = en*ratio
    assert math.isclose(mean_poisson_deviance(n, en*rate)*len(n),
        mean_poisson_deviance(n/en, rate, sample_weight=en)*en.sum(), rel_tol=3e-14)
    selected, rr, y, weight = transformed_mark(n, cost, en, ec)
    mean = np.array([100., 80., 150., 200.]); observed_y = cost[selected]/n[selected]
    lhs = mean_tweedie_deviance(observed_y, rr*mean, power=1.5, sample_weight=n[selected])*n[selected].sum()
    rhs = mean_tweedie_deviance(y, mean, power=1.5, sample_weight=weight)*weight.sum()
    assert math.isclose(lhs, rhs, rel_tol=2e-13)
    assert int((y == 0).sum()) == 1
    # Include penalty scaling, rather than claiming normalized weighted losses
    # leave an unchanged numerical regularization parameter equivalent.
    penalty = .7; norm_beta = 2.3; nominal_alpha = 1.
    old_obj = .5*lhs/n[selected].sum()+.5*nominal_alpha*norm_beta
    adjusted_alpha = nominal_alpha*n[selected].sum()/weight.sum()
    new_obj = .5*rhs/weight.sum()+.5*adjusted_alpha*norm_beta
    assert math.isclose(new_obj, old_obj*n[selected].sum()/weight.sum(), rel_tol=2e-13)
    count_alpha = .001*len(n)/en.sum()
    original_count = .5*mean_poisson_deviance(n, en*rate)+.5*.001*norm_beta
    transformed_count = .5*mean_poisson_deviance(n/en, rate, sample_weight=en)+.5*count_alpha*norm_beta
    assert math.isclose(transformed_count, original_count*len(n)/en.sum(), rel_tol=2e-13)
    return {'count_offset_weight_deviance_identity': True, 'mark_offset_weight_deviance_identity': True,
        'both_normalized_penalty_rescalings_verified': True, 'zero_cost_positive_count_retained': True,
        'new_fits': 0, 'new_model_inference': 0}


def main():
    sys.stdout.reconfigure(encoding='utf8'); assert not INDEX.exists() and not DOC.exists() and not (OUT/'report.json').exists()
    assert not w.read(R/'registro/semana2_mision017_fase2_actual.json').get('active_jobs')
    if OUT.exists():
        correction = w.read(OUT/'implementation_correction.json')
        assert correction['unchanged_synthetic_fixture_sha256'] == w.sha(OUT/'synthetic_objective_identity.json')
    else:
        OUT.mkdir(); dump(OUT/'synthetic_objective_identity.json', synthetic())
    counts_report = w.read(COUNTS/'report.json'); links_report = w.read(LINKS/'report.json')
    assert links_report['count_likelihood_input_positivity_pass'] and links_report['paired_mark_link_support_pass']
    paths = [Path(__file__), COUNTS/'report.json', COUNTS/'validation_v1/report.json', COUNTS/'completion_receipt.json',
        LINKS/'report.json', R/'herramientas/registrar_recuentos_fuente2024.py',
        R/'herramientas/recuperar_productor_FSp_edificios.py', R/'src/semana2/modelo_peril2023.py',
        R/'src/semana2/modelo_peril_frecuencia2023.py', R/'herramientas/robustez2023_ciclo3.py',
        R/'registro/semana2_robustez2023_ciclo3_plan.json', R/'registro/semana2_robustez2023_ciclo8_plan.json',
        R/'registro/semana2_robustez2023_ciclo16_plan.json', R/'registro/semana2_mision017_FSp_edificios_recuperacion_plan_v1.json',
        R/'registro/semana2_mision017_fase2_tanda8_plan_v1.json', OUT/'synthetic_objective_identity.json']
    if (OUT/'implementation_correction.json').exists(): paths.append(OUT/'implementation_correction.json')
    novelty = [
        {'recipe': 'Ciclo3R25', 'existing': 'Poisson/Gamma on emerging2023positive-count response, B20comparison, same older observation mapping.',
            'why_not_current': 'No developed2021-2024paired RKM-count/frozen-cost source mark offsets; standard two-part idea already tried.'},
        {'recipe': 'Ciclo8R38/R39 and ciclo16R58/R59/R60/R61',
            'existing': 'Developed2023peril PoissonGLM and Tweedie1.5/1.8marks retaining zeros, target count/cost credibility adapters. C16also adds small Poisson trees.',
            'why_not_current': 'Source marks are observed cost/count with calendar exposure, not current4year source RKM-frequency and E_C/E_Nmark offsets. Preserve old results, do not rerun or call this a first family.'},
        {'recipe': 'FS/FSp and restored FSpbuildings',
            'existing': 'Developed2021-2023and2021-2024Poisson/Gamma trees with cost-completion offset in frequency and observed positive marks.',
            'why_not_current': 'Cost proxy product may remain coherent; it does not separately identify latent count frequency/marks. Proposed paired source offsets and linear main effects differ. No declaration that historical f*s is invalid.'},
        {'recipe': 'Tanda8', 'existing': 'Current4year source Poisson on physical-peril weather ratios with existing RKM count offsets, source-only nuisance controls.',
            'why_not_current': 'Frequency/weather correction only, no complete paired mark model or complete backbone. Do not repeat weather fits.'}]
    results = []; ready = True
    for line in ['motor', 'buildings', 'contents']:
        cp = COUNTS/f'counts_{line}.parquet'; lp = LINKS/f'rkm_links_{line}.parquet'
        rp = HOME/f'rows_s1_{line}.parquet'; fp = HOME/f'partition_source/folds_{line}.parquet'
        assert w.sha(cp) == counts_report['outputs'][cp.name]
        assert w.sha(lp) == links_report['outputs'][lp.name]
        paths += [cp, lp, rp, fp]
        count = pd.read_parquet(cp); link = pd.read_parquet(lp)
        rows = pd.read_parquet(rp, columns=['row_id', 'year', 'T0_cents', 'exposure_model', 'exposure_calendar'])
        part = pd.read_parquet(fp, columns=['row_id', 'source_group', 'internal_validation'])
        assert count.row_id.is_unique and link.row_id.is_unique
        assert np.array_equal(count.row_id, rows.row_id) and np.array_equal(link.row_id, rows.row_id)
        assert np.array_equal(part.row_id, rows.row_id)
        assert np.array_equal(count.year, rows.year) and np.array_equal(link.year, rows.year)
        assert rows.year.isin([2021, 2022, 2023, 2024]).all()
        assert np.array_equal(count.T0_cents_total, rows.T0_cents)
        assert np.array_equal(count.exposure, rows.exposure_calendar)
        assert np.array_equal(np.round(rows.exposure_calendar, 4), rows.exposure_model)
        held = part.internal_validation.to_numpy(bool)
        assert set(part.loc[held, 'source_group']).isdisjoint(part.loc[~held, 'source_group'])
        perils = [x['peril'] for x in links_report['checks'] if x['line'] == line]
        assert len(perils) == len(set(perils))
        for peril in perils:
            n = count['N_'+peril].to_numpy(float); cost = count['T0_cents_'+peril].to_numpy(float)/100
            en = link['E_count_rkm_'+peril].to_numpy(float); ec = count['E_cost_'+peril].to_numpy(float)
            selected, ratio, y, weight = transformed_mark(n, cost, en, ec)
            assert np.allclose(ratio, link.loc[selected, 'mark_ratio_rkm_'+peril], rtol=0, atol=0)
            zeros = int(((n > 0)&(cost == 0)).sum())
            excluded_mark_no_information = (n > 0)&(ec == 0)
            assert not (cost[excluded_mark_no_information] > 0).any()
            train_mark = selected&~held; held_mark = selected&held
            train_n = n[selected][~held[selected]]; train_w = weight[~held[selected]]
            cell_ready = train_mark.sum() >= 100 and held_mark.sum() >= 20 and en[~held].sum() > 0
            ready &= cell_ready
            if len(y):
                direct = cost[selected]/n[selected]
                assert np.allclose(y*ratio, direct, rtol=2e-15, atol=1e-10)
            result = {'line': line, 'peril': peril, 'source_rows': len(rows), 'reported_accepted_claims': int(n.sum()),
                'training_positive_count_periods': int(train_mark.sum()), 'held_positive_count_periods': int(held_mark.sum()),
                'training_positive_groups': int(part.loc[train_mark, 'source_group'].nunique()),
                'held_positive_groups': int(part.loc[held_mark, 'source_group'].nunique()),
                'zero_cost_positive_count_periods': zeros,
                'zero_cost_marks_with_no_cost_link_information': int(excluded_mark_no_information.sum()),
                'ratio_positive_mark_quantiles': np.quantile(ratio, [0, .01, .5, .99, 1]).tolist(),
                'transformed_mark_max': float(y.max()), 'transformed_weight_sum': float(weight.sum()),
                'count_alpha_scale_train': float((~held).sum()/en[~held].sum()),
                'mark_alpha_scale_train': float(train_n.sum()/train_w.sum()),
                'source_only_preflight_support_pass': bool(cell_ready),
                'not_ultimate_frequency_identification': True}
            results.append(result)
    assert len(results) == 15
    sources = {w.rel(p): w.sha(p) for p in paths}
    report = {'author': 'Codex', 'utc': datetime.now(timezone.utc).isoformat(),
        'status': 'P27response_contract_ready_for_later_preregistration' if ready else 'P27response_contract_support_inadequate',
        'prior_recipes': novelty, 'by_line_peril': results, 'all_preflight_support_pass': bool(ready),
        'new_pairing': 'Bind saved current4year source/A1Sgroups to existing actual counts,RKM E_Nand frozen E_C. No new CDF/calendar integration or claim reassignment.',
        'count_contract': 'Poisson n/E_N with weights E_N; optimize on E_N>0. For nominal per-original-row mean-deviance penalty alpha, adjusted alpha=alpha*n_original_training_rows/sum(E_N). Zero-exposure zero-count input periods contribute zero likelihood and remain in the original row denominator.',
        'mark_contract': 'p1.5mean-deviance of cost/N with offset r=E_C/E_N. Response cost/(N*r), weights N*sqrt(r), adjusted alpha=nominal_alpha*sum(N)/sum(weights), fit on N>0,r>0; retain cost0.',
        'estimand_limits': ['Accepted reported events as of official cut; source-only RKM and empirical cost completion are frozen assumptions, not identified ultimate event counts.',
            'Count RKM support and cost empirical1095support differ; tail beyond observed support and reserve adequacy remain unknown.',
            'New-source count/mark model would change only source annual cost relativities; later whole target comparison still required.',
            'Support thresholds100train/20held are source-preflight feasibility, not target credibility or proof of private generalization.'],
        'sources': sources, 'new_source_fits': 0, 'new_C0_fits': 0, 'new_model_inference': 0,
        'new_target_scores': 0, 'new_future_prices': 0, 'new_submissions': 0,
        '2024_open': True, 'B00_all_alternatives_preserved': True, 'goal_achieved': False}
    dump(OUT/'report.json', report)
    next_unit = ('P28: preregister one standard main-effects Poisson/Tweedie1.5 count/mark source model per peril on the P27current4year paired-offset contract, if the exact prior-recipe review finds no equivalent current fit. '
        'Freeze source-only preprocessing/features/regularization normalization/iteration cap and an explicit source gate/cost before fitting. '
        'Use saved global source held groups, retain zero marks and all claim/period records, no Gamma deletion or E_cost-as-count substitution. '
        'Start with source inner fits only and save each checkpoint/gradient; no full refits or new target scoring unless its preregistered source criterion passes. '
        'Keep all previous FS/FSp/cycle8/cycle16adverses; no claim this is a first count/severity family. No new C0,2025prices or upload in source stage. '
        'No P25mask tuning; private robustness and all global/NBguards remain.' if ready else
        'Resolve only P27failed source-count/mark support/contract cells with legitimate existing evidence before any fit; do not pool perils, drop claims or change thresholds to force feasibility.')
    table = '\n'.join(f'| {x["line"]} | {x["peril"]} | {x["training_positive_count_periods"]} | {x["held_positive_count_periods"]} | {x["zero_cost_positive_count_periods"]} |' for x in results)
    text = '# P27: contrato separado de frecuencia y marca antes de otra familia\n\nCodex, '+report['utc']+'. '
    text += ('La revisión confirma que frecuencia/severidad ya se ensayó en ciclo3, ciclo8, ciclo16y FS/FSp; no se repetirán esas recetas ni se presenta la familia como nueva. '
        'La diferencia posible es un GLM de efectos principales sobre los cuatro años y grupos actuales, usando conjuntamente los vínculos de número y coste guardados. '
        'FS/FSpusa exposición de coste en frecuencia y marca observada: su producto puede ser un proxy coherente, pero sus piezas no identifican por sí solas frecuencia y severidad últimas.\n\n'
        'Se conciliaron las entradas de2.409.311periodos fuente con los recuentos existentes y los grupos A1S, sin reestimar una curva ni asignar siniestros de nuevo. '
        'La primera aserción comparaba por error exposición exacta con el predictor redondeado; el fallo y código se conservan. Se corrigió la columna de lectura a calendario y se comprobó el redondeo por separado, sin cambiar datos ni repetir el fixture matemático. '
        'La comprobación nueva se centra en respuesta/peso de la marca con offset, no repite calendarios o las auditorías terminadas de RKM.\n\n'
        '| Ramo | Peril | Periodos positivos entrenamiento | Retenidos | Marca cero retenida |\n|---|---|---:|---:|---:|\n'+table+'\n\n'
        'Para frecuencia, respuesta N/E_N y peso E_N. Para marca, r=E_C/E_N, respuesta C/(N*r) y peso N*sqrt(r), con potencia1,5. '
        'Una marca de coste cero y número positivo se conserva. La identidad de desviación con el offset se comprobó por otro método y se incluyó el cambio de escala de la penalización: '
        'alpha_f=alpha_nominal*n_filas/sum(E_N), alpha_m=alpha_nominal*sum(N)/sum(N*sqrt(r)). Aplicar los mismos números de alpha sin ese ajuste no sería la misma función penalizada.\n\n'
        +('Las15celdas cumplen el umbral de viabilidad fuente predefinido de100periodos positivos de entrenamiento y20retenidos. Esto no añade soporte emergente ni prueba generalización privada.' if ready else
        'Alguna celda incumple la viabilidad fuente; queda registrada y no se relaja ni se agrupa para forzar otra prueba.')
        +'\n\nLa separación depende de supuestos de observación y de los siniestros aceptados al corte. La cola última y suficiencia de reservas siguen sin identificarse. '
        'Se conserva el soporte RKM hasta1.361días frente al coste empírico condicionado a1.095; no se equiparan. Cero ajustes, inferencias, scores nuevos o envíos. '
        'B00/F3c y los adversos se conservan,2024abierto adaptativo.\n\nPróximo trabajo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'; '+w.rel(OUT/'synthetic_objective_identity.json')+'.\n')
    DOC.write_text(text, encoding='utf8'); body = OUT/'forum_resultado.md'; body.write_text(text, encoding='utf8')
    posted = subprocess.run([sys.executable, str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'), '--autor', 'Codex',
        '--id', 'COD-S2-20261026-PRIVADA-P27-FRECUENCIA-CONTRATO',
        '--asunto', 'P27: recetas previas preservadas y contrato número/marca con penalización explícita',
        '--cuerpo', str(body)], capture_output=True, text=True, encoding='utf8', check=True)
    receipt = {'author': 'Codex', 'utc': report['utc'], 'status': report['status'],
        'report': w.rel(OUT/'report.json'), 'report_sha256': w.sha(OUT/'report.json'), 'document': w.rel(DOC),
        'source_preflight_support_pass': bool(ready), 'new_source_fits': 0, 'new_C0_fits': 0,
        'new_model_inference': 0, 'new_target_scores': 0, 'new_submissions': 0,
        'forum': json.loads(posted.stdout), 'next_unit': next_unit, 'goal_achieved': False,
        '2024_open': True, 'B00_all_alternatives_preserved': True}
    dump(INDEX, receipt); archive = R/'privado'/('corte_P27_'+datetime.now(timezone.utc).strftime('%H%M%S%f')); archive.mkdir()
    w.update(R/'registro/semana2_mision_privada_actual.json', {'P27': receipt, 'next_unit': next_unit}, archive)
    w.update(R/'registro/semana2_mision017_fase2_actual.json', {'private_P27': receipt, 'next_unit': next_unit}, archive)
    state = ROOT/'Preparación/ESTADO_PROYECTO.json'; own = w.read(state)['week_2_mission017_phase2_20261025']
    own.update(private_P27=receipt, next_unit=next_unit); w.update(state, {'week_2_mission017_phase2_20261025': own}, archive)
    note = '\n\n## Privada P27: contrato número/marca sin ajustes, 26 de octubre de2026\n\nCodex, '+report['utc']+'. Recetas ciclo3/8/16y FS/FSpya existentes, conservadas. Nueva viabilidad: cuatro años/grupos actuales con E_N RKM y E_Cguardados; pesos y respuestas con offset y escala de penalización verificados sin ajuste. Soporte fuente de15celdas: '+str(bool(ready))+'. Cero inferencias/scores/envíos nuevos; no mejora privada establecida. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md', 'DECISIONES.md']: w.append(ROOT/'Preparación'/name, note, archive)
    w.update(ROOT/'RUTAS_PROYECTO.json', {'week_2_private_count_mark_contract_index': w.rel(INDEX), 'week_2_private_count_mark_contract_report': w.rel(DOC)}, archive)
    dump(OUT/'completion_receipt.json', receipt)
    print(json.dumps({'closed': True, 'source_support_pass': bool(ready), 'cells': len(results), 'new_fits': 0, 'forum': receipt['forum']}))


if __name__ == '__main__': main()
