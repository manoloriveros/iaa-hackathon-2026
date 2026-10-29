# Coberturas y denominadores de exposición por peril

Codex, corte UTC 2026-10-24T01:22:57.474479+00:00. Diagnóstico preinscrito solo con pólizas de 2023. Se conservan B00, todas las alternativas y las curvas congeladas de cada fold. No se entrenó, predijo o puntuó un modelo nuevo.

## La exclusión de daño accidental en hogar no concuerda con el objetivo

Con la bandera accidental_damage_cover desactivada existen seis siniestros de daño accidental en edificios, con 3.175,58 CU netos, y 24 en contenidos, con 25.869,48 CU. Los treinta están cerrados, tienen coste positivo y pertenecen al objetivo canónico; no son reclamaciones repudiadas de coste cero. Su asociación con periodo, póliza, fold y fechas fue comprobada.

Por tanto, esa bandera no se impondrá como máscara de exposición cero para este peril bajo T0. El resultado establece una incompatibilidad entre esa interpretación del campo y los datos modelados; no determina si hay errores, extensiones contractuales, una clasificación más amplia del peril u otra semántica. No se cambian status, banderas, costes o asignaciones, ni se eliminan los treinta siniestros para hacer encajar la hipótesis.

## Cuánto cambiaría el denominador

Para cada ramo, negocio y fold de ajuste se comparan:

`D_all = Σ exposición_nominal × qN_peril`

`D_candidate = Σ máscara_candidata × exposición_nominal × qN_peril`

La exposición nominal viene de F0 con sus correcciones conservadas y está expresada en años de cobertura. No es capital asegurado ni número de pólizas. qN es la completitud de conteo aprendida sin el fold retenido; qC se conserva aparte para coste. Contar pólizas no sustituye a sumar exposición, ni qC sustituye a qN en una frecuencia. Las máscaras son hipótesis previas: en autos, comprehensive para daño propio/glass_hail y comprehensive o third_party_fire_theft para robo; en hogar, la bandera activa para daño accidental. El resto mantiene toda exposición.

| Ramo | Peril con máscara candidata | D_candidate / D_all | D_all / D_candidate | Siniestros positivos únicos fuera |
| --- | --- | ---: | ---: | ---: |
| Edificios | accidental_damage | 38.66–40.32% | 2.480–2.587 | 6 |
| Contenidos | accidental_damage | 43.41–45.33% | 2.206–2.304 | 24 |
| Autos | glass_hail | 76.27–79.56% | 1.257–1.311 | 0 |
| Autos | own_damage | 76.27–79.56% | 1.257–1.311 | 0 |
| Autos | theft | 88.61–90.07% | 1.110–1.128 | 0 |

Los rangos incluyen negocios y cinco ajustes solapados. Las cifras inversas son razones de denominadores, no tasas estimadas ni factores de precio adoptados. Si se redujera únicamente D dejando el mismo numerador, la frecuencia n/D subiría por esa razón. Esto no corrige una incompatibilidad entre ambos conjuntos. No se estimó una frecuencia nueva ni se aplicó esa razón a predicciones.

## Qué respalda la información de cobertura

En autos no hay reclamaciones observadas fuera de las tres máscaras convencionales contrastadas. Es una condición compatible con una sensibilidad futura, no un contrato validado o prueba de riesgo futuro nulo. Las descripciones oficiales archivadas enumeran categorías de cobertura y causas; no proporcionan en esos campos una matriz contractual completa. Glass_hail además reúne dos causas bajo una etiqueta. No se adopta una exclusión automática para autos con esta evidencia.

Bicycle_cover se describe como cobertura opcional de bicicleta, mientras theft es un peril más amplio. Se auditan sus dos categorías sin transformar la bandera en una máscara para todo robo o daño accidental. La ausencia de la extensión de bicicleta no convierte toda exposición a robo en cero.

