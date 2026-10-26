# Reentrenamiento completo desde originales

Codex, 26 de octubre de 2026. El participante pidió continuar el reentrenamiento completo en un entorno limpio, sin enviar nada a Kaggle. Esta corrida es una reconstrucción técnica del flujo histórico; no cambia la selección ni se presenta como revisión profesional independiente.

El estado de ejecución se registra en `registro/reentrenamiento_originales_actual.json`. Las corridas y todos los archivos por fila permanecen en `privado/reentrenamiento_completo_20261026/`. La reproducción parcial anterior desde OOF guardadas se conserva y tiene un alcance distinto.

## El mapa que faltaba enlazar

| Capa | Insumos de esta corrida | Salida que consume la siguiente |
| --- | --- | --- |
| MLind | Originales de ambos mercados; preparación, clima e historia originales | Bases y ventanas de historia reconstruidas |
| T2b | Desarrollado 2021-2023 o 2021-2024; folds y parámetros congelados | Predicciones dev, hold, pcv y prod; seis modelos fuente nuevos |
| C1 | Predicciones PCV y producción nuevas | CSV MLind 2025, sin tendencia |
| A1 | Preparación y exposición efectiva propias de esa línea, desde originales | Nueve modelos sin F1, nueve con F1 y tres del contraste histórico |
| A1 designada | Modelos nuevos, tres semillas y nivel neutral por ramo | A1fixF1b3n 2025 y A1/R0 de 2024 |
| M017 | OOF nuevas, las dos producciones nuevas y constantes públicas históricas | Mezcla 50/50, F, F2, final_creible, F3c y F3d |
| FSp | Conteos desde originales y scripts `fsp_light` originales | Frecuencia, severidad y completitud por peligro para histórico y producción |
| F4c | Componentes FSp nuevos y la cadena M017 nueva | CSV F4c para cotejo, sin envío |

La unidad T2b hace seis ajustes internos para fijar rondas y seis refits completos. A1 añade 21 ajustes internos y 21 refits. FSp añade 60 ajustes internos y 60 refits: 15 peligros, dos familias y dos ámbitos. Las calibraciones de nivel/factores forman parte de la receta histórica; no se confunden con árboles fuente nuevos. No se entrenan variantes T1/T3, ni se prueban semillas o regularizaciones adicionales.

## Qué se conserva y qué se restauró

Los scripts originales de Claude se extraen del commit `40b3100`, sin tomar versiones posteriores concurrentes. La preparación inicial usa `MLIND_RAIZ`; las rutas personales de las otras líneas se sustituyen únicamente en copias privadas. Las fuentes originales quedan intactas. Los planes preinscritos son `registro/reentrenamiento_originales_plan.json` y `registro/reentrenamiento_cadena_plan.json`.

Hay dos carencias de código histórico que se restauran expresamente:

- El generador de la curva global REP-N2 no aparece entre las fuentes recibidas. La restauración usa la expresión de `conf_insumos.py`, con el mismo coste topado al percentil 99,5 y riesgo inverso por peligro, retirando solo la restricción de ocurrencias hasta 2023. La curva de confirmación conserva esa restricción. No se afirma haber recuperado el generador perdido.
- La A1 de confirmación de autos que consume la cadena histórica se produjo antes de ID01. Solo para reproducir ese ancestro se habilita el cruce sin rellenar ceros, con la ausencia de clientes documentada. La producción A1 mantiene la corrección ID01. La fuente anterior no está localizada; esta restauración debe cotejarse por claves, sin presentarla como una copia recuperada del original.

FSp se reconstruye con `fsp_light.py` y `fsp_light_prod.py` del paquete original, que sí se encontraron. La familia FSp de `transfer2.py` y las recuperaciones posteriores de Codex tienen otra receta y no se sustituyen por esos archivos.

Los factores aprendidos de las sondas históricas son constantes congeladas, con procedencia y SHA. Se recalculan los factores locales de la receta, pero no se realizan nuevas consultas o sondas públicas. Las guardas que exigían los bytes del archivo histórico pasan a un cotejo externo; las guardas de soporte, claves, finitud y las paradas estadísticas permanecen. Así se pueden medir diferencias de entorno sin inyectar la predicción anterior para hacer pasar el flujo.

## Entorno y aislamiento

Se creó un venv nuevo con `include-system-site-packages = false`, Python 3.12.14 y las versiones declaradas de las bibliotecas: NumPy 2.5.3, pandas 3.0.5, PyArrow 26.0.0, LightGBM 4.7.0, SciPy 1.18.1 y scikit-learn 1.9.1. El entrenamiento histórico declaró Python 3.13: esta diferencia de intérprete se conserva como límite del cotejo, sin llamarlo el mismo entorno.

El espacio de cálculo comienza solo con código congelado, copias de los Parquet originales y metadatos agregados de la receta pública. Los directorios de modelos y predicciones están vacíos antes del primer ajuste. Cada original se verifica por SHA; el preparador MLind vuelve a comprobar su contrato de huellas. Los procesos hijo corren con `-I -X utf8`, sin credenciales heredadas, con dos hilos y sus temporales dentro de la corrida.

El bloqueo de red y de lecturas ajenas al entorno/corrida impide usar silenciosamente una predicción histórica. También se bloquea escribir sobre las copias de originales. La prueba de los tres controles se conserva en `corrida/verification_isolation.json`.

## Ejecución y comprobación

Las órdenes se dan desde la raíz del repositorio y con el Python del entorno nuevo:

```powershell
python -X utf8 herramientas/reentrenar_desde_originales.py preparar --trabajo privado/una_corrida_nueva
python -X utf8 herramientas/reentrenar_desde_originales.py correr --trabajo privado/una_corrida_nueva
python -X utf8 herramientas/completar_reentrenamiento_cadena.py preparar --trabajo privado/una_corrida_nueva
python -X utf8 herramientas/completar_reentrenamiento_cadena.py correr --trabajo privado/una_corrida_nueva
python -X utf8 herramientas/comparar_reentrenamiento_originales.py --trabajo privado/una_corrida_nueva --salida privado/cotejo_nuevo.json
```

Los preparadores exigen destinos nuevos y nunca borran intentos anteriores. Cada etapa guarda orden, duración, código de salida y SHA de log/salidas. Los bloqueos identifican los procesos propios. Una etapa fallida se conserva para diagnosticarla; no se repite una etapa completada. La segunda unidad empieza después de que termine T2b y requiere su recibo final correcto.

El comparador abre los históricos en un proceso separado. Informa igualdad de claves, orden, bytes, valores, máximas diferencias absolutas/relativas y concordancia numérica con `rtol=1e-10, atol=1e-9`, fijadas antes del cotejo. Las salidas CSV de seis decimales se informan además por igualdad exacta y diferencia máxima. No se retocan parámetros para mejorar el cotejo ni se confunde una diferencia de redondeo con un cambio de modelo demostrado.

Esta comprobación no entrena con una nueva partición, no vuelve a seleccionar modelos con 2024 y no acredita su generalización privada. La reproducción por otra persona continúa siendo un pendiente separado.
