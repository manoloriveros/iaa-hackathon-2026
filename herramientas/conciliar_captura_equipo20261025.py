"""Lectura actual de cuota y confirmación del score público que aportó el usuario."""
from pathlib import Path
from datetime import datetime,timezone
import json
from kaggle.api.kaggle_api_extended import KaggleApi
ROOT=Path('C:/dev/Hakaton');R=ROOT/'Hackaton/Repositorio_IAA2026';OUT=R/'privado/semana2/robustez2023/mision017_20261025_v1/retoma_20261025_noche_v1';OUT.mkdir(parents=True,exist_ok=True);P=OUT/'cuota_y_score_captura.json';assert not P.exists()
SLUG='iaa-ai-assisted-hackathon-2026-part-2';EXPECTED=.16033;a=KaggleApi();a.authenticate();lim=a.competition_get_submission_limits(SLUG);rows=a.competition_submissions(SLUG,page_size=100) or [];matches=[]
for x in rows:
 try:score=float(x.public_score)
 except (TypeError,ValueError):continue
 if abs(score-EXPECTED)<1e-10:
  matches.append({'ref':x.ref,'date_UTC':x.date.isoformat()+'Z' if x.date else None,'status':str(x.status).rsplit('.',1)[-1],'public_score':score,'bytes':x.total_bytes})
result={'utc':datetime.now(timezone.utc).isoformat(),'competition':SLUG,'limits':{k:getattr(lim,k) for k in ['num_today','num_total','num_allowed_now','limited_by_total']},'expected_public_score_from_human_screenshot':EXPECTED,'matching_public_score_receipts':matches,'other_public_scores_not_emitted_or_used_for_selection':True,'descriptions_filenames_private_scores_not_inspected_or_emitted':True,'2024_data_or_confirmation_artifacts_read':False,'no_POST':True,'new_fits':0,'screen_leaderboard_rank_not_reverified':True}
with P.open('x',encoding='utf8') as h:json.dump(result,h,ensure_ascii=False,indent=2)
print(json.dumps(result))
