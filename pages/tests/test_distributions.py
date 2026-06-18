"""Test delle distribuzioni multivariate (M6).

Verifica chiave: la t di Student multivariata, con la parametrizzazione scelta
(S = (df-2)/df * Sigma), riproduce la COVARIANZA target Sigma, non la matrice di scala.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulations.distributions import (  # noqa: E402
    campiona_normale,
    campiona_rendimenti,
    campiona_t_student,
)


def _cov_target():
    sigma = np.array([0.05, 0.18])
    corr = np.array([[1.0, 0.3], [0.3, 1.0]])
    d = np.diag(sigma)
    return d @ corr @ d


def test_normale_media_e_covarianza():
    mu = np.array([0.03, 0.07])
    cov = _cov_target()
    rng = np.random.default_rng(1)
    campioni = campiona_normale(mu, cov, (500_000,), rng)
    assert np.allclose(campioni.mean(axis=0), mu, atol=2e-3)
    cov_emp = np.cov(campioni, rowvar=False)
    assert np.allclose(cov_emp, cov, atol=2e-3)


def test_t_student_riproduce_covarianza_target():
    # la covarianza empirica deve avvicinarsi a Sigma, NON a (df/(df-2))*Sigma
    mu = np.array([0.0, 0.0])
    cov = _cov_target()
    df = 6
    rng = np.random.default_rng(2)
    campioni = campiona_t_student(mu, cov, df, (1_000_000,), rng)
    cov_emp = np.cov(campioni, rowvar=False)
    # tolleranza piu' ampia: la t ha code spesse, stima piu' rumorosa
    assert np.allclose(cov_emp, cov, rtol=0.05, atol=5e-3)


def test_t_student_code_piu_spesse_della_normale():
    # la curtosi della t deve superare quella della normale (=3)
    mu = np.array([0.0])
    cov = np.array([[0.04]])
    rng = np.random.default_rng(3)
    t = campiona_t_student(mu, cov, 5, (500_000,), rng).ravel()
    z = campiona_normale(mu, cov, (500_000,), rng).ravel()
    curtosi_t = np.mean((t / t.std()) ** 4)
    curtosi_z = np.mean((z / z.std()) ** 4)
    assert curtosi_t > curtosi_z


def test_t_student_df_non_valido():
    with pytest.raises(ValueError):
        campiona_t_student(np.array([0.0]), np.array([[0.04]]), 2.0, (10,),
                           np.random.default_rng(0))


def test_dispatcher_normale_e_t():
    mu = np.array([0.03, 0.07])
    cov = _cov_target()
    rng = np.random.default_rng(4)
    n = campiona_rendimenti(mu, cov, (100,), rng, distribuzione="normale")
    t = campiona_rendimenti(mu, cov, (100,), rng, distribuzione="t", df=5)
    assert n.shape == (100, 2)
    assert t.shape == (100, 2)


def test_dispatcher_distribuzione_sconosciuta():
    with pytest.raises(ValueError):
        campiona_rendimenti(np.array([0.0]), np.array([[1.0]]), (10,),
                            np.random.default_rng(0), distribuzione="cauchy")


def test_riproducibilita_seed():
    mu = np.array([0.03, 0.07])
    cov = _cov_target()
    a = campiona_normale(mu, cov, (1000,), np.random.default_rng(7))
    b = campiona_normale(mu, cov, (1000,), np.random.default_rng(7))
    assert np.array_equal(a, b)
