"""Vincoli per l'ottimizzazione (M7).

Costruisce i vincoli nel formato richiesto da scipy.optimize.minimize (SLSQP): una
lista di dict con 'type' ('eq' o 'ineq') e 'fun' (>= 0 per 'ineq', = 0 per 'eq'), piu'
i bounds per ciascun peso.

Tutti i vincoli sono configurabili tramite l'oggetto ConfigVincoli. Funzioni pure.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np


@dataclass
class ConfigVincoli:
    """Configurazione dei vincoli di ottimizzazione.

    Indici riferiti all'ordine canonico delle asset class nel set CMA.
    """

    n_asset: int
    bounds: list[tuple[float, float]] = field(default_factory=list)  # (min,max) per asset
    gruppi: list[tuple[list[int], float, float]] = field(default_factory=list)  # (idx, Lg, Ug)
    idx_liquidita: list[int] = field(default_factory=list)
    liquidita_min: float | None = None
    idx_illiquidi: list[int] = field(default_factory=list)
    illiquidita_max: float | None = None
    rendimento_min: float | None = None
    volatilita_max: float | None = None
    durations: np.ndarray | None = None
    duration_min: float | None = None
    duration_max: float | None = None
    fx: np.ndarray | None = None
    fx_min: float | None = None
    fx_max: float | None = None
    pesi_correnti: np.ndarray | None = None
    turnover_max: float | None = None


def costruisci_vincoli(
    cfg: ConfigVincoli, mu: np.ndarray, cov: np.ndarray
) -> tuple[list[dict], list[tuple[float, float]]]:
    """Restituisce (lista_vincoli, bounds) per scipy.optimize.minimize."""
    vincoli: list[dict] = []

    # pieno investimento: somma pesi = 1
    vincoli.append({"type": "eq", "fun": lambda w: np.sum(w) - 1.0})

    # vincoli di gruppo: Lg <= somma pesi gruppo <= Ug
    for idx, lg, ug in cfg.gruppi:
        idx_arr = np.array(idx, dtype=int)
        vincoli.append({"type": "ineq", "fun": (lambda w, i=idx_arr, L=lg: np.sum(w[i]) - L)})
        vincoli.append({"type": "ineq", "fun": (lambda w, i=idx_arr, U=ug: U - np.sum(w[i]))})

    # liquidita minima
    if cfg.liquidita_min is not None and cfg.idx_liquidita:
        i = np.array(cfg.idx_liquidita, dtype=int)
        vincoli.append({"type": "ineq", "fun": (lambda w, i=i, L=cfg.liquidita_min: np.sum(w[i]) - L)})

    # illiquidita massima
    if cfg.illiquidita_max is not None and cfg.idx_illiquidi:
        i = np.array(cfg.idx_illiquidi, dtype=int)
        vincoli.append({"type": "ineq", "fun": (lambda w, i=i, U=cfg.illiquidita_max: U - np.sum(w[i]))})

    # rendimento minimo
    if cfg.rendimento_min is not None:
        vincoli.append({"type": "ineq", "fun": (lambda w, R=cfg.rendimento_min: w @ mu - R)})

    # volatilita massima
    if cfg.volatilita_max is not None:
        vincoli.append({"type": "ineq",
                        "fun": (lambda w, S=cfg.volatilita_max: S - np.sqrt(max(w @ cov @ w, 0.0)))})

    # duration
    if cfg.durations is not None:
        if cfg.duration_min is not None:
            vincoli.append({"type": "ineq", "fun": (lambda w, D=cfg.durations, L=cfg.duration_min: w @ D - L)})
        if cfg.duration_max is not None:
            vincoli.append({"type": "ineq", "fun": (lambda w, D=cfg.durations, U=cfg.duration_max: U - w @ D)})

    # esposizione valutaria
    if cfg.fx is not None:
        if cfg.fx_min is not None:
            vincoli.append({"type": "ineq", "fun": (lambda w, F=cfg.fx, L=cfg.fx_min: w @ F - L)})
        if cfg.fx_max is not None:
            vincoli.append({"type": "ineq", "fun": (lambda w, F=cfg.fx, U=cfg.fx_max: U - w @ F)})

    # turnover rispetto alla AAS vigente: sum |w - w0| <= T_max
    if cfg.turnover_max is not None and cfg.pesi_correnti is not None:
        w0 = cfg.pesi_correnti
        vincoli.append({"type": "ineq",
                        "fun": (lambda w, w0=w0, T=cfg.turnover_max: T - np.sum(np.abs(w - w0)))})

    # bounds individuali
    if cfg.bounds:
        bounds = cfg.bounds
    else:
        bounds = [(0.0, 1.0)] * cfg.n_asset  # default: no short, max 100%

    return vincoli, bounds


def turnover(pesi: np.ndarray, pesi_correnti: np.ndarray) -> float:
    """Turnover L1 rispetto alla AAS vigente: somma dei valori assoluti delle differenze."""
    return float(np.sum(np.abs(np.asarray(pesi) - np.asarray(pesi_correnti))))
