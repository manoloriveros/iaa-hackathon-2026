"""Cierre de PRE00: solo evidencia e índices de revisión, sin cambios del catálogo."""
from pathlib import Path
from datetime import datetime,timezone
import json
import re
import shutil
import sys

ROOT=Path(__file__).resolve().parents[3]
BASE=Path(__file__).parent
sys.path.insert(0,str(ROOT/'Hackaton/Semana 1/Limpieza'))
import clean_data as c


def number(v,d=0):
    return f'{float(v):,.{d}f}'.replace(',','_').replace('.',',').replace('_','.')


def main(out):
    assert '--figure-inspected' in sys.argv,'Inspect actual figure before closure.'
    assert not (out/'manifest.json').exists(),'Already closed; do not rewrite.'
    s=json.loads((out/'summary.json').read_text('utf-8'));v=json.loads((out/'verification.json').read_text('utf-8'))
    ui=json.loads((out/'interface_verification.json').read_text('utf-8'))
    assert v['failed']==ui['failed']==0 and ui['all_413_claims_exercised']
    protected=json.loads((out/'protected_hashes_before.json').read_text('utf-8'))
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    now=datetime.now(timezone.utc).isoformat();rel=out.relative_to(ROOT).as_posix()
    m={'created_utc':now,'type':'immutable_PRE00_review_no_data_changes','files':[
        {'path':p.relative_to(out).as_posix(),'sha256':c.digest(p),'bytes':p.stat().st_size}
        for p in sorted(out.rglob('*')) if p.is_file()]}
    c.dump(out/'manifest.json',m)
    paths={name:ROOT/'Preparación'/name for name in ['ESTADO_PROYECTO.json','MEMORIA_PROYECTO.md','DECISIONES.md']}
    paths['RUTAS_PROYECTO.json']=ROOT/'RUTAS_PROYECTO.json'
    state=json.loads(paths['ESTADO_PROYECTO.json'].read_text('utf-8'));memory=paths['MEMORIA_PROYECTO.md'].read_text('utf-8')
    decisions=paths['DECISIONES.md'].read_text('utf-8');routes=json.loads(paths['RUTAS_PROYECTO.json'].read_text('utf-8'))
    decision='D'+str(max(map(int,re.findall(r'\bD(\d+)\b',decisions)))+1)
    close=BASE/'closures'/datetime.now(timezone.utc).strftime('closure_%Y%m%dT%H%M%SZ');close.mkdir(parents=True,exist_ok=False)
    for name,p in paths.items():shutil.copy2(p,close/('before_'+name))
    review={'decision_id':decision,'rule':'PRE00','status':'verified_review_only_source_coverage_pending','run':'../'+rel,
        'report':'../'+rel+'/informe.html','proposal':'../'+rel+'/proposal.json','verification':'../'+rel+'/verification.json',
        'frozen_cohort':'../'+rel+'/tables/frozen_prehistory_cohort.parquet','financial_reconciliation':'../'+rel+'/financial_reconciliation.json',
        'index':'../Hackaton/Semana 1/Revision_prehistoria/current_run.json','records':413,'policies':413,'customers':413,
        'legacy_at_2021_boundary':244,'before_recorded_new_business':169,'accepted_records':409,'open_records':15,'repudiated_records':4,
        'observed_net_accepted_CU':s['prehistory_financial']['net_accepted_CU'],'before_days_min':s['before_days_min'],'before_days_max':s['before_days_max'],
        'reported_before_first_start':s['reported_before_first_start'],'reported_equal_first_start':s['reported_equal_first_start'],
        'reported_after_first_start':s['reported_after_first_start'],'minimum_loss_date_concentration':s['loss_on_minimum_date'],
        'policy_history_rows':s['cohort_policy_history_rows'],'all_claim_history_rows':s['cohort_all_claim_history_rows'],
        'case_histories':12,'control_policies':1,'previous_DUP01_aliases':s['previous_duplicate_aliases'],
        'technical_checks':v['passed'],'interface_logic_checks':ui['passed'],'all_413_claims_interaction_checked':True,
        'figure_visually_inspected':True,'browser_rendering_verified':False,'independent_validation':False,
        'data_modified':False,'claims_reassigned':False,'active_dataset_changed':False,'audit_mark_applied':False,
        'operational_T0_materialized':False,'predictors_added':False,'models_trained':False,'source_coverage_confirmed':False,
        'application_authorized':False,'calendar_dates_pending':True,'pending_capitals_unchanged':1454,
        'closure':'../'+close.relative_to(ROOT).as_posix()}
    state['prehistory_claim_review']=review;state['memory_as_of']=now
    routes['week_1_prehistory_claim_review_index']='Hackaton/Semana 1/Revision_prehistoria/current_run.json'
    text=f'''\n\n### {decision}, revisión de los 413 siniestros anteriores al primer periodo observado, 16 de octubre de 2026, America/Bogota\n\nEl participante pidió comparar historiales, ejemplos y tratamiento sin modificar datos. La corrida ../{rel} reconstruye asignaciones desde el catálogo REN00 y claims DUP01, reproduciendo exactamente los 413 IDs before_first_observed_period. Son 296 motor, 67 edificios y 50 contenidos, un expediente por póliza y cliente (413 de cada uno), con claves existentes. Se archivan {number(s['cohort_policy_history_rows'])} periodos completos de esas pólizas y {number(s['cohort_all_claim_history_rows'])} expedientes incluyendo los otros siniestros asignados. Hay doce ejemplos y un control; cada uno de los 413 expedientes abre su historia completa en el explorador.\n\nSe distinguen 244 pólizas cuya primera fila es renovación el 01-01-2021, new_business=false, renewal_count>0 y cliente anterior a 2021: compatibles con historia truncada al comienzo de la ventana, sin probar las condiciones del contrato anterior. Otros 169 tienen negocio nuevo y contador cero después de la pérdida; requieren aclarar contrato, vínculo y fecha. No inferir cobertura o falta de ella solo desde esas categorías, ni usar otra póliza/ramo del cliente como sustituto. La distancia al primer inicio observado va de 4 a 499 días. Hay {number(s['loss_on_minimum_date'])} ocurrencias en el mínimo 01-12-2020, compatible con un límite del generador pero sin código o fecha verdadera anterior; no corregir por esa concentración.\n\nNingún reporte es estrictamente anterior al primer inicio: {s['reported_equal_first_start']} son del mismo día y {s['reported_after_first_start']} posteriores. Una ocurrencia previa no era necesariamente información disponible al cotizar. Se diagnostica report_date < period_start en los periodos posteriores sin crear predictores; misma fecha no garantiza conocimiento al inicio del día. Estado, pagos e incurrido están valorados al 31-12-2024, sin snapshots financieros históricos. No filtrar antecedentes de backtests por estado final retrospectivo. prior_claims_5y es declaración de cinco años antes del ingreso, no ventana móvil interna; no sumarlo o sobrescribirlo con estos registros sin resolver ventanas y solapamiento.\n\nLos 413 incluyen 409 aceptados, 15 abiertos y cuatro repudiated. El neto aceptado observado es {number(s['prehistory_financial']['net_accepted_CU'],2)} CU; pagado, reserva y recuperaciones concilian con Decimal. Asignados más prehistoria igualan todos los componentes del total claims. Mantener el bloque previo fuera del objetivo de periodos publicados preserva el total económico en conciliación; no equivale a borrar sus registros o coste. No hay exposición previa publicada para estimar una prima pura de ese bloque. Los escenarios de forzar el primer periodo solo ilustran el traslado indebido de coste sin cobertura/exposición acreditadas, sin aplicarlo. {s['report_date_would_match_a_row']} reportes coinciden con algún periodo disponible y {s['report_after_first_period_end']} son posteriores al fin de la primera fila; report_date no sustituye loss_date para el objetivo.\n\nUn expediente tiene un alias DUP01 excluido; se conserva solo el representante y no se reinserta la copia. La diferencia histórica 414→413 sigue atribuida a DUP01. El caso M10432603 distingue ocurrencia 23-12-2020, inicio 21-05-2021 y reporte 21-05-2022. B99888204 tiene pérdida 01-12-2020 y reporte 08-01-2022, siendo renovación en enero 2021. El control B01979656 ocurre 31-12-2023 y se reporta 04-01-2024 con cobertura observada 2023; sigue asignado a 2023. Los otros ejemplos muestran pérdida grande, alta posterior, abierto, repudiated, distancias extrema/corta y declaración previa cero.\n\nPRE00 propone conservar los registros sin alterar fechas, claves, importes o estado; mantener clasificación before_first_observed_period y conciliación separada fuera de T0 de los intervalos actuales. No crear exposición/póliza 2020 ni ampliar la primera fila, trasladar pérdida por reporte o cambiarla de ramo. Una eventual marca audit_pre00 y la recuperación de periodos anteriores requieren autorización posterior; no se aplican. Un bloque futuro de antecedentes reportados solo podría evaluarse con atribución y disponibilidad acreditadas y sin estados/importes futuros. Preguntas a la fuente preparadas sobre run-off/migración, significado de new_business, fechas mínimas, contratos previos y revisiones de claves. No se contactó a terceros.\n\nPasaron {v['passed']} controles propios de fuentes, cohorte, todos los valores originales de historias, asignación independiente, contextos de cliente, disponibilidad y conciliación Decimal; {ui['passed']} controles de lógica del explorador ejercitan doce ejemplos y los 413 expedientes. Figura inspeccionada; sin renderizado real de navegador o validación independiente acreditados. Manifiesto, código, contexto y solicitud conservados. Ningún cambio de datos, asignación, catálogo REN00, guard de predictores o protocolo 1.4, ninguna activación PRE00, T0 operativo, entrenamiento, proveedor externo, envío o delegación. Los 1.454 capitales y las fechas siguen pendientes.\n\nIAA Documentación §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §3.2, §3.3 y §§3.5–3.6: trazabilidad, límites, sesgo y responsabilidad. Codex investigó y propuso; no hay confirmación de cobertura del origen o autorización de cambio. Consultar prehistory_claim_review e índice Revision_prehistoria/current_run.json.\n'''
    c.dump(paths['ESTADO_PROYECTO.json'],state);c.dump(paths['RUTAS_PROYECTO.json'],routes)
    paths['DECISIONES.md'].write_text(decisions.rstrip()+text,encoding='utf-8')
    paths['MEMORIA_PROYECTO.md'].write_text(memory.rstrip()+f'\n\nPrehistoria {decision}: revisión de 413 expedientes (296/67/50), un cliente/póliza por expediente. 244 renovaciones al inicio 2021 son compatibles con historia truncada; 169 pérdidas anteriores al negocio nuevo requieren aclaración. No hay reportes estrictamente anteriores al primer inicio. Los 409 aceptados suman {number(s["prehistory_financial"]["net_accepted_CU"],2)} CU, conservados en conciliación separada fuera del objetivo de los periodos suministrados. PRE00 es propuesta sin activar: no mover fechas, asignar al primer periodo, inventar exposición ni borrar. [Informe con doce casos y explorador completo](../{rel}/informe.html); {v["passed"]} controles de datos y {ui["passed"]} de interfaz. Catálogo REN00 y protocolo 1.4 permanecen iguales; fechas/capitales pendientes. Ver prehistory_claim_review y {decision}.\n',encoding='utf-8')
    index=BASE/'current_run.json'
    c.dump(index,{'workspace_relative_run':rel,'report_workspace_relative':rel+'/informe.html','decision_id':decision,
        'status':review['status'],'prehistory_records':413,'data_modified':False,'active_dataset_changed':False})
    assert all(c.digest(ROOT/p)==sha for p,sha in protected.items())
    assert all(c.digest(out/e['path'])==e['sha256'] for e in m['files'])
    c.dump(close/'closure.json',{'created_utc':now,'decision_id':decision,'review':review,'manifest_sha256':c.digest(out/'manifest.json'),
        'source_and_active_hashes_preserved':True,'post_documents':{p.relative_to(ROOT).as_posix():c.digest(p) for p in list(paths.values())+[index]}})
    print(json.dumps({'decision':decision,'report':str(out/'informe.html'),'closure':str(close)},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
