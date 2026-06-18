"""Service layer per l'ottimizzazione AAS (M7).

Facade tra dominio e motore di ottimizzazione: converte comparto, CMA e proposta di
partenza nei parametri del solver, costruisce la ConfigVincoli a partire dai limiti del
comparto e delle asset class, esegue l'ottimizzazione e prepara i risultati per la UI.

Nessuna formula implementata qui: orchestrazione.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.calculations.metrics import matrice_covarianza
from src.domain.models import CMASet, Comparto, Proposta
from src.optimization.constraints import ConfigVincoli, turnover
from src.optimization.optimizer import (
    RisultatoOttimizzazione,
    arrotonda_pesi,
    ottimizza,
)
from src.optimization.efficient_frontier import (
    EsitoDiagnostica,
    PuntoFrontiera,
    diagnostica_infeasibilita,
    frontiera_efficiente,
)


@dataclass
class EsitoOttimizzazioneAAS:
    successo: bool
    proposta: Proposta | None
    rendimento: float | None
    volatilita: float | None
    turnover_vs_vigente: float | None
    messaggio: str
    diagnostica: EsitoDiagnostica | None = None


def _arrays(cma: CMASet):
    nomi = [ac.nome for ac in cma.asset_class]
    mu = np.array([ac.mu_nominale for ac in cma.asset_class], dtype=float)
    sigma = np.array([ac.sigma for ac in cma.asset_class], dtype=float)
    corr = np.array(cma.correlazioni.valori, dtype=float)
    cov = matrice_covarianza(sigma, corr)
    return nomi, mu, cov


def costruisci_config_da_comparto(
    cma: CMASet, comparto: Comparto, proposta_vigente: Proposta | None,
    rendimento_min: float | None = None, volatilita_max: float | None = None,
    turnover_max: float | None = None,
) -> ConfigVincoli:
    """Costruisce la ConfigVincoli dai limiti di comparto e asset class."""
    nomi = [ac.nome for ac in cma.asset_class]
    bounds = [(ac.peso_min, ac.peso_max) for ac in cma.asset_class]
    idx_liquidita = [i for i, ac in enumerate(cma.asset_class)
                     if "liquid" in ac.nome.lower() and not ac.illiquidita]
    idx_illiquidi = [i for i, ac in enumerate(cma.asset_class) if ac.illiquidita]
    pesi_correnti = None
    if proposta_vigente is not None and proposta_vigente.coerente_con(cma):
        pesi_correnti = np.array([proposta_vigente.pesi[n] for n in nomi], dtype=float)

    return ConfigVincoli(
        n_asset=len(nomi),
        bounds=bounds,
        idx_liquidita=idx_liquidita,
        liquidita_min=comparto.liquidita_minima if comparto.liquidita_minima > 0 else None,
        idx_illiquidi=idx_illiquidi,
        illiquidita_max=comparto.quota_max_illiquida if comparto.quota_max_illiquida < 1 else None,
        rendimento_min=rendimento_min,
        volatilita_max=volatilita_max,
        pesi_correnti=pesi_correnti,
        turnover_max=turnover_max,
    )


def ottimizza_aas(
    cma: CMASet, comparto: Comparto, obiettivo: str, cfg: ConfigVincoli,
    nome_proposta: str = "Proposta ottimizzata", passo_arrotondamento: float | None = 0.005,
) -> EsitoOttimizzazioneAAS:
    """Esegue l'ottimizzazione e restituisce una proposta (o la diagnostica se fallisce)."""
    nomi, mu, cov = _arrays(cma)
    res = ottimizza(obiettivo, cfg, mu, cov)

    if not res.successo or res.pesi is None:
        diag = diagnostica_infeasibilita(cfg, mu, cov)
        return EsitoOttimizzazioneAAS(
            successo=False, proposta=None, rendimento=None, volatilita=None,
            turnover_vs_vigente=None, messaggio=res.messaggio, diagnostica=diag,
        )

    pesi = res.pesi
    if passo_arrotondamento:
        pesi = arrotonda_pesi(pesi, passo_arrotondamento)
        # ri-verifica dei bounds dopo arrotondamento
        for i, (lo, hi) in enumerate(cfg.bounds):
            if pesi[i] < lo - 1e-9 or pesi[i] > hi + 1e-9:
                # l'arrotondamento ha violato un bound: usa i pesi non arrotondati
                pesi = res.pesi
                break

    tov = None
    if cfg.pesi_correnti is not None:
        tov = turnover(pesi, cfg.pesi_correnti)

    proposta = Proposta(nome=nome_proposta, pesi={n: float(w) for n, w in zip(nomi, pesi)})
    return EsitoOttimizzazioneAAS(
        successo=True, proposta=proposta,
        rendimento=float(pesi @ mu),
        volatilita=float(np.sqrt(max(pesi @ cov @ pesi, 0.0))),
        turnover_vs_vigente=tov, messaggio=res.messaggio,
    )


def calcola_frontiera(cma: CMASet, cfg: ConfigVincoli, n_punti: int = 20) -> list[PuntoFrontiera]:
    """Calcola la frontiera efficiente sotto i vincoli configurati."""
    _, mu, cov = _arrays(cma)
    return frontiera_efficiente(cfg, mu, cov, n_punti)
