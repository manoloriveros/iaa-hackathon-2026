"""Produce informe HTML y gráficos a partir de la evidencia, sin releer originales."""
from __future__ import annotations

import base64
import csv
import hashlib
import html
import json
import os
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "Preparación/.cache/parquet-reader"))
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter
import numpy as np
import pandas as pd

BASE = Path(__file__).parent
OUT = ROOT / json.loads((BASE / "current_run.json").read_text(encoding="utf-8"))["run"]
FIG = OUT / "graficos"
FIG.mkdir(exist_ok=True)
COLORS = ["#116b76", "#e48b41", "#6478a4"]
LABELS = {"motor": "Autos", "buildings": "Edificios", "contents": "Contenidos"}
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9,
                     "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titleweight": "bold", "axes.grid": True,
                     "grid.alpha": .15, "figure.facecolor": "white", "savefig.facecolor": "white"})


def fmt(value, digits=2):
    if value is None or (isinstance(value, float) and not np.isfinite(value)):
        return "sin dato"
    if isinstance(value, (int, np.integer)):
        return f"{value:,}".replace(",", ".")
    if isinstance(value, (float, np.floating)):
        return f"{value:,.{digits}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return str(value)


def esc(value):
    return html.escape(str(value))


def table(frame, limit=None):
    frame = frame.head(limit) if limit else frame
    return '<div class="scroll"><table><thead><tr>'+''.join('<th>'+esc(c)+'</th>' for c in frame.columns)+'</tr></thead><tbody>'+''.join('<tr>'+''.join('<td>'+esc(fmt(v))+'</td>' for v in row)+'</tr>' for row in frame.itertuples(index=False, name=None))+'</tbody></table></div>'


def picture(filename, caption):
    data = base64.b64encode((FIG / filename).read_bytes()).decode()
    return f'<figure><img loading="lazy" src="data:image/png;base64,{data}" alt="{esc(caption)}"><figcaption>{esc(caption)}</figcaption></figure>'


def finish(fig, name):
    fig.tight_layout(pad=1.5)
    fig.savefig(FIG / name, dpi=155, bbox_inches="tight")
    plt.close(fig)


def profile_plot(ax, profile, color=COLORS[0], label=None):
    if profile['name'].endswith('_id'):
        ax.barh(['distintos', 'faltantes'], [profile['unique'], profile['missing']], color=color)
        ax.set_xlabel('Registros / claves'); return
    if 'counts' in profile:
        counts = profile['counts'][:14]
        ax.barh([x['value'][:26] for x in counts][::-1], [x['n']/max(1,profile['rows'])*100 for x in counts][::-1], color=color, alpha=.75, label=label)
        ax.set_xlabel('% de filas; hasta 14 niveles mostrados')
    elif 'histogram' in profile:
        hist = profile['histogram']; edges = np.array(hist['edges']); counts=np.array(hist['counts'])
        ax.stairs(counts/max(1,counts.sum())*100, edges, color=color, label=label, linewidth=1.6)
        ax.set_xlabel('Valor, ventana p0,5–p99,5'); ax.set_ylabel('% en ventana')
    else:
        ax.text(.5,.5,'Sin distribución representable',ha='center',transform=ax.transAxes)


def variable_figure(col, physical, segments):
    if os.environ.get('IAA_REUSE_FIGURES') == '1' and (FIG/('variable_'+col+'.png')).exists():
        return 'variable_'+col+'.png'
    related = segments.loc[segments.feature == col]
    relevant = [line for line in LABELS if any(p['table'] in [f'policies_{line}', f'test_{line}'] for p in physical)]
    numcols = 3 if len(relevant)>1 or len(related.line.unique())>1 else 1
    numrows = 2 if len(related) else 1
    fig, axes = plt.subplots(numrows, numcols, figsize=(13 if numcols==3 else 7, 4*numrows), squeeze=False)
    for ax in axes.ravel(): ax.set_visible(False)
    if relevant:
        for i,line in enumerate(relevant):
            ax=axes[0,i]; ax.set_visible(True)
            for prefix,color,label in [('policies_',COLORS[0],'2021–2024'),('test_',COLORS[1],'2025')]:
                p=next((p for p in physical if p['table']==prefix+line),None)
                if p: profile_plot(ax,p,color,label)
            ax.set_title(LABELS[line]+' · distribución')
            if ax.get_legend_handles_labels()[0]: ax.legend(fontsize=8)
    else:
        ax=axes[0,0];ax.set_visible(True);profile_plot(ax,physical[0]);ax.set_title(physical[0]['table']+' · distribución')
    if len(related):
        for i,(line,g) in enumerate(related.groupby('line',sort=False)):
            if i>=numcols:break
            ax=axes[1,i];ax.set_visible(True)
            g=g.sort_values('exposure',ascending=False).head(12).sort_values('observed_cost_per_exposure')
            ax.barh(g.level.astype(str).str.slice(0,25),g.observed_cost_per_exposure,color=COLORS[0])
            ax.set_title(LABELS[line]+' · asociación bruta')
            ax.set_xlabel('Incurrido neto observado / año de exposición (CU)')
    fig.suptitle(col+' · distribución y experiencia observada',fontsize=13,y=1.01)
    name='variable_'+col+'.png';finish(fig,name);return name


