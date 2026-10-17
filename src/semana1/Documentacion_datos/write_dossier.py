"""Dossier local editable y HTML a partir de fuentes congeladas y cifras conciliadas."""
from datetime import datetime, timedelta, timezone
from pathlib import Path
from html import escape
import json
import os
import re
import sys
import unicodedata
from urllib.parse import quote
import collect_documentation as a
import clean_data as c
import pandas as pd
import numpy as np
import mistune
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt


def n(value,dec=0):return f'{float(value):,.{dec}f}'.replace(',','_').replace('.',',').replace('_','.')
def slug(text):return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().lower()).strip('-')
def clean_prose(text):
    """Espaciado editorial, conservando identificadores, rutas y bloques de código."""
    pieces=re.split(r'(```[\s\S]*?```|`[^`\n]*`|\]\([^)]*\)|audit_(?:pre|ren)00|audit_ref_test2025)',text)
    for i in range(0,len(pieces),2):
        s=pieces[i]
        s=re.sub(r'\b([A-Za-zÁÉÍÓÚÑÜáéíóúñü_]+)(?=\d)',lambda m:m[1] if '_' in m[1] or m[1].isupper() else m[1]+' ',s)
        s=re.sub(r'(?<=[A-Za-záéíóúñü]),(?=\d)',', ',s)
        s=re.sub(r'(\bD\d+),(?=\d)',r'\1, ',s)
        s=re.sub(r'[;:](?=\S)',lambda m:m[0]+' ',s)
        s=re.sub(r'(?<=\w)(?=§)',' ',s)
        s=re.sub(r'\+(?=\d)','+ ',s)
        pieces[i]=s
    return ''.join(pieces)
def table(headers,rows):
    cell=lambda x:str(x).replace('|',' / ').replace('\n',' ')
    return '\n'+'| '+' | '.join(headers)+' |\n| '+' | '.join('---' for _ in headers)+' |\n'+''.join('| '+' | '.join(cell(x) for x in row)+' |\n' for row in rows)+'\n'


CSS='''body{margin:0;background:#f2f5f7;color:#1d3341;font:16px/1.72 system-ui,sans-serif}header{padding:34px max(24px,calc((100vw - 1500px)/2));background:#17394d;color:white}header h1{font-size:31px;line-height:1.25;margin:0 0 12px}.layout{max-width:1550px;margin:auto;display:grid;grid-template-columns:270px minmax(0,1fr);gap:28px;padding:24px}.standalone{display:block;max-width:1300px}nav{position:sticky;top:15px;align-self:start;max-height:94vh;overflow:auto;background:white;padding:18px;border-radius:10px}nav a{display:block;font-size:13px;line-height:1.5;margin:8px 0}main{background:white;padding:32px;border-radius:12px;min-width:0}h1{font-size:30px;line-height:1.3}h2{font-size:24px;line-height:1.35;padding-top:25px;border-top:1px solid #dfe8ed;margin-top:35px;scroll-margin-top:20px}h3{font-size:19px;margin-top:25px}a{color:#006f69;text-underline-offset:3px}header a{color:#dcf4f1}table{border-collapse:collapse;min-width:100%;font-size:13px;line-height:1.5}th,td{padding:10px;border-bottom:1px solid #dce5ea;text-align:left;vertical-align:top;min-width:90px}th{background:#edf3f6}td:first-child,th:first-child{min-width:95px}.tablewrap{overflow:auto;max-height:740px;border:1px solid #e3eaee;border-radius:6px;margin:18px 0}pre{overflow:auto;background:#f2f6f8;padding:18px;font-size:12px;line-height:1.55;border-radius:7px}code{font-size:.9em;overflow-wrap:anywhere}img{max-width:100%;height:auto}blockquote{margin:20px 0;padding:10px 20px;border-left:4px solid #b57a28;background:#fff5e3}input{box-sizing:border-box;width:100%;font:inherit;padding:12px;border:1px solid #b4c7d1;border-radius:6px}.field{border-top:1px solid #dfe8ed;padding:18px 0}.field h2{border:0;padding:0;margin:0 0 10px}.field .meta{font-size:13px;color:#566c77}.field p{margin:8px 0}.count{font-size:14px;color:#566c77}button{font:inherit;padding:8px 12px;cursor:pointer;border:1px solid #b4c7d1;background:white;border-radius:5px}footer{font-size:13px;padding-top:25px;color:#526b78}@media(max-width:1000px){.layout{grid-template-columns:1fr;padding:12px}nav{position:static;max-height:none}main{padding:20px}}@media print{nav,header,.controls{display:none}.layout{display:block;max-width:none;padding:0}main{padding:0}h2{break-after:avoid}table{font-size:10px}.tablewrap{max-height:none;overflow:visible}a{color:inherit}body{background:white;font-size:11pt}}'''


def html_document(title,body,links='',toc=True):
    entries=[]
    def replace(match):
        label=re.sub('<[^>]+>','',match[1]);ident=slug(label);entries.append((ident,label));return f'<h2 id="{ident}">{match[1]}</h2>'
    body=re.sub(r'<h2>([\s\S]*?)</h2>',replace,body)
    body=body.replace('<table>','<div class="tablewrap"><table>').replace('</table>','</table></div>')
    nav='<nav aria-label="Índice">'+''.join(f'<a href="#{ident}">{escape(label)}</a>' for ident,label in entries)+'</nav>' if toc else ''
    grid='layout' if toc else 'layout standalone'
    return f'<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>{escape(title)}</title><style>{CSS}</style></head><body><header><h1>{escape(title)}</h1><p>{links}</p></header><div class="{grid}">{nav}<main>{body}</main></div></body></html>'


