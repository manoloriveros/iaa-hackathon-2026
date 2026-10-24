# Decisiones de semana 2: capital, clima, nivel del nuevo negocio y gasto fijo

Claude (Cowork), 23 de octubre de 2026. Evidencia del aporte [CLA-S2-20261023-003](../../Foro/FORO.md).

En CLA-S2-20261023-001 quedaron cuatro decisiones para el participante. Su respuesta, en la sesión de Claude, fue: «en las cuatro recomendaciones realiza tus sugerencias, dividir los valores con criterio, clima como indicas, nivel de nuevos negocios con credibilidad, gasto fijo de la primas según exposición pero en este caso dame tu opinión».

Antes de calcular nada quedó fijado cómo se aplica cada decisión en `preinscripcion_decisiones_20261023.json` (CLA-S2-DEC-20261023, SHA-256 2978406fe37a7601cf08b7450a6d46765c5acae23b696a87c93e843ba6a55b51, escrito en el equipo a las 20:09:35 UTC). Esta carpeta guarda solo agregados. Las tablas por fila o por dirección están en `Hackaton/Repositorio_IAA2026/privado/semana2/decisiones_participante_20261023/`, fuera de Git.

Aquí no se ajustan modelos de precios, no se abre 2024 y no se cambia ningún archivo de Codex. Los GLM de la sección 3 solo estiman una relatividad. Integrar las decisiones en F0, en las recetas y en la selección queda en manos de quien mantiene ese flujo. Es trabajo de IA, sin revisión humana.

## Qué contiene

| Archivo | Contenido |
| --- | --- |
| `preinscripcion_decisiones_20261023.json` | Las cuatro reglas y lo que se iba a informar, escrito antes de calcular |
| `aplicar_decisiones.py` | Aplica las cuatro reglas desde los Parquet originales y escribe evidencia, tablas, figuras y manifiesto |
| `glm_robusto.py` | GLM Poisson y Gamma con enlace log, por IRLS, con errores típicos robustos agrupados por cliente |
| `figuras_decisiones.py` | Las cinco figuras |
| `factor_nuevo_negocio.py` | Calcula el factor de nuevo negocio de cualquier receta a partir de su OOF |
| `factores_nb_cred.json` | Los factores c, la relatividad creíble y Z por ramo |
| `evidencia_decisiones.json` | Todas las cifras, con las huellas de las entradas |
| `tablas/` | Coeficientes de los GLM, comprobación del clima, diagnóstico sobre los OOF de 2023 y gasto fijo de las veinte referencias |
| `aporte_CLA-S2-20261023-003.md`, `cifras_aporte.json`, `verificar_aporte.py` | El aporte tal como se anexó al foro y el verificador de sus cifras |
| `manifiesto.json` | SHA-256 de entradas, scripts, salidas y tablas privadas |

## 1. Capital entre mil con criterio (CAPS2-01)

En hogar del emergente hay filas con capitales mil veces mayores que el resto: por encima de 5 millones de CU en edificios y de 2 millones en contenidos, cuando la población normal no pasa de 894.000 y 283.200. F0 de Codex los trataba como capital desconocido (una máscara). La decisión es dividirlos entre mil, pero solo si una prueba de la propia fila lo respalda.

La prueba se apoya en que la prima escrita no depende de la escala en que se registró el capital: la prima por mil de capital (1.000 × prima / capital) delata la escala. En la población normal de edificios va de 0,451 a 17,4 (mediana 1,06); en contenidos, de 1,61 a 10,6 (mediana 3,43). Una fila por encima del umbral se divide si su prima por mil queda por debajo del mínimo normal con el capital leído y dentro del rango normal con el capital entre mil. Es la prueba PRM01-R de D66.

![Prima por mil antes y después de dividir](fig1_capital.png)

Las 349 filas por encima del umbral (157 de edificios y 192 de contenidos; 110 de entrenamiento y 239 de test) pasan la prueba, y ninguna queda fuera. Con el capital leído, su prima por mil es como mucho 0,011 en edificios y 0,0070 en contenidos, 41 y 231 veces por debajo del mínimo normal. Divididas, quedan entre 0,60 y 11,0 en edificios y entre 2,09 y 6,95 en contenidos. También hay una comprobación independiente: 72 de las 157 de edificios y 91 de las 192 de contenidos tienen otra fila de la misma póliza, en escala normal, con un capital entre 0,80 y 1,25 veces el dividido.

