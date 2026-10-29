"""Documenta los fallos observados sin modificar el diseño o sus umbrales."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json

ROOT=Path(__file__).resolve().parents[3]
REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/b20_soporte_folds_20261024_v1'
DOC=REPO/'docs/archivo/semana2/SOPORTE_B20_POR_FOLD_2023.md'
INDEX=REPO/'registro/semana2_b20_soporte_folds_actual.json'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()


def dump(p,d):
    p.write_text(json.dumps(d,ensure_ascii=False,indent=2,allow_nan=False)+'\n',encoding='utf-8')


def ev(p):
    return {'path':rel(p),'sha256':sha(p)}


def es(x,n=2):
    return f'{x:.{n}f}'.replace('.',',') if x is not None else 'indefinido'


def main():
    assert not INDEX.exists() and not DOC.exists(),'No repetir documentación.'
    p,r,v=(read(RUN/x) for x in ['plan_snapshot.json','report.json','verification.json'])
    assert v['failed']==0 and v['passed']==911
    for x in p['frozen_sources']:
        assert sha(ROOT/x['path'])==sha(ROOT/x['snapshot'])==x['sha256']
    now=datetime.now(timezone.utc).isoformat()
    folds=read(RUN/'fold_cell_audit.json');pool=read(RUN/'pooled_cell_audit.json');proxy=read(RUN/'outer_training_proxy.json')
    primary=[x for x in folds if x['eligibility_gate']]
    lines=['# Soporte de B20 por fold: concentración y evidencia pendiente','',
        'El contraste mínimo de edificios sigue sin soporte admisible. Fallan cinco de las diez celdas de cola retenida, repartidas entre cuatro folds. Todas alcanzan el mínimo de componentes positivos; los incumplimientos vienen de la concentración del coste. Solo el fold 0 pasa ambas colas. No se retira ningún siniestro, componente, fold o banda.', '',
        'Codex, corte UTC '+now+'. Auditoría de artefactos guardados de 2023 con las reglas del [diseño previo](DISENO_CONTRASTE_MINIMO_B20_2023.md). Se inventarían las 75 celdas ramo/fold/banda y las 15 agrupadas de B20. La puerta de elegibilidad se aplica únicamente a las diez celdas de edificios bandas 1/5 y sus dos colas agrupadas; no se extiende a otros ramos o bandas. No se entrenan, cargan o consultan modelos, producen tasas, cambian cortes o calculan nuevos D²/intervalos.', '',
        '## Resultado con los umbrales intactos','',
        'Por fold y cola se exigen simultáneamente al menos diez componentes con coste positivo, máximo 50% del coste en un componente y equivalente de concentración de al menos tres. En las colas agrupadas son cincuenta positivos, máximo 20% y equivalente de diez. Son límites prudenciales fijados por el diseño después de los diagnósticos; no son requisitos de Kaggle/IAA ni una garantía de precisión.', '',
        '| Fold | Banda | Componentes positivos | Mayor participación en coste | Equivalente de concentración | Resultado |',
        '| --- | --- | ---: | ---: | ---: | --- |']
    for x in sorted(primary,key=lambda x:(x['fold'],x['band'])):
        lines.append(f"| {x['fold']} | {x['band']} | {x['positive_groups']} | {es(100*x['largest_group_cost_share'])}% | {es(x['cost_concentration_equivalent_groups'])} | {'Cumple la celda' if x['verdict']['pass'] else 'Falla concentración y equivalente'} |")
    lines += ['', 'Los cinco incumplimientos son edificios banda 1 en folds 1, 2, 3 y 4, y banda 5 en fold 4. Ninguna de esas diez celdas falla por el mínimo de positivos: hay de 11 a 28. Contar positivos y medir concentración responde a preguntas diferentes. Tener diecisiete componentes positivos no compensa que uno reúna el 91,82% del coste, como ocurre en fold 3/banda 1.', '',
        'El fold 2/banda 1 tiene equivalente 2,911 y participación 55,38%; también falla. La clasificación usa valores completos, sin redondear a tres equivalentes o a 50%. No se promedian criterios entre bandas ni se da por bueno un fold porque su otra cola pase. Se exigían cinco vistas admisibles: conservar solo el fold 0 o saltarse la cola problemática cambiaría el diseño.', '',
        '| Cola de edificios agrupada | Positivos | Mayor participación | Equivalente | Resultado con 50 / 20% / 10 |',
        '| --- | ---: | ---: | ---: | --- |']
    for x in pool:
        if x['eligibility_gate']:
            lines.append(f"| Banda {x['band']} | {x['positive_groups']} | {es(100*x['largest_group_cost_share'])}% | {es(x['cost_concentration_equivalent_groups'])} | {'Cumple la celda' if x['verdict']['pass'] else 'Falla concentración y equivalente'} |")
    lines += ['', 'La banda 5 agrupada cumple, pero fold 4/banda 5 falla. La banda 1 agrupada también falla. La agregación oculta fragilidad y el paso de una celda no acredita el conjunto.', '',
        'En cada celda se suma T0 por componente completo presente en ella: Cg. La participación máxima es max(Cg)/ΣCg; el equivalente es (ΣCg)²/ΣCg². Es una descripción de concentración de coste, no un número de observaciones independientes para un intervalo. Un componente puede tener varias filas o bandas; los recuentos no se suman entre bandas como muestras nuevas. Los folds comparten ajuste, aunque los componentes retenidos sean disjuntos.', '',
        '## Qué aporta el ajuste exterior guardado','',
        'También se leyeron las tasas de ajuste ya guardadas para edificios. Son 50.320 apariciones de 12.580 periodos originales, cuatro usos por periodo entre modelos. Cada modelo deja fuera un fold y ve los otros cuatro. Estos valores son de ajuste, no tasas internas fuera de muestra del contraste propuesto.', '',
        '| Fold exterior excluido | Positivos del ámbito de ajuste | Positivos banda 1 / banda 5 | log(P80/P20) de tasa de ajuste |',
        '| --- | ---: | ---: | ---: |']
    for x in proxy:
        tails={c['band']:c for c in x['tail_cells']}
        lines.append(f"| {x['fold']} | {x['positive_groups']} | {tails[1]['positive_groups']} / {tails[5]['positive_groups']} | {es(x['log_P80_minus_P20'],4)} |")
    lines += ['', 'En esos cinco ámbitos exteriores hay de 385 a 409 componentes positivos y un rango log(P80/P20) entre 0,8583 y 1,1036. Es mayor que log(1,25)=0,2231, pero el requisito del diseño se refiere al ámbito interno de calibración. No se traslada esa comprobación a tasas que todavía no existen. Las colas inferiores del ajuste exterior solo tienen de 42 a 53 positivos y conservan concentración; este contexto tampoco certifica soporte interno.', '',
        'El futuro procedimiento tendría diez conjuntos únicos de tres folds para generar veinte predicciones internas ordenadas. El material actual tiene cinco modelos exteriores entrenados con cuatro folds. Las predicciones de ajuste guardadas vieron las etiquetas de sus propias filas; no pueden rebautizarse como OOF internas. Tampoco puede usarse sin más la OOF de otro fold si su modelo o C0 vio el fold exterior.', '',
        '## Evidencia que ahora queda resuelta y la que falta','',
        '| Cuestión | Resultado de esta auditoría | Consecuencia |',
        '| --- | --- | --- |',
        '| Soporte retenido por fold de las dos colas | Inventario completo: cinco celdas fallan por dos criterios de concentración; mínimos de positivos cumplidos | Carencia medida, condición incumplida; no autoriza ajuste |',
        '| Soporte de las colas agrupadas | Banda 1 falla; banda 5 pasa solo agrupada | La agregación no sustituye cada fold |',
        '| Tasas y C0 internos sin ambos folds | No existen en estos artefactos; lo guardado excluye solo el fold exterior | No puede acreditarse sin un procedimiento distinto; no se produce aquí |',
        '| Soporte de cada ámbito interno y su rango de log-tasa | Sigue desconocido; el ajuste exterior es solo contexto | No se marca como cumplido ni se extrapola de sus recuentos |',
        '| Implementación estricta y coste de primera etapa | Adaptador 2023, grafo de ancestros y enumeración de flujos C0 aún pendientes | No invocar productores históricos que recorren otros años |',
        '| Mecanismo residual y beneficio | Pendiente, intercepto y mejoras no estimados; los costes concentrados siguen siendo explicación rival | No promocionar, recalibrar o añadir complejidad |', '',
        'Para superar la concentración haría falta evidencia legítima que cambie la información disponible y satisfaga las reglas conservadas. Volver a sumar estas mismas filas no crea componentes nuevos. Una corrección de origen solo sería admisible si hubiese evidencia de un error; esta auditoría no detecta ni declara inválidos los siniestros. No se recortan importes, eliminan costes grandes, combinan bandas después de ver resultados o relajan topes para obtener elegibilidad.', '',
        'La documentación adicional del grafo o un lector más estricto puede resolver riesgos de implementación, pero no borra el incumplimiento numérico ya observado. Incluso un soporte completo del ajuste interno no anularía la pantalla retenida fallida. El mandato vigente mantiene el contraste sin ejecución.', '',
        '## Verificación y decisiones','',
        'Pasaron 911 comprobaciones propias de esta auditoría, sin fallos. El productor clasifica celdas guardadas; el comprobador reconstruye cantidades de soporte con diccionarios y centavos a partir de las filas guardadas. Los umbrales se contrastan además con fracciones exactas. Se conservaron los 50.094 periodos OOF, los 30.869 componentes y todo su T0; las 75 celdas particionan las filas sin exclusión. Las celdas de coste nulo o vacías conservan concentración indefinida y no acreditan soporte.', '',
        'También se cotejaron las tasas de ajuste y sus cortes ya guardados, las fronteras inclusivas de los umbrales y los casos indefinidos. No se repitieron las suites de entrenamiento o calibración, inferencias o bootstrap. Las cifras de controles acreditan esta conciliación, no independencia profesional, potencia estadística o mejora predictiva.', '',
        'Se mantienen los umbrales, los siniestros y todos los candidatos. B00 conserva la referencia y B01–B20 permanecen como alternativas; contador propio 195 ajustes de precio y 285 constantes, sin cambios. Cero parámetros, ajustes, tasas nuevas, modelos cargados, remuestreos o recetas. La condición de soporte sigue fallida, sin promoción o complejidad añadida.', '',
        '2024, test, actas, scores, SEL01 y ledger siguen cerrados en este trabajo. La exposición previa a un título de otro chat se mantiene declarada sin usar sus cifras o afirmar ceguera completa. Codex firma esta comprobación propia, que no constituye revisión humana o profesional independiente. Documentación IAA §§2–3 y Gobernanza §2.8 orientan procedencia y alcance; los umbrales pertenecen al diseño del proyecto.', '',
        '[Plan](../../registro/semana2_b20_soporte_folds_plan_v1.json), [índice y recibos](../../registro/semana2_b20_soporte_folds_actual.json), [diseño condicionado](DISENO_CONTRASTE_MINIMO_B20_2023.md) y [bandas originales](CALIBRACION_B20_BANDAS_AJUSTE_2023.md). Los 75 registros por fold, 15 agrupados, cinco vistas de ajuste, decisiones, fuentes SHA y snapshots están en la corrida privada `b20_soporte_folds_20261024_v1`, fuera de Git.']
    DOC.write_text('\n'.join(lines)+'\n',encoding='utf-8')
    decisions=[
        ('SUP-01','Aplicar exactamente las reglas congeladas del diseño','Diez celdas retenidas y dos colas agrupadas de edificios, sin umbrales nuevos.'),
        ('SUP-02','Registrar cinco celdas fallidas en cuatro folds','Todos los mínimos de positivos pasan; fallan concentración máxima y equivalente.'),
        ('SUP-03','Mantener cada siniestro, componente, fold y banda','No convertir sensibilidad o coste alto en error ni buscar una submuestra elegible.'),
        ('SUP-04','No sustituir reglas por promedios o redondeos','La banda5 agrupada pasa pero fold4/banda5 falla; fold2/banda1 no alcanza3.'),
        ('SUP-05','Separar vistas de ajuste exterior y soporte interno requerido','Tasas guardadas4/5 in-sample y positivos/rango no prueban la calibración interna3/5.'),
        ('SUP-06','Cerrar el inventario retenido y mantener incumplimiento y carencias','Se mide la condición fallida; faltan predicciones internas/C0, soporte y preflight estricto.'),
        ('SUP-07','Conservar contraste sin ejecución y sin más complejidad','La auditoría no estima pendiente, beneficio, parámetro, causa o coste último.'),
        ('SUP-08','Conservar B00 y todas las alternativas, contadores y límites','2024/test/ledger cerrados, sin entrenamiento/remoto o cambios de automatizaciones.')]
    dump(RUN/'decision_journal.json',{'id':p['id'],'author':'Codex','utc':now,'decisions':[
        {'id':a,'decision':b,'basis':c} for a,b,c in decisions]})
    dump(RUN/'evidence_gaps.json',{'id':p['id'],'resolved_inventory':'All10heldoutfoldtailcells classified under unchanged rules.',
        'failed_condition':'Fivecells in fourfolds; pooledband1 also fails. No threshold relaxation or exclusions.',
        'pending':r['missing_evidence'],'outer_proxy_does_not_resolve_inner':True,
        'additional_documentation_cannot_erase_measured_concentration':True,'can_execute':False})
    (RUN/'code').mkdir()
    codes=[REPO/'src/semana2/auditar_soporte_b20_folds2023.py']+[REPO/'herramientas'/x for x in
        ['preparar_auditoria_soporte_b20_folds2023.py','verificar_soporte_b20_folds2023.py','documentar_soporte_b20_folds2023.py']]
    for code in codes:(RUN/'code'/code.name).write_bytes(code.read_bytes())
    outputs=[DOC]+[RUN/x for x in ['report.json','verification.json','fold_cell_audit.json','pooled_cell_audit.json',
                 'outer_training_proxy.json','decision_journal.json','evidence_gaps.json']]
    dump(RUN/'manifest.json',{'id':p['id'],'author':'Codex','inputs':p['frozen_sources'],
        'outputs':[ev(x) for x in outputs],'code_snapshots':[ev(RUN/'code'/x.name) for x in codes],
        'new_fits':0,'new_inference':0,'claims_or_groups_excluded':0})
    idx={'id':p['id'],'author':'Codex','utc':now,'path_base':'workspace_root',
        'status':'saved_fold_support_verified_five_cells_failed_four_folds_no_execution',
        'run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),
        'plan':rel(REPO/'registro/semana2_b20_soporte_folds_plan_v1.json'),'plan_sha256':r['source_plan_sha256'],
        'report':ev(RUN/'report.json'),'verification':ev(RUN/'verification.json')|{'passed':911,'failed':0},
        'fold_cells':ev(RUN/'fold_cell_audit.json'),'pooled_cells':ev(RUN/'pooled_cell_audit.json'),
        'outer_training_proxy':ev(RUN/'outer_training_proxy.json'),'decision_journal':ev(RUN/'decision_journal.json'),
        'evidence_gaps':ev(RUN/'evidence_gaps.json'),'manifest':ev(RUN/'manifest.json'),
        'fold_gate_cells':10,'fold_gate_passed':5,'fold_gate_failed':5,'failed_folds':[1,2,3,4],
        'source_count':len(p['frozen_sources']),'support_gate':'failed','inner_oof_support_established':False,
        'fit_authorized':False,'can_execute':False,'new_fits':0,'new_inference':0,'parameters_estimated':0,
        'new_bootstrap':0,'new_recipes':0,'claims_or_groups_excluded':0,'thresholds_relaxed':False,
        'reference':'W2-B00','promotion':False,'all_alternatives_preserved':True,'2024_test_closed':True,'ledger_read':False,
        'prior_external2024_header_exposure_disclosed':True,'complete_blindness_claim_allowed':False,
        'professional_independent_validation':False,'forum_prior':p['forum_prior'],'forum_result':p['forum_result'],
        'next_step':'Reuse saved failed support receipt. No training or threshold relaxation; inner evidence and strict scoped preflight remain missing and cannot erase observed heldout failure.'}
    dump(INDEX,idx)
    np=REPO/'registro/semana2_continuidad_nocturna.json';n=read(np);before=n.get('current_unit')
    assert not any(x['id']==p['id'] for x in n['completed_units'])
    unit={'id':p['id'],'run':rel(RUN),'documentation':rel(DOC),'index':rel(INDEX),'verification':idx['verification'],
        'decision_journal':idx['decision_journal'],'completed_utc':now,'forum_result':p['forum_result'],
        'new_fits':0,'new_inference':0,'support_gate':'failed','fit_authorized':False}
    n['completed_units'].append(unit)
    if (n.get('current_unit') or {}).get('id')==p['id']:n['current_unit']=None
    elif p['id'] in n.get('parallel_artifact_diagnostics',{}):
        n['parallel_artifact_diagnostics'][p['id']].update(status='completed_support_failed',index=rel(INDEX))
    n['latest_completed_unit'],n['updated_utc']=unit,now
    n['latest_b20_fold_support_index']=rel(INDEX);n['no_repetition_for_completed_b20_fold_support']=True
    n['integration_decisions']['B20_fold_support']='10heldoutbuildingtailcells:5fail in folds1/2/3/4, all on maxcostshare+concentrationequivalent; positivecounts pass. Outertraining context is not innerOOF; no fit or threshold relaxation.'
    n.setdefault('condition_progress_without_auto_closure',{})['B20-fold-support']='Inventory completed and exactcostchecked, but support condition FAILS; innerOOF evidence remains missing, no automatic closure.'
    n['next_unit']='Saved B20 fold-support audit is complete: read latest_b20_fold_support_index without repeating suites. Fiveheldouttailcells fail in fourfolds under unchanged rules; no fitting, calibration, newprices, exclusions, rebinning or threshold relaxation. Only separate necessary evidence/scoped-preflight review may be designed; innerOOF artifacts are not generated under current no-training scope. Own2024/test/ledger stayclosed; preserve window/incident and any concurrent authorized unit.'
    if n.get('current_unit') is None:n['status']='scheduled_'+str(len(n['completed_units']))+'_units_B20_fold_support_audited_failed_no_training'
    dump(np,n)
    dump(RUN/'registration_receipt.json',{'id':p['id'],'utc':now,'previous_current_unit':before,
        'current_unit_after':n.get('current_unit'),'preserved_other_current_unit':
            (before or {}).get('id') in (None,p['id']) or before==n.get('current_unit'),
        'window_end':n['window_end'],'frequency':n['frequency'],'completed_units_at_cut':len(n['completed_units']),
        'automation_toml_changed':False})
    rp=ROOT/'RUTAS_PROYECTO.json';routes=read(rp)
    routes.update(week_2_b20_fold_support_index=rel(INDEX),week_2_b20_fold_support_report=rel(DOC),
                  week_2_b20_fold_support_plan=idx['plan']);dump(rp,routes)
    sp=ROOT/'Preparación/ESTADO_PROYECTO.json';raw=sp.read_text(encoding='utf-8-sig');key='semana2_b20_soporte_folds2023_20261024'
    assert key not in json.loads(raw)
    state={'utc':now,'author':'Codex','path_base':'workspace_root','index':rel(INDEX),'status':idx['status'],
        'fold_gate_failed':5,'failed_folds':[1,2,3,4],'support_gate':'failed','fit_authorized':False,
        'new_fits':0,'new_inference':0,'claims_or_groups_excluded':0,'thresholds_relaxed':False,'2024_test_closed':True}
    sp.write_text(raw.replace('{','{\n  '+json.dumps(key)+': '+json.dumps(state,ensure_ascii=False)+',',1),encoding='utf-8')
    note=('\n\n## '+p['id']+': auditoría del soporte por fold sin relajar reglas\n\nCodex, UTC '+now+
        '. Encargo humano: auditar soporte B20 guardado, sin relajar/excluir/reentrenar o abrir2024/test. Plan y foro SUPPORT-PRE antes del análisis. '
        '24fuentes congeladas con SHA/snapshots;75celdas retenidas de ramo/fold/banda y15agrupadas inventariadas. Solo10colas edificios1/5 porfold '
        'y2agrupadas son puerta del diseño; no se extienden umbrales a otrosramos o bandas.\n\n'
        'Fallan5/10celdas en4folds: banda1 de folds1,2,3,4 y banda5 de fold4. Todas alcanzan≥10grupos positivos (11–28); '
        'las cinco fallan máximo50% de coste y equivalente≥3. Mayorparticipación/equivalente:fold1b1 62,62%/2,30;fold2b1 55,38%/2,91; '
        'fold3b1 91,82%/1,18;fold4b1 71,39%/1,87;fold4b5 66,75%/2,17. Solo fold0 pasa ambascolas. '
        'Agrupadas:banda1 69positivos/31,65%/6,09 falla reglas50/20%/10;banda5 124/19,02%/14,16 pasa soloesa celda. '
        'Sin redondeo para decidir, promedios entrecolas o selección de folds.\n\n'
        'Cinco vistas de ajuste exterior guardadas4/5 tienen385–409positivos y log(P80/P20)0,8583–1,1036; '
        'la colainferior tiene42–53positivos. Son50.320apariciones de12.580periodos, no nuevasmuestras. '
        'No constituyen predicciones internas fuera de muestra3/5 o C0 excluyendo ambosfolds; soporte/rango internos siguen desconocidos. '
        'Faltan esas fuentes, adaptador estricto2023/grafo/costeprimeraetapa y evidencia delmecanismo/beneficio; no se genera aquí. '
        'Resolver documentación no borra concentraciónretenida fallida.\n\n'
        'Pasaron911comprobaciones propias específicas sinfallos: celdas guardadas frente a centavos/diccionarios y umbrales con fraccionesexactas. '
        '50.094periodos y30.869componentes completos, T0conservado; sin repetir suites de modelado/calibración o bootstrap. '
        'Ocho decisiones registradas. Cero ajuste/parámetro/inferencia/modelocargado/remuestreo/recetanueva/exclusión o relajación. '
        'B00/B01–B20 y contador195/285 exactos; puerta fallida, sin promoción o complejidad. '
        'Informe docs/archivo/semana2/SOPORTE_B20_POR_FOLD_2023.md e índice registro/semana2_b20_soporte_folds_actual.json; corrida privada b20_soporte_folds_20261024_v1.\n\n'
        '2024/test/actas/scores/SEL01/ledger cerrados; exposición previa del título ajeno declarada sin uso/ceguera completa. '
        'Revisión propia, no profesional independiente. Memoria/estado/decisiones/rutas/continuidad actualizados; ventana/incidente/otrasautomatizaciones '
        'y cualquierunidadconcurrente preservados. No remoto, envío, delegación o mensajeexterno.\n')
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        with (ROOT/'Preparación'/name).open('a',encoding='utf-8',newline='') as f:f.write(note)
    update=('\n\n## Soporte por fold B20 auditado; condición fallida\n\nLa [auditoría](SOPORTE_B20_POR_FOLD_2023.md) '
        'clasifica diez colas retenidas de edificios: cincofallan en cuatrofolds por concentración, aunque todas cumplenpositivos. '
        'Solo fold0 pasaambas. Bandas/umbrales y todoslossiniestros intactos. 911comprobaciones específicas propias sinfallos; '
        'ajusteexterior guardado solo contexto, soporteinternoOOF aún desconocido. No entrenar ni repetir diagnósticos. '
        'B00/B01–B20, contador195/285, 2024/test/ledger cerrados y ventana/programación conservados; balanceparcial.\n')
    for name in ['PLAN_NOCTURNO_20261023.md','BALANCE_NOCTURNO_PARCIAL_20261024.md']:
        with (REPO/'docs/archivo/semana2'/name).open('a',encoding='utf-8',newline='') as f:f.write(update)
    body=('Resultado de '+p['forum_prior']+': soporte B20 porfold bajo umbrales intactos del diseño. 75celdas retenidas y15agrupadas inventariadas; '
        'puerta solo10colas edificios1/5 y2agrupadas. Fallan5/10celdas en4folds:banda1folds1,2,3,4 ybanda5fold4. '
        'Todas≥10positivos; fallan ambasconcentraciones (máximo50%/equivalente3). Mayor%/equivalente:62,62/2,30;55,38/2,91;91,82/1,18;71,39/1,87;66,75/2,17. '
        'Solo fold0 pasaambas. Agrupadabanda1 falla31,65%/6,09;banda5 pasa19,02%/14,16 sin ocultarfold4.\n\n'
        'Vistasexteriores4/5:385–409positivos ylogP80/P20 .8583–1.1036, pero son tasas deajuste (50320apariciones/12580periodos), '
        'no innerOOF3/5 niC0 excluyendodosfolds. Soporte/rango internos, adaptador/grafo/costeprimeraetapa y mecanismo/beneficio siguenpendientes. '
        'Documentación adicional no borra incumplimientonumérico. No umbralesrelajados, costesrecortados, exclusiones, rebinning o entrenamientos.\n\n'
        '911comprobaciones específicas propias sinfallos con centavos/diccionarios y reglasracionales; 50094periodos/30869componentes/T0conservados. '
        'Ocho decisiones; cero parámetro/fit/inferencia/modelocargado/bootstrap/recetanueva. B00/B01–B20 y195/285intactos. '
        'Informe docs/archivo/semana2/SOPORTE_B20_POR_FOLD_2023.md; índice registro/semana2_b20_soporte_folds_actual.json. '
        '2024/test/actas/scores/SEL01/ledgercerrados; exposiciónprevia de títuloexterno declarada sinuso/cegueracompleta; revisiónpropia sinindependenciaprofesional. '
        'Continuidad actualizada con puerta fallida, sin permisooperativo para entrenar; ventana/incidente/otrasautomatizaciones y unidadconcurrente preservados.\n')
    (REPO/'registro'/(p['forum_result']+'_cuerpo.md')).write_text(body,encoding='utf-8')
    print(json.dumps({'document':rel(DOC),'index':rel(INDEX),'completed_units_at_cut':len(n['completed_units']),
        'passed':v['passed'],'support_gate':'failed','new_fits':0}))


if __name__=='__main__':
    main()
