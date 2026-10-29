# Guía técnica del paquete de reproducción

Esta guía reúne las notas operativas del paquete de reproducción: estructura, datos, órdenes, verificación hecha y control de versiones. Proviene del README de trabajo del 19 de octubre de 2026, cuya copia íntegra queda en `privado/trazabilidad/` (y sus versiones anteriores, en la historia de Git); la portada del repositorio presenta ahora la entrega final. La autoría de cada pieza consta en `registro/` y en `docs/expediente/`.

## Entrega final del 23 de octubre de 2026: S41

La entrega final de la parte 1 es `S41_nivel_credibilidad.csv` (SHA-256 `d8661c28…c643a5`, envío Kaggle 57531719, puntuación pública 0,13016), que el participante seleccionó en Kaggle el 23 de octubre (CIE-D103-20261023). Es la Mezcla por peligro sin reentrenar, con el nivel de 2025 de cada ramo multiplicado por el factor que dio la regla de credibilidad fijada antes de puntuar las sondas (D100): 0,9962 en autos, 1,0260 en edificios y 1,0126 en contenidos. `python herramientas/regenerar_s41.py --raiz C:/dev/Hakaton` lo regenera byte a byte desde el CSV de S30 y aplica los diez controles de entrega (recibo en `evidencia/entrega_final_S41.json`); el paso de nivel se repitió además en las tres raíces de la reproducción, con el mismo SHA y diferencias de último bit en las notas ([REPRODUCCION_COMPLETA.md](../../REPRODUCCION_COMPLETA.md)). En qué consiste, con qué hipótesis, por qué es adecuado y con qué límites está en la página 4 del [informe](../../entrega/informe_es.pdf) y en su anexo; las calibraciones que se probaron después y no se eligieron (D101 y D102) quedan en el anexo y en [SENSIBILIDAD_S43.md](SENSIBILIDAD_S43.md), y las reservas con la regla de S41, en [RESERVAS_ACOTACION.md](RESERVAS_ACOTACION.md). Lo que sigue en esta guía describe S30, que S41 conserva intacto salvo por esos tres factores.

## Estado de trabajo al 20 de octubre de 2026

La [revisión desde la posición del participante](REVISION_DESDE_EL_PARTICIPANTE.md), solicitada el 19 de octubre, contrasta la cadena vigente y propone decisiones de cierre. Conserva la autoría registrada y no firma la revisión humana. Su registro distingue recálculos nuevos, evidencia histórica y supuestos pendientes.

Desde el 19 de octubre de 2026 esta es la carpeta común de trabajo y revisión de la semana 1, por solicitud del participante. El modelo definitivo es `S30_claude_b`, la Mezcla por peligro (puntuación pública 0,12996, envío Kaggle 57371361). `S22_claude_propio` queda como registro histórico y ya no es respaldo operativo. La selección final manual en Kaggle sigue pendiente. Ambos predicen el coste último esperado de cada periodo de póliza de 2025 en autos, edificios y contenidos. S30 cambia frente a S22 la severidad de autos y edificios por una con tendencia anual por peligro y los pesos de contenidos.