| | Edificios | Contenidos |
| --- | ---: | ---: |
| Filas por encima del umbral | 157 | 192 |
| Pasan la prueba | 157 | 192 |
| De ellas en test | 104 | 135 |
| Confirmadas además por la historia de la póliza | 72 | 91 |
| Prima por mil máxima con el capital leído | 0,011 | 0,0070 |
| Mínimo de la población normal | 0,451 | 1,61 |

En F0 basta con poner, en esas filas, `x_log_sum_insured = log(sum_insured_model)`. Se conservan `sum_insured_raw` y las marcas `audit_capital_scale_adjusted` y `audit_capital_scale_confirmed`, que no entran como predictores, igual que las demás marcas `audit_*`. La tabla `capital_caps2_01.parquet` tiene una fila por cada una de las 349, y la lista ordenada de sus `row_id` tiene SHA-256 964cab97d1fcb2b559c744374581be9a9d21fd92836bef991db29f8878d161bb.

## 2. Clima de la dirección (CLIMA-S2-01)

El clima del año de cobertura no se conoce al cotizar y la base de Codex lo deja fuera; eso se mantiene. Algunas variables, en cambio, describen más la dirección que el año: si una calle es ventosa o lluviosa, lo es todos los años. Esas variables se pueden usar como un atributo de la dirección, medido en otro año.

Entran en el bloque las variables que tienen una correlación entre direcciones de 0,80 o más de 2023 a 2024 y de 2024 a 2025: la exposición al viento (0,87 y 0,91), el índice forestal (0,89 y 0,87) y la lluvia anual (0,92 y 0,95). Las demás no llegan: granizo (0,20 y 0,23), sequía estival (0,60 y −0,24), heladas (0,79 y 0,70) y temperatura (0,90 y 0,50).

Cada fila toma el valor de su dirección en el otro año de 2023–2024: las de 2023 toman 2024, las de 2024 toman 2023 y las de 2025 la media de los dos. Nunca entra el clima del propio año ni el de 2025. En las filas de 2023 eso significa usar 2024; se acepta porque la variable se trata como un rasgo estable de la dirección, y se declara.

![Persistencia y gradiente del clima](fig2_clima.png)

Si el bloque mide un rasgo estable, debería ordenar los siniestros casi igual que el clima del propio año. En el desarrollado de 2021 a 2023, con miles de siniestros, la frecuencia del tercil más alto frente al más bajo es:

| Peligro y variable | Otros años (bloque) | Propio año | Siniestros |
| --- | ---: | ---: | ---: |
| Tormenta en edificios, viento | 1,53 | 1,60 | 5.868 |
| Incendio en edificios, índice forestal | 1,43 | 1,41 | 798 |
| Inundación en edificios, lluvia | 2,27 | 2,07 | 1.689 |
| Inundación en contenidos, lluvia | 2,92 | 2,15 | 1.254 |
| Escape de agua en edificios, lluvia | 0,87 | 0,88 | 7.507 |
| Escape de agua en contenidos, lluvia | 0,94 | 0,94 | 4.004 |

En el emergente de 2023 la comparación va en la misma dirección, pero con pocos siniestros (49 de incendio, 42 y 51 de inundación); está en `tablas/clima_comprobacion.csv`.

El bloque es una variante (F0 más el bloque) para que Codex la contraste con su política de selección; no entra en la base sin ese contraste. La tabla `clima_direccion_s2_01.parquet` tiene una fila por dirección y año (2023, 2024 y 2025) con `x_clima_dir_wind_exposure_index`, `x_clima_dir_wildfire_index` y `x_clima_dir_rainfall_mm`.

El clima realizado de 2025 se declara como escenario, sin entrar en las predicciones. Los factores son los de CLA-S2-20261023-001 (estandarización directa por tramos de una variable): lunas −24 %, escape de agua +12 % en edificios y +19 % en contenidos, hundimiento −25 % con solo 52 siniestros y tormenta −4 %.

## 3. Nivel del nuevo negocio con credibilidad (NB-CRED-01)

### Por qué importa tanto

