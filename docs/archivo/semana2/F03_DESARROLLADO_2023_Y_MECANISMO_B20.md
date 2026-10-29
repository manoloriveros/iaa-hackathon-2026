# F03: mercado desarrollado de 2023 y mecanismo de B20

Codex, corte UTC 2026-10-24T15:00:15.085824+00:00. El mercado desarrollado aporta definiciones y un contexto para formular hipótesis de heterogeneidad. Esta revisión documental no establece que la contracción de B20 corrija sobreajuste, una pendiente o un efecto causal. Tampoco aporta nuevos componentes al soporte emergente. G1 sigue plausible y no establecido; el incumplimiento de soporte emergente G2 conserva su estado anterior, sin repetir su diagnóstico.

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

El [índice F03](../../../registro/semana2_F03_desarrollado2023_actual.json) enlaza matriz, recibo de esquema/diccionario, fuentes con SHA y decisiones. [F02](F02_SEMANTICA_Y_DISPONIBILIDAD_2023.md), [revisión de mecanismo/soporte](EVIDENCIA_DISPONIBLE_MECANISMO_SOPORTE_B20_2023.md) y [evidencia adversa previa del prior](CAPITAL_POR_FILA_Y_AUTOS_NUEVOS_2023.md) mantienen sus versiones. La documentación IAA de propósito/procedencia (§2) y modelo (§3), y gobernanza §2.8 orientan distinguir evidencia, supuesto y revisión propia; esta ficha no certifica aptitud actuarial.
