# Reproducción y pendientes de la entrega conjunta

Codex, 26 de octubre de 2026. Esta guía distingue la reproducción realizada de los pasos que todavía requieren trabajo o una persona distinta. El corte inicial se conserva en [reproduccion_m017_actual.json](../registro/reproduccion_m017_actual.json). El reentrenamiento posterior completo de semana 2 terminó y se verificó: [guía desde originales](REENTRENAMIENTO_ORIGINALES.md) e [índice actual](../registro/reentrenamiento_originales_actual.json). F3c, F3d y F4c nuevos coinciden con los CSV históricos; la reproducción por otra persona sigue pendiente.

## Corte inicial: comprobación parcial desde OOF guardadas

| Objeto | Comprobación realizada | Alcance pendiente |
| --- | --- | --- |
| S41 | Código y factores extraídos de la etiqueta `parte1-entrega-final-S41`; CSV exacto y diez controles de entrega aprobados | Usa el S30 guardado. No repite el entrenamiento completo de semana 1 |
| Etiquetas de semana 2 | Reconstruidas desde los Parquet originales con `etiquetas.py` de Claude; T0 total 27.997.991,57 CU | Esa igualdad agregada no sustituye un cotejo nuevo de todas las filas ni acredita último observado |
| F3c | Factores reaprendidos y CSV exacto en un entorno Python nuevo, con OOF guardadas | No se volvieron a entrenar los árboles fuente ni a generar sus OOF |
| F3d | La misma comprobación; CSV exacto con K=60 en contenidos y K=300 en autos | La igualdad no acredita su mejora privada ni su admisión como final |
| F4c | SHA histórico, esquema, 209.063 filas, orden, cobertura de test, unicidad y valores válidos | Reproducción del constructor pendiente de las tablas FSp históricas exactas, incluidas las de producción |

La dependencia `f3_eval.py` se encontró en los archivos recibidos y se incorporó a Git conservando su procedencia. El diagnóstico P20 anterior se conserva como corte histórico. `lib26.py` original permanece intacto; el adaptador cambia únicamente sus dos rutas absolutas en una copia privada. Windows requiere además UTF-8 explícito: con la codificación predeterminada, el corte por el comentario acentuado de `construir_F3b.py` fallaba y seguía hasta una lectura que no correspondía. Se conserva ese primer intento y su log.

## Cómo repetir la comprobación de factores

El código está en [reproducir_m017_local.py](../herramientas/reproducir_m017_local.py), con el [plan previo](../registro/reproduccion_m017_plan.json). Los datos del concurso, OOF y predicciones no se redistribuyen con el repositorio. El operador necesita acceso autorizado a los originales y a los insumos privados que enumera `bindings()`. El manifiesto de la corrida guarda origen y SHA de los 37 archivos; los nombres por sí solos no prueban equivalencia.

Usar Python 3.12.14 en un entorno virtual nuevo, sin paquetes heredados, e instalar [requirements_reproduccion_m017.txt](../receta/requirements_reproduccion_m017.txt). Desde la raíz del repositorio, pasando el ejecutable de ese entorno:

```powershell
python -X utf8 herramientas/reproducir_m017_local.py preparar --trabajo "privado/reproduccion_m017/otro operador"
python -X utf8 herramientas/reproducir_m017_local.py etiquetas --trabajo "privado/reproduccion_m017/otro operador"
python -X utf8 herramientas/reproducir_m017_local.py factores --trabajo "privado/reproduccion_m017/otro operador"
python -X utf8 herramientas/reproducir_m017_local.py candidatos --trabajo "privado/reproduccion_m017/otro operador"
```

La preparación exige una carpeta nueva, copia los insumos y compila todos los scripts sin ajustarlos. La ejecución usa `-I -X utf8`. No consulta Kaggle ni calcula puntuaciones nuevas. Cada salida se coteja por SHA completo; una diferencia detiene la secuencia. Los intentos fallidos conservan su recibo y las etapas completadas no se repiten. Las rutas de esta herramienta se resuelven desde su archivo, no desde un directorio personal de Claude.

El entorno nuevo pertenece a esta comprobación parcial. No se declara equivalente al entorno de entrenamiento original de todos los modelos ni reemplaza `requirements.txt` de semana 1.

## Brecha inicial y cierre posterior desde originales

La reproducción completa de semana 1 tiene su evidencia histórica y sus diferencias en [REPRODUCCION_COMPLETA.md](REPRODUCCION_COMPLETA.md). No se repitió por cambios documentales.

La brecha inicial consistía en enlazar todos los ancestros T2b/A1/FSp, restaurar las piezas faltantes y generar las predicciones sin leer las anteriores. Quedó resuelta en la corrida posterior de 57 etapas, con 87 modelos finales nuevos. Los datos originales, las adaptaciones privadas de rutas, las dos restauraciones explícitas, el entorno y las diferencias internas se documentan en [REENTRENAMIENTO_ORIGINALES.md](REENTRENAMIENTO_ORIGINALES.md). Las constantes públicas históricas permanecen congeladas; no hubo nuevas sondas.

## Reproducción por otra persona

Sigue pendiente. El mismo asistente en otro entorno hace una comprobación propia. Una persona distinta debe disponer de acceso permitido a los datos, clonar un commit identificado y documentar su entorno, insumos, órdenes, duración, fallos y hashes de salidas. Puede usar la [plantilla de acta](../registro/acta_otro_operador_plantilla.json), que no contiene una firma ni una revisión realizada.

El acta separa repetir factores desde OOF, reentrenar toda la cadena y revisar la idoneidad actuarial. Aprobar uno no acredita los otros. Las restricciones de colaboración del concurso deben comprobarse antes de compartir acceso con alguien ajeno al participante; esta guía no contacta a terceros ni les concede acceso.

## Decisiones vigentes del participante

F3d y F4c se revisan y preparan, sin envío o cambio de selección. La regla v4 queda como antecedente para una futura decisión, no como autorización de envío ni cierre de las guardas comunes de selección. Su ventaja privada esperada depende de supuestos; F3d conserva la sensibilidad a clientes influyentes y la reproducción exacta de F4c no acredita por sí misma una mejora privada.

El inglés queda diferido hasta que la versión española sea definitiva. El informe español anterior y sus PDF se conservan como corte fechado: su frase sobre `f3_eval` ausente queda superada por esta evidencia y tendrá que actualizarse al cerrar la siguiente edición completa. No se atribuye aprobación humana general.

## Cotejo posterior de alcance, 26 de octubre

El [cierre de doce pendientes](semana2/CIERRE_DOCE_PENDIENTES_F3C.md) agrega igualdad por fila de las 109.296 etiquetas históricas, cuatro contrastes de receta residual, cinco archivos de intervalos guardados y un grafo de nueve nodos. No reentrena todos los ancestros A1/T2b ni FSp. Los controles adversos protegen los factores y niveles nuevos; la mezcla de peligros, categorías y folds heredados conservan los límites allí identificados. La puerta `herramientas/puerta_uso_F3c.py` conserva las restricciones de ese corte y no se modifica por esta reproducción. La nueva evidencia cierra el reentrenamiento de la cadena histórica desde originales, descrito en la guía posterior; no cierra la reproducción por otra persona, la revisión profesional ni las guardas de selección.
