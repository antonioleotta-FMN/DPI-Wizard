"""Validazione della matrice di correlazione e proposta di correzione (M2, DEC-006).

Le validazioni STRUTTURALI (simmetria, diagonale 1, range [-1,1], dimensioni) sono gia
applicate dal modello di dominio MatriceCorrelazione. Qui si aggiunge la verifica di
SEMI-DEFINITEZZA POSITIVA (PSD) e, se fallisce, una PROPOSTA di correzione tramite la
nearest correlation matrix (algoritmo di Higham).

Principio inviolabile (requisito "Precisione" del progetto, DEC-006): nessuna
correzione viene applicata silenziosamente. Questo modulo RESTITUISCE un esito e una
matrice proposta; la decisione di accettarla resta all'utente, a valle.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

# Soglia sotto la quale un autovalore e' considerato "negativo" solo per rumore
# numerico (matrice gia' PSD a meno di arrotondamenti). 1e-8 e' rigoroso ma robusto
# rispetto agli errori di arrotondamento delle decomposizioni spettrali.
_TOLL_AUTOVALORE = 1e-8


@dataclass
class EsitoValidazionePSD:
    """Risultato della verifica di semi-definitezza positiva.

    is_psd               True se la matrice e' PSD (entro tolleranza numerica)
    autovalore_minimo    il piu' piccolo autovalore osservato
    matrice_proposta     nearest correlation matrix (Higham), valorizzata solo se
                         is_psd e' False; altrimenti None
    differenza_max       massima differenza assoluta tra matrice originale e proposta
    messaggi             note esplicative per l'utente
    """

    is_psd: bool
    autovalore_minimo: float
    matrice_proposta: np.ndarray | None = None
    differenza_max: float | None = None
    messaggi: list[str] = field(default_factory=list)


def _autovalore_minimo(matrice: np.ndarray) -> float:
    # eigvalsh: per matrici simmetriche, autovalori reali ordinati crescenti
    return float(np.linalg.eigvalsh(matrice)[0])


def is_semidefinita_positiva(matrice: np.ndarray, toll: float = _TOLL_AUTOVALORE) -> bool:
    """True se tutti gli autovalori sono >= -toll (PSD entro tolleranza numerica)."""
    return _autovalore_minimo(np.asarray(matrice, dtype=float)) >= -toll


def nearest_correlation_higham(
    matrice: np.ndarray,
    max_iter: int = 100,
    tol: float = 1e-8,
) -> np.ndarray:
    """Nearest correlation matrix secondo Higham (2002), alternating projections.

    Proietta alternativamente sull'insieme delle matrici PSD (azzerando gli
    autovalori negativi) e sull'insieme delle matrici con diagonale unitaria,
    correggendo con l'aggiustamento di Dykstra. Converge alla matrice di
    correlazione valida piu' vicina (in norma di Frobenius) a quella di partenza.

    Restituisce una matrice simmetrica, PSD, con diagonale 1.
    """
    a = np.asarray(matrice, dtype=float)
    n = a.shape[0]
    y = a.copy()
    delta_s = np.zeros_like(a)

    # Floor strettamente positivo sugli autovalori: garantisce che la matrice
    # risultante sia PSD anche dopo gli arrotondamenti, evitando autovalori
    # marginalmente negativi (~ -1e-9) sul bordo del cono.
    eig_floor = 1e-8

    def _proietta_psd(m: np.ndarray) -> np.ndarray:
        # proiezione sul cono PSD: autovalori sotto il floor portati al floor
        vals, vecs = np.linalg.eigh(m)
        vals_clipped = np.clip(vals, eig_floor, None)
        return (vecs * vals_clipped) @ vecs.T

    def _proietta_diagonale_unitaria(m: np.ndarray) -> np.ndarray:
        m = m.copy()
        np.fill_diagonal(m, 1.0)
        return m

    x = y.copy()
    for _ in range(max_iter):
        r = y - delta_s
        x = _proietta_psd(r)
        delta_s = x - r
        y = _proietta_diagonale_unitaria(x)
        # criterio di arresto sulla variazione
        if np.linalg.norm(y - x, ord="fro") / max(np.linalg.norm(y, ord="fro"), 1e-12) < tol:
            break

    # simmetrizzazione e clamp finale di sicurezza nel range [-1, 1]
    y = 0.5 * (y + y.T)
    np.fill_diagonal(y, 1.0)
    return np.clip(y, -1.0, 1.0)


def valida_psd(matrice: np.ndarray) -> EsitoValidazionePSD:
    """Verifica PSD e, se necessario, propone (senza applicare) la correzione Higham.

    Vedi DEC-006: la matrice proposta e' un SUGGERIMENTO. La decisione di sostituire
    la matrice originale spetta all'utente, a livello di servizio/UI.
    """
    m = np.asarray(matrice, dtype=float)
    autoval_min = _autovalore_minimo(m)

    if autoval_min >= -_TOLL_AUTOVALORE:
        return EsitoValidazionePSD(
            is_psd=True,
            autovalore_minimo=autoval_min,
            messaggi=["La matrice e' semi-definita positiva: nessuna correzione necessaria."],
        )

    proposta = nearest_correlation_higham(m)
    diff_max = float(np.max(np.abs(proposta - m)))
    return EsitoValidazionePSD(
        is_psd=False,
        autovalore_minimo=autoval_min,
        matrice_proposta=proposta,
        differenza_max=diff_max,
        messaggi=[
            f"La matrice NON e' semi-definita positiva (autovalore minimo "
            f"{autoval_min:.2e}).",
            "E' stata calcolata una matrice di correlazione valida piu' vicina "
            "(algoritmo di Higham).",
            f"Massima variazione rispetto all'originale: {diff_max:.4f}.",
            "La correzione NON e' stata applicata: deve essere confermata "
            "esplicitamente dall'utente.",
        ],
    )
