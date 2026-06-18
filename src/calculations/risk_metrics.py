"""Metriche di rischio su distribuzioni simulate (M6).

Funzioni pure riusabili da Monte Carlo e stress test: percentili, VaR, Expected
Shortfall di mercato, probabilita ed entita media dello shortfall, drawdown.

Convenzioni:
  - Le PERDITE sono espresse come valori positivi (perdita = capitale - montante).
  - VaR ed ES sono definiti su una distribuzione di perdita, a un livello di
    confidenza alpha (es. 0.95).
  - Lo shortfall previdenziale e' un concetto DISTINTO dall'ES di mercato e ha una
    denominazione diversa (vedi funzioni dedicate).
"""

from __future__ import annotations

import numpy as np


def percentili(valori: np.ndarray, punti: tuple[int, ...] = (5, 25, 50, 75, 95)) -> dict[int, float]:
    """Percentili di una distribuzione di valori."""
    v = np.asarray(valori, dtype=float)
    return {p: float(np.percentile(v, p)) for p in punti}


def var_perdita(perdite: np.ndarray, alpha: float) -> float:
    """Value at Risk: percentile alpha della distribuzione di perdita.

    perdite: array di perdite (positive = perdita). alpha: livello di confidenza.
    """
    return float(np.percentile(np.asarray(perdite, dtype=float), alpha * 100.0))


def expected_shortfall_mercato(perdite: np.ndarray, alpha: float) -> float:
    """Expected Shortfall (CVaR): perdita media oltre il VaR al livello alpha."""
    p = np.asarray(perdite, dtype=float)
    soglia = var_perdita(p, alpha)
    coda = p[p >= soglia]
    return float(np.mean(coda)) if coda.size > 0 else soglia


def prob_shortfall(metriche: np.ndarray, soglia: float) -> float:
    """Probabilita che la metrica sia inferiore alla soglia: P(X < soglia)."""
    x = np.asarray(metriche, dtype=float)
    return float(np.mean(x < soglia))


def shortfall_medio_condizionato(metriche: np.ndarray, soglia: float) -> float:
    """Entita media dello shortfall: E[soglia - X | X < soglia].

    Concetto distinto dall'ES di mercato. Restituisce 0 se nessuno scenario e' sotto
    soglia.
    """
    x = np.asarray(metriche, dtype=float)
    sotto = x[x < soglia]
    return float(np.mean(soglia - sotto)) if sotto.size > 0 else 0.0


def drawdown_da_serie(serie: np.ndarray) -> np.ndarray:
    """Drawdown lungo una o piu' serie di valori.

    serie: (..., n_step). Restituisce array della stessa forma con il drawdown a ogni
    step: (V_t - max_{s<=t} V_s) / max_{s<=t} V_s, valore <= 0.
    """
    s = np.asarray(serie, dtype=float)
    massimi = np.maximum.accumulate(s, axis=-1)
    return (s - massimi) / massimi


def max_drawdown_da_serie(serie: np.ndarray) -> np.ndarray:
    """Massimo drawdown (il piu' negativo) per ciascuna serie."""
    return drawdown_da_serie(serie).min(axis=-1)


def bande_percentili(serie: np.ndarray, punti: tuple[int, ...] = (5, 50, 95)) -> dict[int, np.ndarray]:
    """Bande percentili lungo l'asse degli scenari, per ogni step temporale.

    serie: (n_scenari, n_step). Restituisce {p: array (n_step,)} per il fan chart.
    """
    s = np.asarray(serie, dtype=float)
    return {p: np.percentile(s, p, axis=0) for p in punti}
