"""Actualiza CLAUDE.md (sección 13 y nota de versiones) con el resultado público de S21, S22 y D86."""
import os
import sys

p = sys.argv[1]
s = open(p, encoding="utf-8", newline="").read()
R = [
("## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 14:45 America/Bogota)",
 "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 15:45 America/Bogota)"),
("Corte de esta memoria: 18 de octubre de 2026, 14:45 America/Bogota en la sección 13;",
 "Corte de esta memoria: 18 de octubre de 2026, 15:45 America/Bogota en la sección 13;"),
("y el tercer motor de frecuencia descartado en hogar.",
 "y el tercer motor de frecuencia descartado en hogar; la decimotercera (15:45) añade el resultado público de S21 (0,12874), la variante S22 sin forma de hogar y D86."),
("Esta sección resume lo que pasó entre D69 y D85, más las entradas de Codex hasta N30 y VAL03.",
 "Esta sección resume lo que pasó entre D69 y D86, más las entradas de Codex hasta N32 y VAL03."),
("(revisión integral de Claude, secciones 4.6 a 4.9 para la línea propia)",
 "(revisión integral de Claude, secciones 4.6 a 4.10 para la línea propia)"),
("con IDs CLA-20261018-001 a 011 hasta ahora; el siguiente es CLA-20261018-012.",
 "con IDs CLA-20261018-001 a 013 hasta ahora; el siguiente es CLA-20261018-014."),
("A las 14:20 de Bogotá el participante autorizó ensayar de inmediato H y S21 con nombres neutrales (N30, COD-20261018-048); sus puntuaciones públicas no estaban al corte.",
 "Con autorización del participante (N30), Codex envió H y S21: H obtuvo 0,12886 y S21 0,12874 en el público, por debajo de A_G (0,12908) y de S09b (0,12889), pese a que S21 superaba a S09b en +0,00255 en V24 (COD-20261018-049). El nivel no explica la inversión (mover S21 un 2,4 %, su diferencia de total con S09b, cambia el D² de V24 entre −0,00031 y +0,00015) y la forma no desplaza el nivel de 2025 (`diagnostico_forma_nivel.py`); la ganancia de S21 frente a S09b sí dependía de la cola (−0,00103 en V23 sin el 0,1 % superior). `S22_claude_propio.csv` (SHA-256 `c21a02e14de4a89f892604239b7cfd9ac4e95ea7d175460a25ba806a5a3541b0`, D86, foro CLA-20261018-012 y 013) es S21 con la forma solo en autos: frente a S09b +0,00164 y +0,00222, y +0,00097 y +0,00114 sin el 0,1 % superior, con los tres ramos positivos; frente a S21 −0,00054 y −0,00033; frente a A_G +0,00165 con IC95 por cliente, dirección y región por encima de cero (`intervalos_region.py`, nuevo); total 211,7 millones de CU. La lectura de su resultado público quedó fijada antes de enviarla: si supera a S21, la forma de hogar probablemente no se traslada a 2025; si no, la inversión viene de otra parte. Codex volvió a A_G como ancla principal por instrucción del participante (COD-20261018-050)."),
("| N01_G | Codex | 0,13751 | 0,12825 | EBM de frecuencia; mejor local, peor público |",
 "| N01_G | Codex | 0,13751 | 0,12825 | EBM de frecuencia; mejor local, peor público |\n| N01_H | Codex | 0,13726 | 0,12886 | Meta geométrica; ensayo N30 del 18 de octubre |\n| S21_claude_propio | Claude | 0,13807 | 0,12874 | Línea propia (D85); ensayo N30, por debajo de S09b pese a +0,00255 en V24 |"),
("Con la regla oficial de diez intentos diarios (N30), H y S21 se ensayan antes de la ventana de las 19:00 de Bogotá (00:00 UTC del 19), cuando la cuota se reinicia.",
 "Con la regla oficial de diez intentos diarios (N30), la cuota se reinicia a las 19:00 de Bogotá (00:00 UTC); a las 14:31 de Bogotá quedaban tres envíos del día."),
("D85 es la última y la próxima libre es D86;",
 "D86 es la última y la próxima libre es D87;"),
]
for a, b in R:
    assert s.count(a) == 1, a[:70]
    s = s.replace(a, b)
tmp = p + ".tmp_claude"
open(tmp, "w", encoding="utf-8", newline="").write(s)
os.replace(tmp, p)
print("ok", len(s))
