"""Test di Monte Carlo (convergenza, riproducibilita) e motore vincoli (M3)."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.calculations.metrics import matrice_covarianza, rendimento_netto_costi  # noqa: E402
from src.constraints.engine import (  # noqa: E402
    Stato,
    riepilogo_stato,
    verifica_vincoli,
)
from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import (  # noqa: E402
    ConfigSimulazione,
    DefinizioneShortfall,
    Proposta,
)
from src.simulations.montecarlo import simula_montecarlo  # noqa: E402


def _setup_due_asset():
    mu = np.array([0.03, 0.07])
    sigma = np.array([0.05, 0.18])
    corr = np.array([[1.0, 0.2], [0.2, 1.0]])
    cov = matrice_covarianza(sigma, corr)
    costi = np.array([0.0, 0.0])
    pesi = np.array([0.5, 0.5])
    return pesi, mu, cov, costi


# --------------------------- Monte Carlo: convergenza --------------------- #
def test_montecarlo_convergenza_rendimento_medio():
    # Con molte simulazioni e orizzonte 1 anno, costi e inflazione nulli,
    # la media dei rendimenti annui deve avvicinarsi a w'mu.
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=200_000, seed=1, inflazione=0.0)
    res = simula_montecarlo(
        pesi, mu, cov, costi, config,
        orizzonte_anni=1, obiettivo_rendimento=0.0,
    )
    atteso = float(pesi @ mu)  # 0.5*0.03 + 0.5*0.07 = 0.05
    media_sim = float(np.mean(res.rendimenti_annui_medi))
    assert abs(media_sim - atteso) < 0.002  # tolleranza Monte Carlo


def test_montecarlo_riproducibilita_seed():
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=5_000, seed=123)
    r1 = simula_montecarlo(pesi, mu, cov, costi, config, 10, 0.0)
    r2 = simula_montecarlo(pesi, mu, cov, costi, config, 10, 0.0)
    assert np.array_equal(r1.montanti_finali, r2.montanti_finali)
    assert r1.prob_shortfall == r2.prob_shortfall


def test_montecarlo_seed_diverso_cambia_risultato():
    pesi, mu, cov, costi = _setup_due_asset()
    c1 = ConfigSimulazione(n_simulazioni=5_000, seed=1)
    c2 = ConfigSimulazione(n_simulazioni=5_000, seed=2)
    r1 = simula_montecarlo(pesi, mu, cov, costi, c1, 10, 0.0)
    r2 = simula_montecarlo(pesi, mu, cov, costi, c2, 10, 0.0)
    assert not np.array_equal(r1.montanti_finali, r2.montanti_finali)


def test_montecarlo_percentili_ordinati():
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=20_000, seed=7)
    res = simula_montecarlo(pesi, mu, cov, costi, config, 10, 0.0)
    p = res.percentili
    assert p[5] <= p[25] <= p[50] <= p[75] <= p[95]


def test_montecarlo_prob_shortfall_in_range():
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=20_000, seed=7, inflazione=0.02)
    res = simula_montecarlo(
        pesi, mu, cov, costi, config, 10, 0.0,
        definizione_shortfall=DefinizioneShortfall.REALE_NEGATIVO,
    )
    assert 0.0 <= res.prob_shortfall <= 1.0


def test_montecarlo_costi_riducono_montante():
    pesi, mu, cov, _ = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=20_000, seed=7, inflazione=0.0)
    senza = simula_montecarlo(pesi, mu, cov, np.array([0.0, 0.0]), config, 10, 0.0)
    con = simula_montecarlo(pesi, mu, cov, np.array([0.01, 0.01]), config, 10, 0.0)
    assert np.median(con.montanti_finali) < np.median(senza.montanti_finali)


def test_montecarlo_var_positivo_e_es_maggiore():
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=50_000, seed=7, confidenza_var=0.95)
    res = simula_montecarlo(pesi, mu, cov, costi, config, 10, 0.0)
    # ES di mercato >= VaR (la coda oltre il VaR ha perdita media >= VaR)
    assert res.expected_shortfall >= res.var


def test_montecarlo_dimensioni_incoerenti():
    pesi, mu, cov, costi = _setup_due_asset()
    config = ConfigSimulazione(n_simulazioni=1_000, seed=1)
    with pytest.raises(ValueError):
        simula_montecarlo(pesi, mu[:1], cov, costi, config, 10, 0.0)


# --------------------------- Motore vincoli ------------------------------- #
def _proposta_valida_demo():
    # pesi entro le bande demo, liquidita 5%, illiquido (private) 10%
    return Proposta(nome="test", pesi={
        "Liquidita": 0.05,
        "Govt EUR": 0.30,
        "Corporate": 0.15,
        "Equity DM": 0.25,
        "Equity EM": 0.10,
        "Real assets": 0.05,
        "Private markets": 0.10,
    })


def test_vincoli_proposta_valida():
    cma, comparto = cma_demo(), comparto_demo()
    esiti = verifica_vincoli(_proposta_valida_demo(), comparto, cma)
    # nessun vincolo violato
    assert all(e.stato != Stato.VIOLATO for e in esiti)


def test_vincoli_illiquido_oltre_limite():
    cma, comparto = cma_demo(), comparto_demo()
    # private markets 15% (max comparto 15%, peso_max asset 15%): al limite
    # portiamo a violazione: 0.20 supera sia banda asset sia quota comparto
    p = Proposta(nome="test", pesi={
        "Liquidita": 0.05, "Govt EUR": 0.25, "Corporate": 0.15,
        "Equity DM": 0.20, "Equity EM": 0.10, "Real assets": 0.05,
        "Private markets": 0.20,
    })
    esiti = verifica_vincoli(p, comparto, cma)
    illiquida = next(e for e in esiti if e.nome == "Quota illiquida")
    assert illiquida.stato == Stato.VIOLATO
    assert riepilogo_stato(esiti) == Stato.VIOLATO


def test_vincoli_liquidita_sotto_minimo():
    cma, comparto = cma_demo(), comparto_demo()
    # liquidita 0% < minimo 5%
    p = Proposta(nome="test", pesi={
        "Liquidita": 0.00, "Govt EUR": 0.35, "Corporate": 0.15,
        "Equity DM": 0.25, "Equity EM": 0.10, "Real assets": 0.05,
        "Private markets": 0.10,
    })
    esiti = verifica_vincoli(p, comparto, cma)
    liq = next(e for e in esiti if e.nome == "Liquidita minima")
    assert liq.stato == Stato.VIOLATO


def test_vincoli_proposta_incoerente_con_cma():
    cma, comparto = cma_demo(), comparto_demo()
    p = Proposta(nome="x", pesi={"Liquidita": 1.0})
    with pytest.raises(ValueError):
        verifica_vincoli(p, comparto, cma)
