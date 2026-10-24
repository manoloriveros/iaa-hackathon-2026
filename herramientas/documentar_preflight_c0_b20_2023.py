"""Registra preflight de metadatos y sus límites; soporte sigue fallido."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1'
DOC=REPO/'docs/semana2/PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md'
INDEX=REPO/'registro/semana2_b20_preflight_c0_actual.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(p,d):p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')
def ev(p):return {'path':rel(p),'sha256':sha(p)}


def main():
    assert not INDEX.exists() and not DOC.exists()
    p,r,v=(read(RUN/x) for x in ['plan_snapshot.json','report.json','verification.json'])
    assert v['passed']==384 and v['failed']==0
    for x in p['frozen_sources']:assert sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256']
    now=datetime.now(timezone.utc).isoformat();outer=read(RUN/'observed_outer_scopes.json')
    lines=['# Preflight de C0 y aislamiento del contraste mínimo de B20','',
        'El soporte continúa fallido y el contraste no es ejecutable. Los cinco C0 exteriores guardados concuerdan con la exclusión de su fold, y sus exposiciones efectivas de 2023 coinciden con las entradas de B20. Ese resultado no habilita su reutilización como C0 interno: los veinte casos ordenados del diseño incorporarían etiquetas que deben quedar protegidas si se usan los objetos actuales.', '',
        'Codex, UTC '+now+'. Auditoría de código, registros de pertenencia, parámetros y pesos C0 ya guardados, y cachés exclusivamente de 2023. Se congelaron 66 fuentes con SHA y snapshots. No se abren las tablas de observación que mezclan años, los resúmenes con filas de 2024, datos originales, bundles de modelos o resultados de confirmación. Los manifiestos superiores se leen solo como metadatos de rutas y hashes. Cero ajustes, parámetros, valores C0 o precios nuevos.', '',
        '## Qué aprende C0 y qué debe aislarse','',
        'El código histórico de C0 coincide por SHA con su snapshot original. Para cada peril, `fit_reporting` usa los retrasos y edades de truncamiento de las notificaciones de ajuste para producir la distribución de conteos y pesos por notificación. Los mismos pesos y las marcas de coste producen la curva de coste y la marca media. Después se estima la frecuencia con el conteo y la exposición de ajuste corregida por completitud de conteos. El producto de frecuencia y marca media determina los pesos de la mezcla.', '',
        '| Dependencia | Información que determina el objeto | Regla del contraste interno |',
        '| --- | --- | --- |',
        '| Curva de notificación | Retrasos, edades de truncamiento y conteos del ajuste | Excluir los folds exterior e interior |',
        '| Pesos por notificación | Masas de la curva de conteos y tamaño de cada intervalo | Mismo ámbito que la curva |',
        '| Curva de coste y marca media | Marcas T0 y pesos de las notificaciones de ajuste | Mismo ámbito, sin marcas protegidas |',
        '| Frecuencia por peril | Conteo y denominador de exposición × completitud de conteos | Denominador construido solo con periodos de ajuste |',
        '| Mezcla de coste por peril | Frecuencia × marca media, normalizadas entre perils | No reutilizar mezcla exterior o global |',
        '| Completitud y exposición C0 por periodo | Curvas y mezcla congeladas del ámbito, fechas y exposición del periodo | Aplicar objetos ya fijados; las fechas de la fila no aportan sus etiquetas |', '',
        'C0 es exposición nominal multiplicada por la completitud de coste mezclada. Aislar únicamente el GLM o las curvas de reporte deja sin proteger otras dependencias aprendidas. Medianas, escalas y OHE del B20 interno también deben usar el mismo conjunto de tres folds.', '',
        'El corte histórico de valoración sigue siendo 31 de diciembre de 2024. Ese parámetro del objetivo observado no equivale a abrir pólizas, targets o validación de 2024. Se conservan las convenciones de T0 y C0, y las limitaciones retrospectivas y de coste último. En esta auditoría no se leyeron T0 o reservas de Parquet.', '',
        '## Aislamiento observado de los cinco ámbitos exteriores','',
        'Se cotejaron los registros de entrenamiento de C0 y sus pesos con las identidades de los 50.094 periodos de 2023 y 30.869 componentes. Los 12.580 periodos de edificios tienen las mismas claves en cada vínculo de 2023 y en la caché usada por B20; exposición nominal y C0 base coinciden exactamente. Los recuentos y sumas de pesos también concuerdan con los recibos del GLM.', '',
        '| Fold excluido | Periodos de ajuste de edificios | Periodos retenidos | Notificaciones de ajuste de edificios | Cruces de grupo / cliente / dirección |',
        '| --- | ---: | ---: | ---: | --- |']
    for x in outer:
        lines.append(f"| {x['outer_fold']} | {x['fit_periods']} | {x['heldout_periods']} | {x['fit_claims_buildings']} | 0 / 0 / 0 |")
    lines += ['', 'Cada registro de notificación guardado pertenece a un periodo de 2023 y a los cuatro ámbitos que no excluyen su fold. La unión de edificios contiene 519 notificaciones distintas; no son 519 periodos positivos. Los pesos guardados se corresponden con esos registros y suman el número de notificaciones por peril. Las dimensiones y masas de las curvas concuerdan con los conteos. Se comprueba la coherencia de los artefactos guardados, sin reestimar curvas o contrastarlas contra transacciones originales.', '',
        'El código histórico selecciona parte de sus ámbitos con `row_id`. En este inventario los 50.094 valores son globalmente únicos, por lo que no se detecta una colisión en los datos actuales. El nuevo contrato de pertenencia usa siempre `(market, line, row_id)`; una prueba sintética demuestra que una colisión entre ramos puede pasar un filtro por row_id y quedar rechazada por la clave compuesta. No se presenta ese caso sintético como un error real ya observado.', '',
        '## Por qué los objetos actuales no sirven como primera etapa interna','',
        'Para predecir internamente el fold j mientras el fold k queda reservado para evaluación exterior, todos los objetos aprendidos deben usar solo los otros tres folds. Se enumeraron diez conjuntos únicos de ajuste y veinte casos ordenados k/j, con hashes de pertenencia de periodos y componentes. Son propuestas de pertenencia; no se crea ningún estimador o C0 para esos ámbitos.', '',
        'Usar el C0 exterior k para las filas internas j incluiría las notificaciones de j en su propio ajuste de C0. Usar el C0 OOF ya guardado para j excluiría j, pero incluiría las notificaciones de k. Las veinte combinaciones contienen datos protegidos en ambas alternativas. Ninguna de las dos reutilizaciones pasa el contrato interno.', '',
        'Esto no invalida el uso exterior documentado de los cinco C0 guardados. La incompatibilidad surge al intentar asignarles el papel interno del contraste nuevo. Una caché cuyo nombre o hash es correcto tampoco acredita por sí sola el ámbito requerido: el manifiesto debe incluir el conjunto exacto de entrenamiento y todos sus ancestros.', '',
        '## Coste propuesto que ya puede enumerarse','',
        'Los seis perils de edificios están presentes en las cinco vistas exteriores. A partir de la unión de metadatos se contaron las notificaciones disponibles en cada uno de los diez tríos, sin usar sus marcas, ajustar curvas o eliminar registros:', '',
        '| Peril | Mínimo de notificaciones entre los diez tríos | Llamadas de reporte previstas, una por trío |',
        '| --- | ---: | ---: |']
    labels={'accidental_damage':'Daño accidental','escape_of_water':'Escape de agua','fire':'Incendio','flood':'Inundación','storm':'Tormenta','subsidence':'Subsidencia'}
    for name in r['building_perils']:
        lines.append(f"| {labels[name]} | {r['min_planned_notifications_by_peril'][name]} | 10 |")
    lines += ['', 'Todos superan el mínimo de cinco notificaciones exigido por la rutina histórica. Ese mínimo técnico se refiere a notificaciones y no sustituye las reglas de componentes positivos, concentración o rango de tasas del contraste. Tampoco demuestra que los retrasos y marcas internos sean estables o que las curvas nuevas converjan a una verdad última.', '',
        'El presupuesto hipotético queda desglosado: diez GLM internos de edificios; cinco pendientes de calibración y cinco constantes de nivel; diez flujos C0 con sesenta llamadas de reporte por peril, sesenta constantes de frecuencia derivadas y diez mezclas normalizadas de seis entradas. Las sesenta marcas medias son salidas de esas mismas llamadas de reporte, no sesenta modelos Gamma adicionales. Se reutilizarían cinco modelos exteriores. Estos son recuentos de trabajo previsto, no estimaciones hechas ni cambios del contador.', '',
        'La base reserva ρ=1 se mantiene fija. La pendiente propuesta se denomina β de calibración, todavía sin estimar y acotada en [0,1]. El `b` histórico de `fit_reporting` designa el factor de reservas, no esa pendiente: pasar β a ese argumento cambiaría el objetivo y C0. La separación queda declarada en el contrato; su aplicación en un adaptador numérico sigue pendiente. No se añaden escenarios .75/1.25 o colas a este ensayo mínimo.', '',
        '## Qué se implementó y qué falta','',
        'Se incorporó un selector puro de pertenencias que exige 2023, test falso, claves compuestas únicas, folds válidos y ausencia de cruces por componente, cliente y dirección. Solo recibe metadatos. Las catorce pruebas incluyen ámbitos válidos, año/test indebido sintéticos, duplicados, cruces, exclusiones inválidas, colisión de row_id y etiquetas sintéticas alteradas que no cambian la pertenencia.', '',
        'Esas pruebas validan el selector, no la invariancia de un C0 ajustado al envenenar etiquetas protegidas. No existe aquí un núcleo numérico C0 nuevo ni se lo invoca. El ejecutor histórico `run()` lee tablas de todos los años y test antes de recorrer los ámbitos; no es un punto de entrada admisible para esta actuación. Se conserva sin cambios como evidencia y no se ejecuta.', '',
        '| Carencia | Estado después del preflight | Evidencia aún necesaria |',
        '| --- | --- | --- |',
        '| Dependencias y pertenencia exterior | Inventariadas y conciliadas en los artefactos guardados | No constituye revisión independiente o de transacciones |',
        '| Contrato interno de pertenencia | Diez tríos y veinte casos enumerados; selector de metadatos comprobado | Conectarlo a un adaptador numérico de ámbito estricto, sin lectura previa de otros años |',
        '| C0 numérico interno | No implementado ni estimado aquí | Rutinas puras con fechas/marcas/denominadores y mezcla del mismo ámbito; clave de caché que incorpore fuentes, grupos, receta, valoración y parámetros |',
        '| Invariancia de todo el aprendizaje | Solo se comprobó el selector | Alterar etiquetas de ambos folds protegidos y cotejar curvas, marcas, frecuencias, mezcla, transformaciones, GLM y calibrador del flujo real |',
        '| Artefactos internos y su soporte | Ausentes de esta actuación | Tasas y C0 internos válidos, manifiestos completos y comprobación de las reglas originales; no generarlos bajo el mandato actual |',
        '| Soporte retenido | Sigue fallido: cinco de diez celdas en cuatro folds | Evidencia legítima suficiente; los controles de implementación no eliminan la concentración medida |', '',
        'El recuento de llamadas de primera etapa queda resuelto para el caso base de edificios. Sigue pendiente un presupuesto de ejecución verificable del adaptador real, su entorno y pruebas del flujo completo. Un cambio de código futuro necesita sus propios recibos: los de este preflight no certifican una implementación posterior.', '',
        'La condición de soporte no se rebaja a advertencia informativa. No se relajan umbrales, combinan bandas para pasar, eliminan siniestros, fijan un nuevo roster o promueven alternativas. B00 conserva referencia y B01–B20 se preservan. No se calcula nueva calibración, mejora o precio.', '',
        '## Recibos y alcance','',
        'Pasaron 384 comprobaciones propias, incluidas catorce pruebas del contrato de metadatos, sin fallos. Se mantienen 195 ajustes de precio y 285 constantes en el contador propio. Cero ajustes, inferencias, valores C0, parámetros o remuestreos nuevos; no hay entrenamiento remoto, envíos, mensajes externos o delegación.', '',
        '2024, test, actas, scores, SEL01 y ledger permanecen cerrados en este trabajo. La exposición previa a un título ajeno se mantiene declarada sin usar sus métricas o afirmar ceguera completa. La comprobación de Codex no equivale a revisión profesional independiente. Documentación IAA §§2–3 y Gobernanza §2.8 orientan procedencia y alcance; la condición de soporte sigue regida por el diseño del proyecto.', '',
        '[Plan previo](../../registro/semana2_b20_preflight_c0_plan_v1.json), [índice y recibos](../../registro/semana2_b20_preflight_c0_actual.json), [auditoría de soporte](SOPORTE_B20_POR_FOLD_2023.md), [diseño mínimo](DISENO_CONTRASTE_MINIMO_B20_2023.md), [selector de metadatos](../../src/semana2/ambitos_c0_b20_2023.py) y [código histórico C0](../../src/semana2/variables_ultimo.py). El detalle de ámbitos, reutilizaciones incompatibles, dependencias y fuentes SHA queda en `privado/semana2/desarrollo2023/b20_preflight_c0_20261024_v1`, fuera de Git.']
    DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    decisions=[
        ('C0P-01','Mantener soporte fallido y contraste sin ejecución','Las comprobaciones de pertenencia no anulan las cinco celdas de coste concentrado.'),
        ('C0P-02','Aislar todos los ancestros C0, no solo las curvas','Pesos, marcas, frecuencias/denominadores y mezcla también dependen del ajuste.'),
        ('C0P-03','Conservar uso exterior documentado de los cinco C0','Fuentes2023, registros de ajuste y vínculos concuerdan; no se declara fuga inexistente en ese uso.'),
        ('C0P-04','Rechazar ambas reutilizaciones internas en veinte pares','C0 exterior ve etiquetas internas; C0 OOF de j ve etiquetas exteriores k.'),
        ('C0P-05','Usar contrato puro con claves compuestas','row_id actual es único, pero la colisión sintética demuestra fragilidad de usarlo solo; no se altera la partición.'),
        ('C0P-06','Enumerar sesenta llamadas de primera etapa por peril','Seis perils por diez tríos; marcas retornadas no se cuentan como nuevos Gamma; todavía ninguna ejecución.'),
        ('C0P-07','Separar rho de reserva y beta de calibración','rho1 y valoración histórica fijas; no pasar pendiente como factor de reservas o cambiar T0/C0.'),
        ('C0P-08','No invocar el ejecutor histórico de todos los años','Hace falta un adaptador estricto; solo se implementa y prueba pertenencia de metadatos.'),
        ('C0P-09','Mantener carencias numéricas y pruebas del flujo pendientes','Selector comprobado no acredita invariancia del C0 aprendido, artefactos internos, soporte o beneficio.')]
    dump(RUN/'decision_journal.json',{'id':p['id'],'author':'Codex','utc':now,'decisions':[
        {'id':a,'decision':b,'basis':c} for a,b,c in decisions]})
    dump(RUN/'evidence_gaps.json',{'id':p['id'],'resolved':['C0 dependency inventory and five outer membership reconciliations',
        'Exact stored2023 link/cache equality','Ten planned memberships and20unsafe cache-reuse cases',
        'Basebuildingperil workload count60 and metadata selector14fixtures'],
        'pending':['Strict2023 numeric C0 adapter and full cache/provenance contract',
        'Actual fitted-object poisoning tests and numerical parity',
        'Nested internal rate/C0 artifacts and their original support rules',
        'Verified execution budget/environment for implemented code',
        'Failed heldout support and unestablished mechanism/benefit remain'],
        'support_gate':'failed','can_execute':False,'fit_authorized':False})
    (RUN/'code').mkdir()
    codes=[REPO/'src/semana2'/x for x in ['preflight_c0_b20_2023.py','ambitos_c0_b20_2023.py']]+[
        REPO/'herramientas'/x for x in ['preparar_preflight_c0_b20_2023.py','verificar_preflight_c0_b20_2023.py','documentar_preflight_c0_b20_2023.py']]
    for code in codes:(RUN/'code'/code.name).write_bytes(code.read_bytes())
    outputs=[DOC]+[RUN/x for x in ['report.json','verification.json','observed_outer_scopes.json','planned_inner_scopes.json',
        'unsafe_cache_reuse.json','C0_dependency_inventory.json','decision_journal.json','evidence_gaps.json']]
    dump(RUN/'manifest.json',{'id':p['id'],'author':'Codex','inputs':p['frozen_sources'],'outputs':[ev(x) for x in outputs],
        'code_snapshots':[ev(RUN/'code'/x.name) for x in codes],'new_fits':0,'new_inference':0,'new_C0_values':0})
    idx={'id':p['id'],'author':'Codex','utc':now,'path_base':'workspace_root',
        'status':'C0_dependencies_outer_scope_reconciled_inner_reuse_rejected_support_failed_no_execution',
        'run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),
        'plan':rel(REPO/'registro/semana2_b20_preflight_c0_plan_v1.json'),'plan_sha256':r['source_plan_sha256'],
        'report':ev(RUN/'report.json'),'verification':ev(RUN/'verification.json')|{'passed':384,'failed':0},
        'outer_scopes':ev(RUN/'observed_outer_scopes.json'),'planned_inner_scope_receipt':ev(RUN/'planned_inner_scopes.json'),
        'unsafe_cache_reuse':ev(RUN/'unsafe_cache_reuse.json'),'dependencies':ev(RUN/'C0_dependency_inventory.json'),
        'decision_journal':ev(RUN/'decision_journal.json'),'evidence_gaps':ev(RUN/'evidence_gaps.json'),'manifest':ev(RUN/'manifest.json'),
        'source_count':66,'observed_outer_scopes_reconciled':5,'planned_inner_scopes_count':10,
        'unsafe_existing_reuse_cases':20,'hypothetical_reporting_peril_calls':60,
        'C0_numeric_core_implemented':False,'fitted_object_poisoning_tested':False,'metadata_fixtures':14,
        'support_gate':'failed','fit_authorized':False,'can_execute':False,
        'new_fits':0,'new_inference':0,'new_C0_values':0,'parameters_estimated':0,'new_bootstrap':0,
        'claims_or_groups_removed':0,'thresholds_relaxed':False,'reference':'W2-B00','promotion':False,'all_alternatives_preserved':True,
        '2024_test_closed':True,'ledger_read':False,'prior_external2024_header_exposure_disclosed':True,
        'complete_blindness_claim_allowed':False,'professional_independent_validation':False,
        'forum_prior':p['forum_prior'],'forum_result':p['forum_result'],
        'next_step':'Reuse preflight receipts. Numeric scoped C0 adapter, actual fitted-object poisoning and nested artifacts remain unimplemented; failed support unchanged. No fitting or reopening years.'}
    dump(INDEX,idx)
    np=REPO/'registro/semana2_continuidad_nocturna.json';n=read(np);before=n.get('current_unit')
    assert not any(x['id']==p['id'] for x in n['completed_units'])
    unit={'id':p['id'],'run':rel(RUN),'documentation':rel(DOC),'index':rel(INDEX),'verification':idx['verification'],
        'decision_journal':idx['decision_journal'],'completed_utc':now,'forum_result':p['forum_result'],
        'support_gate':'failed','new_fits':0,'new_inference':0,'new_C0_values':0,'fit_authorized':False}
    n['completed_units'].append(unit)
    if (n.get('current_unit') or {}).get('id')==p['id']:n['current_unit']=None
    elif p['id'] in n.get('parallel_artifact_diagnostics',{}):n['parallel_artifact_diagnostics'][p['id']].update(status='completed_support_still_failed',index=rel(INDEX))
    n['latest_completed_unit'],n['updated_utc']=unit,now
    n['latest_b20_C0_preflight_index']=rel(INDEX);n['no_repetition_for_completed_b20_C0_preflight']=True
    n['integration_decisions']['B20_C0_preflight']='Fiveouter scopes/links reconciled;20nested cache reuses unsafe. Tenplannedtrios,60hypotheticalreportingcalls. Metadata selector14fixtures is not numericC0; supportfailed and nofit.'
    n.setdefault('condition_progress_without_auto_closure',{})['B20-C0-preflight']='Membership/dependencies and resourcecounts audited; numeric scoped adapter and full learned-object tests missing. No closure of failed support.'
    n['next_unit']='B20 C0 metadata preflight completed; reuse latest_b20_C0_preflight_index without repeating suites. Fiveouter scopes valid for original use, all20nested reuses invalid. Numeric strict2023 C0 adapter/full fitted-object poisoning/nested artifacts remain absent. Support staysFAILED; no training, C0reestimation, calibration, newprices, relaxedthresholds, deletions or2024/test/ledger opening. Any further work must stay separately authorized and preserve existing window/incident/concurrent unit.'
    if n.get('current_unit') is None:n['status']='scheduled_'+str(len(n['completed_units']))+'_units_C0_preflight_done_support_failed_no_training'
    dump(np,n)
    dump(RUN/'registration_receipt.json',{'id':p['id'],'utc':now,'previous_current_unit':before,'current_unit_after':n.get('current_unit'),
        'preserved_other_current_unit':(before or {}).get('id') in (None,p['id']) or before==n.get('current_unit'),
        'completed_units_at_cut':len(n['completed_units']),'window_end':n['window_end'],'frequency':n['frequency'],'automation_toml_changed':False})
    rp=ROOT/'RUTAS_PROYECTO.json';routes=read(rp)
    routes.update(week_2_b20_C0_preflight_index=rel(INDEX),week_2_b20_C0_preflight_report=rel(DOC),week_2_b20_C0_preflight_plan=idx['plan']);dump(rp,routes)
    sp=ROOT/'Preparación/ESTADO_PROYECTO.json';raw=sp.read_text(encoding='utf-8-sig');key='semana2_b20_preflight_c02023_20261024'
    assert key not in json.loads(raw)
    state={'utc':now,'author':'Codex','path_base':'workspace_root','index':rel(INDEX),'status':idx['status'],
        'outer_scopes_reconciled':5,'nested_reuse_cases_rejected':20,'support_gate':'failed','fit_authorized':False,
        'new_fits':0,'new_inference':0,'new_C0_values':0,'2024_test_closed':True}
    sp.write_text(raw.replace('{','{\n  '+json.dumps(key)+': '+json.dumps(state,ensure_ascii=False)+',',1),encoding='utf-8')
    note=('\n\n## '+p['id']+': dependencias C0 y aislamiento sin entrenamiento\n\nCodex, UTC '+now+
        '. Encargo humano de preflight C0/folds con soporte fallido y2024/test cerrados. Plan/foro C0-PRE previos;66fuentes conSHA/snapshots: '
        'metadatos2023, C0scopes entrenados2023, enlaces/caches exclusivos2023 y código. No tablasmixtas, summaries2024, originales, bundles o T0/reservasParquet. '
        '384comprobaciones propias sinfallos, incluidas14pruebas del selector de metadatos; sin reentrenar, valoresC0/precios nuevos o inferencia.\n\n'
        'Se inventarían curvas de conteo, pesospornotificación, curva/marca decoste, frecuencia/denominador y mezcla: todos requieren mismo ámbito. '
        'CincoC0exteriores excluyen sufold, sin cruces componente/cliente/dirección; enlaces2023 idénticos a cachesB20 y recibos de pesos/counts compatibles. '
        '50.094periodos/30.869componentes;12.580edificios y519notificaciones distintas en unión de registrosC0. row_id único actual, '
        'pero contrato puro usa(market,line,row_id) y rechaza colisión sintética entre ramos. Usoexterior conservado, sin afirmar fugaenél.\n\n'
        'Dieztríos de ajuste yveintecasos internos enumerados por pertenencia, sin estimadores. Enlos20, usarC0exterior parafoldinterno ve susnotificaciones; '
        'usarC0OOFguardado delinterno ve lasdelexterior. Ningunareutilización cumple elcontrato interno. Seis perils, mínimos denotificaciones '
        'portrío AD29/agua68/incendio27/inundación21/tormenta122/subsidencia14; todos≥5 de rutina, sin sustituirsoporte de coste fallido. '
        'Presupuesto hipotético:60llamadasreporteporperil,60constantesfrecuencia y10mezclas;60marcas retornadas enmismasllamadas no sonmodelosGammaextra. '
        'Se mantienen10GLMinternos,5pendientes/5constantes y5modelosexteriores reutilizados. No añade contador.\n\n'
        'Separar rho_reserva1 de beta_calibración noestimada; valoraciónhistórica2024-12-31 fija no es apertura de pólizas2024. '
        'No invocarrunhistórico que lee todoslosaños/test. Implementado solo selectorpuro depertenencia; no núcleoC0numérico ni pruebadeinvariancia '
        'deobjetosaprendidos anteetiquetasprotegidas. Faltan adaptadorestricto/provenienciacaché, paridadnumérica, pruebasdeflujo real, '
        'artefactos/rangosoporteinternos y presupuesto/entorno deimplementación verificados. Soporteretenido siguefallido5/10encuatrofolds; '
        'documentación/recursoscontados no borranconcentración. Nueve decisiones.\n\n'
        'B00/B01–B20 y195/285preservados;sinpromoción, umbralrelajado, exclusión, complejidad, entrenamiento/remoto/envío/delegación o mensajeexterno. '
        '2024/test/actas/scores/SEL01/ledgercerrados, exposiciónprevia de títuloajeno declarada sinuso/cegueracompleta, revisiónpropia sinindependenciaprofesional. '
        'Informe docs/semana2/PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md e índice registro/semana2_b20_preflight_c0_actual.json; corrida privada b20_preflight_c0_20261024_v1. '
        'Memoria/estado/decisiones/rutas/continuidad actualizados; ventana/incidente/otrasautomatizaciones yunidadconcurrente respetados.\n')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        with (ROOT/'Preparación'/name).open('a',encoding='utf-8',newline='') as f:f.write(note)
    update=('\n\n## Preflight C0 terminado; soporte continúa fallido\n\nEl [preflight](PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md) '
        'concilia5scopesexteriores yrechaza20reutilizaciones internas. Seenumeran10tríos/60llamadasreportebuildings, sin ajustar. '
        '384comprobaciones/14fixturesdemetadatos sinfallos; selector puro no esadaptador C0numérico. Faltan núcleoestricto/pruebasdeflujo/artefactos internos, '
        'y la condición de soporte medida permanece fallida. Noentrenar o repetir suites;195/285, B00/alternativas,2024/test/ledgercerrados, '
        'ventana/programación/incidente intactos. Balance parcial.\n')
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:
        with (REPO/'docs/semana2'/name).open('a',encoding='utf-8',newline='') as f:f.write(update)
    body=('Resultado de '+p['forum_prior']+':66fuentes congeladas,384checks propios/14fixturesmetadatos sinfallos. '
        'CincoC0exteriores2023 concilian registros/pesos/modelosguardados y links-cachesB20, sin cruces grupo/cliente/dirección. '
        'No se declara fugaen usoexterior original. Todoslosancestros C0 deben aislarse: conteocurvas/pesos, marcas/costecurvas, frecuencia/denominador ymezcla.\n\n'
        'Dieztríos/veinteparesinternos inventariados: las20reutilizaciones deC0guardado sonincompatibles porque ven etiquetas interiores o exteriores protegidas. '
        'Seis perils buildings =>60llamadasreportehypotéticas,60frecuenciasderivadas/10mezclas; marcas incluidas en llamadas, no Gammaextra. '
        'Mínimosnotificacionesportrío29/68/27/21/122/14, todos≥5, sin acreditarsoporte de cola. rho_reserva1 separado de beta_calibración, '
        'valoraciónhistórica fija. No invocarproductor de todoslosaños/test.\n\n'
        'Implementado selector puro con clavescompuestas yfixtures; no C0numérico o pruebadepoisoning deobjetosaprendidos. '
        'Pendientes adaptadorestricto/paridad/grafocaché/flujo real/artefactos internos y presupuestoimplementado. Soporte sigueFALLIDO, '
        'sin entrenar, nueva C0/inferencia/precio, parámetros, umbralesrelajados o exclusión. B00/B01–B20,195/285,2024/test/actas/scores/SEL01/ledgercerrados intactos. '
        'Informe docs/semana2/PREFLIGHT_C0_Y_AISLAMIENTO_B20_2023.md; índice registro/semana2_b20_preflight_c0_actual.json. '
        'Exposiciónprevia ajena sinuso/cegueracompleta, revisiónpropia noindependiente; ventana/incidente/otrasautomatizaciones/unidadconcurrente preservados.\n')
    (REPO/'registro'/(p['forum_result']+'_cuerpo.md')).write_text(body,encoding='utf-8')
    print(json.dumps({'document':rel(DOC),'index':rel(INDEX),'completed_units_at_cut':len(n['completed_units']),'passed':384,'support_gate':'failed','new_fits':0}))


if __name__=='__main__':main()
