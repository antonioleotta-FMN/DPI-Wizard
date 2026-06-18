"""Motore di ottimizzazione (M7).

Risolve problemi di Asset Allocation vincolata con scipy SLSQP. Espone:
  - ottimizza: risolve un problema dato obiettivo + vincoli;
  - arrotonda_pesi: arrotonda e rinormalizza, poi ri-verifica i vincoli.

Principio (sezione 5.7): in caso di infeasibilita' o mancata convergenza NON restituire
pesi apparentemente validi; segnalare il fallimento. La diagnostica e' in diagnostics.py.

Funzioni pure (deterministiche dato il punto iniziale): nessuna dipendenza da Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass, replace

import numpy as np
from scipy.optimize import minimize

from src.optimization.constraints import ConfigVincoli, costruisci_vincoli
from src.optimization.objectives import ContestoOttimizzazione, OBIETTIVI


@dataclass
class RisultatoOttimizzazione:
    successo: bool
    pesi: np.ndarray | None
    valore_obiettivo: float | None
    messaggio: str
    n_iterazioni: int


def _punto_iniziale(n: int, bounds, pesi_correnti=None) -> np.ndarray:
    """Punto iniziale fattibile: AAS vigente se disponibile, altrimenti equipesato."""
    if pesi_correnti is not None:
        return np.asarray(pesi_correnti, dtype=float)
    return np.full(n, 1.0 / n)


def _ottimizza_con_turnover(
    obiettivo: str, cfg: ConfigVincoli, ctx: ContestoOttimizzazione,
    tol: float, max_iter: int,
) -> RisultatoOttimizzazione:
    """Ottimizzazione con vincolo di turnover riformulato a variabili ausiliarie.

    Si introducono u_i >= |w_i - w0_i| con i vincoli u_i >= w_i - w0_i e
    u_i >= w0_i - w_i, e sum(u_i) <= T_max. Cosi' il problema resta liscio e SLSQP
    converge. Le variabili di decisione diventano [w (n), u (n)].
    """
    n = cfg.n_asset
    w0 = np.asarray(cfg.pesi_correnti, dtype=float)
    fun_obiettivo = OBIETTIVI[obiettivo]

    # i vincoli base sui soli w, riusati estraendo w dalla parte iniziale del vettore
    vincoli_w, bounds_w = costruisci_vincoli(
        replace(cfg, turnover_max=None, pesi_correnti=None), ctx.mu, ctx.cov
    )

    def _estrai_w(x):
        return x[:n]

    vincoli = []
    for v in vincoli_w:
        f = v["fun"]
        vincoli.append({"type": v["type"], "fun": (lambda x, f=f: f(_estrai_w(x)))})
    # u_i >= w_i - w0_i  ->  u_i - (w_i - w0_i) >= 0
    for i in range(n):
        vincoli.append({"type": "ineq",
                        "fun": (lambda x, i=i: x[n + i] - (x[i] - w0[i]))})
        vincoli.append({"type": "ineq",
                        "fun": (lambda x, i=i: x[n + i] + (x[i] - w0[i]))})
    # sum(u) <= T_max
    vincoli.append({"type": "ineq",
                    "fun": (lambda x, T=cfg.turnover_max: T - np.sum(x[n:]))})

    bounds = list(bounds_w) + [(0.0, 1.0)] * n  # u in [0,1]
    x0 = np.concatenate([w0, np.zeros(n)])

    res = minimize(
        (lambda x: fun_obiettivo(_estrai_w(x), ctx)), x0, method="SLSQP",
        bounds=bounds, constraints=vincoli,
        options={"ftol": tol, "maxiter": max_iter},
    )
    if not res.success:
        return RisultatoOttimizzazione(
            successo=False, pesi=None, valore_obiettivo=None,
            messaggio=f"Ottimizzazione non riuscita: {res.message}",
            n_iterazioni=int(res.get("nit", 0)),
        )
    pesi = np.asarray(res.x[:n], dtype=float)
    pesi[np.abs(pesi) < 1e-9] = 0.0
    s = pesi.sum()
    if s > 0:
        pesi = pesi / s
    return RisultatoOttimizzazione(
        successo=True, pesi=pesi, valore_obiettivo=float(res.fun),
        messaggio="Ottimizzazione riuscita.", n_iterazioni=int(res.get("nit", 0)),
    )


def ottimizza(
    obiettivo: str,
    cfg: ConfigVincoli,
    mu: np.ndarray,
    cov: np.ndarray,
    rf: float = 0.0,
    x0: np.ndarray | None = None,
    tol: float = 1e-9,
    max_iter: int = 500,
) -> RisultatoOttimizzazione:
    """Ottimizza l'allocazione per l'obiettivo dato, sotto i vincoli configurati."""
    if obiettivo not in OBIETTIVI:
        raise ValueError(f"Obiettivo non riconosciuto: {obiettivo!r}")
    ctx = ContestoOttimizzazione(mu=np.asarray(mu, float), cov=np.asarray(cov, float), rf=rf)

    # vincolo di turnover: usa la riformulazione a variabili ausiliarie (vincolo L1
    # non liscio, problematico per SLSQP in forma diretta)
    if cfg.turnover_max is not None and cfg.pesi_correnti is not None:
        return _ottimizza_con_turnover(obiettivo, cfg, ctx, tol, max_iter)

    fun_obiettivo = OBIETTIVI[obiettivo]
    vincoli, bounds = costruisci_vincoli(cfg, ctx.mu, ctx.cov)
    n = cfg.n_asset
    if x0 is None:
        x0 = _punto_iniziale(n, bounds, cfg.pesi_correnti)

    res = minimize(
        fun_obiettivo, x0, args=(ctx,), method="SLSQP",
        bounds=bounds, constraints=vincoli,
        options={"ftol": tol, "maxiter": max_iter},
    )

    if not res.success:
        return RisultatoOttimizzazione(
            successo=False, pesi=None, valore_obiettivo=None,
            messaggio=f"Ottimizzazione non riuscita: {res.message}",
            n_iterazioni=int(res.get("nit", 0)),
        )

    pesi = np.asarray(res.x, dtype=float)
    # pulizia numerica: azzera pesi minuscoli e rinormalizza
    pesi[np.abs(pesi) < 1e-9] = 0.0
    somma = pesi.sum()
    if somma > 0:
        pesi = pesi / somma

    return RisultatoOttimizzazione(
        successo=True, pesi=pesi, valore_obiettivo=float(res.fun),
        messaggio="Ottimizzazione riuscita.", n_iterazioni=int(res.get("nit", 0)),
    )


def arrotonda_pesi(pesi: np.ndarray, passo: float) -> np.ndarray:
    """Arrotonda i pesi al passo dato (es. 0.005) e rinormalizza a somma 1."""
    p = np.round(np.asarray(pesi, dtype=float) / passo) * passo
    s = p.sum()
    return p / s if s > 0 else p
