"""Motore di stress test deterministico (M6).

Applica uno ScenarioStress a una proposta su un set CMA e calcola l'impatto
istantaneo sul portafoglio: variazione di prezzo per asset class, perdita complessiva,
contributo alla perdita per asset class, nuovo valore, effetto su liquidita e quota
illiquida, ed eventuali violazioni dei vincoli dopo lo shock.

Gli stress test sono DETERMINISTICI: non producono probabilita. Sono separati dal
Monte Carlo (modulo simulations).

Le formule obbligazionarie (duration/convexity) sono delegate a fixed_income_shocks.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

from src.domain.models import CMASet, Comparto, Proposta
from src.stress_testing.fixed_income_shocks import shock_tasso
from src.stress_testing.scenarios import ScenarioStress


@dataclass
class RisultatoStress:
    scenario: str
    perdita_pct: float                      # perdita complessiva, decimale (<0 = perdita)
    nuovo_valore: float                     # per 1 di capitale iniziale
    shock_per_asset: dict[str, float]       # variazione prezzo per asset class
    contributo_perdita: dict[str, float]    # contributo (peso * shock) per asset class
    note: list[str]


def _shock_asset(ac, scenario: ScenarioStress) -> tuple[float, list[str]]:
    """Variazione di prezzo per una singola asset class secondo lo scenario.

    Somma gli effetti di tutti gli shock il cui match e' contenuto nel nome dell'asset
    class (case-insensitive). Restituisce (variazione_prezzo, note).
    """
    nome_lower = ac.nome.lower()
    var_prezzo = 0.0
    note: list[str] = []
    for s in scenario.shock:
        if s.match.lower() not in nome_lower:
            continue
        if s.shock_rendimento_diretto is not None:
            var_prezzo += s.shock_rendimento_diretto
        if s.shock_tasso_delta_y is not None:
            if ac.duration is None:
                note.append(
                    f"{ac.nome}: shock di tasso ignorato (duration non disponibile)."
                )
            else:
                esito = shock_tasso(ac.duration, s.shock_tasso_delta_y, convexity=None)
                var_prezzo += esito.variazione_prezzo_pct
                note.append(f"{ac.nome}: {esito.nota}")
    return var_prezzo, note


def applica_stress(
    proposta: Proposta, cma: CMASet, scenario: ScenarioStress
) -> RisultatoStress:
    """Applica uno scenario di stress e calcola l'impatto sul portafoglio."""
    if not proposta.coerente_con(cma):
        raise ValueError("Proposta non coerente con le asset class del CMASet")

    shock_per_asset: dict[str, float] = {}
    contributo: dict[str, float] = {}
    note: list[str] = []
    perdita = 0.0

    for ac in cma.asset_class:
        peso = proposta.pesi[ac.nome]
        var_prezzo, note_ac = _shock_asset(ac, scenario)
        shock_per_asset[ac.nome] = var_prezzo
        contributo[ac.nome] = peso * var_prezzo
        perdita += peso * var_prezzo
        note.extend(note_ac)

    return RisultatoStress(
        scenario=scenario.nome,
        perdita_pct=perdita,
        nuovo_valore=1.0 + perdita,
        shock_per_asset=shock_per_asset,
        contributo_perdita=contributo,
        note=note,
    )


def effetto_su_quote(
    proposta: Proposta, cma: CMASet, risultato: RisultatoStress
) -> dict[str, float]:
    """Effetto dello shock sulle quote di liquidita e illiquidita.

    Dopo lo shock i pesi relativi cambiano (gli asset colpiti pesano meno). Restituisce
    le nuove quote di liquidita e illiquidita.
    """
    ac_per_nome = {ac.nome: ac for ac in cma.asset_class}
    nuovi_valori = {
        n: proposta.pesi[n] * (1.0 + risultato.shock_per_asset[n])
        for n in proposta.pesi
    }
    totale = sum(nuovi_valori.values())
    if totale <= 0:
        return {"liquidita": 0.0, "illiquida": 0.0}
    quota_liquidita = sum(
        v for n, v in nuovi_valori.items()
        if "liquid" in n.lower() and not ac_per_nome[n].illiquidita
    ) / totale
    quota_illiquida = sum(
        v for n, v in nuovi_valori.items() if ac_per_nome[n].illiquidita
    ) / totale
    return {"liquidita": quota_liquidita, "illiquida": quota_illiquida}
