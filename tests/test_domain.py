"""Test di validazione dei modelli di dominio (M0).

Verificano che le regole di validazione Pydantic accettino input corretti e
respingano input non validi. Nessuna formula finanziaria e' testata qui.
"""

import sys
from pathlib import Path

import pytest
from pydantic import ValidationError

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.domain.models import (  # noqa: E402
    AssetClass,
    CMASet,
    Comparto,
    ConfigShortfall,
    DefinizioneShortfall,
    MatriceCorrelazione,
    Proposta,
)


# --------------------------- fixtures di base ------------------------------ #
def _asset(nome, mu=0.05, sigma=0.10, pmin=0.0, pmax=1.0):
    return AssetClass(nome=nome, mu_nominale=mu, sigma=sigma, peso_min=pmin, peso_max=pmax)


def _matrice_2x2(rho=0.3):
    return MatriceCorrelazione(
        etichette=["A", "B"], valori=[[1.0, rho], [rho, 1.0]]
    )


# --------------------------- AssetClass ------------------------------------ #
def test_asset_class_valida():
    ac = _asset("Equity", mu=0.06, sigma=0.18)
    assert ac.nome == "Equity"
    assert ac.valuta == "EUR"


def test_asset_class_bande_incoerenti():
    with pytest.raises(ValidationError):
        _asset("X", pmin=0.6, pmax=0.4)


def test_asset_class_sigma_negativa():
    with pytest.raises(ValidationError):
        AssetClass(nome="X", mu_nominale=0.05, sigma=-0.1)


# --------------------------- MatriceCorrelazione --------------------------- #
def test_matrice_valida():
    m = _matrice_2x2(0.5)
    assert m.valori[0][1] == 0.5


def test_matrice_non_simmetrica():
    with pytest.raises(ValidationError):
        MatriceCorrelazione(etichette=["A", "B"], valori=[[1.0, 0.3], [0.4, 1.0]])


def test_matrice_diagonale_non_unitaria():
    with pytest.raises(ValidationError):
        MatriceCorrelazione(etichette=["A", "B"], valori=[[0.9, 0.3], [0.3, 1.0]])


def test_matrice_valore_fuori_range():
    with pytest.raises(ValidationError):
        MatriceCorrelazione(etichette=["A", "B"], valori=[[1.0, 1.5], [1.5, 1.0]])


def test_matrice_dimensioni_incoerenti():
    with pytest.raises(ValidationError):
        MatriceCorrelazione(etichette=["A", "B", "C"], valori=[[1.0, 0.3], [0.3, 1.0]])


# --------------------------- CMASet ---------------------------------------- #
def test_cmaset_valido():
    cma = CMASet(
        nome="demo",
        asset_class=[_asset("A"), _asset("B")],
        correlazioni=_matrice_2x2(0.2),
    )
    assert len(cma.asset_class) == 2


def test_cmaset_etichette_disallineate():
    with pytest.raises(ValidationError):
        CMASet(
            nome="demo",
            asset_class=[_asset("A"), _asset("C")],
            correlazioni=_matrice_2x2(0.2),  # etichette A, B
        )


def test_cmaset_nomi_duplicati():
    with pytest.raises(ValidationError):
        CMASet(
            nome="demo",
            asset_class=[_asset("A"), _asset("A")],
            correlazioni=_matrice_2x2(0.2),
        )


# --------------------------- Proposta -------------------------------------- #
def test_proposta_valida():
    p = Proposta(nome="base", pesi={"A": 0.6, "B": 0.4})
    assert abs(sum(p.pesi.values()) - 1.0) < 1e-9


def test_proposta_somma_errata():
    with pytest.raises(ValidationError):
        Proposta(nome="base", pesi={"A": 0.6, "B": 0.5})


def test_proposta_peso_negativo():
    with pytest.raises(ValidationError):
        Proposta(nome="base", pesi={"A": 1.2, "B": -0.2})


def test_proposta_coerente_con_cma():
    cma = CMASet(
        nome="demo",
        asset_class=[_asset("A"), _asset("B")],
        correlazioni=_matrice_2x2(0.2),
    )
    assert Proposta(nome="p", pesi={"A": 0.5, "B": 0.5}).coerente_con(cma)
    assert not Proposta(nome="p", pesi={"A": 1.0}).coerente_con(cma)


# --------------------------- ConfigShortfall ------------------------------- #
def test_shortfall_default_reale_negativo():
    cs = ConfigShortfall()
    assert cs.definizione == DefinizioneShortfall.REALE_NEGATIVO


def test_shortfall_montante_richiede_soglia():
    with pytest.raises(ValidationError):
        ConfigShortfall(definizione=DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA)


def test_shortfall_montante_con_soglia():
    cs = ConfigShortfall(
        definizione=DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA, soglia_montante=1_000_000
    )
    assert cs.soglia_montante == 1_000_000


# --------------------------- Comparto -------------------------------------- #
def test_comparto_valido():
    c = Comparto(
        nome="Garantito",
        patrimonio=50_000_000,
        orizzonte_anni=10,
        obiettivo_rendimento=0.01,
    )
    assert c.shortfall.definizione == DefinizioneShortfall.REALE_NEGATIVO
