# Prima de riesgo para el AI Hackathon IAA 2026 (parte 1)

Este repositorio contiene el código, la receta y las comprobaciones que producen la predicción final de la parte 1 del reto: el coste último esperado de los siniestros de cada periodo de póliza de 2025 en autos, edificios y contenidos, evaluado con el D² Tweedie de potencia 1,5. La selección final es `S30_claude_b` (puntuación pública 0,12996, envío Kaggle 57371361) y el respaldo es `S22_claude_propio` (0,12988, envío 57370117). Las dos salen de los mismos datos preparados y de casi los mismos componentes; S30 cambia la severidad de autos y edificios por una con tendencia anual por peligro y reparte de otra forma los pesos de contenidos.

Con una sola orden se repiten las dos mezclas a partir de los componentes guardados y se comprueba que los CSV coinciden byte a byte con los enviados. Con otra se reentrenan todos los componentes desde las matrices de variables y se compara cada artefacto intermedio con su huella original.

## Qué hay en cada carpeta

| Carpeta o archivo | Contenido |
| --- | --- |
| `reproducir.py` | Punto de entrada único (modos `plan`, `datos`, `componentes`, `todo`, `mezcla` y `verificar`), versión 1.1: termina con código 0 solo cuando todo lo pedido coincide con la receta |
| `receta/receta.json` | Los 36 nodos que van de las variables a los dos CSV: script, argumentos exactos, dependencias, salidas, procedencia y tiempo de referencia |
| `receta/huellas_esperadas.json` | Bytes, SHA-256 y huella de contenido de las 8 entradas, de las 184 salidas originales y de los 3 insumos de exposición del modo mezcla |
| `receta/especificaciones/` | Configuraciones de los modelos LightGBM (`cfg_*.json`) y pesos de las dos mezclas (`spec_s22_propio.json`, `spec_s30.json`) |
| `receta/codigo.json` | SHA-256 de cada script y su comparación con los manifiestos de corrida donde los hay; la sección `paquete` identifica la versión del orquestador y de las herramientas |
| `src/modelos/` | Código de la línea principal de Claude, copiado sin cambios desde donde se ejecutó: variables, modelos, severidades, mezcla y la batería de validación |
| `src/linea_b/` | Código de la línea B de Claude: severidad con tendencia por peligro, regla de nivel para sus componentes y mezcla de S30 |
| `src/datos/` | Etapas desde los originales: productor de la capa preparada de Codex (`n62_codex/`), bases actuariales y matriz F0 |
| `herramientas/` | `huella.py` (huellas de bytes y de contenido), `inventario.py` (huellas esperadas desde las corridas originales), `etapas_datos.py` (raíz de proyecto mínima para las etapas de datos) y `probar_controles.py` (45 casos que comprueban desde la consola que el paquete rechaza faltantes, archivos ilegibles, huellas ausentes y diferencias) |
| `entorno/` | Entorno de referencia (versiones, núcleos, memoria) |
| `docs/` | Verificación de la reconstrucción (`verificacion.md`), evidencia de los casos de control (`controles/`), lista de adaptación para la parte 2 e historia del desarrollo |

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

Las etapas de datos fallan si los originales, la capa, las decisiones congeladas, las bases, las tablas F0 o los bloques del contrato no coinciden con la receta. La capa preparada la produce `src/datos/n62_codex/rebuild_base.py`, el productor de Codex (N62) que aplica las ocho reglas de datos (ID01, EXP01, CAP01, CAT01, AGE01, DUP01, REN00 y PRE00) leyendo solo los originales y `rules.json`. Después corren sin cambios `src/datos/bases_actuariales.py` (D67) y `src/datos/construir_f0.py` (D68), dentro de una raíz de proyecto mínima que el orquestador arma en `--trabajo`, porque los dos localizan sus entradas subiendo hasta `RUTAS_PROYECTO.json`. F0 lee además tres listas congeladas del proyecto que solo alimentan marcas `audit_*`, excluidas de los predictores; se toman de `--decisiones` (por defecto la misma carpeta Semana 1) y se comprueban por SHA-256.

