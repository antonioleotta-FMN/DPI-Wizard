"""Metriche deterministiche di portafoglio (M1).

Funzioni pure su array NumPy: nessuno stato, nessun I/O, nessuna dipendenza da
Streamlit. Tutte le quantita sono annue e in forma decimale (0.05 = 5%).

Ogni funzione riporta in docstring la scheda metodologica: definizione, formula,
input/output, ipotesi, limiti. I test numerici indipendenti sono in
tests/test_calculations.py.

Convenzioni di ordinamento: l'ordine degli asset in `pesi`, `mu`, `sigma` e nelle
righe/colonne di `correlazioni`/`cov` DEVE essere il medesimo. La conversione da
modelli di dominio ad array ordinati e responsabilita dei servizi (src/services),
non di questo modulo.
"""

from __future__ import annotations

import numpy as np

ArrayLike = np.ndarray


# --------------------------------------------------------------------------- #
# Helper interni
# --------------------------------------------------------------------------- #
def _as_1d(x: ArrayLike, nome: str) -> np.ndarray:
    a = np.asarray(x, dtype=float).ravel()
    if a.ndim != 1:
        raise ValueError(f"{nome} deve essere monodimensionale")
    return a


def _check_dim(pesi: np.ndarray, altro: np.ndarray, nome: str) -> None:
    if pesi.shape[0] != altro.shape[0]:
        raise ValueError(
            f"Dimensioni incompatibili: pesi ({pesi.shape[0]}) vs {nome} "
            f"({altro.shape[0]})"
        )


def matrice_covarianza(sigma: ArrayLike, correlazioni: ArrayLike) -> np.ndarray:
    """Matrice di covarianza da volatilita e correlazioni.

    DEFINIZIONE
        Sigma = D C D, con D = diag(sigma) e C matrice di correlazione.
    INPUT
        sigma          vettore (n,) di volatilita annue, >= 0
        correlazioni   matrice (n,n) di correlazione (simmetrica, diagonale 1)
    OUTPUT
        matrice (n,n) di covarianza
    IPOTESI
        Le correlazioni sono valide (validazione a monte nel dominio/data).
    LIMITI
        Non verifica la semi-definitezza positiva: e' responsabilita di src/data.
    """
    s = _as_1d(sigma, "sigma")
    c = np.asarray(correlazioni, dtype=float)
    if c.shape != (s.shape[0], s.shape[0]):
        raise ValueError(
            f"correlazioni deve essere ({s.shape[0]},{s.shape[0]}), e' {c.shape}"
        )
    d = np.diag(s)
    return d @ c @ d


def rendimento_atteso(pesi: ArrayLike, mu: ArrayLike) -> float:
    """Rendimento atteso di portafoglio.

    DEFINIZIONE
        E(R_p) = w' mu
    INPUT
        pesi   vettore (n,) di pesi
        mu     vettore (n,) di rendimenti attesi annui
    OUTPUT
        scalare: rendimento atteso annuo del portafoglio
    IPOTESI
        mu in forma aritmetica annua coerente tra asset class.
    LIMITI
        Su orizzonti pluriennali usare la convenzione geometrica (DEC-003),
        gestita nelle proiezioni/simulazioni, non qui.
    """
    w = _as_1d(pesi, "pesi")
    m = _as_1d(mu, "mu")
    _check_dim(w, m, "mu")
    return float(w @ m)


def volatilita(pesi: ArrayLike, cov: ArrayLike) -> float:
    """Volatilita (deviazione standard) di portafoglio.

    DEFINIZIONE
        sigma_p = sqrt(w' Sigma w)
    INPUT
        pesi   vettore (n,) di pesi
        cov    matrice (n,n) di covarianza
    OUTPUT
        scalare: volatilita annua del portafoglio (>= 0)
    IPOTESI
        Sigma simmetrica e semi-definita positiva.
    LIMITI
        Se la varianza calcolata e' lievemente negativa per errori numerici
        (Sigma quasi-PSD), viene azzerata prima della radice.
    """
    w = _as_1d(pesi, "pesi")
    c = np.asarray(cov, dtype=float)
    if c.shape != (w.shape[0], w.shape[0]):
        raise ValueError(f"cov deve essere ({w.shape[0]},{w.shape[0]}), e' {c.shape}")
    var = float(w @ c @ w)
    if var < 0.0:
        var = 0.0
    return float(np.sqrt(var))


def rendimento_reale(r_nominale: float, inflazione: float) -> float:
    """Rendimento reale (formula di Fisher esatta).

    DEFINIZIONE
        R_reale = (1 + R_nominale) / (1 + pi) - 1
    INPUT
        r_nominale   rendimento nominale annuo
        inflazione   tasso di inflazione annuo (pi)
    OUTPUT
        scalare: rendimento reale annuo
    IPOTESI
        inflazione > -1 (per evitare divisione per zero o segno invertito).
    LIMITI
        Usa la formula esatta, non l'approssimazione R_nom - pi (DEC-004).
    """
    if inflazione <= -1.0:
        raise ValueError("inflazione deve essere > -1")
    return (1.0 + r_nominale) / (1.0 + inflazione) - 1.0


def rendimento_netto_costi(pesi: ArrayLike, mu: ArrayLike, costi: ArrayLike) -> float:
    """Rendimento atteso al netto dei costi.

    DEFINIZIONE
        R_net = w' mu - w' c = w' (mu - c)
    INPUT
        pesi   vettore (n,) di pesi
        mu     vettore (n,) di rendimenti nominali attesi
        costi  vettore (n,) di TER annui (>= 0), DEC-007
    OUTPUT
        scalare: rendimento netto costi annuo
    IPOTESI
        Costi costanti annui per asset class (DEC-007).
    LIMITI
        Non modella turnover ne costi di transazione.
    """
    w = _as_1d(pesi, "pesi")
    m = _as_1d(mu, "mu")
    c = _as_1d(costi, "costi")
    _check_dim(w, m, "mu")
    _check_dim(w, c, "costi")
    return float(w @ (m - c))


def risk_contribution(
    pesi: ArrayLike, cov: ArrayLike
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Scomposizione del rischio per asset class.

    DEFINIZIONI
        sigma_p = sqrt(w' Sigma w)
        MCTR_i  = (Sigma w)_i / sigma_p          marginal contribution to risk
        CCTR_i  = w_i * MCTR_i                    component contribution to risk
        PCTR_i  = CCTR_i / sigma_p                percent contribution (somma = 1)
    INPUT
        pesi   vettore (n,) di pesi
        cov    matrice (n,n) di covarianza
    OUTPUT
        (mctr, cctr, pctr), ciascuno vettore (n,)
        Proprieta: sum(cctr) = sigma_p, sum(pctr) = 1.
    IPOTESI
        sigma_p > 0.
    LIMITI
        Con sigma_p = 0 (portafoglio a rischio nullo) la decomposizione non e'
        definita: viene sollevata un'eccezione.
    """
    w = _as_1d(pesi, "pesi")
    c = np.asarray(cov, dtype=float)
    if c.shape != (w.shape[0], w.shape[0]):
        raise ValueError(f"cov deve essere ({w.shape[0]},{w.shape[0]}), e' {c.shape}")
    sigma_p = volatilita(w, c)
    if sigma_p <= 0.0:
        raise ValueError(
            "risk_contribution non definita per volatilita di portafoglio nulla"
        )
    sigma_w = c @ w
    mctr = sigma_w / sigma_p
    cctr = w * mctr
    pctr = cctr / sigma_p
    return mctr, cctr, pctr
