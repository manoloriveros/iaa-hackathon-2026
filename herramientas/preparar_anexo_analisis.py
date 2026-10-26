"""Figuras estáticas y anexo de datos, sin volver a leer datos por fila.

Usos: python herramientas/preparar_anexo_analisis.py figuras | pdf
Figuras: matplotlib. PDF: reportlab, pypdfium2 y pypdf.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
from xml.sax.saxutils import escape

REPO=Path(__file__).resolve().parents[1]
OUT=REPO/'docs/entrega/analisis'
ROOT=REPO.parents[1]
M={'developed':'Desarrollado','emerging':'Emergente'}
L={'motor':'Autos','buildings':'Edificios','contents':'Contenidos'}
COL={'developed':'#176b83','emerging':'#ba5428'}


def data():
    return json.loads((OUT/'datos_panel.json').read_text(encoding='utf-8'))


def f(v,n=0):
    return f'{v:,.{n}f}'.replace(',','@').replace('.',',').replace('@','.')


def agg(d,market,years=None,line=None):
    rows=[x for x in d['portfolio'] if x['market']==market and (years is None or x['year'] in years) and (line is None or x['line']==line)]
    return {k:sum(x[k] or 0 for x in rows) for k in ['rows','exposure','exposure_raw','T0_cents','accepted','positive','positive_periods','reserve_cents','known_customers','new_business','exposure_changed']}


def figures():
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    import numpy as np
    d=data();figdir=OUT/'figuras';figdir.mkdir(exist_ok=True)
    plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,
        'axes.spines.left':False,'axes.edgecolor':'#bacbd2','axes.labelcolor':'#163044','text.color':'#163044',
        'xtick.color':'#4d6373','ytick.color':'#4d6373','axes.titleweight':'bold','savefig.facecolor':'white','svg.fonttype':'none'})
    receipt=[]
    def save(fig,name):
        fig.tight_layout(pad=1.6)
        for ext in ['png','svg']:
            p=figdir/(name+'.'+ext)
            fig.savefig(p,dpi=190,bbox_inches='tight')
            if ext=='svg':
                p.write_text('\n'.join(line.rstrip() for line in p.read_text(encoding='utf-8').splitlines())+'\n',encoding='utf-8',newline='\n')
            receipt.append({'ruta':p.relative_to(REPO).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
        plt.close(fig)
    fig,axes=plt.subplots(1,2,figsize=(10.7,3.8))
    years=[2023,2024,2025];x=np.arange(3)
    for j,market in enumerate(M):
        counts=[agg(d,market,[y])['rows']/1000 for y in years]
        bars=axes[0].bar(x+(j-.5)*.35,counts,.35,color=COL[market],label=M[market])
        for bar in bars:axes[0].text(bar.get_x()+bar.get_width()/2,bar.get_height()+9,f(bar.get_height(),1),ha='center',fontsize=8)
        vals=[]
        for y in years:
            a=agg(d,market,[y]);vals.append(100*(1-a['known_customers']/a['rows']))
        # El primer año emergente carece de historia anterior observable.
        if market=='emerging':vals[0]=np.nan
        axes[1].plot(years,vals,marker='o',linewidth=2,color=COL[market],label=M[market])
        for y,v in zip(years,vals):
            if np.isfinite(v):axes[1].annotate(f(v,1)+' %',(y,v),xytext=(0,8 if market=='emerging' else -16),textcoords='offset points',ha='center',fontsize=9)
    axes[0].set_xticks(x,['2023','2024','2025\n(test)']);axes[0].set_ylabel('Miles de periodos');axes[0].set_ylim(0,820);axes[0].set_title('Volumen de cartera',loc='left');axes[0].legend(frameon=False,fontsize=9,loc='upper center',ncol=2)
    axes[1].set_xticks(years);axes[1].set_ylim(0,100);axes[1].set_ylabel('% de periodos');axes[1].set_title('Sin cliente observado en años anteriores',loc='left');axes[1].grid(axis='y',alpha=.18)
    save(fig,'cartera_y_clientes')
    fig,axes=plt.subplots(1,2,figsize=(10.7,3.7));x=np.arange(3)
    for j,market in enumerate(M):
        rates=[];freq=[]
        for line in L:
            a=agg(d,market,[2023,2024],line);rates.append(a['T0_cents']/100/a['exposure']);freq.append(100*a['accepted']/a['exposure'])
        for ax,vals in zip(axes,[rates,freq]):
            bars=ax.bar(x+(j-.5)*.35,vals,.35,label=M[market],color=COL[market])
            for b in bars:ax.annotate(f(b.get_height(),1),(b.get_x()+b.get_width()/2,b.get_height()),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
    for ax in axes:ax.set_xticks(x,list(L.values()));ax.grid(axis='y',alpha=.15);ax.set_axisbelow(True);ax.margins(y=.20)
    axes[0].set_title('T0 por exposición, 2023-2024',loc='left');axes[0].set_ylabel('CU por año de exposición');axes[0].legend(frameon=False,fontsize=9)
    axes[1].set_title('Frecuencia reportada, 2023-2024',loc='left');axes[1].set_ylabel('Aceptados por 100 años de exposición')
    save(fig,'coste_y_frecuencia')
    fig,axes=plt.subplots(1,2,figsize=(10.7,3.7));x=np.arange(2)
    for j,year in enumerate([2023,2024]):
        vals=[100*agg(d,m,[year])['reserve_cents']/agg(d,m,[year])['T0_cents'] for m in M]
        bars=axes[0].bar(x+(j-.5)*.35,vals,.35,color=['#176b83','#7ba5b4'][j],label=str(year))
        for b in bars:axes[0].annotate(f(b.get_height(),1)+' %',(b.get_x()+b.get_width()/2,b.get_height()),xytext=(0,4),textcoords='offset points',ha='center',fontsize=9)
    axes[0].set_xticks(x,list(M.values()));axes[0].set_ylim(0,30);axes[0].set_title('Reserva de caso / T0',loc='left');axes[0].set_ylabel('% del incurrido neto observado');axes[0].legend(frameon=False)
    before=[];after=[]
    for market in M:
        a=agg(d,market,[2021,2022,2023,2024]);before.append(a['exposure_raw']/a['exposure']);after.append(1)
    axes[1].bar(x-.17,before,.34,label='Original / conciliada',color='#ba5428');axes[1].bar(x+.17,after,.34,label='Conciliada / conciliada',color='#9bb8c1')
    for i,v in enumerate(before):axes[1].text(i-.17,v+.025,f(v,3),ha='center',fontsize=9)
    axes[1].set_xticks(x,list(M.values()));axes[1].set_ylim(0,1.65);axes[1].set_title('Distorsión del denominador histórico',loc='left');axes[1].set_ylabel('Cociente de exposición');axes[1].legend(frameon=False,fontsize=8)
    save(fig,'reservas_y_exposicion')
    (OUT/'figuras/manifest.json').write_text(json.dumps({'data_sha256':hashlib.sha256((OUT/'datos_panel.json').read_bytes()).hexdigest(),'files':receipt},indent=1)+'\n',encoding='utf-8')
    write_markdown(d)
    print(json.dumps({'figuras':len(receipt),'carpeta':str(figdir)}))


def write_markdown(d):
    lines=['# Datos de ambas semanas: análisis para el informe','',
        'Codex, 26 de octubre de 2026. Análisis descriptivo local, sin entrenamiento ni inferencia. Valoración de los siniestros: cierre de 2024. Los importes se expresan en CU ficticias.','',
        '## Comparación que puede incorporarse al cuerpo del informe','',
        'El mercado emergente reduce la historia de entrenamiento a 2023-2024 y cambia la composición de la cartera a predecir. En 2025, el 76,04 % de sus periodos pertenece a clientes sin registro anterior en el mismo ramo, frente al 15,19 % del mercado desarrollado. Este cambio limita la transferencia de un modelo validado principalmente sobre renovaciones. La exposición se reconstruyó con días inclusivos / 365; los objetivos observados de ambas semanas coinciden por fila con sus bases preparadas. Los costes de 2025 siguen sin etiqueta y el incurrido neto histórico no se presenta como coste último.','',
        '| Mercado | Periodos de entrenamiento | Exposición histórica (años) | T0 observado (millones CU) | Test 2025 |',
        '| --- | ---: | ---: | ---: | ---: |']
    for market in M:
        a=agg(d,market,[2021,2022,2023,2024]);t=agg(d,market,[2025])
        lines.append(f"| {M[market]} | {f(a['rows'])} | {f(a['exposure'],1)} | {f(a['T0_cents']/1e8,2)} | {f(t['rows'])} |")
    lines+=['','El entrenamiento desarrollado abarca 2021-2024; el emergente, 2023-2024. Los totales de esa tabla describen volúmenes de distinta duración, no una comparación directa de riesgo.','',
        '## Comparación en años comunes','',
        '| Mercado | Ramo | Exposición 2023-2024 | T0 / exposición (CU/año) | Aceptados por 100 años | Severidad positiva (CU) | Reserva / T0 |',
        '| --- | --- | ---: | ---: | ---: | ---: | ---: |']
    for market in M:
        for line in L:
            a=agg(d,market,[2023,2024],line)
            lines.append(f"| {M[market]} | {L[line]} | {f(a['exposure'],1)} | {f(a['T0_cents']/100/a['exposure'],2)} | {f(100*a['accepted']/a['exposure'],2)} | {f(a['T0_cents']/100/a['positive'],2)} | {f(100*a['reserve_cents']/a['T0_cents'],1)} % |")
    lines+=['','Frecuencia: siniestros aceptados reportados, incluidos los de coste cero. Severidad: coste total / número de siniestros de coste positivo. Para recuperar la identidad frecuencia × severidad debe usarse la frecuencia de positivos. Los porcentajes se obtienen de sumas, no de medias de tasas.','',
        '![Cartera y clientes](figuras/cartera_y_clientes.png)','',
        'La primera cohorte emergente no tiene historia anterior observable. Su falta de antecedentes no demuestra que todos sus clientes sean nuevos en el mercado. El gráfico omite ese porcentaje para no equiparar el inicio del archivo con adquisición comercial.','',
        '![Coste y frecuencia](figuras/coste_y_frecuencia.png)','',
        'Las diferencias de coste por exposición reúnen cobertura, composición y madurez. Las etiquetas proceden de una sola valoración y los reportes tardíos están truncados. No son estimaciones de un efecto causal ni tarifas últimas.','',
        '## Conciliación de siniestros y exposición','',
        '| Mercado | Originales | Copias excluidas | Anteriores a cobertura | Rechazados asignados | Aceptados asignados | Abiertos aceptados |',
        '| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for q in d['quality']:
        lines.append('| '+' | '.join([M[q['market']]]+[f(q[k]) for k in ['raw_claims','duplicate_copies','precoverage','repudiated_assigned','included','open']])+' |')
    lines+=['','Las exclusiones anteriores son disjuntas. En cada mercado, originales = copias + anteriores a cobertura + rechazados asignados + aceptados asignados. La condición anterior a cobertura describe la relación con el archivo disponible, sin afirmar su causa operativa.','',
        '![Reservas y exposición](figuras/reservas_y_exposicion.png)','',
        'La exposición original agregada supera la conciliada. Las tasas por exposición se calculan sobre la capa corregida. Los originales permanecen intactos. El cambio afecta 14.229 filas de entrenamiento desarrollado y 609 emergentes; el test de ambos mercados no cambia.','',
        '## Variables, faltantes y uso','',
        'El emergente sustituye edad exacta por bandas. Carece de kilometraje anual y variables de telemática de autos, y de fecha de nacimiento y banda crediticia del maestro de clientes; incorpora género. La existencia de género no acredita su conveniencia actuarial. Las columnas ausentes se separan de los nulos dentro de una columna. Los nulos de clientes y direcciones se ponderan por periodos enlazados, no por tamaño del maestro.','',
        'El clima se enlazó por dirección y año dentro de cada mercado, con cobertura comprobada en todas las cohortes. Sus nulos también se verificaron con conteos Arrow. Incluye 2025, pero su disponibilidad al inicio del periodo necesita un contrato temporal. No se usa para declarar una comparación retrospectiva prospectiva. El campo new_business es comercial y no equivale a ausencia de historia del cliente.','',
        'La semana 2 aporta veinte pólizas de referencia y ocho supuestos de gastos. La comisión emergente de comparison_site está vacía. El panel conserva el valor pendiente; no deduce una prima comercial desde T0 ni añade gastos a la predicción de coste último.','',
        '## Validación y trazabilidad','',
        'El productor verifica integridad de originales, claves, enlaces, orden del test, intervalos, estados y fechas. Reconstruye T0 en centavos y lo coteja por fila con los objetivos preparados de ambas semanas. La comprobación separada suma por escalares, vuelve al dinero original con Decimal y revisa la asignación mediante búsqueda binaria en intervalos. También recalcula los nulos desde sus fuentes. Las pruebas del navegador revisan filtros, exportación, tablas, diseño adaptable y ausencia de tráfico de red. Sus recuentos y recibos finales figuran en [VALIDACION_PANEL.md](VALIDACION_PANEL.md).','',
        'Las fuentes exactas, sus SHA-256 y el entorno están en [datos_panel.json](datos_panel.json). La carpeta privada del corte conserva las filas auditadas; el panel y este anexo solo incluyen agregados. Los datos se descargaron anteriormente: esta revisión no consulta reglas o puntuaciones en vivo.','',
        'La revisión es propia y asistida por IA. No equivale a validación profesional independiente. Los datos de 2024 ya se abrieron adaptativamente; este análisis no crea un nuevo conjunto confirmatorio ni modifica decisiones de modelos o entregas.','',
        'Las prácticas IAA priorizadas por el proyecto exigen propósito y límites claros (Consideraciones profesionales §3.1), ficha de datos (Documentación §2) y distinción de revisión propia e independiente (Gobernanza §2.8). Este anexo aporta evidencia para esos puntos sin certificar cumplimiento profesional.','',
        '## Integración en la entrega','',
        'El primer párrafo y la primera tabla son material para el cuerpo conjunto de cinco páginas. Este documento y el PDF son anexos de datos: no reemplazan el informe competitivo, ni afirman cubrir la selección final de la segunda semana. El panel anterior conserva el recorrido de S41 y enlaza este análisis de ambos mercados.','']
    (OUT/'ANALISIS_DOS_SEMANAS.md').write_text('\n'.join(lines),encoding='utf-8')
    first=lines.index('## Comparación en años comunes')
    (OUT/'TEXTO_PARA_INFORME.md').write_text('\n'.join(lines[:first]),encoding='utf-8')


def pdf():
    from reportlab.platypus import SimpleDocTemplate,Paragraph,Spacer,Table,TableStyle,Image,PageBreak
    from reportlab.lib import colors
    from reportlab.lib.styles import getSampleStyleSheet,ParagraphStyle
    from reportlab.lib.enums import TA_LEFT
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.units import mm
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    import pypdfium2 as pdfium
    from pypdf import PdfReader
    d=data();run=ROOT/d['private_run'];fonts=Path('C:/Windows/Fonts')
    pdfmetrics.registerFont(TTFont('Segoe',str(fonts/'segoeui.ttf')))
    pdfmetrics.registerFont(TTFont('SegoeBold',str(fonts/'segoeuib.ttf')))
    pdfmetrics.registerFontFamily('Segoe',normal='Segoe',bold='SegoeBold',italic='Segoe',boldItalic='SegoeBold')
    styles=getSampleStyleSheet()
    styles.add(ParagraphStyle(name='Text',fontName='Segoe',fontSize=10,leading=14,spaceAfter=8,textColor=colors.HexColor('#163044')))
    styles.add(ParagraphStyle(name='TitleA',fontName='SegoeBold',fontSize=23,leading=27,spaceAfter=11,textColor=colors.HexColor('#163044')))
    styles.add(ParagraphStyle(name='SubA',fontName='SegoeBold',fontSize=14,leading=18,spaceBefore=10,spaceAfter=7,textColor=colors.HexColor('#176b83')))
    styles.add(ParagraphStyle(name='SmallA',fontName='Segoe',fontSize=8.3,leading=11,spaceAfter=7,textColor=colors.HexColor('#4d6373')))
    styles.add(ParagraphStyle(name='CellA',fontName='Segoe',fontSize=8.1,leading=10.8,textColor=colors.HexColor('#163044')))
    story=[];width=A4[0]-36*mm
    def para(text,kind='Text'):return Paragraph(escape(text),styles[kind])
    def add(text,kind='Text'):story.append(para(text,kind))
    def table(headers,rows,widths=None):
        vals=[[para(str(x),'CellA') for x in row] for row in [headers]+rows]
        t=Table(vals,colWidths=widths or [width/len(headers)]*len(headers),repeatRows=1,hAlign='LEFT')
        t.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf3f5')),('VALIGN',(0,0),(-1,-1),'TOP'),('LINEBELOW',(0,0),(-1,-1),.4,colors.HexColor('#d9e2e5')),('LEFTPADDING',(0,0),(-1,-1),6),('RIGHTPADDING',(0,0),(-1,-1),6),('TOPPADDING',(0,0),(-1,-1),6),('BOTTOMPADDING',(0,0),(-1,-1),6)]))
        story.extend([t,Spacer(1,8)])
    def image(name):
        from PIL import Image as PILImage
        p=OUT/'figuras'/(name+'.png');im=PILImage.open(p);w,h=im.size
        story.append(Image(str(p),width=width,height=width*h/w));story.append(Spacer(1,4))
    add('IAA 2026 | Anexo de análisis de datos','SmallA')
    add('Dos semanas, dos mercados','TitleA')
    add('Corte del 26 de octubre de 2026. Codex. Análisis descriptivo desde originales, sin ajustar modelos ni consultar puntuaciones. Los siniestros están valorados al cierre de 2024.')
    table(['Mercado / historia','Periodos históricos','Exposición (años)','T0 (M CU)','Test 2025'],[[M[m]+(' / 2021-24' if m=='developed' else ' / 2023-24'),f(agg(d,m,[2021,2022,2023,2024])['rows']),f(agg(d,m,[2021,2022,2023,2024])['exposure'],1),f(agg(d,m,[2021,2022,2023,2024])['T0_cents']/1e8,2),f(agg(d,m,[2025])['rows'])] for m in M],[width*.23,width*.21,width*.21,width*.15,width*.20])
    add('El volumen histórico tiene distinta duración. Para contrastar tasas entre mercados se usan solo 2023 y 2024; 2025 aporta covariables y exposición, sin etiquetas de coste.')
    image('cartera_y_clientes')
    add('Figura 1. Volumen y clientes sin registro anterior en su ramo. Se omite el primer año emergente del segundo gráfico porque no hay historia anterior observable. El indicador no equivale al campo comercial new_business.','SmallA')
    add('La composición del test cambia','SubA')
    add('En el emergente, el 76,04 % de los periodos de 2025 no tiene un cliente observado previamente en su ramo, frente al 15,19 % desarrollado. En 2024 emergente era 15,31 %. Una validación dominada por renovaciones necesita una lectura separada para clientes sin historia.')
    add('CU es una unidad monetaria ficticia. Los costes mostrados son T0 observado; faltan siniestros aún no reportados y las reservas no tienen una observación posterior que demuestre su suficiencia.','SmallA')
    story.append(PageBreak())
    add('Comparación con denominadores comunes','TitleA')
    add('La tasa observada divide la suma de T0 por exposición conciliada. La frecuencia cuenta siniestros aceptados reportados. La combinación de edades de cartera, coberturas y madurez impide interpretar una diferencia como efecto puro del mercado.')
    image('coste_y_frecuencia')
    add('Figura 2. Años comunes 2023-2024. Frecuencia por 100 años de exposición; coste en CU por año. Ambos mercados se observan al mismo cierre de 2024, con truncamiento de reporte.','SmallA')
    rows=[]
    for m in M:
        for l in L:
            a=agg(d,m,[2023,2024],l)
            rows.append([M[m],L[l],f(a['exposure'],1),f(a['T0_cents']/100/a['exposure'],2),f(100*a['accepted']/a['exposure'],2),f(a['T0_cents']/100/a['positive'],2)])
    table(['Mercado','Ramo','Exposición','CU / año','Aceptados / 100 años','Severidad positiva CU'],rows,[width*.18,width*.15,width*.18,width*.15,width*.17,width*.17])
    add('Frecuencia y severidad usan conteos distintos cuando hay un aceptado de coste cero. La identidad coste / exposición = frecuencia positiva × severidad positiva se verifica con el conteo de costes positivos. Hay un siniestro aceptado de coste cero en el desarrollado y ninguno en el emergente.')
    add('Variables que condicionan la transferencia','SubA')
    add('El emergente presenta edad por bandas y omite kilometraje anual, telemática de autos, fecha de nacimiento y banda crediticia de clientes. Incorpora género; su disponibilidad no demuestra conveniencia actuarial. El panel separa columnas ausentes de nulos y permite revisar su proporción por año y ramo.')
    add('Los atributos de clientes, direcciones y clima se ponderan por periodos enlazados. El clima se cruza por dirección y año, con cobertura comprobada en todas las cohortes. Contiene 2025, cuya disponibilidad al cotizar sigue siendo una limitación temporal.')
    story.append(PageBreak())
    add('Conciliación y madurez del coste','TitleA')
    add('Cada siniestro se enlaza dentro de su mercado por ramo, póliza y fecha de ocurrencia. Las exclusiones son disjuntas y permanecen auditadas; no se trasladan siniestros de un mercado a otro.')
    table(['Mercado','Originales','Copias','Anteriores a cobertura','Rechazados asignados','Aceptados asignados'],[[M[q['market']]]+[f(q[k]) for k in ['raw_claims','duplicate_copies','precoverage','repudiated_assigned','included']] for q in d['quality']],[width*.20,width*.15,width*.12,width*.18,width*.18,width*.17])
    add('Originales = copias + anteriores a cobertura + rechazados asignados + aceptados asignados. T0 = incurrido - recuperaciones. Reserva = incurrido - pagos. No se descuenta otra vez la franquicia. La causa de las ocurrencias anteriores a cobertura no puede establecerse solo con estos archivos.','SmallA')
    image('reservas_y_exposicion')
    add('Figura 3. La reserva de caso mide una parte del coste ya reportado, sin certificar suficiencia. El denominador original de exposición exagera la cobertura histórica, especialmente en el emergente.','SmallA')
    add('La exposición se calcula con días inclusivos / 365 y cuatro decimales, sin imponer un tope automático de uno. Cambian 14.229 filas históricas desarrolladas y 609 emergentes. Los test no cambian. Las tasas usan exposición conciliada y los originales se conservan intactos.')
    add('Reporte y reservas requieren cautela','SubA')
    add('Hay 10.120 siniestros aceptados abiertos asignados en el desarrollado y 1.055 en el emergente. Sus pagos y reservas proceden de una sola valoración. Los retrasos del panel son descriptivos de reportados al corte: sus medianas y percentiles no miden la completitud de lo aún no reportado.')
    add('No se ajusta un modelo de IBNR, ni se aplica un factor de último a estos agregados. Los resultados de modelos ya existentes conservan sus propios supuestos y recibos.')
    story.append(PageBreak())
    add('Qué se comprobó y cómo usarlo','TitleA')
    add('El productor coteja los originales con sus manifiestos SHA-256, incluyendo la copia desarrollada entregada como referencia en la segunda semana. T0 coincide por fila, en centavos, con los objetivos preparados de ambos mercados. La exposición coincide con sus capas existentes.')
    add('La comprobación separada usa sumas escalares, dinero Decimal desde los originales y búsqueda binaria en intervalos, frente al join relacional del productor. Recalcula nulos de pólizas y de maestros enlazados. El navegador comprueba combinaciones de filtros, tablas, exportación sin etiquetas inventadas, anchos de pantalla y ausencia de tráfico de red.')
    add('Los recuentos finales, los intentos fallidos y sus correcciones se conservan en VALIDACION_PANEL.md y en el recibo privado. El panel enlaza esas fuentes. Esta revisión es propia y asistida por IA; no se acredita validación profesional independiente.')
    add('Texto breve para el cuerpo conjunto','SubA')
    add('El mercado emergente reduce la historia a 2023-2024 y cambia la composición del test: el 76,04 % de los periodos de 2025 pertenece a clientes sin registro anterior en su ramo, frente al 15,19 % desarrollado. Reconstruimos exposición y objetivo desde los originales y cotejamos cada etiqueta histórica con las bases preparadas. La comparación descriptiva usa años comunes y declara la falta de coste último observado; los resultados de 2025 permanecen sin etiqueta.')
    add('Este anexo acompaña al informe. El primer párrafo y su tabla están en TEXTO_PARA_INFORME.md para incorporarlos al cuerpo conjunto de cinco páginas. No sustituye la selección final de modelos ni la sección de prima comercial de la semana 2.')
    add('Prima comercial y límites pendientes','SubA')
    add('La segunda semana aporta veinte pólizas de referencia y ocho supuestos de gastos. La comisión emergente de comparison_site está vacía. No se convierte T0 en tarifa comercial ni se añaden gastos a la predicción de coste último. Esa conversión requiere la receta de prima de riesgo elegida y resolver los supuestos pendientes.')
    add('2024 ya se consultó de forma adaptativa. Este análisis no crea un nuevo conjunto confirmatorio, no modifica modelos ni selecciona envíos. Las prácticas IAA priorizadas son propósito y límites (Consideraciones profesionales §3.1), ficha de datos (Documentación §2) y distinción de revisión propia e independiente (Gobernanza §2.8).')
    add('Archivos de evidencia','SubA')
    for text in ['panel_analisis.html: filtros, tablas, datos embebidos y descarga de agregados.',
                 'analisis/datos_panel.json: cifras exactas, rutas, SHA-256 y entorno.',
                 'analisis/ANALISIS_DOS_SEMANAS.md: anexo editable y tablas completas.',
                 'analisis/VALIDACION_PANEL.md: acta de controles y límites.',
                 'registro/panel_analisis_actual.json: índice del corte privado con filas auditadas.']:
        add(text,'SmallA')
    add('Las figuras PNG y SVG se conservan en analisis/figuras. No hay datos por fila en los entregables. Uso local; sin publicación o redistribución autorizada.','SmallA')
    destination=OUT/'anexo_datos_dos_semanas.pdf'
    def footer(canvas,doc):
        canvas.setFont('Segoe',8);canvas.setFillColor(colors.HexColor('#4d6373'))
        canvas.drawString(18*mm,12*mm,'IAA 2026 | Datos de ambas semanas | Revisión propia asistida por IA')
        canvas.drawRightString(A4[0]-18*mm,12*mm,str(doc.page))
    SimpleDocTemplate(str(destination),pagesize=A4,leftMargin=18*mm,rightMargin=18*mm,topMargin=17*mm,bottomMargin=21*mm,
        title='IAA 2026 - Datos de ambas semanas',author='Codex, para Manuel Rodríguez').build(story,onFirstPage=footer,onLaterPages=footer)
    reader=PdfReader(destination);assert len(reader.pages)==4,f'El anexo debe tener cuatro páginas; tiene {len(reader.pages)}'
    preview=run/'pdf';preview.mkdir(exist_ok=True)
    pdfdoc=pdfium.PdfDocument(str(destination))
    for i in range(len(pdfdoc)):
        page=pdfdoc[i];bitmap=page.render(scale=1.45);bitmap.to_pil().save(preview/f'pagina_{i+1}.png');bitmap.close();page.close()
    # Revisa geometría textual extraída; la revisión visual sigue siendo necesaria.
    import pdfplumber
    boxes=[]
    with pdfplumber.open(destination) as doc:
        for i,page in enumerate(doc.pages):
            words=page.extract_words();bad=[w for w in words if w['x0']<0 or w['x1']>page.width+.5 or w['top']<0 or w['bottom']>page.height]
            assert not bad, f'Texto fuera de página {i+1}'
            boxes.append({'pagina':i+1,'palabras':len(words),'fuera_de_pagina':len(bad)})
    receipt={'paginas':len(reader.pages),'sha256':hashlib.sha256(destination.read_bytes()).hexdigest(),'texto':boxes,'rasterizado':True,'revision_visual':'pendiente'}
    (run/'pdf/recibo.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=1)+'\n',encoding='utf-8')
    print(json.dumps(receipt,ensure_ascii=False))


if __name__=='__main__':
    ap=argparse.ArgumentParser(description=__doc__);ap.add_argument('modo',choices=['figuras','pdf'])
    mode=ap.parse_args().modo
    figures() if mode=='figuras' else pdf()
