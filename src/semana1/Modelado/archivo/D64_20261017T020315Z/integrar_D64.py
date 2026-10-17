"""Integración documental D64; no lee datos de concurso ni ajusta modelos."""
import hashlib
import json
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

MODEL = Path(__file__).resolve().parent.parent
ROOT = MODEL.parents[2]
PREP = ROOT / "Preparación"
REF = MODEL / "Referencias_publicas"
stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
CLOSE = MODEL / "archivo" / ("D64_" + stamp)
CLOSE.mkdir()
files = [MODEL / "experimentos.json", MODEL / "protocolo_metodologico.json", MODEL / "METODOLOGIA_ACTUARIAL.md", MODEL / "README.md", PREP / "MEMORIA_PROYECTO.md", PREP / "ESTADO_PROYECTO.json", PREP / "DECISIONES.md"]
for path in files:
    dest = CLOSE / "before" / path.relative_to(ROOT)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(path, dest)

capture = Path("C:/Users/manol/AppData/Local/Temp/codex-clipboard-28188f87-9817-49c9-8cf5-40feba98f178.png")
shutil.copy2(capture, REF / "captura.png")
source = {
    "received_on": "2026-10-16", "timezone": "America/Bogota",
    "captured_at": None, "source": "user_attached_image", "live_leaderboard_verified": False,
    "competition_association": "Part 1 inferred from project context; title and URL absent from image",
    "image": "captura.png", "image_sha256": hashlib.sha256(capture.read_bytes()).hexdigest(),
    "rows": [
        {"name": "RiskForge", "rank_displayed": 1, "score_displayed": "0.11416", "entries_displayed": 3, "last_displayed": "3h"},
        {"name": "sandbox_2_basic_glm.csv", "rank_displayed": None, "score_displayed": "0.10563", "entries_displayed": 1, "last_displayed": "2d"},
        {"name": "sample_submission.csv", "rank_displayed": None, "score_displayed": "0.07169", "entries_displayed": 1, "last_displayed": "2d"},
        {"name": "sandbox_1_average_cost_baseline.csv", "rank_displayed": None, "score_displayed": "0.07169", "entries_displayed": 1, "last_displayed": "2d"},
    ],
}

def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

write_json(REF / "captura.json", source)
subprocess.run([sys.executable, str(REF / "calcular.py")], check=True, capture_output=True, text=True)