def main():
    profiles=json.loads((OUT/'profiles.json').read_text(encoding='utf-8'))
    checks=pd.read_json(OUT/'checks.json')
    annual=pd.read_csv(OUT/'tables/annual_summary_date365.csv')
    segments=pd.read_csv(OUT/'tables/segments_date365.csv')
    shifts=pd.read_csv(OUT/'tables/train_test_shift.csv')
    claims=pd.read_parquet(OUT/'tables/claims_diagnostic.parquet')
    joins=pd.read_json(OUT/'claim_join_diagnostics.json')
    notes={r['column']:r for r in csv.DictReader((BASE/'column_notes.tsv').open(encoding='utf-8'),delimiter='\t')}
    columns={}
    for p in profiles:
        for c in p['columns']:
            columns.setdefault(c['name'],[]).append(dict(c,table=p['name'],rows=p['rows']))
    missing_notes=set(columns)-set(notes)
    if missing_notes: raise RuntimeError('Faltan interpretaciones: '+str(missing_notes))
    rows=sum(p['rows'] for p in profiles)
    overview=pd.DataFrame([{'Tabla':p['name'],'Filas':p['rows'],'Columnas':len(p['columns']),'Memoria MB':p['memory_mb']} for p in profiles])
    exposure_sensitivity=annual.groupby('line')[['recorded_exposure','exposure']].sum()
    exposure_sensitivity['raw_over_date_ratio']=exposure_sensitivity.recorded_exposure/exposure_sensitivity.exposure
    fig,ax=plt.subplots(figsize=(10,4))
    x=np.arange(len(exposure_sensitivity))
    ax.bar(x-.18,exposure_sensitivity.recorded_exposure,width=.36,color=COLORS[1],label='exposure tal como viene')
    ax.bar(x+.18,exposure_sensitivity.exposure,width=.36,color=COLORS[0],label='días inclusivos / 365')
    ax.set_xticks(x,[LABELS[i] for i in exposure_sensitivity.index]);ax.set_ylabel('Suma de exposición 2021–2024');ax.legend()
    ax.set_title('El denominador cambia materialmente las tasas');finish(fig,'exposicion_sensibilidad.png')
    capital=pd.read_csv(OUT/'tables/capital_scale_diagnostics.csv')
    fig,ax=plt.subplots(figsize=(11,4.8))
    for i,row in capital.iterrows():
        ax.plot([row['median'],row['p99'],row['max']],[i,i,i],color='#9bafb9')
        for key,marker,color in [('median','o',COLORS[0]),('p99','s',COLORS[2]),('max','X',COLORS[1])]:
            ax.scatter(row[key],i,marker=marker,color=color,s=65,label=key if i==0 else None)
    ax.set_xscale('log');ax.set_yticks(range(len(capital)),capital.table);ax.set_xlabel('Capital asegurado en CU · escala logarítmica');ax.legend()
    ax.set_title('La escala de los capitales requiere revisión');finish(fig,'capitales_escala.png')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for line,color in zip(LABELS,COLORS):
        a=annual[annual.line==line]
        axes[0].plot(a.year,a.exposure,marker='o',label=LABELS[line],color=color)
        axes[1].plot(a.year,a.reported_frequency,marker='o',label=LABELS[line],color=color)
        axes[2].plot(a.year,a.observed_cost_per_exposure,marker='o',label=LABELS[line],color=color)
    for ax in axes: ax.set_xticks([2021,2022,2023,2024]);ax.legend(fontsize=8);ax.set_xlabel('Año de cobertura')
    axes[0].set_title('Exposición');axes[0].set_ylabel('Años de cobertura')
    axes[1].set_title('Frecuencia reportada aceptada');axes[1].set_ylabel('Siniestros / año de exposición')
    axes[2].set_title('Coste observado, aún inmaduro');axes[2].set_ylabel('Incurrido neto / año de exposición (CU)')
    finish(fig,'cartera_y_experiencia.png')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for ax,(line,color) in zip(axes,zip(LABELS,COLORS)):
        c=claims[(claims.line==line)&(claims.status!='repudiated')]
        positive=c.observed_net_incurred[c.observed_net_incurred>0]
        ax.hist(np.log10(positive),bins=45,color=color,alpha=.9)
        ax.set_title(LABELS[line]);ax.set_xlabel('log10(incurrido neto positivo en CU)');ax.set_ylabel('Siniestros')
    finish(fig,'severidad_log.png')
    fig,axes=plt.subplots(1,2,figsize=(13,4))
    c=claims[claims.status!='repudiated'].copy()
    status=claims.groupby(['loss_year','status'],observed=True).size().unstack(fill_value=0)
    (status.div(status.sum(axis=1),axis=0)*100).plot.bar(stacked=True,ax=axes[0],color=[COLORS[0],COLORS[1],COLORS[2]])
    axes[0].set_ylabel('% de siniestros reportados');axes[0].set_xlabel('Año de ocurrencia');axes[0].set_title('Estado al 31/12/2024')
    for year,color in zip([2021,2022,2023,2024],['#116b76','#6478a4','#e48b41','#b35c64']):
        v=np.sort(c.loc[c.loss_year==year,'report_lag_days'].dropna())
        axes[1].plot(v,np.arange(1,len(v)+1)/len(v),label=str(year),color=color)
    axes[1].set_xlabel('Días entre ocurrencia y reporte');axes[1].set_ylabel('Fracción acumulada observada');axes[1].legend();axes[1].set_xlim(0,365)
    axes[1].set_title('Retraso de reporte, truncado por el corte')
    finish(fig,'madurez_y_reporte.png')
    missing=[]
    for p in profiles:
        for c in p['columns']:
            if c['missing']: missing.append({'table':p['name'],'column':c['name'],'pct':c['missing_pct']})
    miss=pd.DataFrame(missing).sort_values('pct',ascending=False)
    fig,ax=plt.subplots(figsize=(12,7))
    top=miss.head(28).iloc[::-1]
    ax.barh(top.table+' / '+top.column,top.pct,color=COLORS[0]);ax.set_xlabel('% faltante');ax.set_title('Campos con mayor proporción faltante · 28 combinaciones')
    finish(fig,'faltantes.png')
    fig,axes=plt.subplots(1,3,figsize=(14,4))
    for ax,line,color in zip(axes,LABELS,COLORS):
        q=claims[(claims.line==line)&(claims.status!='repudiated')].groupby('peril',observed=True).observed_net_incurred.sum().sort_values()
        ax.barh(q.index,q.values,color=color);ax.set_title(LABELS[line]);ax.set_xlabel('Incurrido neto reportado (CU)')
    finish(fig,'coste_por_peligro.png')
    spotlights=''
    cases=[('motor','driver_age','Edad del conductor'),('buildings','flood_zone','Zona de inundación'),
           ('contents','security_level','Seguridad en contenidos'),('motor','cover_type','Alcance de cobertura')]
    for line,feature,title in cases:
        g=segments[(segments.line==line)&(segments.feature==feature)].copy()
        def rank(level):
            try:return float(str(level).strip('(').split(',')[0])
            except ValueError:return float('inf')
        if feature in ['driver_age','flood_zone']:
            g=g.assign(order=g.level.map(rank)).sort_values('order')
        fig,axes=plt.subplots(1,3,figsize=(14,4.5))
        for ax,metric,label in zip(axes,['reported_frequency','observed_severity','observed_cost_per_exposure'],
                                  ['Siniestros / exposición','CU / siniestro reportado','CU / exposición']):
            ax.bar(np.arange(len(g)),g[metric],color=COLORS[0])
            ax.set_xticks(range(len(g)),g.level,rotation=60,ha='right',fontsize=8)
            ax.set_ylabel(label);ax.set_title(title)
        name='lectura_'+feature+'.png';finish(fig,name)
        spotlights+=picture(name,'Asociaciones brutas 2021–2024, con duración inclusiva / 365 como denominador de sensibilidad. Frecuencia × severidad = coste observado por exposición. Sin ajuste por otras variables; no son efectos causales ni factores aprobados.')
        spotlights+=table(g[['level','exposure','claims','reported_frequency','observed_severity','observed_cost_per_exposure']])
    spotlights+='<p>En autos, 17–24 años presenta aproximadamente 1.079 CU observadas por exposición frente a 362 en 51–59. La diferencia se observa principalmente en frecuencia, pero mezcla coberturas, vehículos y territorios; no es un recargo recomendado por edad. En edificios, la zona 5 muestra más frecuencia y más severidad que la zona 1; el grupo es mucho menor y no se ha ajustado capital ni región.</p><p>En contenidos, alarma con cerraduras presenta menor coste bruto que protección estándar. No hemos estimado el efecto causal de instalar una alarma. En autos, terceros puede mostrar menor frecuencia y mayor severidad que cobertura amplia: comparar solo coste medio total puede invertir la intuición sobre el alcance de cobertura por composición y tipo de reclamaciones.</p>'
    # Every numeric result below comes from the saved audit, never from a fabricated example.
    issues=checks[checks.affected>0].sort_values(['severity','affected'],ascending=[True,False])
    hard=issues[issues.severity=='error']
    checks.to_csv(OUT/'tables/validation_checks.csv',index=False)
    dict_rows=[];cards=[]
    for col,physical in columns.items():
        note=notes[col]
        for p in physical:
            dict_rows.append({'table':p['table'],'column':col,'meaning':note['meaning'],
                              'insurance_and_tariff':note['insurance_and_tariff'],'availability':note['availability'],
                              'proposed_treatment':note['proposed_treatment'],'missing_pct':p['missing_pct'],
                              'unique':p['unique'],'dtype':p['dtype']})
        name=variable_figure(col,physical,segments)
        stats=[]
        aliases=[]
        for p in physical:
            q=p.get('quantiles',{})
            stats.append({'Tabla':p['table'],'Tipo':p['dtype'],'Faltante %':p['missing_pct'],'Distintos':p['unique'],
                          'Mínimo':q.get('min',p.get('min','')),'Mediana':q.get('p50',''),'Media':p.get('mean',''),
                          'p99':q.get('p99',''),'Máximo':q.get('max',p.get('max',''))})
            if p.get('case_space_aliases'):
                aliases.append(p['table']+': '+json.dumps(p['case_space_aliases'],ensure_ascii=False))
        assoc=segments[segments.feature==col][['line','level','rows','exposure','claims','observed_cost_per_exposure','reported_frequency','observed_severity']]
        cells=table(pd.DataFrame(stats))
        if len(assoc): cells+='<details><summary>Ver denominadores y experiencia de todos los grupos</summary>'+table(assoc)+'</details>'
        if aliases: cells+='<p class="warning">Variantes de escritura detectadas: '+esc('; '.join(aliases))+'</p>'
        cards.append(f'<article class="column-card" data-search="{esc(col+" "+note["meaning"]+" "+" ".join(p["table"] for p in physical))}"><h3>{esc(col)}</h3><p>{esc(note["meaning"])}</p><p>{esc(note["insurance_and_tariff"])}</p><p class="timing">Disponibilidad: {esc(note["availability"])}</p><p>Tratamiento propuesto: {esc(note["proposed_treatment"])}</p><details><summary>Estadísticas y gráfico de {esc(col)}</summary>'+cells+picture(name,'Arriba: distribución original. Abajo: asociación bruta con incurrido neto reportado, excluidos rechazados, dividida por duración derivada de fechas / 365; hasta 12 grupos de mayor exposición. No son efectos causales ni factores de tarifa. Los histogramas muestran p0,5–p99,5; extremos y tablas completas permanecen disponibles.')+'</details></article>')
        if os.environ.get('IAA_REUSE_FIGURES') != '1': print('gráfico y ficha '+col,flush=True)
    pd.DataFrame(dict_rows).to_csv(OUT/'tables/dictionary_interpreted.csv',index=False)
    save_rows=[]
    for p in profiles:
        for c in p['columns']:
            save_rows.append({'table':p['name'],'column':c['name'],'missing':c['missing'],'missing_pct':c['missing_pct'],'unique':c['unique'],**c.get('quantiles',{})})
    pd.DataFrame(save_rows).to_csv(OUT/'tables/column_profile.csv',index=False)
    stats=annual.copy()
    stats.columns=['Ramo' if c=='line' else c for c in stats.columns]
    sources='<ol><li>Diccionario y enunciado oficiales de la competición IAA, archivados en Preparación/artifacts/verification/iaa_launch_20261016/pages; datos sintéticos originales identificados por input_hashes.json.</li><li><a href="https://www.casact.org/sites/default/files/2021-03/5_Werner_Modlin.pdf">Werner y Modlin, Basic Ratemaking, CAS, 5.ª edición, 2016</a>, capítulos 1, 4 y 6: exposición, frecuencia, severidad y distinción entre pérdidas, prima, gastos y resultado. Referencia educativa; no fija reglas de este concurso.</li><li><a href="https://scikit-learn.org/stable/auto_examples/linear_model/plot_tweedie_regression_insurance_claims.html">scikit-learn, ejemplo de regresión Tweedie para seguros</a>: sirve de referencia técnica para distinguir cantidad del periodo y coste por exposición; no se ha ajustado ese modelo aquí.</li><li>Papers IAA priorizados: Documentación §2; Consideraciones profesionales §§3.1–3.6; Gobernanza §2.8. Validación propia asistida por IA; revisión humana y comprobación independiente pendientes.</li></ol>'
    unmatched=json.loads((OUT/'unmatched_claims_diagnosis.json').read_text(encoding='utf-8'))
    customer_keys=json.loads((OUT/'customer_key_diagnosis.json').read_text(encoding='utf-8'))
    padding=json.loads((OUT/'customer_key_padding_check.json').read_text(encoding='utf-8'))
    worked=json.loads((OUT/'worked_policy_example.json').read_text(encoding='utf-8'))
    construction=pd.read_csv(OUT/'tables/construction_dictionary.csv')
    content=f'''<header><p class="eyebrow">IAA 2026 · Primera semana · Revisión propia asistida por IA</p><h1>Entender los datos antes de tarificar</h1><p class="lead">Once tablas, {fmt(rows)} filas en total y {len(columns)} nombres de columna distintos. Diccionario, calidad, cruces y experiencia descriptiva. Costes valorados al 31 de diciembre de 2024.</p><p>Este informe no entrena modelos, no produce una tarifa aprobada y no trata el incurrido observado como coste último. Los datos son sintéticos; los mecanismos descritos para cada variable son hipótesis profesionales que aún requieren comprobación.</p></header>
    <nav><a href="#modelo">Qué representa cada fila</a><a href="#calidad">Validación</a><a href="#experiencia">Experiencia y gráficos</a><a href="#tiempo">Tiempo y fuga</a><a href="#diccionario">Cada columna</a><a href="#acciones">Decisiones siguientes</a></nav>
    <section id="modelo"><h2>De tablas a una decisión de precio</h2><p>El cliente es la persona. La dirección describe un lugar. La póliza es el contrato. La fila es un intervalo concreto de cobertura; puede ser menor de un año. El siniestro es un evento reportado que debe asignarse al intervalo donde ocurrió. El clima tiene una fila por dirección y año. Estas unidades no son intercambiables.</p>{table(overview)}
    <div class="flow">customers ─customer_id→ periodos de póliza ←address_id─ addresses<br>weather ─address_id + año→ periodos de póliza<br>claims ─ramo + policy_id + loss_date dentro del periodo→ row_id<br>row_id + coste esperado de su periodo → prediction</div>
    <p>Los maestros se unen muchos-a-uno. Siniestros a pólizas es inicialmente muchos-a-muchos y requiere resolver fechas. No se suman costes después de un cruce ingenuo por policy_id. Unir weather solo por dirección multiplicaría las filas entre años.</p>{table(joins)}
    <p>El cruce dejó {sum(x['unmatched'] for x in unmatched)} siniestros sin periodo inclusivo compatible. Todos son anteriores al primer periodo observado de su póliza, no claves de póliza inexistentes. Pueden representar antecedentes fuera de la ventana disponible o un desfase que requiere aclaración. La proxy de las filas contiene solo los asignados sin ambigüedad; no se reparten los anteriores a una póliza cercana ni se imputan como costes del periodo actual.</p>
    <h3>Qué se quiere predecir</h3><p>La etiqueta final deseada es el coste último esperado de los siniestros ocurridos en el periodo, neto de franquicias y recuperaciones y excluyendo rechazados. No se pide predecir written_premium, ni afirmar que cada póliza sufrirá un siniestro.</p>
    <div class="formula">Frecuencia reportada = siniestros reportados aceptados / exposición<br>Severidad observada = incurrido neto reportado / siniestros aceptados<br>Coste observado por exposición = frecuencia reportada × severidad observada<br>Coste esperado del periodo ≈ exposición × tasa anual esperada</div>
    <p>La última igualdad supone una tasa pertinente al periodo; una cobertura parcial no tiene por qué abarcar una fracción uniforme de la estacionalidad. La igualdad frecuencia × severidad es una descomposición agregada con denominadores consistentes. No presupone que el coste observado ya esté a último.</p>
    <h3>La proxy que usamos para explorar, no la etiqueta definitiva</h3><p>Para cada siniestro aceptado se calcula incurred_to_date − recoveries; los rechazados aportan cero. Se asigna a un único row_id con fechas inclusivas y se suma. No se vuelve a restar franquicia. Paid_to_date − recoveries se conserva por separado, y incurred_to_date − paid_to_date describe la reserva de caso registrada. Los saldos negativos se señalan, no se recortan a escondidas.</p>
    <p>Una tarifa comercial añade decisiones sobre gastos, margen, financiación y otras condiciones. Esas piezas no forman parte de la predicción de siniestros solicitada. Por ello, written_premium, discount_applied y payment_method requieren distinguir riesgo técnico y decisiones comerciales.</p></section>
    <section><h2>Un periodo real del archivo y cómo entraría al cálculo</h2>{table(pd.DataFrame([worked]))}<p>La fila M00000001 cubre 141 días de 2021. Su duración derivada es 141/365, aproximadamente 0,3863 años. Si un modelo llegara a estimar una tasa anual de riesgo r(X) para sus condiciones, la predicción del periodo sería aproximadamente 0,3863 × r(X), con la salvedad de estacionalidad. No hemos asignado un valor inventado a r(X) ni ajustado un modelo.</p><p>driver_age describe al conductor; years_licensed su experiencia declarada; cover_type define los eventos cubiertos; las franquicias determinan qué parte del daño paga el asegurador. Cuando se construye la proxy con siniestros ya netos de franquicia, no se vuelven a deducir sus 0 CU voluntarias y 250 CU obligatorias.</p></section>
    <section id="calidad"><h2>¿Los datos tienen sentido?</h2><p>La respuesta tiene niveles: que un archivo se lea, que las claves y magnitudes sean coherentes, que las relaciones tengan sentido asegurador y que la información hubiera existido al decidir el precio. Pasar un nivel no garantiza el siguiente.</p>
    <h3>La exposición mezcla magnitudes y convenciones</h3><p>Se observan valores iguales a días y otros compatibles con ACT/360. ACT/365 es la convención predominante y coincide con todo el test dentro del redondeo comprobado. No todo valor ligeramente superior a uno es por sí solo un error: hay que distinguir base de conteo, año bisiesto y una cantidad de días almacenada como años. exposure_conventions.csv conserva esos contrastes, cuyos conteos pueden solaparse.</p>{picture('exposicion_sensibilidad.png','Comparación con una exposición derivada como (último día − primer día + 1) / 365. Escenario de sensibilidad explícito; no es una reparación aprobada por el organizador ni modifica los Parquet.')}{table(exposure_sensitivity.reset_index())}
    <p class="warning">Para que las asociaciones de este informe no hereden el denominador claramente distorsionado, los gráficos de frecuencia y coste por exposición usan días inclusivos / 365. Los CSV con la exposición registrada se conservan por separado. No cambian los importes ni el conteo de siniestros. Esto sigue siendo una hipótesis de trabajo pendiente de revisión humana, no una etiqueta final.</p>
    <h3>Capitales con saltos cercanos a mil veces</h3>{picture('capitales_escala.png','Mediana, p99 y máximo por tabla. La escala logarítmica deja ver los extremos que un histograma central ocultaría.')}{table(capital)}<p>En el histórico se detectan 1.002 filas de edificios y 1.065 de contenidos entre 900 y 1.100 veces la mediana de la misma póliza. El patrón sugiere mezcla de unidades o escala; no prueba qué valor debe sustituir al original. Los umbrales monetarios de cribado se muestran expresamente y no son límites contractuales.</p>
    <h3>Claves, fechas y vocabularios</h3><p>El cruce literal con customers falla en {fmt(customer_keys['missing_rows'])} filas históricas de autos. El maestro tiene claves únicas de ocho dígitos y las claves fallidas son más cortas. Rellenar ceros iniciales como texto hasta ocho posiciones recupera todos los cruces fallidos del histórico y del test, sin cambiar originales. Es una transformación candidata respaldada por consistencia con el maestro. Las asociaciones de atributos del cliente aquí conservan el cruce literal de la auditoría; los grupos faltantes incluyen este problema y no deben tratarse como segmentos de riesgo limpios.</p>{table(pd.DataFrame(padding['checks']))}<p>Las incidencias de siniestros se reinterpretan después del diagnóstico dirigido: todos los no asignados son anteriores al primer periodo observado. La severidad «error» de la criba inicial significa que no deben agregarse sin revisión, no que se haya probado una fecha inválida.</p>{table(pd.DataFrame([{k:v for k,v in x.items() if k!='examples'} for x in unmatched]))}{table(construction)}<p>En construcción, mayúsculas y separadores pueden normalizarse de forma explícita. Los códigos abreviados t y w no reciben automáticamente un significado: su correspondencia con las categorías del diccionario necesita confirmación.</p>
    <p>Se evaluaron {len(checks)} comprobaciones generales; {len(issues)} registran casos a revisar o cambios informativos. {len(hard)} comprobaciones con severidad «error» tienen casos afectados. Los diagnósticos dirigidos anteriores son adicionales. Las verificaciones sin incidencias también se conservan en validation_checks.csv. Los rangos amplios de cribado son criterios explícitos de esta revisión, no umbrales legales o de la IAA.</p>{table(issues[['table','rule','affected','denominator','fraction','severity','detail']])}{picture('faltantes.png','Faltantes por tabla y columna. La ausencia estructural de reparador, tercero o telemática no debe imputarse como un cero de riesgo. Solo se muestran las 28 proporciones mayores; todas están en el diccionario.')}
    <p>Las variantes de mayúsculas y separadores aparecen en las fichas. Se propone normalizarlas mediante un mapa explícito, pero no se modificó el original. Un outlier puede ser un error, una unidad distinta o un riesgo genuino; no se elimina sin estudiar contexto.</p></section>
    <section id="experiencia"><h2>Cartera, frecuencia, severidad y desarrollo</h2>{picture('cartera_y_experiencia.png','Años 2021–2024. Los numeradores usan reportados aceptados y costes valorados a una única fecha. Una bajada de 2024 puede reflejar inmadurez, truncamiento o mezcla, además de cambios de riesgo.')}{table(stats)}
    {picture('severidad_log.png','Distribución del incurrido neto positivo de siniestros aceptados, con eje log10. En ese eje 2 representa 100 CU y 3 representa 1.000 CU. Se excluyen de este gráfico los ceros y negativos, que sí permanecen en las estadísticas.')}
    {picture('coste_por_peligro.png','Suma observada por causa, no riesgo normalizado por cobertura específica. El mayor total puede deberse a más exposición o más contratos con esa cobertura, además de frecuencia y severidad.')}
    {picture('madurez_y_reporte.png','Abiertos, cerrados y rechazados al corte; retrasos de reporte observados. La distribución reciente está truncada: no incluye los siniestros aún desconocidos al 31/12/2024. No es una distribución completa de retrasos ni una estimación de IBNR.')}
    <p>No se puede identificar el IBNR completo ni el desarrollo último únicamente a partir de una foto de siniestros. Tampoco hay un triángulo de valoraciones sucesivas. El análisis puede orientar hipótesis y pruebas de sensibilidad; un factor de desarrollo elegido requiere documentar una base y su incertidumbre.</p><h3>Cómo leer el efecto aparente de una variable</h3>{spotlights}</section>
    <section id="tiempo"><h2>Qué se sabría al cotizar</h2><p>renewal_decision solo existe en entrenamiento y representa un resultado del periodo: se reserva para diagnóstico y se excluye de predictores. repairer_id, third_party_id, peril y los importes del siniestro futuro son resultados posteriores. Una historia de siniestros solo sería utilizable con un corte temporal correcto.</p><p>El clima anual realizado, customer_service_contacts, days_unoccupied, telematics_score y los maestros sin fecha de vigencia requieren aclaración. Estar presentes en el test del reto no demuestra disponibilidad profesional ex ante. Conviene distinguir un escenario con información provista por el benchmark y otro prospectivo basado en datos conocidos o previsiones documentadas.</p><p>La validación debe imitar el año futuro. Repetir una entidad no es automáticamente fuga: un renovado puede tener historia legítima, pero un split aleatorio puede dar una estimación optimista si no respeta el uso previsto. Clientes, pólizas y direcciones generan dependencias distintas. En un backtest histórico tampoco podemos asumir que las reservas valoradas en 2024 ya se conocían en 2021.</p><h3>Comparación del histórico con 2025</h3><p>Las diferencias siguientes se calculan entre filas, sin ponderación de exposición. El cambio estandarizado usa la desviación típica histórica; variación total compara proporciones categóricas. Son descriptores de composición, no una prueba de fallo ni una predicción del efecto en coste.</p>{table(shifts.reindex(shifts.standardized_mean_difference.abs().sort_values(ascending=False).index).head(25))}</section>
    <section id="diccionario"><h2>Interpretación de cada columna</h2><p>Las definiciones proceden del diccionario oficial. Las implicaciones de seguro y tratamientos son interpretaciones propuestas. Cada ficha reúne estadísticas de todas las tablas donde aparece el campo y un gráfico. Las asociaciones usan exposición y siniestros como denominadores, pero no ajustan confusión, selección, desarrollo o múltiples comparaciones. No son causalidad ni coeficientes de una tarifa.</p><label for="search">Buscar por columna, concepto o tabla</label><input id="search" type="search" placeholder="Por ejemplo: exposure, inundación, claims, franquicia"><p id="counter"></p><button id="expand">Abrir todas las estadísticas visibles</button>{''.join(cards)}</section>
    <section id="acciones"><h2>Qué usaríamos y qué falta comprobar</h2><p>Como base candidata de suscripción: cobertura y franquicias, exposición, características físicas de vehículo o inmueble, capital y atributos geográficos conocidos. Incluso estas variables necesitan integridad y fecha de referencia. Las variables comerciales y proxies personales se revisan por separado; no se justifican solo porque eleven una métrica.</p><h3>Cómo se combinarían, sin afirmar aún un modelo elegido</h3><p>Una formulación de frecuencia estima el número esperado de siniestros del periodo con la exposición como cantidad de riesgo; una formulación de severidad estima el coste condicionado a siniestro. Su combinación busca coste esperado. Otra formulación puede estimar directamente el coste por exposición. Estas son opciones conceptuales, no experimentos comparados en este informe. Un coeficiente de un modelo logarítmico se interpretaría manteniendo las demás variables del modelo fijas; un cociente entre dos barras de este EDA no hace ese ajuste.</p><p>Primero se fijaría una fecha de decisión y se construirían atributos conocidos a esa fecha. Los maestros se unirían con cardinalidad controlada; el clima sería conocido o pronosticado según el escenario; la historia interna usaría reportes anteriores y valoraciones que hubieran existido entonces. Con una sola foto de reservas al cierre de 2024 no puede afirmarse que un backtest de 2021 reproduzca toda la información financiera disponible en aquel momento.</p><p>Antes del modelo: resolver incidencias de dominio y cruces; acordar la información disponible en la fecha de decisión; definir objetivo observable, ajustes de desarrollo y supuestos de recuperación; diseñar validación temporal con dependencia; implementar Tweedie D² y comprobar el archivo final. Una reducción del coste medio entre categorías no es una recomendación de descuento hasta contrastar confusión, incertidumbre, estabilidad y pertinencia profesional.</p><p>El análisis de 2025 aquí se limita a predictores, exposición y formato. sample_submission contiene una plantilla, no etiquetas verdaderas. No se entrenó ni se envió un modelo.</p><h3>Fuentes y reproducción</h3>{sources}<p>Comando de cálculo desde la raíz: Preparación/.venv/Scripts/python.exe "Hackaton/Semana 1/Analisis/audit_data.py". El renderer usa current_run.json y no relee originales. run.json, input_hashes.json y las copias de scripts permiten identificar esta ejecución; las tablas CSV permiten revisar cada gráfico.</p></section>'''
    style='''body{margin:0;background:#f2f5f6;color:#243541;font-family:system-ui,Segoe UI,sans-serif;line-height:1.65}main{max-width:1160px;margin:auto;padding:28px}header,section{background:white;border:1px solid #dde5e8;border-radius:12px;padding:28px;margin-bottom:22px}h1{font-size:38px;line-height:1.15;color:#113b49}h2{font-size:27px;color:#155b69}h3{color:#234c5b}p{max-width:100ch}.eyebrow{font-size:13px;letter-spacing:.1em;text-transform:uppercase;color:#647884}.lead{font-size:20px}nav{display:flex;gap:12px;flex-wrap:wrap;margin:20px 0}nav a{padding:8px 12px;background:#e1edef;border-radius:6px;color:#155b69;text-decoration:none}figure{margin:22px 0}img{width:100%;height:auto;background:white}figcaption{color:#556976;font-size:13px}table{border-collapse:collapse;width:100%;font-size:13px}th,td{text-align:left;padding:9px 10px;border-bottom:1px solid #e4e9eb;vertical-align:top}th{background:#eaf1f3;position:sticky;top:0}tr:nth-child(even){background:#f8fafb}.scroll{overflow:auto;margin:18px 0;max-height:650px}.formula,.flow{background:#eef5f5;border-left:4px solid #17717a;padding:20px;font-family:ui-monospace,monospace;white-space:normal;overflow:auto}.column-card{border-top:2px solid #dce9ec;padding:12px 0 28px}.column-card h3{font-family:ui-monospace,monospace;font-size:22px}.timing{background:#f5f2e9;padding:12px}.warning{background:#fff0dd;padding:12px}summary{cursor:pointer;color:#116b76;font-weight:600;padding:10px 0}input{padding:13px;font-size:17px;width:95%;border:1px solid #8eafb5;border-radius:6px}button{background:#155b69;color:white;border:0;padding:10px 18px;border-radius:5px;cursor:pointer}a{color:#12687a}@media(max-width:650px){main{padding:8px}section,header{padding:16px}h1{font-size:29px}}'''
    script='''const s=document.getElementById('search');const cards=[...document.querySelectorAll('.column-card')];function filter(){let q=s.value.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');let n=0;for(const c of cards){let v=c.dataset.search.toLowerCase().normalize('NFD').replace(/[\\u0300-\\u036f]/g,'');c.hidden=!v.includes(q);if(!c.hidden)n++}document.getElementById('counter').textContent=n+' columnas visibles de '+cards.length}s.addEventListener('input',filter);filter();document.getElementById('expand').onclick=()=>cards.filter(c=>!c.hidden).forEach(c=>c.querySelector('details').open=true);'''
    (OUT/'informe.html').write_text('<!doctype html><html lang="es"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Validación actuarial de datos IAA 2026</title><style>'+style+'</style><main>'+content+'</main><script>'+script+'</script></html>',encoding='utf-8')
    shutil.copy2(__file__,OUT/'render_report.py');shutil.copy2(BASE/'column_notes.tsv',OUT/'column_notes.tsv')
    print(json.dumps({'report':str(OUT/'informe.html'),'unique_columns':len(columns),'physical_columns':len(dict_rows),'figures':len(list(FIG.glob('*.png')))},ensure_ascii=True))


if __name__=='__main__': main()
