"""Test numerici indipendenti delle metriche deterministiche (M1).

Per ogni metrica il risultato atteso e' calcolato a mano / per via indipendente e
confrontato entro tolleranza. Questo soddisfa il criterio della Definition of Done:
"il risultato e' confrontato con un caso numerico atteso".
"""

import math
import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.calculations.metrics import (  # noqa: E402
    matrice_covarianza,
    rendimento_atteso,
    rendimento_netto_costi,
    rendimento_reale,
    risk_contribution,
    volatilita,
)

TOL = 1e-10


# --------------------------- matrice_covarianza --------------------------- #
def test_covarianza_due_asset():
    # sigma = [0.10, 0.20], rho = 0.5
    # Sigma = [[0.01, 0.5*0.10*0.20], [..., 0.04]] = [[0.01, 0.01],[0.01, 0.04]]
    sigma = [0.10, 0.20]
    corr = [[1.0, 0.5], [0.5, 1.0]]
    atteso = np.array([[0.01, 0.01], [0.01, 0.04]])
    assert np.allclose(matrice_covarianza(sigma, corr), atteso, atol=TOL)


def test_covarianza_diagonale_se_incorrelati():
    sigma = [0.1, 0.3, 0.2]
    corr = np.eye(3)
    atteso = np.diag([0.01, 0.09, 0.04])
    assert np.allclose(matrice_covarianza(sigma, corr), atteso, atol=TOL)


# --------------------------- rendimento_atteso ---------------------------- #
def test_rendimento_atteso_manuale():
    # w=[0.6,0.4], mu=[0.05,0.10] -> 0.6*0.05 + 0.4*0.10 = 0.03 + 0.04 = 0.07
    assert abs(rendimento_atteso([0.6, 0.4], [0.05, 0.10]) - 0.07) < TOL


def test_rendimento_atteso_dim_errata():
    with pytest.raises(ValueError):
        rendimento_atteso([0.5, 0.5], [0.05])


# --------------------------- volatilita ----------------------------------- #
def test_volatilita_due_asset_manuale():
    # w=[0.6,0.4], sigma=[0.10,0.20], rho=0.5
    # Sigma=[[0.01,0.01],[0.01,0.04]]
    # var = 0.6^2*0.01 + 0.4^2*0.04 + 2*0.6*0.4*0.01
    #     = 0.0036 + 0.0064 + 0.0048 = 0.0148
    # sigma_p = sqrt(0.0148)
    cov = matrice_covarianza([0.10, 0.20], [[1.0, 0.5], [0.5, 1.0]])
    atteso = math.sqrt(0.0148)
    assert abs(volatilita([0.6, 0.4], cov) - atteso) < 1e-12


def test_volatilita_singolo_asset():
    # un solo asset: sigma_p = sigma
    cov = matrice_covarianza([0.15], [[1.0]])
    assert abs(volatilita([1.0], cov) - 0.15) < TOL


def test_volatilita_var_negativa_azzerata():
    # cov degenerata che potrebbe dare var leggermente < 0 -> deve restituire 0
    cov = np.array([[0.0, 0.0], [0.0, 0.0]])
    assert volatilita([0.5, 0.5], cov) == 0.0


# --------------------------- rendimento_reale ----------------------------- #
def test_rendimento_reale_fisher():
    # r=0.05, pi=0.02 -> (1.05/1.02)-1 = 0.0294117647...
    atteso = 1.05 / 1.02 - 1.0
    assert abs(rendimento_reale(0.05, 0.02) - atteso) < TOL
    # NON deve coincidere con l'approssimazione r - pi = 0.03
    assert abs(rendimento_reale(0.05, 0.02) - 0.03) > 1e-4


def test_rendimento_reale_inflazione_nulla():
    assert abs(rendimento_reale(0.05, 0.0) - 0.05) < TOL


def test_rendimento_reale_inflazione_invalida():
    with pytest.raises(ValueError):
        rendimento_reale(0.05, -1.0)


# --------------------------- rendimento_netto_costi ----------------------- #
def test_netto_costi_manuale():
    # w=[0.5,0.5], mu=[0.06,0.08], costi=[0.002,0.010]
    # lordo = 0.5*0.06+0.5*0.08 = 0.07
    # costo medio = 0.5*0.002+0.5*0.010 = 0.006
    # netto = 0.064
    val = rendimento_netto_costi([0.5, 0.5], [0.06, 0.08], [0.002, 0.010])
    assert abs(val - 0.064) < TOL


def test_netto_costi_uguale_lordo_se_costi_zero():
    val = rendimento_netto_costi([0.3, 0.7], [0.05, 0.09], [0.0, 0.0])
    assert abs(val - rendimento_atteso([0.3, 0.7], [0.05, 0.09])) < TOL


# --------------------------- risk_contribution ---------------------------- #
def test_risk_contribution_somma_pctr_uno():
    cov = matrice_covarianza([0.10, 0.20, 0.15], np.array(
        [[1.0, 0.3, 0.2], [0.3, 1.0, 0.4], [0.2, 0.4, 1.0]]
    ))
    pesi = [0.4, 0.35, 0.25]
    _, cctr, pctr = risk_contribution(pesi, cov)
    # somma PCTR = 1
    assert abs(pctr.sum() - 1.0) < 1e-12
    # somma CCTR = sigma_p
    assert abs(cctr.sum() - volatilita(pesi, cov)) < 1e-12


def test_risk_contribution_caso_manuale_due_asset():
    # w=[0.6,0.4], Sigma=[[0.01,0.01],[0.01,0.04]]
    # Sigma w = [0.01*0.6+0.01*0.4, 0.01*0.6+0.04*0.4] = [0.01, 0.022]
    # sigma_p = sqrt(0.0148)
    # MCTR = [0.01, 0.022]/sigma_p
    # CCTR = w*MCTR = [0.006, 0.0088]/sigma_p
    cov = np.array([[0.01, 0.01], [0.01, 0.04]])
    sigma_p = math.sqrt(0.0148)
    mctr, cctr, pctr = risk_contribution([0.6, 0.4], cov)
    assert np.allclose(mctr, np.array([0.01, 0.022]) / sigma_p, atol=1e-12)
    assert np.allclose(cctr, np.array([0.006, 0.0088]) / sigma_p, atol=1e-12)
    assert np.allclose(pctr, np.array([0.006, 0.0088]) / 0.0148, atol=1e-12)


def test_risk_contribution_volatilita_nulla():
    with pytest.raises(ValueError):
        risk_contribution([0.5, 0.5], np.zeros((2, 2)))
