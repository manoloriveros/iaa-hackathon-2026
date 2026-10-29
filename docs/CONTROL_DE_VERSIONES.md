# Cómo mantengo y entrego el código

Uso Git para conservar el desarrollo de las dos semanas, identificar el código de cada entrega y explicar qué cambió. La rúbrica del concurso pide un repositorio estructurado con control de versiones; por eso mi entrega incluye la historia y las instrucciones de reproducción, además de los archivos finales. Mantengo una [versión inglesa de esta guía](VERSION_CONTROL.md).

## Mi criterio de versionado

Agrupo los cambios por tema y conservo su autoría. En cada commit indico las referencias del trabajo, la asistencia de IA y el estado real de revisión humana. No cambio fechas para simular un registro contemporáneo ni reescribo la historia. La reconstrucción realizada el 26 de octubre conserva sus límites: recuperó versiones finales de archivos y no todas sus revisiones intermedias.

Antes de asociar un CSV a un envío, identifico el commit del código que lo produjo y su estado de trabajo. La herramienta [versionado.py](../herramientas/versionado.py) permite auditar, incorporar fuentes y emitir ese sello. Las copias de código importadas conservan su procedencia; los resultados históricos siguen ligados a sus versiones y huellas originales.

## Lo comprobado para mi entrega

Mi paquete `entrega-codigo-20261029` reúne los dos notebooks, sus recetas, el código de ambas semanas y la documentación vigente. Mantengo las propuestas anteriores en `docs/archivo`, con su mapa de rutas y versiones. En el [registro de sincronización](../registro/sincronizacion_github_actual.json) identifico la revisión de contenido y la confirmación remota.

La consulta anterior, conservada en [revision_entrega_actual.json](../registro/revision_entrega_actual.json), describía el remoto del 26 de octubre y no esta versión. Conservo esa fotografía como evidencia fechada.

Mi política mantiene el repositorio privado hasta el cierre de la parte 2 y prevé abrirlo después con MIT. Antes de enviar el formulario debo resolver el acceso del jurado. No doy por hecho que una persona pueda abrir una URL privada ni que disponga de un plazo adicional después del cierre.

## Qué incluyo y qué mantengo fuera

Incluyo código, notebooks sin salidas, configuración congelada, documentación, licencia y trazabilidad que pueda compartirse. Mantengo fuera los datos del concurso, predicciones por fila, modelos entrenados, credenciales y conversaciones privadas. La guía [NOTICE.md](../NOTICE.md) distingue mi licencia de las licencias de datos, fuentes y paquetes.

Uso la guardia de contenido y los hooks como controles automáticos. Sus resultados tienen fecha y alcance; no sustituyen la revisión de lo que efectivamente se va a publicar.

## Cómo compruebo el estado

Desde la raíz del repositorio puedo inspeccionar el estado sin entrenar ni enviar:

```powershell
git status --short
git log -5 --format=fuller
git tag --list
python herramientas/versionado.py auditar
```

Estas órdenes son de inspección. Las acciones de sincronización y publicación se registran aparte. Conservo el diagnóstico y el procedimiento detallado del 26 de octubre en la [versión anterior](archivo/versiones_previas_20261029/docs/CONTROL_DE_VERSIONES.md).

Las fuentes oficiales son [Submissions](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/overview/submissions) y [Evaluation](https://www.kaggle.com/competitions/iaa-ai-assisted-hackathon-2026-part-2/overview/evaluation). La etiqueta final es una medida de trazabilidad de mi proyecto; el formulario exige la URL del repositorio, no un campo separado para la etiqueta o el SHA.
