# Documentación de los datos de la primera semana

La guía consolidada recoge el trabajo con los datos hasta D61, CAP06R y protocolo 1.10. [Leer el dossier](runs/dossier_20261017T013104Z_47591209/informe.html) o [abrir la versión editable](runs/dossier_20261017T013104Z_47591209/DOCUMENTACION_DATOS.md).

Incluye fuentes, once tablas, relaciones, diccionario de 107 campos, reglas y motivos, linaje de las dos ramas, casos, verificaciones, uso de IA y 58 controles de seguimiento. [Diccionario consultable](runs/dossier_20261017T013104Z_47591209/diccionario.html) · [Validaciones y pendientes](runs/dossier_20261017T013104Z_47591209/validaciones.html) · [Registro de fuentes](runs/dossier_20261017T013104Z_47591209/fuentes.html).

La base conserva 1.454 capitales pendientes; la rama retrospectiva CAP06R conserva 419 y 3.108 correcciones acumuladas, 1.035 de ellas retrospectivas. Los originales y los índices de datos permanecen intactos. El dossier es una fotografía de documentación, no otra capa de datos ni aprobación para modelar. D59 cubre CAP05R; AGE01 fija una convención de edad y su evidencia deja dos diferencias sin explicar.

[current_run.json](current_run.json) identifica esta versión. Los datos se consumen por los índices de Limpieza, no por este índice documental. Las fuentes mutables se copiaron antes de actualizar memoria. El gráfico se inspeccionó como imagen; la vista automatizada HTML fue bloqueada por política de file://. La estructura, enlaces y lógica de búsqueda tienen controles propios.

Para crear otra fotografía sin transformar datos, ejecutar collect_documentation.py, pasar la carpeta generada a write_dossier.py y verify_documentation.py y revisar el contenido antes de un nuevo cierre. Los recolectores actuales fijan el corte CAP06R y las reglas documentadas: adaptar y versionar el corte si avanzan los datos. No ejecutar record_documentation.py sobre una corrida cerrada o reutilizar el índice de esta versión para sobrescribirla.
