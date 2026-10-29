"""Revisión documental delimitada de evidencia2023 existente; sin recalcular diagnósticos."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib, json, os, re, subprocess, sys

ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/desarrollo2023/evidencia_mecanismo_soporte_b20_20261024_v1'
DOC=REPO/'docs/archivo/semana2/EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md'
INDEX=REPO/'registro/semana2_b20_mecanismo_soporte_revision_actual.json'
NIGHT=REPO/'registro/semana2_continuidad_nocturna.json'
IDENT='S2-B20-EVIDENCIA-MECANISMO-SOPORTE2023-v1-20261024'
STATEKEY='week_2_B20_mechanism_support_evidence2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
rel=lambda p:p.relative_to(ROOT).as_posix()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    RUN.mkdir(parents=True,exist_ok=False)
    request='Dale, revisa si hay evidencia de2023 que permita resolver el mecanismo y el soporte de B20, sin repetir diagnósticos ni entrenar. Conserva B00, deja las decisiones en el foro y mantén2024cerrado.'
    (RUN/'user_request.txt').write_text(request+'\n',encoding='utf-8')
    names={
      'support':'semana2_b20_soporte_folds_actual.json','design':'semana2_b20_contraste_minimo_actual.json',
      'priorities':'semana2_b20_prioridades_actual.json','bands':'semana2_b20_bandas_calibracion_actual.json',
      'attribution':'semana2_b20_atribucion_actual.json','fire_AD':'semana2_b20_incendio_AD_actual.json',
      'trace':'semana2_b19_traza_actual.json','reserve':'semana2_sensibilidad_observacion_c0_reservas_v1_snapshot.json',
      'mixture':'semana2_sensibilidad_observacion_actual.json','calendar':'semana2_soporte_calendario2023_actual.json',
      'coverage':'semana2_coberturas_peril2023_actual.json','development':'semana2_desarrollo2023_actual.json',
      'counters':'semana2_contadores_propios_actual.json'}
    data={};sources=[]
    def freeze(p,label):
        snap=RUN/'sources'/f'{len(sources):02d}_{p.name}';snap.parent.mkdir(exist_ok=True)
        with snap.open('xb') as f:f.write(p.read_bytes())
        item={'label':label,'path':rel(p),'sha256':sha(p),'snapshot':rel(snap)};sources.append(item)
    for label,name in names.items():
        p=REPO/'registro'/name;data[label]=read(p);freeze(p,label)
    # Only new and directly relevant aggregate documents, no OOF/model/raw data.
    for label in ['support','design']:
        obj=data[label];p=ROOT/obj['documentation'];assert sha(p)==obj['documentation_sha256'];freeze(p,label+'_documentation')
    for label,key in [('support','evidence_gaps'),('support','fold_cells'),('support','outer_training_proxy'),('design','readiness')]:
        ref=data[label][key];p=ROOT/ref['path'];assert sha(p)==ref['sha256'];freeze(p,label+'_'+key)
    sup=data['support'];assert sup['support_gate']=='failed' and sup['fold_gate_failed']==5 and sup['failed_folds']==[1,2,3,4]
    assert data['design']['can_execute'] is False
    original_statuses=data['priorities']['original_gate_statuses']
    evidence=[
      {'id':'E01','source':'bands','question':'G1','supports':'Los A/E agrupados de edificios bajos/altos son compatibles con relatividades demasiado dispersas.',
       'does_not_establish':'Bandas intermedias no monótonas, variación por fold y pocos costes dominantes impiden establecer que esa sea la explicación residual robusta.',
       'disposition':'hypothesis_plausible_not_established'},
      {'id':'E02','source':'support','question':'G2','supports':'Inventario terminado: las10 celdas retenidas de ambas colas cumplen positivos;5 fallan por concentración en folds1/2/3/4. Solo fold0 cumple ambas colas. Banda1 agrupada también falla.',
       'does_not_establish':'El cumplimiento de banda5 agrupada o el mínimo de positivos no acredita el conjunto. No es falta de contar positivos; son concentraciones observadas bajo reglas de este diseño.',
       'disposition':'support_measured_and_failed'},
      {'id':'E03','source':'attribution','question':'G1','supports':'La mejora agregada se invierte al omitir pocos componentes favorables; el numerador de ganancias explica la inversión.',
       'does_not_establish':'No identifica una pendiente poblacional o un defecto de datos; los componentes se seleccionaron por sus resultados y no constituyen una población nueva.',
       'disposition':'concentration_rival_explanation'},
      {'id':'E04','source':'fire_AD','question':'G1','supports':'Los dos incendios fijados están ausentes del ajuste3 donde AD cambia de signo; la ganancia del incendio principal tiene pesos netos/brutos distintos.',
       'does_not_establish':'La composición es descriptiva, no causa única de AD, prueba de dispersión excesiva o razón para imponer signo/máscara. Las aproximaciones de influencia previas son de B19.',
       'disposition':'composition_rival_explanation'},
      {'id':'E05','source':'trace','question':'G1/G2','supports':'La traza de los12 grupos seleccionados concilió siniestros con originales al corte; no documentó un error que autorice invalidar los grandes costes revisados.',
       'does_not_establish':'La selección no es representativa ni una revisión de todas las transacciones; no certifica reservas/último ni descarta todo error posible. No hay corrección material nueva acreditada.',
       'disposition':'no_documented_source_correction'},
      {'id':'E06','source':'reserve','question':'G1','supports':'Los estreses previos de reserva/reporte separan sensibilidad del objetivo/enlace; la cola no observada no queda identificada.',
       'does_not_establish':'Factores de estrés no son reservas verdaderas ni nueva información de siniestros. No trasladan automáticamente un resultado de otro modelo al mecanismo de B20.',
       'disposition':'observation_uncertainty_context_not_resolution'},
      {'id':'E07','source':'mixture','question':'G1/G2','supports':'La mezcla por peril/negocio tiene celdas escasas y costes concentrados; sus pruebas previas no justificaron adoptar esa variante.',
       'does_not_establish':'No son una prueba directa nueva de la pendiente B20 o su soporte. No agregan componentes independientes o severidades futuras conocidas.',
       'disposition':'context_only_no_new_support'},
      {'id':'E08','source':'calendar','question':'G1','supports':'Negocio nuevo tiene menos exposición madura para retrasos largos; calendario y soporte de reporte permanecen como explicaciones rivales.',
       'does_not_establish':'No establece una causa del fallo de precios o una curva separada válida; no resuelve riesgos de censura y cola con información fuera del soporte.',
       'disposition':'maturity_rival_explanation'},
      {'id':'E09','source':'coverage','question':'G1/G2','supports':'El recibo de coberturas encontró costes positivos cerrados fuera de la máscara propuesta de daño accidental de hogar.',
       'does_not_establish':'No acredita que los costes estén mal ni permite cambiar denominador sin numerador coherente. Semántica contractual pendiente; no nueva exposición/siniestros admisibles que cure soporte.',
       'disposition':'structural_mask_not_supported'},
      {'id':'E10','source':'support','question':'G2/G4','supports':'Las tasas guardadas son exteriores, entrenadas con4folds. El contraste propuesto requeriría tasas/C0 internos que excluyan2folds.',
       'does_not_establish':'Las tasas de ajuste no son OOF internas. Los10 conjuntos internos de3folds no están acreditados en estos artefactos; fabricarlos requeriría entrenamiento y ni su eventual soporte borraría el fallo retenido.',
       'disposition':'inner_support_unknown_no_substitution'}
    ]
    for row in evidence:
        label=row['source'];row['source_index']=rel(REPO/'registro'/names[label]);row['source_id']=data[label]['id'];row['source_sha256']=next(x['sha256'] for x in sources if x['label']==label)
    verdict={'id':IDENT,'author':'Codex','utc':now(),'scope':'Existing named2023 aggregate artifacts only; not an exhaustive claim over every possible dataset/source.',
      'mechanism':'plausible_not_established','support':'measured_failed_for_existing_slope_design',
      'new_direct_evidence':'Completed fold-support audit resolves what was unknown about heldout tails: the gate fails; it does not make the design eligible.',
      'source_error_or_additional_2023_information_established':False,'sufficient_evidence_to_resolve_G1_G2':False,
      'current_slope_design_can_execute':False,'original_gate_statuses':original_statuses,'gates_closed':[],
      'g2_refinement':'heldout support no longer unknown; measured fail. Internal support remains unknown. No global model-invalidity inference.',
      'necessary_next_evidence':[
        'For mechanism: a pertinent new2023 fact that distinguishes or materially strengthens the residual dispersion hypothesis against level, concentration and maturation explanations. Unique causal proof is not required, but current descriptive association is insufficient for this design.',
        'For current support: legitimate additional2023 information or an evidenced material source correction that actually changes information under a versioned proposal. No such correction is established; changing thresholds, grouping bands or deleting costly claims does not supply evidence.',
        'Only after those requirements: strict2023 inner-scope preparation and complete resource/ancestor inventory. Engineering controls cannot erase the heldout screen failure.'],
      'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_closed':True,'promotion':False,
      'new_fits':0,'new_inference':0,'model_loads':0,'new_scores':0,'new_bootstrap':0,'new_numerical_diagnostics':0,'new_recipes':0,
      'professional_independent_validation':False,'prior_external2024_header_exposure_disclosed':True}
    dump(RUN/'evidence_ledger.json',{'id':IDENT,'author':'Codex','utc':now(),'evidence':evidence});dump(RUN/'verdict.json',verdict)
    rows='\n'.join('| '+x['id']+' | '+x['source_id']+' | '+x['disposition']+' |' for x in evidence)
    doc=f'''# Evidencia disponible de2023 sobre mecanismo y soporte de B20

Codex, corte UTC{verdict['utc']}. En los artefactos identificados no encontré evidencia suficiente para resolver el mecanismo o hacer admisible el contraste de pendiente de B20. La revisión por fold terminó después de la priorización y aporta evidencia nueva relevante: el soporte retenido ya está medido y falla. No se vuelve a calcular.

## Qué permite concluir la evidencia nueva

El [recibo de soporte por fold](SOPORTE_B20_POR_FOLD_2023.md) registra cinco incumplimientos entre diez celdas de las dos colas de edificios, repartidos entre cuatro folds. Las diez cumplen el mínimo de componentes positivos. Fallan concentración y número equivalente de costes; no basta incrementar un contador o invocar que hay positivos suficientes.

Las celdas fallidas son banda1 de folds1,2,3,4 y banda5 de fold4. Solo fold0 cumple ambas colas. El mayor componente supone91,82% del coste en fold3/banda1. La banda1 agrupada falla; banda5 agrupada cumple, pero eso no resuelve su fallo en fold4. Son cifras guardadas del recibo, sin nuevos porcentajes, D², umbrales o sumas.

Por tanto, una parte de G2 cambia de pregunta: ya no falta medir soporte retenido; la condición está medida e incumplida. El soporte interno sigue desconocido. Estas reglas son prudenciales del contraste ya diseñado, posteriores a los diagnósticos; no son requisitos IAA/Kaggle, una prueba de potencia o un veto a todos los modelos del conjunto. B20 permanece como alternativa, sin promoción o retirada.

## Qué explica y qué no explica el material existente

{rows}

Las bandas de edificios motivan la hipótesis de relatividades demasiado dispersas. Su variación por fold, compensaciones entre componentes y composición AD/incendio no distinguen esa hipótesis de explicaciones rivales con suficiente estabilidad. No se necesita identificar una causa única para cualquier investigación predictiva; tampoco basta una relación agregada para tratar este mecanismo como establecido. La revisión deja G1 plausible y abierta.

La traza de siniestros concilió los casos seleccionados con los originales a un corte de valoración. No aporta un error nuevo que permita borrar o corregir grandes costes para obtener elegibilidad. Su selección limitada tampoco certifica todo el archivo, reservas o coste último. Reservas, cola, mezcla, calendario y coberturas conservan incertidumbres documentadas; los estreses anteriores no son hechos nuevos de reserva verdadera ni pruebas directas adicionales de B20. No se extrapola una prueba de otro modelo para declarar resuelta su pendiente.

Los positivos fuera de la máscara propuesta de hogar impiden justificar ceros estructurales o cambiar solo el denominador. Esa discrepancia semántica no convierte los siniestros en errores ni crea más soporte. No se cambian T0, C0, exposiciones, coberturas, folds o componentes.

El material de ajuste exterior tampoco rellena la falta de OOF interna: vio las etiquetas de sus propias filas y excluye un fold, mientras el procedimiento interno propuesto debe excluir dos, también en C0 y transformaciones. No se rebautiza el replay de ajuste ni otra OOF como evidencia interna. Producirla requeriría un entrenamiento distinto, fuera de esta revisión; aun si pasara su soporte, seguiría pendiente el incumplimiento retenido ya observado.

## Decisión y evidencia que podría cambiarla

No ejecutar ahora el contraste. Mantener G1 abierta y G2 incumplida para ese diseño, separando el soporte interno desconocido. No recontar filas, repetir suites, aflojar topes, combinar bandas, cambiar cortes o retirar incendios para pasar. Un nuevo diseño requeriría su propia necesidad, sustento y receta; esta conclusión no selecciona otra familia o B21.

La decisión podría revisarse ante información2023 adicional legítima o una corrección material de origen sustentada por evidencia que cambie realmente la información. Esa fuente tendría que declarar procedencia, fecha de disponibilidad, componentes completos, alcance temporal y diferencia frente al corte actual. Nada de eso está acreditado como nuevo en los recibos examinados. Con los mismos componentes/costes, repetir diagnósticos no crea información. Se preservaría la versión fallida y se evaluaría el cambio bajo un diseño versionado; no se aplica una corrección hipotética.

Para G1 falta además un hecho pertinente que fortalezca o distinga el mecanismo residual frente a nivel, pocos costes grandes y maduración. Para G4 siguen pendientes los ámbitos internos estrictos2023, ancestros/C0 y recursos completos; preparar ingeniería no cierra G1/G2. Esta revisión no establece un inventario universal de todas las fuentes que podrían existir: su cobertura queda delimitada en fuentes y SHA.

## Alcance y trazabilidad

Se reutilizan diez piezas de evidencia de los índices nombrados. Solo se leen índices y documentos/JSON agregados guardados, con fuentes congeladas. Cero ajustes, carga de modelos, inferencias, nuevos scores, diagnósticos numéricos, remuestreos o recetas. Los controles de esta revisión son de integridad documental; no se repiten los911 controles de soporte ni otras suites y no se suman como validación predictiva independiente.

B00 conserva la referencia, todas las alternativas permanecen y2024/test/SEL01/actas/ledger siguen cerrados aquí. Se mantiene declarada la exposición previa a métricas en un asunto ajeno, sin reproducirlas, usarlas o afirmar ceguera completa. No remoto, envíos, publicación externa, mensajes a otros chats, delegación o cambios a automatizaciones. Investigación adaptativa, revisión propia de Codex, sin revisión profesional independiente o aprobación humana. Documentación IAA§§2–3 y Gobernanza§2.8 orientan procedencia y alcance; no certifican suficiencia de evidencia.

[Prioridades](PRIORIDADES_Y_EVIDENCIA_PENDIENTE_B20_2023.md), [diseño](DISENO_CONTRASTE_MINIMO_B20_2023.md), [soporte nuevo](SOPORTE_B20_POR_FOLD_2023.md) e [índice de esta revisión](../../registro/{INDEX.name}). Ledger de evidencia, veredicto, fuentes y decisiones en {rel(RUN)}.
'''
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    journal={'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'EV-01','decision':'Reutilizar la auditoría nueva por fold; G2retenido medido/fallido, no elegible. No repetir su diagnóstico.'},
      {'id':'EV-02','decision':'Mantener mecanismo plausible; separar evidencia directa, explicación rival y contexto de otros modelos.'},
      {'id':'EV-03','decision':'No hay corrección de origen o información2023 adicional nueva acreditada en las fuentes revisadas. No corregir/borrar costes para pasar.'},
      {'id':'EV-04','decision':'El ajuste exterior no sustituye OOF interna; ingeniería o más entrenamiento no borran el fallo retenido.'},
      {'id':'EV-05','decision':'No ejecutar, promover o retirar; conservar B00/alternativas,T0/C0 y2024cerrado. Cerrar esta revisión documental sin extenderla a nuevos diagnósticos.'}]}
    dump(RUN/'decision_journal.json',journal)
    fid='COD-S2-20261024-048'
    fb=f'''Codex. Respuesta a la instrucción directa de buscar evidencia2023 que resuelva mecanismo/soporte, a047 y B20-SUPPORT-RESULT. Revisión de diez piezas ya existentes, no repetición de diagnósticos. Informe:{rel(DOC)}; ledger y fuentes SHA:{rel(RUN/'evidence_ledger.json')}.

Resultado: no hay evidencia suficiente en las fuentes delimitadas para hacer admisible el contraste. La auditoría por fold nueva ya mide el soporte retenido:5/10celdas fallan por concentración en4folds; todas cumplen el mínimo de positivos. Solo fold0 pasa ambas colas. G2 pasa de no medido a medido/incumplido para esa parte, no a resuelto favorablemente. El soporte interno sigue desconocido; tasas exteriores/ajuste no lo sustituyen. No recalculé sus cifras o controles.

G1 sigue plausible: bandas sugieren dispersión excesiva, pero concentración/composición de costes, maduración y objetivo/enlace son explicaciones rivales. La traza concilió los casos seleccionados; no acredita una corrección material nueva. Los estreses de reservas/cola, mezcla y coberturas no añaden observaciones o verdad actuarial ni son nuevas pruebas directas de B20. La revisión no afirma ausencia universal de fuentes/error.

No entrenar este contraste ahora, borrar/recortar siniestros, modificar bandas o relajar umbrales para pasar. Para revisar la decisión falta información2023 adicional legítima o corrección real documentada que cambie información y sustento del mecanismo, con procedencia/fechas/grupos y versión que preserve el fallo. Ninguna se ha establecido en este corte. Ingeniería anidada puede atender G4, sin borrar G1/G2. EV-01 aEV-05 mantienen abiertas las carencias y distinguen reglas de este diseño de un veto universal a los datos/modelos.

Cero ajustes, cargas, inferencias, nuevos scores, diagnósticos numéricos o bootstrap. B00 y todas las alternativas conservados,T0/C0/folds intactos;2024/test/SEL01/actas/ledger cerrados. Exposición previa de asunto externo declarada sin usar métricas o afirmar ceguera completa. Revisión propia exploratoria, sin aprobación humana o validación profesional independiente; automatizaciones/otros chats sin cambios.'''
    fp=RUN/'forum_048.md';fp.write_text(fb,encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','Evidencia2023 de mecanismo y soporte B20: condición medida pero incumplida','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={**verdict,'status':'evidence_review_complete_mechanism_open_support_failed_no_execution','path_base':'workspace_root','run':rel(RUN),'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_result':fid,'sources':sources,'evidence_ledger':{'path':rel(RUN/'evidence_ledger.json'),'sha256':sha(RUN/'evidence_ledger.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')}}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.evidenciaB20.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
        with (RUN/'registration_steps.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(changes[-1])+'\n')
    entry={'id':IDENT,'author':'Codex','completed_utc':now(),'run':rel(RUN),'documentation':rel(DOC),'index':rel(INDEX),'forum_result':fid,'new_fits':0,'new_numerical_diagnostics':0,'new_scores':0,'mechanism':'plausible_not_established','support':'measured_failed'}
    def night(raw):
        n=json.loads(raw);assert not any(x['id']==IDENT for x in n['completed_units'])
        vals={'completed_units':n['completed_units']+[entry],'latest_completed_unit':entry,'latest_b20_mechanism_support_evidence_index':rel(INDEX),'updated_utc':now()}
        if n.get('current_unit') is None:vals.update(next_unit_before_B20_evidence_review=n.get('next_unit'),next_unit='Evidence review complete: no sufficient new2023 evidence establishes mechanism or cures measured heldout support failure. Reuse receipts; no new diagnostics, fitting, threshold relaxation, rebinning or exclusions on unchanged sources. Only genuine relevant new information/material source correction could justify versioned review; strict2023 preflight cannot erase failed support. Preserve B00/all alternatives, own2024/test closed and overnight window.',queue=['Current B20 slope proposal remains non executable; internal support unknown, heldout support measured failed.','Do not repeat completed evidence review or support diagnostics on identical sources.','Preserve existing incident monitor/window and honest07:00Bogota balance.'])
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(NIGHT,night)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## Evidencia2023 para mecanismo y soporte de B20

Codex, UTC{now()}. Instrucción directa revisada sin repetir diagnósticos o entrenar. Informe {rel(DOC)}, índice {rel(INDEX)}, foro048 y decisiones EV-01 aEV-05. La auditoría por fold ya terminada aporta nueva evidencia directa:5/10celdas de colas retenidas fallan por concentración en4folds aunque todas cumplen el mínimo de positivos. G2retenido está medido/incumplido; soporte interno sigue desconocido. No se recalcularon cifras o verificaciones de soporte.

Se revisaron diez piezas de evidencia: bandas, soporte, atribución, incendio/AD, traza, reservas/reporte, mezcla, calendario, coberturas y ámbitos internos. G1 sigue plausible, sin evidencia suficiente que distinga dispersión residual de concentración, composición, maduración u objetivo/enlace. No hay corrección material de origen o información2023 adicional nueva establecida en las fuentes delimitadas; no es afirmación universal sobre todas las fuentes posibles. La traza valida conciliación de casos seleccionados, no todo archivo o suficiencia actuarial. Ingeniería, tasas exteriores o cambiar topes/cortes/casos no resuelven el fallo retenido.

No ejecutar el contraste ahora. Solo evidencia adicional legítima o una corrección real documentada podría justificar revisión versionada conservando fallos; ninguna se aplica. B00 y todas las alternativas,T0/C0/folds conservados. Cero ajustes, cargas de modelos, inferencias, nuevos scores, diagnósticos numéricos, remuestreos o recetas.2024/test/SEL01/actas/ledger cerrados aquí; exposición previa de asunto externo declarada sin usar cifras o afirmar ceguera completa. Revisión propia exploratoria, sin revisión profesional independiente o aprobación humana. Otras conversaciones/automatizaciones y ventana intactas.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(REPO/'docs/archivo/semana2/PLAN_NOCTURNO_20261023.md',lambda raw:raw+f"\n\n## Evidencia2023 de mecanismo/soporte revisada sin nuevos diagnósticos\n\nCodex,{now()}. [Revisión de evidencia](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md), foro048: soporte retenido medido/fallido en el recibo existente; mecanismo plausible y soporte interno desconocido. Ninguna corrección material o información2023 nueva legítima acreditada en el corte. No repetir esta revisión o diagnósticos con fuentes iguales; no entrenar el contraste, relajar topes o alterar casos. B00 y alternativas conservados,2024cerrado; ventana/automatizaciones sin cambios.\n")
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_b20_mechanism_support_review_index',rel(INDEX)),'week_2_b20_mechanism_support_review_report',rel(DOC)))
    before=read(RUN/'registration_cuts/before'/NIGHT.relative_to(ROOT));after=read(RUN/'registration_cuts/after'/NIGHT.relative_to(ROOT))
    checks={'frozen_snapshots_exact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'source_indices_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources),'previous_completions_preserved':after['completed_units'][:-1]==before['completed_units'],'current_unit_preserved':after.get('current_unit')==before.get('current_unit'),'schedule_unchanged':after['window_end']==before['window_end'] and after['automation_id']==before['automation_id'],'own2024closed':after['confirmation_2024_open'] is False,'ten_evidence_items_unique':len(evidence)==len({x['id'] for x in evidence})==10}
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:
        p=ROOT/('Preparaci'+chr(243)+'n')/name;checks[name+'_prefix_preserved']=(RUN/'registration_cuts/after'/p.relative_to(ROOT)).read_bytes().startswith((RUN/'registration_cuts/before'/p.relative_to(ROOT)).read_bytes())
    dump(RUN/'integrity_receipt.json',{'id':IDENT,'author':'Codex','utc':now(),'checks':checks,'passed':all(checks.values()),'scope':'Only document/source/registration integrity; no statistical suites repeated.'});assert all(checks.values())
    dump(RUN/'registration.json',{'changes':changes,'active_catalog_mutations':0,'counter_mutations':0,'new_fits':0,'new_numerical_diagnostics':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve()]
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum':fid,'document':rel(DOC),'evidence_items':len(evidence),'integrity_ok':all(checks.values()),'sufficient_evidence':False,'new_numerical_diagnostics':0,'new_fits':0},ensure_ascii=True))

if __name__=='__main__':main()
