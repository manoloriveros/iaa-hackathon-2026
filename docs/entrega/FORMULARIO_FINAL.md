# Requisitos del formulario de entrega final

La entrega conjunta de las dos semanas se completa en el [formulario IAA AI Assisted Hackathon 2026 Final Submission](https://docs.google.com/forms/d/e/1FAIpQLScygWJ4HR6CofbDoOFhGGYQ6vBN7wLj7115DT_iiz-y9KS7bA/viewform). Tiene ocho campos obligatorios: tres de identificación, tres archivos y dos enlaces. Consulta de Codex del 27 de octubre de 2026, 12:54 de Bogotá. Esta revisión registra requisitos y archivos disponibles; el formulario sigue sin completar ni enviar.

El cierre mostrado es **30 de octubre de 2026, 11:59:59 p. m. EDT**, equivalente al **30 de octubre, 10:59:59 p. m. de Bogotá** y al 31 de octubre, 03:59:59 UTC. Coincide con el cierre de la competición de parte 2 registrado en el contrato local.

## Campos y forma de entrega

| Campo exacto | Qué registrar | Formato y condición observada |
| --- | --- | --- |
| Correo | Correo de contacto que el participante confirme para la entrega. | Dirección de correo; obligatorio. |
| Team Name in Kaggle | Nombre exacto del equipo en la competición, conservando espacios y caracteres. | Texto breve; obligatorio. El usuario de la cuenta no sustituye automáticamente al nombre del equipo. |
| Team Members Actual Names | Nombre completo real del participante, que compite solo. | Texto de varias líneas; obligatorio. Confirmar la escritura final antes de cargarlo. |
| Week 1 Prediction File | CSV de la selección final S41 de semana 1. | Un archivo, máximo 100 MB; obligatorio. |
| Week 2 Prediction File | CSV de riesgo F3c, confirmado como definitivo por el participante el 28 de octubre. | Un archivo, máximo 100 MB; obligatorio. La decisión local no acredita una marca final comprobada en Kaggle. |
| Video Demo Link (URL to recorded video) | Enlace al video grabado que pueda abrir el jurado. | URL; obligatorio. Este campo no recibe el archivo del video. |
| Project Write-Up File | Informe conjunto de ambas semanas, con la construcción de prima comercial de las veinte pólizas. | Un archivo, máximo 100 MB; obligatorio. Se propone el PDF revisado. |
| Code Repository Link (Version Control URL) | Enlace al repositorio con el historial y el código de ambas partes. | URL; obligatorio. Debe poder consultarlo el jurado. |

La pantalla dice «archivo compatible», pero no detalla extensiones admitidas. El CSV de predicciones procede del contrato del concurso; el PDF es la propuesta de entrega del proyecto. No se ha probado su aceptación mediante una subida. La pantalla no fija idioma, resolución de video, plataforma de alojamiento o convención de nombres de archivo. Tampoco ofrece campos separados para anexos, tabla de primas comerciales, prompts, elegibilidad, etiqueta Git o SHA del commit.

Los límites de **primeras cinco páginas** y **primeros cinco minutos** proceden de las reglas del concurso, no de una instrucción visible adicional en este formulario. La tabla comercial debe quedar dentro del informe; el CSV de semana 2 conserva primas de riesgo.

## Archivos disponibles

Las rutas siguientes se resuelven desde `C:/dev/Hakaton`. Sus tamaños y hashes se comprobaron en esta consulta, sin recalcular predicciones. El detalle de integridad está en [el registro del formulario](../../registro/formulario_final_actual.json).

| Entregable | Ruta o enlace actual | Situación |
| --- | --- | --- |
| Predicción semana 1 | `Hackaton/Repositorio_IAA2026/privado/envios_S41_S42_20261022/S41_riesgo_ultimo.csv` | 13.014.667 bytes; coincide con la huella de la decisión final S41. |
| Predicción semana 2 | `Hackaton/Repositorio_IAA2026/privado/semana2/claude_mision017_20261025/F3c_2025.csv` | 4.351.233 bytes; SHA intacto. Elección definitiva confirmada por el participante; no se modificó la selección en la interfaz de Kaggle en esta actualización. |
| Informe revisado | `Hackaton/Semana 2/Claude/informe_final_20261026/informe_final_IAA2026_es.pdf` | 235.087 bytes; revisión técnica del 29 de octubre centrada en modelo y validaciones, con F3c definitivo. Diez páginas en total y cinco calificables. |
| Guion español | `Hackaton/Repositorio_IAA2026/docs/entrega/video/GUION_VIDEO_ES.md` | Guion existente; objetivo de 4:45. La grabación, su duración real y el enlace siguen pendientes según su registro. |
| Código | [manoloriveros/iaa-hackathon-2026](https://github.com/manoloriveros/iaa-hackathon-2026) | URL existente; privado según la política del proyecto. Acceso del jurado y publicación posterior al cierre pendientes de comprobación. |

## Preparación y comprobación de la entrega

1. Confirmar correo, nombre exacto del equipo y nombre completo. Google avisa que el nombre, correo y foto de la cuenta se registrarán al subir archivos y enviar el formulario.
2. La elección de semana 2 está cerrada en F3c por decisión del participante del 28 de octubre. Conciliar los dos CSV con las marcas finales de Kaggle y con el modelo descrito en informe y video. Esta actualización documental no acciona la interfaz de Kaggle.
3. Revisar la versión final del informe. Las cinco primeras páginas explican el problema, la arquitectura, las decisiones metodológicas, las validaciones y las primas comerciales; conservan el contraste adverso de F3c-R y el alcance de la evidencia.
4. Grabar el video, medir la duración y obtener una URL que abra el jurado. Usar un alojamiento que permita consultar el video mediante el enlace y comprobar el acceso desde una sesión sin iniciar, si esa es la modalidad elegida. La plataforma y el tipo de visibilidad no están prescritos en la pantalla.
5. Cerrar el código de ambas semanas, crear la etiqueta final y documentar su commit en README o en la documentación de entrega, porque el formulario solo ofrece una URL para el código. Seguir [la guía de control de versiones](../CONTROL_DE_VERSIONES.md); el formulario no pide subir ZIP ni bundle.
6. Cargar un CSV por semana y un informe, pegar los dos enlaces y revisar que las tres cargas terminen sin error. No sustituir el archivo de riesgo por la tabla de primas comerciales.
7. Revisar la respuesta completa y enviarla antes del cierre. Conservar la confirmación y cualquier recibo que el formulario ofrezca; comprobar entonces si permite editar la respuesta. No se ha establecido una política de reenvíos o modificaciones.

La política vigente mantiene GitHub privado hasta el cierre y prevé hacerlo público después. El plazo del formulario coincide con ese cierre: hay que dejar resuelto cómo podrá abrirlo el jurado, sin asumir un margen adicional. Esta consulta no cambia permisos ni publica el repositorio.

## Fuentes

Los campos, la obligatoriedad, el máximo de archivo y la fecha se leyeron en el formulario abierto en Chrome. Su transcripción sin datos de cuenta está en [la fuente archivada](../fuentes/formulario_final_20261027.txt). Los formatos CSV y los límites de evaluación proceden de [las reglas del reto](../../../REGLAS_2026.md) y del [contrato de semana 2](<../../../Semana 2/CONTRATO_SEMANA2.md>). La selección S41, la [decisión definitiva F3c](../../registro/semana2_decision_final_F3c_20261028.json), el PDF y el guion se vinculan mediante sus registros en el índice del formulario. No se volvió a consultar ni enviar el formulario para esta actualización documental.
