"""Invariante PRE00 para consumidores de coste por periodo; no modifica siniestros."""
import pandas as pd

VERSION = '1.0'
FLAG = 'audit_pre00'


def assert_prehistory_excluded(claims, assigned_claim_ids):
    """Rechaza una asignación que lleve un expediente PRE00 a un periodo actual.

    Una corrección futura de cobertura exige revisar la cohorte y su autorización.
    No se desplazan fechas ni se borran importes para resolver ese conflicto.
    Se admiten snapshots históricos sin la columna, cuya exclusión sigue por fechas.
    """
    if FLAG not in claims.columns:
        return
    if not claims.claim_id.is_unique:
        raise ValueError('PRE00 requiere identificadores de siniestro únicos.')
    flag = claims[FLAG]
    if not pd.api.types.is_bool_dtype(flag) or flag.isna().any():
        raise ValueError('audit_pre00 debe ser booleano sin nulos.')
    assigned = pd.Index(assigned_claim_ids)
    if not assigned.is_unique or not assigned.isin(claims.claim_id).all():
        raise ValueError('Asignación duplicada o ajena al conjunto de siniestros.')
    if claims.loc[flag, 'claim_id'].isin(assigned).any():
        raise ValueError('PRE00: coste anterior al historial asignado a un periodo actual; revisar antes de continuar.')
