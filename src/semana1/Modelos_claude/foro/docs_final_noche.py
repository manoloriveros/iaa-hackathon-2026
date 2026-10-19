import os
def rw(p, fn):
    s = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if crlf: s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2); os.replace(p + ".tmp_claude", p)
def rep1(s, a, b):
    assert s.count(a) == 1, a[:70]
    return s.replace(a, b)
R = "Hackaton/Semana 1/Modelos_claude/README.md"
BUL = ("- Las partes de las dos semillas nuevas quedan en `runs/CFS_motor_s45` y `runs/CFSS6_motor` (con `selecciones_v23/sel_CFSS6_motor.parquet`). CFSS6 iguala a CFSS en V23 y V24; en 2025 mueve las predicciones por fila entre −2,2 % y +2,5 % (percentiles 1 y 99) y el total +0,036 %. No hay S22b (CLA-20261018-023).\n"
       "- Nivel de 2025: en edificios la tasa de S22 (492,1 por unidad de exposición) queda un 4,1 % por debajo de la proyección por tendencias de la sección 3 del INFORME (513,0) y en autos un 1,4 % por encima (594,5 frente a 586,4). Es coherente: sin forma, las predicciones de edificios quedan más concentradas y el factor que minimiza la devianza Tweedie queda por debajo del que iguala totales (cociente observado/predicho en V23 de 1,080 frente a 1,001 con forma). No se toca el nivel.\n")
rw(R, lambda s: s.rstrip("\n") + "\n" + BUL)
C = "CLAUDE.md"
rw(C, lambda s: rep1(s, "con IDs CLA-20261018-001 a 022 hasta ahora; el siguiente es CLA-20261018-023.",
                     "con IDs CLA-20261018-001 a 023 hasta ahora; el siguiente es CLA-20261018-024."))
rw(C, lambda s: rep1(s, "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 17:30 America/Bogota)",
                     "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 19:30 America/Bogota)"))
rw(C, lambda s: rep1(s, "la decimocuarta (17:30) añade S22 en el público (0,12988, primer puesto) y D87.",
                     "la decimocuarta (17:30) añade S22 en el público (0,12988, primer puesto) y D87; la decimoquinta (19:30) cierra D87 (semillas de autos sin efecto, nivel de 2025 coherente con la proyección por tendencias) y recoge S30 de la línea B (0,12996)."))
rw(C, lambda s: rep1(s, "Corte de esta memoria: 18 de octubre de 2026, 17:30 America/Bogota en la sección 13;",
                     "Corte de esta memoria: 18 de octubre de 2026, 19:30 America/Bogota en la sección 13;"))
print("ok")
