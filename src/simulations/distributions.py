"""Distribuzioni per la simulazione Monte Carlo (M6).

Fornisce il campionamento di rendimenti multivariati secondo due modelli:
  - NORMALE multivariata: r = mu + L z, con L L^T = Sigma (Cholesky), z ~ N(0, I).
  - t di STUDENT multivariata: code piu' spesse, gradi di liberta' (df) configurabili.

Parametrizzazione della t (esplicita, sezione 4.5 del piano):
  Si vuole che la covarianza dei rendimenti sia Sigma. Per una t multivariata con df
  gradi di liberta' e matrice di scala S, la covarianza e' df/(df-2) * S. Quindi si
  impone  S = (df-2)/df * Sigma,  cosi' che Cov(r) = Sigma per df > 2.

Funzioni pure su array NumPy: nessuna dipendenza da Streamlit o dal dominio.

Robustezza numerica: se Sigma non e' fattorizzabile con Cholesky (non PSD a meno di
arrotondamenti), si ricorre alla decomposizione spettrale con floor sugli autovalori.
Il chiamante e' comunque tenuto a validare la matrice a monte (mai correzione
silenziosa dei dati utente; qui si tratta solo di stabilita' numerica del campionamento).
"""

from __future__ import annotations

import numpy as np

# Default tecnico provvisorio per i gradi di liberta' della t (configurabile).
DF_DEFAULT = 5
# Floor sugli autovalori per il fallback spettrale.
_EIG_FLOOR = 1e-12


def _fattore_radice(cov: np.ndarray) -> np.ndarray:
    """Restituisce L tale che L L^T ~= cov.

    Prova Cholesky (efficiente, richiede cov definita positiva). In caso di
    fallimento usa la radice simmetrica via decomposizione spettrale con floor sugli
    autovalori, garantendo comunque un fattore utilizzabile.
    """
    cov = np.asarray(cov, dtype=float)
    try:
        return np.linalg.cholesky(cov)
    except np.linalg.LinAlgError:
        vals, vecs = np.linalg.eigh(cov)
        vals_clipped = np.clip(vals, _EIG_FLOOR, None)
        return vecs @ np.diag(np.sqrt(vals_clipped))


def campiona_normale(
    mu: np.ndarray,
    cov: np.ndarray,
    dimensioni: tuple[int, ...],
    rng: np.random.Generator,
) -> np.ndarray:
    """Campiona da una normale multivariata N(mu, cov).

    dimensioni: forma del blocco di campioni da generare (es. (n_sim, n_periodi)).
    Restituisce array di forma (*dimensioni, n_asset).
    """
    mu = np.asarray(mu, dtype=float).ravel()
    n_asset = mu.shape[0]
    L = _fattore_radice(cov)
    z = rng.standard_normal(size=(*dimensioni, n_asset))
    return mu + z @ L.T


def campiona_t_student(
    mu: np.ndarray,
    cov: np.ndarray,
    df: float,
    dimensioni: tuple[int, ...],
    rng: np.random.Generator,
) -> np.ndarray:
    """Campiona da una t di Student multivariata con covarianza pari a cov.

    Costruzione: r = mu + z / sqrt(g/df), dove z ~ N(0, S), g ~ chi2(df), con
    S = (df-2)/df * cov. Per df > 2 si ha Cov(r) = cov.

    df deve essere > 2 affinche' la covarianza sia finita e pari a cov.
    """
    if df <= 2:
        raise ValueError("I gradi di liberta' della t devono essere > 2")
    mu = np.asarray(mu, dtype=float).ravel()
    cov = np.asarray(cov, dtype=float)
    n_asset = mu.shape[0]

    scala = (df - 2.0) / df * cov
    L = _fattore_radice(scala)
    z = rng.standard_normal(size=(*dimensioni, n_asset)) @ L.T
    # variabile chi-quadro per ciascun campione (broadcast sull'ultima dimensione)
    g = rng.chisquare(df, size=(*dimensioni, 1))
    return mu + z / np.sqrt(g / df)


def campiona_rendimenti(
    mu: np.ndarray,
    cov: np.ndarray,
    dimensioni: tuple[int, ...],
    rng: np.random.Generator,
    distribuzione: str = "normale",
    df: float = DF_DEFAULT,
) -> np.ndarray:
    """Dispatcher: campiona secondo la distribuzione scelta ('normale' o 't').

    In entrambi i casi la covarianza target dei rendimenti e' cov.
    """
    if distribuzione == "normale":
        return campiona_normale(mu, cov, dimensioni, rng)
    if distribuzione == "t":
        return campiona_t_student(mu, cov, df, dimensioni, rng)
    raise ValueError(f"Distribuzione non riconosciuta: {distribuzione!r}")
