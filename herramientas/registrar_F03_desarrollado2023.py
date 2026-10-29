"""Integra F03 documental sin ejecutar productores, modelos o diagnósticos."""
from pathlib import Path
from datetime import datetime,timezone
import json,hashlib,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/revision_F03_2023/f03_20261024_v1'
DOC=REPO/'docs/archivo/semana2/F03_DESARROLLADO_2023_Y_MECANISMO_B20.md'
INDEX=REPO/'registro/semana2_F03_desarrollado2023_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-F03-DESARROLLADO2023-v1-20261024';FID='COD-S2-20261024-054'
STATEKEY='week_2_F03_developed_context2023_v1_20261024'
now=lambda:datetime.now(timezone.utc).isoformat()
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,val):
    value=json.dumps(val,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+value+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+value+raw[m.end()+end:]

def main():
    assert not INDEX.exists() and not DOC.exists()
    schema=read(RUN/'schema_dictionary_receipt.json')
    assert schema['dictionary_unchanged_from_archive'] and schema['row_values_read']==0
    assert all(not x['common_type_differences'] for x in schema['comparison'])
    b20=read(REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json')
    prior=read(REPO/'registro/semana2_desarrollo2023_plan_v6.json')['credibility_rule']
    assert b20['recipe']['params']['alpha']==1 and 'developed2021-2023' in prior['developed_prior']
    paths=[SOURCE,REPO/'registro/semana2_b20_fuentes2023_plan_v1.json',REPO/'registro/semana2_F02_disponibilidad2023_actual.json',REPO/'registro/semana2_contenido_oficial_actual.json',REPO/'registro/semana2_b20_mecanismo_soporte_revision_actual.json',REPO/'registro/semana2_b20_soporte_folds_actual.json',REPO/'registro/semana2_glm_ridge_coberturas_plan_v1.json',REPO/'registro/semana2_desarrollo2023_plan_v6.json',REPO/'src/semana2/entrenar_glm_ridge_coberturas2023.py',REPO/'src/semana2/entrenar_desarrollo2023_v8.py',REPO/'src/semana2/credibilidad2023.py',REPO/'src/semana2/variables_ultimo.py',ROOT/'Hackaton/Semana 2/Claude/decisiones_20261023/aplicar_decisiones.py',REPO/'docs/archivo/semana2/CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md',REPO/'registro/semana2_desarrollo2023_actual.json',REPO/'registro/semana2_contadores_propios_actual.json',REPO/'registro/semana2_continuidad_nocturna.json']
    sources=[]
    for i,p in enumerate(paths):
        q=RUN/'sources'/f'{i:02d}_{p.name}';q.parent.mkdir(exist_ok=True)
        with q.open('xb') as f:f.write(p.read_bytes())
        sources.append({'path':rel(p),'snapshot':rel(q),'sha256':sha(p),'intentional_mutable_source_index':p==SOURCE})
    dump(RUN/'source_manifest.json',{'id':IDENT,'utc':now(),'sources':sources,'schema_receipt':rel(RUN/'schema_dictionary_receipt.json'),'prior_author':'Claude; reviewed/summarized by Codex, not reexecuted','raw_parquet_content_checks_reused':'F01; no repeat download/hash sweep'})
    matrix=[
      {'block':'Keys and groups','established':'Official dictionary forbids joins across markets: equal IDs may identify unrelated records.','contribution':'Namespace every key by market in any future comparison; maintain separate within-market linkage.','not_established':'Entity equivalence or independent emergent support.'},
      {'block':'Target and exposure','established':'Same documented row total, CU, net excess/recoveries, exclude repudiated, exposure in years, loss-date assignment; shared valuation2024-12-31.','contribution':'Define a comparable estimand for occurrence-year2023.','not_established':'Equal risk levels, reserve adequacy, policy wording, or ultimate truth; no target values compared.'},
      {'block':'Buildings risk fields','established':'Same common column types; developed exact policyholder_age versus emerging age_band; construction literal categories differ.','contribution':'Clarify materials, property use, AD option and net excess terms.','not_established':'MIX equivalence to solely non-standard, or identical contractual coverage/measurement/as-of.'},
      {'block':'Geography and other lines','established':'R01-R12 versus E01-E06; no documented crosswalk. Developed has exact motor age, mileage, telematics; emerging uses age bands and lacks those extra features.','contribution':'Identify representational differences before interpreting transported relativity.','not_established':'Aligned regional effects, shared full covariate distribution or transportable price coefficients.'},
      {'block':'Historical prior','established':'Recorded developed prior and seasonality pool2021-2023; auxiliary Poisson/Gamma, not isolated2023 Tweedie ridge.','contribution':'Existing process evidence and a warning about mismatched effects/objectives.','not_established':'New2023-only replicate, new independent source, evidence for ridge alpha1 or numerical validation of raw prior.'},
      {'block':'B20 mechanism/support','established':'B20 recipe uses emerging T0/C0 and seven main effects per line with alpha1; no developed coefficient-centred penalty is declared.','contribution':'Separate coefficient regularization hypothesis from credibility/transportability.','not_established':'Cause of shrinkage benefit, emergent low-band slope correction, independent components or passing heldout support.'}
    ]
    review={'id':IDENT,'author':'Codex','utc':now(),'scope':'F03 documentary correspondence for developed occurrence2023 only; no empirical market/score comparison, raw row values or numerical diagnostic','matrix':matrix,'existing_developed_prior_years':[2021,2022,2023],'isolated2023_prior_reconstructed':False,'current_B20_developed_coefficient_prior':False,'market_keys_can_collide':True,'cross_market_join_performed':False,'schema_common_type_differences':False,'G1':'plausible_not_established','G2':'existing_emerging_support_failure_unchanged','new_emerging_components':0,'new_2023_cohort':False,'row_values_read':0,'new_fits':0,'model_loads':0,'new_predictions':0,'new_scores':0,'new_numerical_diagnostics':0,'new_bootstrap':0,'target_exposure_C0_folds_changed':False,'reference':'W2-B00','all_alternatives_preserved':True,'2024_test_model_validation_opened':False,'prior_external2024_subject_exposure_disclosed':True,'professional_independent_validation':False,'night_window_reopened':False}
    dump(RUN/'documentary_review.json',review)
    doc=f'''# F03: mercado desarrollado de 2023 y mecanismo de B20

Codex, corte UTC {review['utc']}. El mercado desarrollado aporta definiciones y un contexto para formular hipótesis de heterogeneidad. Esta revisión documental no establece que la contracción de B20 corrija sobreajuste, una pendiente o un efecto causal. Tampoco aporta nuevos componentes al soporte emergente. G1 sigue plausible y no establecido; el incumplimiento de soporte emergente G2 conserva su estado anterior, sin repetir su diagnóstico.

## Alcance de lo comprobado

Se releyó el [diccionario oficial de Kaggle](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/data), idéntico al archivado. Se cotejaron nombres y tipos de las tres tablas de pólizas, clientes, direcciones y siniestros en ambos mercados. De edificios emergente se reutilizó el recibo F02. Se inspeccionaron recetas y código fuente como texto, sin importar los productores, cargar modelos, abrir filas o ejecutar sus funciones.

La referencia a 2023 significa correspondencia para una eventual comparación de ocurrencia/periodo 2023. No se extrajo una cohorte desarrollada, midió su distribución, calculó un efecto ni certificó transporte empírico. Los originales son multiaño; solo se consultó su esquema común, sin estadísticas de grupos de filas. Se reutiliza la identidad binaria de F01: la republicación no añadió datos.

## Qué puede compararse y qué sigue condicionado

| Aspecto | Correspondencia comprobada | Límite para B20 |
| --- | --- | --- |
| Unidad y objetivo | Coste total del periodo en CU, neto de franquicias y recuperaciones; rechazados excluidos; exposición en años | Compartir unidad/definición no iguala nivel de riesgo, reservas, gastos o suscripción |
| Asignación | Póliza y fecha de ocurrencia dentro del periodo, incluido un posible subperiodo por cambio contractual | Una fila no es siempre una anualidad completa; no trasladar conteos o denominadores sin conciliación propia |
| Valoración | Ambos mercados valorados al 31-12-2024 | Para ocurrencias de 2023 el corte documental coincide, pero el último sigue sin observarse y las velocidades/reservas pueden diferir |
| Edificios | Capital, material, uso, desocupación, alarmas, AD y franquicias tienen campos equivalentes en el esquema | Mismos nombres/tipos no prueban iguales distribuciones, condiciones contractuales o disponibilidad al cotizar |
| Edad | Edad exacta en desarrollado, bandas en emergente | No trasladar un coeficiente de edad exacta como si fuera un contraste de bandas; no reconstruir edades individuales |
| Regiones | R01–R12 frente a E01–E06 | No hay correspondencia regional documentada; no equiparar códigos por número o semejanza |
| Autos y clientes | Desarrollado añade kilometraje, telemática, edad exacta, fecha de nacimiento y banda crediticia; emergente tiene otras representaciones | Una relación ajustada con más información no estima necesariamente el mismo efecto en emergente |

No aparecieron diferencias de tipo en las columnas comunes de las seis tablas cotejadas. Esto acredita compatibilidad de representación, sin comprobar valores, calidad, distribución o causalidad. Los identificadores son únicos dentro de cada mercado, pero pueden repetirse entre mercados para registros distintos. El diccionario ordena unir tablas solo dentro de su carpeta. Una comparación futura debe conservar el mercado en las claves y mantener separados los componentes y denominadores; no se hace ninguna unión entre carteras aquí.

Construcción requiere cuidado: desarrollado distingue brick/stone/timber/non-standard; emergente BRK/STN/WOD/MIX, donde MIX abarca mixto o no estándar. El mapa de códigos conserva significado amplio, pero MIX no acredita correspondencia uno a uno con solo non-standard. occupancy sigue siendo uso de vivienda, distinto de profesión. Las condiciones temporales de F02 continúan abiertas, especialmente ventana y carácter declarado/realizado de days_unoccupied. Más años en desarrollado no sustituyen declaraciones o endosos fechados. El capital tampoco queda validado por parecerse al de la otra cartera.

AD es una cobertura opcional y existe en ambos mercados. Su presencia común permite formular una pregunta contractual más precisa: qué costes netos y selección de riesgos representa cada indicador. No demuestra equivalencia del condicionado, selección de clientes o interacción con los perils. El diccionario no contiene el clausulado completo. Las franquicias no se deducen otra vez de pagos ya netos.

## El prior histórico y B20 son piezas distintas

La receta v6 documenta que los coeficientes, errores y estacionalidad recibidos de Claude se estimaron con desarrollado 2021–2023. La inspección de nb_credibilidad confirma esa lista de años. Es un agregado histórico que incluye 2023, no una estimación aislada de 2023. No se descompone un coeficiente no lineal agregado restando años, ni se atribuye a esta ficha una reproducción desde los datos originales. No se ejecutó el constructor histórico, que lee fuentes multiaño.

Ese prior pertenece a auxiliares Poisson de frecuencia y Gamma de severidad y a una adaptación de nuevo negocio. B20 es un GLM Tweedie 1,5 con enlace log y penalización ridge alpha=1, con siete efectos principales por ramo. Su receta no centra la penalización en coeficientes desarrollados. El código de ajuste usa T0 y e_cost_mix_1.0 emergentes, transforma los predictores dentro del ajuste y penaliza sus coeficientes. No corresponde interpretar su contracción como credibilidad hacia la cartera desarrollada.

La revisión anterior de autos nuevos ya dejó resultados adversos de la adaptación del prior y diferencias entre objetivos auxiliares y precio Tweedie. Se conserva esa evidencia sin repetirla, volver a medirla o convertirla en prueba de daño universal de todo transporte. Sí impide usar la mera existencia del prior como aprobación de su eficacia o como validación independiente de B20. Los errores del prior, referencias y estacionalidad también forman parte de su incertidumbre; compartir receta o año no asegura intercambio estadístico entre mercados.

Usar siniestros de 2023 valorados en diciembre de 2024 es análisis retrospectivo. No constituye información disponible al inicio de 2023 para cotizar. Una eventual comparación debe declarar el instante de decisión y el de valoración, sin llamar prospectivos a datos posteriores a ese instante. No se usan clima realizado futuro, primas comerciales como objetivo técnico o gastos para explicar el coste de siniestros.

## Consecuencia sobre el mecanismo y el soporte

F03 permite separar hipótesis: una reducción de varianza por regularización de los mismos efectos emergentes, heterogeneidad técnica omitida, mezcla contractual y diferencias de observación son mecanismos posibles con implicaciones distintas. Esta ficha no elige uno ni asigna signo o magnitud a los campos. La coincidencia de un signo en otra cartera, si algún día se comprobara, sería contexto de transportabilidad y no identificación causal del beneficio emergente.

El soporte de G2 es el de los grupos y costes emergentes en sus folds guardados. No se suman siniestros desarrollados, no se usa su volumen para elevar tamaños efectivos, no se reemplazan bandas ni se recalculan umbrales. Los registros desarrollados tampoco se declaran nuevos ejemplos emergentes independientes por pertenecer a otro mercado. La concentración de los costes ya medida sigue sin resolver.

## Evidencia que permitiría avanzar

Primero harían falta condiciones y declaraciones versionadas que acrediten comparabilidad de coberturas, franquicias y fechas de conocimiento en 2023. Para una comparación empírica posterior se necesitaría una extracción documentada de 2023 por mercado, asignación y unidades conciliadas, transformaciones comunes justificadas, corte de valoración explícito y revisión de solapamiento de características. No se implementa ni ejecuta esa comparación bajo esta solicitud documental.

Si se quisiera identificar un efecto desarrollado específico de 2023, haría falta un artefacto existente con linaje y ámbito exactos o un trabajo posterior expresamente delimitado. El prior 2021–2023 revisado no lo proporciona. Cualquier nueva receta tendría hipótesis, comparador estándar, criterios, configuración/coste y comentario previo, dentro del alcance autorizado entonces. Nada de ello remedia por sí solo G2: sigue faltando información emergente legítima adicional o una corrección material demostrada que cambie la evidencia.

F03 queda revisada como contexto documental, con transportabilidad numérica no establecida. B00 y todas las alternativas se conservan; T0/C0, exposición, folds, modelos y contadores quedan intactos. Cero entrenamiento, cargas de modelos, inferencias, scores o remuestreos. 2024, test, ledger, actas y SEL01 permanecen cerrados para datos y resultados de modelado. La exposición histórica de un asunto externo sigue declarada, sin repetir o usar sus métricas. La ventana nocturna y su automatización continúan cerradas. Revisión propia de Codex, no aprobación humana o validación profesional independiente.

## Evidencia conservada

El [índice F03](../../registro/{INDEX.name}) enlaza matriz, recibo de esquema/diccionario, fuentes con SHA y decisiones. [F02](F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md), [revisión de mecanismo/soporte](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md) y [evidencia adversa previa del prior](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) mantienen sus versiones. La documentación IAA de propósito/procedencia (§2) y modelo (§3), y gobernanza §2.8 orientan distinguir evidencia, supuesto y revisión propia; esta ficha no certifica aptitud actuarial.
'''
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[
      ('F03-01','Restringir F03 a correspondencia documental2023: esquema compatible no acredita transporte empírico, valores o efectos.'),
      ('F03-02','No unir identificadores ni sumar soporte entre mercados; G2emergente permanece sin cambio.'),
      ('F03-03','Prior recibido de Claude es2021-2023, no aislado2023; no reproducirlo ni presentar revisión como nueva validación independiente.'),
      ('F03-04','Distinguir Poisson/Gamma y credibilidad de B20Tweedie/ridge; su penalización no se centra en coeficientes desarrollados.'),
      ('F03-05','Preservar diferencias de edad,región,construcción y disponibilidad F02; requerir condiciones/captura fechadas, sin inventar equivalencias.'),
      ('F03-06','No cerrar G1/G2ni modificar B00/alternativas,T0/C0/folds o modelos; sin entrenar o repetir diagnósticos.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    body=f'''F03 solicitada, Codex. Revisión documental para comparación de mercado desarrollado2023, sin extraer filas o calcular nuevos diagnósticos. Informe: {rel(DOC)}. Matriz y recibos: {rel(RUN)}.

El diccionario vigente es igual al archivado; las columnas comunes de seis tablas por mercado conservan tipos. Edad exacta/bandas, variables de autos y codificación de construcción difieren. MIX emergente abarca mixto o no estándar; no es equivalencia exacta con solo non-standard. Regiones R/E sin cruce documentado. Los IDs pueden coincidir para riesgos distintos: el diccionario exige uniones solo dentro del mercado. No se unen carteras ni se suman componentes,positivos,denominadores o soporte efectivo al emergente.

Objetivo total por periodo, CU, coste neto, exposición y valoración31-12-2024 tienen correspondencia documental. No prueban mismo nivel, suscripción, reservas, condicionado o último observado. Datos2023 valorados después no son conocimiento al inicio2023. Condiciones temporales F02 siguen abiertas; no nueva admisión.

El prior histórico recibido de Claude y su estacionalidad agrupan desarrollado2021-2023. Código/plan revisados como texto; no ejecución ni nueva reproducción raw. No es artefacto aislado2023. Los auxiliares Poisson/Gamma y su credibilidad difieren del objetivo Tweedie de B20; B20ridge alpha1 no se centra en coeficientes desarrollados. Los adversos previos de la adaptación se conservan sin repetirlos o usarlos para declarar daño universal del transporte. El prior ya usado no es nueva confirmación independiente.

F03aporta semántica y preguntas de transportabilidad/heterogeneidad, no mecanismo demostrado ni soporte emergente nuevo. G1plausible/no establecido y G2incumplido siguen sin cambio. Faltan condiciones/declaraciones fechadas y comparabilidad de datos2023 para cualquier comparación empírica posterior; esta solicitud no la ejecuta. Haría falta nueva información emergente legítima o corrección material acreditada para cambiar la evidencia de soporte, no volumen desarrollado.

Decisiones F03-01 a F03-06,autor Codex. B00 y todas las alternativas,T0/C0/exposición/folds/modelos/contadores conservados.2024/test/ledger/actas/SEL01cerrados; sin filas de ningún año,entrenamiento,cargas,inferencias,scores o remuestreos. Ventana/automatización nocturna cerradas; sin mensajes externos o delegación. Revisión documental propia,no aprobación humana o validación profesional independiente.
'''
    fp=RUN/'forum_054.md'
    with fp.open('x',encoding='utf-8') as f:f.write(body)
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,'--asunto','F03: contexto desarrollado2023, prior histórico y límites para el mecanismo B20','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={k:v for k,v in review.items() if k!='matrix'}
    idx.update(path_base='workspace_root',status='F03_documentary_context_reviewed_transportability_unestablished_no_emerging_support_added',run=rel(RUN),documentation=rel(DOC),documentation_sha256=sha(DOC),forum_result=FID)
    for key,name in [('review','documentary_review.json'),('source_manifest','source_manifest.json'),('decision_journal','decision_journal.json'),('schema_receipt','schema_dictionary_receipt.json')]:idx[key]={'path':rel(RUN/name),'sha256':sha(RUN/name)}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.F03review.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def source_update(raw):
        for k,v in {'F03_status':idx['status'],'F03_review_index':rel(INDEX),'F03_completed_utc':now(),'F03_emerging_support_added':False,'F03_empirical_transportability_established':False}.items():raw=top(raw,k,v)
        return raw
    change(SOURCE,source_update)
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## F03: contexto desarrollado de 2023 y límites para B20

Codex, UTC {now()}, foro054, decisiones F03-01 a F03-06. Informe {rel(DOC)}, índice {rel(INDEX)}, recibos/matriz/fuentes SHA en {rel(RUN)}. Diccionario oficial vigente idéntico al archivado; comparación de nombres/tipos, sin valores, de seis tablas por mercado. F02 edificios emergente reutilizada. Sin diferencias de tipo en columnas comunes; diferencias de edad/bandas, autos y códigos de construcción. MIX no equivale solo a non-standard. IDs pueden coincidir entre riesgos distintos; uniones solo dentro de mercado, sin sumar componentes o soporte al emergente. Igual objetivo/unidad/valoración no prueba igual nivel, reservas, condicionado o distribución. F02 temporal sigue abierto.

Prior recibido de Claude es agregado desarrollado2021-2023, no aislado2023; se revisaron plan/código como texto sin ejecución. Auxiliares Poisson/Gamma/estacionalidad/credibilidad difieren de B20Tweedie ridge alpha1: B20no se centra en coeficientes desarrollados. Adversos previos conservados sin repetir ni declarar rechazo universal de transporte. F03es contexto documental, no nuevo mecanismo demostrado o confirmación independiente. G1plausible/no establecido y G2incumplido conservados; no nueva cohorte o soporte emergente. Faltan condiciones/declaraciones fechadas y correspondencia/ámbito2023 para comparación empírica posterior, no ejecutada. Para cambiar soporte faltaría información emergente legítima o corrección material demostrada.

B00 y todas las alternativas,T0/C0/exposición/folds/modelos/contadores intactos. Cero filas leídas,entrenamiento,cargas,inferencias,scores,remuestreos o diagnósticos repetidos.2024/test/SEL01/actas/ledgercerrados; exposición previa de asunto externo declarada sin repetir/usar métricas. Ventana/automatización nocturna cerradas. Sin contactos externos,nuevos chats o delegación. Revisión documental propia de Codex,no aprobación humana o validación profesional independiente.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_F03_developed_context_index',rel(INDEX)),'week_2_F03_developed_context_report',rel(DOC)))
    integrity={'id':IDENT,'utc':now(),'frozen_source_copies_intact':all(sha(ROOT/x['snapshot'])==x['sha256'] for x in sources),'original_model_contract_counter_night_sources_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in sources if not x['intentional_mutable_source_index']),'common_schema_types_equal':all(not x['common_type_differences'] for x in schema['comparison']),'documentary_scope_only':True}
    assert all(v for k,v in integrity.items() if isinstance(v,bool))
    dump(RUN/'documentary_integrity_receipt.json',integrity)
    dump(RUN/'registration.json',{'changes':changes,'price_catalog_mutations':0,'counter_mutations':0,'feature_contract_mutations':0,'model_code_mutations':0,'night_index_mutations':0})
    files=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/inspeccionar_esquemas_F03.py']
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'documentation':rel(DOC),'G1':review['G1'],'G2':review['G2'],'emerging_support_added':False,'new_fits':0,'row_values_read':0,'integrity':integrity},ensure_ascii=True))

if __name__=='__main__':main()
