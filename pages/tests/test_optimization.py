"""Test del motore di ottimizzazione (M7)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import Proposta  # noqa: E402
from src.optimization import (  # noqa: E402
    ConfigVincoli,
    arrotonda_pesi,
    diagnostica_infeasibilita,
    frontiera_efficiente,
    ottimizza,
    turnover,
)
from src.services import (  # noqa: E402
    costruisci_config_da_comparto,
    ottimizza_aas,
)


def _mercato():
    sigma = np.array([0.05, 0.12, 0.18])
    corr = np.array([[1, 0.2, 0.1], [0.2, 1, 0.3], [0.1, 0.3, 1]])
    cov = np.diag(sigma) @ corr @ np.diag(sigma)
    mu = np.array([0.03, 0.05, 0.08])
    return mu, cov


# --------------------------- soluzione analitica -------------------------- #
def test_min_varianza_vs_analitica():
    mu, cov = _mercato()
    inv = np.linalg.inv(cov)
    uno = np.ones(3)
    w_analitico = inv @ uno / (uno @ inv @ uno)
    cfg = ConfigVincoli(n_asset=3, bounds=[(-1, 1)] * 3)
    res = ottimizza("min_varianza", cfg, mu, cov)
    assert res.successo
    assert np.allclose(res.pesi, w_analitico, atol=1e-4)


# --------------------------- somma pesi e bounds -------------------------- #
def test_somma_pesi_unitaria():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3)
    for ob in ["min_varianza", "max_rendimento", "max_sharpe"]:
        res = ottimizza(ob, cfg, mu, cov)
        assert res.successo
        assert abs(res.pesi.sum() - 1.0) < 1e-6


def test_bounds_rispettati():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0.1, 0.5)] * 3)
    res = ottimizza("max_rendimento", cfg, mu, cov)
    assert res.successo
    assert all(0.1 - 1e-6 <= w <= 0.5 + 1e-6 for w in res.pesi)


def test_max_rendimento_concentra_su_asset_migliore():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3)
    res = ottimizza("max_rendimento", cfg, mu, cov)
    # senza altri vincoli, massimizza sul rendimento piu' alto (asset 3)
    assert res.pesi[2] > 0.99


def test_vincolo_rendimento_minimo():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3, rendimento_min=0.06)
    res = ottimizza("min_varianza", cfg, mu, cov)
    assert res.successo
    assert res.pesi @ mu >= 0.06 - 1e-6


def test_vincolo_volatilita_massima():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3, volatilita_max=0.10)
    res = ottimizza("max_rendimento", cfg, mu, cov)
    assert res.successo
    assert np.sqrt(res.pesi @ cov @ res.pesi) <= 0.10 + 1e-4


# --------------------------- infeasibilita' ------------------------------- #
def test_infeasible_rendimento_irraggiungibile():
    mu, cov = _mercato()
    # rendimento minimo 0.10 > max mu (0.08): impossibile
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3, rendimento_min=0.10)
    res = ottimizza("min_varianza", cfg, mu, cov)
    assert not res.successo
    diag = diagnostica_infeasibilita(cfg, mu, cov)
    assert not diag.feasible
    assert "rendimento_min" in diag.vincoli_problematici


def test_infeasible_non_restituisce_pesi():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3, rendimento_min=0.10)
    res = ottimizza("min_varianza", cfg, mu, cov)
    assert res.pesi is None


# --------------------------- arrotondamento ------------------------------- #
def test_arrotondamento_mantiene_somma():
    pesi = np.array([0.333, 0.333, 0.334])
    arr = arrotonda_pesi(pesi, 0.01)
    assert abs(arr.sum() - 1.0) < 1e-9


# --------------------------- turnover ------------------------------------- #
def test_turnover_l1():
    w = np.array([0.5, 0.3, 0.2])
    w0 = np.array([0.4, 0.4, 0.2])
    assert abs(turnover(w, w0) - 0.2) < 1e-12


def test_vincolo_turnover():
    mu, cov = _mercato()
    w0 = np.array([0.8, 0.1, 0.1])
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3,
                        pesi_correnti=w0, turnover_max=0.1)
    res = ottimizza("max_rendimento", cfg, mu, cov)
    assert res.successo
    assert turnover(res.pesi, w0) <= 0.1 + 1e-4


# --------------------------- determinismo --------------------------------- #
def test_determinismo():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3)
    r1 = ottimizza("max_sharpe", cfg, mu, cov)
    r2 = ottimizza("max_sharpe", cfg, mu, cov)
    assert np.allclose(r1.pesi, r2.pesi)


# --------------------------- frontiera ------------------------------------ #
def test_frontiera_volatilita_crescente_con_rendimento():
    mu, cov = _mercato()
    cfg = ConfigVincoli(n_asset=3, bounds=[(0, 1)] * 3)
    punti = frontiera_efficiente(cfg, mu, cov, n_punti=10)
    assert len(punti) >= 3
    # ordinati per rendimento, la volatilita non deve diminuire drasticamente
    punti_ord = sorted(punti, key=lambda p: p.rendimento)
    vol = [p.volatilita for p in punti_ord]
    # la frontiera efficiente e' monotona non decrescente in volatilita
    assert vol[-1] >= vol[0]


# --------------------------- integrazione service ------------------------- #
def test_service_ottimizza_demo():
    cma, comp = cma_demo(), comparto_demo()
    vig = Proposta(nome="vig", pesi={
        "Liquidita": 0.05, "Govt EUR": 0.30, "Corporate": 0.15, "Equity DM": 0.25,
        "Equity EM": 0.10, "Real assets": 0.05, "Private markets": 0.10,
    })
    cfg = costruisci_config_da_comparto(cma, comp, vig)
    esito = ottimizza_aas(cma, comp, "min_varianza", cfg)
    assert esito.successo
    assert esito.proposta is not None
    assert abs(sum(esito.proposta.pesi.values()) - 1.0) < 1e-6
