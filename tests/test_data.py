"""Test del data layer (M2): validazione PSD, dataset demo, IO Excel."""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.demo import cma_demo, comparto_demo, nomi_asset_class_demo  # noqa: E402
from src.data.excel_io import esporta_cma_excel, importa_cma_excel  # noqa: E402
from src.data.validation import (  # noqa: E402
    is_semidefinita_positiva,
    nearest_correlation_higham,
    valida_psd,
)


# --------------------------- validazione PSD ------------------------------ #
def test_matrice_identita_e_psd():
    assert is_semidefinita_positiva(np.eye(3))


def test_matrice_demo_e_psd():
    m = np.array(cma_demo().correlazioni.valori)
    esito = valida_psd(m)
    assert esito.is_psd
    assert esito.matrice_proposta is None


def test_matrice_non_psd_genera_proposta():
    # Matrice di correlazione strutturalmente valida ma NON PSD.
    # Tre asset perfettamente "incoerenti": rho_12=0.9, rho_13=0.9, rho_23=-0.9
    m = np.array([
        [1.0, 0.9, 0.9],
        [0.9, 1.0, -0.9],
        [0.9, -0.9, 1.0],
    ])
    assert not is_semidefinita_positiva(m)
    esito = valida_psd(m)
    assert not esito.is_psd
    assert esito.matrice_proposta is not None
    assert esito.differenza_max is not None
    # la proposta deve essere PSD, simmetrica, diagonale 1
    prop = esito.matrice_proposta
    assert is_semidefinita_positiva(prop)
    assert np.allclose(prop, prop.T, atol=1e-10)
    assert np.allclose(np.diag(prop), 1.0, atol=1e-10)
    # valori entro [-1, 1]
    assert prop.min() >= -1.0 - 1e-9 and prop.max() <= 1.0 + 1e-9


def test_higham_idempotente_su_matrice_gia_psd():
    # Su una matrice gia' PSD, la proposta deve essere praticamente invariata
    m = np.array(cma_demo().correlazioni.valori)
    prop = nearest_correlation_higham(m)
    assert np.allclose(prop, m, atol=1e-6)


def test_correzione_non_applicata_silenziosamente():
    # DEC-006: valida_psd NON modifica l'input
    m = np.array([
        [1.0, 0.9, 0.9],
        [0.9, 1.0, -0.9],
        [0.9, -0.9, 1.0],
    ])
    m_copia = m.copy()
    valida_psd(m)
    assert np.array_equal(m, m_copia)


# --------------------------- dataset demo --------------------------------- #
def test_demo_sette_asset_class():
    cma = cma_demo()
    assert len(cma.asset_class) == 7
    assert [ac.nome for ac in cma.asset_class] == nomi_asset_class_demo()


def test_demo_etichettato():
    assert "[DEMO]" in cma_demo().nome
    assert "[DEMO]" in comparto_demo().nome


def test_demo_private_markets_illiquido():
    cma = cma_demo()
    pm = next(ac for ac in cma.asset_class if ac.nome == "Private markets")
    assert pm.illiquidita is True


# --------------------------- IO Excel ------------------------------------- #
def test_round_trip_excel(tmp_path):
    cma = cma_demo()
    percorso = tmp_path / "cma.xlsx"
    esporta_cma_excel(cma, percorso)
    assert percorso.exists()

    ricaricato = importa_cma_excel(percorso)
    # nome, versione, numero asset class
    assert ricaricato.nome == cma.nome
    assert ricaricato.versione == cma.versione
    assert len(ricaricato.asset_class) == len(cma.asset_class)
    # confronto campo per campo dei mu e sigma
    for orig, ric in zip(cma.asset_class, ricaricato.asset_class):
        assert orig.nome == ric.nome
        assert abs(orig.mu_nominale - ric.mu_nominale) < 1e-12
        assert abs(orig.sigma - ric.sigma) < 1e-12
        assert orig.illiquidita == ric.illiquidita
    # matrice identica
    assert np.allclose(
        np.array(cma.correlazioni.valori),
        np.array(ricaricato.correlazioni.valori),
        atol=1e-12,
    )


def test_import_file_inesistente(tmp_path):
    with pytest.raises(FileNotFoundError):
        importa_cma_excel(tmp_path / "non_esiste.xlsx")
