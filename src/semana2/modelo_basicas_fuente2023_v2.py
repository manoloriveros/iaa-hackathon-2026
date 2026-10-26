"""Mismo modelo; enlace idempotente solo si las columnas existentes son exactas."""
from .modelo_basicas_fuente2023 import *
def attach(frame,extra):
 old.base.require(not extra.duplicated(KEY).any(),'Extras repetidos')
 cols=KEY+[c for c in extra if c.startswith('x_')]
 overlap=[c for c in cols if c not in KEY and c in frame.columns]
 if overlap:
  audit=frame[KEY+overlap].merge(extra[KEY+overlap],on=KEY,validate='one_to_one',how='left',suffixes=('_existing','_origin'),indicator=True)
  old.base.require(audit['_merge'].eq('both').all(),'Faltan claves del origen')
  for c in overlap:
   a=audit[c+'_existing'];b=audit[c+'_origin'];old.base.require((a.eq(b)|(a.isna()&b.isna())).all(),'Valor divergente: '+c)
  cols=[c for c in cols if c not in overlap]
 out=frame.merge(extra[cols],on=KEY,validate='one_to_one',how='left',indicator=True)
 old.base.require(out['_merge'].eq('both').all() and len(out)==len(frame),'Enlace incompleto')
 return out.drop(columns='_merge')
