"""Congela la verificación sintética y publica antes de ajustar cualquier fixture."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/g4_flujo_sintetico_20261024_v1'
PLAN=REPO/'registro/semana2_g4_flujo_sintetico_plan_v1.json'
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def main():
    assert not PLAN.exists()
    RUN.mkdir(parents=True,exist_ok=False)
    files=[REPO/'src/semana2/flujo_g4_sintetico2023.py',REPO/'herramientas/probar_flujo_g4_sintetico2023.py',REPO/'src/semana2/c0_estricto2023.py',REPO/'src/semana2/ambitos_c0_b20_2023.py']
    frozen=[]
    for p in files:
        q=RUN/'preregistered_sources'/p.name;q.parent.mkdir(exist_ok=True);q.write_bytes(p.read_bytes())
        frozen.append({'path':rel(p),'sha256':sha(p),'snapshot':rel(q)})
    plan={'id':'S2-G4-FLUJO-SINTETICO2023-v1-20261024','author':'Codex','utc':datetime.now(timezone.utc).isoformat(),
        'authorization_literal':'Avanza con G4 y valida el flujo completo con datos sintéticos. Sin entrenar con datos del concurso ni repetir diagnósticos; conserva B00, deja las decisiones y resultados en el foro y mantén2024cerrado.',
        'scope':'Synthetic software integration only: preprocessing,C0,GLM,nested calibration,application and replay. No contest data/estimators or external submission.',
        'hypothesis':'Changing protected outer labels/predictors cannot change any learned ancestor or calibration. Each inner learner also excludes its own inner fold. Allowed training changes must affect the learned stages.',
        'fixture':{'id':'G4-SYNTHETIC-v1','seed':20261024,'building_rows':400,'motor_contents_passthrough_rows':40,'claims':360,'folds':5,'source':'Generated from fixed code in memory; no real-data parameter extraction.'},
        'GLM':{'features':['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone','x_accidental_damage_cover','x_property_type','x_region'],
            'family':'TweedieRegressor','power':1.5,'alpha':1.,'link':'log','solver':'lbfgs','max_iter':2000,'tol':1e-6,
            'numeric':'fit-only median keep_empty_features and StandardScaler','categorical':'fit-only OHE drop-first,min_frequency50,max_categories40,unknown-ignore',
            'response':'T0/C0','sample_weight':'sqrt(C0)','normalized_penalized_gradient_max':1e-4},
        'C0':{'core':'c0_estricto2023.py frozen','valuation':'2024-12-31','reserve_factor':1.,'additional_tail_mass':0.,'six_building_perils':True,'no_reestimate_on_competition_data':True},
        'calibration':{'scope':'Four inner OOF folds inside each outer-training set; all ancestor learners exclude outer and respective inner folds.',
            'L':'b=1,profiled a','S':'0<=b<=1,profiled a; one bounded solve plus endpoint comparisons',
            'objective':'Unweighted sum observed-unit Tweedie deviance1.5, no A/E balancing',
            'centering':'C0-weighted mean log rate on inner OOF training only',
            'a_formula':'log(sum(y/sqrt(h)))-log(sum(sqrt(h))); h=C0*exp(m+b*(log(r)-m))',
            'solver':'scipy bounded,xatol1e-10,maxiter500','normalized_projected_KKT_max':1e-6,
            'reject':'All-zero target,constant rates,wrong scopes or corrupt artifacts; no fallback to protected rows.'},
        'acceptance':{'all_new_tests_pass':True,'outer_poison_cases':5,'ordered_inner_poison_cases':20,'entire_learned_state_and_serialized_objects_identical':True,
            'positive_training_controls':2,'serialization_replay_no_fit':True,'manual_exp_X_beta_rtol':1e-10,'deviance_formula_external_api_rtol':1e-12,
            'profile_vs_joint_optimization_loss_difference_max':1e-8,'known_calibration_a_b_error_max':1e-5,
            'exact_motor_contents_passthrough':True,'wrong_year_test_scope_mutation_duplicate_group_crossing_rejected':True,
            'input_data_or_network_open_attempts':0,'one_deliberate_fake_reader_guard_probe':True},
        'resources':{'CPU_threads':2,'wall_seconds_max':600,'scope_attempts_max':120,'successful_synthetic_GLM_fits_max':120,
            'synthetic_C0_workflows_max':120,'synthetic_reporting_peril_calls_max':720,'synthetic_calibrator_calls_max':80,'joint_reference_optimizations':3,
            'expected_baseline_unique_inner_fits':10,'expected_baseline_outer_fits':5,'expected_total_successful_scoped_fits':72,
            'new_competition_fits':0,'new_real_predictions_scores':0,'new_catalog_candidates':0,'old_suites_or_resampling':0},
        'failure_policy':'Preserve failed attempt/source/log. Only documented implementation/fixture repairs,never tune criteria to predictive results. No optimizer restarts or new seeds.',
        'retained_reference':'W2-B00','G1_G2_remain_unresolved':True,'2024_test_closed':True,'ledger_actas_SEL01_closed':True,'promotion':False,
        'forum_prior':'COD-S2-20261024-059','frozen_sources':frozen}
    PLAN.write_text(json.dumps(plan,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (RUN/'plan_snapshot.json').write_bytes(PLAN.read_bytes())
    p=RUN/'forum_059_pre.md';p.write_text('''Codex. Preinscripción G4 solicitada: flujo completo exclusivamente sintético, sin filas ni estimadores del concurso. Plan: Hackaton/Repositorio_IAA2026/registro/semana2_g4_flujo_sintetico_plan_v1.json. Código/fixture y suite congelados con SHA antes de ajustar.

Se integran el núcleo C0 existente, mediana/escalado/OHE ajustados por ámbito, GLM Tweedie1,5 log alpha1 con los siete efectos de edificios y calibración estándar L/S del diseño anterior. Cada exterior usa cuatro predicciones internas, cuyos ancestros excluyen exterior e interior. El calibrador aprende legítimamente las etiquetas internas del ajuste exterior; no se exige invariancia a ellas. Ningún ancestro o calibrador puede aprender de las etiquetas del exterior. Motor/contenidos son controles sintéticos de paso directo, sin tocar modelos guardados.

Fixture fijo generado en memoria: semilla20261024,400periodos de edificios,40controles de otros ramos y360notificaciones. No se extraen parámetros de datos reales. C0 rho1 y cola adicional0. GLM con respuesta T0/C0 y peso sqrt(C0),imputador/escalador/OHE solo de ajuste. L fija b1; S perfila a y acota b entre0y1,con centro logtasa ponderado por C0 interior. Un solve acotado y extremos,sin selección de alpha/semilla o reinicios. KKT perfilado normalizado<=1e-6,gradiente GLM<=1e-4.

Criterio técnico previo: invariancia de todos los objetos aprendidos y su aplicación a consultas fijas ante cinco envenenamientos exteriores y veinte pares interiores; controles positivos de coste/predictor permitido; fórmulas por otro método,replay serializado sin fit,fronteras,tasas empatadas/objetivo nulo,ámbitos/cachés incorrectos,2024/test,duplicados/cruce de grupos y mutación de objetos. Se bloquean lectores de CSV/Parquet/estimadores externos y red; una sonda deliberada usa una ruta falsa. No se repite la suite C0 aislada ni diagnósticos de modelos reales.

Presupuesto: dos hilos,hasta600s,120intentos de ámbito/120GLM/120C0 sintéticos y80calibradores como máximos. Línea base: diez ámbitos internos únicos y cinco exteriores; el plan enumera la prueba completa. Todos los ajustes son sintéticos y se cuentan aparte. Fallos conservados con fuentes y log; reparaciones solo de implementación/fixture documentadas,sin relajar criterios por desempeño.

Esta comprobación prepara software revisable; no resuelve mecanismo/soporte G1/G2 o valida último/uso actuarial. No promoción,retirada o nueva receta del catálogo. B00 y alternativas,T0/C0/folds/contadores reales conservados.2024/test/ledger/actas/SEL01 cerrados. Sin entrenamiento remoto,envíos,publicación externa,mensajes a otras conversaciones o delegación. Ventana nocturna cerrada. Revisión técnica propia,no aprobación humana o validación profesional independiente.
''',encoding='utf-8')
    out=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',plan['forum_prior'],'--asunto','G4: preinscripción de flujo completo y aislamiento con fixtures sintéticos','--cuerpo',str(p)],capture_output=True,text=True)
    assert out.returncode==0,out.stderr
    (RUN/'forum_prior_receipt.json').write_text(out.stdout,encoding='utf-8')
    print(json.dumps({'plan':rel(PLAN),'plan_sha256':sha(PLAN),'forum_prior':plan['forum_prior'],'frozen_sources':len(frozen),'synthetic_fits_run':0},ensure_ascii=True))

if __name__=='__main__':main()
