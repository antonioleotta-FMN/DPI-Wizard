"""Frontiera efficiente e diagnostica di infeasibilita' (M7).

frontiera_efficiente: genera punti minimizzando la varianza a rendimenti target
crescenti, restituendo i portafogli efficienti fattibili.

diagnostica_infeasibilita: quando un problema non e' risolvibile, prova a identificare
quali vincoli lo rendono infeasible, testandoli singolarmente.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np

from src.optimization.constraints import ConfigVincoli
from src.optimization.optimizer import RisultatoOttimizzazione, ottimizza


@dataclass
class PuntoFrontiera:
    rendimento_target: float
    rendimento: float
    volatilita: float
    pesi: np.ndarray


def frontiera_efficiente(
    cfg: ConfigVincoli,
    mu: np.ndarray,
    cov: np.ndarray,
    n_punti: int = 20,
) -> list[PuntoFrontiera]:
    """Genera la frontiera efficiente minimizzando la varianza a rendimenti target.

    I target vanno dal rendimento minimo al massimo ammessi dalle asset class. I punti
    non fattibili vengono semplicemente esclusi.
    """
    mu = np.asarray(mu, dtype=float)
    r_min, r_max = float(mu.min()), float(mu.max())
    targets = np.linspace(r_min, r_max, n_punti)

    punti: list[PuntoFrontiera] = []
    for r in targets:
        cfg_r = replace(cfg, rendimento_min=float(r))
        res = ottimizza("min_varianza", cfg_r, mu, cov)
        if res.successo and res.pesi is not None:
            w = res.pesi
            punti.append(PuntoFrontiera(
                rendimento_target=float(r),
                rendimento=float(w @ mu),
                volatilita=float(np.sqrt(max(w @ cov @ w, 0.0))),
                pesi=w,
            ))
    return punti


@dataclass
class EsitoDiagnostica:
    feasible: bool
    vincoli_problematici: list[str]
    messaggio: str


def diagnostica_infeasibilita(
    cfg: ConfigVincoli, mu: np.ndarray, cov: np.ndarray
) -> EsitoDiagnostica:
    """Identifica i vincoli che rendono il problema infeasible.

    Strategia: risolve prima il problema con i soli vincoli di base (budget + bounds);
    se gia' quello fallisce, il problema e' strutturalmente infeasible. Altrimenti
    aggiunge i vincoli uno per volta e segnala quelli che, aggiunti, causano il
    fallimento.
    """
    base = ConfigVincoli(n_asset=cfg.n_asset, bounds=cfg.bounds)
    res_base = ottimizza("min_varianza", base, mu, cov)
    if not res_base.successo:
        return EsitoDiagnostica(
            feasible=False, vincoli_problematici=["budget/bounds"],
            messaggio="Anche i soli vincoli di base non sono soddisfacibili: "
                      "controllare i bounds (la loro somma deve permettere pesi che "
                      "sommano a 1).",
        )

    problematici: list[str] = []
    # ciascun vincolo aggiunto isolatamente sopra la base
    prove = {
        "rendimento_min": replace(base, rendimento_min=cfg.rendimento_min),
        "volatilita_max": replace(base, volatilita_max=cfg.volatilita_max),
        "liquidita_min": replace(base, idx_liquidita=cfg.idx_liquidita,
                                 liquidita_min=cfg.liquidita_min),
        "illiquidita_max": replace(base, idx_illiquidi=cfg.idx_illiquidi,
                                   illiquidita_max=cfg.illiquidita_max),
        "duration": replace(base, durations=cfg.durations,
                            duration_min=cfg.duration_min, duration_max=cfg.duration_max),
        "turnover_max": replace(base, pesi_correnti=cfg.pesi_correnti,
                                turnover_max=cfg.turnover_max),
    }
    for nome, cfg_prova in prove.items():
        # salta se il vincolo non e' attivo
        attivo = any([
            nome == "rendimento_min" and cfg.rendimento_min is not None,
            nome == "volatilita_max" and cfg.volatilita_max is not None,
            nome == "liquidita_min" and cfg.liquidita_min is not None,
            nome == "illiquidita_max" and cfg.illiquidita_max is not None,
            nome == "duration" and (cfg.duration_min is not None or cfg.duration_max is not None),
            nome == "turnover_max" and cfg.turnover_max is not None,
        ])
        if not attivo:
            continue
        res = ottimizza("min_varianza", cfg_prova, mu, cov)
        if not res.successo:
            problematici.append(nome)

    if problematici:
        return EsitoDiagnostica(
            feasible=False, vincoli_problematici=problematici,
            messaggio="Vincoli incompatibili (isolatamente non soddisfacibili): "
                      + ", ".join(problematici)
                      + ". Allentare uno di questi puo' rendere il problema fattibile.",
        )
    return EsitoDiagnostica(
        feasible=True, vincoli_problematici=[],
        messaggio="I vincoli risultano singolarmente fattibili: l'infeasibilita' puo' "
                  "derivare dalla loro combinazione. Provare ad allentare i piu' "
                  "stringenti (es. rendimento minimo o turnover).",
    )
