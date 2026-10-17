# Catálogo de modelos y cálculos propuestos

Actualización D64, 16 de octubre de 2026. Los 22 candidatos conservan sus IDs, olas, dependencias y estado sin ejecutar. Esta tabla desarrolla el contrato de cálculo de [experimentos.json](experimentos.json); no acredita implementaciones, entrenamiento o resultados propios.

`Y` es T0 (o el escenario declarado), `e` la exposición positiva, `m` el coste esperado del periodo, `lambda` la frecuencia anual de costes positivos y `s` la esperanza de severidad positiva por siniestro. Modelos por ramo salvo variante conjunta declarada. Los contratos neuronales son adaptaciones propuestas del proyecto, sujetas a sus condiciones bibliográficas e implementación. Todas las filas se evalúan sobre importes con potencia 1,5.

| ID | Familia | Ola | Cálculo de coste del periodo propuesto | Ajuste y controles |
| --- | --- | ---: | --- | --- |
| M00 | line_constant_rate | 1 | `m=e*q_r` | Comparar q_r=sum(Y)/sum(e) y q_r=sum(Y/sqrt(e))/sum(sqrt(e)); ajustar por ramo en train. |
| M01 | glm_tweedie | 1 | `m=e*exp(beta0+x*beta)` | GLM con enlace log; minimizar desviación Tweedie de importes; p_fit=1.5 de referencia y p_fit=1.9 como sensibilidad D50. |
| M02 | gam_tweedie | 2 | `m=e*exp(beta0+sum_j f_j(x_j))` | GAM: curvas y penalización dentro de train; interacciones solo como variante identificada. |
| M03 | glm_gam_frequency_severity | 2 | `m=e*lambda(x)*s(x)` | Poisson para conteo de costes positivos con offset log(e); gamma-log para severidad positiva por siniestro. Si se agregan medias por periodo, ponderar severidad por el conteo positivo. |
| M04 | lightgbm_tweedie | 1 | `m=e*exp(f_arboles(x))` | Boosting Tweedie: verificar base margin/offset o ajustar tasa Y/e con peso e**(2-p_fit). No multiplicar exposición dos veces. |
| M05 | xgboost_tweedie | 1 | `m=e*exp(f_arboles(x))` | Boosting Tweedie: mismo contrato de importe y exposición; verificar soporte del offset en la versión elegida. |
| M06 | catboost_tweedie | 1 | `m=e*exp(f_arboles(x))` | Boosting Tweedie: usar tasa Y/e y peso e**(2-p_fit) si no hay offset; revertir cualquier reescala de CU antes de evaluar. |
| M07 | catboost_frequency_severity | 2 | `m=e*lambda_cat(x)*s_cat(x)` | Frecuencia de coste positivo y severidad positiva separadas; verificar objetivo gamma o likelihood válida. Tweedie con p=2 no es gamma admisible en CatBoost. |
| M08 | credibility_glmm | 2 | `m=e*E[exp(eta(x)+u_grupo) dado historia disponible]` | Especificar distribución, varianza y posterior del efecto; integrar en la escala de coste. Grupos nuevos usan distribución predictiva, sin etiquetas futuras. |
| M09 | glm_gam_residual_boosting | 2 | `m=m_base*exp(g(x))` | Refinamiento multiplicativo con log(m_base) como offset; minimizar pérdida sobre Y, sin log(Y) ni regresión Tweedie sobre residuos negativos. Folds internos para selección. |
| M10 | tabular_cann | 3 | `m=m_GLM*exp(g_red(x))` | CANN con salida positiva; pérdida de importe Tweedie y exposición ya incluida en m_GLM. Comparar contra base sin corrección. |
| M11 | mlp_and_ft_transformer | 3 | `m=e*exp(f_red(x))` | MLP/FT-Transformer: mismo objetivo y contrato F0 que árboles; regularización y parada dentro del desarrollo. |
| M12 | localglmnet | 3 | `m=e*exp(beta0+sum_j beta_j(x)*x_j)` | LocalGLMnet: coeficientes dependientes de x; centrar/identificar efectos y revisar estabilidad sin atribuir causalidad. |
| M13 | localglmftt_and_caftt | 3 | `m=e*lambda_transformer(x)*s(x), o salida Tweedie positiva adaptada` | LocalGLMftt/CAFTT: escoger adaptación explícita antes de implementar. No atribuir coste agregado a un experimento original de frecuencia. |
| M14 | longitudinal_cann_poisson_nb_mvnb | 3 | `m=E[N_periodo dado historia]*s(x,historia)` | CANN longitudinal Poisson/NB/MVNB para conteos; duración incorporada en E[N]. Severidad positiva y contracción histórica se validan por separado. |
| M15 | distributional_refinement_network | 3 | `m=integral_0_infinito (1-F_refinada(t dado x)) dt` | DRN: extraer esperanza finita en CU del periodo, con masa cero y cola explícitas; no sustituirla por mediana o cuantiles. |
| M16 | blend_then_stacking | 4 | `m=sum_k alpha_k*m_k, alpha_k>=0, sum_k alpha_k=1` | Primero mezcla convexa de importes compatibles; pesos y stacking con predicciones fuera de muestra y evaluación externa. Stacking posterior exige salida positiva. |
| M17 | tabm | 3 | `m=e*exp(f_TabM(x))` | Propuesta de adaptación Tweedie; salida y pérdida verificadas antes de piloto. Si es frecuencia-severidad, conservar contrato M03. |
| M18 | actuarial_neural_additive_model | 3 | `m=e*exp(beta0+sum_j f_j_red(x_j))` | ANAM: especificar efectos, suavidad, restricciones e interacciones antes de medir; propuesta de coste por periodo. |
| M19 | credibility_transformer_and_in_context_extension | 3 | `m=e*exp(f_transformer(x,contexto_admisible))` | Propuesta de coste: definir tokens, contexto y contracción; no incluir etiquetas de evaluación ni memoria con información futura. |
| M20 | tabpfn_positive_severity_first | 3 | `m=e*lambda(x)*E[S_positivo dado x]` | TabPFN solo en severidad inicialmente; extraer media en CU. exp(E[log(S)]) no equivale a E[S]; revisar retransfomación, versión, licencia y pesos. |
| M21 | zero_inflated_tweedie_boosting | 3 | `m=(1-pi(x))*e*q_Tweedie(x)` | Mezcla cero adicional/Tweedie: pi es masa estructural adicional y q es media del componente Tweedie. Exigir evidencia de ceros extra; D50 no la encontró en conteos. |