En 2025 el 77 % de la exposición es nuevo negocio, casi todo una cartera de broker que entra en enero. En 2023 y 2024 era una parte pequeña. Por eso la relatividad del nuevo negocio frente a la renovación fija casi todo el nivel de 2025. El emergente tiene pocos datos de nuevo negocio (315 siniestros de autos, 40 de edificios y 37 de contenidos en 2023) y el desarrollado tiene muchos (9.400, 1.782 y 1.719 entre 2021 y 2023). La credibilidad combina las dos fuentes según cuánto informa cada una.

### Qué se estimó

1. Por ramo y mercado, un GLM de frecuencia (Poisson, enlace log) y otro de severidad por siniestro (Gamma, enlace log), con las mismas covariables comunes (edad, carnet, NCB, vehículo, cobertura, canal, franquicia, densidad urbana en autos; capital, ocupación, alarmas, zona inundable, tipo y antigüedad de la vivienda, entre otras, en hogar), la región de cada mercado y un indicador de nuevo negocio. Su coeficiente es la relatividad neta de las demás covariables. Se excluyen las variables que dependen del propio nuevo negocio: renovaciones previas, antigüedad del cliente, días entre cotización e inicio y mes de inicio.
2. La exposición se pondera por estación. El nuevo negocio orgánico empieza a lo largo del año y termina el 31 de diciembre, así que cubre más meses de invierno. En edificios la frecuencia de enero, febrero y diciembre es 1,27, 1,35 y 1,45 veces la media. Cada día de exposición se pondera con el índice mensual de las renovaciones del desarrollado.
3. Solo entran años maduros: emergente 2023 (2024 sigue cerrado para la confirmación) y desarrollado de 2021 a 2023.
4. Los errores típicos son robustos y agrupados por cliente, para no contar dos veces a un cliente con varios periodos.
5. τ mide la distancia real entre mercados. Para las otras 75 categorías con al menos 100 siniestros emergentes se compara el coeficiente de los dos mercados y se descuenta el ruido de muestreo: τ² = media de [(β_em − β_dev)² − SE_em² − SE_dev²]. Sale τ = 0,048 en frecuencia y 0 en severidad.
6. La credibilidad es Z = τ² / (τ² + SE²), con SE el error típico de la relatividad emergente. Z dice qué parte del peso se lleva el emergente.

### El resultado

| Ramo | Frecuencia emergente | Frecuencia desarrollado | Z | Severidad emergente | Severidad desarrollado | Z | Relatividad creíble | c |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Autos | 1,23 | 1,16 | 0,36 | 1,32 | 0,98 | 0,00 | 1,16 | 0,713 |
| Edificios | 1,21 | 1,13 | 0,08 | 0,97 | 0,98 | 0,00 | 1,11 | 0,946 |
| Contenidos | 1,18 | 1,15 | 0,07 | 0,80 | 0,93 | 0,00 | 1,07 | 1,132 |

![Relatividades del nuevo negocio en los dos mercados](fig3_nuevo_negocio.png)

En frecuencia, el emergente de autos aporta algo (Z = 0,36) y el de hogar casi nada (Z de 0,07 y 0,08), porque con 40 y 37 siniestros su relatividad tiene un error típico de 0,16 y 0,17 en escala log. En severidad τ es cero: las diferencias entre mercados en las otras categorías se explican por el ruido, así que la severidad del nuevo negocio se toma entera del desarrollado. El 1,32 de autos lo explican pocos siniestros: los cinco mayores suman el 38 % del coste del nuevo negocio de autos en 2023, frente al 4,1 % en la renovación y al 3,9 % del nuevo negocio del desarrollado. Si se quitan los cinco mayores de cada grupo, la media queda en 2.170 CU en el nuevo negocio y en 2.095 en la renovación.

Las sensibilidades preinscritas apenas mueven el resultado:

| Variante | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: |
| Principal | 1,160 | 1,113 | 1,065 |
| Sin estacionalidad | 1,164 | 1,101 | 1,056 |
| Índice estacional del emergente | 1,170 | 1,081 | 1,025 |
| τ sin las categorías de NCB | 1,161 | 1,113 | 1,065 |

### Cómo se aplica a una receta

El factor deja la receta como está y corrige solo el nivel de sus filas de nuevo negocio.

1. Con las predicciones cruzadas de la receta en sus filas de ajuste, se calcula por ramo la razón entre el A/E del nuevo negocio y el de la renovación. Eso lleva la receta a la experiencia emergente.
2. Esa razón se multiplica por c = exp(θ_creíble − θ_emergente), que mueve la relatividad emergente hacia la creíble.
3. g_NB = razón × c multiplica las filas de nuevo negocio; las renovaciones no cambian.

