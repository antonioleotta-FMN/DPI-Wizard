"""Funzioni obiettivo per l'ottimizzazione dell'Asset Allocation Strategica (M7).

Ogni obiettivo e' una funzione (pesi, contesto) -> valore scalare da MINIMIZZARE
(gli obiettivi di massimizzazione restituiscono il negativo). Funzioni pure su NumPy.

Contesto: un oggetto con mu (rendimenti attesi), cov (covarianza), rf (risk free).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class ContestoOttimizzazione:
    mu: np.ndarray
    cov: np.ndarray
    rf: float = 0.0


def varianza(pesi: np.ndarray, ctx: ContestoOttimizzazione) -> float:
    """Varianza di portafoglio w' Sigma w (da minimizzare)."""
    return float(pesi @ ctx.cov @ pesi)


def rendimento_negativo(pesi: np.ndarray, ctx: ContestoOttimizzazione) -> float:
    """Negativo del rendimento atteso (per massimizzare il rendimento)."""
    return -float(pesi @ ctx.mu)


def sharpe_negativo(pesi: np.ndarray, ctx: ContestoOttimizzazione) -> float:
    """Negativo dello Sharpe ratio (per massimizzare lo Sharpe).

    Sharpe = (w'mu - rf) / sqrt(w' Sigma w). Restituisce un valore grande se la
    volatilita e' nulla (caso degenere), per scoraggiare soluzioni prive di rischio.
    """
    var = float(pesi @ ctx.cov @ pesi)
    if var <= 1e-18:
        return 1e6
    return -(float(pesi @ ctx.mu) - ctx.rf) / np.sqrt(var)


# Mappa nome -> funzione obiettivo (per obiettivi "diretti" senza vincoli impliciti)
OBIETTIVI = {
    "min_varianza": varianza,
    "max_rendimento": rendimento_negativo,
    "max_sharpe": sharpe_negativo,
}
