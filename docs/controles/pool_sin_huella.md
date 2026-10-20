# Rechazo de Pool sin huella antes de cargar modelos

Corrección de Codex autorizada por el participante el 19 de octubre de 2026, en respuesta al caso CLA008-CAP03 comunicado en COD-20261019-120. Se aplica a la capa de captura, versión 1.1.1, sin modificar la receta ni el orquestador de reproducción 1.2.

En modo `reproducir`, el envoltorio de CatBoost comprueba los Pool de entrenamiento y validación antes de calcular la clave o consultar un estimador. Recorre también listas, tuplas, diccionarios y argumentos posicionales. Si falta la huella de `X`, `y` o `resto`, o tiene un formato inválido, registra `pool_sin_huella` con `rechazado=true` y lanza `NoHayEstimador`. Así se detiene un Pool construido antes de instalar la captura. No se intenta reconstruir una huella incompleta a partir de sus dimensiones.

La prueba propia contiene diez casos adversos y cuatro controles. Los diez rechazos ocurrieron con cero llamadas a la búsqueda de metadatos, a `load_model`, al ajuste original y a los parámetros o getters del Pool. Los cuatro controles alcanzaron un doble de búsqueda que interrumpe antes de leer archivos o cargar modelos. Se importó el módulo completo y se usó su envoltorio real con dobles de Pool y modelo; no se importó CatBoost, LightGBM o torch. No es una reproducción con modelos reales ni una prueba del CLI completo.

El primer intento quedó interrumpido al escribir el primer evento en el directorio temporal del sandbox. No completó ningún caso ni buscó modelos. Se conserva el script de ese intento y la incidencia. La batería posterior usa eventos persistentes dentro de `privado`, con los mismos casos, criterio y fuente de captura.

Evidencia:

- Plan: [registro/correccion_pool_previo_20261019_plan.json](../../registro/correccion_pool_previo_20261019_plan.json).
- Registro final: [registro/correccion_pool_previo_20261019.json](../../registro/correccion_pool_previo_20261019.json).
- Batería sin ajustes: [herramientas/probar_pool_sin_huella.py](../../herramientas/probar_pool_sin_huella.py).
- Recibo privado: `privado/trazabilidad/correccion_pool_previo_20261019/verificacion.json`, junto a eventos, fuentes antes/después, parche e incidencia.

Para comprobar un cambio posterior, con las dependencias de NumPy y pandas disponibles, usar un destino nuevo:

```text
python herramientas/probar_pool_sin_huella.py --salida=privado/<nueva_revision>/verificacion.json
```

La corrección cierra el caso acotado CLA008-CAP03 en esta fuente. Las pruebas históricas se conservan y no se suman a estos catorce casos. No acredita la corrida completa, otra persona o entorno, reservas suficientes ni revisión actuarial. La aceptación humana previa de GOV-007 conserva su alcance específico y no se extiende a esta capa nueva. No hubo ajuste, inferencia, replay, cambio de predicciones, envío a Kaggle ni operación remota.
