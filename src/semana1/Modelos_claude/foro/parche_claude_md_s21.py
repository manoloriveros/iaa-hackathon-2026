"""Actualiza la sección 13 de CLAUDE.md con S21 (D85). Reemplazos exactos, cada uno debe aparecer una sola vez."""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
crlf = "\r\n" in s
s = s.replace("\r\n", "\n")
R = [
("## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 12:30 America/Bogota)",
 "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 14:45 America/Bogota)"),
("Esta sección resume lo que pasó entre D69 y D83, más las entradas nocturnas y de la mañana de Codex (N01 a N15, VAL01 y VAL02).",
 "Esta sección resume lo que pasó entre D69 y D85, más las entradas de Codex hasta N30 y VAL03."),
("(revisión integral de Claude, secciones 4.6 y 4.7 para la línea propia)",
 "(revisión integral de Claude, secciones 4.6 a 4.9 para la línea propia)"),
("con IDs CLA-20261018-001 a 008 hasta ahora; el siguiente es CLA-20261018-009.",
 "con IDs CLA-20261018-001 a 011 hasta ahora; el siguiente es CLA-20261018-012."),
("las frecuencias por peligro con severidad media o por capital (CFS, CFSS) y las redes neuronales.",
 "las frecuencias por peligro con severidad media o por capital (CFS, CFSS), las redes neuronales y, en contenidos, las severidades ampliadas (FSAXc4, CFSXc)."),
("Codex mantiene N01_H como su próximo envío para la ventana que abre el 18 de octubre a las 19:00 de Bogotá y retuvo S16 sin cola (COD-20261018-017).",
 "Con la regla oficial de diez intentos diarios (N30), H y S21 se ensayan antes de la ventana de las 19:00 de Bogotá (00:00 UTC del 19), cuando la cuota se reinicia."),
(", una elasticidad b < 1 en contenidos elegida por V23 y la frecuencia aditiva con severidad GLM en autos (FSAS_motor: +0,00003 y +0,00002 en el agregado, por debajo del umbral de +0,0001; cierre de D84).",
 ", una elasticidad b < 1 en contenidos elegida por V23, la frecuencia aditiva con severidad GLM en autos (FSAS_motor: +0,00003 y +0,00002 en el agregado, por debajo del umbral de +0,0001; cierre de D84), la severidad GLM con covariables físicas en edificios y autos (empeora V23; con diez veces más ridge, edificios empeora en los dos cortes) y el tercer motor de frecuencia en hogar (LightGBM por peligro de profundidad intermedia con severidad GLM, FS2S_buildings y FS2Xc_contents: ninguna combinación mejora V23 y V24 a la vez; D85)."),
("`DECISIONES.md` termina ahora en CRLF y la próxima decisión libre de la serie D es D85; hay que releer su final antes de escribir.",
 "`DECISIONES.md` mezcla finales de línea (Codex añadió N30 en LF); las entradas de Claude van en CRLF, D85 es la última y la próxima libre es D86; hay que releer su final antes de escribir. `device_commit_files` compara `expectedMtimeMs` en milisegundos enteros: con decimales rechaza el archivo aunque no haya cambiado."),
]
for a, b in R:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
i = s.index("Estimación propia vigente de Claude: `S20_claude_propio.csv`")
j = s.index("\n", i)
nuevo = open(sys.argv[2], encoding="utf-8").read().strip("\n")
s = s[:i] + nuevo + s[j:]
if crlf:
    s = s.replace("\n", "\r\n")
tmp = p + ".tmp_claude"
open(tmp, "w", encoding="utf-8", newline="").write(s)
os.replace(tmp, p)
print("ok", len(s), "crlf" if crlf else "lf")