Para empezar la revisión: [guía pendiente del participante](../../REVISION_PENDIENTE_PARTICIPANTE.md), [panel detallado](../../panel_revision.html#revision), [informe actual](../../entrega/informe_es.pdf), [fuente editable actual](../../entrega/informe/INFORME_ES.md), [matriz de requisitos](../../../registro/requisitos.json) y [estado de entrega](../../../registro/estado_entrega.json). El anexo está después de las cinco páginas calificables del informe actual. El panel funciona como archivo HTML local, sin servicios externos. Tiene filtros de variables, pruebas y hallazgos, y notas de revisión exportables. La página es una fotografía fechada; no acredita aprobación humana.

El repositorio [manoloriveros/iaa-hackathon-2026](https://github.com/manoloriveros/iaa-hackathon-2026) es privado. El cierre de la parte 1 es el viernes 23 de octubre a las 11:00 a. m. Bogotá. Informe, video y código se entregan al finalizar la parte 2. Las [fuentes oficiales del 19 de octubre](../../fuentes/reglas_kaggle_20261019.json) conservan el contrato consultado.

La [reconstrucción D97](../../REPRODUCCION_COMPLETA.md) produjo los CSV exactos desde los originales y guardó estimadores. Coinciden 162 de 181 huellas históricas; 19 difieren en los últimos bits y se conserva el código 3. El replay del autor coincide en 194 salidas con su nueva corrida de referencia; VAL12 cotejó 191 salidas principales disponibles localmente. Se conserva el límite del reindexado, de los recálculos actuariales y de la ausencia de independencia. Esta revisión documental no repite ninguna de esas corridas.

## Qué hay en cada carpeta

| Carpeta o archivo | Contenido |
| --- | --- |
| `reproducir.py` | Punto de entrada único (modos `plan`, `datos`, `componentes`, `todo`, `mezcla` y `verificar`), versión 1.2: controles de conformidad, copia de insumos en Windows, rutas absolutas antes de cambiar de directorio y serialización LF de los dos CSV finales |
| `receta/receta.json` | Los 36 nodos que van de las variables a los dos CSV: script, argumentos exactos, dependencias, salidas, procedencia y tiempo de referencia |
| `receta/huellas_esperadas.json` | Bytes, SHA-256 y huella de contenido de las 8 entradas, de las 184 salidas originales y de los 3 insumos de exposición del modo mezcla |
| `receta/especificaciones/` | Configuraciones de los modelos LightGBM (`cfg_*.json`) y pesos de las dos mezclas (`spec_s22_propio.json`, `spec_s30.json`) |
| `receta/codigo.json` | SHA-256 de cada script y su comparación con los manifiestos de corrida donde los hay; la sección `paquete` identifica la versión del orquestador y de las herramientas |
| `src/modelos/` | Código de la línea principal de modelado, copiado sin cambios desde donde se ejecutó: variables, modelos, severidades, mezcla y la batería de validación |
| `src/linea_b/` | Código de la línea B de modelado: severidad con tendencia por peligro, regla de nivel para sus componentes y mezcla de S30 |
| `src/datos/` | Etapas desde los originales: productor de la capa preparada (`n62_codex/`), bases actuariales y matriz F0 |
| `herramientas/` | `huella.py` (huellas de bytes y de contenido), `inventario.py` (huellas esperadas desde las corridas originales), `etapas_datos.py` (raíz de proyecto mínima para las etapas de datos) y `probar_controles.py` (45 casos que comprueban desde la consola que el paquete rechaza faltantes, archivos ilegibles, huellas ausentes y diferencias) |
| `entorno/` | Entorno de referencia (versiones, núcleos, memoria) |
| `docs/` | Verificación de la reconstrucción (`verificacion.md`), evidencia de los casos de control (`controles/`), lista de adaptación para la parte 2 e historia del desarrollo |
| `registro/` | Estado, requisitos, fuentes por SHA, artefactos de mezcla y plantilla de revisión humana; se versionan |
| `privado/` | Copias exactas de CSV, componentes de referencia y corridas nuevas; se excluye completo de Git |

## Datos

Los datos del concurso no están en el repositorio y no deben subirse a él: las reglas prohíben redistribuirlos. Los scripts los leen de una carpeta con la estructura de `Hackaton/Semana 1` del proyecto, que se indica con `--semana1=<carpeta>` o con la variable `IAA_SEMANA1`:

```text
Semana 1/
  Datos/                                   los once Parquet originales del reto (weather.parquet y sample_submission.parquet se leen aquí)
  Matriz_F0_claude/runs/f0_20261017T141732Z_65df7fca/        matrices F0 por ramo, particiones y contrato de disponibilidad (D68)
  Bases_actuariales_claude/runs/bases_20261017T120251Z_45443ff0/   asignación de siniestros y T0 (D67)
  Modelos_claude/, Modelos_claude_b/       solo para el modo mezcla: corridas guardadas de los componentes
```

`reproducir.py componentes` comprueba antes de empezar que las ocho entradas tienen la huella de contenido registrada, y `reproducir.py mezcla` comprueba cada componente guardado antes de mezclar.

## Cómo reproducir

Los 46 insumos de mezcla y la plantilla ya están congelados por SHA en `privado/artefactos_s30_s22/` (47 archivos, unos 193 MB). Son predicciones guardadas de componentes y exposiciones, no una reproducción completa del entrenamiento. Las corridas originales se conservan como evidencia. Para repetir la mezcla desde esta carpeta común:

```powershell
$env:PYTHONPATH='C:/dev/Hakaton/Preparación/.cache/parquet-reader'
$env:PYTHONUTF8='1'
& 'C:/dev/Hakaton/Preparación/.venv/Scripts/python.exe' reproducir.py mezcla --semana1=privado/artefactos_s30_s22 --artefactos=privado/artefactos_s30_s22 --trabajo=privado/mi_revision --continuar-si-difiere
```

La opción de continuar conserva las diferencias intermedias y devuelve 3 cuando las hay; no representa conformidad íntegra. Sin ella, la primera diferencia detiene con 1. Los CSV finales siempre requieren bytes exactos. `registro/artefactos_mezcla.json` permite volver a localizar cada original. Para recrear esas copias, `herramientas/congelar_mezcla.py --semana1=<Semana 1>` comprueba todos los SHA antes de copiar y se niega a sobrescribir una copia privada alterada.

Instalar las versiones de `requirements.txt` (Python 3.13). Con otras versiones la mezcla se repite igual, pero el reentrenamiento de los componentes puede no ser byte a byte.

Repetir las mezclas finales desde los componentes guardados (segundos):

```text
python reproducir.py mezcla --semana1="C:\dev\Hakaton\Hackaton\Semana 1" --trabajo=trabajo_mezcla
```

La salida termina con el SHA-256 obtenido y el esperado de cada CSV (`fd9528e0…e3bc5` para S30 y `c21a02e1…3541b0` para S22), `coincide: true` y el estado de la corrida. El código de salida es 0 solo si todo coincide: 1 si un artefacto requerido falta, no se puede leer, no tiene huella esperada o difiere, si un nodo falla o si un CSV final tiene otro SHA-256; 2 si la orden es incorrecta; 3 si se pidió `--continuar-si-difiere` y hubo diferencias de contenido en artefactos intermedios aunque los CSV coincidan. Fuera del entorno de referencia, el Parquet de 2025 a precisión completa difiere en el último bit (ver más abajo), así que la orden estricta se detiene en él con código 1 y, con `--continuar-si-difiere`, termina con código 3 y los dos CSV iguales.

Reentrenar todos los componentes desde las variables (unas diez horas con dos núcleos; se puede interrumpir y relanzar con la misma orden: antes de saltar un nodo ya hecho se comprueban las huellas de sus salidas, y un nodo con salidas parciales detiene la orden salvo que se pida `--relanzar-parciales`, que las aparta sin borrarlas):

```text
python reproducir.py plan                      # orden de los nodos y orden exacta de cada uno
python reproducir.py componentes --semana1=<carpeta> --trabajo=reconstruccion
python reproducir.py verificar --trabajo=reconstruccion
```

Cada nodo deja su salida en `reconstruccion/registros/<nodo>.log` y una línea en `reconstruccion/registro.jsonl` con la orden, la duración y, para cada artefacto, si coincide en bytes y en contenido con el original. La reconstrucción se detiene en el primer artefacto requerido que no coincide; `--continuar-si-difiere` la deja seguir anotando cada diferencia, pero entonces termina con código 3 y no con 0. `verificar` termina con código 1 si algo falta, es ilegible, no tiene huella esperada o difiere. `--objetivo=S30` limita el trabajo a lo que necesita S30 (S22 añade la red neuronal de contenidos y tres severidades).

Desde los once Parquet originales (unos dos minutos más):

```text
python reproducir.py datos --semana1=<carpeta Semana 1> --trabajo=desde_cero     # capa preparada, bases actuariales y F0
python reproducir.py todo --semana1=<carpeta Semana 1> --trabajo=desde_cero      # lo anterior y después todos los componentes
```

Las etapas de datos fallan si los originales, la capa, las decisiones congeladas, las bases, las tablas F0 o los bloques del contrato no coinciden con la receta. La capa preparada la produce `src/datos/n62_codex/rebuild_base.py`, el productor N62, que aplica las ocho reglas de datos (ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00) leyendo solo los originales y `rules.json`. Después corren sin cambios `src/datos/bases_actuariales.py` (D67) y `src/datos/construir_f0.py` (D68), dentro de una raíz de proyecto mínima que el orquestador arma en `--trabajo`, porque los dos localizan sus entradas subiendo hasta `RUTAS_PROYECTO.json`. F0 lee además tres listas congeladas del proyecto que solo alimentan marcas `audit_*`, excluidas de los predictores; se toman de `--decisiones` (por defecto la misma carpeta Semana 1) y se comprueban por SHA-256.

## Qué hace el modelo

La etiqueta de entrenamiento es T0: el coste incurrido neto de los siniestros aceptados asignados a cada periodo de póliza, valorado al 31 de diciembre de 2024 (D67). Los siniestros todavía no reportados no se suman a la etiqueta; entran por la exposición. Cada fila de entrenamiento lleva una exposición efectiva, la nominal multiplicada mes a mes por la completitud de reporte del peligro que sale de un chain-ladder de conteos, y los modelos usan su logaritmo como offset. Al predecir 2025 se usa la exposición nominal, de modo que la predicción queda a nivel último sin un segundo factor de IBNR (D70).

La validación es temporal y tiene tres cortes. V23 entrena con 2021 y 2022, para el boosting con la mitad de calibración de 2023 y mide en la mitad de selección. V24 entrena con 2021 a 2023 con las rondas de V23 multiplicadas por 1,15 y mide en 2024. Producción entrena con 2021 a 2024 con las rondas por 1,3 y predice 2025. No se usan costes observados de 2025. La normalización anual de prima y la regla de nivel sí usan covariables y predicciones de esa cartera; el método opera sobre un lote, no acredita cotización individual estable.

S30 mezcla diez componentes, tres o cuatro por ramo:

| Ramo | Componente | Peso |
| --- | --- | ---: |
| Autos | CatBoost Tweedie del coste total, cuatro semillas (`CAT_motor_4s`) | 0,2 |
| Autos | CatBoost Poisson por peligro por severidad GLM gamma con nivel por tendencia anual (`B_CFST_motor_tendencia`) | 0,6 |
| Autos | LightGBM Tweedie del total con F0 a F4 (`S04b_lgbm_F0124_F3autos`) | 0,1 |
| Autos | LightGBM Tweedie del total con variables reducidas (`S06c_lgbm_motor_red`) | 0,1 |
| Edificios | LightGBM Tweedie del total con siete variables de cliente (`S12h_edif_md1000`) | 0,4 |
| Edificios | CatBoost Poisson por peligro por severidad por capital con tendencia (`B_CFST_buildings_tendencia`) | 0,3 |
| Edificios | Frecuencia aditiva por peligro por severidad por capital con tendencia (`B_FSAST_buildings_tendencia`) | 0,3 |
| Contenidos | LightGBM Tweedie del total (`S08h_hogar_F3s2`) | 0,3 |
| Contenidos | Frecuencia aditiva por peligro por severidad LightGBM gamma (`FSA_contents`) | 0,3 |
| Contenidos | Frecuencia aditiva por peligro por severidad GLM con covariables físicas (`FSAXc4_contents`) | 0,4 |

La mezcla aplica después una forma sobre la tasa (en autos abre la dispersión de las tasas con exponente 1,09 y en autos y contenidos usa una elasticidad de exposición de 0,95) y fija el nivel de 2025 con la media de dos factores Tweedie óptimos, el de V23 y el de V24. Los componentes cuyo cociente entre total de 2025 y total de V24 se aparta más de un 1,5 % del de un componente ancla del ramo no entran en la referencia de nivel (regla s17): aportan forma y reparto entre peligros, no nivel. El detalle de cada decisión está en `docs/` y en el registro de decisiones del proyecto (D67 a D89).

## Verificación hecha

Desde los originales, la capa preparada sale con el SHA-256 de las once tablas de la capa preaudit, las bases actuariales y las matrices F0 salen iguales en contenido y las variables dan marcos de modelo idénticos a los originales (matriz de predictores con sus tipos y categorías, etiquetas, offsets y particiones). La mezcla desde los componentes guardados da los dos CSV con el SHA-256 entregado en dos máquinas: el entorno de referencia (Python 3.13, numpy 2.5.3, pandas 3.0.5, pyarrow 26.0.0) y la máquina virtual del participante (Python 3.10.12, numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1). En la segunda, el Parquet de 2025 a precisión completa difiere en el último bit (diferencia relativa máxima 1,4 × 10⁻¹⁵), que desaparece al escribir el CSV; con la versión 1.1 del orquestador esa corrida termina con código 3 (CSV iguales, artefacto intermedio distinto) y no se presenta como éxito. Los controles del paquete (versión 1.1, hallazgo GOV-007 del enjambre de validación) se comprobaron con `herramientas/probar_controles.py`: 45 casos desde la orden de consola, todos con el código de salida esperado, en el entorno de referencia y en la máquina virtual del participante (`docs/controles/`). La reconstrucción completa de componentes y su comparación artefacto por artefacto están en `docs/archivo/semana1/verificacion.md`.

## Control de versiones

Git se inició aquí el 19 de octubre de 2026 y ya está conectado al repositorio privado. El primer commit conserva el paquete de reproducción recibido y las fuentes oficiales. La consolidación posterior añade el expediente y corrige el orquestador Windows; los scripts de modelo y sus pesos permanecen identificados por sus hashes. La historia anterior se conserva por decisiones de solo adición, foro y manifiestos; no se inventaron commits retrospectivos. Para registrar cambios revisados, desde esta carpeta:

```text
git status
git diff
git add <archivos_revisados>
git commit -m "Describir el cambio y su evidencia"
git push
```

El repositorio queda local o privado hasta que el formulario de la parte 2 indique cómo entregarlo: las reglas solo permiten compartir código públicamente en los foros o cuadernos de la competición.

## Límites

La verificación es propia y asistida por IA; no hay todavía revisión humana independiente. V23 y V24 se usaron para elegir pesos, formas y reglas, así que no son una validación independiente de la mezcla final. La etiqueta T0 toma las reservas de caso a su valor del 31 de diciembre de 2024 y no añade IBNER; con una sola valoración no se puede comprobar si esas reservas son suficientes. La tendencia de severidad extrapola un año el crecimiento observado, acotado a ±15 %.


El seguimiento solicitado el 19 de octubre sobre la reproducción completa y el sesgo de reservas está en [COORDINACION_REPRODUCCION_RESERVAS.md](COORDINACION_REPRODUCCION_RESERVAS.md), con inventario y peticiones REP/RES en [el registro común](../../../registro/coordinacion_reproduccion_reservas.json). COD-20261019-113 recibió la respuesta CLA-20261019-004: corrida completa no recuperable según el autor y modelos ajustados no persistidos en el inventario aportado. COD-20261019-114 conserva carencias y observaciones; reproducción completa y sesgo de reservas siguen pendientes. No se ha reentrenado ni enviado a Kaggle para esta coordinación.


[Saneamiento de los quince pendientes](SUBSANACION_PENDIENTES.md): evidencia preparada por ID, hoja privada de capitales, mensajes auténticos vinculados y herramientas de comprobación documental. Manuel Ignacio Rodríguez está designado por el participante; su revisión y decisiones siguen pendientes. La decisión humana posterior acepta solo la corrección técnica de GOV-007; los otros catorce hallazgos siguen pendientes.


### Captura 1.1.1: Pool sin huella

La capa de captura rechaza en modo reproducir los Pool de entrenamiento o validación sin huella completa antes de buscar/cargar modelos. El orquestador1.2 y la receta conservan sus huellas. La prueba acotada consta de14casos con dobles, sin ajuste ni carga real; no acredita toda la reproducción. [Control, criterio y evidencia](../../controles/pool_sin_huella.md).


### Kit identificado de captura 1.1.1

La copia común `privado/kits/captura_1_1_1_20261019/codigo_incorporado` incorpora la capa y el lanzador con versión/SHA explícitos en sus recibos futuros. Los recibos de kit e instalación local ya cotejan ambos campos; no son una ejecución de modelos ni su adopción por la línea de reproducción en la nube. [Guía de incorporación y comprobación](../../controles/kit_captura_1_1_1.md) · [registro común](../../../registro/kit_captura_1_1_1_20261019.json).
