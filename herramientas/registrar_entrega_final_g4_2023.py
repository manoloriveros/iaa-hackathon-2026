"""Cierra modelo propio y CSV verificado; no envía a Kaggle ni reajusta."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib
import importlib.metadata as md
import json,os,sys,subprocess,zipfile
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(REPO/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import entradas_g4_2023 as ingress
from registrar_resultado_entradas_g4_2023 import top
RUN=REPO/'privado/semana2/modelo_final_g4_2023/final_20261024_v1'
PLAN=REPO/'registro/semana2_g4_modelo_final_plan_v1.json'
INDEX=REPO/'registro/semana2_g4_entrega_final_actual.json'
DOC=REPO/'docs/archivo/semana2/G4_MODELO_PROPIO_Y_CSV_2025.md'
PRIORITY=REPO/'registro/semana2_b20_prioridades_actual.json'
SOURCE=REPO/'registro/semana2_b20_fuentes2023_actual.json'
PREPARATION=REPO/'registro/semana2_g4_modelo_envio_preparacion_v1.json'
DEVELOPMENT=REPO/'registro/semana2_desarrollo2023_actual.json'
COUNTER=REPO/'registro/semana2_contadores_propios_actual.json'
IDENT='G4-STANDARD-CSV-READY-v1-20261024';FID='COD-S2-20261024-070'
STATEKEY='week_2_G4_own_model_and_CSV2025_ready_v1_20261024'
G4STATUS='standard_full2023_to2025_pipeline_verified_nested_calibration_trial_not_run'
now=lambda:datetime.now(timezone.utc).isoformat()
rel=lambda p:p.relative_to(ROOT).as_posix()
sha=ingress.sha
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))

def dump(p,o):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(o,f,ensure_ascii=False,indent=2);f.write('\n')

def main():
    assert not INDEX.exists() and not DOC.exists(), 'Reconcile partial closure before retry'
    result=read(RUN/'ready_current.json');plan=read(PLAN);out=ROOT/result['out']
    validation=read(out/'validation.json');guard=read(RUN/'guard1_verification.json');replay=read(RUN/'standalone_replay_guard1_receipt.json')
    assert result['success'] and validation['success'] and guard['success'] and replay['success']
    assert result['real_price_GLM_fits']==3 and result['real_reporting_fits']==15
    assert result['training_rows']==50094 and result['CSV']['rows']==209063 and replay['replay_exact']
    assert guard['CSV_exact'] and guard['model_files_unchanged'] and len(guard['checks'])==8
    assert sha(ROOT/result['CSV']['path'])==result['CSV']['sha256']==replay['CSV_sha256']
    for x in plan['frozen_code']:
        if x['path'].endswith('/modelo_final_g4_2023.py'):
            assert sha(ROOT/x['snapshot'])==x['sha256']
            assert sha(ROOT/x['path'])==guard['new_core_sha256']
        else:assert sha(ROOT/x['path'])==x['sha256']
    for x in plan['sources'].values():assert sha(ROOT/x['path'])==x['sha256']
    versions={p:md.version(p) for p in ['numpy','pandas','scipy','scikit-learn','joblib','pyarrow','threadpoolctl']}
    dump(RUN/'environment.json',{'python':sys.version,'platform':sys.platform,'packages':versions,'threads':2,'Kaggle_or_Linux_execution_verified':False})
    (RUN/'requirements.txt').write_text('\n'.join(k+'=='+v for k,v in versions.items())+'\n',encoding='utf-8')
    old_report=REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1/report.json'
    old=read(old_report)
    previous=[x for x in old['summary'] if x['model_id'] in ['W2-B20','W2-B00']]
    dump(RUN/'reused_2023_recipe_evidence.json',{'source':{'path':rel(old_report),'sha256':sha(old_report)},
        'summary':previous,'recipe':'Same standard GLM recipe; final all2023 model itself has no new OOF score',
        'adaptive_exploratory_evidence':True,'old_adverse_segment_and_concentration_results_preserved':True,
        '2024_confirmation_opened':False,'no_new_CV_or_bootstrap':True})
    calendar_checks=sum(x['C0']['direct_calendar_checks'] for x in validation['training'])
    calendar_error=max(x['C0']['max_abs_calendar_error'] for x in validation['training'])
    train_rows='\n'.join('| '+r['line']+' | '+str(r['rows'])+' | '+str(r['claims'])+' | '+str(next(q['rows'] for q in validation['quotes'] if q['line']==r['line']))+' |' for r in validation['training'])
    doc=f'''# Modelo propio G4 y CSV para Kaggle

El CSV propio está preparado: 209.063 predicciones de 2025, con dos columnas (`row_id`, `prediction`), IDs únicos y orden idéntico a la plantilla emergente. Se ajustaron tres GLM estándar con las 50.094 filas de 2023. El replay desde disco reprodujo exactamente todas las predicciones sin ajustar nada. 2024 permanece cerrado para políticas, precios, validación, scores y ledger; B00 y las alternativas se conservan.

Codex, {now()}. Preinscripción COD-S2-20261024-069; reparación focal G4-FINAL-GUARD1; resultado {FID}. La instrucción del participante de continuar automáticamente hasta finalizar permitió completar capital, C0 y modelos de 2023 y la inferencia de 2025. El resultado es un archivo local listo para cargar; no se ha enviado a Kaggle ni seleccionado una entrega final oficial.

| Ramo | Filas de ajuste2023 | Siniestros2023 | Predicciones2025 |
| --- | ---: | ---: | ---: |
{train_rows}

## Receta y ámbito

Se mantuvo la receta estándar de efectos principales ya especificada en B20: Tweedie1,5 con enlace log y alpha1, siete variables por ramo, mediana y escala numéricas y codificación categórica aprendidas solo del ajuste. No se añadió calibración de nivel/pendiente, tendencia, clima, credibilidad o mezcla con otras predicciones. No hubo otra búsqueda de hiperparámetros o entrenamiento repetido de los cinco folds.

El ámbito final comprende toda la cohorte elegible de 2023 y tiene identidad propia. Sus parámetros de capital, curvas C0, preprocesadores y GLM se aprendieron en ese ámbito, sin renombrar un objeto exterior como final. Para edificios y contenidos se conservó CAPS2-01 con sus umbrales anteriores de diez millones y un millón. La prima se emplea solo en la regla auditada de calidad de capital, fuera de los predictores. En el ajuste se corrigieron26capitales de edificios y30de contenidos; en2025se aplicó la regla congelada a104y135respectivamente. No se aprendieron referencias de las cotizaciones.

C0 conserva rho1 y masa de cola no observada0. Se ajustaron quince curvas de reporte (5autos,6edificios,4contenidos), quince frecuencias y sus marcas medias usando ocurrencias de2023 y seguimiento hasta el corte histórico2024-12-31. Eso no abre la cohorte de pólizas2024. La respuesta del GLM es T0/C0 y el peso sqrt(C0). Para cotizar2025 se multiplica la tasa anual por la exposición nominal reconciliada; no se aplica a una cotización futura la completitud observada de una póliza2023.

Las tres tablas oficiales de test2025, el maestro estático de direcciones y la plantilla de IDs solo se decodificaron después de terminar los tres modelos. Las fuentes de ajuste son copias ya estrictas2023, con SHA histórico, columnas explícitas y prueba de fechas/año en el footer. No se ejecutó un productor histórico que materialice todos los años. Las cotizaciones conservaron su exposición tras comprobar la regla de días inclusivos/365 redondeada a cuatro decimales.

## Comprobaciones y reparación

La nueva prueba focal sintética recorrió los tres ramos, con tres GLM y quince curvas de reporte aparte de los cómputos reales. Pasaron ocho controles de flujo y ámbito. En datos reales, T0 concilió con los siniestros heredados en centavos; los tres GLM convergieron y sus gradientes penalizados quedaron por debajo del criterio previo1e-4. La predicción manual exp(Xbeta+intercepto) y la identidad de pesos Tweedie cumplieron rtol1e-12/atol1e-9. C0 coincidió con integración diaria directa en {calendar_checks}casos, con error máximo {calendar_error:.3g}, bajo el límite1e-12.

La revisión posterior detectó una falta de guarda en la función de capital: admitía por sí sola un artefacto válido del otro ramo. La ejecución real había pasado el artefacto correcto a cada ramo. Se archivó la sonda adversa y se preinscribió la reparación antes de cambiar el código. Solo se añadieron rechazos de ramo/umbral y año admisible. No se alteraron parámetros, operaciones numéricas, modelos o CSV y no se reentrenó. Pasaron ocho controles focales, incluidos artefactos reseñalados de ámbito incorrecto; las características recalculadas desde los raw2025 y las209.063predicciones siguieron idénticas.

Se conservan el código anterior de ajuste y el código posterior con guardas. Los recibos originales certifican su versión original; la versión de consumo posterior tiene su propio replay. Hubo replay dentro del proceso y en otro proceso desde los tres modelos guardados, con todos los fit y los productores de capital/C0 bloqueados. Se verificaron columnas, orden, cobertura exacta de209.063IDs, valores positivos/finitos y roundtripCSVsin pérdida. No se rellenaron filas, recortaron precios o mezclaron mercados.

## Evidencia de rendimiento y límites

La receta B20 tenía D² OOF2023 de0,08938 frente a0,06858deB00 en la corrida histórica. Se reutiliza esa evidencia; no se ejecutó otra validación o bootstrap sobre las mismas etiquetas. Es exploratoria tras búsqueda adaptativa y conserva sus advertencias por segmentos y concentración. El modelo ajustado con todo2023 no tiene un nuevo score de validación. Ningún diagnóstico de ajuste se presenta como prueba de generalización.

La estimación de último sigue condicionada al tratamiento heredado de reservas y a cola no observada nula. No se ha identificado independientemente la masa fuera de soporte ni se ha efectuado una revisión actuarial profesional. Las carencias del ensayo de calibración de B20 siguen registradas. El CSV utiliza el GLM estándar sin esa calibración. No hay promoción formal, retirada de B00 o selección final manual. La exposición previa ajena de información2024 permanece declarada; no se consultó o usó en este trabajo.

## Archivos y reproducción

CSV: `{result['CSV']['path']}`. SHA256: `{result['CSV']['sha256']}`. Los modelos, capitales, C0, vistas de cotización, plan, entorno y recibos están en `{rel(RUN)}`. Índice: `{rel(INDEX)}`. El paquete privado de revisión incluye los objetos y las entradas derivadas necesarias para replay, código actual y fuentes archivadas anteriores. No incluye el foro, memoria compartida, credenciales o predicciones de otros modelos. Es local; no se ha publicado o enviado.

El comando de replay usa los modelos congelados y no entrena:

```powershell
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/herramientas/reproducir_csv_final_g4_sin_ajuste.py' --manifest 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/replay_manifest_guard1.json' --receipt 'C:/dev/Hakaton/Hackaton/Repositorio_IAA2026/privado/semana2/modelo_final_g4_2023/final_20261024_v1/replay_revision_nueva.json'
```

El recibo solicitado debe ser nuevo. El entrenamiento original y sus fuentes están archivados para revisión; no reejecutar su consumidor con las mismas fuentes para confirmar un cambio editorial. El paquete no se presenta como reproducción profesional independiente o ejecución verificada en Kaggle/Linux. La comprobación en proceso separado sigue siendo verificación propia de Codex.

Decisiones G4FNL-01 a G4FNL-07. Tres nuevos GLM reales y quince ajustes de reporte; tres GLM y quince ajustes de reporte sintéticos se cuentan aparte. Sin política2024, scores2024, ledger, actas o SEL01 abiertos; sin nuevos chats, delegación, cómputo remoto o automatizaciones. La ventana nocturna anterior sigue cerrada. La intervención humana es la autorización de alcance, no una aprobación técnica inventada del modelo. Referencias del proyecto: IAA Documentación§2 y Gobernanza§2.8.
'''
    # Espaciado editorial de cantidades sin tocar rutas/identificadores.
    for a,b in [('corrigieron26capitales','corrigieron 26 capitales'),('y30de','y 30 de'),('a104y135','a 104 y 135'),
        ('2025se','2025 se'),('15curvas','15 curvas'),('5autos','5 autos'),('6edificios','6 edificios'),('4contenidos','4 contenidos'),
        ('casos,',' casos,'),('las209.063predicciones','las 209.063 predicciones'),('de0,','de 0,'),('deB00','de B00'),('al criterio previo1e-4','al criterio previo 1e-4')]:doc=doc.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(doc)
    decisions=[('G4FNL-01','Completar el modelo propio automáticamente bajo autorización actual,con ajuste/C0solo2023 e inferencia2025,2024cerrado.'),
        ('G4FNL-02','Conservar receta estándarB20 sin búsqueda o calibraciones extras y declarar ámbito finaltodo2023distinto de folds.'),
        ('G4FNL-03','Aceptar controles numéricos/convergencia/calendario/manual yCSVde209063IDs exactos;no confundir ajuste con validación.'),
        ('G4FNL-04','Conservar y reparar falta de guarda de ramo con preinscripción;replayfocal confirma modelos/características/CSVidénticos,sinreajuste.'),
        ('G4FNL-05','Guardar paquete privado,requisitos,fuentes antiguas/nuevas yreplay autónomo exacto;no enviar/publicar o declarar Kaggle/Linux verificado.'),
        ('G4FNL-06','Contabilizar3GLMreales y15curvas/15frecuencias/15marcas;3GLM/15curvas sintéticos aparte,sin repetirOOF/bootstrap.'),
        ('G4FNL-07','B00/alternativas y adversos/G1/G2del ensayo de calibración conservados;no promoción,listafinal o aprobación profesional inventada.')]
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[{'id':k,'decision':v} for k,v in decisions]})
    # Paquete local con whitelist explícita; nunca contiene el foro o estado común.
    files=[DOC,PLAN,RUN/'environment.json',RUN/'requirements.txt',RUN/'ready_current.json',RUN/'decision_journal.json',
        RUN/'replay_manifest_guard1.json',RUN/'standalone_replay_guard1_receipt.json',RUN/'standalone_replay_receipt.json',
        RUN/'guard1_verification.json',RUN/'focused_capital_guard_gap.json',RUN/'forum_guard1_pre.md',RUN/'forum_guard1_receipt.json',
        RUN/'reused_2023_recipe_evidence.json',out/'result.json',out/'validation.json',out/'training_receipts.json',ROOT/result['CSV']['path']]
    files += [ROOT/x['path'] for x in plan['frozen_code']]
    files += [REPO/'herramientas/reproducir_csv_final_g4_sin_ajuste.py',REPO/'herramientas/verificar_guarda_final_g4_sin_ajuste.py']
    files += list((RUN/'preregistered_sources').glob('*.py'))+list((RUN/'guard1_sources').glob('*.py'))
    for folder in ['models','C0','quotes','capital']:
        files += [p for p in (out/folder).glob('*') if p.is_file() and not p.name.endswith('_population.parquet')]
    files=list(dict.fromkeys(files))
    dump(RUN/'packet_contents.json',{'id':IDENT,'scope':'Private local replay/review packet;not a Kaggle upload or public distribution.',
        'files':[{'path':rel(p),'sha256':sha(p)} for p in files]})
    packet=RUN/'paquete_modelo_propio_g4_2023.zip'
    with zipfile.ZipFile(packet,'x',compression=zipfile.ZIP_DEFLATED) as z:
        for p in files+[RUN/'packet_contents.json']:z.write(p,arcname=rel(p))
    with zipfile.ZipFile(packet) as z:
        assert z.testzip() is None
        for x in read(RUN/'packet_contents.json')['files']:assert hashlib.sha256(z.read(x['path'])).hexdigest()==x['sha256']
    ignored=subprocess.run(['git','check-ignore','--quiet',str(ROOT/result['CSV']['path'])],cwd=REPO)
    assert ignored.returncode==0
    index={'id':IDENT,'author':'Codex','utc':now(),'status':'own_standard_model_CSV_ready_2023_only_2024_closed',
        'path_base':'workspace_root','run':rel(RUN),'model_id':result['model_id'],'CSV':result['CSV'],
        'documentation':rel(DOC),'documentation_sha256':sha(DOC),'forum_prior':plan['forum_prior'],
        'forum_guard_repair':'COD-S2-20261024-G4-FINAL-GUARD1','forum_result':FID,
        'training_years':[2023],'prediction_years':[2025],'training_rows':50094,'real_price_GLM_fits':3,
        'real_reporting_fits':15,'real_frequency_constants':15,'real_weighted_mark_means':15,
        'synthetic_price_GLM_fits':3,'synthetic_reporting_fits':15,'synthetic_tests':8,'guard_focal_tests':8,
        'C0_calendar_reference_cases':calendar_checks,'C0_calendar_max_abs_error':calendar_error,
        'independent_process_replay_exact':True,'raw2025_features_identical_after_guard_repair':True,
        'CSV_roundtrip_exact':True,'standard_final_pipeline_real_verified':True,
        'G4_nested_calibration_flow_real_verified':False,'G4_original_nested_trial_gate_closed':False,
        'reference':'W2-B00','all_alternatives_preserved':True,'G1_G2_resolved':False,
        '2024_policy_rows_read':0,'2024_predictions':0,'2024_scores_consulted':False,
        'prior_external2024_subject_exposure_disclosed':True,'promotion':False,'manual_final_selection':False,
        'submission_sent':False,'Kaggle_score':None,'remote_training':False,'professional_independent_validation':False,
        'packet':{'path':rel(packet),'sha256':sha(packet),'files':len(files)+1,'private_local_only':True}}
    for key,p in [('plan',PLAN),('validation',out/'validation.json'),('guard_repair',RUN/'guard1_verification.json'),
        ('replay',RUN/'standalone_replay_guard1_receipt.json'),('replay_manifest',RUN/'replay_manifest_guard1.json'),
        ('previous_2023_recipe_evidence',RUN/'reused_2023_recipe_evidence.json'),('decisions',RUN/'decision_journal.json')]:index[key]={'path':rel(p),'sha256':sha(p)}
    body=RUN/'forum_070_result.md'
    body.write_text(f'''Codex,entrega local del modelo propio preinscrito069 y reparaciónG4-FINAL-GUARD1.Informe:{rel(DOC)}.Índice:{rel(INDEX)}.CSV:{result['CSV']['path']} (SHA256 {result['CSV']['sha256']}).Paquete privado:{rel(packet)}.

TresGLMTweedie1,5/alpha1 de efectos principales ajustados con50094filasde2023;sin climatología,tendencia,credibilidad,calibración extra o mezclas de otraspredicciones.Ámbito finaltodo2023propio,capital/C0/preprocesadores aprendidos aquí;15curvas de reporte,15frecuencias y15marcas ponderadas.T0yregla de exposición conservados.Precio2025=exposición nominal*tasa anualcondicional,con límitesrho1/cola0declarados.

CSVpropio209063filas:90521autos,52295edificios,66247contenidos.IDs únicos,enordenexacto deplantillaemergente;preciospositivosfinitos yroundtripCSVexacto.Sinrelleno,clippingomercadosmezclados.Test/direcciones/plantilla solo decodificados tras terminar los3ajustes;2024políticas/ledger/actas/SEL01 no abiertos.

Verificación:focal sintética8controles (3GLM/15curvassintéticos aparte),gradientes reales<=1e-4,predicciónmanual eidentidadpesos dentro delcriterio,120comprobacionesC0contra calendario con error máximo2,74e-14<1e-12.Estadoaprendido sincambios alpredecir,replay de modelosdesde disco yproceso separado exactos para209063filascon todoajuste/C0bloqueado.

La sonda posterior detectó falta de rechazo de capitaldelotro ramo enlafunciónaislada.La ejecuciónreal usó artefactos correctos.Reparaciónpreinscrita soloañadióguardasderamo/umbral/año.Se preservanfuenteysonda anteriores.Pasaron8adversos/replaysfocales;featuresraw2025,modelosypreciossiguieronidénticos,sinreajustar.No se afirmaconsumoactualcertificado por recibodecódigoanterior;haymanifiestoreplayguardado nuevo.

Rendimiento:recetahistóricaB20OOF2023D²0,08938frenteB00 0,06858,evidenciaadaptativaexploratoriaconadvertencias anteriores preservadas.No nuevosOOF/bootstrap ovalidación2024;ajustefinalnoesvalidación.No sepromueveB20,G4oelnuevocandidato porunscore,seconservaB00yrestodelcatálogo.Lascarencias delensayodependiente/calibraciónoriginalsiguenabiertas;elCSVusaGLMestándarsincalibración.

G4FNL-01a07,autorCodex.Cierre hastaCSVlocalverificado,sin envío a cuentaKaggle o selecciónfinal manual.PaqueteCRC/SHAcomprobados,requisitos/fuentes/recibos propios,sin foro/memoria/credenciales oCSVdeotrosmodelos.Contabilizar3GLMrealesy15reportes,15frecuencias,15marcas;sintéticosseparados.Sinremoto,nuevoschats,delegaciónoautomatizaciones.Ventananocturnacerrada.VerificaciónpropiaenWindows,noKaggle/Linuxorevisiónprofesionalindependiente.Noaprobaciónhumanadelmodeloinventada.
''',encoding='utf-8')
    posted=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',FID,
        '--asunto','G4:modelo propio yCSV209063listos,2023solo,replayexacto y2024cerrado','--cuerpo',str(body)],capture_output=True,text=True)
    assert posted.returncode==0,posted.stderr
    dump(RUN/'forum_result_receipt.json',json.loads(posted.stdout));dump(INDEX,index)
    changes=[]
    preserve_paths=[REPO/'registro/semana2_continuidad_nocturna.json',old_report,
        REPO/'privado/semana2/desarrollo2023/ridge20_20261024_v1/manifest.json',ROOT/result['CSV']['path']]
    preserved={rel(p):sha(p) for p in preserve_paths}
    def change(path,fn,allowed=None):
        before=path.read_bytes();raw=before.decode('utf-8-sig');updated=fn(raw)
        if allowed is not None:
            old,new=json.loads(raw),json.loads(updated)
            assert {k:v for k,v in old.items() if k not in allowed}=={k:v for k,v in new.items() if k not in allowed}
        after=updated.encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,payload in [('before',before),('after',after)]:
            p=RUN/'registration_cuts'/phase/path.relative_to(ROOT);p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(payload)
        tmp=path.with_name(path.name+'.G4delivery.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert path.read_bytes()==before,'Concurrent edit:'+rel(path);os.replace(tmp,path)
        changes.append({'path':rel(path),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(path)})
    def update(raw,values):
        for k,v in values.items():raw=top(raw,k,v)
        return raw
    def counter_update(raw):
        d=json.loads(raw);inc=d['increments'];assert not any(x.get('id')==IDENT for x in inc)
        inc.append({'id':IDENT,'utc':now(),'scope':'Final all2023 standard model,not repeated CV',
            'price_base_fits':3,'closed_form_pricing_constants':0,'reporting_peril_fits':15,'frequency_constants':15,
            'positive_weighted_mark_means':15,'capital_reference_objects':2,'normalized_mixtures':3,
            'synthetic_GLM_fits_separate':3,'synthetic_reporting_fits_separate':15,'index':rel(INDEX)})
        vals={'as_of_utc':now(),'cumulative_price_base_fits':d['cumulative_price_base_fits']+3,'increments':inc,
            'supplementary_reporting_peril_fits_since_counter_start':d['supplementary_reporting_peril_fits_since_counter_start']+15,
            'mixture_frequency_constants_since_counter_start_separate':d['mixture_frequency_constants_since_counter_start_separate']+15,
            'mixture_positive_severity_means_since_counter_start_separate':d['mixture_positive_severity_means_since_counter_start_separate']+15,
            'latest_final_deployment_index':rel(INDEX),
            'reporting_counter_notice':str(d.get('reporting_counter_notice',''))+' Added15 final all2023reporting-peril fits inG4deployment;synthetic15excluded.',
            'final_deployment_counter_notice':'3full2023GLM,15reporting curves/frequencies/weighted means;pricing constants and slopes unchanged.Synthetic3GLM/15reporting fits separate.'}
        return update(raw,vals)
    change(COUNTER,counter_update,{'as_of_utc','cumulative_price_base_fits','increments','supplementary_reporting_peril_fits_since_counter_start',
        'mixture_frequency_constants_since_counter_start_separate','mixture_positive_severity_means_since_counter_start_separate',
        'latest_final_deployment_index','reporting_counter_notice','final_deployment_counter_notice'})
    def priority_update(raw):
        d=json.loads(raw);g=d['current_gate_statuses'];g['G4']=G4STATUS
        blocks=[('G4:standard final pipeline verified;nested calibration trial remains unrun' if str(x).startswith('G4:') else x) for x in d.get('current_blockers',[])]
        return update(raw,{'current_gate_statuses':g,'current_blockers':blocks,'G4_final_standard_index':rel(INDEX),'G4_final_standard_utc':now()})
    change(PRIORITY,priority_update,{'current_gate_statuses','current_blockers','G4_final_standard_index','G4_final_standard_utc'})
    def source_update(raw):
        d=json.loads(raw);g=d['current_B20_gate_statuses'];g['G4']=G4STATUS
        return update(raw,{'current_B20_gate_statuses':g,'G4_final_standard_index':rel(INDEX),'G4_final_standard_pipeline_verified':True,
            'G4_nested_calibration_flow_real_verified':False})
    change(SOURCE,source_update,{'current_B20_gate_statuses','G4_final_standard_index','G4_final_standard_pipeline_verified','G4_nested_calibration_flow_real_verified'})
    link={'index':rel(INDEX),'utc':now(),'CSV':result['CSV'],'status':'own_CSV_ready','training_years':[2023],'prediction_years':[2025],
        'models_fitted':3,'reporting_fits':15,'2024_closed':True,'promotion':False,'submission_sent':False}
    change(PREPARATION,lambda raw:top(raw,'subsequent_final_deployment',link),{'subsequent_final_deployment'})
    change(DEVELOPMENT,lambda raw:top(raw,'G4_final_standard_deployment',link),{'G4_final_standard_deployment'})
    change(ROOT/'Preparación/ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,index),{STATEKEY})
    section=f'''\n\n## G4: modelo propio y CSV listos con entrenamiento2023

Codex,UTC {now()},preinscripción069,reparaciónG4-FINAL-GUARD1,resultado070;G4FNL-01a07.Informe {rel(DOC)},índice {rel(INDEX)},CSV {result['CSV']['path']} SHA256 {result['CSV']['sha256']}.Instrucción humana de continuar automáticamente hasta finalizar se aplicó a capital/C0/GLMfinales2023 e inferencia2025;no cambió cierre2024 o permiso de publicación/envío.Se terminóCSVlocalpropio,no se copió mezcla ni se hizo envío.

TresGLMestándarTweedie1,5/alpha1,50094filas2023,sieteefectosporramo,sin búsqueda ocalibración.Nuevoámbitofinaltodo2023distintodefolds,2capitales,3objetosC0con15curvas/15frecuencias/15marcas.T0/exposiciónpreservados,rho1/cola0condicional.Test2025/maestro/plantilla solo despuésdeajustar3GLM.CSV209063IDsúnicos,enorden,preciospositivosfinitos,roundtripexacto;90521motor/52295edificios/66247contenidos.Replaydisco/procesoseparado exacto209063confitsbloqueados,estadoaprendidosincambios.

Ocho pruebasfocalessintéticas(3GLM/15curvas aparte),120integracionesC0contra calendario(error2,74e-14),convergencia/gradiente<=1e-4,predicciónmanual eidentidadpesos.Detectadaguardaderamocapitalfaltanteensondaposteriorsintética;ejecuciónrealusóramocorrecto.Reparaciónpreinscritaguardasderamo/umbral/año,8controlesfocales,features/modelos/CSVidénticos,sinreentrenar.Fuentesanterioresynuevaspreservadas,manifiestoreplayguardadoactual.

EvidenciaOOFrecetahistóricaB20en2023D²0,08938vsB000,06858reutilizada,sin nuevaCV/bootstrap;exploratoria/adaptativa,adversosdeconcentración/segmentosconservados.No nuevavalidación2024,últimoindependiente o promoción.G1/G2yensayodecalibraciónanidadasiguenpendientes,CSVutilizaGLMsincalibración.B00/alternativas/catalogoOOFconservados.Contadorpropioincrementado3GLMreales,15reportes,15frecuenciasy15marcas;sintéticosseparados.Constantesdeprecio/calibradorespreviosintactos.

Paqueteprivadolocal {rel(packet)} CRC/SHAverificados,requisitos/código/modelos/entradasderivadas/recibos,sinforo/memoria/credencialesoprediccionesajenas.2024políticas/precios/scores/ledger/actas/SEL01cerrados,exposiciónpreviaajenaconservadacomodeclaración.Sinselecciónfinalmanual,envío,publicación,remoto,otroschats,delegaciónoautomatizaciones;ventananocturnacerrada.VerificaciónpropiadeCodexenWindows,novalidaciónprofesionalindependienteoaprobaciónhumanadelmodelo.\n'''
    for n in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/'Preparación'/n,lambda raw:raw+section)
    routes={'week_2_G4_own_model_CSV_index':rel(INDEX),'week_2_G4_own_model_CSV_report':rel(DOC),
        'week_2_G4_own_CSV':result['CSV']['path'],'week_2_G4_own_model_packet':rel(packet)}
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:update(raw,routes),set(routes))
    count=read(COUNTER)
    integrity={'id':IDENT,'utc':now(),'CSV_and_original_metadata_preserved_during_registration':all(sha(ROOT/p)==h for p,h in preserved.items()),
        'preserved_hashes':preserved,'original_frozen_training_core_archived':True,'guarded_runtime_core_matches_receipt':sha(REPO/'src/semana2/modelo_final_g4_2023.py')==guard['new_core_sha256'],
        'packet_readback_hashes_verified':True,'unrelated_top_level_shared_keys_preserved':True,'CSV_ignored_by_git':True,
        'counter_after':{k:count[k] for k in ['cumulative_price_base_fits','cumulative_closed_form_constants','supplementary_reporting_peril_fits_since_counter_start',
            'mixture_frequency_constants_since_counter_start_separate','mixture_positive_severity_means_since_counter_start_separate']},
        'new_fits_during_registration':0,'submission_sent':False}
    assert integrity['CSV_and_original_metadata_preserved_during_registration'] and integrity['guarded_runtime_core_matches_receipt']
    dump(RUN/'closure_integrity_receipt.json',integrity);dump(RUN/'registration.json',{'changes':changes,'price_base_fit_increment':3,'reporting_fit_increment':15,
        'old_OOF_catalog_mutations':0,'night_index_mutations':0,'old_model_mutations':0})
    allfiles=[p for p in RUN.rglob('*') if p.is_file()]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/registrar_plan_modelo_final_g4_2023.py',
        REPO/'herramientas/registrar_resultado_entradas_g4_2023.py']
    dump(RUN/'manifest.json',{'id':IDENT,'author':'Codex','utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in allfiles]})
    print(json.dumps({'id':IDENT,'forum_result':FID,'CSV':result['CSV'],'packet':rel(packet),'packet_files':len(files)+1,
        'document':rel(DOC),'replay_exact':True,'real_GLM_fits':3,'cumulative_own_price_fits':count['cumulative_price_base_fits'],
        '2024_closed':True,'submission_sent':False,'integrity':True},ensure_ascii=True))

if __name__=='__main__':main()