def main(out):
    assert not (out/'manifest.json').exists()
    f=a.readj(out/'facts.json');sources=a.readj(out/'source_register.json');dictionary=a.readj(out/'dictionary_107.json');state=a.readj(out/'evidence/state.json')
    def url(key):return quote(os.path.relpath(c.ROOT/sources[key]['workspace_relative_path'],out).replace('\\','/'),safe='/')
    def link(key,label=None):return f'[{label or sources[key]["source_id"]}]({url(key)})'
    def report(key,label):return link('report_'+key,label)
    def pathlink(path,label):return '['+label+']('+quote(os.path.relpath(path,out).replace('\\','/'),safe='/')+')'
    cut=datetime.fromisoformat(f['cut_created_utc']).astimezone(timezone(timedelta(hours=-5))).strftime('%Y-%m-%d %H:%M America/Bogota')
    rawrows={row['table']:row['rows'] for row in f['raw_tables']};train=sum(rawrows[x] for x in ['policies_motor','policies_buildings','policies_contents'])
    current_claims=next(x['rows'] for x in f['current_tables'] if x['layer']=='base' and x['table']=='claims')
    idcount=sum(row['id_changes'] for row in f['cleaning_summary']);expcount=sum(row['exposure_changes'] for row in f['cleaning_summary'])
    expbefore=sum(row['exposure_before'] for row in f['cleaning_summary'] if row['table'].startswith('policies_'))
    expafter=sum(row['exposure_after'] for row in f['cleaning_summary'] if row['table'].startswith('policies_'))
    stage=pd.DataFrame(f['capital_stages']);groups=pd.DataFrame(f['pending_groups'])
    fig,axes=plt.subplots(1,2,figsize=(14,5.6))
    labels=stage.rule.tolist();x=np.arange(len(stage))
    axes[0].bar(x,stage.cumulative_corrected,color='#397b8c',label='Capitales corregidos acumulados')
    axes[0].bar(x,stage.remaining,bottom=stage.cumulative_corrected,color='#d9a75c',label='Capitales pendientes')
    for i,row in stage.iterrows():axes[0].text(i,3527+35,n(row.remaining),ha='center',fontsize=10)
    axes[0].set_xticks(x,labels,rotation=30,ha='right');axes[0].set_ylim(0,3950);axes[0].set_ylabel('Filas de capital extremo originales');axes[0].set_title('3.527 filas originales, sin doble conteo');axes[0].legend(loc='upper center',bbox_to_anchor=(.5,-.2),fontsize=9,frameon=False)
    groupnames={'A_retrospective_D34':'Conflicto numérico conservado','C_no_original_normal_reference':'Sin referencia original habitual','D_CAP01_dependency_only':'Dependen de CAP01','E_TW_dependency':'Dependen de T/W','F_incomplete_context':'Contexto incompleto','G_other_conflicts':'Otros conflictos'}
    groups=groups.sort_values('rows',ascending=False)
    axes[1].barh([groupnames.get(x,x) for x in groups.review_group],groups.rows,color='#397b8c');axes[1].invert_yaxis()
    for i,v in enumerate(groups.rows):axes[1].text(v+2,i,n(v),va='center')
    axes[1].set_xlim(0,180);axes[1].set_xlabel('Filas pendientes');axes[1].set_title('419 pendientes en CAP06R')
    for ax in axes:ax.spines[['top','right']].set_visible(False)
    fig.suptitle('Capitales al cierre D61 · Las categorías residuales conservan su clasificación histórica',fontsize=14);fig.tight_layout(rect=[0,.06,1,.95]);fig.savefig(out/'figures/capitales_y_pendientes.png',dpi=160,bbox_inches='tight');plt.close(fig)
    roles={'customers':'Un cliente; maestro compartido y sin versión histórica por año.','addresses':'Un inmueble/dirección; atributos físicos y geográficos.','weather':'Dirección y año; no implica disponibilidad ex ante de todo el clima anual.',
        'claims':'Un expediente reportado, valorado al 31-12-2024.','sample_submission':'Una salida por fila test; no contiene costes reales.'}
    inventory=table(['Tabla original','Filas','Columnas','Unidad de observación'],[(x['table'],n(x['rows']),x['columns'],roles.get(x['table'],'Un periodo de póliza de '+('2025' if x['table'].startswith('test_') else '2021 a 2024')+'.')) for x in f['raw_tables']])
    matrix=[
        ['ID01','D32','123.664 celdas customer_id','Ceros iniciales hasta ocho dígitos; maestro único y referencia existente.','Solo autos; no fusionar claves distintas del maestro.'],
        ['EXP01','D32','14.229 celdas exposure','Días cubiertos inclusivos/365; cuatro decimales.','No cambiar fechas ni recortar exposición a1.'],
        ['CAP01','D36','2.073 celdas sum_insured','División por mil en lista autorizada con respaldo anterior original.','Base; no cascadas ni corrección de los1.454 restantes.'],
        ['CAT01','D38','700.210 celdas construction_type','Mapa explícito de alias de caja.','t y w permanecen separados.'],
        ['AGE01','D38','2.936 celdas policyholder_age','Años cumplidos al inicio desde nacimiento del maestro.','Cambio de definición; no cambia driver_age.'],
        ['DUP01','D42','604 copias excluidas de claims','Igualdad total salvo ID; conserva CL+ocho dígitos.','Alias y filas excluidas conservados;57 grupos no idénticos intactos.'],
        ['REN00','D45','12.041 periodos marcados','audit_ren00 en todas las filas de2.742 pólizas congeladas.','No retirar pólizas ni siniestros, ni alterar fechas/etiquetas.'],
        ['PRE00','D47','413 siniestros marcados','audit_pre00; coste fuera del objetivo de periodos actuales.','No borrar siniestros ni modificar importes/estados/fechas.']]
    stages_table=table(['Regla','Decisión','Cambios nuevos','Corregidos acumulados','Pendientes','Anclas posteriores test2025 nuevas','Filas test corregidas'],[[r['rule'],r['decision'],n(r['rows']),n(r['cumulative_corrected']),n(r['remaining']),n(r['new_test2025_anchors']),n(r['test_rows_changed'])] for r in f['capital_stages']])
    period_roles=[['customer_id','policies → customers','many_to_one','Maestro único; no sumar varias filas de cliente.'],['address_id','policies → addresses','many_to_one','Compartir dirección no implica mismo tomador ni mismos bienes.'],['address_id + year','policies → weather','many_to_one','Separar año de exposición de fecha de publicación del clima.'],['policy_id + line + loss_date','claims → periodo','Una asignación o excepción explícita','La fecha de ocurrencia debe caer entre period_start y period_end inclusivos.'],['row_id','test → sample_submission','one_to_one','Una predicción por fila, sin pérdidas ni duplicaciones.']]
    doc=f'''# Documentación de los datos de la primera semana

Versión documental 1.0. Corte de datos D61, {cut}. Rama retrospectiva CAP06R y protocolo metodológico {f['protocol_version']}. Las fechas UTC de las carpetas pueden ser del día siguiente al día local.

Los once Parquet originales se conservan. La preparación tiene dos ramas: la base mantiene 1.454 capitales pendientes; la rama retrospectiva incorpora 1.035 correcciones adicionales y conserva 419 pendientes. Las reglas aplicadas tienen listas de cambios y evidencia de verificación, pero ninguna rama está aprobada todavía como conjunto final para entrenar o entregar predicciones.

Este dossier permite seguir cada dato desde el archivo recibido hasta la versión que lo consume, comprender las decisiones actuariales y localizar lo que falta resolver. Los resultados de revisiones anteriores conservan su fecha y su catálogo; sus cifras no se presentan automáticamente como cifras de CAP06R.

## Estado de los datos al cierre

{table(['Elemento','Estado al corte','Referencia'],[
['Originales','11 archivos Parquet intactos;105 nombres de campo y242 ocurrencias de columna.',link('routes','Mapa de rutas')],
['Periodos de póliza',n(train)+' train y'+n(rawrows['sample_submission'])+' test.',link('official_dictionary','Diccionario oficial archivado')],
['Siniestros',n(rawrows['claims'])+' originales;'+n(current_claims)+' después de DUP01;413 marcados PRE00.',report('prehistory_audit_application','PRE00')],
['Base preparada','ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00;1.454 capitales pendientes.',link('week_1_prepared_data_index','Índice base')],
['Rama retrospectiva','CAP06R;3.108 correcciones de capital totales y419 pendientes.',link('week_1_retrospective_prepared_data_index','Índice retrospectivo')],
['Auditoría','audit_ren00 y audit_pre00;107 nombres de campo en el catálogo derivado.','dictionary_107.json'],
['Preparación para modelos','T0/F0 y particiones operativas pendientes; sin entrenamiento en este trabajo.',link('methodological_protocol','Protocolo1.10')]])}

El índice base apunta al catálogo `{f['base_catalog_workspace_relative']}`. El retrospectivo apunta a `{f['retrospective_catalog_workspace_relative']}`. Los archivos current_run.json de otras carpetas identifican una operación o revisión concreta. No son intercambiables con esos dos índices de entrada.

## Archivos recibidos y unidades de observación

Los datos activos originales están en `Hackaton/Semana 1/Datos`. La descarga y el ZIP permanecen en `Preparación/data/raw/iaa_2026_part1_20261016`. El mapa central resuelve las rutas relativas desde `C:/dev/Hakaton`; las rutas antiguas archivadas no se reescriben.

{inventory}

Las filas de póliza representan años naturales completos o fracciones de año. Una modificación durante el año puede generar varios periodos de la misma póliza. No deben contarse como asegurados distintos ni sumarse sus capitales como si fueran bienes diferentes. Los periodos terminan antes si hay cancelación o baja. El test corresponde a 2025 y sus 626.639 filas deben conservar su identidad al preparar la salida.

Las cifras anteriores se leen de los metadatos de los originales en esta conciliación. El historial de EDA, D30, usa los originales previos a DUP01. {report('data_validation','Consultar EDA y gráficos históricos')}. Los ficheros son sintéticos para el concurso; su procesamiento en servicios de IA se rige por el contrato archivado y no constituye permiso general de redistribución. {link('rules','Reglas archivadas del proyecto')}.

## Relaciones entre tablas y definición temporal

{table(['Clave','Relación','Cardinalidad exigida','Cuidado al construir datos'],period_roles)}

Una póliza mantiene policy_id entre años. El cliente puede tener varios ramos y varias personas pueden compartir una dirección. La clave de siniestro no debe unirlo indiscriminadamente a todos los años de su póliza: la asignación usa su ramo y fecha de ocurrencia. report_date indica cuándo se conoció, no el periodo de riesgo al que pertenece.

Las cardinalidades deben comprobarse en el ensamblado real: un join no debe multiplicar filas, exposición o coste de forma inadvertida. La revisión de claves y los diagnósticos existentes no sustituyen esos contratos dentro del futuro constructor de X y del objetivo. También falta fijar qué versión temporal de cada maestro podría conocerse en cada corte.

## Diccionario actuarial de las variables

El [diccionario consultable](diccionario.html) reúne los 105 nombres originales y las dos marcas derivadas. Cada entrada indica tablas, significado para el seguro y la tarifa, observaciones de disponibilidad, propuesta inicial D30 y tratamiento actual. También está en [CSV](tables/dictionary_107.csv) y [JSON](dictionary_107.json). La inclusión de una columna en el diccionario no la aprueba como predictor.

sum_insured es el límite de edificios o de contenidos, según el ramo. Es un importe por riesgo y periodo; no es prima ni pérdida observada, y no se anualiza con exposure. Un límite mayor puede cambiar la pérdida cubierta, pero no determina una variación proporcional de la prima o del coste esperado. vehicle_value_group en autos es una categoría de valor, no un importe monetario comparable al capital de hogar.

exposure mide tiempo cubierto. voluntary_excess y compulsory_excess son franquicias; el diccionario ya describe paid_to_date neto de franquicia, por lo que no se deben restar automáticamente otra vez del coste observado. incurred_to_date incluye pagado y estimación de caso, y recoveries son recuperaciones observadas. Los abiertos y los siniestros aún no reportados impiden equiparar ese incurrido con coste último conocido.

renewal_decision es un desenlace de fila y falta en test. audit_ren00 y audit_pre00 son metadatos de auditoría. customer_service_contacts tiene un problema distinto: la investigación D50 recomendó excluirlo por relación contemporánea con los siniestros y deriva, pero el guard vigente aún lo deja pasar. Esta brecha permanece abierta.

## Cómo se conserva el linaje

La unidad de preservación es el archivo original. Cada aplicación crea otra carpeta de corrida, un catálogo y bitácoras; no reemplaza el Parquet recibido. Cada catálogo declara rutas desde la raíz y SHA256. Las tablas sin cambios pueden seguir referenciando un archivo de una corrida anterior. No es necesario copiar las once tablas en cada operación.

El recorrido de pólizas es originales → ID01/EXP01 → CAP01 → CAT01/AGE01 → REN00. El de siniestros es original → DUP01 → PRE00. El catálogo base reúne ambas rutas. La rama retrospectiva parte de esa preparación y añade CAP02R → CAP03R → CAP04R → CAP05R → CAP06R sobre los capitales, heredando todos los demás datos.

Para identificar un padre no basta mirar parent_sha256: las operaciones añaden claves específicas como audit_parent_sha256 o endorsement_capital_parent_sha256. Se deben leer el índice, el catálogo completo, lineage.json y los hashes de la operación. Los códigos y los punteros se conservan por separado para poder distinguir qué versión se consumió.

La bitácora de un cambio de valor guarda identidad, tabla, posición, valor anterior y nuevo, regla, y referencias de revisión cuando proceden. Las operaciones recientes añaden hashes de cohorte, solicitud, origen y derivado. La reversión reconstruye los valores y la tabla Arrow del padre; no implica que el archivo Parquet recomprimido deba tener los mismos bytes. SHA256 comprueba la preservación de los archivos originales; la igualdad Arrow comprueba filas, valores, tipos y metadatos.

## Reglas aplicadas en la base

{table(['Regla','Decisión','Alcance','Qué hace','Límite'],matrix)}

Los alcances cuentan celdas, filas o pólizas según la regla. No se suman para obtener un número de observaciones distintas: una misma fila puede recibir varios ajustes o una marca posterior. Los 12.041 REN00 son periodos de 2.742 pólizas; los 413 PRE00 son expedientes de siniestro.

## Identificadores de clientes y exposición

ID01 recuperó {n(idcount)} celdas de customer_id: 98.110 en train de autos y25.554 en test de autos. El código se trata como texto de ocho dígitos ASCII. La preparación rechaza claves inválidas, exige unicidad del maestro y pertenencia a él. No se fusionaron dos claves diferentes del maestro. El recálculo de Claude encontró una proporción de IDs cortos coherente con la pérdida de ceros iniciales.

EXP01 cambió {n(expcount)} exposiciones de train, repartidas así:

{table(['Tabla','Cambios de exposición','Antes en años registrados','Después con días inclusivos /365'],[[r['table'],n(r['exposure_changes']),n(r['exposure_before'],4),n(r['exposure_after'],4)] for r in f['cleaning_summary'] if r['table'].startswith('policies_')])}

La exposición total de train pasa de {n(expbefore,4)} a {n(expafter,4)} años. El test no necesitó correcciones de exposición. La regla es round((period_end − period_start +1)/365,4). Las fechas no cambian. Un periodo inclusivo de366 días daría1,0027; ese ejemplo explica la convención, no afirma que haya tal periodo en los datos. D59 registró que los periodos2024 terminan como máximo el30 de diciembre.

La convención dominante respalda ACT/365, pero no equivale a confirmación del organizador. Sin uniformar unidades, una tasa por año podría tener un denominador artificialmente grande. No debe dividirse ciegamente toda exposición entre365 ni reconstruirse un capital a partir de la exposición. {report('data_cleaning','Limpieza ID01 y EXP01')}.

## Categorías de construcción y edad

CAT01 unifica las variantes explícitas de construction_type: Brick/BRICK→brick, STONE→stone, NON_STANDARD→non_standard, T→t y W→w, según el mapa archivado. Cambió555.824 celdas de train de edificios y144.386 de test, total700.210. La normalización de caja no unifica t y w.

La revisión longitudinal de T/W encontró evidencia de recodificación alrededor de2023 y preparó una candidata CON01. Esa candidata continúa fuera de los catálogos activos; el material físico que significan los códigos no se confirmó. Los16 pendientes que dependen de T/W no quedan resueltos por CAT01. {report('construction_review','Revisión de construcción y candidata no activa')}.

AGE01 define policyholder_age de hogar como años cumplidos desde customers.date_of_birth hasta period_start. Cambió1.122/300 filas de train/test de edificios y1.209/305 de contenidos, total2.936. La edad de conductor de autos se conserva, porque puede corresponder a otra persona.

El recálculo D59 explica2.432 diferencias por edad a la fecha de cotización,457 por cumpleaños en el propio día de inicio y45 por edad al final del periodo. Son2.934 explicadas y dos sin explicar en esa revisión. Por tanto, AGE01 establece una definición común; no demuestra2.936 errores de captura. La memoria inicial que resumía los tres grupos como explicación de todas las diferencias queda matizada por este corte. Los valores anteriores siguen en bitácora. {report('data_refinement','Refinamiento CAT01 y AGE01')} · {link('D59_evidence','Evidencia D59 de las convenciones')}.

## Capitales y criterios de corrección

La revisión inicial separó3.527 capitales extremos para estudiar: más de10 millones CU en edificios o más de1 millón en contenidos. Esos umbrales son filtros de revisión, no límites contractuales. Una cifra alta o una coincidencia de dirección por sí sola no autorizó una reparación.

CAP01 dividió por mil2.073 filas con una referencia anterior original de la misma póliza, contexto exigido conocido e igual, ausencia de solape, distancia entre inicios de1 a400 días y razón entre capital hipotético y referencia dentro de0,90–1,10. Se conservaron1.454 pendientes y no se generaron cascadas a partir de reparaciones recién hechas. {report('capital_review','Revisión de capitales')} · {report('capital_correction','Aplicación CAP01')}.

Los campos comparados en edificios fueron customer_id, address_id, construction_type, occupancy, accidental_damage_cover, voluntary_excess, compulsory_excess, smoke_alarms y mortgage. En contenidos fueron customer_id, address_id, tenure, security_level, high_value_items, accidental_damage_cover, works_from_home, lodgers, bicycle_cover y ambas franquicias. Igualdad en esos campos es un criterio parcial; no prueba que todos los factores tarifarios o el riesgo físico permanezcan constantes.

La segunda implementación D59 añade evidencia global compatible con la hipótesis×1000: separación de las nubes y coincidencia aproximada de medianas tras dividir. No confirma la unidad por el sistema de origen. No se usan importes de siniestro o prima para elegir el capital que conviene ni se copian límites de otra fecha.

## La rama retrospectiva de capitales

{stages_table}

La columna de anclas cuenta respaldos posteriores de test2025 para una corrección retrospectiva; la última columna cuenta filas corregidas que pertenecen a test. Son cosas diferentes. CAP01 utiliza respaldo anterior, por lo que la columna de anclas posteriores es cero; corrigió540 filas test. La rama retrospectiva corrige otras13 filas test, todas en CAP05R, y usa136 anclas posteriores test acumuladas.

CAP02R aplicó las867 propuestas de D48,430 edificios y437 contenidos; todas tenían respaldo posterior,111 de test2025. CAP03R añadió once de las doce discrepancias revisadas en D51 y mantuvo C48613718 pendiente, con un respaldo test nuevo. CAP04R corrigió109 filas con contexto anterior distinto pero respaldo posterior completo compatible,75 edificios y34 contenidos, con17 apoyos test. Cada lista quedó congelada antes de aplicar. {link('CAP02R_rules','CAP02R')} · {link('CAP03R_rules','CAP03R')} · {link('CAP04R_rules','CAP04R')}.

CAP05R aplicó46 de las48 referencias distantes revisadas:18 edificios y28 contenidos, con21 anclas anteriores y25 posteriores; siete apoyos test y13 filas test corregidas. La excepción DIST01-R exige primera referencia original completa elegida antes del contexto/importe, extremos completos e iguales, más de400 días y hasta dos años calendario, una sola fila intermedia incompleta sin cambios conocidos y pasos monetarios compatibles. Los20 huecos CAL00 de sus92 enlaces se conservaron. No se amplió el criterio general de400 días. {link('CAP05R_rules','Regla DIST01-R aplicada a la lista de46')}.

CAP06R añadió solo C00502745 y C00399729, como excepción manual por revisión de ampliaciones y renovaciones. Estas dos filas siguen sin cumplir DIST01-R; no se declara que una regla anterior haya pasado por reinterpretación. {link('CAP06R_rules','Excepción manual CAP06R')}.

![Evolución de capitales corregidos y grupos pendientes](figures/capitales_y_pendientes.png)

La suma se concilia en cada paso: corregidos acumulados + pendientes =3.527. Al corte son3.108 +419. Las1.035 correcciones retrospectivas son867+11+109+46+2. La base no incorpora estas1.035. Las fechas anteriores de algunas anclas no convierten la selección retrospectiva de la regla en un procedimiento causal disponible en aquel momento.

## Dos casos completos de ampliaciones y renovaciones

{table(['Periodo','C50633171','C56600576'],[
['2021 original','C00502745:27.200.000 CU','C00399729:25.700.000 CU'],
['2021 después de CAP06R','27.200 CU','25.700 CU'],
['2022 antes de ampliación','C01100142:27.700 hasta03-05','C00997126:26.200 hasta11-09'],
['2022 ampliado','C01153989:39.400 desde04-05','C01147928:37.700 desde12-09'],
['2023 al renovar','C01702744:28.300 hasta15-05','C01618408:26.700 hasta03-02']])}

Los contadores de renovación son7→8→8→9 y15→16→16→17. Las ampliaciones observadas de2022 son42,24% y43,89%; al renovar bajan28,17% y29,18%. Dividir únicamente2021 por mil conserva esa variación y da aumentos hacia la base inicial2022 de1,84% y1,95%. No hay siniestros observados para estas pólizas. Los nulos high_value_items de C01100142 y security_level de C00997126 siguen sin imputar.

D60 comparó el patrón con otras2.305 pólizas originales, excluyendo las dos focales de sus estadísticas. La selección fue exploratoria, después de observar los casos; no constituye una validación independiente o una prueba contractual. La autorización posterior D61 se limita a los dos IDs y conserva las primeras referencias completas de2022 aunque contradigan una trayectoria suave. {report('endorsement_capital_review','Revisión de ocho periodos')} · {report('endorsement_capital_application','Aplicación y seis periodos preservados')}.

## Siniestros duplicados y coste observado

DUP01 identifica604 pares con igualdad de los once campos distintos de claim_id;1.208 registros implicados. Se conserva el representante CL seguido de ocho dígitos y se excluye su copia de nueve dígitos. El identificador completo retenido tiene diez caracteres por incluir CL. La selección se congela y guarda alias, exclusiones, originales de las filas y reversión.

claims pasa de163.150 a162.546 registros. Los600 pares de2022, tres de2021 y uno de2020 no representan604 nuevos siniestros tras depurar. La reducción de incurrido neto aceptado registrada es3.174.167,49 CU, de los cuales358,88 corresponden a prehistoria y3.173.808,61 a periodos observados. Es un efecto sobre el agregado diagnóstico de ese corte, no ahorro económico producido por la IA ni estimación de pérdida última evitada.

Los57 grupos de coincidencias no idénticas se conservaron; no se borran por compartir póliza y fecha. Los demás siniestros y las pólizas permanecen. El EDA previo y el diagnóstico previo a DUP01 se consultan como históricos; el diagnóstico posterior recalcula el agregado con la capa depurada. {report('duplicate_claim_review','Revisión de los604 pares')} · {report('duplicate_application','DUP01 aplicado y alias')}.

## Prehistoria de siniestros y objetivo

PRE00 marca413 siniestros anteriores al primer periodo observado de su póliza. Son409 aceptados y cuatro repudiados; el incurrido neto aceptado observado es1.721.459,84 CU. Se conservan los162.546 expedientes completos, sus importes, fechas y estados. Los413 no se trasladan al primer periodo observado ni se convierten en pérdidas de una cobertura no registrada.

La marca audit_pre00 y target_scope.py impiden cargar su coste al objetivo de los periodos actuales; una asignación contradictoria obliga a revisar, no se resuelve silenciosamente moviendo fechas o poniendo importes a cero. D59 observó que los413 se reportaron dentro de alguna cobertura observada, hecho compatible con reporte tardío pero insuficiente para reconstruir la cobertura histórica de ocurrencia. {report('prehistory_claim_review','Revisión de prehistoria')} · {report('prehistory_audit_application','PRE00 y conciliación financiera')}.

El contrato económico busca coste último esperado por periodo en CU. El primer objetivo operativo propuesto T0 es incurrido observado neto de recuperaciones, excluyendo repudiados y respetando la asignación por ocurrencia. Las tablas diagnósticas existentes no son el T0 final materializado para entrenar. Abiertos, reporte tardío y valoración única al31-12-2024 limitan una validación histórica causal: usar importes valorados después del corte no los hace conocidos en ese corte. {link('methodology','Objetivo y validación metodológica')}.

La salida solicitada por el reto es una predicción no negativa de coste por cada periodo test, en CU; no una prima comercial ni una tasa anual aislada. El contrato archivado define Tweedie D² con potencia1,5. El scorer efectivo y la transformación entre tasas y coste por periodo aún deben implementarse y probarse conforme al protocolo; la documentación del contrato no acredita esa implementación.

## Calendario y rechazos de renovación

La revisión CAL00 estudió500.245 continuidades que dejan sin cubrir el31-12-2024:200.063 de autos,150.111 de edificios y150.071 de contenidos. Los periodos terminan el30-12 y reaparecen el01-01-2025. El usuario decidió mantener las fechas pendientes. EXP01 respeta los días registrados, sin añadir ese día. No se desplazan siniestros para acomodar la discontinuidad. {report('calendar_review','Revisión del calendario')}.

La revisión de rechazos identificó2.742 pólizas con declined_by_insurer en2024 que continúan en2025. REN00 marca todas sus12.041 filas,9.110 train y2.931 test. No cambia etiquetas, fechas o siniestros. La continuidad observada impide interpretar automáticamente ese código como ausencia de cobertura posterior; su significado de negocio permanece sin confirmar. La pertenencia retrospectiva a REN00 tampoco es información ex ante de tarifa. {report('declined_renewal_review','Historias de rechazo')} · {report('renewal_audit_application','REN00 aplicado')}.

## Los419 capitales pendientes actuales

{table(['Grupo histórico conservado','Filas actuales','Tratamiento al corte'],[[r['review_group'],n(r['rows']),{'C_no_original_normal_reference':'Mantener108 por instrucción humana; no demostrar escala absoluta por vecinos de otras pólizas.','F_incomplete_context':'154 residuales tras revisar202 y corregir48 en CAP05R/CAP06R; conservar nulos.','G_other_conflicts':'138 sin adjudicación nueva; revisar cada conflicto.','E_TW_dependency':'16 pendientes; CON01 no activa.','D_CAP01_dependency_only':'Dos dependencias de reparaciones anteriores; sin cascada.','A_retrospective_D34':'Una discrepancia numérica conservada, C48613718.'}.get(r['review_group'],'Sin cambio.')] for r in f['pending_groups']])}

Los nombres de grupo proceden del inventario histórico; no se reevalúan para convertirlos en etiquetas de modelo. C48613718/C01596694 conserva29.300.000 CU. B19256617/B00962235 conserva377.000.000, aunque otra fila de la misma póliza recibió corrección previa. B67263929 tiene dos de los108 registros sin referencia original:107 pólizas no equivalen a108 registros. Las historias no justifican cascadas o imputación silenciosa.

Hay177 filas pendientes en test2025 en CAP06R, frente a190 en la base. No se pueden presentar419 como pendiente de todas las versiones ni190 como pendiente del test retrospectivo. La tabla [pendientes actuales por origen](tables/current_pending_by_table.csv) y el [inventario de419](tables/pending_419_snapshot.csv) identifican el conjunto de este corte. El tratamiento para modelar valores extremos aún requiere decisión explícita y preparación dentro de cada corte, no se considera resuelto por documentarlos.

## Validaciones realizadas y alcance de la evidencia

Cada operación conservó su propia verificación: listas congeladas, comparación con el padre, preservación de otros campos, bitácora y reversión. Las operaciones recientes prueban también segunda aplicación sin cambios y rechazo de un valor inesperado. Que un control técnico pase acredita su criterio, no el significado contractual de una variable o la idoneidad completa del conjunto para modelar.

D59 es una segunda implementación asistida por Claude, desde originales y definiciones del proyecto, con41 comprobaciones satisfactorias. Recalculó la base y la rama hasta CAP05R, sin reutilizar el código de aplicación de Codex. Aporta contraste de implementación; comparte definiciones y supuestos del proyecto, y declara revisión humana pendiente. No se denomina auditoría humana o validación independiente profesional. Su informe y dashboard no se reescriben para aparentar cobertura de CAP06R. {link('D59_report','Revisión crítica D59')}.

CAP06R tiene279 controles propios y siete comprobaciones posteriores de activación, con reversión e idempotencia acreditadas. No se suman las pruebas de todas las corridas como observaciones independientes o una puntuación de confianza. Este dossier concilia fuentes, catálogos, metadatos y conjuntos de capitales; no reejecuta los58 controles completos ni todas las reglas históricas.

La comprobación actual del guard1.0 bloquea renewal_decision, audit_ren00 y audit_pre00, pero customer_service_contacts sigue aceptada. El resultado exacto está en [guard_probe.json](guard_probe.json). La exclusión de contactos debe aplicarse y probarse antes de entrenar; la recomendación D50 no es todavía una garantía operativa. El diccionario F0 y los selectores reales deberán tener pruebas de esta y otras dependencias temporales.

## Trabajo pendiente antes de modelar

El [registro de58 controles](validaciones.html) conserva prioridad, alcance, criterio de cierre y trabajo pendiente de D56, más actualizaciones documentales al corte D61. Es una conciliación de estados, no una nueva aprobación de cada control. El registro se ofrece también en [CSV](tables/validation_register_58.csv) y [JSON](validation_register_58.json).

Los bloqueos de preparación son construir y conciliar T0 con componentes; fijar F0 y excluir contactos/etiquetas posteriores; implementar joins con cardinalidades; congelar V22/V23/V24 y roles sin contaminación; preparar transformaciones dentro de cada entrenamiento; y probar scorer, unidades y cobertura final de filas. El calendario2024, la semántica de rechazo, los419/1.454 capitales y la información de origen siguen pendientes según el catálogo elegido.

Se mantienen abiertas las coherencias de autos, coberturas e importes de hogar, maestros sin versión, clima anual, telemática, primas y atributos comerciales. D59 registra161.822 NCB superiores a años con licencia,3.717 edades implícitas de licencia menores de16 y2.533 eléctricos sin cilindrada. Son sondeos de revisión, no autorización para recortar o imputar. Tras DUP01, su corte registra502/1.087 siniestros de daño accidental sin opción en edificios/contenidos y cuatro de daño propio fuera de comprehensive. Los ocho/tres netos superiores al capital que allí figuran no se presentan como recálculo sobre CAP06R.

Para avanzar, cada incidencia necesita una decisión con motivo, alcance temporal y verificación reproducible. Aprobar una cohorte de reparación no aprueba automáticamente entrenamiento, una regla de imputación general o un envío. T/W, nulos y los57 grupos de siniestros no idénticos permanecen sin depuración automática.

## Uso de IA y responsabilidad de las decisiones

El participante definió prioridades, pidió revisiones de casos y autorizó explícitamente los conjuntos aplicados. Codex preparó análisis, código, propuestas y controles propios. Los informes enlazan las solicitudes y listas congeladas; una propuesta sin aplicar no se cuenta como transformación. Claude aportó investigación D50 y una segunda implementación D59 a solicitud del participante, con sus versiones y límites.

El informe D59 registra que los once originales y las capas analizadas se copiaron al espacio de trabajo en la nube de Claude y se contrastaron por SHA256 con los catálogos. Ese procesamiento previo forma parte de su procedencia, bajo el uso del concurso descrito en el contrato; no supone permiso de redistribución. Su resultado se cita con el catálogo CAP05R que realmente verificó.

Jev/TypeSafe se evaluó antes de financiarlo: saldo observado cero, un intento bloqueado por falta de fondos, cero decisiones de modelo recibidas, cero cargas de dataset y un piloto de18 casos preparado sin ejecutar. No se añadieron fondos ni se usó Jev para decidir correcciones. No se acredita su precisión o calibración actuarial. {report('ai_validation_tool_assessment','Evaluación Jev y propuesta de piloto')}.

Las referencias IAA priorizadas orientan ficha y linaje de datos (Documentación§2), reproducción/uso/riesgos (§§4–6), distinción de verificación propia y validación independiente (Gobernanza§2.8) y responsabilidad humana/comunicación de IA (Consideraciones profesionales§3.2 y§§3.5–3.6). Son documentos educativos; esta trazabilidad no acredita una certificación profesional. {link('IAA_priorities','Prácticas IAA aplicadas')}.

## Cómo leer y reproducir la preparación

Se parte siempre de RUTAS_PROYECTO.json. Para análisis de base se abre current_dataset.json; para una reconstrucción retrospectiva explícita, current_retrospective_dataset.json. Antes de leer un archivo se verifica el SHA256 del catálogo. Un análisis guarda el hash del índice y del catálogo que consumió, ya que los punteros current pueden avanzar.

Los scripts de aplicación históricos exigen su padre congelado. No deben lanzarse contra CAP06R esperando reconstruir de nuevo una etapa anterior. Para reproducción integral hace falta un espacio aislado con la misma estructura, originales verificados, catálogos y padres de cada operación; restaurar el código archivado en su ubicación lógica y recorrer las instrucciones de esa operación. No se redirigen los índices de trabajo ni se ejecutan scripts dentro de source_snapshot asumiendo que sus rutas sigan siendo correctas allí. La reproducción integral aislada no se declara realizada por este dossier.

Los artefactos cerrados permiten una comprobación de integridad sin repetir transformaciones. Por ejemplo, el CLI de CAP06R devuelve una verificación de aplicación ya existente al repetir prepare, y verify sobre una corrida cerrada verifica el manifiesto. Eso no es por sí solo un recálculo independiente de la regla. Los comandos de la última operación son:

```powershell
& '.\\Preparación\\.venv\\Scripts\\python.exe' '.\\Hackaton\\Semana 1\\Limpieza\\endorsement_capitals.py' prepare
& '.\\Preparación\\.venv\\Scripts\\python.exe' '.\\Hackaton\\Semana 1\\Limpieza\\endorsement_capitals.py' verify 'C:\\dev\\Hakaton\\Hackaton\\Semana 1\\Limpieza\\runs\\capendorse_20261017T010844Z_fbf8cc20'
```

D59 conserva validar_ajustes.py para un nuevo recálculo desde originales; su informe antiguo no actualiza su alcance sin una nueva ejecución y evidencia. Las bitácoras, hashes y solicitudes de cada operación están en sus carpetas. Los originales, carpetas cerradas y sus manifiestos se mantienen como evidencia; para corregir una presentación se crea una edición nueva.

## Registro de decisiones y fuentes

El [recorrido de decisiones](decisiones.html) recoge D28 a D61 e indica dónde se aplicó, revisó o dejó pendiente cada asunto. Los registros de modelos son contexto de preparación, sin atribuir entrenamiento. La decisión documental posterior no incorpora otra transformación de datos.

El [registro de fuentes](fuentes.html) enlaza los archivos que respaldan esta síntesis, con SHA256 y copia de los contextos mutables usados al comenzar. [facts.json](facts.json) contiene las cifras conciliadas; [source_register.json](source_register.json), la procedencia. Los índices base/retrospectivo y los archivos de datos se protegen por hash antes y después de la documentación. La evidencia de comprobación del dossier se guarda en [documentation_verification.json](documentation_verification.json).

Esta fotografía se actualiza mediante una nueva corrida cuando cambien datos o decisiones. El nombre CAP06R en una fuente, los1.454 de la base, los419 de la rama y el alcance CAP05R de D59 son parte del significado de sus resultados; deben viajar con ellos al citar cifras o preparar una entrega.
'''
    doc=clean_prose(doc)
    (out/'DOCUMENTACION_DATOS.md').write_text(doc,encoding='utf-8')
    md=mistune.create_markdown(escape=True,plugins=['table'])
    rendered=md(doc)
    # Main title already appears in the native HTML header.
    rendered=re.sub(r'^<h1>[\s\S]*?</h1>\s*','',rendered,count=1)
    links='<a href="DOCUMENTACION_DATOS.md">Versión editable</a> · <a href="diccionario.html">Diccionario</a> · <a href="validaciones.html">58 controles</a> · <a href="fuentes.html">Fuentes</a>'
    (out/'informe.html').write_text(html_document('Documentación de los datos de la primera semana',rendered,links),encoding='utf-8')
    # Complete field reference, searchable locally without network or external assets.
    cards=[]
    for row in dictionary:
        search=clean_prose(' '.join([row['column'],row['meaning'],*row['tables'],row['treatment_at_cut']])).casefold()
        availability_label='Disponibilidad de la marca derivada' if row['column'].startswith('audit_') else 'Disponibilidad descrita en D30'
        cards.append(f'<article class="field" id="campo-{escape(row["column"])}" data-search="{escape(search,quote=True)}"><h2>{escape(row["column"])}</h2><p class="meta">Tablas: {escape(", ".join(row["tables"]))}</p><p>{escape(clean_prose(row["meaning"]))}</p><p>{escape(clean_prose(row["insurance_and_tariff"]))}</p><p>{availability_label}: {escape(clean_prose(row["availability"]))}</p><p>Tratamiento al corte D61: {escape(clean_prose(row["treatment_at_cut"]))}</p><details><summary>Propuesta inicial y procedencia</summary><p>{escape(clean_prose(row["original_proposed_treatment_D30"]))}</p><p>{escape(row["definition_source"])}</p></details></article>')
    fieldbody='<p>105 campos originales y dos marcas añadidas. Las notas D30 se conservan identificadas como iniciales; el tratamiento al cierre distingue cambios aplicados y propuestas. La disponibilidad F0 no está aprobada por listar una variable aquí.</p><div class="controls"><label for="fieldSearch">Buscar campo, tabla o término</label><input id="fieldSearch" type="search" placeholder="Por ejemplo: sum_insured, motor, audit"><p id="fieldCount" class="count">107 de 107 campos</p></div>'+''.join(cards)+'''<script>document.getElementById('fieldSearch').addEventListener('input',e=>{const q=e.target.value.toLocaleLowerCase('es').trim();let count=0;for(const el of document.querySelectorAll('.field')){const visible=el.dataset.search.includes(q);el.hidden=!visible;if(visible)count++;}document.getElementById('fieldCount').textContent=count+' de 107 campos';});</script>'''
    (out/'diccionario.html').write_text(html_document('Diccionario de datos y tratamiento actual',fieldbody,'<a href="informe.html">Volver al dossier</a> · <a href="tables/dictionary_107.csv">CSV</a>',False),encoding='utf-8')
    backlog=a.readj(out/'validation_register_58.json')
    backlogmd='# Registro de validaciones al corte CAP06R\n\nLos58 controles parten de D56. Las actualizaciones son documentales, salvo la sonda actual del guard descrita en el dossier. No se reejecutó todo el registro. Se mantienen los criterios de cierre y las incidencias sin nueva decisión.\n\n'
    for row in backlog:
        backlogmd+=f'## {row["id"]} {row["title"]}\n\nPrioridad {row["priority"]}. Área {row["area"]}. Estado documentado {row["status_at_documentation_cut"]}.\n\n{row["documentation_update_at_CAP06R"]}\n\nTrabajo pendiente: {row["remaining_work_current"]}\n\nCriterio de cierre: {row["closure_criterion"]}\n\n'
    backlogmd=clean_prose(backlogmd)
    (out/'VALIDACIONES.md').write_text(backlogmd,encoding='utf-8')
    (out/'validaciones.html').write_text(html_document('Registro de validaciones de datos',re.sub(r'^<h1>[\s\S]*?</h1>\s*','',md(backlogmd),count=1),'<a href="informe.html">Volver al dossier</a> · <a href="tables/validation_register_58.csv">CSV</a>'),encoding='utf-8')
    decisions=pd.read_parquet(out/'tables/decision_timeline.parquet')
    decisionbody='<p>Registros de decisión conservados al corte D61. Se separa revisión de aplicación en los informes enlazados del dossier. Los números de decisión organizan el registro; no se infiere un orden horario entre trabajos paralelos.</p>'+decisions[['decision','title']].to_html(index=False,border=0)
    decisionbody+='<p><a href="'+url('decisions')+'">Registro completo de decisiones</a></p>'
    (out/'decisiones.html').write_text(html_document('Decisiones sobre los datos y la preparación',decisionbody,'<a href="informe.html">Volver al dossier</a>',False),encoding='utf-8')
    sourcebody='<p>Registro de procedencia. Las filas pueden referirse al mismo archivo en funciones distintas. Los hashes describen el contenido consultado, no una aprobación de todas sus conclusiones. Los contextos mutables del proyecto se copiaron en evidence antes de actualizar documentación; su copia conserva el contenido del corte aunque el archivo vivo avance.</p><div class="tablewrap"><table><thead><tr><th>Referencia</th><th>Función</th><th>Archivo consultado</th><th>Copia del corte</th><th>SHA256 consultado</th></tr></thead><tbody>'
    for key,row in sources.items():
        snapshot=f'<a href="{quote(row["snapshot"],safe="/")}">Copia congelada</a>' if row.get('snapshot') else 'Archivo de origen'
        sourcebody+=f'<tr><td>{row["source_id"]}</td><td>{escape(key)}</td><td><a href="{url(key)}">{escape(row["workspace_relative_path"])}</a></td><td>{snapshot}</td><td><code>{row["sha256"]}</code></td></tr>'
    sourcebody+='</tbody></table></div>'
    (out/'fuentes.html').write_text(html_document('Fuentes y versiones de la documentación',sourcebody,'<a href="informe.html">Volver al dossier</a>',False),encoding='utf-8')
    c.dump(out/'render_metadata.json',{'document_title':'Documentación de los datos de la primera semana','cut_decision':'D61','version':'1.0',
        'main_sections':re.findall(r'^## (.+)$',doc,re.M),'dictionary_fields':len(dictionary),'validation_controls':len(backlog),
        'source_entries':len(sources),'unique_source_files':len({x['workspace_relative_path'] for x in sources.values()}),
        'real_browser_rendering_verified':False,'independent_validation':False})
    print(json.dumps({'report':str(out/'informe.html'),'sections':len(re.findall(r'^## ',doc,re.M)),'dictionary_fields':len(dictionary),'controls':len(backlog)},ensure_ascii=False))


if __name__=='__main__':main(Path(sys.argv[1]).resolve())