El denominador amplio actual sigue siendo una aproximación explícita y condicionada. Una eventual estimación por peril tendría que mantener coherentes el conjunto de siniestros, la exposición realmente cubierta y la composición de costes de cada fila. Cambiar solo el denominador de una tasa agregada y mantener una mezcla igual para todos no incorpora por sí mismo la cobertura individual. Tampoco es correcto usar cero reclamaciones de una celda para deducir su exclusión contractual.

## Decisión y próximo ensayo justificable

No se integra ninguna máscara ni se cambia C0, el objetivo o B00. La máscara dura de daño accidental en hogar queda bloqueada por costes positivos fuera; autos queda como hipótesis compatible pero sin validación contractual. Se conservan todos los resultados adversos y los 4.567 siniestros, con 15.297.103,84 CU netos en total.

El siguiente ensayo justificable es un GLM estándar con las coberturas admisibles como efectos principales, manteniendo T0 y C0 sin ceros impuestos: cover_type en autos y accidental_damage_cover en hogar. Responde a una omisión concreta del GLM reducido B14, no a una necesidad de árboles o interacciones. Todavía no está ajustado ni puntuado; cualquier ejecución exige su propia receta, configuración y comentario previo. No se elige un peso, una mezcla o una lista final con este diagnóstico.

## Verificación y alcance

Pasaron 167 controles del productor, 2345 verificaciones y adversos focales y 725 conciliaciones de lectura, con solapamiento. Son controles técnicos; la hipótesis de la máscara de hogar falló. La cuenta separada usa diccionarios de claves y math.fsum para nominal, conteos y costes, contrasta cada categoría y conserva centavos. Los dos comandos adversos reales rechazan año sintético 2024 o cobertura ausente antes de salidas; sus fallos esperados permanecen archivados. No se repiten suites de precios o bootstrap anteriores.

Se auditaron 50.094 periodos, 30.869 componentes, 150 celdas de denominadores y 430 por categoría de cobertura. Los siniestros retenidos no entran en las vistas de ajuste. El perfil global es descriptivo y deduplicado. El contador propio sigue en 165 ajustes de precio y 285 constantes, con primeras etapas y auxiliares separados, sin incremento en esta unidad.

2024 sigue cerrado para este trabajo: no se abrieron actas, predicciones, scores o ledger, ni se hicieron precios de ese año o test. Se conserva la exposición previa de un título ajeno con métricas de confirmación, sin repetirlas o usarlas; no se afirma ceguera completa. El lector del foro solo muestra autor, ID y UTC. Sin remoto, envíos, publicación externa, nuevos chats, delegación o cambios a otras automatizaciones. Revisión técnica propia, no profesional independiente ni aprobación humana.

## Evidencia y continuidad

[Plan congelado](../../../registro/semana2_coberturas_peril2023_plan_v1.json), [índice de esta revisión](../../../registro/semana2_coberturas_peril2023_actual.json), [productor](../../../src/semana2/auditar_coberturas_peril2023.py), [segunda cuenta y adversos](../../../herramientas/verificar_coberturas_peril2023_semana2.py). Evidencia restringida y hashes: `Hackaton/Repositorio_IAA2026/privado/semana2/desarrollo2023/coberturas_20261024T011932Z_14b50ca9`; descripción oficial archivada en `Hackaton/Semana 2/Codex/fuentes_variables_ultimo/data_description_response.json`.

Antecedente: [calendario y soporte](SOPORTE_CALENDARIO_REPORTE_2023.md). [Balance parcial de la noche](BALANCE_NOCTURNO_PARCIAL_20261024.md). La revisión aplica las prioridades de propósito/límites, segmentos y trazabilidad de las prácticas IAA del proyecto sin convertir documentación o controles propios en certificación.


## Ensayo posterior registrado

El [GLM B19](GLM_COBERTURAS_2023.md) ya probó cobertura como efecto principal sobre B14, sin cambiar T0/C0 ni imponer ceros. Empeora el D² global y se conserva como resultado adverso; no se adopta máscara o elimina siniestros. La propuesta pendiente descrita en el corte anterior queda ejecutada bajo su receta propia.
