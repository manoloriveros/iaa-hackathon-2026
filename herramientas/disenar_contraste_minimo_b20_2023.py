"""Diseño documental condicional. No contiene un entrenador o calibrador."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import sys

ROOT = Path(__file__).resolve().parents[3]
REPO = ROOT / 'Hackaton/Repositorio_IAA2026'
ID = 'S2-B20-DISENO-CONTRASTE2023-v1-20261024'
RUN = REPO / 'privado/semana2/desarrollo2023/b20_diseno_contraste_20261024_v1'
PLAN = REPO / 'registro/semana2_b20_contraste_minimo_diseno_v1.json'
DOC = REPO / 'docs/archivo/semana2/DISENO_CONTRASTE_MINIMO_B20_2023.md'
PRE, RESULT = 'COD-S2-20261024-B20-DESIGN-PRE', 'COD-S2-20261024-B20-DESIGN-RESULT'
read = lambda p: json.loads(p.read_text(encoding='utf-8-sig'))
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
rel = lambda p: p.relative_to(ROOT).as_posix()
utc = lambda: datetime.now(timezone.utc).isoformat()


def dump(p, d):
    p.write_text(json.dumps(d, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def prepare():
    assert not PLAN.exists() and not RUN.exists()
    files, indices = {}, {}

    def add(path, expected=None):
        p = path.resolve(strict=True)
        assert p.is_relative_to(ROOT) and p.suffix in ['.json', '.md']
        assert '2024' not in rel(p).lower() and 'test' not in rel(p).lower()
        digest = sha(p)
        if expected:
            assert digest == expected, 'Fuente cambiada: ' + rel(p)
        files[rel(p)] = digest

    for label, name in [('synthesis', 'semana2_b20_sintesis_actual.json'),
                        ('calibration', 'semana2_b20_bandas_calibracion_actual.json'),
                        ('attribution', 'semana2_b20_atribucion_actual.json'),
                        ('contraction', 'semana2_b20_contraccion_actual.json'),
                        ('fire_AD', 'semana2_b20_incendio_AD_actual.json'),
                        ('ridge', 'semana2_glm_ridge_actual.json')]:
        path = REPO / 'registro' / name
        add(path)
        indices[label] = rel(path)
        d = read(path)
        add(ROOT / d['documentation'], d.get('documentation_sha256'))
        for key in ['report', 'verification', 'readout', 'closure_verification', 'decision_journal']:
            if key in d:
                item = d[key]
                if isinstance(item, dict):
                    add(ROOT / item['path'], item['sha256'])
                else:
                    add(ROOT / item, d.get(key + '_sha256'))
    for name in ['semana2_politica_seleccion_v1.json', 'semana2_contrato_entrenamiento.json',
                 'semana2_glm_ridge_coberturas_plan_v1.json', 'semana2_contadores_propios_actual.json',
                 'semana2_desarrollo2023_actual.json', 'semana2_b20_bandas_calibracion_plan_v1.json']:
        add(REPO / 'registro' / name)
    add(ROOT / 'Preparación/Antecedentes/IAA_IA/PRACTICAS_PRIORITARIAS.md')
    RUN.mkdir()
    (RUN / 'sources').mkdir()
    frozen = []
    for i, (path, digest) in enumerate(files.items()):
        snap = RUN / 'sources' / f'{i:02d}_{Path(path).name}'
        snap.write_bytes((ROOT / path).read_bytes())
        assert sha(snap) == digest
        frozen.append({'path': path, 'sha256': digest, 'snapshot': rel(snap)})
    plan = {
        'id': ID, 'author': 'Codex', 'utc': utc(), 'path_base': 'workspace_root',
        'authorization_literal': 'Continúa con el diseño previo de un contraste estándar mínimo para B20: identifica el mecanismo residual que lo justificaría y fija soporte y criterios de aceptación. Registra las decisiones, sin reentrenar ni abrir 2024 o test.',
        'status': 'conditional_design_only_support_failed_no_execution',
        'source_indices': indices, 'frozen_sources': frozen,
        'mechanism': {
            'id': 'M20-BUILDING-SPREAD',
            'hypothesis': 'Relatividades de riesgo de edificios demasiado dispersas, una vez separado el nivel global.',
            'evidence': 'A/E B20 edificios 1.966/1.563/.856/1.198/.714 por bandas de ajuste; extremos compatibles con pendiente de calibración menor que uno.',
            'not_established': ['No monotonía estricta en bandas intermedias', 'Rangos de folds cruzan uno',
                'Costes concentrados', 'C0/maduración y mezcla de perils pueden producir el patrón'],
            'fire_AD_role': 'Composición/incendios y AD inestable son explicación rival; no justifican interacción, máscara, exclusión o efecto causal.'},
        'contrast': {
            'line': 'buildings', 'family': 'Tweedie power1.5 log-rate calibration',
            'raw_anchor': 'B20 unchanged',
            'control_L': {'b': 1.0, 'a': 'estimated on inner cross-fitted training predictions'},
            'candidate_S': {'b_bounds': [0.0, 1.0], 'a': 'profiled separately under same objective'},
            'additional_free_parameters_vs_L': 1, 'one_candidate_only': True,
            'primary_comparison': 'S_minus_L', 'raw_guard': 'S_minus_rawB20',
            'formula': 'z_i=log(r_i)-m; r_star=exp(m); h_i(b)=C0_i*r_star*exp(b*z_i); mu_i=exp(a)*h_i(b)',
            'centering': 'm=sum(C0_i*log(r_i))/sum(C0_i) from inner-OOF training rows only',
            'objective': 'unweighted sum d_1.5(T0_i,mu_i); no penalty on a,b, no per-band parameters',
            'profile_intercept': 'a(b)=log(sum(T0_i/sqrt(h_i(b)))/sum(sqrt(h_i(b))))',
            'no_forced_AE_one': True,
            'scope_fixed': ['B20 alpha1 and seven original features', 'All perils T0 and C0 family unchanged',
                'All buildings rows; same transformation for new and renewal', 'motor and contents exact rawB20 predictions'],
            'excluded': ['other alpha', 'per-band factors', 'isotonic', 'business slopes', 'AD interaction',
                'hard coverage masks', 'row routing', 'claim deletion', 'target winsorization', 'new seeds']},
        'support': {
            'status': 'failed_on_existing_screen_no_fit_eligible',
            'origin': 'Project prudential design choices fixed now after existing2023 diagnostics; not Kaggle/IAA requirements, power estimates or confirmatory thresholds.',
            'screen_population': 'Existing building OOF tails: original fixed training-defined bands1 and5; do not rebin.',
            'pooled_tail': {'positive_groups_min': 50, 'largest_cost_group_share_max': .20,
                            'cost_concentration_equivalent_groups_min': 10.0},
            'fold_tail': {'positive_groups_min': 10, 'largest_cost_group_share_max': .50,
                          'cost_concentration_equivalent_groups_min': 3.0},
            'inner_calibration_each_outer_scope': {'positive_groups_total_min': 100,
                'tail_support': 'same pooled_tail rules on inner-OOF fit-only bands1/5',
                'log_rate_p80_minus_p20_min': 0.22314355131420976,
                'strict_positive_finite_C0_and_rates': True, 'unique_complete_groups_and_2023_only': True},
            'concentration_equivalent_count_is_not_inferential_sample_size': True,
            'all_five_scopes_must_pass': True, 'no_fold_or_cell_deletion_to_pass': True,
            'known_screen': [
                {'cell': 'buildings pooled band1', 'positive_groups': 69,
                 'largest_cost_group_share': 0.3165190285652545,
                 'cost_concentration_equivalent_groups': 6.091867231595157,
                 'result': 'fail concentration and equivalent-count rules'},
                {'cell': 'buildings pooled band5', 'positive_groups': 124,
                 'largest_cost_group_share': 0.19024732159082064,
                 'cost_concentration_equivalent_groups': 14.157133853009933,
                 'result': 'pass three pooled-tail rules, not overall readiness'},
                {'cell': 'buildings band1 most concentrated fold',
                 'largest_cost_group_share_rounded': .9182, 'result': 'fail fold share rule'}],
            'unknown': ['Remaining fold support', 'Inner-OOF calibration-scope support', 'Log-rate spread'],
            'failure_consequence': 'Stop before any future fit. No automatic threshold relaxation, regrouping or additional complexity; a revision needs distinct evidence and a version preserving this failure.'},
        'validation_design': {
            'years': [2023], 'outer_folds': [0, 1, 2, 3, 4], 'reuse_original_component_assignment': True,
            'outer_eval': 'F_k', 'outer_train': 'all2023 minus F_k',
            'inner_eval': 'F_j with j!=k', 'inner_train': 'all2023 minus (F_k union F_j)',
            'inner_learned_objects_exclude_both': ['B20 buildings GLM', 'imputer', 'scaler', 'OHE',
                'reporting curves', 'frequency/severity mixture weights', 'all learned C0 parameters'],
            'calibration_fit': 'Inner-OOF rates and matching inner-OOF C0 on outer_train; labels of F_k absent from every ancestor.',
            'outer_prediction': 'Saved B20 buildings outer model and its matching saved outer C0; a_k,b_k,m_k frozen before applying to F_k.',
            'common_rows_targets_weights_denominator': True,
            'no_global_OOF_calibrator_then_same_row_scoring': True,
            'do_not_reuse_inner_models_that_saw_outer_eval': True,
            'inner_training_fold_sets': [[i for i in range(5) if i not in (k,j)]
                                         for k in range(5) for j in range(k+1,5)],
            'no_refit_in_current_task': True,
            'existing_all_years_producers_not_invoked': True,
            'future_adapter_required': 'Strict2023 scoped adapter plus provenance guard, pure functions and graph audit before execution. Do not call existing all-years run().'},
        'acceptance': {
            'role': 'Exploratory development eligibility only, never automatic promotion or independent confirmation.',
            'all_conditions_conjunctive': True,
            'preconditions': ['All support gates pass', 'Separate authorization for fitting',
                'Frozen scoped implementation/resources, source SHA and forum preregistration', 'No unresolved technical blockers'],
            'primary_global_delta_D2_S_minus_L_min': .0005,
            'global_delta_D2_S_minus_rawB20_min': 0.0,
            'nonnegative_outer_fold_deltas_S_minus_L_min_count': 4,
            'worst_outer_fold_delta_D2_S_minus_L_min': -.001,
            'strict_0_lt_b_lt_1_min_outer_scopes': 4, 'b_at_zero_in_any_scope_reject': True,
            'tail_gap': {'definition': 'G=log(AE_band1)-log(AE_band5), same original B20 memberships for L/S',
                         'G_L_must_be_positive': True, 'G_S_min': 0.0, 'G_S_over_G_L_max': .80},
            'segment_delta_D2_S_minus_rawB20_min': -.001,
            'segments': ['motor', 'buildings', 'contents', 'new_customer', 'renewal', 'buildings_new', 'buildings_renewal'],
            'unchanged_motor_contents_absolute_tolerance': 0.0,
            'influence': {'remove': 'max(5,ceil(.001*G)) capped atG-1; favorable groups selected separately per comparison',
                          'comparisons': ['S_minus_L', 'S_minus_rawB20'], 'delta_D2_remaining_min': 0.0,
                          'evaluation_sensitivity_only_not_refit_or_cleanup': True},
            'absolute_buildings_nominal2023_total_change_vs_raw_max': .05,
            'no_new_CI_or_bootstrap_in_this_trial': True,
            'stop_if_any_fail_or_unknown': True,
            'negative_result': 'Keep raw B20 and B00/all alternatives; publish failure, no automatic next alpha/cut/seed/recipe.',
            'positive_result': 'Only evidence for further review. Adaptive2023 choice and parameter/first-stage uncertainty remain; common selection policy unchanged.'},
        'technical_preflight_future': ['exact2023 row/group scope', 'positive finite rates/C0',
            'a profile matches direct observed-unit deviance and KKT', 'rate weights if used are sqrt(C0), not C0',
            'normalized projected KKT residual<=1e-6', 'duplicate/source mutation fail before fit',
            'outer label poisoning cannot change any trained ancestor or calibration',
            'boundaries b0/b1, ties, empty tails and undefined A/E preserved as failures/undefined',
            'serialized inference and manual exp(Xbeta) agree', 'no optimizer restart or tuning after failure'],
        'resources': {
            'current': {'new_price_fits': 0, 'new_calibration_fits': 0, 'new_constants': 0,
                        'new_inference': 0, 'new_bootstrap': 0, 'new_catalog_recipes': 0},
            'future_only_if_gates_pass': {'unique_inner_B20_buildings_fits': 10,
                'ordered_inner_holdout_predictions': 20, 'saved_outer_B20_buildings_models_reused': 5,
                'new_outer_B20_fits': 0, 'slope_calibration_fits': 5, 'level_only_constants': 5,
                'C0_training_workflows': 10,
                'C0_detail': '10 times the frozen original building-peril C0 workflow, including reporting and frequency/severity composition; separate first-stage counts must be enumerated in implementation preflight.',
                'all_scenarios_and_challenger_search': 0, 'full_procedure_bootstrap': 0,
                'CPU_threads': 2, 'remote_or_test_or_submission': False,
                'resource_enumeration_incomplete_blocks_execution': True}},
        'current_conclusion': 'A concrete falsifiable hypothesis and minimal contrast are specified, but present support screen fails. Mechanism and calibration parameters not estimated; no trial or model is executable under this design-only authorization.',
        '2024_test_closed': True, 'ledger_read': False, 'promotion': False,
        'reference': 'W2-B00', 'all_alternatives_preserved': True,
        'prior_external2024_header_exposure_disclosed': True, 'complete_blindness_claim_allowed': False,
        'professional_independent_validation': False, 'forum_prior': PRE, 'forum_result': RESULT,
        'IAA': 'Purpose/limits ProfessionalConsiderations3.1; segment differences3.3; Governance2.8; Documentation3. Prudential numbers are project choices, no certification.'}
    dump(PLAN, plan)
    dump(RUN / 'plan_snapshot.json', plan)
    npath = REPO / 'registro/semana2_continuidad_nocturna.json'
    n = read(npath)
    unit = {'id': ID, 'plan': rel(PLAN), 'status': 'design_only_preregistered_no_training', 'forum_prior': PRE}
    if n.get('current_unit'):
        n.setdefault('parallel_artifact_diagnostics', {})[ID] = unit
    else:
        n['current_unit'] = unit
    n['updated_utc'] = utc()
    dump(npath, n)
    (REPO / 'registro' / (PRE + '_cuerpo.md')).write_text(
        'Diseño autorizado por el participante, sin entrenar. ' + ID + ': hipótesis de relatividades de edificios excesivamente dispersas, '
        'todavía no demostrada. Un único contraste de pendiente log-tasa 0<=b<=1 frente a b=1, con nivel libre bajo idéntico objetivo Tweedie1,5 '
        'en ambos brazos, base B20 intacta y ninguna calibración por bandas. Soporte y aceptación fijados en plan antes de cualquier nuevo ensayo. '
        'Los datos2023 previos ya muestran fallo de soporte por concentración, por lo que no hay permiso operativo para ajustar. '
        'Se documentan anidamiento necesario de B20/C0, controles, presupuesto futuro separado y criterio de parada. '
        'Solo JSON/Markdown guardados; cero parámetros, precios, inferencias, remuestreo, originales/OOF/modelos/2024/test/ledger. '
        'B00/B01–B20 conservados, revisión propia y exposición previa de título ajeno declarada sin uso.\n', encoding='utf-8')
    print(json.dumps({'id': ID, 'sources': len(frozen), 'status': plan['status'], 'new_fits': 0}))


def document():
    p = read(PLAN)
    assert not DOC.exists()
    for x in p['frozen_sources']:
        assert sha(ROOT / x['path']) == sha(ROOT / x['snapshot']) == x['sha256']
    text = '''# Contraste mínimo propuesto para B20: pendiente de riesgo en edificios

Se fija un único contraste estándar de calibración en log-tasa para comprobar si las relatividades de edificios están demasiado separadas. Se enfrenta una pendiente libre entre cero y uno con un control de pendiente uno; ambos permiten corregir el nivel. Añade un parámetro frente al control. El mecanismo todavía es una hipótesis y el soporte actual falla: el diseño queda condicionado y no se entrena.

## Evidencia que motiva la hipótesis

Las bandas B20 de edificios, fijadas en ajuste, tienen A/E 1,966 / 1,563 / 0,856 / 1,198 / 0,714. Las bajas infrapredicen en el agregado y la más alta sobrepredice; es compatible con un contraste de riesgo demasiado amplio. Las bandas intermedias no son monótonas. La banda 1 cambia de A/E 0,342 a 3,457 entre folds, comparte componentes y concentra costes. Esto no establece una pendiente verdadera menor que uno ni exige recalibrar.

El diagnóstico posterior de incendio/AD también queda incorporado: los dos incendios fijados están fuera del ajuste 3, donde AD cambia de signo, y un solo incendio representa 35,8% de la ganancia neta global B20/B19. La composición de perils y los costes grandes son explicaciones rivales. No se deriva una interacción AD×incendio, una máscara contractual ni la retirada de siniestros. El diseño no intenta identificar una causa de AD.

La calibración se refiere al coste observado T0 bajo el puente C0. No separa por sí sola un fallo de la prima de un fallo de maduración, reservas o mezcla. Tampoco identifica coste último. Los recibos ya existentes y la exposición previa a un título externo se declaran; este diseño posterior a los diagnósticos es exploratorio, aunque se registre antes de un eventual ensayo nuevo.

## Un cambio y un control que separa nivel de dispersión

Sea r la tasa anual B20 y e su exposición efectiva C0. Solo en las filas de calibración de ajuste se calcula m = Σ(e log r)/Σe y r* = exp(m). Para z = log r − m se propone:

    h(b) = e × r* × exp(b z)
    μ(a,b) = exp(a) × h(b)

| Brazo | Parámetros de calibración | Función |
| --- | --- | --- |
| B20 original | a=0, b=1 | Ancla sin cambios, salvaguarda descriptiva |
| L, control de nivel | a libre, b=1 | Permite que un desplazamiento de nivel explique la mejora |
| S, compresión | a libre, 0≤b≤1 | Comprueba una sola compresión continua del contraste de riesgo |

La comparación primaria es S−L. El efecto adicional es una pendiente, no cinco factores por banda. El intercepto se estima por separado en ambos brazos bajo el mismo objetivo, porque fijarlo a un valor común impondría niveles distintos de forma arbitraria al cambiar la pendiente. Se conserva una salvaguarda S−B20 original.

Se minimiza la suma no ponderada de devianzas de unidades observadas d₁,₅(T0, μ). En escala de tasas, la identidad exige pesos √e sobre d₁,₅(T0/e, tasa), no pesos e. Para un b fijo, el intercepto se perfila exactamente:

    a(b) = log[Σ T0/√h(b) ÷ Σ √h(b)]

Esto satisface el score del intercepto y no fuerza ΣT0/Σμ=1. La pendiente se estima dentro de [0,1], sin penalización, búsqueda de alpha o rejilla de recetas. b=1 expresa ausencia de compresión; b=0 borra toda relatividad de edificios y se rechaza como solución degenerada. No se calcula a, b o m en esta tarea.

Se conservan los siete efectos B20, alpha=1, transformaciones y codificación. El mismo cambio se aplicaría a todos los edificios, incluidos nuevos y renovación. Autos y contenidos mantienen exactamente sus predicciones B20. No hay pendientes por negocio, factores por bandas, isotónica, interacciones, enrutamiento, cortes nuevos, recortes del target o exclusión de siniestros.

## Soporte exigido antes de ajustar

Estos son límites prudenciales elegidos para este diseño después de ver los diagnósticos de 2023. No proceden de Kaggle o la IAA, no se estimaron mediante potencia y no convierten el análisis en confirmatorio. El tope de una quinta parte del coste limita el dominio de un componente; el equivalente de diez grupos describe dispersión de coste, sin ser un tamaño muestral inferencial. Los mínimos de positivos impiden sostener la dirección con muy pocos componentes; tampoco garantizan precisión.

| Ámbito | Regla conjunta |
| --- | --- |
| Cada cola agrupada, bandas originales 1 y 5 de edificios | ≥50 componentes positivos, mayor componente ≤20% del coste y equivalente de concentración ≥10 |
| Cada cola por fold | ≥10 componentes positivos, mayor componente ≤50% y equivalente de concentración ≥3 |
| Cada ámbito futuro de calibración interna | ≥100 componentes positivos totales; ambas colas con las reglas agrupadas; log-tasa P80−P20≥log(1,25); tasas y C0 estrictamente positivos y finitos |
| Integridad | Componentes completos, partición original, solo 2023, sin duplicados o fuga de ancestros; las cinco vistas deben pasar |

La comprobación barata previa usa las bandas OOF ya fijadas, sin cambiar sus cortes para obtener soporte. Las comprobaciones de calibración interna, si alguna vez procedieran, usarían cortes hechos solo con tasas de ajuste de su ámbito. Ante cualquier fallo o dato desconocido no se ajusta ni se elige una subpoblación favorable.

| Evidencia ya guardada | Frente a la regla | Estado |
| --- | --- | --- |
| Edificios banda 1: 69 grupos positivos, mayor 31,65%, equivalente 6,09 | Supera el tope 20% y queda bajo 10 equivalentes | Falla |
| Edificios banda 5: 124 positivos, mayor 19,02%, equivalente 14,16 | Cumple esas tres reglas agrupadas | Cumple solo esta celda |
| Edificios banda 1, fold más concentrado: mayor 91,82% | Supera el tope 50% por fold | Falla |
| Resto de soporte por fold, ámbitos internos y rango de log-tasa | No evaluados en este diseño | Pendientes |

La puerta actual está cerrada. No se presenta el soporte de la banda 5 como soporte global. Su apertura exigiría evidencia nueva pertinente o una revisión justificada y versionada que conserve este fallo; no se relajan umbrales automáticamente, combinan bandas después del resultado o borran componentes para pasar. El resultado de hoy es el diseño y su inadmisibilidad actual para entrenamiento.

## Cómo evitar fuga si el contraste llegara a ser admisible

Se conservan los cinco folds por componentes de 2023. Para evaluar Fk, todo lo aprendido usa exclusivamente los otros cuatro folds. Dentro de ellos, para producir la tasa de calibración de Fj, el B20 interno y todas sus dependencias se ajustan sin Fk ni Fj. Esto incluye medianas, escalas, OHE, curvas de reporte y mezcla de frecuencias/severidades de C0. Cada etiqueta de calibración se empareja con su tasa y C0 internos, ambos fuera de muestra respecto a esa etiqueta.

Con las predicciones internas de los cuatro folds se fijarían m, a y b. Solo después se aplicarían al B20 exterior guardado y al C0 exterior correspondiente, que ya excluyen Fk. No se puede entrenar un calibrador sobre toda la OOF actual y puntuarlo sobre las mismas filas. Tampoco basta usar el modelo OOF guardado de Fj: normalmente vio Fk, por lo que contaminaría la calibración del fold exterior. El C0 exterior no sustituye al C0 interno que debe excluir también Fj.

Hay 20 evaluaciones internas ordenadas, pero solo diez conjuntos de tres folds de ajuste: excluir Fk/Fj equivale a excluir Fj/Fk. Una caché con receta y fuentes idénticas permite diez B20 internos de edificios y diez flujos C0, con predicciones separadas para cada fold excluido. Se reutilizarían cinco modelos B20 exteriores, sin volver a entrenarlos.

Los productores históricos que recorren todos los años no se invocan. Hace falta un adaptador de ámbito 2023, funciones puras, manifiesto completo de ancestros y pruebas que alteren etiquetas exteriores sin cambiar ningún objeto aprendido. Su implementación y coste detallado aún no están congelados y también impiden la ejecución. No se crean datos ni resultados de confirmación.

## Criterios de aceptación del eventual ensayo local

Todas las condiciones se exigen juntas; un fallo o una condición desconocida conserva B20 original y todas las alternativas. Los márgenes siguientes son reglas de elegibilidad exploratoria, no pruebas de significación o promoción. El margen útil global de 0,0005 se toma de la política común; su aplicación local no sustituye la confirmación de esa política.

| Dimensión | Regla previa |
| --- | --- |
| Soporte y técnica | Todas las puertas anteriores; fuentes y ámbitos exactos; predicciones positivas/finita; objetivo y gradiente cotejados, KKT proyectado normalizado ≤10⁻⁶; sin reinicio del optimizador tras fallo |
| Ganancia primaria | ΔD² S−L global, sin ponderar y con nulo común, ≥0,0005 |
| Ancla original | ΔD² S−B20 global ≥0 |
| Estabilidad descriptiva | S−L no negativo en ≥4/5 folds; ningún fold por debajo de −0,001. b estrictamente entre 0 y 1 en ≥4/5 vistas; ninguna solución b=0 |
| Mecanismo observado | G_L=log(A/E banda1)−log(A/E banda5)>0 y 0≤G_S≤0,8 G_L, sobre las mismas membresías B20; reduce al menos 20% de la separación residual sin invertirla |
| Segmentos | ΔD² S−B20 ≥−0,001 en ramos, nuevo/renovación y edificios nuevo/renovación; autos/contenidos exactamente iguales |
| Influencia | Para S−L y S−B20 por separado, retirar de evaluación max(5,ceil(0,001G)) grupos más favorables, con tope G−1; ΔD² restante ≥0. No elimina datos ni reentrena |
| Nivel | Cambio absoluto del total nominal 2023 de edificios frente a B20 ≤5%; no se calcula 2025 |

La reducción del 20% de G exige que una ganancia de pérdida acompañe el mecanismo propuesto. Es una decisión de materialidad del diseño, no una estimación de cuánto debe mejorar. Los folds comparten ajuste y no son cinco experimentos independientes. No se calculan nuevos intervalos ni bootstrap de predicciones fijas para declarar certeza. Una eventual ganancia mantendría la selección adaptativa y la incertidumbre de reestimar la primera etapa y el modelo.

Un resultado favorable solo justificaría revisión posterior. B00 conserva la referencia; no hay roster, B21, promoción, retiro, otra tanda de 2024 ni cambio del protocolo común. Las salvaguardas de escenarios, nueva población, advertencias y acta de selección siguen pendientes de su procedimiento autorizado. Un resultado adverso se publica íntegro y no desencadena otro alpha, semilla, corte o familia.

## Coste, límites y decisiones

Ahora: cero parámetros estimados, ajustes, constantes, inferencias, recetas de catálogo o remuestreos. El contador propio permanece en 195 ajustes de precio y 285 constantes. El presupuesto hipotético, si en otra actuación se superaran las puertas y se autorizara entrenar, sería diez B20 internos de edificios, cinco pendientes de calibración y cinco constantes de nivel, además de diez flujos C0. Sus curvas y estimaciones auxiliares deben enumerarse separadamente antes de poder arrancar. No se ocultan dentro de los diez ajustes de precio. CPU local, dos hilos; sin remoto, escenarios adicionales, bootstrap completo o envíos.

Se registran las decisiones de mantener el mecanismo como hipótesis; elegir edificios por la evidencia previa; separar pendiente de nivel; usar un solo parámetro adicional; exigir soporte y detenerse porque falla; anidar C0 y transformaciones; fijar aceptación conjunta; conservar la política común; y no entrenar ni abrir otros años. La disponibilidad de último, reservas/reaperturas, reporte, capital y semántica contractual sigue condicionando el uso. Revisión de Codex, sin revisión humana o profesional independiente implícita.

2024, test, actas, scores, SEL01 y ledger permanecen cerrados en este trabajo. La exposición previa a un título ajeno queda declarada sin reproducir sus cifras, usarlas o afirmar ceguera completa. No se concilian aquí el estado o autorizaciones de una tanda externa.

[Plan estructurado](../../registro/semana2_b20_contraste_minimo_diseno_v1.json), [índice y recibos](../../registro/semana2_b20_contraste_minimo_actual.json), [síntesis anterior](SINTESIS_B20_Y_SIGUIENTE_PASO_2023.md), [bandas](CALIBRACION_B20_BANDAS_AJUSTE_2023.md) e [incendio/AD](INCENDIO_Y_AD_B20_2023.md). Fuentes congeladas, decisiones y comprobación de estructura del diseño quedan en privado. Documentación IAA §3 y Gobernanza §2.8 orientan el registro y la distinción de revisión propia; los umbrales prudenciales no se atribuyen a esas referencias.
'''
    DOC.write_text(text, encoding='utf-8')
    decisions = [
        ('D01', 'Hipótesis de dispersión excesiva en edificios, no mecanismo demostrado', 'Bandas extremas compatibles; monotonía intermedia, estabilidad y concentración insuficientes.'),
        ('D02', 'Una pendiente S frente a control L de nivel; conservar B20 crudo', 'Evita atribuir a compresión una mera corrección del nivel; un parámetro adicional.'),
        ('D03', 'Mismo objetivo observado Tweedie1.5 con C0 común por ámbito', 'Intercepción perfilada no fuerza A/E uno; no confundir calibración proxy con último.'),
        ('D04', 'Soporte previo con topes de concentración, positivos y rango', 'Reglas prudenciales declaradas después de diagnósticos; sin potencia o significación acreditada.'),
        ('D05', 'Detener antes de entrenar: pantalla actual falla', 'Banda1 edificios 31,65% y equivalente6,09; fold extremo91,82%. No relajación automática.'),
        ('D06', 'Anidar modelo, transformaciones y C0; cachear diez tríos', 'El calibrador global OOF y los modelos internos que vieron el fold exterior filtran etiquetas.'),
        ('D07', 'Aceptación conjunta: ganancia, mecanismo, estabilidad, segmentos, influencia y nivel', 'Ningún resultado aislado justifica promoción o más complejidad.'),
        ('D08', 'No añadir máscara/AD×incendio o excluir costes', 'Composición del fold no establece causalidad ni invalida los siniestros.'),
        ('D09', 'Diseño y presupuesto condicional, sin ejecutor o nueva receta de catálogo', 'Faltan soporte y adaptador estricto con cómputo de primera etapa congelado.'),
        ('D10', 'Conservar B00/B01–B20, política y 2024/test/ledger cerrados', 'Diseño exploratorio posterior a uso adaptativo; exposición externa declarada, revisión propia.')]
    dump(RUN / 'decision_journal.json', {'id': ID, 'author': 'Codex', 'utc': utc(),
        'decisions': [{'id': a, 'decision': b, 'basis': c} for a,b,c in decisions]})
    dump(RUN / 'current_readiness.json', {'id': ID, 'mechanism': 'plausible_not_established',
        'support_screen': p['support']['status'], 'known_screen': p['support']['known_screen'],
        'fit_authorized': False, 'can_execute': False, 'parameters_estimated': 0,
        'missing': ['support evidence', 'scoped implementation and resource enumeration', 'separate training scope authorization'],
        'new_fits': 0, 'new_inference': 0, '2024_test_closed': True})
    print(json.dumps({'document': rel(DOC), 'decisions': len(decisions), 'support': 'failed', 'new_fits': 0}))


if __name__ == '__main__':
    {'prepare': prepare, 'document': document}[sys.argv[1]]()
