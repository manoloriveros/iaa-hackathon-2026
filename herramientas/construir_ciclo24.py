"""Crear variantes explícitas desde plantillas conservadas, antes del prerregistro."""
from pathlib import Path
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'

def swap(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)

p=R/'src/semana2/modelo_contrato_fuente2023.py';s=p.read_text(encoding='utf-8')
s=swap(s,'"""Profesores GLM/aditivo con covariables básicas comunes, adaptación mínima."""','"""Mismos predictores físicos de referencia, penalización fuente reducida a 0,1."""')
s=swap(s,"FEATURES['motor']['categorical'].append('x_make_model')\nFEATURES['buildings']['numeric'].append('x_mortgage')\nFEATURES['contents']['numeric']+=['x_works_from_home','x_lodgers']",'# No new covariates: the original physical teacher feature contract is retained.')
s=swap(s,'max_categories=400','max_categories=40')
s=swap(s,"TweedieRegressor(power=1.5,alpha=1.,link='log'","TweedieRegressor(power=1.5,alpha=.1,link='log'")
s=swap(s,'np.asarray(x.T@g).ravel()+est.coef_','np.asarray(x.T@g).ravel()+.1*est.coef_')
out=R/'src/semana2/modelo_fuente_penalizacion2023.py';assert not out.exists();out.write_text(s,encoding='utf-8')

p=R/'herramientas/robustez2023_ciclo22.py';s=p.read_text(encoding='utf-8')
s=s.replace('ciclo22','ciclo24').replace('CICLO22','CICLO24').replace('ROBUSTEZ22','ROBUSTEZ24').replace('2026102522','2026102524')
s=s.replace('modelo_contrato_fuente2023','modelo_fuente_penalizacion2023').replace('contrato_faltante2023_v1','fuente_desarrollado2023_fisica_v1')
for a,b in [('W2-COD-R82','W2-COD-R90'),('W2-COD-R83','W2-COD-R91'),('W2-COD-R84','W2-COD-R92'),('W2-COD-R85','W2-COD-R93')]:s=s.replace(a,b)
s=swap(s,'"""Aporte de atributos contractuales omitidos, cinco bloques fuente y CV2023."""','"""Menor contracción fuente, mismos predictores; cinco bloques antes de CV2023."""')
s=swap(s,",R/'herramientas/preparar_variables_contrato_faltantes2023.py'",'')
s=swap(s,"'hypothesis':'Physical teachers omit contractual make_model,mortgage,works_from_home,lodgers. Shared definitions and300code levels are not proof of transported effects. Test source incremental signal across all5savedsourceblocks before target CV.'","'hypothesis':'Current source main-effect GLM ridge1 remains a normalized population penalty despite626355sourceperiods. Test a fixed tenfold reduction to.1 for possible shape underfit,with unchanged physical variables and smalltreecapacity. Large source size alone doesnot establish lowerbias or transportability;all5sourceblocks must pass beforetarget.'")
s=swap(s,"'availability':'F0_contractual at policyinception,only2023 rows;source-target records never joined;KEY links within each market,alloldcolumnsunchanged'","'availability':'same frozen physical feature contract and temporal limitations asR36;only2023 rows,no new covariates or ID crossmarketjoin'")
s=swap(s,"'new_features':{'motor':['make_model categorical300levels'],'buildings':['mortgage'],'contents':['works_from_home','lodgers']}","'new_features':[]")
s=swap(s,"'source_GLM':'sameTweedie1.5alpha1 main effects;median/clip.005,.995/standardscale;OHEmin100max400dropfirst;region/buildingconstructionexcluded'","'source_GLM':'sameTweedie1.5 alpha.1 main effects;median/clip.005,.995/standardscale;OHEmin100max40dropfirst;region/buildingconstructionexcluded'")
s=swap(s,"   extra=pq.read_table(EXTRA/f'{line}_emerging_extra.parquet').to_pandas()\n",'')
s=swap(s,"    f=m.attach(pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas(),extra);fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)","    f=pq.read_table(BASE/f'{line}_fold{fold}.parquet',filters=[('year','=',2023)]).to_pandas();fit=f[f.fold.ne(fold)].copy();val=f[f.fold.eq(fold)].sort_values(m.KEY).reset_index(drop=True)")
out=R/'herramientas/robustez2023_ciclo24.py';assert not out.exists();out.write_text(s,encoding='utf-8')
print('Created explicit source-alpha.1 module and cycle24 runner; historical templates unchanged.')
