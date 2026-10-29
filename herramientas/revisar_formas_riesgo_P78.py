"""Revisión nueva de elasticidades fuente y formas históricas, sin ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p78_current_direct_models',R/'herramientas/preparar_GLM_fuente_directa_P74.py')
r=importlib.util.module_from_spec(s);s.loader.exec_module(r)
k=r.p.k;m=r.m;q=r.q;w=r.w;pd=r.pd;np=r.np;BASE=r.BASE
MODELS={'P75':BASE/'P75_validacion_GLM_fuente_directa_20261027','P77':BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027'}
CONTROL=r.p.t.OUT;OUT=BASE/'P78_formas_riesgo_20261027'
PLAN=R/'registro/semana2_formas_riesgo_revision_plan.json';INDEX=R/'registro/semana2_formas_riesgo_revision_actual.json';DOC=R/'docs/archivo/semana2/PRIVADA_P78_FORMAS_RIESGO.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)
def quantiles(x):return {str(t):float(v) for t,v in zip([.01,.5,.99],np.quantile(x,[.01,.5,.99]))}


def fixture():
    # Two fixed base predictions, one group: distinguish estimands without claiming
    # that either finite-sample estimator has superior future expected performance.
    y=np.array([100.,100.]);mu=np.array([1.,100.]);ae=float(y.sum()/mu.sum())
    moment=math.fsum((y/np.sqrt(mu)).tolist())/math.fsum(np.sqrt(mu).tolist())
    scalar=float(np.sum(y/np.sqrt(mu))/np.sum(np.sqrt(mu)));assert math.isclose(moment,scalar,rel_tol=1e-15)
    loss_ae=float(m.e.unit(y,mu*ae).sum());loss_m=float(m.e.unit(y,mu*moment).sum());assert loss_m<loss_ae
    derivative=math.fsum((np.sqrt(mu*moment)-y/np.sqrt(mu*moment)).tolist());assert abs(derivative)<1e-12
    a=3.;b=7.;gamma_a=.2;gamma_b=-.1;epsilon=1e-5
    fa=lambda z:math.log(.5*z+.5*b)+gamma_a*math.log(z)+gamma_b*math.log(b)
    numerical=(fa(a*math.exp(epsilon))-fa(a*math.exp(-epsilon)))/(2*epsilon)
    analytic=a/(a+b)+gamma_a;assert math.isclose(analytic,numerical,abs_tol=2e-10)
    return {'synthetic_single_group_AE_scale':ae,'synthetic_single_group_Tweedie15_scale':moment,'synthetic_loss_AE':loss_ae,'synthetic_loss_metric':loss_m,
        'synthetic_metric_logscale_derivative':derivative,'source_elasticity_formula_finite_difference_match':True,
        'limit':'A/Eis a legitimate aggregate-moment estimator; different weighting/finite-sample optimum does not prove a model bug or private gain. No shrunk/normalized joint optimum claim.'}


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    paths=[Path(__file__),Path(k.core.b.__file__),Path(k.g.__file__),r.PLAN]
    for folder in MODELS.values():
        assert w.read(folder/'completion_receipt.json')['report_sha256']==w.sha(folder/'report.json')
        paths += [folder/'report.json',folder/'completion_receipt.json',folder/'POOLED_prices.parquet']
        for line in q.LINES:
            paths += [folder/f'{line}_{outer}/learning.json' for outer in range(5)]
    for line in q.LINES:
        paths += [r.p.t.t.OUT/f'input_{line}_0.parquet']+[CONTROL/f'{line}_{outer}/learning.json' for outer in range(5)]
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'NEWP75/P77source elasticities and all saved cells; P65rating-function map. No new model application, fit, price, loss score, resampling or repeated support/source audit.',
        'known_outcomes':'Both direct GLMwhole failures/intervals already known; all descriptions are adaptive, no independent validation.',
        'configuration':{'source_elasticity':'P75:1+beta_logT2b/scale and beta_logA1S/scale. P77:source share in monetaryhalfprior plus corresponding coefficient/scale. Conditional partial derivatives given all other supplied inputs, NOTcausal effects.',
            'rows':'All historical rows perline, every saved model/fold; do not select cells or fields. Quantiles1/50/99and negative fractions; no model forward call.',
            'rating_map':'Read ALLP65source-component NC B/prior factors/normalizers and celllevels from saved artifacts. Same old band definitions, no support recount or target labels used to learn a new coefficient.',
            'estimating_equations':'Static source says NC B/prior shapes use withinbusiness A/Erelative ratios, linearcredn/(n+300), price-weighted normalizers. Line/business/Gresidual stages already use Tweedie15moments, business/residual geometriccredK400/K300. DirectGLMuses log1pmain effects shared acrossbusiness, source slopes and ridge1.',
            'new_math_fixture':'One synthetic heterogeneous-base cohort demonstrates distinct A/Eand Tweedie15scale optima; compare raw unshrunk scalar deviance/derivative ONLY. No real group reestimation or threshold search.'},
        'criterion':'Exact model column maps/keys and monetaryprior derivative identity; independent synthetic scalar sums/derivative/finite difference. Differences motivate at most a separately registered standard estimator test, not promotion or calling A/Ewrong.',
        'budget':{'new_real_fits':0,'new_CDF_fits':0,'new_model_forward_calls':0,'new_scores':0,'new_resampling':0,'synthetic_closed_scale_estimates':2,'new2025inference':0,'new_submissions':0},
        'sources':{**w.read(r.PLAN)['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True}
    dump(PLAN,plan);body=OUT/'forum_previo.md'
    body.write_text('Codex. P78registra revisión nueva sin ajustar ni puntuar: elasticidades fuente condicionalesP75/P77deTODOSlosmodelos/filas/celdas guardadas y mapa de funcionesNCB/historia/negocioP65. Esos efectos son bandas por negocio con credibilidad; elGLMdirecto impone pendientes logcomunes. El códigoP65usa A/Esolo en formasNCB/prior; niveles línea/negocio y residuosYAusan momentosTweedie. Fixture sintético distingue los dos óptimos escalares sin declarar A/Eerróneo o mejora privada. No reestimar grupos reales, quitar campos o repetir soportes/suites; cero modelos forward/scores/2025/envíos. B00preservado,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P78registered_before_saved_risk_form_review','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P78-FORMAS-PREVIO','P78: formas de riesgo y ecuaciones distintas, sin ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    test=fixture();source_rows=[];rating=[];levels=[];cells={}
    for family,folder in MODELS.items():
        cells[family]=w.read(folder/'report.json')['results']['POOLED']['NOMINAL']['cells']
        for line in q.LINES:
            raw=r.frame_for(line,0)
            for outer in range(5):
                a=w.read(folder/f'{line}_{outer}/learning.json');names=a['preprocess']['numeric'];assert names[:2]==['log_annual_T2b_source','log_relative_A1S_source']
                gamma_b=a['coef'][0]/a['preprocess']['scale'][0];gamma_a=a['coef'][1]/a['preprocess']['scale'][1]
                if family=='P75':share_a=np.zeros(len(raw));share_b=np.ones(len(raw))
                else:
                    aa=raw.annual_A1S.to_numpy(float)*a['source_A1S_anchor']['source_annual_monetary_anchor'];bb=raw.annual_T2b.to_numpy(float)
                    share_a=aa/(aa+bb);share_b=bb/(aa+bb);assert np.allclose(share_a+share_b,1.,rtol=1e-15)
                e_a=share_a+gamma_a;e_b=share_b+gamma_b
                source_rows.append({'family':family,'line':line,'outer':outer,'coef_logA1S_original_units':gamma_a,'coef_logT2b_original_units':gamma_b,
                    'conditional_elasticity_A1S':quantiles(e_a),'conditional_elasticity_T2b':quantiles(e_b),'negative_A1S_fraction':float(np.mean(e_a<0)),
                    'negative_T2b_fraction':float(np.mean(e_b<0)),'joint_source_scale_elasticity':1+gamma_a+gamma_b})
    for line in q.LINES:
        for outer in range(5):
            a=w.read(CONTROL/f'{line}_{outer}/learning.json')
            for component,obj in a['components'].items():
                levels.append({'line':line,'outer':outer,'component':component,'line_level':obj['level'],'cell_levels':obj['cell_level'],
                    'estimator':'Tweedie15scale_moment','business_credibility':'positive_periods/(positive_periods+400), geometric'})
                for shape in obj['shape']:
                    rating.append({'line':line,'outer':outer,'component':component,'variable':shape['which'],'normalizers':shape['normalizers'],
                        'all_stored_factors':shape['factors'],'business_specific':True,'estimator':'relative_withinbusiness_aggregate_AE','credibility':'positive_periods/(positive_periods+300), linear'})
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P78saved_source_elasticities_and_rating_equation_map_complete','source_elasticities':source_rows,'all_held_cells':cells,
        'P65rating_functions':rating,'P65levels':levels,'synthetic_math':test,'already_metric_aligned':['line optimum','business levels','residual nuisance and factors'],
        'not_a_bug_or_gain_claim':True,**plan['budget']})
    print(json.dumps({'complete':True,'source_model_maps':len(source_rows),'rating_maps':len(rating),'negative_source_elasticity_scopes':sum(z['negative_A1S_fraction']>0 or z['negative_T2b_fraction']>0 for z in source_rows),'synthetic_math':test,'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    next_unit='P79: preflight SAMEP65structured calibrated half-source base with ONLYNCB/prior withinbusiness raw AEscale ratios replaced by relative Tweedie15scale moments. Keep bands, K300linearcred, normalization, K400business levels, source inputs/currentqand already-metric residual stages EXACT. Synthetic score/derivative/poison/full-flow checks first; no real fit until separate P80registration and all original gates. A/Eis not a proved bug; no guaranteed joint or private gain.'
    text='# P78: funciones de riesgo y estimadores\n\nCodex, '+utc()+'. Se mapearon los30GLMguardadosP75/P77en unidades originales y todas sus celdas; no se aplicaron modelos o puntuaron nuevos precios. Las elasticidades son derivadas parciales del modelo con otros inputs fijos, no efectos causales de cambiar riesgos. Se conservan todos los signos y rangos sin elegir campos.\n\n'
    text+='P65usa bandasNCB0/1-2/3-5/6-9/10+e historial0/1/2+, con relatividades separadas por negocio y credibilidad linealK300. LosGLMdirectos usan pendientes log1pcomunes a ambos negocios. La forma funcional y la regularización difieren, además del prior; no se atribuye una pérdida a una sola causa.\n\n'
    text+='EnP65solo las formasNCB/historia estiman razones A/Epor negocio. Los niveles de línea/negocio y los factores residuales YAusan momentosTweedie1,5yconservan su contrato. Un fixture sintético verificó por suma independiente y derivada que, con bases heterogéneas, el óptimo de escalaTweedie difiere de A/E. Eso no invalida A/Ecomo estimador de media agregada ni demuestra superioridad futura; la mezcla de credibilidad y normalización tampoco es una optimización conjunta.\n\n'
    text+='El cambio siguiente propuesto sustituye solo esa ecuación de forma, conservando toda la arquitecturaP65ycredibilidad. No se eliminaron grupos, estimaron escalas reales, hicieron nuevos ajustes/CDF/scores/remuestreos/2025/envíos. B00/F3cyalternativas conservados,2024abierto adaptativo, fuente2024/cola/reservas/maestros limitan transporte, sin revisión independiente.\n\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n'
    text+='\n## Elasticidades guardadas en unidades originales\n\nCada fila usa el modelo y fold indicados sobre las mismas covariables históricas por ramo. A1S y T2b cambian individualmente con los demás inputs fijos; las columnas contienen percentiles 1/50/99. No se predijo un precio nuevo.\n\n| Modelo | Ramo | Fold | A1S p1/p50/p99 | T2b p1/p50/p99 | Escala conjunta |\n|---|---|---:|---|---|---:|\n'
    for item in d['source_elasticities']:
        fmt=lambda key:'/'.join(f'{value:.5f}' for value in item[key].values())
        text+=f"| {item['family']} | {item['line']} | {item['outer']} | {fmt('conditional_elasticity_A1S')} | {fmt('conditional_elasticity_T2b')} | {item['joint_source_scale_elasticity']:.5f} |\n"
    test=d['synthetic_math']
    text+=f"\nFixture sintético, dos bases de 1 y 100 con costes de 100 y 100: A/E={test['synthetic_single_group_AE_scale']:.8f}; escala Tweedie={test['synthetic_single_group_Tweedie15_scale']:.8f}. La derivada de escala en el segundo valor es {test['synthetic_metric_logscale_derivative']:.3g}. No se usaron costes reales para esta comparación.\n"
    DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P78-FORMAS-RESULTADO','P78: diferencia de forma y momento, próxima prueba estándar acotada')}
    archive=R/'privado'/('corte_P78_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P78'),(R/'registro/semana2_mision_privada_actual.json','P78')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P78=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P78: formas de riesgo y momentos\n\nCodex, '+receipt['utc']+'.Mapas30GLM/P65yfixture sintético nuevos; cero ajuste real/modeloforward/scoring/remuestreo/envíos, sin causalidad o bug declarado. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_risk_form_review_index':w.rel(INDEX),'week_2_private_risk_form_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