# Contratos de salida propuestos, no afirmaciones sobre implementaciones de autores.
contracts = {
    "M00": ("m=e*q_r", "Comparar q_r=sum(Y)/sum(e) y q_r=sum(Y/sqrt(e))/sum(sqrt(e)); ajustar por ramo en train."),
    "M01": ("m=e*exp(beta0+x*beta)", "GLM con enlace log; minimizar desviación Tweedie de importes; p_fit=1.5 de referencia y p_fit=1.9 como sensibilidad D50."),
    "M02": ("m=e*exp(beta0+sum_j f_j(x_j))", "GAM: curvas y penalización dentro de train; interacciones solo como variante identificada."),
    "M03": ("m=e*lambda(x)*s(x)", "Poisson para conteo de costes positivos con offset log(e); gamma-log para severidad positiva por siniestro. Si se agregan medias por periodo, ponderar severidad por el conteo positivo."),
    "M04": ("m=e*exp(f_arboles(x))", "Boosting Tweedie: verificar base margin/offset o ajustar tasa Y/e con peso e**(2-p_fit). No multiplicar exposición dos veces."),
    "M05": ("m=e*exp(f_arboles(x))", "Boosting Tweedie: mismo contrato de importe y exposición; verificar soporte del offset en la versión elegida."),
    "M06": ("m=e*exp(f_arboles(x))", "Boosting Tweedie: usar tasa Y/e y peso e**(2-p_fit) si no hay offset; revertir cualquier reescala de CU antes de evaluar."),
    "M07": ("m=e*lambda_cat(x)*s_cat(x)", "Frecuencia de coste positivo y severidad positiva separadas; verificar objetivo gamma o likelihood válida. Tweedie con p=2 no es gamma admisible en CatBoost."),
    "M08": ("m=e*E[exp(eta(x)+u_grupo) dado historia disponible]", "Especificar distribución, varianza y posterior del efecto; integrar en la escala de coste. Grupos nuevos usan distribución predictiva, sin etiquetas futuras."),
    "M09": ("m=m_base*exp(g(x))", "Refinamiento multiplicativo con log(m_base) como offset; minimizar pérdida sobre Y, sin log(Y) ni regresión Tweedie sobre residuos negativos. Folds internos para selección."),
    "M10": ("m=m_GLM*exp(g_red(x))", "CANN con salida positiva; pérdida de importe Tweedie y exposición ya incluida en m_GLM. Comparar contra base sin corrección."),
    "M11": ("m=e*exp(f_red(x))", "MLP/FT-Transformer: mismo objetivo y contrato F0 que árboles; regularización y parada dentro del desarrollo."),
    "M12": ("m=e*exp(beta0+sum_j beta_j(x)*x_j)", "LocalGLMnet: coeficientes dependientes de x; centrar/identificar efectos y revisar estabilidad sin atribuir causalidad."),
    "M13": ("m=e*lambda_transformer(x)*s(x), o salida Tweedie positiva adaptada", "LocalGLMftt/CAFTT: escoger adaptación explícita antes de implementar. No atribuir coste agregado a un experimento original de frecuencia."),
    "M14": ("m=E[N_periodo dado historia]*s(x,historia)", "CANN longitudinal Poisson/NB/MVNB para conteos; duración incorporada en E[N]. Severidad positiva y contracción histórica se validan por separado."),
    "M15": ("m=integral_0_infinito (1-F_refinada(t dado x)) dt", "DRN: extraer esperanza finita en CU del periodo, con masa cero y cola explícitas; no sustituirla por mediana o cuantiles."),
    "M16": ("m=sum_k alpha_k*m_k, alpha_k>=0, sum_k alpha_k=1", "Primero mezcla convexa de importes compatibles; pesos y stacking con predicciones fuera de muestra y evaluación externa. Stacking posterior exige salida positiva."),
    "M17": ("m=e*exp(f_TabM(x))", "Propuesta de adaptación Tweedie; salida y pérdida verificadas antes de piloto. Si es frecuencia-severidad, conservar contrato M03."),
    "M18": ("m=e*exp(beta0+sum_j f_j_red(x_j))", "ANAM: especificar efectos, suavidad, restricciones e interacciones antes de medir; propuesta de coste por periodo."),
    "M19": ("m=e*exp(f_transformer(x,contexto_admisible))", "Propuesta de coste: definir tokens, contexto y contracción; no incluir etiquetas de evaluación ni memoria con información futura."),
    "M20": ("m=e*lambda(x)*E[S_positivo dado x]", "TabPFN solo en severidad inicialmente; extraer media en CU. exp(E[log(S)]) no equivale a E[S]; revisar retransfomación, versión, licencia y pesos."),
    "M21": ("m=(1-pi(x))*e*q_Tweedie(x)", "Mezcla cero adicional/Tweedie: pi es masa estructural adicional y q es media del componente Tweedie. Exigir evidencia de ceros extra; D50 no la encontró en conteos."),
}
catalog = json.loads((MODEL / "experimentos.json").read_text(encoding="utf-8"))
catalog["updated_on"] = "2026-10-16"
catalog["calculation_contract_decision"] = "D64"
catalog["public_reference"] = {"source": "Referencias_publicas/captura.json", "table": "Referencias_publicas/TABLA_Y_CALCULOS.md", "own_results": False, "live_verified": False, "selection_threshold": None, "changes_candidate_priority": False}
catalog["metric"]["fit_power_vs_evaluation_power"] = "p_fit may vary by declared experiment; evaluate every candidate with p_eval=1.5"
catalog["required_before_training"].append("exclude_customer_service_contacts_in_real_feature_guard_and_verify_D50_gap")
for candidate in catalog["candidates"]:
    prediction, fit = contracts[candidate["id"]]
    candidate["calculation_contract"] = {"status": "proposed_not_implemented_or_fitted", "period_prediction": prediction, "fit_and_controls": fit, "evaluation_power": 1.5, "rate_weight_if_equivalent_tweedie_fit": "exposure**(2-p_fit)", "local_D2": None, "public_D2": None}
