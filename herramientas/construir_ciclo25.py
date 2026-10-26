"""Crear receta de producto frecuencia/marca desde flujo conservado de cinco bloques."""
from pathlib import Path
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
def swap(s,a,b):
 assert s.count(a)==1,(a,s.count(a))
 return s.replace(a,b)
s=(R/'herramientas/robustez2023_ciclo24.py').read_text(encoding='utf-8')
s=s.replace('ciclo24','ciclo25').replace('CICLO24','CICLO25').replace('ROBUSTEZ24','ROBUSTEZ25').replace('2026102524','2026102525').replace('modelo_fuente_penalizacion2023','modelo_frecuencia_gamma2023').replace('fuente_desarrollado2023_fisica_v1','fuente_positivos2023_v1')
for a,b in [('W2-COD-R90','W2-COD-R94'),('W2-COD-R91','W2-COD-R95'),('W2-COD-R92','W2-COD-R96'),('W2-COD-R93','W2-COD-R97')]:s=s.replace(a,b)
s=swap(s,'"""Menor contracción fuente, mismos predictores; cinco bloques antes de CV2023."""','"""Producto actuarial frecuencia Poisson por Gamma, cinco bloques antes de CV2023."""')
s=swap(s,"f['T0']=rng.poisson(.3,n)*rng.gamma(3,100,n)","f['T0']=np.round(rng.poisson(.3,n)*rng.gamma(3,100,n),2);f['cost_cents']=np.rint(100*f.T0).astype(np.int64);f['N_positive']=f.T0.gt(0).astype(int);f['N_zero']=0;f['N']=f.N_positive")
s=s.replace("'synthetic_price_fits':len(receipts)","'synthetic_price_fits':sum(x['price_estimator_fits'] for x in receipts)")
s=swap(s,"'hypothesis':'Current source main-effect GLM ridge1 remains a normalized population penalty despite626355sourceperiods. Test a fixed tenfold reduction to.1 for possible shape underfit,with unchanged physical variables and smalltreecapacity. Large source size alone doesnot establish lowerbias or transportability;all5sourceblocks must pass beforetarget.'","'hypothesis':'Repeated aggregateTweedie gains depend on few largecost groups. A standard Poissonpositivecostfrequency times Gamma meanpositiveclaim models separate counting and mark mechanisms while preserving fullcost. All5sourceblocks must pass beforetarget;not changing target or claiming maturity identified.'")
s=swap(s,"'source_GLM':'sameTweedie1.5 alpha.1 main effects;median/clip.005,.995/standardscale;OHEmin100max40dropfirst;region/buildingconstructionexcluded'","'source_GLM':'Poisson positivecostclaimcount/e,weights e,alpha.001;Gamma cost/Npositive onpositivecountperiods,weightsNpositive,alpha.1. Samephysicalsourceonlymedian/clip/scale/OHEmin100max40;allperiodsinfrequency,allnetcostretained'")
s=swap(s,"'source_trees':'same200depth3leaves8lr.025,min5000L2500L1100,seed2026102506 residual onextendedGLM;no capacity increase'","'source_trees':'same priorfrequency200depth3leaves8lr.025,min5000L220L11,seed2026102516 residual onPoissonfrequency only;Gamma mark unchanged,no capacity increase'")
s=swap(s,"'source_fit_budget':36,'target_fit_budget':30,'real_fit_budget_max':66", "'source_fit_budget':54,'target_fit_budget':30,'real_fit_budget_max':84")
s=swap(s,"'synthetic_price_fits':12,'real_fits_max':66", "'synthetic_price_fits':15,'real_fits_max':84")
s=s.replace("'new_price_fits':len(receipts)","'new_price_fits':sum(x['price_estimator_fits'] for x in receipts)")
s=s.replace('new_price_fits=report[\'new_price_fits\']','new_price_fits=report[\'new_price_fits\']')
s=swap(s,"new,ids,len(receipts),reference_id='W2-COD-R36'", "new,ids,sum(x['price_estimator_fits'] for x in receipts),reference_id='W2-COD-R36'")
# The baseline family denotes a pricing comparator, not matching likelihoods of the two components.
s=swap(s,"'source_veto':'eachfamily eachline pooled5sourcefoldfullcostloss <=1.002savedC17samefamily;>=4/5folds relative loss <=1.002. Allsourcegroup/customer/address disjoint and sameheldrows/denominator. Blocks previouslyseen adaptively,notindependentconfirmation.'","'source_veto':'eachfamily eachline pooled5sourcefoldFULLCOSTTweedieloss <=1.002savedC17GLMorpricesmalltree respectively;>=4/5folds relative loss <=1.002. Componentslearnoutsideheldsourcegroups/customer/address. Sameheldrows/denominator;previouslyseen adaptively,notindependentconfirmation.'")
out=R/'herramientas/robustez2023_ciclo25.py';assert not out.exists();out.write_text(s,encoding='utf-8');print('Created explicit PoissonGamma cycle25; templates unchanged.')
