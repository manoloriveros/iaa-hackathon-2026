"""Cambiar solo el proveedor de tasas del GLM conjunto; conservar ecuaciones."""
from pathlib import Path
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');s=(R/'src/semana2/modelo_region_hogar2023.py').read_text(encoding='utf-8');a='from . import modelo_profesor_comun2023 as core';b='from . import modelo_fuente_mascarada2023 as core';assert s.count(a)==1;s=s.replace(a,b);out=R/'src/semana2/modelo_region_hogar_mascarado2023.py';assert not out.exists();out.write_text(s,encoding='utf-8');print('New joint module: same objective/design;masked-source rate provider;0fits.')