`factor_nuevo_negocio.py --oof <parquet> --modelo <receta>` hace los tres pasos. Con todo 2023 da:

| Receta | Autos | Edificios | Contenidos |
| --- | ---: | ---: | ---: |
| W2-B00 (tasa constante por ramo) | 1,621 | 0,904 | 1,234 |
| W2-B06 (GLM con el nivel de B00) | 0,724 | 0,810 | 1,319 |
| W2-B08 (mitad B00, mitad B06) | 1,016 | 0,854 | 1,275 |

c se calculó con el emergente de 2023. Si la receta final se entrena con 2023 y 2024, conviene repetir `aplicar_decisiones.py` con esa ventana para que θ_emergente y Z correspondan a los mismos datos.

Las recetas W2-B10 y W2-B11 de Codex (COD-S2-20261023-015) ya calibran el nivel de cada segmento de nuevo negocio y renovación con el escalar Tweedie aprendido en el ajuste, solo con el emergente. Para llevarlas al nivel creíble basta con multiplicar su factor de nuevo negocio por c.

### Lo que dice 2023, y lo que no puede decir

El diagnóstico aplica el factor, fold por fold y sin mirar el fold evaluado, a los OOF de 2023 de las diez recetas de Codex (`dev3_20261023T181613Z_24c943a3`). Lo compara con la receta guardada, con el nivel solo emergente (Z = 1) y con el nivel solo desarrollado (Z = 0), con la mezcla real de 2023 y con la de 2025.

![Diagnóstico sobre los OOF de 2023](fig4_diagnostico_2023.png)

- Con la mezcla de 2025, el nivel del nuevo negocio pesa más que el cambio de receta. W2-B00 pasa de un D² de 0,054 a 0,091 con el nivel creíble y a 0,093 con el solo emergente.
- Con todas las filas de 2023, el nivel creíble nunca es el mejor: gana la receta guardada o el nivel solo emergente. En las recetas que ya modelan el nuevo negocio, el creíble resta D² (W2-B06 baja de 0,068 a 0,032 y W2-B08 de 0,079 a 0,069), porque 2023 contiene esos siniestros grandes.
- Sin las 51 filas más caras (el 0,1 %), el creíble supera al solo emergente en nueve de las diez recetas, aunque la receta guardada sigue por delante en nueve de diez.

La lectura es que 2023 no puede decidir el nivel de 2025. Lo que separa a las variantes son unos pocos siniestros grandes del nuevo negocio orgánico, y el nuevo negocio de 2025 es otra población.

### Lo que está en juego y lo que queda sin medir

Para una receta que reproduce la experiencia emergente, pasar al nivel creíble cambia el total de 2025 en −24 % en autos, −4 % en edificios y +10 % en contenidos. Ninguno de los dos mercados mide el bloque transferido: la relatividad creíble describe el nuevo negocio orgánico. Si el bloque de enero se comportara como renovación, el nivel creíble bajaría otro 10 % en autos, 8 % en edificios y 5 % en contenidos. Esa es la incertidumbre que conviene declarar en el informe.

Propongo congelar antes de abrir 2024 tres variantes del nivel para la receta que vaya a confirmación (guardada, solo emergente y creíble), con la creíble como principal por decisión del participante, y leerlas en 2024 como diagnóstico fuera de tiempo. El nuevo negocio de 2024 también es orgánico, así que tampoco medirá el bloque de enero.

## 4. Gasto fijo en la prima comercial (GASTO-F-01)

La prima comercial de cada fila es P = [R × (1 + r) + F] / (1 − v − c − t − m), con los supuestos de `expenses.parquet` para el emergente: F = 85 CU por póliza, v = 0,15, t = 0,08, m = 0,08, comisión 0 en directo y 0,20 en broker, y r = 0,12 de reaseguro catastrófico sobre la prima de riesgo de edificios y contenidos. El denominador es 0,69 en directo y 0,49 en broker: cada CU de gasto fijo cuesta 1,45 CU de prima en directo y 2,04 en broker. La regla decidida es F_fila = 85 × exposición.

![Gasto fijo en las veinte referencias](fig5_gasto_fijo.png)

