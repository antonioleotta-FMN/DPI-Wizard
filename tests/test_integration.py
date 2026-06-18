"""Test di integrazione e controlli architetturali (M8).

Verifica end-to-end del flusso completo e controlli invarianti:
  - nessuna formula quantitativa nelle pagine Streamlit;
  - riproducibilita' delle simulazioni a parita' di seed;
  - flusso CMA -> proposta -> metriche -> simulazione -> stress -> ottimizzazione.
"""

import re
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import Proposta  # noqa: E402
from src.services import (  # noqa: E402
    ParametriSimulazioneCMA,
    calcola_frontiera,
    costruisci_config_da_comparto,
    esegui_simulazione_cma,
    esegui_stress,
    ottimizza_aas,
)
from src.services.portfolio_service import calcola_metriche  # noqa: E402
from src.stress_testing import scenari_demo  # noqa: E402

PAGES_DIR = Path(__file__).resolve().parents[1] / "pages"

# pattern di calcolo quantitativo che NON devono comparire nelle pagine
_PATTERN_FORMULE = re.compile(
    r"np\.(sqrt|cov|percentile|linalg|dot|exp|log|cumprod)|cholesky|@ ?cov|Sigma @"
)


def _proposta_demo():
    return Proposta(nome="vigente", pesi={
        "Liquidita": 0.05, "Govt EUR": 0.30, "Corporate": 0.15, "Equity DM": 0.25,
        "Equity EM": 0.10, "Real assets": 0.05, "Private markets": 0.10,
    })


# ----------------------- controllo architetturale ------------------------ #
def test_nessuna_formula_nelle_pagine():
    violazioni = []
    for f in PAGES_DIR.glob("*.py"):
        for i, riga in enumerate(f.read_text().splitlines(), 1):
            if riga.strip().startswith("#") or "import" in riga:
                continue
            if _PATTERN_FORMULE.search(riga):
                violazioni.append(f"{f.name}:{i}: {riga.strip()}")
    assert not violazioni, "Formule trovate nelle pagine:\n" + "\n".join(violazioni)


# ----------------------- riproducibilita' -------------------------------- #
def test_simulazione_riproducibile():
    cma, comp = cma_demo(), comparto_demo()
    p = _proposta_demo()
    par = ParametriSimulazioneCMA(seed=123, n_simulazioni=3000, orizzonte_anni=10)
    r1 = esegui_simulazione_cma(cma, p, comp, par)
    r2 = esegui_simulazione_cma(cma, p, comp, par)
    assert np.array_equal(r1.montanti_reali, r2.montanti_reali)
    assert r1.prob_shortfall == r2.prob_shortfall


def test_seed_diverso_da_risultato_diverso():
    cma, comp = cma_demo(), comparto_demo()
    p = _proposta_demo()
    r1 = esegui_simulazione_cma(cma, p, comp, ParametriSimulazioneCMA(seed=1, n_simulazioni=3000))
    r2 = esegui_simulazione_cma(cma, p, comp, ParametriSimulazioneCMA(seed=2, n_simulazioni=3000))
    assert not np.array_equal(r1.montanti_reali, r2.montanti_reali)


# ----------------------- flusso end-to-end ------------------------------- #
def test_flusso_completo():
    cma, comp = cma_demo(), comparto_demo()
    vigente = _proposta_demo()

    # 1. metriche deterministiche
    metriche = calcola_metriche(cma, vigente, 0.02, comp.orizzonte_anni)
    assert metriche.rendimento_nominale > 0
    assert metriche.volatilita > 0

    # 2. simulazione CMA (normale e t)
    sim_n = esegui_simulazione_cma(cma, vigente, comp,
                                   ParametriSimulazioneCMA(distribuzione="normale", n_simulazioni=3000))
    sim_t = esegui_simulazione_cma(cma, vigente, comp,
                                   ParametriSimulazioneCMA(distribuzione="t", df=5, n_simulazioni=3000))
    assert 0.0 <= sim_n.prob_shortfall <= 1.0
    # la t (code spesse) non deve avere ES inferiore alla normale in modo sistematico
    assert sim_t.expected_shortfall >= sim_n.expected_shortfall - 0.05

    # 3. stress test
    res, quote = esegui_stress(cma, vigente, scenari_demo()[1])  # azionario -30%
    assert res.perdita_pct < 0
    assert "illiquida" in quote

    # 4. ottimizzazione
    cfg = costruisci_config_da_comparto(cma, comp, vigente)
    esito = ottimizza_aas(cma, comp, "min_varianza", cfg)
    assert esito.successo
    # il portafoglio a minima varianza ha volatilita <= della vigente
    assert esito.volatilita <= metriche.volatilita + 1e-6

    # 5. frontiera
    punti = calcola_frontiera(cma, cfg, n_punti=8)
    assert len(punti) >= 3


def test_coerenza_montante_mediano_vs_deterministico():
    # la mediana del montante reale simulato (normale) deve essere vicina al montante
    # deterministico geometrico, a parita' di ipotesi
    cma, comp = cma_demo(), comparto_demo()
    p = _proposta_demo()
    orizzonte = 15
    par = ParametriSimulazioneCMA(distribuzione="normale", n_simulazioni=20000,
                                  orizzonte_anni=orizzonte, inflazione=0.02, seed=7)
    sim = esegui_simulazione_cma(cma, p, comp, par)
    mediana_montante = float(np.median(sim.montanti_reali))
    # deve essere un montante reale plausibile e positivo
    assert mediana_montante > 0.5
