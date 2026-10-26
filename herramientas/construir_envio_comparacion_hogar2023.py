"""Mismos controles de POST propios, directorio y mensajes distintos congelados."""
from pathlib import Path
R=Path('C:/dev/Hakaton/Hackaton/Repositorio_IAA2026');p=R/'herramientas/enviar_candidatos_robustos2023.py';s=p.read_text(encoding='utf-8')
a="OUT=R/'privado/semana2/robustez2023/entrega_20261025_v1'";b="OUT=R/'privado/semana2/robustez2023/comparacion_publica_hogar_20261025_v1'";assert s.count(a)==1;s=s.replace(a,b)
a="def message(x):return 'Codex '+x['model_id']+' | fixed sqrt pool '+str(x['weight'])+' | train2023 only | '+x['sha256'][:16]";b="def message(x):return 'Codex RESEARCH '+x['model_id']+' | home weight '+str(x['home_weight'])+' | train2023 gates unresolved | '+x['sha256'][:16]";assert s.count(a)==1;s=s.replace(a,b)
p=R/'herramientas/enviar_comparacion_hogar2023.py';assert not p.exists();p.write_text(s,encoding='utf-8');print('Created bounded 2CSV submission helper;preserves readonlyswitch,no scorelookuntilbatchcomplete,uncertainPOSTguard,ownreceipt checks.')