En 17 de las 20 referencias, cobrar F entero en vez de F × exposición cambia en menos de 8 CU la parte de la prima que paga el gasto fijo, porque casi todas empiezan en los primeros días de enero. Las otras tres:

| Referencia | Qué es | F × exposición | F entero por póliza y año | F entero en cada fila |
| --- | --- | ---: | ---: | ---: |
| C00314425 | Tramo del 13-01 al 06-02 de una póliza con otra fila hasta el 31-12 | 11,9 | 12,3 | 173,5 |
| B00250679 | Tramo del 22-11 al 31-12 de una póliza nueva del 15-11 | 19,0 | 147,6 | 173,5 |
| M00129413 | Póliza nueva del 02-09 al 31-12 | 57,5 | 173,5 | 173,5 |

Las cifras son la parte de la prima comercial que paga el gasto fijo, F / denominador, en CU.

El participante pidió opinión sobre este punto. F × exposición me parece la regla correcta como base, por cuatro razones:

- Trata los 85 CU como un coste anual por póliza, que es como se construye en tarificación un gasto fijo por unidad de exposición (Werner y Modlin, *Basic Ratemaking*, capítulo 7, «Other Expenses and Profit»).
- La prima comercial por año de un mismo riesgo no depende de cómo se parta el periodo.
- No cobra dos veces en los tramos, como pasaría con C00314425.
- Permite comparar P / exposición con la prima escrita, que es anual.

Su punto débil es la póliza nueva corta. Si parte de los 85 CU es coste de emisión, que se gasta entero al empezar, F × exposición se queda corta en M00129413 (recupera 28 CU) y en B00250679 (9 CU). No hay datos para separar emisión de mantenimiento, así que mantendría F × exposición y declararía una sensibilidad en esas dos: cobrar F entero por póliza y año sube su prima comercial en 116 y 129 CU. La regla de F entero en cada fila es la menos defendible de las tres.

El R de `tablas/gasto_fijo_referencias.csv` es ilustrativo (tasa observada de 2023 por ramo × exposición) hasta tener el candidato final; la figura solo muestra la parte del gasto fijo, que no depende de R.

## Cambios respecto de la preinscripción

- El control de hueco preinscrito (filas bajo el umbral con prima por mil menor que el mínimo normal / 10) no podía fallar, porque el mínimo normal se calcula sobre esas mismas filas. Se informa y se añade uno que sí puede fallar: filas bajo el umbral con prima por mil menor que la mediana normal / 100. Da cero.
- Se añadieron, sin preinscribirlos, la concentración de la severidad en los cinco mayores siniestros y el diagnóstico sin el 0,1 % de filas más caras. Los dos se leen como descriptivos.
- En el desarrollado la comprobación del clima usa la media de los otros años de 2021 a 2024, la misma idea con más años.

## Cómo repetirlo

Desde `C:/dev/Hakaton`, con un Python que tenga pandas, pyarrow, scipy y matplotlib:

```powershell
$py = 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe'
$env:PYTHONPATH = 'C:/dev/Hakaton/Preparación/.cache/parquet-reader'   # pyarrow aislado del laboratorio
$dir = 'Hackaton/Semana 2/Claude/decisiones_20261023'
& $py "$dir/aplicar_decisiones.py" --out "$dir/repeticion" --privado "$dir/repeticion/privado"
& $py "$dir/verificar_aporte.py"
```

Sin argumentos de datos lee `Hackaton/Semana 2/Datos/emerging`, `Hackaton/Semana 1/Datos`, el OOF de `dev3_20261023T181613Z_24c943a3` y la evidencia de `revision_apertura_20261023`, y comprueba sus SHA-256 contra los manifiestos antes de calcular. La corrida original se hizo en la nube de Claude (Python 3.13, pandas 3.0, numpy 2.5, pyarrow 26, scipy 1.18) y tardó unos tres minutos y medio; repetida dio la misma evidencia salvo la hora.

## Límites

- Los GLM estiman una relatividad para la credibilidad, no son candidatos de precio, y su relatividad describe el nuevo negocio orgánico de los dos mercados, no el bloque transferido.
- El bloque de clima usa 2024 en las filas de 2023 y descansa en la persistencia de esas tres variables.
- Las comparaciones entre mercados son de los datos de 2023 (emergente) y 2021–2023 (desarrollado) al 31-12-2024, sin desarrollo a último.
- Revisión de IA, no revisión profesional independiente.
