"""Test del motore dei percorsi multi-periodo (M6)."""

import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.simulations.path_engine import (  # noqa: E402
    converti_covarianza_annua_a_periodo,
    converti_rendimento_annuo_a_periodo,
    evolvi_percorsi,
)


def test_montante_composto_senza_costi():
    # 1 scenario, 3 anni, 1 asset, rendimento costante 10% -> 1.1^3
    rend = np.full((1, 3, 1), 0.10)
    res = evolvi_percorsi(rend, np.array([1.0]), costo_annuo=0.0, periodi_per_anno=1)
    assert abs(res.montanti_finali[0] - 1.1 ** 3) < 1e-12


def test_costi_riducono_montante():
    rend = np.full((1, 5, 1), 0.06)
    senza = evolvi_percorsi(rend, np.array([1.0]), 0.0, 1)
    con = evolvi_percorsi(rend, np.array([1.0]), 0.01, 1)
    assert con.montanti_finali[0] < senza.montanti_finali[0]


def test_ribilanciamento_vs_buy_and_hold_differiscono():
    rng = np.random.default_rng(0)
    rend = rng.normal(0.05, 0.15, size=(2000, 10, 2))
    pesi = np.array([0.5, 0.5])
    reb = evolvi_percorsi(rend, pesi, 0.0, 1, ribilanciamento=True)
    bh = evolvi_percorsi(rend, pesi, 0.0, 1, ribilanciamento=False)
    # le mediane non devono coincidere esattamente
    assert abs(np.median(reb.montanti_finali) - np.median(bh.montanti_finali)) > 1e-6


def test_drawdown_su_serie_nota():
    # serie che sale a 1.2 poi scende a 0.9: drawdown minimo = 0.9/1.2 - 1 = -0.25
    rend = np.array([[[0.2], [-0.25]]])  # 1 scenario, 2 periodi: *1.2 poi *0.75
    res = evolvi_percorsi(rend, np.array([1.0]), 0.0, 1)
    # serie: [1.0, 1.2, 0.9] -> max dd = (0.9-1.2)/1.2 = -0.25
    assert abs(res.max_drawdown[0] - (-0.25)) < 1e-12


def test_flussi_contributi_aumentano_montante():
    rend = np.zeros((1, 3, 1))  # rendimento nullo
    contributi = np.array([0.1, 0.1, 0.1])
    res = evolvi_percorsi(rend, np.array([1.0]), 0.0, 1, contributi=contributi)
    # capitale 1 + 3 contributi da 0.1, rendimento nullo -> 1.3
    assert abs(res.montanti_finali[0] - 1.3) < 1e-12


def test_conversione_frequenza():
    # rendimento annuo 12.68% -> mensile ~1% (1.01^12 - 1 = 0.1268)
    mu_mensile = converti_rendimento_annuo_a_periodo(np.array([0.1268]), 12)
    assert abs(mu_mensile[0] - 0.01) < 1e-3
    # covarianza annua / 12
    cov = np.array([[0.04]])
    assert np.allclose(converti_covarianza_annua_a_periodo(cov, 12), cov / 12)
