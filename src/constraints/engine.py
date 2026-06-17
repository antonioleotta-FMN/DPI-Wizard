"""Motore di verifica dei vincoli (M3).

Verifica una proposta di Asset Allocation rispetto a tre famiglie di vincoli:
  - INTERNI/STRATEGICI: bande min/max per asset class, liquidita minima, quota
    massima illiquida (parametri del Comparto e delle AssetClass).
  - NORMATIVI: i controlli che l'app puo' ragionevolmente effettuare in modo
    automatico. NB (Ag.2): l'app NON sostituisce la valutazione legale o degli organi
    del Fondo; i limiti normativi puntuali (es. DM 166/2014) vanno parametrizzati e
    validati internamente, non sono cablati come verita' assolute.

Ogni vincolo produce un EsitoVincolo con stato a semaforo:
  OK        rispettato
  WARNING   vicino al limite (entro una soglia di prossimita')
  VIOLATO   non rispettato

Funzioni pure: nessuna dipendenza da Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

import numpy as np

from src.domain.models import CMASet, Comparto, Proposta


class Stato(str, Enum):
    OK = "OK"
    WARNING = "WARNING"
    VIOLATO = "VIOLATO"


class TipoVincolo(str, Enum):
    INTERNO = "interno"
    STRATEGICO = "strategico"
    NORMATIVO = "normativo"


@dataclass
class EsitoVincolo:
    nome: str
    tipo: TipoVincolo
    stato: Stato
    valore: float
    limite: float
    messaggio: str


# Soglia di prossimita' per emettere WARNING (5% del limite, relativo)
_MARGINE_WARNING = 0.05


def _stato_max(valore: float, limite_max: float) -> Stato:
    if valore > limite_max + 1e-12:
        return Stato.VIOLATO
    if valore >= limite_max * (1.0 - _MARGINE_WARNING):
        return Stato.WARNING
    return Stato.OK


def _stato_min(valore: float, limite_min: float) -> Stato:
    if valore < limite_min - 1e-12:
        return Stato.VIOLATO
    if valore <= limite_min * (1.0 + _MARGINE_WARNING):
        return Stato.WARNING
    return Stato.OK


def verifica_vincoli(
    proposta: Proposta, comparto: Comparto, cma: CMASet
) -> list[EsitoVincolo]:
    """Verifica una proposta e restituisce la lista degli esiti."""
    if not proposta.coerente_con(cma):
        raise ValueError(
            "La proposta non e' coerente con le asset class del CMASet"
        )

    esiti: list[EsitoVincolo] = []
    ac_per_nome = {ac.nome: ac for ac in cma.asset_class}

    # --- Bande min/max per asset class (interni/strategici) ---
    for nome, peso in proposta.pesi.items():
        ac = ac_per_nome[nome]
        if peso > ac.peso_max + 1e-12:
            esiti.append(EsitoVincolo(
                nome=f"Peso max {nome}", tipo=TipoVincolo.STRATEGICO,
                stato=Stato.VIOLATO, valore=peso, limite=ac.peso_max,
                messaggio=f"Peso {peso:.1%} sopra il massimo {ac.peso_max:.1%}",
            ))
        elif peso < ac.peso_min - 1e-12:
            esiti.append(EsitoVincolo(
                nome=f"Peso min {nome}", tipo=TipoVincolo.STRATEGICO,
                stato=Stato.VIOLATO, valore=peso, limite=ac.peso_min,
                messaggio=f"Peso {peso:.1%} sotto il minimo {ac.peso_min:.1%}",
            ))

    # --- Quota illiquida massima (interno) ---
    quota_illiquida = sum(
        peso for nome, peso in proposta.pesi.items()
        if ac_per_nome[nome].illiquidita
    )
    esiti.append(EsitoVincolo(
        nome="Quota illiquida", tipo=TipoVincolo.INTERNO,
        stato=_stato_max(quota_illiquida, comparto.quota_max_illiquida),
        valore=quota_illiquida, limite=comparto.quota_max_illiquida,
        messaggio=f"Quota illiquida {quota_illiquida:.1%} "
                  f"(max {comparto.quota_max_illiquida:.1%})",
    ))

    # --- Liquidita minima (interno): asset class denominata 'Liquidita' ---
    quota_liquidita = sum(
        peso for nome, peso in proposta.pesi.items()
        if "liquid" in nome.lower() and not ac_per_nome[nome].illiquidita
    )
    esiti.append(EsitoVincolo(
        nome="Liquidita minima", tipo=TipoVincolo.INTERNO,
        stato=_stato_min(quota_liquidita, comparto.liquidita_minima),
        valore=quota_liquidita, limite=comparto.liquidita_minima,
        messaggio=f"Liquidita {quota_liquidita:.1%} "
                  f"(min {comparto.liquidita_minima:.1%})",
    ))

    # --- Somma pesi = 1 (controllo di coerenza, normativo/strutturale) ---
    somma = sum(proposta.pesi.values())
    esiti.append(EsitoVincolo(
        nome="Somma pesi", tipo=TipoVincolo.NORMATIVO,
        stato=Stato.OK if abs(somma - 1.0) < 1e-6 else Stato.VIOLATO,
        valore=somma, limite=1.0,
        messaggio=f"Somma pesi {somma:.4f}",
    ))

    return esiti


def riepilogo_stato(esiti: list[EsitoVincolo]) -> Stato:
    """Stato complessivo: VIOLATO se almeno un vincolo violato, WARNING se almeno un
    warning, altrimenti OK."""
    if any(e.stato == Stato.VIOLATO for e in esiti):
        return Stato.VIOLATO
    if any(e.stato == Stato.WARNING for e in esiti):
        return Stato.WARNING
    return Stato.OK
