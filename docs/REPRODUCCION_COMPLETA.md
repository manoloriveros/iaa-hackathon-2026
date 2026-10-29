# Cómo reproduzco S30 y la entrega S41

Mi entrada principal es el [notebook de semana 1](../notebooks/week1_developed_market.ipynb). He integrado en él la preparación, el código y la configuración para reconstruir la mezcla S30 desde los once archivos oficiales y aplicar después la calibración de nivel S41. No necesito cargar modelos o predicciones anteriores para esa ruta.

Conservo también el ejecutor original [reproducir.py](../reproducir.py), su [receta](../receta/) y la documentación extensa de las comprobaciones históricas en la [versión anterior de esta guía](archivo/versiones_previas_20261029/docs/REPRODUCCION_COMPLETA.md).

## Entradas, entorno y salidas

Necesito acceso permitido a los once Parquet del mercado desarrollado. En Kaggle adjunto los datos oficiales; en local indico la carpeta con `IAA_W1_DATA`. La [guía de notebooks](../notebooks/README.md) explica la selección de entradas y el espacio de trabajo. Uso las versiones de referencia de [requirements.txt](../requirements.txt); Torch corresponde al respaldo histórico S22 y no es necesario para la ruta final S30/S41 del notebook.

El entorno histórico declarado fue Ubuntu, Python 3.13.16, dos núcleos y 8 GB. No lo convierto en una garantía de memoria o duración en otra máquina. La receta es larga y su ejecución alojada en Kaggle sigue sin acreditarse.

La cadena prepara los datos, construye la base actuarial y F0, genera los componentes, forma S30 y aplica los factores congelados de S41. El notebook conserva los controles de integridad y compara el CSV final con su huella histórica. Los resultados por fila permanecen privados.

## Qué quedó reproducido

La ejecución local reanudada completó los 30 nodos de S30 y produjo los CSV S30 y S41 con sus huellas históricas. La F0 conserva la reconstrucción de CAP01 y de una marca de confirmación inferida retrospectivamente. Esa inferencia reproduce el campo de auditoría de este conjunto, pero no recupera el proceso original de decisiones y no la uso como predictor.

El ejecutor devolvió código 3 por 160 diferencias intermedias. Las comparaciones registradas incluyen diferencias numéricas muy pequeñas en arreglos y tablas de predicción, y tres huellas de tablas de variables cuya causa no se estableció. Que el CSV coincida no elimina esas diferencias. La ejecución tuvo interrupciones y reanudaciones; no la presento como Run All ininterrumpido ni como reproducción independiente.

El [registro de notebooks](../registro/notebooks_kaggle_actual.json) identifica archivos, ejecuciones y recibos. Las verificaciones anteriores del ejecutor original conservan sus propias fechas y alcances en el archivo; no mezclo sus contadores con los del notebook.

## Ruta original del repositorio

Para inspeccionar el plan sin entrenar:

```text
python reproducir.py plan --objetivo=S30
```

Para reconstruir desde originales, en una ejecución de modelado expresamente autorizada:

```text
python reproducir.py todo --objetivo=S30 --semana1=<carpeta_semana1> --originales=<carpeta_parquet> --trabajo=<carpeta_nueva> --continuar-si-difiere
python reproducir.py verificar --trabajo=<carpeta_nueva>
```

La calibración S41 se documenta en [MODELO_FINAL_S41.md](MODELO_FINAL_S41.md) y en [regenerar_s41.py](../herramientas/regenerar_s41.py). Esa herramienta original necesita las rutas e insumos que declara; para una reproducción autocontenida de las dos entregas uso los notebooks.

La reproducción de semana 2 está en [REENTRENAMIENTO_ORIGINALES.md](REENTRENAMIENTO_ORIGINALES.md). Una revisión actuarial independiente y una repetición por otra persona siguen siendo alcances distintos de mis comprobaciones asistidas por IA.
