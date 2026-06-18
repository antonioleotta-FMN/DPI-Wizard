"""Test del motore di stress test deterministico (M6)."""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import Proposta  # noqa: E402
from src.stress_testing.fixed_income_shocks import shock_tasso  # noqa: E402
from src.stress_testing.scenarios import (  # noqa: E402
    ScenarioStress,
    ShockAssetClass,
    scenari_demo,
)
from src.stress_testing.stress_engine import (  # noqa: E402
    applica_stress,
    effetto_su_quote,
)


def _proposta():
    return Proposta(nome="test", pesi={
        "Liquidita": 0.05, "Govt EUR": 0.30, "Corporate": 0.15,
        "Equity DM": 0.25, "Equity EM": 0.10, "Real assets": 0.05,
        "Private markets": 0.10,
    })


# --------------------------- fixed income shocks -------------------------- #
def test_shock_tasso_solo_duration():
    # duration 5, +100bp -> dP/P = -5 * 0.01 = -0.05
    esito = shock_tasso(5.0, 0.01)
    assert abs(esito.variazione_prezzo_pct - (-0.05)) < 1e-12
    assert not esito.usata_convexity


def test_shock_tasso_con_convexity():
    # duration 5, convexity 50, +100bp -> -0.05 + 0.5*50*0.0001 = -0.05 + 0.0025
    esito = shock_tasso(5.0, 0.01, convexity=50.0)
    assert abs(esito.variazione_prezzo_pct - (-0.0475)) < 1e-12
    assert esito.usata_convexity


# --------------------------- stress engine -------------------------------- #
def test_stress_azionario_perdita_attesa():
    # scenario: equity -20%. Pesi equity DM 0.25 + EM 0.10 = 0.35 -> perdita 0.35*-0.20
    cma = cma_demo()
    scenario = ScenarioStress(
        nome="test", shock=[ShockAssetClass(match="equity", shock_rendimento_diretto=-0.20)]
    )
    res = applica_stress(_proposta(), cma, scenario)
    assert abs(res.perdita_pct - (0.35 * -0.20)) < 1e-12
    assert abs(res.nuovo_valore - (1.0 + 0.35 * -0.20)) < 1e-12


def test_stress_tasso_usa_duration():
    # govt (duration 7) e corporate (duration 5), +100bp
    # govt: 0.30 * (-7*0.01) = 0.30*-0.07; corporate: 0.15*(-5*0.01)=0.15*-0.05
    cma = cma_demo()
    scenario = ScenarioStress(
        nome="tassi",
        shock=[ShockAssetClass(match="govt", shock_tasso_delta_y=0.01),
               ShockAssetClass(match="corporate", shock_tasso_delta_y=0.01)],
    )
    res = applica_stress(_proposta(), cma, scenario)
    attesa = 0.30 * (-7 * 0.01) + 0.15 * (-5 * 0.01)
    assert abs(res.perdita_pct - attesa) < 1e-12


def test_stress_contributi_sommano_a_perdita():
    cma = cma_demo()
    res = applica_stress(_proposta(), cma, scenari_demo()[0])
    assert abs(sum(res.contributo_perdita.values()) - res.perdita_pct) < 1e-12


def test_effetto_su_quote_illiquida_cambia():
    cma = cma_demo()
    # scenario che colpisce gli illiquidi: la loro quota relativa scende
    scenario = scenari_demo()[4]  # "Illiquidi sotto stress"
    res = applica_stress(_proposta(), cma, scenario)
    quote = effetto_su_quote(_proposta(), cma, res)
    assert quote["illiquida"] < 0.10  # era 0.10 (private markets) prima dello shock


def test_stress_proposta_incoerente():
    cma = cma_demo()
    p = Proposta(nome="x", pesi={"Liquidita": 1.0})
    with pytest.raises(ValueError):
        applica_stress(p, cma, scenari_demo()[0])


def test_scenari_demo_etichettati():
    for s in scenari_demo():
        assert "[DEMO]" in s.nome
