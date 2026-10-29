# Fuente del informe final español

Copia del constructor del informe vigente, con F3c confirmado como definitivo por el participante el 28 de octubre de 2026. `PROCEDENCIA.json` identifica cada original y su SHA-256; `ORIGEN.json` registra la incorporación desde un snapshot seleccionado sin datos. La fuente original es de Claude y las ediciones posteriores mantienen su autoría en el registro editorial. Codex añadió el cierre de F3c y la comparación adversa de F3c-R en las páginas 1 y 5.

El constructor necesita Python con pandas, el archivo privado `prima_comercial_F3c_20ref.csv` y los archivos tipográficos indicados en `style.css`. Estos recursos no se incluyen en Git. En el espacio de trabajo autorizado permanecen junto a los originales, bajo `Hackaton/Semana 2/Claude/informe_final_20261026/fuente`, relativo a la raíz del proyecto. No ejecutar el constructor sin esos recursos ni sustituir sus valores.

La edición comprobada llamó a `build.build()` desde esa carpeta para producir el HTML. Después usó `herramientas/renderizar_informe_editorial.cjs` con Playwright y Chrome local para obtener el PDF y su recibo de maquetación. El renderizador comprueba diez páginas, fuentes cargadas, ausencia de desbordamientos y de solicitudes externas. La revisión visual de las páginas modificadas está registrada en `privado/decision_F3c_final_20261028/verificacion.json`.

`style.css` se copió por separado, sin cambios y con SHA registrado, porque `versionado.py incorporar` excluye esa extensión. Los PDF y HTML generados contienen referencias por fila y permanecen fuera de Git. Este código solo compone el documento; no ajusta modelos ni genera predicciones. No se volvió a entrenar para documentar la decisión.

La decisión vigente está en `registro/semana2_decision_final_F3c_20261028.json` y el PDF se identifica en `registro/informe_final_editorial_actual.json`. Sus limitaciones predictivas y resultados adversos se conservan; la elección del participante no acredita superioridad privada.
