"""Curvatura y contrastes del GLM P82 guardado, sin volver a ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import importlib.util
import argparse
import math
import inspect
import json
import sys

R=Path(__file__).resolve().parents[1];ROOT=R.parents[1]
s=importlib.util.spec_from_file_location('p83_saved_band_kernel',R/'herramientas/preparar_GLM_bandas_negocio_P81.py')
k=importlib.util.module_from_spec(s);s.loader.exec_module(k)
m=k.m;q=k.q;w=k.w;np=k.np;pd=k.pd;BASE=k.BASE
MODELS=BASE/'P82_validacion_GLM_bandas_negocio_20261027'
CONTROL=BASE/'P65_validacion_reporte_por_ramo_20261027'
OUT=BASE/'P83_penalizacion_guardada_20261027'
PLAN=R/'registro/semana2_penalizacion_guardada_revision_plan.json';INDEX=R/'registro/semana2_penalizacion_guardada_revision_actual.json'
DOC=R/'docs/semana2/PRIVADA_P83_PENALIZACION_Y_BANDAS.md'


def utc():return datetime.now(timezone.utc).isoformat()
def dump(path,value):return q.dump(path,value)


def curvature(x,y,base,coef,intercept):
    relative=np.exp(x@coef+intercept);weight=np.sqrt(base);target=y/base
    # Actual normalized weighted half-Tweedie deviance used by saved sklearnGLM.
    row=weight*(np.sqrt(relative)+target/np.sqrt(relative))/(2*weight.sum())
    assert np.isfinite(row).all() and (row>0).all()
    return relative,row,x.T@(row[:,None]*x)


def synthetic():
    x=np.array([[0.,1.,-1.],[1.,0.,.5],[0.,1.,2.],[1.,0.,-.5]])
    y=np.array([0.,150.,20.,0.]);base=np.array([10.,100.,40.,30.]);coef=np.array([.1,-.2,.03]);intercept=-.4;alpha=1.
    relative,row,hessian=curvature(x,y,base,coef,intercept)
    def gradient(beta):
        pred=np.exp(x@beta+intercept);weight=np.sqrt(base);target=y/base
        score=weight*(np.sqrt(pred)-target/np.sqrt(pred))/weight.sum()
        return x.T@score+alpha*beta
    step=1e-5;differences=[]
    for j in range(x.shape[1]):
        direction=np.zeros(x.shape[1]);direction[j]=step
        derivative=(gradient(coef+direction)-gradient(coef-direction))/(2*step)
        expected=hessian[:,j]+alpha*np.eye(x.shape[1])[:,j]
        assert np.allclose(derivative,expected,rtol=2e-9,atol=2e-10);differences.append(float(np.max(np.abs(derivative-expected))))
    return {'synthetic_regularized_gradient_Hessian_finite_difference_match':True,'max_finite_difference_error':max(differences),
        'limit':'Observed local curvature includes target and current fit; diagonal penalty fractions are NOTactual coefficient shrinkage, case-deletion influence, causal effects, a score gain or a tuning result.'}


def rating_contrasts(artifact):
    columns=artifact['preprocess']['columns'];coefs=dict(zip(columns,artifact['coef']));records=[]
    for field in ['history_business_band','ncb_business_band']:
        for business in [0,1]:
            chosen={name.split('=',1)[1].split('|',1)[1]:value for name,value in coefs.items() if name.startswith(f'{field}={business}|')}
            if chosen:
                values=list(chosen.values());records.append({'field':field,'business':business,'all_logcoefficients':chosen,'largest_to_smallest_rating_factor':math.exp(max(values)-min(values))})
    return records


def register():
    assert not OUT.exists() and not PLAN.exists() and not INDEX.exists()
    phase=w.read(R/'registro/semana2_mision017_fase2_actual.json');assert not phase.get('active_jobs') and not phase.get('active_execution')
    assert phase['P82_execution']['state']=='TERMINAL_SUCCESS'
    assert w.read(MODELS/'completion_receipt.json')['report_sha256']==w.sha(MODELS/'report.json')
    parent=w.read(k.PLAN);m.check_sources(parent)
    paths=[Path(__file__),Path(k.__file__),Path(inspect.getfile(k.r.TweedieRegressor)),k.PLAN,MODELS/'report.json',MODELS/'completion_receipt.json',
        BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027/report.json',CONTROL/'report.json']
    for line in q.LINES:
        for outer in range(5):paths += [MODELS/f'{line}_{outer}/learning.json',CONTROL/f'{line}_{outer}/learning.json',k.r.p.t.t.OUT/f'input_{line}_{outer}.parquet']
    OUT.mkdir();plan={'author':'Codex','utc':utc(),'scope':'Only NEWP82saved band coefficients/local training-curvature equations and all saved P82/P77/P65held cells. No fitting, selection, new held score/bootstrap or old source/report replay.',
        'need':'P82band representation still fails despite convergence and protected whole evaluation. Quantify the actual fixed ridge penalty against likelihood curvature instead of attributing failures to signs, groups, scope offsets absent from this model or insufficient arbitrary capacity.',
        'configuration':{'models':'ALL15saved P82models, all original train rows after existing held selector; no field/fold/line chosen by effect.',
            'normalized_objective':'sum(sqrt(b)*D15(y/b,exp(Xbeta+a)))/(2*sum(sqrt(b))) + alpha*||beta||^2/2, alpha=1, interceptunpenalized.',
            'observed_data_curvature':'row h_i=sqrt(b_i)*(sqrt(r_i)+(y_i/b_i)/sqrt(r_i))/(2*sum sqrt(b)). H=X.T diag(h)X. Scalar diagonals independently summed for ALLcolumns.',
            'intercept_profiled_curvature':'Center Xby hweights; Hprofile=Xcenter.T diag(h)Xcenter. Eigenvalues/trace sum(lambda/(lambda+alpha))are LOCALcurvature diagnostics only, no formal degrees-of-freedom or case-deletion claim.',
            'per_column':'All stored coefficients, train mean/std/prevalence, observed data Hjj, alpha/(alpha+Hjj)diagonal fraction. The fraction is NOTactual shrinkage in a correlated multivariate fit.',
            'band_contrasts':'ALLbusiness-specific P82history/NCBcoefficients and max/minfactor contrasts, alongside ALLsaved P65component shape contrasts. Different architectures, not a causal decomposition.',
            'held_cells':'Copy existing P82/P77/P65reports verbatim, no new price/score or paired interval.'},
        'criterion':'Pin actual saved model/input/library hashes; one synthetic observed-Hessian/regularized-gradient finite-difference fixture; all real diagonals by scalar sums; nonnegative profiled eigenvalues within numerical tolerance. No hyperparameter tested/selected.',
        'budget':{'new_real_fits':0,'new_source_fits':0,'new_CDF_fits':0,'new_diagnostic_training_mean_vectors':15,'new_Hessians':15,'new_held_scores':0,'new_resampling':0,'new2025inference':0,'new_submissions':0},
        'future_limit':'No direct alpha/field/band rescue from outer outcomes. Any finite training-only selection algorithm must be separately justified and preregistered, freeze grid/cost/criterion and exclude each inner held group from ALLpreprocessing/reporting/selection before unchanged outer evaluation.',
        'sources':{**parent['sources'],**{w.rel(path):w.sha(path) for path in paths}},'2024_open':True,'B00_all_alternatives_preserved':True,'goal_achieved':False}
    dump(PLAN,plan);body=OUT/'forum_previo.md';body.write_text('Codex. P83registra revisión nueva de TODOSlos15GLMguardadosP82, sin ajustar ni remuestrear. Cuantificaré coeficientes/contrastes por negocio, curvatura observada de entrenamiento y penalizaciónalpha1con su normalización real; diagonales por otra suma y fixtureHessiano/gradiente sintético.15vectores medios diagnósticos SOLOentrenamiento, cero nuevos scores retenidos/2025/envíos. Fracción diagonal no es contracción real multivariable, influencia por eliminación, causa de pérdida o permiso para elegiralpha. Copia de celdas guardadasP82/P77/P65sin nuevos precios. Cualquier selección futura necesitaría algoritmo protegido interno completo y registro separado. B00/adversos conservados,2024abierto adaptativo. Plan '+w.rel(PLAN)+' SHA '+w.sha(PLAN),encoding='utf8')
    reg={'author':'Codex','utc':utc(),'status':'P83registered_before_saved_penalty_review','plan':w.rel(PLAN),'plan_sha256':w.sha(PLAN),
        'forum':q.post(body,'COD-S2-20261027-PRIVADA-P83-PENALIZACION-PREVIO','P83: coeficientes y curvatura de penalización guardados, sin ajustar')}
    dump(OUT/'registration.json',reg);dump(INDEX,reg);print(json.dumps(reg))


def run():
    assert not (OUT/'report.json').exists();plan=w.read(PLAN);m.check_sources(plan);assert w.read(OUT/'registration.json')['plan_sha256']==w.sha(PLAN)
    fixture=synthetic();records=[];structured=[];held={}
    k.setup()
    for line in q.LINES:
        for outer in range(5):
            f=k.frame_for(line,outer);train=f.loc[~f.is_held].copy();artifact=w.read(MODELS/f'{line}_{outer}/learning.json')
            assert artifact['fit_row_ids_digest']==m.p.b.digest(sorted(train.row_id))
            x,_=k.design(train,line,artifact['preprocess']);y=train.T0.to_numpy(float)
            base=k.b.ultimate_source_offset(train)*train.q_paired.to_numpy(float)
            relative,row,H=curvature(x,y,base,np.asarray(artifact['coef']),artifact['intercept']);alpha=artifact['parameters']['alpha'];assert alpha==1
            diagonals=[]
            for j in range(x.shape[1]):
                scalar=math.fsum((row*x[:,j]*x[:,j]).tolist());assert math.isclose(scalar,H[j,j],rel_tol=4e-13,abs_tol=2e-13);diagonals.append(scalar)
            center=np.average(x,axis=0,weights=row);xc=x-center;profile=xc.T@(row[:,None]*xc)
            eigen=np.linalg.eigvalsh(profile);assert eigen.min()>=-1e-10;positive=np.maximum(eigen,0)
            columns=[]
            for j,name in enumerate(artifact['preprocess']['columns']):
                kind='business_band' if name.startswith(('history_business_band=','ncb_business_band=')) else ('categorical' if '=' in name else 'numeric_or_missing')
                columns.append({'name':name,'kind':kind,'coef':artifact['coef'][j],'training_mean':float(x[:,j].mean()),'training_std':float(x[:,j].std()),
                    'Hjj_data':diagonals[j],'diagonal_penalty_fraction_not_actual_shrinkage':alpha/(alpha+diagonals[j])})
            records.append({'line':line,'outer':outer,'rows':len(train),'intercept':artifact['intercept'],'all_columns':columns,'band_contrasts':rating_contrasts(artifact),
                'profiled_data_eigenvalues':eigen.tolist(),'local_penalized_curvature_trace_not_formal_df':float(np.sum(positive/(positive+alpha))),
                'scalar_diagonals_all_match':True,'new_diagnostic_training_mean_vectors':1,'new_real_fits':0})
            a=w.read(CONTROL/f'{line}_{outer}/learning.json')
            for name,component in a['components'].items():
                for shape in component['shape']:
                    for business in [0,1]:
                        selected={key.split('|',1)[1]:value for key,value in shape['factors'].items() if key.startswith(str(business)+'|')}
                        values=list(selected.values());structured.append({'line':line,'outer':outer,'component':name,'variable':shape['which'],'business':business,
                            'all_factors':selected,'largest_to_smallest_rating_factor':max(values)/min(values)})
    for name,folder in [('P82',MODELS),('P77',BASE/'P77_validacion_GLM_prior_dos_fuentes_20261027'),('P65',CONTROL)]:held[name]=w.read(folder/'report.json')['results']['POOLED']['NOMINAL']['cells']
    m.check_sources(plan);dump(OUT/'report.json',{'author':'Codex','utc':utc(),'status':'P83saved_band_penalty_curvature_review_complete','records':records,'all_P65shape_contrasts':structured,
        'all_saved_held_cells':held,'synthetic_math':fixture,'no_causal_or_private_gain_claim':True,**plan['budget']})
    values=[z['diagonal_penalty_fraction_not_actual_shrinkage'] for a in records for z in a['all_columns'] if z['kind']=='business_band']
    print(json.dumps({'complete':True,'models':len(records),'band_diagonal_penalty_fraction_range':[min(values),max(values)],'local_curvature_trace_range':[min(z['local_penalized_curvature_trace_not_formal_df'] for z in records),max(z['local_penalized_curvature_trace_not_formal_df'] for z in records)],'new_real_fits':0}))


def close():
    assert not (OUT/'completion_receipt.json').exists();d=w.read(OUT/'report.json');m.check_sources(w.read(PLAN))
    values=[z['diagonal_penalty_fraction_not_actual_shrinkage'] for a in d['records'] for z in a['all_columns'] if z['kind']=='business_band']
    next_unit='P84: design and synthetic-preflight a finite TRAINING-ONLYregularization-selection algorithm for SAMEP82standardGLM, not an outer-score alpha rescue. Inspect/reuse only valid P67own-inner report objects/keys after numeric binding, no protected outerqborrowed. Freeze grid, exact selector, tie rule/cost/criteria and whole poison/replay before any real fit; unchanged outer/private guards. If inner inputs lack required provenance, prepare them without fitting rather than silently reuse.'
    text='# P83: penalización y bandas del GLM guardado\n\nCodex, '+utc()+'. Se revisaron los15GLMP82guardados y todas sus columnas, con15vectores medios diagnósticos de entrenamiento y sin ajustar modelos o generar scores retenidos. Se conservaron todos los contrastes/celdas, sin elegir campos o ramos.\n\n'
    text+=f"En las bandas por negocio, alpha/(alpha+Hjj)oscila entre{min(values):.6f}y{max(values):.6f}. Es una fracción diagonal de curvatura observada, no la contracción real de un coeficiente en un modelo correlacionado. La regularización numérica y categórica actúa sobre columnas con escalas distintas; el código estandariza las numéricas y deja indicadores0/1. La evidencia cuantifica esa ecuación, sin demostrar que causó la pérdida o cuálalpha sería mejor.\n\n"
    text+='Todas las diagonales reales coincidieron con sumas escalares. El Hessiano con penalización coincidió con diferencias del gradiente en un fixture sintético. Se guardaron espectros de curvatura con intercepto perfilado y su traza penalizada local; no son grados de libertad formales, influencia por eliminación, un diagnóstico causal o una validación privada. Los contrastesP65pertenecen a otra arquitectura con credibilidad/niveles/mezcla, no son coeficientes óptimos paraP82.\n\n'
    text+='No se eligió o probó unalpha, ni se cambió la receta fallidaP82. Una selección futura tendría que ser parte de un algoritmo finito aprendido SOLOdentro del entrenamiento, excluyendo también de CDF/preprocesamiento a cada retenido interno, y evaluado completo con las guardas originales. Ningún ajuste real/CDF/remuestreo/score retenido/2025/envío. B00/F3cyalternativas conservados,2024abierto adaptativo y fuente/snapshots/cola/reservas siguen condicionales; sin revisión independiente.\n\n'
    text+='| Ramo | Fold | Filas de entrenamiento | Traza local penalizada |\n|---|---:|---:|---:|\n'
    for z in d['records']:text+=f"|{z['line']}|{z['outer']}|{z['rows']}|{z['local_penalized_curvature_trace_not_formal_df']:.5f}|\n"
    text+='\nPróximo: '+next_unit+'\n\nEvidencia: '+w.rel(OUT/'report.json')+'.\n';DOC.write_text(text,encoding='utf8');body=OUT/'forum_resultado.md';body.write_text(text,encoding='utf8')
    receipt={'author':'Codex','utc':utc(),'status':d['status'],'report':w.rel(OUT/'report.json'),'report_sha256':w.sha(OUT/'report.json'),'document':w.rel(DOC),'next_unit':next_unit,
        **w.read(PLAN)['budget'],'2024_open':True,'goal_achieved':False,'forum':q.post(body,'COD-S2-20261027-PRIVADA-P83-PENALIZACION-RESULTADO','P83: penalización cuantificada, sin elegir hiperparámetros')}
    archive=R/'privado'/('corte_P83_'+datetime.now(timezone.utc).strftime('%H%M%S%f'));archive.mkdir();w.update(INDEX,receipt,archive)
    for path,key in [(R/'registro/semana2_mision017_fase2_actual.json','private_P83'),(R/'registro/semana2_mision_privada_actual.json','P83')]:w.update(path,{key:receipt,'next_unit':next_unit},archive)
    state=ROOT/'Preparación/ESTADO_PROYECTO.json';own=w.read(state)['week_2_mission017_phase2_20261025'];own.update(private_P83=receipt,next_unit=next_unit);w.update(state,{'week_2_mission017_phase2_20261025':own},archive)
    note='\n\n## Privada P83: curvatura de penalización guardada\n\nCodex, '+receipt['utc']+'.Quince modelos guardados, curvatura nueva por sumas independientes; sin ajustes reales/remuestreo/scores retenidos/envíos. No prueba causal o selección dealpha. Informe: '+w.rel(DOC)+'. Próximo: '+next_unit+'\n'
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:w.append(ROOT/'Preparación'/name,note,archive)
    w.update(ROOT/'RUTAS_PROYECTO.json',{'week_2_private_saved_penalty_review_index':w.rel(INDEX),'week_2_private_saved_penalty_review_report':w.rel(DOC)},archive)
    dump(OUT/'completion_receipt.json',receipt);print(json.dumps({'closed':True,'new_real_fits':0,'forum':receipt['forum']}))


if __name__=='__main__':
    sys.stdout.reconfigure(encoding='utf8');ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('mode',choices=['register','run','close']);args=ap.parse_args()
    with m.e.threadpool_limits(limits=2):{'register':register,'run':run,'close':close}[args.mode]()
