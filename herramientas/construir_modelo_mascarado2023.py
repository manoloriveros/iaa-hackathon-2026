"""Mismo GLM físico ridge1 y residual pequeño; solo cambia vista de entrada."""
from pathlib import Path
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');p=R/'src/semana2/modelo_fuente_penalizacion2023.py';s=p.read_text(encoding='utf-8')
for a,b in [('"""Mismos predictores físicos de referencia, penalización fuente reducida a 0,1."""','"""Profesores físicos de referencia sobre una vista de medición con más ausentes."""'),("TweedieRegressor(power=1.5,alpha=.1,link='log'","TweedieRegressor(power=1.5,alpha=1.,link='log'"),('np.asarray(x.T@g).ravel()+.1*est.coef_','np.asarray(x.T@g).ravel()+est.coef_')]:
 assert s.count(a)==1,a;s=s.replace(a,b)
p=R/'src/semana2/modelo_fuente_mascarada2023.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('Created frozen reference-price specification,alpha1,max40,unchangedtreecapacity;0fits.')
