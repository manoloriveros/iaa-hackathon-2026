"""Completa solo cuerpo/continuidad tras colisión del cuerpo v1; no recalcula plan."""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os
ROOT=Path(__file__).resolve().parents[3];REPO=ROOT/'Hackaton/Repositorio_IAA2026'
read=lambda p:json.loads(p.read_text(encoding='utf-8-sig'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rel=lambda p:p.relative_to(ROOT).as_posix()


def main():
    folder=ROOT/'Hackaton/Semana 2/Codex';plan=REPO/'registro/semana2_b20_contraccion2023_plan_v2.json';p=read(plan)
    assert all(sha(ROOT/x['path'])==x['sha256'] for x in p['frozen_sources'])
    body=folder/'contraccion_b20_2023_v2_preinscripcion.md'
    mode=('Se reutilizan términos logarítmicos concurrentes terminados, con SHA, y se cotejan en veinte filas.' if p['concurrent_source_ready_at_preregistration'] else 'La fuente concurrente no estaba materializada al registrar: se cotejan solo los veinte periodos con el diseño común y un predictor manual, sin repetir la atribución completa de 50.094 filas o los 31 grupos.')
    text=f'''Registro antes de calcular el diagnóstico `semana2_b20_contraccion2023_plan_v2.json`, que sustituye el borrador v1 sin cálculos ni comentario previo. La conciliación encontró la unidad concurrente S2-B20-ATRIBUCION2023-v1-20261024 y acotó este trabajo. {mode} La disponibilidad de fuente se fijó antes de calcular y no depende de resultados. Una colisión con el archivo del cuerpo v1 detuvo la preparación después de guardar el plan v2, sin cálculos; se conserva el cuerpo v1 y se completa este cuerpo v2 con el plan y fuentes intactos.

El núcleo nuevo compara los quince pares B20/B19: norma L2 estandarizada, excepciones individuales, efectos en escala original, rango entre folds y referencias comunes. La penalización de B20 afecta todos los coeficientes, con intercepto libre: menor norma conjunta no garantiza contracción individual o causalidad de cobertura. Se verifican medianas, medias/escalas, categorías/referencias, T0/C0 y folds. Cinco folds solapados no son CI independientes.

Los mismos doce componentes y veinte periodos de la traza terminada quedan fijados, sin nueva selección, grupos, pesos o retirada. Para esas veinte predicciones OOF existentes se coteja log(tasa20/tasa19) como intercepto, cobertura, nuevo negocio y otros efectos. Solo replay nativo focal y reconstrucción manual por otro método, sin precios con betas alteradas. Se examinan totales observados y nominales condicionales, distinguiendo intercepto de calibración agregada. Las desviaciones guardadas se suman en el subconjunto y se contrastan con la ganancia global neta ya existente, sin recalcular D² global, intervalos o bootstrap. Una fracción neta puede superar 100% por compensaciones y no es probabilidad.

El criterio previo conserva los resultados adversos, incluyendo coordenadas que crecen, grupos que empeoran o niveles que cambian. No se adopta normalización, alpha, enrutamiento, receta, promoción, retirada o lista final. Fsum/diccionarios y predictor manual cotejan coeficientes, términos y balances; guardas de año, claves, C0, objetivo y transformaciones y un comando real con C0 sintético incompatible deben fallar antes de modelos. No se repiten las suites 542/48 o la atribución global concurrente.

Solo artefactos de 2023, sin reentrenar o producir precios nuevos. B00 y todas las alternativas conservados. 2024/test, precios, predicciones, scores, SEL01, actas y ledger cerrados en este trabajo. Exposición previa de asunto externo declarada, sin usar cifras ni afirmar ceguera completa. Revisión propia, no profesional independiente. Sin remoto, envíos, nuevos chats, delegación o cambios a otras automatizaciones. Kaggle 752144 no cambió semánticamente en la consulta de este ciclo; no se duplica fuente, cotejo de test o envío.
'''
    with body.open('x',encoding='utf-8') as f:f.write(text)
    night=REPO/'registro/semana2_continuidad_nocturna.json';before=night.read_bytes();n=json.loads(before.decode('utf-8-sig'))
    prior=n.get('parallel_artifact_diagnostics',{}).get('S2-B20-CONTRACCION2023-v1-20261024')
    if prior is not None:n['parallel_artifact_diagnostics']['S2-B20-CONTRACCION2023-v1-20261024']=dict(prior,status='superseded_before_forum_or_calculation',replacement=p['id'])
    entry={'id':p['id'],'plan':rel(plan),'status':'preregistered_saved_artifacts_no_refit','forum_preregistration':p['forum_prior']}
    if n.get('current_unit') is None:n['current_unit']=entry;n['status']='B20_saved_contraction_level_diagnostic_in_progress'
    else:n.setdefault('parallel_artifact_diagnostics',{})[p['id']]=entry
    n['updated_utc']=datetime.now(timezone.utc).isoformat();tmp=night.with_name(night.name+'.contraccionb20completar.tmp')
    with tmp.open('x',encoding='utf-8') as f:json.dump(n,f,ensure_ascii=False,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    assert night.read_bytes()==before,'Concurrent continuity changed; preserve registeredplan/body and retry only continuity'
    os.replace(tmp,night)
    with (folder/'contraccion_b20_v2_preparation_receipt.json').open('x',encoding='utf-8') as f:json.dump({'utc':n['updated_utc'],'plan':rel(plan),'plan_sha256':sha(plan),'prior_collision':'Existing v1 preregistration body preserved; completed separate v2 body, no calculations or source/plan changes','source_mode':p['selected_decomposition_mode'],'actual_mode':'current_unit' if n.get('current_unit')==entry else 'parallel_artifact_diagnostic','new_fits':0},f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'plan':rel(plan),'sha256':sha(plan),'source_mode':p['selected_decomposition_mode'],'sources':len(p['frozen_sources'])}))


if __name__=='__main__':main()
