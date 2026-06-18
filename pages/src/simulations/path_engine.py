"""Motore dei percorsi multi-periodo (M6).

Evolve il montante di portafoglio lungo il tempo a partire dai rendimenti campionati,
gestendo frequenza (annuale/mensile), ribilanciamento (ai pesi target o nessuno) e
flussi opzionali (contributi/uscite). Calcola anche i drawdown lungo i percorsi.

Funzioni pure su array NumPy.

Convenzioni:
  - I rendimenti in ingresso sono per-periodo (gia' alla frequenza scelta) e hanno
    forma (n_sim, n_periodi, n_asset).
  - n_periodi = orizzonte_anni * periodi_per_anno.
  - Senza flussi, il montante e' per 1 unita di capitale iniziale.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class RisultatoPercorsi:
    """Output dell'evoluzione dei percorsi.

    montanti_finali     (n_sim,) montante nominale a fine orizzonte
    serie_montanti      (n_sim, n_periodi+1) montante a ogni step (incluso t0)
    max_drawdown        (n_sim,) massimo drawdown per scenario (valore <= 0)
    """

    montanti_finali: np.ndarray
    serie_montanti: np.ndarray
    max_drawdown: np.ndarray


def _rendimento_portafoglio_periodo(
    rend_asset: np.ndarray, pesi: np.ndarray, costo_periodo: float, ribilanciamento: bool
) -> np.ndarray:
    """Rendimento di portafoglio per periodo.

    Con ribilanciamento: pesi costanti ogni periodo -> media pesata dei rendimenti.
    Senza ribilanciamento: i pesi derivano dal drift del periodo precedente.
    Restituisce (n_sim, n_periodi).
    """
    n_sim, n_periodi, _ = rend_asset.shape
    if ribilanciamento:
        return rend_asset @ pesi - costo_periodo

    # buy & hold: i pesi evolvono col valore relativo degli asset
    rend_pf = np.empty((n_sim, n_periodi))
    pesi_correnti = np.tile(pesi, (n_sim, 1))
    for t in range(n_periodi):
        r_t = rend_asset[:, t, :]
        valore_asset = pesi_correnti * (1.0 + r_t)
        valore_pf = valore_asset.sum(axis=1)
        rend_pf[:, t] = valore_pf - 1.0 - costo_periodo
        # rinormalizza i pesi per il periodo successivo
        pesi_correnti = valore_asset / valore_pf[:, None]
    return rend_pf


def evolvi_percorsi(
    rend_asset: np.ndarray,
    pesi: np.ndarray,
    costo_annuo: float,
    periodi_per_anno: int,
    ribilanciamento: bool = True,
    contributi: np.ndarray | None = None,
    uscite: np.ndarray | None = None,
    capitale_iniziale: float = 1.0,
) -> RisultatoPercorsi:
    """Evolve i montanti lungo i percorsi.

    rend_asset       (n_sim, n_periodi, n_asset) rendimenti per-periodo
    pesi             (n_asset,) pesi target
    costo_annuo      TER annuo di portafoglio; convertito alla frequenza
    periodi_per_anno 1 (annuale) o 12 (mensile)
    contributi/uscite (n_periodi,) flussi per periodo, opzionali
    """
    pesi = np.asarray(pesi, dtype=float).ravel()
    n_sim, n_periodi, _ = rend_asset.shape
    costo_periodo = costo_annuo / periodi_per_anno

    rend_pf = _rendimento_portafoglio_periodo(
        rend_asset, pesi, costo_periodo, ribilanciamento
    )

    serie = np.empty((n_sim, n_periodi + 1))
    serie[:, 0] = capitale_iniziale
    usa_flussi = contributi is not None or uscite is not None
    c = np.zeros(n_periodi) if contributi is None else np.asarray(contributi, dtype=float)
    w = np.zeros(n_periodi) if uscite is None else np.asarray(uscite, dtype=float)

    for t in range(n_periodi):
        base = serie[:, t]
        if usa_flussi:
            base = base + c[t] - w[t]
        serie[:, t + 1] = base * (1.0 + rend_pf[:, t])

    montanti_finali = serie[:, -1]

    # max drawdown lungo ciascun percorso
    massimi_correnti = np.maximum.accumulate(serie, axis=1)
    drawdown = (serie - massimi_correnti) / massimi_correnti
    max_dd = drawdown.min(axis=1)

    return RisultatoPercorsi(
        montanti_finali=montanti_finali,
        serie_montanti=serie,
        max_drawdown=max_dd,
    )


def converti_rendimento_annuo_a_periodo(mu_annuo: np.ndarray, periodi_per_anno: int) -> np.ndarray:
    """Converte rendimenti attesi annui in per-periodo (geometrico)."""
    mu_annuo = np.asarray(mu_annuo, dtype=float)
    return (1.0 + mu_annuo) ** (1.0 / periodi_per_anno) - 1.0


def converti_covarianza_annua_a_periodo(cov_annua: np.ndarray, periodi_per_anno: int) -> np.ndarray:
    """Converte la covarianza annua in per-periodo (scalatura lineare nel tempo)."""
    return np.asarray(cov_annua, dtype=float) / periodi_per_anno
