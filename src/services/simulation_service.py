"""Service layer per la simulazione CMA avanzata e gli stress test (M6).

Facade tra dominio e motori: la pagina Streamlit chiama questi servizi, mai
direttamente distributions/path_engine/stress_engine. Qui avviene la conversione dai
modelli di dominio agli array ordinati e l'orchestrazione dei calcoli.

Nessuna formula finanziaria implementata qui: solo orchestrazione.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.calculations.metrics import matrice_covarianza, rendimento_reale
from src.calculations.risk_metrics import (
    bande_percentili,
    expected_shortfall_mercato,
    percentili,
    prob_shortfall,
    shortfall_medio_condizionato,
    var_perdita,
)
from src.domain.models import (
    CMASet,
    Comparto,
    DefinizioneShortfall,
    Proposta,
)
from src.simulations.distributions import campiona_rendimenti
from src.simulations.path_engine import (
    converti_covarianza_annua_a_periodo,
    converti_rendimento_annuo_a_periodo,
    evolvi_percorsi,
)
from src.stress_testing.scenarios import ScenarioStress
from src.stress_testing.stress_engine import RisultatoStress, applica_stress, effetto_su_quote


@dataclass
class ParametriSimulazioneCMA:
    """Parametri configurabili della simulazione CMA avanzata."""

    distribuzione: str = "normale"   # "normale" | "t"
    df: float = 5                    # gradi di liberta' (se t)
    orizzonte_anni: int = 15
    periodi_per_anno: int = 1        # 1 annuale, 12 mensile
    n_simulazioni: int = 10_000
    seed: int = 42
    inflazione: float = 0.02
    ribilanciamento: bool = True
    confidenza_var: float = 0.95     # DEC-002 (provvisorio, configurabile)


@dataclass
class RisultatoSimulazioneCMA:
    montanti_reali: np.ndarray
    serie_montanti: np.ndarray
    bande_serie: dict[int, np.ndarray]
    max_drawdown: np.ndarray
    rend_geom_reale: np.ndarray
    percentili_montante: dict[int, float]
    prob_shortfall: float
    shortfall_medio: float
    var: float
    expected_shortfall: float
    max_drawdown_mediano: float
    parametri: ParametriSimulazioneCMA
    definizione_shortfall: DefinizioneShortfall


def _ordina(cma: CMASet, proposta: Proposta):
    if not proposta.coerente_con(cma):
        raise ValueError("Proposta non coerente con le asset class del CMASet")
    nomi = [ac.nome for ac in cma.asset_class]
    pesi = np.array([proposta.pesi[n] for n in nomi], dtype=float)
    mu = np.array([ac.mu_nominale for ac in cma.asset_class], dtype=float)
    sigma = np.array([ac.sigma for ac in cma.asset_class], dtype=float)
    costi = np.array([ac.costo for ac in cma.asset_class], dtype=float)
    return nomi, pesi, mu, sigma, costi


def _soglia_shortfall(
    definizione: DefinizioneShortfall,
    rend_geom_reale: np.ndarray,
    rend_geom_nom: np.ndarray,
    obiettivo: float,
    inflazione: float,
):
    """Restituisce (serie_metrica, soglia) per la definizione di shortfall attiva."""
    if definizione == DefinizioneShortfall.REALE_NEGATIVO:
        return rend_geom_reale, 0.0
    if definizione == DefinizioneShortfall.REALE_SOTTO_OBIETTIVO:
        return rend_geom_reale, obiettivo
    if definizione == DefinizioneShortfall.NOMINALE_NEGATIVO:
        return rend_geom_nom, 0.0
    if definizione == DefinizioneShortfall.SOTTO_INFLAZIONE:
        return rend_geom_nom, inflazione
    # MONTANTE_SOTTO_SOGLIA gestito a parte dal chiamante
    return rend_geom_reale, 0.0


def esegui_simulazione_cma(
    cma: CMASet, proposta: Proposta, comparto: Comparto, par: ParametriSimulazioneCMA
) -> RisultatoSimulazioneCMA:
    """Esegue la simulazione CMA avanzata (normale o t, multi-periodo)."""
    _, pesi, mu, sigma, costi = _ordina(cma, proposta)
    corr = np.array(cma.correlazioni.valori, dtype=float)
    cov_annua = matrice_covarianza(sigma, corr)
    costo_annuo = float(pesi @ costi)

    n_periodi = par.orizzonte_anni * par.periodi_per_anno
    mu_periodo = converti_rendimento_annuo_a_periodo(mu, par.periodi_per_anno)
    cov_periodo = converti_covarianza_annua_a_periodo(cov_annua, par.periodi_per_anno)

    rng = np.random.default_rng(par.seed)
    rend = campiona_rendimenti(
        mu_periodo, cov_periodo, (par.n_simulazioni, n_periodi), rng,
        distribuzione=par.distribuzione, df=par.df,
    )

    perc = evolvi_percorsi(
        rend, pesi, costo_annuo, par.periodi_per_anno,
        ribilanciamento=par.ribilanciamento,
    )
    montante_nom = perc.montanti_finali
    # caso limite numerico: un percorso puo' azzerare il capitale (perdita cumulata
    # >= 100%). Si applica un floor minimo positivo per evitare potenze di base
    # negativa nel rendimento geometrico; questi scenari restano correttamente
    # classificati come shortfall.
    montante_nom = np.maximum(montante_nom, 1e-12)
    deflatore = (1.0 + par.inflazione) ** par.orizzonte_anni
    montante_reale = montante_nom / deflatore

    rend_geom_reale = montante_reale ** (1.0 / par.orizzonte_anni) - 1.0
    rend_geom_nom = montante_nom ** (1.0 / par.orizzonte_anni) - 1.0

    # shortfall secondo definizione attiva
    definizione = comparto.shortfall.definizione
    if definizione == DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA:
        soglia = comparto.shortfall.soglia_montante or 1.0
        p_sf = prob_shortfall(montante_reale, soglia)
        sf_medio = shortfall_medio_condizionato(montante_reale, soglia)
    else:
        serie, soglia = _soglia_shortfall(
            definizione, rend_geom_reale, rend_geom_nom,
            comparto.obiettivo_rendimento, par.inflazione,
        )
        p_sf = prob_shortfall(serie, soglia)
        sf_medio = shortfall_medio_condizionato(serie, soglia)

    # VaR / ES di mercato sui rendimenti reali finali (perdita = 1 - montante)
    perdite = 1.0 - montante_reale
    var = var_perdita(perdite, par.confidenza_var)
    es = expected_shortfall_mercato(perdite, par.confidenza_var)

    serie_reale = perc.serie_montanti / deflatore
    return RisultatoSimulazioneCMA(
        montanti_reali=montante_reale,
        serie_montanti=serie_reale,
        bande_serie=bande_percentili(serie_reale, (5, 50, 95)),
        max_drawdown=perc.max_drawdown,
        rend_geom_reale=rend_geom_reale,
        percentili_montante=percentili(montante_reale),
        prob_shortfall=p_sf,
        shortfall_medio=sf_medio,
        var=var,
        expected_shortfall=es,
        max_drawdown_mediano=float(np.median(perc.max_drawdown)),
        parametri=par,
        definizione_shortfall=definizione,
    )


def esegui_stress(
    cma: CMASet, proposta: Proposta, scenario: ScenarioStress
) -> tuple[RisultatoStress, dict[str, float]]:
    """Applica uno scenario di stress e calcola anche l'effetto sulle quote."""
    risultato = applica_stress(proposta, cma, scenario)
    quote = effetto_su_quote(proposta, cma, risultato)
    return risultato, quote
