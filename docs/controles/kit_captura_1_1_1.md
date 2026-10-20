# Complemento de captura 1.1.1 para el kit de reproducción

La captura 1.1.1 se incorpora mediante un complemento de código identificado, asociado por SHA-256 al `codigo.tar.gz` histórico. Ese archivo base y los recibos anteriores se conservan. El ZIP contiene solo la capa de captura, el lanzador con metadatos, los ayudantes, las pruebas sin ajustes y esta guía. No contiene datos, estimadores ni predicciones.

Desde la carpeta común, crear y comprobar el complemento no ajusta ni carga modelos:

```text
python herramientas/kit_captura.py crear --salida=privado/<complemento_nuevo> --base=<codigo.tar.gz>
python herramientas/kit_captura.py verificar --kit=privado/<complemento_nuevo>
```

`manifiesto.json` identifica el kit base, el ZIP y cada miembro. `recibo_kit.json` registra explícitamente `captura_version=1.1.1` y el SHA-256 completo de `captura.py`. El verificador lee el ZIP sin extraerlo o activar su código y contrasta esos campos con los bytes y el `VERSION` literal de la fuente.

El lanzador `reproducir_capturado.py` también añade `captura_version` y `captura_sha256` a sus recibos futuros, incluidas las salidas de error que ya emitían recibo. La identidad se obtiene por AST y SHA, sin importar la capa. Describe la fuente local al inicio de esa orden; no atribuye esa versión a modelos o eventos históricos ni acredita por sí sola la identidad de toda una corrida.

Para la incorporación por Claude, preparar una copia nueva del kit base, cotejar su SHA con el manifiesto y aplicar allí el complemento. Devolver un recibo fechado con la ruta de la copia, la versión y el SHA de captura, el SHA del ZIP y el resultado del cotejo de sus miembros. La instalación puede comprobarse sin entrenar, cargar estimadores o relanzar la corrida. No se considera instalada fuera de la carpeta común hasta recibir esa evidencia auténtica.

El registro común y la evidencia local se guardan en `registro/kit_captura_1_1_1_20261019.json` y `privado/trazabilidad/kit_captura_1_1_1_20261019/`. La verificación acotada del kit y los recibos no cierra la reproducción completa, reservas, independencia o revisión humana. La aceptación anterior de GOV-007 conserva su alcance específico.
