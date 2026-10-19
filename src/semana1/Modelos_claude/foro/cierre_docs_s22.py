"""Cierra la documentación de la tarde: README (cierre de la décima ronda), INFORME 4.9 y CLAUDE.md (tercer motor en autos)."""
import os

def rw(p, fn, crlf=None):
    s = open(p, encoding="utf-8", newline="").read()
    was_crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if was_crlf:
        s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2)
    os.replace(p + ".tmp_claude", p)

def rep1(s, a, b):
    assert s.count(a) == 1, a[:70]
    return s.replace(a, b)

README = "Hackaton/Semana 1/Modelos_claude/README.md"
CIERRE = ("\n### Cierre de la ronda\n\n"
          "- El tercer motor de frecuencia también falla en autos: FS2S_motor da 0,09166 en V23 y 0,08926 en V24 (CFSS: 0,09306 y 0,09100), se aparta −3,86 % del ancla y con la rejilla de la peor de las dos mejoras sube el agregado +0,00003 y +0,00004, por debajo del +0,0001 fijado en CLA-20261018-011 (`experimentos/tercer_motor/robustez_s21_prueba_fs2s_motor.json`). Queda adverso en los tres ramos (cierre de D86).\n"
          "- `intervalos_region.py` añade el remuestreo por región (12 regiones) que usa Codex, con cliente y dirección, la diferencia dentro de cada región y la reserva × 0,75, × 1 y × 1,25. S22 frente a A_G: +0,00165, región [+0,00041; +0,00352], una región negativa; S21 frente a A_G: +0,00198, región [+0,00060; +0,00412] (`experimentos/intervalos_region_s22.json` y `intervalos_region_s21.json`).\n"
          "- Codex reprodujo S22 desde los componentes y lo retiene por adversos puntuales frente a A_G en la cohorte del segundo semestre de 2024 (COD-20261018-062). Autos es el mismo en S20, S21 y S22, y en contenidos ese semestre S22 retrocede menos que S21 (−0,00392 frente a −0,00458).\n"
          "- `mezcla3.py` deja fuera de la referencia de nivel FS2Xc de contenidos y FS2S de autos; S21 y S22 se repiten en el equipo con el mismo SHA-256 después del cambio.\n")
rw(README, lambda s: s.rstrip("\n") + "\n" + CIERRE)
rw(README, lambda s: rep1(s, "Quedan como resultados adversos. Autos (FS2P_motor y FS2S_motor) estaba entrenando al escribir esto.",
                          "Quedan como resultados adversos. Autos (FS2P_motor y FS2S_motor) tampoco pasa; ver el cierre de la décima ronda."))

INFORME = "Hackaton/Semana 1/Evaluacion_integral_claude/INFORME.md"
rw(INFORME, lambda s: rep1(s, "Autos estaba entrenando al escribir esta sección; su resultado se publica en el foro.",
                           "En autos da 0,09166 y 0,08926 y la mejor combinación sube el agregado +0,00003 y +0,00004, por debajo del umbral, así que tampoco entra."))

CLAUDE = "CLAUDE.md"
rw(CLAUDE, lambda s: rep1(s, "y el tercer motor de frecuencia en hogar (LightGBM por peligro de profundidad intermedia con severidad GLM, FS2S_buildings y FS2Xc_contents: ninguna combinación mejora V23 y V24 a la vez; D85).",
                          "y el tercer motor de frecuencia (LightGBM por peligro de profundidad intermedia con severidad GLM): en hogar ninguna combinación mejora V23 y V24 a la vez y en autos sube el agregado +0,00003 y +0,00004 (D85 y cierre de D86)."))
rw(CLAUDE, lambda s: rep1(s, "con IDs CLA-20261018-001 a 013 hasta ahora; el siguiente es CLA-20261018-014.",
                          "con IDs CLA-20261018-001 a 014 hasta ahora; el siguiente es CLA-20261018-015."))
rw(CLAUDE, lambda s: rep1(s, "D86 es la última y la próxima libre es D87;",
                          "D86 y su cierre son lo último de Claude y la próxima libre es D87;"))
rw(CLAUDE, lambda s: rep1(s, "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 15:45 America/Bogota)",
                          "## 13. Modelos, escala de validación y envíos (corte 18 de octubre, 16:30 America/Bogota)"))
rw(CLAUDE, lambda s: rep1(s, "Corte de esta memoria: 18 de octubre de 2026, 15:45 America/Bogota en la sección 13;",
                          "Corte de esta memoria: 18 de octubre de 2026, 16:30 America/Bogota en la sección 13;"))
rw(CLAUDE, lambda s: rep1(s, "la variante S22 sin forma de hogar y D86.",
                          "la variante S22 sin forma de hogar, D86 y su cierre (tercer motor adverso también en autos; Codex retiene S22 por H2)."))
print("ok")
