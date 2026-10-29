# Cómo organizo la reproducción de las dos semanas

Entrego dos [notebooks autocontenidos](../notebooks/README.md) para reconstruir mis resultados desde los datos oficiales. En semana 1 genero S30 y aplico la calibración S41; en semana 2 reconstruyo F3c y calculo las veinte primas comerciales. Mantengo las constantes y reglas históricas congeladas durante la reproducción.

| Receta | Entradas | Evidencia local existente |
| --- | --- | --- |
| S30 y S41 | Once archivos del mercado desarrollado | Treinta nodos completados en una ejecución reanudada; CSV finales con las huellas históricas |
| F3c | Archivos desarrollados y emergentes, incluidos gastos y referencias | Cuarenta y ocho etapas correctas en una ejecución reanudada; CSV F3c exacto |

Los archivos, sus huellas y los recibos están identificados en [notebooks_kaggle_actual.json](../registro/notebooks_kaggle_actual.json). Conservo la [guía de semana 1](REPRODUCCION_COMPLETA.md) y la [reconstrucción original de semana 2](REENTRENAMIENTO_ORIGINALES.md) para distinguir los recorridos.

## Qué exige repetirlos

Necesito los datos oficiales y un entorno con las dependencias declaradas. Los notebooks crean una corrida aislada y materializan su código; no descargan archivos de mi equipo. En local configuro las variables de entrada y de salida de la [guía](../notebooks/README.md). Los modelos, bases y registros intermedios quedan en almacenamiento temporal y pueden requerir conservarse para estudiar una interrupción.

No he verificado la ejecución alojada en Kaggle, su tiempo ni su espacio máximo. La primera semana conserva diferencias intermedias, incluidas tres huellas de variables sin causa establecida. Ambas comprobaciones locales tuvieron reanudaciones. No equiparo el CSV exacto con igualdad de toda la cadena ni con una revisión profesional independiente.

## Otros recorridos que conservo

Antes de los notebooks hice una comprobación parcial de factores desde OOF guardadas y una reconstrucción completa posterior de semana 2. Cada una conserva su alcance y su entorno. La [versión anterior](archivo/versiones_previas_20261029/docs/REPRODUCCION_DOS_SEMANAS.md) mantiene esos detalles y los ensayos F3d/F4c, que no sustituyen mi elección definitiva F3c.

Una repetición por otra persona requiere identificar el commit, el entorno, los datos autorizados, las órdenes, las interrupciones y las huellas. La [plantilla de acta](../registro/acta_otro_operador_plantilla.json) sigue siendo una plantilla; no representa una revisión realizada ni una firma. Conservar este límite forma parte de mi documentación de confianza y control.
