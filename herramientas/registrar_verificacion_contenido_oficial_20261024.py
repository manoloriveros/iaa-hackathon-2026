"""Publica el resultado binario existente; no interpreta los Parquet descargados."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,re,subprocess,sys
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
RUN=REPO/'privado/semana2/integridad_oficial/contenido_20261024_v1'
DOC=REPO/'docs/semana2/VERIFICACION_CONTENIDO_KAGGLE_20261024.md'
INDEX=REPO/'registro/semana2_contenido_oficial_actual.json'
SOURCES=REPO/'registro/semana2_b20_fuentes2023_actual.json'
IDENT='S2-CONTENIDO-OFICIAL-20261024-v1';STATEKEY='week_2_official_parquet_binary_content20261024_v1'
now=lambda:datetime.now(timezone.utc).isoformat()
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'))
rel=lambda p:p.relative_to(ROOT).as_posix()

def sha(p):
    with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()

def dump(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf-8') as f:json.dump(obj,f,ensure_ascii=False,indent=2);f.write('\n')

def top(raw,key,value):
    val=json.dumps(value,ensure_ascii=False,indent=2).replace('\n','\n  ')
    if key not in json.loads(raw):return raw[:raw.rfind('}')].rstrip()+',\n  '+json.dumps(key)+': '+val+'\n}\n'
    m=re.search(r'(?m)^  '+re.escape(json.dumps(key))+r':\s*',raw);assert m,key
    _,end=json.JSONDecoder().raw_decode(raw[m.end():]);return raw[:m.end()]+val+raw[m.end()+end:]

def main():
    r=read(RUN/'report.json');assert r['files_checked']==r['files_expected']==24 and r['all_content_equal_to_historical_originals'] and not r['errors']
    before_sources=read(SOURCES);frozen_plan=ROOT/before_sources['plan'];plan_hash=sha(frozen_plan)
    with (RUN/'source_plan_index_before.json').open('xb') as f:f.write(SOURCES.read_bytes())
    inventory=read(RUN/'inventory_before.json');after=read(RUN/'inventory_after.json');assert inventory['files']==after['files']
    assert all(x['byte_for_byte_equal'] and x['sha256_equal'] and x['official_md5_matches_received'] and x['local_matches_historical_manifest'] for x in r['results'])
    ndev=sum(x['name'].startswith('developed/') for x in r['results']);nem=sum(x['name'].startswith('emerging/') for x in r['results'])
    body=f'''# Contenido de los Parquet oficiales: comparación binaria

Los24Parquet activos comprobados son idénticos byte por byte a los originales locales históricos. Coinciden sus SHA-256 y las huellas oficialesMD5 de los objetos recibidos. No se detectó un cambio de contenido en estas copias; el cambio observado de fecha no aporta datos nuevos de2023.

Codex, publicación UTC {now()}. La descarga/comparación terminó a {r['utc']}. Respuesta a la instrucción directa «verifica el contenido», posterior a la revisión de metadatos. Este resultado sustituye la incertidumbre de identidad binaria de F01 para las copias comprobadas; no altera la fecha o el alcance histórico de la revisión anterior.

| Grupo de archivos | Comprobados | Comparación directa de bytes | SHA-256 local/descargado | SHA-256 local/manifiesto histórico |
| --- | ---: | --- | --- | --- |
| developed | {ndev} | Todos iguales | Todos iguales | Todos iguales |
| emerging | {nem} | Todos iguales | Todos iguales | Todos iguales |
| Total |24| Todos iguales | Todos iguales | Todos iguales |

## Cómo se comprobó

Se pidió una URL oficial por archivo a KaggleMCP y se descargaron copias en una carpeta privada aislada. Durante la descarga, cada bloque se comparó directamente con el bloque local del mismo tamaño; también se calcularon SHA-256 yMD5 de ambos flujos completos. Los24recibos registran igualdad directa, tamaño, huellas completas y ausencia de un primer byte distinto. No se confía solo en nombres,tamaños o fechas.

Las huellasMD5 publicadas por GoogleCloudStorage en las cabeceras coinciden con los bytes recibidos y con los locales. Cada recibo conserva la generación del objeto y cabeceras de integridad, sin guardar URLs firmadas o credenciales. Los SHA-256 locales coinciden además con los manifiestos anteriores de la descarga original: once archivos desarrollados y trece emergentes. El inventario de nombres/tamaños/fechas fue estable antes y después de la comprobación.

El primer intento completó cinco archivos y después sufrió fallos de conexión/transferencia. Se conservaron esos cinco resultados, los errores y las descargas parciales. Solo los diecinueve pendientes se recuperaron con peticiones de rangos pequeños y comprobación de generación del objeto. La recuperación no repitió los cinco archivos ya verificados. El resultado final completo no se presenta como un primer intento sin fallos; los recibos de ambos pasos están archivados.

Los originales se abrieron únicamente como bytes de lectura y no se sobrescribieron. Las copias nuevas están bajo privado/semana2/integridad_oficial, separadas de los datos activos y de las entradas del modelo. El programa no importa un lector Parquet, dataframe o modelo; no decodificó valores, años, IDs, etiquetas o predicciones. Identificó únicamente la firma del contenedor para no confundir un errorHTML con el archivo solicitado.

La autorización de esta actuación es comprobar la integridad opaca de los24contenedores, incluidos multiaño y test. No se abrió una validación de2024 ni se interpretaron sus filas o las del test. No hubo entrenamiento, nuevas inferencias/scores,C0,remuestreo o diagnóstico predictivo. La exposición previa a métricas de un asunto ajeno sigue declarada; esta operación no añade una lectura semántica de esos resultados ni permite afirmar ceguera completa.

## Consecuencia para B20 y el plan de fuentes

F01 queda resuelta en cuanto a identidad de contenido: estos archivos oficiales reproducen los originales conservados. No hay por esta vía una cohorte2023 adicional, un cambio de siniestros o una corrección material que permita modificar el soporte. No se atribuye una causa interna a la republicación o al cambio de metadatos.

No corresponde repetir los diagnósticos, bandas, entrenamiento o bootstrap por estas fechas. El plan F02 de definición/disponibilidad temporal de campos contractuales permanece como trabajo documental distinto; esta verificación no lo ejecuta. G1 continúa plausible/no establecido y G2retenido sigue fallido; la igualdad de archivos no acredita calidad actuarial, reservas, último, calibración o capacidad predictiva.

B00 y todas las alternativas, T0/C0, folds, datos activos y recetas permanecen.2024 sigue cerrado para modelado/validación, sin apertura de ledger,actas oSEL01. La ventana y automatización nocturnas continúan cerradas; no se crea programación, remoto, mensajes externos o delegación. Verificación propia de integridad, sin revisión profesional independiente o aprobación humana.

## Recibos

La [tabla completa](../../privado/semana2/integridad_oficial/contenido_20261024_v1/report.json) contiene un registro por archivo con SHA-256local/descargado/histórico, MD5oficial, tamaños, igualdad directa y generación del objeto. Los recibos individuales y las copias opacas están en la misma corrida privada; no se enlazan los Parquet para abrirlos como tablas. Los inventarios antes/después y los manifiestos de referencia quedan conservados.

[Índice de verificación](../../registro/{INDEX.name}) y [plan de fuentes anterior](FUENTES_2023_Y_PLAN_REVISION_B20.md). La receta congelada de ese plan no se reescribe; su índice actual recibe el enlace a este resultado con evidencia.
'''
    for a,b in {'Los24':'Los 24','los24':'los 24','MD5de':'MD5 de','MD5publicadas':'MD5 publicadas','huellasMD5':'huellas MD5','oficialesMD5':'oficiales MD5','SHA-256local':'SHA-256 local','MD5oficial':'MD5 oficial','yMD5':'y MD5','errorHTML':'error HTML','GoogleCloudStorage':'Google Cloud Storage','cohorte2023':'cohorte 2023','de2023':'de 2023','de2024':'de 2024','G2retenido':'G2 retenido','|24|':'| 24 |','oSEL01':'o SEL01'}.items():body=body.replace(a,b)
    with DOC.open('x',encoding='utf-8') as f:f.write(body)
    dump(RUN/'decision_journal.json',{'id':IDENT,'author':'Codex','utc':now(),'decisions':[
      {'id':'BIN-01','decision':'Cerrar identidad binaria F01 para24archivos: comparación directa de bytes,SHA256 yMD5oficial coincidentes; referencias históricas preservadas.'},
      {'id':'BIN-02','decision':'El cambio de fecha no acredita nuevos datos2023; no repetir diagnósticos o entrenamiento sobre copias idénticas.'},
      {'id':'BIN-03','decision':'No interpretar filas2024/test: solo contenedores opacos en cuarentena; no abrir confirmación,ledger,actas oSEL01.'},
      {'id':'BIN-04','decision':'Conservar B00/alternativas,T0/C0/folds y G1/G2abiertas. La igualdad no certifica calidad actuarial.'},
      {'id':'BIN-05','decision':'Anotar resultado en índice actual de fuentes, sin reescribir plan congelado o reactivar automatización.'}]})
    fid='COD-S2-20261024-052';fp=RUN/'forum_052.md'
    fp.write_text(f'''Codex, respuesta directa a «verifica el contenido» y al plan051. Resultado completo:24/24Parquet activos,11developed y13emerging,idénticos byte por byte a originales locales. SHA-256descargado/local/histórico coincide en todos;MD5oficial de GoogleCloudStorage también coincide con bytes recibidos/locales. Inventario estable antes/después,cero errores o archivos diferentes. Informe:{rel(DOC)}; recibos por archivo:{rel(RUN/'report.json')}.

Se descargaron copias opacas a privado/semana2/integridad_oficial,fuera de datos activos/modelado. No lectorParquet/dataframe/modelos: comparación de bloques y huellas,no valores o filas2024/test. Se preservan originales,manifiestos,recetas,T0/C0 yfolds. No URLsfirmadas/credenciales guardadas,nuevos scores,C0,bootstrap o entrenamiento. Los objetos multiaño/test solo se trataron como bytes para esta integridad,no se abre validación2024,ledger,actas oSEL01.

El primer intento tuvo fallos de red después de cinco archivos completos; errores y parciales conservados. Se recuperaron solo los19pendientes por rangos pequeños, sin repetir los cinco verificados. El éxito final no se atribuye al intento inicial.

BIN-01 aBIN-05resuelven identidad de contenidoF01para las copias comprobadas. El cambio de fecha no aporta una cohorte2023 adicional o corrección que cambie soporte;no repetir diagnósticos por esos metadatos. Plan congelado original intacto;índice actual enlazado a este resultado. G1plausible yG2retenido fallido siguen abiertos,B00/todas las alternativas conservados. Igualdad de archivos no acredita último,reservas o calidad predictiva. Ventana/automatización nocturnas permanecen cerradas,sin otra programación o mensajes externos. Comprobación propia de integridad,no revisión profesional independiente o aprobación humana.''',encoding='utf-8')
    proc=subprocess.run([sys.executable,str(ROOT/'Hackaton/Semana 2/Foro/comentar.py'),'--autor','Codex','--id',fid,'--asunto','Contenido oficial verificado:24Parquet idénticos, sin datos2023 nuevos por esta versión','--cuerpo',str(fp)],capture_output=True,text=True)
    assert proc.returncode==0,proc.stderr;dump(RUN/'forum_receipt.json',json.loads(proc.stdout))
    idx={'id':IDENT,'author':'Codex','utc':now(),'path_base':'workspace_root','status':'all24_official_parquet_byte_identical_to_historical_originals','documentation':rel(DOC),'documentation_sha256':sha(DOC),'run':rel(RUN),'report':{'path':rel(RUN/'report.json'),'sha256':sha(RUN/'report.json')},'decision_journal':{'path':rel(RUN/'decision_journal.json'),'sha256':sha(RUN/'decision_journal.json')},'forum_result':fid,'files_verified':24,'developed':ndev,'emerging':nem,'byte_equal_all':True,'sha256_equal_all':True,'official_MD5_matches_all':True,'historical_local_manifests_match_all':True,'new2023cohort_from_checked_files':False,'row_values_decoded':False,'2024_model_validation_opened':False,'test_rows_interpreted':False,'new_fits':0,'new_predictions':0,'new_scores':0,'new_C0':0,'new_bootstrap':0,'price_reference':'W2-B00','all_alternatives_preserved':True,'professional_independent_validation':False}
    dump(INDEX,idx);changes=[]
    def change(p,fn):
        before=p.read_bytes();after=fn(before.decode('utf-8-sig')).encode('utf-8')
        if before.startswith(b'\xef\xbb\xbf'):after=b'\xef\xbb\xbf'+after
        for phase,b in [('before',before),('after',after)]:
            q=RUN/'registration_cuts'/phase/p.relative_to(ROOT);q.parent.mkdir(parents=True,exist_ok=True)
            with q.open('xb') as f:f.write(b)
        tmp=p.with_name(p.name+'.contenidoOficial.tmp')
        with tmp.open('xb') as f:f.write(after);f.flush();os.fsync(f.fileno())
        assert p.read_bytes()==before,'Concurrent change '+rel(p);os.replace(tmp,p)
        changes.append({'path':rel(p),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':sha(p)})
    def source_update(raw):
        obj=json.loads(raw);prior={k:obj.get(k) for k in ['status','content_version_resolved','new_2023_cohort_confirmed']}
        vals={'version_resolution_before_binary_check':prior,'status':'F01_binary_identity_resolved_no_new2023cohort_other_evidence_gaps_open','content_version_resolved':True,'verified_content_same_as_historical':True,'content_verification_index':rel(INDEX),'content_verification_utc':now(),'frozen_documentary_plan_unchanged':True}
        for k,v in vals.items():raw=top(raw,k,v)
        return raw
    change(SOURCES,source_update)
    change(ROOT/('Preparaci'+chr(243)+'n')/'ESTADO_PROYECTO.json',lambda raw:top(raw,STATEKEY,idx))
    section=f'''\n\n## Contenido binario de los Parquet oficiales verificado

Codex,UTC {now()},foro052,decisiones BIN-01 aBIN-05. Instrucción directa «verifica el contenido». Informe {rel(DOC)},índice {rel(INDEX)},recibos {rel(RUN/'report.json')}.24/24archivos activos(11developed,13emerging)idénticos byte por byte;SHA256descargado/local/histórico yMD5oficial coincidentes,inventario estable,cero errores. F01identidad binaria resuelta,no cohorte2023 nueva o corrección material en estas copias. Plan congelado intacto e índice actual enlazado;no repetir diagnósticos por la fecha remota.

Copias opacas en privado/semana2/integridad_oficial,separadas de datos activos. Sin decoderParquet/dataframes/modelos,no valores/filas2024/test interpretados;no apertura de validación2024,ledger,actas oSEL01. Originales/manifiestos,T0/C0/folds/recetas yB00/todas las alternativas conservados. Cero ajustes,inferencias,scores,C0 o remuestreo nuevos. G1plausible/G2fallida permanecen;igualdad binaria no valida calidad actuarial o último. Ventana/automatización nocturnas siguen cerradas,sin nueva programación,mensajes externos o delegación. Verificación propia de integridad,no revisión profesional independiente o aprobación humana.\n'''
    for name in ['MEMORIA_PROYECTO.md','DECISIONES.md']:change(ROOT/('Preparaci'+chr(243)+'n')/name,lambda raw:raw+section)
    change(ROOT/'RUTAS_PROYECTO.json',lambda raw:top(top(raw,'week_2_official_content_verification_index',rel(INDEX)),'week_2_official_content_verification_report',rel(DOC)))
    oldstates=read(RUN/'unmodified_state_before.json')['files'];obs={'id':IDENT,'utc':now(),'frozen_source_plan_unchanged':sha(frozen_plan)==plan_hash,'active_model_counter_night_indices_unchanged':all(sha(ROOT/x['path'])==x['sha256'] for x in oldstates),'new_model_operations':0,'scope':'Registration and source preservation; binary comparisons not repeated.'}
    dump(RUN/'registration.json',{'changes':changes,'preservation':obs})
    # Do not rehash the downloaded/baseline containers: use the streamed digests.
    other=[p for p in RUN.rglob('*') if p.is_file() and 'opaque_downloads' not in p.parts]+[INDEX,DOC,Path(__file__).resolve(),REPO/'herramientas/verificar_bytes_parquet_oficiales_20261024.py',REPO/'herramientas/recuperar_verificacion_bytes_20261024.py']
    dump(RUN/'manifest.json',{'id':IDENT,'utc':now(),'files':[{'path':rel(p),'sha256':sha(p)} for p in other]+[{'path':x['fresh_opaque_copy'],'sha256':x['fresh_sha256'],'source':'streaming_download_receipt'} for x in r['results']]})
    print(json.dumps({'id':IDENT,'forum':fid,'all24_identical':True,'F01_content_identity_resolved':True,'model_counter_night_indices_unchanged':obs['active_model_counter_night_indices_unchanged'],'source_plan_unchanged':obs['frozen_source_plan_unchanged'],'report':rel(DOC)},ensure_ascii=True))

if __name__=='__main__':main()
