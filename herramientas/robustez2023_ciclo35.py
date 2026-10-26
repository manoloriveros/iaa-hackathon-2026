"""Corrección de dominio moderada, preservando el fallo de ponderación directa."""
from pathlib import Path
import sys,json,argparse
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026'
sys.path.insert(0,str(R/'src'));sys.path.insert(0,str(ROOT/'Preparación/.cache/parquet-reader'))
from semana2 import modelo_fuente_densidad_templada2023 as m
import robustez2023_ciclo34 as engine
import numpy as np
from scipy.special import expit
OUT=R/'privado/semana2/robustez2023/ciclo35_20261025_v1';PLAN=R/'registro/semana2_robustez2023_ciclo35_plan.json';PREVIOUS=R/'privado/semana2/robustez2023/ciclo34_20261025_v1'
RECIPES=[{'id':'W2-COD-R136','kind':'glm','reference':'W2-COD-R31'},{'id':'W2-COD-R137','kind':'trees','reference':'W2-COD-R32'}];NATURAL={'W2-COD-R136':'W2-COD-R138','W2-COD-R137':'W2-COD-R139'};IDS=[x['id'] for x in RECIPES]+list(NATURAL.values())
engine.m=m;engine.OUT=OUT;engine.PLAN=PLAN;engine.RECIPES=RECIPES;engine.NATURAL=NATURAL;engine.IDS=IDS

class LogitColumn:
 def transform(self,f):return f[['x_ncb_years']].to_numpy()
class FixedLogit:
 def decision_function(self,x):return x[:,0]
 def predict_proba(self,x):
  p=expit(x[:,0]);return np.c_[1-p,p]

def prepare():
 assert not OUT.exists() and not PLAN.exists();OUT.mkdir(parents=True)
 old=engine.read(PREVIOUS/'plan.json');engine.check(old);assert engine.read(PREVIOUS/'report.json')['new_price_fits']==0 and engine.read(PREVIOUS/'combined_weight_preflight.json')['all_pass'] is False
 engine.synthetic()
 # New functional part: nonconstant clipped odds are square-rooted before normalization.
 f=engine.pd.DataFrame({'market':'developed','line':'motor','row_id':['s_SYNTHETIC_DENSITY_'+str(i) for i in range(6)],'year':2023,'is_test':False,'exposure':[.3,.5,.8,1.,.6,.7]})
 for c in m.FEATURES['motor']['numeric']:f[c]=1.
 for c in m.FEATURES['motor']['categorical']:f[c]='A'
 f['x_ncb_years']=np.tile([-4.,0.,4.],2);domain={'line':'motor','held_fold':0,'transformer':LogitColumn(),'estimator':FixedLogit()};w,receipt=m.weights(f,domain);odds=np.exp(f.x_ncb_years.to_numpy());r=np.sqrt(np.clip(odds,.2,5.));original=np.sqrt(f.exposure.to_numpy());expected=original*r/np.average(r,weights=original);assert np.allclose(w,expected,rtol=1e-14,atol=1e-14) and receipt['tempering_power']==.5
 engine.dump(OUT/'tempering_synthetic.json',{'new_price_fits':0,'new_domain_fits':0,'nonconstant_sqrt_clipped_odds_exact':True,'normalizer_fit_only_correct':True,'weights':receipt})
 paths=[ROOT/x['path'] for x in old['sources']]+[Path(__file__),Path(m.__file__),PREVIOUS/'plan.json',PREVIOUS/'report.json',PREVIOUS/'combined_weight_preflight.json',PREVIOUS/'ESS_independent_check.json'];paths=list(dict.fromkeys(paths))
 plan={**old,'id':'S2-ROBUSTEZ2023-CICLO35-v1-20261025','author':'Codex','utc':engine.now(),'forum_prior':'COD-S2-20261025-ROBUSTEZ35-PREVIO','models':RECIPES,'natural_outputs':NATURAL,
 'hypothesis':'C34directdensitycorrectionfailedcombinedESSinallscopes,withoutpricefit. TestONEfixedregularizedcorrectionwithsquare-rootclippedodds(.5strength),trading exactdistributionmatching forboundedvariance with samephysicalmean/capacity. This is a newpostadaptivehypothesis,not a passedC34,not an identified targetdensity ratio or newtargetsupport. No exponentsearch to justreachESS.',
 'weight_rule':'r=sqrt(clip(exp(logit),.2,5));w=sqrt(nominalsourceexposure)*r/weightedmean(r,sqrt(exposure)) oncurrentpricefitrows. Fixedpower.5;rawoddsclip unchanged,effectivefactors[sqrt(.2),sqrt(5)],positiveallrows. No claimthisequalstarget/source density.',
 'tempering_power':.5,'regularization_rationale':'half-strengthlog-densitycorrectionfixedbeforeweightsorprices;variance/biastradeoff,not thresholdrelaxation. Original C34 failedreceipt remains. IfsameESS>=.5fails again,stop;do notsearchpower orchangegate.',
 'outputs':'R136/R137motorfixedsqrt50/50B20;R138/R139natural;homeexactR36,no newinference;weights not selected bytargetorpublicscores','preference_order':IDS,
 'unchanged':'sameESS/sourceveto/primaryR36gain,uncertainty,fold,segment,influencegates;sourceT0/exposure/caseinclusion,source/targetTweedie1.5alpha1andoldtreecapacity,domainmodels andnoC0fit;allfollowoldnumericalengine',
 'sources':[{'path':engine.rel(p),'sha256':engine.sha(p)} for p in paths]}
 engine.dump(PLAN,plan);engine.dump(OUT/'plan.json',plan);print(json.dumps({'plan':engine.rel(PLAN),'real_price_fits_max':30,'synthetic_price_fits':6,'new_domain_fits':0,'new_C0':0,'C34_failed_preserved':True}))

if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('action',choices=['prepare','run']);a=p.parse_args();prepare() if a.action=='prepare' else engine.run()
