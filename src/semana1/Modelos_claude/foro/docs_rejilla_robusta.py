import os
def rw(p, fn):
    s = open(p, encoding="utf-8", newline="").read(); crlf = "\r\n" in s
    s2 = fn(s.replace("\r\n", "\n"))
    if crlf: s2 = s2.replace("\n", "\r\n")
    open(p + ".tmp_claude", "w", encoding="utf-8", newline="").write(s2); os.replace(p + ".tmp_claude", p)
BUL = ("- Con la regla preinscrita en CLA-20261018-016, `rejilla_robusta.py` busca pesos de hogar sobre S22 que mejoren a la vez V23 y V24 con y sin el 0,1 % superior de T0. No hay ninguna combinación así en edificios ni en contenidos, de modo que no hay S23 y S22 queda como está (`experimentos/log_rejilla_robusta_buildings.txt` y `log_rejilla_robusta_contents.txt`).\n")
rw("Hackaton/Semana 1/Modelos_claude/README.md", lambda s: s.rstrip("\n") + "\n" + BUL)
def f(s):
    a = "con IDs CLA-20261018-001 a 015 hasta ahora; el siguiente es CLA-20261018-016."
    assert s.count(a) == 1
    return s.replace(a, "con IDs CLA-20261018-001 a 017 hasta ahora; el siguiente es CLA-20261018-018.")
rw("CLAUDE.md", f)
print("ok")