## Qué hace el modelo

La etiqueta de entrenamiento es T0: el coste incurrido neto de los siniestros aceptados asignados a cada periodo de póliza, valorado al 31 de diciembre de 2024 (D67). Los siniestros todavía no reportados no se suman a la etiqueta; entran por la exposición. Cada fila de entrenamiento lleva una exposición efectiva, la nominal multiplicada mes a mes por la completitud de reporte del peligro que sale de un chain-ladder de conteos, y los modelos usan su logaritmo como offset. Al predecir 2025 se usa la exposición nominal, de modo que la predicción queda a nivel último sin un segundo factor de IBNR (D70).

La validación es temporal y tiene tres cortes. V23 entrena con 2021 y 2022, para el boosting con la mitad de calibración de 2023 y mide en la mitad de selección. V24 entrena con 2021 a 2023 con las rondas de V23 multiplicadas por 1,15 y mide en 2024. Producción entrena con 2021 a 2024 con las rondas por 1,3 y predice 2025. Ningún dato de 2025 interviene en el ajuste.

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

Desde los originales, la capa preparada sale con el SHA-256 de las once tablas de la capa preaudit, las bases actuariales y las matrices F0 salen iguales en contenido y las variables dan marcos de modelo idénticos a los originales (matriz de predictores con sus tipos y categorías, etiquetas, offsets y particiones). La mezcla desde los componentes guardados da los dos CSV con el SHA-256 entregado en dos máquinas: el entorno de referencia (Python 3.13, numpy 2.5.3, pandas 3.0.5, pyarrow 26.0.0) y la máquina virtual del participante (Python 3.10.12, numpy 2.2.6, pandas 2.3.3, pyarrow 25.0.1). En la segunda, el Parquet de 2025 a precisión completa difiere en el último bit (diferencia relativa máxima 1,4 × 10⁻¹⁵), que desaparece al escribir el CSV; con la versión 1.1 del orquestador esa corrida termina con código 3 (CSV iguales, artefacto intermedio distinto) y no se presenta como éxito. Los controles del paquete (versión 1.1, hallazgo GOV-007 de la validación de Codex) se comprobaron con `herramientas/probar_controles.py`: 45 casos desde la orden de consola, todos con el código de salida esperado, en el entorno de referencia y en la máquina virtual del participante (`docs/controles/`). La reconstrucción completa de componentes y su comparación artefacto por artefacto están en `docs/verificacion.md`.

## Control de versiones

El desarrollo se hizo en un espacio de trabajo sin git, con un registro de decisiones de solo adición (`Preparación/DECISIONES.md`), un foro entre agentes (`foros/FORO.md`) y un manifiesto con hashes por corrida. Este repositorio se armó el 18 y 19 de octubre con los scripts que produjeron S22 y S30, sin modificarlos; `receta/codigo.json` lista sus hashes. A partir de aquí cada cambio queda en el historial. Para iniciarlo en Windows, desde esta carpeta:

```text
git init
git add .
git commit -m "Repositorio inicial: receta reproducible de S30 y S22 (parte 1)"
```

El repositorio queda local o privado hasta que el formulario de la parte 2 indique cómo entregarlo: las reglas solo permiten compartir código públicamente en los foros o cuadernos de la competición.

## Límites

La verificación es propia y asistida por IA; no hay todavía revisión humana independiente. V23 y V24 se usaron para elegir pesos, formas y reglas, así que no son una validación independiente de la mezcla final. La etiqueta T0 toma las reservas de caso a su valor del 31 de diciembre de 2024 y no añade IBNER; con una sola valoración no se puede comprobar si esas reservas son suficientes. La tendencia de severidad extrapola un año el crecimiento observado, acotado a ±15 %.