write_json(MODEL / "experimentos.json", catalog)
lines = ["# Catálogo de modelos y cálculos propuestos", "", "Actualización D64, 16 de octubre de 2026. Los 22 candidatos conservan sus IDs, olas, dependencias y estado sin ejecutar. Esta tabla desarrolla el contrato de cálculo de [experimentos.json](experimentos.json); no acredita implementaciones, entrenamiento o resultados propios.", "", "`Y` es T0 (o el escenario declarado), `e` la exposición positiva, `m` el coste esperado del periodo, `lambda` la frecuencia anual de costes positivos y `s` la esperanza de severidad positiva por siniestro. Modelos por ramo salvo variante conjunta declarada. Los contratos neuronales son adaptaciones propuestas del proyecto, sujetas a sus condiciones bibliográficas e implementación. Todas las filas se evalúan sobre importes con potencia 1,5.", "", "| ID | Familia | Ola | Cálculo de coste del periodo propuesto | Ajuste y controles |", "| --- | --- | ---: | --- | --- |"]
for c in catalog["candidates"]:
    prediction, fit = contracts[c["id"]]
    lines.append(f'| {c["id"]} | {c["family"]} | {c["wave"]} | `{prediction}` | {fit} |')
lines.extend(["", "Los resultados local y público de cada candidato siguen sin medir (`null`). Las puntuaciones de [la captura](Referencias_publicas/TABLA_Y_CALCULOS.md) se registran aparte: RiskForge 0,11416; GLM visible 0,10563; plantilla y referencia de coste medio 0,07169. No se equiparan M00/M01 con esos archivos: sus cálculos no se han verificado. La captura no permite cambiar el orden de pruebas ni estimar la mejora de nuestros candidatos.", "", "M00 compara dos tasas constantes distintas. M01–M06 forman la primera ola vigente (M00/M01/M04/M05/M06); el resto mantiene sus condiciones y dependencias. La sensibilidad de potencia de ajuste 1,9 procede de D50, no del leaderboard. A esa potencia, los pesos de tasas equivalentes a importes son `e**0.1`; con 1,5 son `sqrt(e)`. Usar `e` sigue siendo otra sensibilidad actuarial.", "", "Frecuencia-severidad exige una definición consistente: conteo de costes positivos y severidad por siniestro positivo. La fórmula multiplicativa debe representar la misma esperanza agregada; la independencia condicional no se da por probada. Una media por periodo debe ponderarse por su conteo al ajustar severidad; una media por siniestro usa una fila por siniestro. Comparar sobre las mismas filas de evaluación y siniestros admitidos.", "", "Antes de entrenar siguen pendientes T0/F0, splits, métrica/runner multitabla y cierre de la brecha del guard de `customer_service_contacts` identificada en D50/D56. Ver [metodología](METODOLOGIA_ACTUARIAL.md), [protocolo](protocolo_metodologico.json) y fuentes D37/D50. Este catálogo no instala librerías, descarga pesos ni autoriza ejecución remota.", ""])
(MODEL / "CATALOGO_MODELOS.md").write_text("\n".join(lines), encoding="utf-8")