Los resultados local y público de cada candidato siguen sin medir (`null`). Las puntuaciones de [la captura](Referencias_publicas/TABLA_Y_CALCULOS.md) se registran aparte: RiskForge 0,11416; GLM visible 0,10563; plantilla y referencia de coste medio 0,07169. No se equiparan M00/M01 con esos archivos: sus cálculos no se han verificado. La captura no permite cambiar el orden de pruebas ni estimar la mejora de nuestros candidatos.

M00 compara dos tasas constantes distintas. M00/M01/M04/M05/M06 forman la primera ola vigente; el resto mantiene sus condiciones y dependencias. La sensibilidad de potencia de ajuste 1,9 procede de D50, no del leaderboard. A esa potencia, los pesos de tasas equivalentes a importes son `e**0.1`; con 1,5 son `sqrt(e)`. Usar `e` sigue siendo otra sensibilidad actuarial.

Frecuencia-severidad exige una definición consistente: conteo de costes positivos y severidad por siniestro positivo. La fórmula multiplicativa debe representar la misma esperanza agregada; la independencia condicional no se da por probada. Una media por periodo debe ponderarse por su conteo al ajustar severidad; una media por siniestro usa una fila por siniestro. Comparar sobre las mismas filas de evaluación y siniestros admitidos.

Antes de entrenar siguen pendientes T0/F0, splits, métrica/runner multitabla y cierre de la brecha del guard de `customer_service_contacts` identificada en D50/D56. Ver [metodología](METODOLOGIA_ACTUARIAL.md), [protocolo](protocolo_metodologico.json) y fuentes D37/D50. Este catálogo no instala librerías, descarga pesos ni autoriza ejecución remota.
