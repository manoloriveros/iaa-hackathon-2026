"""Nuevo padre aditivo, ejecución validada de cinco bloques ya conservada."""
from pathlib import Path
import sys,json,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_aditivo2023 as m
import robustez2023_ciclo24 as engine

OUT=R/'privado/semana2/robustez2023/ciclo31_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo31_plan.json'
RECIPES=[{'id':'W2-COD-R120','kind':'glm','source_baseline':'W2-COD-R31'},{'id':'W2-COD-R121','kind':'trees','source_baseline':'W2-COD-R32'}]
NATURAL={'W2-COD-R120':'W2-COD-R122','W2-COD-R121':'W2-COD-R123'}
engine.m=m;engine.OUT=OUT;engine.PLAN=PLAN;engine.RECIPES=RECIPES;engine.NATURAL=NATURAL

def prepare():
    assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
    engine.synthetic()
    paths=[Path(__file__),Path(m.__file__),Path(engine.__file__),R/'src/semana2/modelo_fuente_penalizacion2023.py',R/'src/semana2/modelo_profesor_comun2023.py',R/'src/semana2/modelos_robustos2023.py',R/'src/semana2/modelos_robustos_compuestos2023.py',R/'src/semana2/modelo_transferencia2023_v2.py',R/'src/semana2/evaluar_robustez2023_v2.py',engine.REF,engine.OLD,engine.EXTRA/'report.json',R/'privado/semana2/robustez2023/ciclo30_20261025_v1/report.json']
    paths+=list(engine.EXTRA.glob('*.parquet'))+[engine.BLOCKS/f'{line}.parquet' for line in m.FEATURES]+[engine.BAGS/f'{line}_bag{k}.joblib' for line in m.FEATURES for k in range(5)]+[engine.BASE/f'{line}_fold{k}.parquet' for line in m.FEATURES for k in range(5)]
    plan={'id':'S2-ROBUSTEZ2023-CICLO31-v1-20261025','author':'Codex','utc':engine.now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ31-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
    'hypothesis':'Target GLM corrections C15/C30 do not improve stability; target-only GAM C10 had little effective support. Test standard additive source curves, not previously fitted over the full physical source contract, to reduce dependence on a linear parent without adding emerging coefficients. Original source residual trees and larger alternatives have not resolved influence. This is one fixed additive shape, not a hyperparameter sweep.',
    'source_GLM':'Tweedie1.5 alpha1; same physical columns; curved fields match existing SPLINE list;4quantileknots degree2,constant boundary extrapolation;fitonlymedian/clip.005,.995/scale;other numeric linear;OHEmin100max40dropfirst;region/buildingconstructionexcluded',
    'curved_fields':m.CURVED,'source_trees':'same200depth3leaves8lr.025,min5000L2500L1100,seed2026102506,now residual of additiveGLM;no capacity increase',
    'source_veto':'same frozen C24 filter: eachfamily eachline pooled5sourcefoldfullcostloss <=1.002savedC17samefamily and>=4/5folds inside1.002;all sourcegroup/customer/address disjoint. If globalfamily fails,stop its transfer. Sourceblocks alreadyseen adaptively,notindependentconfirmation.',
    'source_fit_budget':36,'target_fit_budget':30,'real_fit_budget_max':66,'new_C0_fits':0,'new_features':[],
    'adapter':'unchanged minimal freeintercept+newbusiness/regionridge1 in saved five2023emergingfolds;alltarget learning outsideheldfold',
    'outputs':'R120/R121fixedsqrt50/50B20;R122/R123natural;weights not learned',
    'criteria':{'delta_min':.005,'lower_exploratory_min':.0005,'positive_folds_min':4,'segment_harm_max_fullnull':.0005,'after31groups_min':.0005},'primary_reference':'W2-COD-R36',
    'bootstrap':{'replicates':2000,'seed':2026102501,'quantiles':[.0041666666667,.9958333333333]},'preference':['W2-COD-R120','W2-COD-R121','W2-COD-R122','W2-COD-R123'],
    'unresolved':'source/emerging missingness shift and sourceultimate transportability remain;sourceveto cannot establish those;no2024 confirmation',
    '2024_closed':True,'B00_preserved':True,'promotion':False,'adaptive_exploratory':True,'pending_public_CSVs_unchanged':True,
    'source_lineage':'physical2023 source,all original losses/exposures retained;noC0refit;markets never joined as shared policy IDs',
    'sources':[{'path':engine.rel(p),'sha256':engine.sha(p)} for p in paths]}
    engine.dump(PLAN,plan);engine.dump(OUT/'plan.json',plan)
    print(json.dumps({'plan':engine.rel(PLAN),'synthetic_fits':12,'real_fits_max':66}))

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else engine.run()