protocol = json.loads((MODEL / "protocolo_metodologico.json").read_text(encoding="utf-8"))
protocol["version"] = "1.11"
protocol["calculation_contract_decision"] = "D64"
protocol["candidate_calculation_table"] = "CATALOGO_MODELOS.md"
protocol["metric"]["fit_power"] = {"reference": 1.5, "sensitivity_D50": 1.9, "evaluation_power_always": 1.5, "rate_equivalent_loss_weight": "exposure**(2-p_fit)"}
protocol["metric"]["public_score_comparison"] = {"reference": "Referencias_publicas/captura.json", "source": "participant_screenshot_not_live", "delta": "s_candidate-s_reference", "relative_deviance_reduction": "(s_candidate-s_reference)/(1-s_reference)", "requires": "same labels, rows, weights and positive null deviance", "own_scores_available": False}
write_json(MODEL / "protocolo_metodologico.json", protocol)
method = (MODEL / "METODOLOGIA_ACTUARIAL.md").read_text(encoding="utf-8")
method = method.replace("Versión 1.10,", "Versión 1.11,", 1)
method += """

## D64: catálogo y métodos de cálculo, versión 1.11

El participante pidió actualizar el catálogo de modelos y la metodología actuarial con la captura aportada. El [catálogo de cálculo](CATALOGO_MODELOS.md) explicita la salida, el ajuste y los controles propuestos de M00–M21. Los 22 candidatos conservan prioridad, dependencias y estado sin entrenar; sus scores propios siguen sin medir. La [tabla pública](Referencias_publicas/TABLA_Y_CALCULOS.md) conserva RiskForge 0,11416, GLM visible 0,10563 y dos referencias 0,07169, con procedencia por imagen y sin verificación en vivo. Los nombres de archivo no acreditan sus métodos ni identifican nuestros candidatos con ellos.

El contrato distingue potencia de ajuste `p_fit` de evaluación `p_eval=1.5`. Para cualquier potencia de ajuste entre uno y dos, la equivalencia de suma de pérdidas entre importes `Y=e*r`, predicción `m=e*q` y tasas usa peso `e**(2-p_fit)`. Con 1,5 es `sqrt(e)`; con la sensibilidad 1,9 de D50 es `e**0.1`. El denominador de D² se calcula de nuevo en la escala de evaluación; esta identidad no iguala los scores de tasas e importes. No cambiar la potencia de evaluación para favorecer un modelo.

M00 compara tasa de balance y tasa que minimiza desviación de importes. M01/M02 usan enlace log con offset de exposición; boosting/redes deben demostrar un offset equivalente o usar tasas con los pesos indicados. Si se incorpora una función adicional de duración, identificarla como variante de proporcionalidad. M09/M10 refinan multiplicativamente una base positiva, con la exposición ya incluida, sin ajustar Tweedie a residuos negativos ni aplicar logaritmo a costes cero. Frecuencia-severidad conserva el conteo de coste positivo; la severidad media agregada por periodo se pondera por ese conteo. La extracción de esperanza de modelos distribucionales y severidad transformada debe volver a CU, sin confundir media con mediana o exponencial de la media logarítmica. El catálogo desarrolla los restantes contratos como propuestas sujetas a verificación de implementación.

Para comparar dos scores de la misma evaluación, `delta=s_A-s_B` y `reducción_de_desviación=(s_A-s_B)/(1-s_B)`, con denominador nulo positivo y común. RiskForge frente al GLM visible: delta 0,00853 y reducción aproximada de desviación 0,9537%, calculadas desde valores redondeados. No interpretar el aumento relativo de D² como porcentaje de reducción del error. La captura no proporciona pérdidas absolutas, predicciones ni incertidumbre de la diferencia.

La implementación operativa de T0/F0, particiones, métrica y runner sigue pendiente. Antes del primer entrenamiento debe cerrarse y comprobarse la exclusión real de customer_service_contacts descrita en D50/D56. Esta actualización no cambia datos, el objetivo, la política D29 ni V22/V23/V24. La verificación métrica histórica conserva su alcance previo y no certifica esta versión; D64 deja comprobaciones documentales y aritméticas propias, sin validación independiente o entrenamiento.
"""
(MODEL / "METODOLOGIA_ACTUARIAL.md").write_text(method, encoding="utf-8")
readme = (MODEL / "README.md").read_text(encoding="utf-8")
readme = readme.replace("El [catálogo de candidatos](experimentos.json) organiza familias de modelos; no es una configuración ejecutable del runner.", "El [catálogo de candidatos](experimentos.json) organiza familias de modelos; no es una configuración ejecutable del runner. D64 añade la [tabla de los 22 modelos y sus cálculos propuestos](CATALOGO_MODELOS.md), la [referencia pública aportada](Referencias_publicas/TABLA_Y_CALCULOS.md) y el protocolo 1.11, sin entrenamiento o resultados propios.")
(MODEL / "README.md").write_text(readme, encoding="utf-8")

