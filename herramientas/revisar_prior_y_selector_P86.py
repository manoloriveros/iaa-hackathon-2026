"""Cierra la evidencia nueva P85 y cuantifica niveles fuente ya guardados."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import json
import math
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p86_frozen_source_contract',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
m=k.m;q=k.q;w=k.w;pd=k.pd;np=k.np;BASE=k.BASE
PREVIOUS=BASE/'P85_validacion_seleccion_GLM_20261027'
MAP=BASE/'P78_formas_riesgo_20261027/report.json'
ANCHORS=BASE/'P76_GLM_prior_dos_fuentes_preflight_20261027/source_anchors.json'
OUT=BASE/'P86_prior_y_selector_20261027'
PLAN=R/'registro/semana2_prior_selector_revision_plan.json';INDEX=R/'registro/semana2_prior_selector_revision_actual.json'
DOC=R/'docs/archivo/semana2/PRIVADA_P86_PRIOR_Y_SELECTOR.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert phase['P85_execution']['state']=='TERMINAL_SUCCESS'
    assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert w.read(PREVIOUS/'completion_receipt.json')['report_sha256']==w.sha(PREVIOUS/'report.json')
    paths=[Path(__file__),PREVIOUS/'report.json',PREVIOUS/'completion_receipt.json',PREVIOUS/'POOLED_prices.parquet',MAP,ANCHORS,
        BASE/'P82_validacion_GLM_bandas_negocio_20261027/POOLED_prices.parquet',R/'registro/semana2_mision_privada_plan_v1.json']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'NEWP85saved inner loss gaps/full price-vector identity and a new algebraic contrast of existing P78/P76level metadata. No repeated source/support audit, fits, model applications, new scores or resampling.',
        'configuration':{'selector':'Read ALL5common-alpha selections and all3saved inner objective totals. Relative gap=(loss_alpha-loss_1)/loss_1, no new evaluation or interval. Verify fullP85/P82rowprice arrays identity, not just equal reported metric.',
            'source_level_ratio':'For ALL3lines/5folds/2businesses, u=P65savedA1Scelllevel/P76developedA1Smonetaryanchor; v=P65savedT2bcelllevel; ratio=u/v. Expresses the difference between separate target-calibrated source levels and a common rescale of the source-onlyhalfprior, ignoring shapes/residuals.',
            'limits':'P65levels were fitted AFTERits history/NCBshapes. These ratios are NOTunshaped scale estimates, actual perrow source shares, optimal blend weights, causal attribution, or proof of transport/private benefit. Never copy these levels into a new unshaped learner.',
            'synthetic_algebra':'Two positive source rates, unequal multipliers u/v: a single common scale cannot match both coefficients for every source pair. Independent scalar arithmetic only, no simulated score or fitted parameter.'},
        'criterion':'All saved arrays/keys equal if algorithm picks existingalpha1; finite positive source ratios, algebra exact by two routes; retain all cells/losses and no new candidate selected.',
        'budget':{'new_real_fits':0,'new_model_applications':0,'new_CDF_fits':0,'new_scores':0,'new_resampling':0,'new2025inference':0,'new_submissions':0},
        'sources':{w.rel(path):w.sha(path) for path in paths},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P86 registra revisión sin entrenar de la evidencia nueva P85: los cinco selectores, sus tres objetivos internos y la identidad completa de precios con P82. Reutiliza mapas P78/anclas P76 para cuantificar, en TODOS los ámbitos, la razón entre niveles A1S/T2b después de calibración separada frente al prior fuente común. No repite auditorías ni aplicaciones de modelos. Los niveles P65 dependen de sus formas: no son óptimos sin formas, pesos por fila, causa probada o valores para copiar a otra receta. Fixture algebraico simple, cero fits/scores/remuestreo/2025/envíos. B00 preservado; 2024 abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P86registered_before_saved_selector_prior_review','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P86-PRIOR-PREVIO','P86: selector cerrado y contraste de escalas fuente, sin ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();m.check_sources(w.read(PLAN));assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    d=w.read(PREVIOUS/'report.json');selections=[]
    for a in d['primary_selections']:
        baseline=a['losses'][0];assert baseline>0
        selections.append({**a,'relative_gap_vs_alpha1':[(value-baseline)/baseline for value in a['losses']]})
    x=pd.read_parquet(PREVIOUS/'POOLED_prices.parquet');y=pd.read_parquet(BASE/'P82_validacion_GLM_bandas_negocio_20261027/POOLED_prices.parquet')
    assert x.equals(y),'Equal selected alpha is insufficient without full row/price identity'
    levels=w.read(MAP)['P65levels'];anchors=w.read(ANCHORS);records=[]
    for line in q.LINES:
        for outer in range(5):
            pair={z['component']:z for z in levels if z['line']==line and z['outer']==outer}
            for nb in ['0','1']:
                scale_a=pair['A1S']['cell_levels'][nb]/anchors[line]['source_annual_monetary_anchor'];scale_b=pair['T2b']['cell_levels'][nb]
                ratio=scale_a/scale_b;assert np.isfinite(ratio) and ratio>0
                records.append({'line':line,'outer':outer,'business':int(nb),'P65_A1S_level_over_source_anchor':scale_a,'P65_T2b_cell_level':scale_b,
                    'relative_level_ratio_not_rowweight':ratio})
    a=4.;b=1.;u=2.;v=1.;common=(u+v)/2
    one=.5*u*a+.5*v*b;two=common*(.5*a+.5*b)
    assert one!=two and math.fsum([.5*u*a,.5*v*b])==one
    dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P86saved_selector_identity_and_level_algebra_complete','all5_inner_selections':selections,'P85_P82_all_rows_and_columns_exact':True,
        'all30_source_level_cases':records,'synthetic_common_scale_is_not_separate_levels':True,'no_causal_or_private_gain_claim':True,**w.read(PLAN)['budget']})
    print(json.dumps({'complete':True,'P85_P82_prices_exact':True,'source_level_ratio_range':[min(z['relative_level_ratio_not_rowweight'] for z in records),max(z['relative_level_ratio_not_rowweight'] for z in records)],'new_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();m.check_sources(w.read(PLAN));d=w.read(OUT/'report.json')
    next_unit='P87: preflight a standard P82GLMwhose SOURCEprior is calibrated percomponent by ONLYown-training line/business scalar levels before fixedhalf mixture, instead of developed-only level anchors. No history/NCBshape pricebase or copied P65levels: learn the new unshaped levels on own train/q. Keep fields/bands/alpha1, old guards and source/report objects; register exact estimator/shrinkage/cost first, synthetic full poison/replay before any real fit. Not a proved cause or guaranteed gain; preserve all earlier models.'
    text='# P86: cierre del selector y escala del prior\n\nCodex, '+utc()+'. Los cinco selectores internos eligieron α=1. Se verificó que todas las filas, columnas y predicciones P85 coinciden exactamente con P82. No hay mejora predictiva nueva y no se amplía la cuadrícula.\n\n'
    text+='| Fold exterior | Aumento relativo del objetivo interno con α=0,1 | Con α=0,01 |\n|---|---:|---:|\n'
    for z in d['all5_inner_selections']:text+=f"| {z['outer']} | {z['relative_gap_vs_alpha1'][1]:.6%} | {z['relative_gap_vs_alpha1'][2]:.6%} |\n"
    values=[z['relative_level_ratio_not_rowweight'] for z in d['all30_source_level_cases']]
    text+=f'\nReutilizando los niveles guardados de P65 y las anclas monetarias fuente, la razón entre sus dos multiplicadores de nivel va de {min(values):.5f} a {max(values):.5f} en los 30 ámbitos ramo/fold/negocio. Se conservan todos. Es un contraste algebraico de contratos: calibrar cada señal antes de mezclarlas permite modificar sus niveles relativos; un único multiplicador común del prior fuente no reproduce en general esa operación.\n\n'
    text+='Los niveles P65 se ajustaron después de sus formas de historial/NCB. Las razones anteriores no son niveles óptimos para un modelo sin esas formas, pesos por fila ni una causa probada de la pérdida del GLM. No se copiarán a otra receta. La diferencia ya estaba declarada en P76; aquí se cuantifica con mapas existentes, sin repetir auditorías de fuente o soporte. Un fixture por dos cálculos escalares verificó la distinción algebraica.\n\n'
    text+='El siguiente mecanismo estándar propuesto calibra solo los niveles de cada componente con su propio entrenamiento antes de la mezcla fija y del GLM. Requiere contrato nuevo y flujo sintético; no implica ganancia esperada acreditada. No se añadieron ajustes, aplicaciones de modelos, scores, remuestreos, curvas, precios 2025 o envíos. B00, F3c y adversos conservados; 2024 es desarrollo adaptativo y persisten límites de transporte, información y valoración. Sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P86-PRIOR-RESULTADO','P86: selector sin mejora y contraste de niveles conservado')}
    archive=R/'privado'/('corte_P86_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P86'),(R/'registro/semana2_mision_privada_actual.json','P86')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P86=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P86: selector cerrado y niveles fuente\n\nCodex, '+receipt['utc']+'.P85/P82 idénticos en todas las filas; contraste de30niveles guardados, sin nuevos ajustes/aplicaciones/scores/envíos. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_prior_selector_review_index':w.rel(INDEX),'week_2_private_prior_selector_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
