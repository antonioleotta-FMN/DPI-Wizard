"""Service layer: facade tra modelli di dominio e calcoli/simulazioni (M3).

Le pagine Streamlit chiamano SOLO questi servizi, mai direttamente calculations,
simulations o constraints. Qui avviene la conversione dai modelli di dominio (nomi,
dizionari) agli array NumPy ORDINATI richiesti dai moduli numerici, garantendo che
l'ordine di pesi/mu/sigma/correlazioni sia sempre coerente.

Principio inviolabile: nessuna formula finanziaria e' implementata qui; questo modulo
orchestra soltanto.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.calculations.metrics import (
    matrice_covarianza,
    montante_atteso,
    rendimento_atteso,
    rendimento_geometrico,
    rendimento_netto_costi,
    rendimento_reale,
    risk_contribution,
    volatilita,
)
from src.constraints.engine import EsitoVincolo, Stato, riepilogo_stato, verifica_vincoli
from src.domain.models import CMASet, Comparto, ConfigSimulazione, Proposta
from src.simulations.montecarlo import RisultatoSimulazione, simula_montecarlo


@dataclass
class MetricheDeterministiche:
    rendimento_nominale: float
    rendimento_netto_costi: float
    rendimento_reale: float
    rendimento_geometrico_reale: float
    montante_reale_atteso: float
    volatilita: float
    quota_illiquida: float
    esposizione_valutaria_non_coperta: float
    duration_media: float
    contributi_rischio_pct: dict[str, float]


def _ordina(cma: CMASet, proposta: Proposta) -> tuple[list[str], np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Estrae array ordinati (nomi, pesi, mu, sigma, costi) secondo l'ordine del CMASet.

    L'ordine canonico e' quello delle asset class nel CMASet; i pesi della proposta
    vengono riallineati a quell'ordine.
    """
    if not proposta.coerente_con(cma):
        raise ValueError("Proposta non coerente con le asset class del CMASet")
    nomi = [ac.nome for ac in cma.asset_class]
    pesi = np.array([proposta.pesi[n] for n in nomi], dtype=float)
    mu = np.array([ac.mu_nominale for ac in cma.asset_class], dtype=float)
    sigma = np.array([ac.sigma for ac in cma.asset_class], dtype=float)
    costi = np.array([ac.costo for ac in cma.asset_class], dtype=float)
    return nomi, pesi, mu, sigma, costi


def _covarianza(cma: CMASet, sigma: np.ndarray) -> np.ndarray:
    corr = np.array(cma.correlazioni.valori, dtype=float)
    return matrice_covarianza(sigma, corr)


def calcola_metriche(
    cma: CMASet, proposta: Proposta, inflazione: float, orizzonte_anni: int = 1
) -> MetricheDeterministiche:
    """Calcola tutte le metriche deterministiche di una proposta.

    orizzonte_anni serve per il montante reale atteso (capitalizzazione composta del
    rendimento geometrico, DEC-003).
    """
    nomi, pesi, mu, sigma, costi = _ordina(cma, proposta)
    cov = _covarianza(cma, sigma)

    r_nom = rendimento_atteso(pesi, mu)
    r_net = rendimento_netto_costi(pesi, mu, costi)
    r_reale = rendimento_reale(r_net, inflazione)
    vol = volatilita(pesi, cov)
    # convenzione geometrica per le proiezioni (DEC-003)
    r_geom_reale = rendimento_geometrico(r_reale, vol)
    montante = montante_atteso(r_geom_reale, orizzonte_anni)

    ac_per_nome = {ac.nome: ac for ac in cma.asset_class}
    quota_illiquida = sum(
        proposta.pesi[n] for n in nomi if ac_per_nome[n].illiquidita
    )
    esp_val = sum(
        proposta.pesi[n] * (1.0 - ac_per_nome[n].copertura_valutaria)
        for n in nomi
        if ac_per_nome[n].valuta != "EUR"
    )
    durations = [
        (proposta.pesi[n], ac_per_nome[n].duration)
        for n in nomi
        if ac_per_nome[n].duration is not None
    ]
    peso_dur = sum(w for w, _ in durations)
    duration_media = (
        sum(w * d for w, d in durations) / peso_dur if peso_dur > 0 else 0.0
    )

    try:
        _, _, pctr = risk_contribution(pesi, cov)
        contributi = {n: float(p) for n, p in zip(nomi, pctr)}
    except ValueError:
        contributi = {n: 0.0 for n in nomi}

    return MetricheDeterministiche(
        rendimento_nominale=r_nom,
        rendimento_netto_costi=r_net,
        rendimento_reale=r_reale,
        rendimento_geometrico_reale=r_geom_reale,
        montante_reale_atteso=montante,
        volatilita=vol,
        quota_illiquida=quota_illiquida,
        esposizione_valutaria_non_coperta=esp_val,
        duration_media=duration_media,
        contributi_rischio_pct=contributi,
    )


def esegui_simulazione(
    cma: CMASet, proposta: Proposta, comparto: Comparto, config: ConfigSimulazione
) -> RisultatoSimulazione:
    """Esegue la simulazione Monte Carlo per una proposta su un comparto."""
    _, pesi, mu, sigma, costi = _ordina(cma, proposta)
    cov = _covarianza(cma, sigma)
    return simula_montecarlo(
        pesi=pesi, mu=mu, cov=cov, costi=costi, config=config,
        orizzonte_anni=comparto.orizzonte_anni,
        obiettivo_rendimento=comparto.obiettivo_rendimento,
        definizione_shortfall=comparto.shortfall.definizione,
        soglia_montante=comparto.shortfall.soglia_montante,
    )


def verifica(
    proposta: Proposta, comparto: Comparto, cma: CMASet
) -> tuple[list[EsitoVincolo], Stato]:
    """Verifica i vincoli e restituisce esiti + stato complessivo."""
    esiti = verifica_vincoli(proposta, comparto, cma)
    return esiti, riepilogo_stato(esiti)
