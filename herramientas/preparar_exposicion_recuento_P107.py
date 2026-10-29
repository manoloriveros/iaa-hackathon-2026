"""Conecta las curvas fuente de recuento existentes a periodos historicos estrictos."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import copy
import importlib.util
import json
import math
import sys

R = Path(__file__).resolve().parents[1]
ROOT = R.parents[1]
spec = importlib.util.spec_from_file_location('p107_previous', R/'herramientas/preparar_recuentos_destino_P106.py')
previous = importlib.util.module_from_spec(spec); spec.loader.exec_module(previous)
w = previous.w
np = previous.np
pd = previous.pd
BASE = previous.BASE
OUT = BASE/'P107_exposicion_recuento_20261027'
COUNTS = previous.OUT
OLD = BASE/'entradas_temporales_v1'
PLAN = R/'registro/semana2_exposicion_recuento_plan.json'
INDEX = R/'registro/semana2_exposicion_recuento_actual.json'
DOC = R/'docs/archivo/semana2/PRIVADA_P107_EXPOSICION_RECUENTO.md'
CUT = pd.Timestamp('2024-12-31')
PERILS = {'motor': ['own_damage', 'third_party_prop', 'bodily_injury', 'theft', 'glass_hail'],
    'buildings': ['storm', 'flood', 'escape_of_water', 'subsidence', 'fire', 'accidental_damage'],
    'contents': ['theft', 'escape_of_water', 'accidental_damage', 'flood']}
utc = previous.utc
dump = previous.dump


def count_curve(model):
    # Only these frozen count fields are consumed. Cost curves, marks and prices
    # are deliberately outside this adapter's inputs.
    support = np.asarray(model['delay_days'], dtype=float)
    curve = np.asarray(model['count_cdf'], dtype=float)
    assert support.ndim == 1 and len(support) > 0 and len(support) == len(curve)
    assert np.isfinite(support).all() and (support >= 0).all()
    assert np.array_equal(support, np.floor(support)) and (np.diff(support) > 0).all()
    assert np.isfinite(curve).all() and (curve >= 0).all() and (curve <= 1).all()
    assert (np.diff(curve) >= 0).all() and curve[-1] == 1.
    return support.astype('int64'), curve


def exposure(periods, model):
    assert periods.row_id.is_unique
    assert periods.year.isin([2023, 2024]).all()
    if 'is_test' in periods:
        assert not periods.is_test.any()
    if 'market' in periods:
        assert periods.market.eq('emerging').all()
    start = pd.to_datetime(periods.period_start, errors='raise')
    end = pd.to_datetime(periods.period_end, errors='raise')
    assert start.notna().all() and end.notna().all()
    assert start.eq(start.dt.normalize()).all() and end.eq(end.dt.normalize()).all()
    hi = (CUT-start).dt.days.to_numpy('int64')
    lo = (CUT-end).dt.days.to_numpy('int64')
    assert (lo >= 0).all() and (hi >= lo).all()
    days = hi-lo+1
    assert np.allclose(days/365., periods.exposure_calendar.to_numpy(float), rtol=1e-12, atol=1e-14)
    support, curve = count_curve(model)
    ages = np.arange(int(hi.max(initial=0))+1)
    index = np.searchsorted(support, ages, side='right')-1
    daily = np.where(index >= 0, curve[np.maximum(index, 0)], 0.)
    accumulated = np.r_[0., np.cumsum(daily)]
    en = (accumulated[hi+1]-accumulated[lo])/365.
    q = en/(days/365.)
    assert np.isfinite(en).all() and (en >= 0).all()
    assert (q >= -1e-12).all() and (q <= 1+1e-12).all()
    return en, q


def count_likelihood_domain(n, en):
    n = np.asarray(n, dtype=float); en = np.asarray(en, dtype=float)
    assert n.shape == en.shape and np.isfinite(n).all() and np.isfinite(en).all()
    assert (n >= 0).all() and np.array_equal(n, np.floor(n)) and (en >= 0).all()
    assert not ((n > 0) & (en == 0)).any()
    return en > 0


def synthetic():
    model = {'delay_days': [2, 9, 30], 'count_cdf': [.25, .7, 1.], 'cost_cdf': 'NOT_AN_INPUT'}
    f = pd.DataFrame({'row_id': ['a','b','c'], 'year': [2024,2024,2023],
        'period_start': pd.to_datetime(['2024-12-31','2024-12-16','2023-01-01']),
        'period_end': pd.to_datetime(['2024-12-31','2024-12-30','2023-12-31']),
        'T0': [0., 1e9, 12.], 'n_accepted': [0,2,1], 'group_id': ['g0','g1','g2'], 'fold': [0,1,2]})
    f['exposure_calendar'] = ((f.period_end-f.period_start).dt.days+1)/365.
    en, q = exposure(f, model)
    # Separate scalar integration over every actual insured date, without the
    # vector searchsorted or cumulative-sum implementation above.
    direct = []
    for row in f.itertuples():
        terms = []
        for date in pd.date_range(row.period_start, row.period_end):
            age = (CUT-date).days
            value = 0.
            for day, probability in zip(model['delay_days'], model['count_cdf']):
                if day <= age: value = probability
            terms.append(value)
        direct.append(math.fsum(terms)/365.)
    assert np.allclose(en, direct, rtol=0, atol=3e-15)
    assert np.array_equal(count_likelihood_domain(f.n_accepted, en), [False,True,True])
    changed = f.copy()
    for name in ['T0','n_accepted','group_id','fold']:
        changed[name] = 'INVALID_PROTECTED_LABEL_OR_FOLD'
    poisoned_model = copy.deepcopy(model)
    poisoned_model['cost_cdf'] = {'corrupt_cost': object()}
    poisoned_model['mean_net_mark'] = object()
    assert np.array_equal(exposure(changed, poisoned_model)[0], en)
    assert np.array_equal(exposure(f.iloc[::-1], model)[0][::-1], en)
    assert np.array_equal(exposure(f.iloc[[1]], model)[0], en[[1]])
    bads = {}
    for label, field, value in [('future_year','year',2025),('test','is_test',True),('market','market','developed'),
        ('future_end','period_end','2025-01-01'),('nonmidnight','period_start','2024-12-31 12:00:00'),
        ('calendar','exposure_calendar',9.)]:
        bad = f.copy(); bad[field] = bad[field].astype('object') if field in bad else None
        bad.loc[0,field] = value
        if field == 'is_test': bad.loc[1:,field] = False
        if field == 'market': bad.loc[1:,field] = 'emerging'
        bads[label] = bad
    bads['duplicate'] = pd.concat([f,f.iloc[[0]]],ignore_index=True)
    for label, bad in bads.items():
        try: exposure(bad, model)
        except (AssertionError, ValueError, TypeError): pass
        else: raise AssertionError('Bad period accepted: '+label)
    for bad in [{'delay_days':[9,2,30],'count_cdf':[.2,.7,1.]},
        {'delay_days':[2,9,30],'count_cdf':[.7,.2,1.]},
        {'delay_days':[2,9,30],'count_cdf':[.2,.7,.9]}]:
        try: exposure(f,bad)
        except AssertionError: pass
        else: raise AssertionError('Bad count curve accepted')
    for n, e in [([1],[0]),([.5],[1]),([-1],[1]),([0],[-1])]:
        try: count_likelihood_domain(n,e)
        except AssertionError: pass
        else: raise AssertionError('Bad count likelihood domain accepted')
    return {'author':'Codex','utc':utc(),'scalar_calendar_matches_vector':True,
        'costs_counts_fold_and_group_not_inputs_to_fixed_count_exposure':True,
        'permutation_subset_projectivity_exact':True,'zero_count_zero_exposure_excluded_with_zero_likelihood':True,
        'positive_count_zero_exposure_rejected':True,'adverse_period_inputs_rejected':list(bads),
        'adverse_curves_rejected':3,'adverse_likelihood_inputs_rejected':4,
        'real_CDF_model_fits':0,'new_source_or_target_rates':0}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase = w.read(R/'registro/semana2_mision017_fase2_actual.json')
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    p106 = w.read(previous.INDEX)
    assert p106['status'] == 'P106existing_observed_counts_aligned_no_frequency_exposure_or_model'
    paths = [Path(__file__), Path(previous.__file__), previous.INDEX, COUNTS/'report.json',
        BASE/'recuentos_fuente2024_rkm_reuse_v1/report.json',
        BASE/'P27_contrato_frecuencia_20261026/report.json', BASE/'P29_fuente_frecuencia_completa_20261026/report.json',
        R/'src/semana2/variables_ultimo.py', R/'herramientas/reutilizar_reporte_fuente2024.py',
        R/'registro/semana2_prioridad_privada_reafirmada_20261027.json']
    paths += [COUNTS/f'counts_{line}.parquet' for line in PERILS]
    paths += [OLD/f'source_reporting_{line}.json' for line in PERILS]
    OUT.mkdir()
    plan = {'author':'Codex','utc':utc(),
        'need':'P106 has accepted-event counts, but its destination path lacks event-count exposure. Native FSp and costq cannot substitute for the paired Poisson exposure.',
        'decision':'Reuse the 15 already validated source-only daily unit-event RKM count objects from source2021-2023 at valuation2024-12-31. No new count CDF fit and no target label may enter this exposure adapter. This simpler source-fixed alternative precedes any need for scope-specific count curves.',
        'configuration':{'destination_years':[2023,2024],'market':'emerging','test_excluded':True,
            'source_count_cohort':[2021,2022,2023],'valuation':'2024-12-31','strata':'line/peril,15',
            'calendar':'Inclusive insured daily sum of frozen countCDF(CUT-day)/365, exactly canonical exposure.',
            'count_definition':'Accepted assigned reported events, including accepted cost0; unchanged P106 definitions.',
            'cost_completion':'Unchanged cost targets and existing separate cost completion. No cost curve/cap borrowed for counts.',
            'tail':'Frozen original F(max observed delay)=1, unobserved tail not identified; no extra mass or retuning.',
            'domain':'No count model here. Later count likelihood must allow N=0,E_N=0 with zero contribution and reject N>0,E_N=0.',
            'scope':'Shared source-only object is intentionally invariant across every outer/inner target group. Target keys/dates are needed to quote exposure; target labels/group/fold cannot alter the object.'},
        'criterion':'Strict year/key/calendar validation; daily scalar synthetic integration, label/cost poisoning, subset/permutation; invalid curve/domain cases reject. All109296 canonical rows unchanged, E_count per15perils in[0,calendar]. No comparison score or model selection.',
        'limits':['Source-to-target delay transport remains an assumption, not empirical target validation.',
            'Retrospective snapshot2024-12-31 is not an inception-available label snapshot.',
            'No ultimate frequency identified, no private score inferred; previous P30 and other adverse source recipes retained.'],
        'budget':{'new_model_fits':0,'new_CDF_fits':0,'new_source_rate_inference':0,'new_scores':0,'new2025inference':0,'new_submissions':0},
        'sources':{w.rel(path):w.sha(path) for path in paths},'B00_all_alternatives_preserved':True,'2024_open':True,'goal_achieved':False}
    dump(PLAN,plan)
    text='Codex. P107 registra antes de calcular entradas la exposición por número de avisos. Se reutilizan las15curvas diarias RKM de recuento fuente2021-2023ya conservadas y verificadas por P27; no se ajusta otra CDF. No entra ninguna etiqueta destino, coste, grupo o fold en esas curvas. Se suma la completitud sobre cada día asegurado de las109296filas históricas2023/2024, con calendario exacto y rechazos de test/año/casos imposibles. La prueba sintética comprobará la suma escalar, la invariancia a etiquetas/costes y a subconjuntos/orden, y el dominio de exposición cero. La exposición de coste sigue separada. La hipótesis de transporte de demoras entre mercados, la cola no observada y el corte retrospectivo siguen abiertos. No se inferirán tasas, precios o scores, ni se promoverá un modelo. B00y alternativas preservados; prioridad privada. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN)
    body=OUT/'forum_previo.md';body.write_text(text,encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P107registered_before_fixed_count_exposure',
        'plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':previous.post(body,'COD-S2-20261027-PRIVADA-P107-EXPOSICION-PREVIO','P107: exposición de recuento fuente fija, sin otra CDF')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    plan=w.read(PLAN);previous.check_sources(plan)
    dump(OUT/'synthetic.json',synthetic())
    records=[];outputs={};total=0
    for line,perils in PERILS.items():
        source=w.read(OLD/f'source_reporting_{line}.json')
        assert source['years']==[2021,2022,2023] and set(source['models'])==set(perils)
        f=pd.read_parquet(COUNTS/f'counts_{line}.parquet');assert f.line.eq(line).all()
        out=f.copy();newcols=[]
        for peril in perils:
            en,q=exposure(f,source['models'][peril])
            out[f'E_count_source_{peril}']=en;out[f'q_count_source_{peril}']=q
            newcols += [f'E_count_source_{peril}',f'q_count_source_{peril}']
            for year in [2023,2024]:
                selected=f.year.eq(year).to_numpy()
                records.append({'line':line,'peril':peril,'year':year,'rows':int(selected.sum()),
                    'E_count_sum':float(en[selected].sum()),'q_count_min':float(q[selected].min()),
                    'q_count_max':float(q[selected].max()),'zero_count_exposure_rows':int((en[selected]==0).sum()),
                    'source_count_events':int(source['models'][peril]['n'])})
        assert out.drop(columns=newcols).equals(f)
        path=OUT/f'count_exposure_{line}.parquet';out.to_parquet(path,index=False)
        outputs[w.rel(path)]=w.sha(path);total+=len(out)
    assert total==109296
    previous.check_sources(plan)
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P107fixed_source_count_exposure_connected_no_price_model',
        'rows':total,'records':records,'outputs':outputs,'canonical_counts_costs_calendar_groups_unchanged':True,
        'source_count_objects_reused':15,'target_learning_calls':0,'scope_specific_count_CDF_fits':0,
        'paired_source_frequency_mark_views_exported':False,**plan['budget']})
    print(json.dumps({'rows':total,'source_count_objects_reused':15,'new_fits':0,'new_scores':0}))


def close():
    plan=w.read(PLAN);previous.check_sources(plan);report=w.read(OUT/'report.json')
    assert all(w.sha(ROOT/path)==sha for path,sha in report['outputs'].items())
    next_unit='P108: register and export explicit per-peril historical P29 paired frequency/mark source rates from already fitted source-only GLM objects, not native FSp proxy. Mask historical2023/2024 before source inference, preserve canonical keys and preprocessors, replay sum(lambda*mark) against saved P29 historical aggregate without refit. Then freeze complete target Poisson-cost recipe and synthetic flow before any new model fit; source-fixed count delay transport and previous P30 failures remain.'
    text='# P107: exposición por número conectada\n\nCodex, '+utc()+'.\n\nLas109296filas históricas2023/2024conservan los recuentos, costes, calendario, grupos y folds de P106. Se añadieron las exposiciones de número para15estratos ramo/peril, calculadas con las curvas fuente de recuento ya existentes. No se ajustó una CDF nueva ni se repitió su auditoría histórica; el adaptador solo consume los soportes y probabilidades de número congelados. Ninguna etiqueta de destino entra en esas curvas, por lo que no se precisa reaprenderlas dentro de los folds.\n\nLa suma vectorial de cada día asegurado coincide con una enumeración escalar sintética. La alteración de costes, recuentos, grupos y folds no cambia la exposición; tampoco el orden o la consulta por subconjuntos. Se rechazaron claves duplicadas, test,2025, otro mercado, calendario/fechas imposibles, curvas inválidas y el caso Npositivo/Ecero. Ncero/Ecero tiene contribución nula a una futura verosimilitud y no debe recibir un denominador artificial. Estos son controles de entradas, sin puntuación predictiva.\n\nSe mantiene explícita la hipótesis de transporte de demoras fuente-destino. El cierre F(maxretraso)=1no identifica cola no observada y el corte2024-12-31es retrospectivo. La exposición de coste sigue separada, sin reetiquetar qcoste como exposición de número. Aún faltan las tasas fuente pareadas explícitas y la receta completa de destino; esta conexión no demuestra mejora privada ni frecuencia última identificada. Se conservan P30y demás resultados adversos. B00y alternativas intactos,2024abierto adaptativo, sin revisión profesional independiente.\n\nCero ajuste de precios/CDF, inferencia de tasas, scores,2025o envíos. Próximo: '+next_unit+'\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':report['status'],'report':w.rel(OUT/'report.json'),
        'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'outputs':report['outputs'],
        'source_count_objects_reused':15,'count_reporting_exposure_implemented':True,
        'paired_source_frequency_mark_views_exported':False,**plan['budget'],'next_unit':next_unit,
        '2024_open':True,'goal_achieved':False,
        'forum':previous.post(body,'COD-S2-20261027-PRIVADA-P107-EXPOSICION-RESULTADO','P107: exposición de número conectada, sin tasas o precios nuevos')}
    cut=R/'privado'/('corte_P107_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));cut.mkdir()
    w.update(INDEX,receipt,cut)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P107'),(R/'registro/semana2_mision_privada_actual.json','P107')]:
        w.update(path,{key:receipt,'next_unit':next_unit},cut)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json'
    own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P107=receipt,next_unit=next_unit)
    w.update(state,{'week_2_mission017_phase2_20261025':own},cut)
    note='\n\n## Privada P107: exposición de número\n\nCodex, '+receipt['utc']+'. Conexión de109296filas a15curvas fuente de número existentes, sin ajuste o score. Suma escalar/sintética y controles adversos pasaron; transporte de demoras entre mercados y cola siguen sin validar. Exposición de coste separada, tasas pareadas y receta destino pendientes. Informe '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,cut)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_target_count_exposure_index':w.rel(INDEX),
        'week_2_private_target_count_exposure_report':w.rel(DOC)},cut)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8')
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('mode',choices=['register','synthetic','run','close'])
    mode=parser.parse_args().mode
    if mode=='synthetic':print(json.dumps(synthetic()))
    else:{'register':register,'run':run,'close':close}[mode]()
