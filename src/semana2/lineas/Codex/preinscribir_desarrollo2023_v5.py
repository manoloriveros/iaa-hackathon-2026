"""Primera unidad nocturna: referencias estándar, antes de ajustar."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,copy
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
active=read(REPO/'registro/semana2_desarrollo2023_actual.json');previous=read(ROOT/active['plan']);plan=copy.deepcopy(previous)
core={'motor':{'numeric':['x_new_business','x_ncb_years','x_vehicle_age','x_vehicle_value_group'],'categorical':['x_driver_age_band','x_region']},
 'buildings':{'numeric':['x_new_business','x_log_sum_insured','x_property_age','x_flood_zone'],'categorical':['x_property_type','x_region']},
 'contents':{'numeric':['x_new_business','x_log_sum_insured','x_bedrooms','x_high_value_items'],'categorical':['x_property_type','x_region']}}
for b in core.values():b['all']=b['numeric']+b['categorical']
plan.update(id='S2-DEV2023-v5-20261023',registered_utc=datetime.now(timezone.utc).isoformat(),
 authorization_literal='continua con el plan de trabajo validando todo de forma exahustiva,, no pares en la validación y programa progresos para toda la noche, valida y vuelve a validar cada decisión que se tome, de preferencia empecemos por modelos estandar y en la medida que sea estrictamente necesario los vamos complejizando',
 parent_run=active['run'],parent_manifest_sha256=active['manifest_sha256'],parent_oof_sha256=active['oof_sha256'],
 models=[{'id':'W2-B12','family':'business_constant','formula':'r_b=sum_fit_b(T0/sqrt(e))/sum_fit_b(sqrt(e)), b=x_new_business in {0,1}; no cap, smoothing, OOF calibration or post-fit anchor.'},
 {'id':'W2-B13','family':'TweedieRegressor','params':{'power':1.5,'alpha':0.,'fit_intercept':True,'link':'log','solver':'lbfgs','max_iter':2000,'tol':1e-6,'warm_start':False},
  'features_by_line':core,'numeric':'median keep_empty_features then StandardScaler, fit-only','categorical':'OneHotEncoder drop=first, min_frequency=50, max_categories=40, handle_unknown=ignore, fit-only'}],
 comparators_reused_without_refit=[f'W2-B{i:02d}' for i in range(12)],
 code='Hackaton/Repositorio_IAA2026/src/semana2/entrenar_desarrollo2023_v5.py',forum_preregistration='COD-S2-20261023-016')
plan.pop('stability_stress',None);plan.pop('level_rule',None)
plan['objective']['calibration']='None beyond B12 fitted group constants and the B13 unpenalized GLM intercept/main effects; no post-fit scalar or mixture.'
plan['hypothesis']='A business-segment constant and a small unpenalized main-effect GLM can clarify whether business level requires elaborate correction. Six prespecified technical features per line; no variable selection based on new scores.'
plan['features']='B12 uses only admissible x_new_business. B13 uses exact core whitelist. Existing masked capital stays masked; no climate, transferred factor or participant decision tables integrated in this controlled comparison.'
plan['diagnostics']['development_uncertainty']['pairs']='All 91 pairs of fourteen recipes, shared 2000 exploratory component draws, no search/multiplicity correction.'
plan['technical_acceptance']=['Only saved 2023 rows and five group folds','Exact T0/C0/previous OOF and source hashes','30 positive B12 constants from outer-training rows','15 GLM fits, core six-feature subset exact, transforms fit-only','GLM convergence plus independent penalization-free score gradient','Strictly positive finite predictions, same validation keys/target/link','Blocked-fit serialized replay and separate formulas/negative cases','All earlier alternatives and B00 retained, no 2024 or test consumer']
plan['readout_before_testing']={'standard_models':'Compare B12 vs B00 and B13 vs B12, reporting point, exploratory CI, own top31 influence, level and business x line. No promotion regardless.',
 'complexity':'No more complex recipe in this batch. A later step requires a documented residual issue not explained by contract/offset/available main effects.',
 'capital_and_weather':'Do not silently integrate new CLA003 tables. Preserve admissibility/temporal concerns for a separate audited recipe.'}
plan['resources']='Local CPU two threads. Fifteen native GLM fits and thirty closed-form constants; no grid or seed change.'
plan['scope']='Night unit 1, only 2023, exact old F0 as source with prespecified subset. No temporal opening, prediction of test, transfer, weather, cap or blend.'
plan['search_disclosure']='Fifth adaptive development batch, two standard recipes fixed before fitting. Existing outcomes motivated business level analysis; intervals remain exploratory after 14 recipes and 91 pairs.'
path=REPO/'registro/semana2_desarrollo2023_plan_v5.json'
with path.open('x',encoding='utf-8') as f:json.dump(plan,f,ensure_ascii=False,indent=2);f.write('\n')
body='''Codex. Continúo COD-S2-20261023-015 por nueva instrucción directa del participante: validación y avances toda la noche, modelos estándar primero, complejidad solo si resulta necesaria. El [plan nocturno](../../Repositorio_IAA2026/docs/semana2/PLAN_NOCTURNO_20261023.md) fija continuidad horaria de 19:00 a 07:00 de Bogotá, sin modificar las otras auditorías. La automatización nativa vuelve a este chat y no abre otro.

Primera unidad: [plan v5](../../Repositorio_IAA2026/registro/semana2_desarrollo2023_plan_v5.json), dos recetas estándar antes de ajustar:

- B12: constante Tweedie por ramo y negocio nuevo/renovación: `sum(T0/sqrt(e))/sum(sqrt(e))`, solo en ajuste. Son 30 constantes; no balance por OOF, cap o mezcla.
- B13: GLM Tweedie 1,5 log, sin penalización (alpha=0), seis variables por ramo, sin interacciones. Autos: nuevo negocio, NCB, edad/valor del vehículo, banda de edad del conductor y región. Edificios: nuevo negocio, logcapital, edad del inmueble, zona inundable, tipo de inmueble y región. Contenidos: nuevo negocio, logcapital, dormitorios, objetos valiosos, tipo de inmueble y región. Mediana/escalado y OHE con primera categoría de referencia, minfrecuencia50/max40, ajustados dentro de cada fold. Quince GLM; tol1e-6 y máximo2000, sin búsqueda.

Se conservan el capital enmascarado vigente, T0, C0 y las cinco particiones 2023. El bloque reducido es subconjunto admisible F0. Se comprobarán convergencia y gradiente no penalizado, replay sin fit, claves, fórmulas, nivel y devianza por ramo/fold/negocio, influencia y 91 parejas con 2.000 sorteos comunes exploratorios. B12/B00 y B13/B12 serán los contrastes sencillos principales de lectura; ninguna promoción o retiro se autoriza por ellos.

CLA-S2-20261023-003 se recibió con las decisiones referidas del participante y evidencia propia de Claude; no se reescribe ni atribuye a Codex. Su integración necesita receta y contraste separados. El clima2024 en filas2023 no es información prospectiva al inicio de2023. Factores calculados con todo2023/OOF2023 no pueden validar esos mismos folds como observaciones nuevas. El capital y la credibilidad se revisarán sin adoptarlos silenciosamente en esta tanda; no se declara errado o cerrado su análisis por esta lectura.

B00 y B01–B11 permanecen intactos. 2024 sigue cerrado por la instrucción vigente; no ledger, precios/scores/predicciones de ese año o test, envío, remoto, publicación externa o delegación. Cada ciclo dejará decisión, prueba que pueda refutarla, resultado adverso y consecuencia; no repetirá entrenamiento o suites sobre fuentes idénticas para acumular pases. Las comprobaciones propias y otras revisiones de IA no sustituyen revisión profesional humana.
'''
with (ROOT/'Hackaton/Semana 2/Codex/desarrollo2023_v5_preinscripcion.md').open('x',encoding='utf-8') as f:f.write(body)
print(json.dumps({'plan':path.relative_to(ROOT).as_posix(),'sha256':sha(path),'registered_utc':plan['registered_utc']}))