decision = """

### D64, catálogo de 22 modelos y contratos de cálculo con referencia pública aportada, 16 de octubre de 2026, America/Bogota

El participante pidió «Actualiza la tabla y los métodos de cálculo» y precisó «Catálogo de modelos y metodología actuarial». Se conserva la imagen y hash en ../Hackaton/Semana 1/Modelado/Referencias_publicas/captura.json. Muestra RiskForge 0,11416 (puesto 1, tres envíos), sandbox_2_basic_glm.csv 0,10563 y sample_submission.csv/sandbox_1_average_cost_baseline.csv 0,07169. Las tres referencias no tienen puesto numérico; textos 3h/2d sin fecha inferida. No se verificó la tabla en vivo ni se identifica RiskForge como equipo propio. El contexto la vincula a parte 1, sin URL visible en la imagen.

CATALOGO_MODELOS.md y experimentos.json desarrollan los contratos propuestos M00–M21, manteniendo olas, dependencias, condiciones y estado sin ejecutar. No se deducen métodos de terceros a partir de scores o nombres. Los scores propios son null. Protocolo/metodología 1.11 distingue p_fit de p_eval=1,5, generaliza peso de tasas equivalente e**(2-p_fit), explicita frecuencia-severidad y refinamiento multiplicativo, esperanza en CU y comparaciones públicas. Se mantiene D29 y V22/V23/V24; ninguna familia se prioriza por esta captura. Brecha del guard de contactos, T0/F0, splits y runner siguen pendientes.

La comparación usa delta D² y reducción relativa de desviación bajo una misma evaluación y denominador nulo positivo: RiskForge–GLM 0,00853 y aproximadamente 0,9537%. Se conservan tabla generada, aritmética decimal, fuente, script y comprobaciones en el cierre D64, con copias previas de documentos. La referencia scikit-learn se consultó para dominio e interpretación; no se reprodujo el scorer del servidor. Verificación propia asistida por IA, sin revisión independiente. No cambia ningún dato, índice de datos o corrida histórica; sin entrenamiento, envíos, automatización, publicación, mensajes o delegación. Documentación IAA §2 y §§4–6, Gobernanza §2.8 y Consideraciones profesionales §§3.5–3.6 orientan procedencia y límites.
"""
with (PREP / "DECISIONES.md").open("a", encoding="utf-8") as stream:
    stream.write(decision)
memory = """

## D64: catálogo y métodos de cálculo actualizados con referencia pública aportada

El participante precisó que quería actualizar el catálogo de modelos y la metodología actuarial. La [tabla M00–M21](../Hackaton/Semana%201/Modelado/CATALOGO_MODELOS.md) y experimentos.json explicitan cálculos propuestos, conservan 22 candidatos sin ejecutar y scores propios null. Protocolo/metodología 1.11 distingue potencia de ajuste y evaluación 1,5, peso e**(2-p_fit), frecuencia-severidad, refinamiento multiplicativo y extracción de esperanza en CU. La [captura conservada y comparaciones](../Hackaton/Semana%201/Modelado/Referencias_publicas/TABLA_Y_CALCULOS.md) muestra RiskForge 0,11416, GLM 0,10563 y dos referencias 0,07169; no es consulta en vivo ni evidencia de métodos o equipo propio. Diferencia RiskForge–GLM 0,00853; reducción aproximada de desviación 0,9537% bajo evaluación común. No cambia prioridad, datos, T0/F0 o validación; sin entrenar o enviar. El cierre D64 conserva documentos previos y comprobaciones propias. D62 sigue siendo fotografía documental hasta D61 y las verificaciones históricas no certifican esta versión.
"""
with (PREP / "MEMORIA_PROYECTO.md").open("a", encoding="utf-8") as stream:
    stream.write(memory)
state = json.loads((PREP / "ESTADO_PROYECTO.json").read_text(encoding="utf-8"))
state["memory_as_of"] = datetime.now(timezone.utc).isoformat()
state["methodological_plan"]["version"] = "1.11"
state["methodological_plan"]["calculation_update_decision"] = "D64"
state["model_calculation_update"] = {"decision_id": "D64", "catalog": "../Hackaton/Semana 1/Modelado/CATALOGO_MODELOS.md", "structured_catalog": "../Hackaton/Semana 1/Modelado/experimentos.json", "public_reference": "../Hackaton/Semana 1/Modelado/Referencias_publicas/captura.json", "reference_status": "user_screenshot_not_live_verified", "candidates": 22, "own_results_available": False, "models_trained": False, "data_changed": False, "closure": "../" + CLOSE.relative_to(ROOT).as_posix(), "verification": "../" + (CLOSE / "verification.json").relative_to(ROOT).as_posix()}
write_json(PREP / "ESTADO_PROYECTO.json", state)
shutil.copy2(__file__, CLOSE / "integrar_D64.py")
print(CLOSE)
