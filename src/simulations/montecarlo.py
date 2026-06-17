"""Motore di simulazione Monte Carlo (M3).

Prima versione (MVP): rendimenti annui da distribuzione NORMALE MULTIVARIATA, con
orizzonti configurabili, costi, inflazione deterministica, ribilanciamento annuale,
seed riproducibile. Produce percentili, probabilita di shortfall (secondo la
definizione attiva, DEC-001), VaR ed Expected Shortfall (DEC-002).

Le metodologie avanzate (distribuzione t, bootstrap, regimi, correlazioni stressate)
sono previste dall'architettura ma NON implementate nell'MVP: la firma di
`simula_montecarlo` e l'oggetto RisultatoSimulazione restano stabili per accoglierle.

Funzioni pure: nessuna dipendenza da Streamlit. La conversione dai modelli di dominio
ad array ordinati e responsabilita di src/services.

LIMITE METODOLOGICO DICHIARATO (rischio di modello): la normale sottostima la
probabilita di eventi estremi (code sottili). I risultati delle code (VaR/ES a
confidenza elevata) vanno letti con cautela. Questo giustifica le estensioni post-MVP.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.domain.models import (
    ConfigSimulazione,
    DefinizioneShortfall,
)


@dataclass
class RisultatoSimulazione:
    """Output di una simulazione Monte Carlo.

    montanti_finali     array (n_sim,) del montante reale o nominale a fine orizzonte,
                        per 1 unita di capitale iniziale (montante = 1 -> nessuna
                        crescita)
    rendimenti_annui_medi array (n_sim,) del rendimento annuo geometrico equivalente
    percentili          dict {percentile: valore montante}
    prob_shortfall      probabilita di shortfall secondo la definizione attiva
    var                 Value at Risk (perdita, segno positivo) a confidenza/orizzonte
    expected_shortfall  Expected Shortfall di mercato (CVaR), perdita media oltre VaR
    es_mancato_obiettivo perdita media (in termini di montante reale) negli scenari
                        sotto la soglia di shortfall; concetto DISTINTO dall'ES di
                        mercato (vedi prompt sez. 8)
    orizzonte_anni      orizzonte usato
    definizione_shortfall definizione attiva, per tracciabilita
    """

    montanti_finali: np.ndarray
    rendimenti_annui_medi: np.ndarray
    percentili: dict[int, float]
    prob_shortfall: float
    var: float
    expected_shortfall: float
    es_mancato_obiettivo: float
    orizzonte_anni: int
    definizione_shortfall: DefinizioneShortfall


def _campiona_rendimenti(
    mu: np.ndarray,
    cov: np.ndarray,
    n_sim: int,
    n_anni: int,
    rng: np.random.Generator,
) -> np.ndarray:
    """Campiona rendimenti annui multivariati normali.

    Restituisce array (n_sim, n_anni, n_asset).
    """
    n_asset = mu.shape[0]
    # multivariate_normal genera (n_sim*n_anni, n_asset)
    campioni = rng.multivariate_normal(mu, cov, size=(n_sim, n_anni))
    return campioni.reshape(n_sim, n_anni, n_asset)


def _evolvi_montante(
    rend_asset: np.ndarray,
    pesi: np.ndarray,
    costi: np.ndarray,
    inflazione: float,
    ribilanciamento_annuale: bool,
) -> np.ndarray:
    """Evolve il montante reale per ogni scenario.

    rend_asset  (n_sim, n_anni, n_asset) rendimenti nominali annui per asset
    Restituisce (n_sim,) montante REALE a fine orizzonte per 1 unita di capitale.

    Con ribilanciamento annuale: ogni anno il rendimento di portafoglio e' la media
    pesata (pesi costanti) dei rendimenti di asset, al netto dei costi; il montante
    nominale si capitalizza e a fine orizzonte si deflaziona per l'inflazione composta.
    """
    n_sim, n_anni, _ = rend_asset.shape
    costo_pf = float(pesi @ costi)  # costo annuo di portafoglio (DEC-007)

    if ribilanciamento_annuale:
        # rendimento di portafoglio annuo (n_sim, n_anni)
        rend_pf = rend_asset @ pesi - costo_pf
        montante_nom = np.prod(1.0 + rend_pf, axis=1)
    else:
        # buy & hold non previsto nell'MVP (DEC-008); ramo lasciato per estensione
        raise NotImplementedError("Ribilanciamento buy & hold non previsto nell'MVP")

    deflatore = (1.0 + inflazione) ** n_anni
    montante_reale = montante_nom / deflatore
    return montante_reale


def _calcola_prob_shortfall(
    montante_reale: np.ndarray,
    rend_annuo_geom_reale: np.ndarray,
    rend_annuo_geom_nom: np.ndarray,
    config: ConfigSimulazione,
    definizione: DefinizioneShortfall,
    obiettivo: float,
    soglia_montante: float | None,
) -> float:
    """Probabilita di shortfall secondo la definizione attiva (DEC-001)."""
    if definizione == DefinizioneShortfall.REALE_NEGATIVO:
        eventi = montante_reale < 1.0
    elif definizione == DefinizioneShortfall.REALE_SOTTO_OBIETTIVO:
        eventi = rend_annuo_geom_reale < obiettivo
    elif definizione == DefinizioneShortfall.NOMINALE_NEGATIVO:
        eventi = rend_annuo_geom_nom < 0.0
    elif definizione == DefinizioneShortfall.SOTTO_INFLAZIONE:
        eventi = rend_annuo_geom_nom < config.inflazione
    elif definizione == DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA:
        if soglia_montante is None:
            raise ValueError("soglia_montante richiesta per MONTANTE_SOTTO_SOGLIA")
        eventi = montante_reale < soglia_montante
    else:  # pragma: no cover
        raise ValueError(f"Definizione di shortfall non gestita: {definizione}")
    return float(np.mean(eventi))


def simula_montecarlo(
    pesi: np.ndarray,
    mu: np.ndarray,
    cov: np.ndarray,
    costi: np.ndarray,
    config: ConfigSimulazione,
    orizzonte_anni: int,
    obiettivo_rendimento: float,
    definizione_shortfall: DefinizioneShortfall = DefinizioneShortfall.REALE_NEGATIVO,
    soglia_montante: float | None = None,
    percentili: tuple[int, ...] = (5, 25, 50, 75, 95),
) -> RisultatoSimulazione:
    """Esegue la simulazione Monte Carlo normale multivariata.

    INPUT
        pesi, mu, cov, costi   array ordinati coerentemente (n_asset)
        config                 ConfigSimulazione (seed, n_sim, confidenza/orizzonte VaR,
                               inflazione, ribilanciamento)
        orizzonte_anni         orizzonte del comparto (per shortfall previdenziale)
        obiettivo_rendimento   obiettivo annuo del comparto (per def. sotto-obiettivo)
        definizione_shortfall  definizione attiva (DEC-001)
        soglia_montante        soglia assoluta, solo se def. = MONTANTE_SOTTO_SOGLIA
    OUTPUT
        RisultatoSimulazione
    """
    pesi = np.asarray(pesi, dtype=float).ravel()
    mu = np.asarray(mu, dtype=float).ravel()
    costi = np.asarray(costi, dtype=float).ravel()
    cov = np.asarray(cov, dtype=float)

    n = pesi.shape[0]
    if not (mu.shape[0] == costi.shape[0] == n and cov.shape == (n, n)):
        raise ValueError("Dimensioni di pesi/mu/costi/cov non coerenti")

    rng = np.random.default_rng(config.seed)

    # --- shortfall previdenziale: orizzonte del comparto ---
    rend_asset = _campiona_rendimenti(mu, cov, config.n_simulazioni, orizzonte_anni, rng)
    montante_reale = _evolvi_montante(
        rend_asset, pesi, costi, config.inflazione, config.ribilanciamento_annuale
    )
    # rendimento annuo geometrico equivalente (reale e nominale)
    rend_geom_reale = montante_reale ** (1.0 / orizzonte_anni) - 1.0
    montante_nom = montante_reale * (1.0 + config.inflazione) ** orizzonte_anni
    rend_geom_nom = montante_nom ** (1.0 / orizzonte_anni) - 1.0

    perc = {p: float(np.percentile(montante_reale, p)) for p in percentili}

    prob_sf = _calcola_prob_shortfall(
        montante_reale, rend_geom_reale, rend_geom_nom,
        config, definizione_shortfall, obiettivo_rendimento, soglia_montante,
    )

    # ES "mancato obiettivo" (DEC-001/sez.8): media della perdita di montante reale
    # rispetto a 1 (potere d'acquisto) negli scenari di shortfall reale.
    eventi_reale = montante_reale < 1.0
    if np.any(eventi_reale):
        es_mancato = float(np.mean(1.0 - montante_reale[eventi_reale]))
    else:
        es_mancato = 0.0

    # --- VaR / ES di mercato: orizzonte breve (DEC-002), perdita su 1 unita ---
    rend_mkt = _campiona_rendimenti(
        mu, cov, config.n_simulazioni, config.orizzonte_var_anni, rng
    )
    montante_mkt = _evolvi_montante(
        rend_mkt, pesi, costi, 0.0, config.ribilanciamento_annuale
    )  # VaR/ES di mercato in termini nominali: inflazione esclusa
    perdita = 1.0 - montante_mkt  # perdita positiva = montante < capitale
    alpha = config.confidenza_var
    var = float(np.percentile(perdita, alpha * 100.0))
    coda = perdita[perdita >= var]
    es_mercato = float(np.mean(coda)) if coda.size > 0 else var

    return RisultatoSimulazione(
        montanti_finali=montante_reale,
        rendimenti_annui_medi=rend_geom_reale,
        percentili=perc,
        prob_shortfall=prob_sf,
        var=var,
        expected_shortfall=es_mercato,
        es_mancato_obiettivo=es_mancato,
        orizzonte_anni=orizzonte_anni,
        definizione_shortfall=definizione_shortfall,
    )
