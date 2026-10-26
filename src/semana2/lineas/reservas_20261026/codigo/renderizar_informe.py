"""Construye INFORME.md y cifras_informe.json a partir de INFORME.plantilla.md y de los JSON de resultados/.

Marcas de la plantilla:
  {{ruta : formato}}              valor de un JSON de resultados/ (prefijos datos, a..g, ctx, cur; separador /)
  {{=calculo(arg, arg) : formato}} cálculo de CALCULOS de verificar_informe.py
  {{#archivo}}                    huella corta (8…4) del SHA-256 de un archivo de la carpeta del informe
  [[texto||fuente]]               cifra citada de otro documento: se escribe tal cual y se declara su fuente
Cada cifra queda en cifras_informe.json con su ruta o cálculo, su formato, el valor escrito y un fragmento literal del
texto donde aparece; verificar_informe.py las recalcula desde los JSON.

Uso: python3 renderizar_informe.py <carpeta del informe>
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import re
import sys
from pathlib import Path

BASE = Path(sys.argv[1]).resolve()
spec = importlib.util.spec_from_file_location("verificar_informe", BASE / "verificar_informe.py")
V = importlib.util.module_from_spec(spec)
spec.loader.exec_module(V)

plantilla = (BASE / "codigo" / "INFORME.plantilla.md").read_text(encoding="utf-8")
ev = V.cargar(BASE)
PAT = re.compile(r"\{\{(.+?)\}\}|\[\[(.+?)\|\|(.+?)\]\]")
salida, pos, marcas = [], 0, []
largo = 0
for m in PAT.finditer(plantilla):
    salida.append(plantilla[pos:m.start()]); largo += m.start() - pos
    if m.group(1) is not None:
        cuerpo = m.group(1).strip()
        if cuerpo.startswith("#"):
            arch = cuerpo[1:].strip()
            h = hashlib.sha256((BASE / arch).read_bytes()).hexdigest()
            txt = V.fmt(h, "sha")
            marcas.append(("huella", arch, h, largo, largo + len(txt)))
        else:
            expr, f = [x.strip() for x in cuerpo.rsplit(" : ", 1)]
            v = V.calcular(ev, expr) if expr.startswith("=") else V.get(ev, expr)
            txt = V.fmt(v, f)
            marcas.append(("cifra", expr, f, largo, largo + len(txt)))
    else:
        txt = m.group(2)
        marcas.append(("literal", txt, m.group(3).strip(), largo, largo + len(txt)))
    salida.append(txt); largo += len(txt)
    pos = m.end()
salida.append(plantilla[pos:])
texto = "".join(salida)
assert "{{" not in texto and "[[" not in texto, "marca sin resolver"
(BASE / "INFORME.md").write_text(texto, encoding="utf-8")


def contexto(i0, i1):
    """Fragmento de la misma línea alrededor del valor: unas palabras antes y después, sin cruzar saltos de línea."""
    ini = texto.rfind("\n", 0, i0) + 1
    fin = texto.find("\n", i1); fin = len(texto) if fin < 0 else fin
    a = max(ini, i0 - 28); b = min(fin, i1 + 28)
    while a > ini and texto[a - 1] not in " |([«":
        a -= 1
    while b < fin and texto[b] not in " |)]»,;.":
        b += 1
    return texto[a:b]


cifras, literales, huellas = [], [], []
for n, (tipo, x, y, i0, i1) in enumerate(marcas, 1):
    if tipo == "cifra":
        e = {"id": f"c{n:03d}", "formato": y, "valor": texto[i0:i1], "contexto": contexto(i0, i1)}
        e["calculo" if x.startswith("=") else "ruta"] = x
        cifras.append(e)
    elif tipo == "literal":
        literales.append({"id": f"l{n:03d}", "texto": contexto(i0, i1), "valor": x, "fuente": y})
    else:
        huellas.append({"id": f"h{n:03d}", "archivo": x, "sha256": y})
out = {"autor": "Claude (Cowork)", "documento": "INFORME.md", "fuentes": {k: f"resultados/{v}" for k, v in V.FUENTES.items()},
       "descripcion": "Cada cifra de INFORME.md con su ruta o cálculo sobre los JSON de resultados/, su formato y el fragmento literal donde aparece; "
                      "las citas de otros documentos van en literales con su fuente.",
       "cifras": cifras, "literales": literales, "huellas": huellas}
(BASE / "cifras_informe.json").write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
print(f"INFORME.md: {len(texto)} caracteres; {len(cifras)} cifras, {len(literales)} literales, {len(huellas)} huellas")
