"""Gestione dello stato condiviso tra le pagine Streamlit (M4).

Centralizza l'inizializzazione del session_state e l'accesso agli oggetti di dominio
correnti (CMA, comparto, proposte). Le pagine importano da qui invece di manipolare
direttamente st.session_state, cosi' la struttura dello stato resta in un solo posto.

Nessuna formula finanziaria: solo stato e orchestrazione leggera.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

# Rende importabile src/ da qualunque pagina
_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import (  # noqa: E402
    CMASet,
    Comparto,
    ConfigSimulazione,
    Proposta,
)

# Chiavi del session_state
_K_CMA = "cma"
_K_COMPARTO = "comparto"
_K_PROPOSTE = "proposte"          # dict[str, Proposta]
_K_CONFIG = "config_sim"
_K_INIT = "_inizializzato"


def init_stato() -> None:
    """Inizializza lo stato con dati demo, una sola volta per sessione."""
    if st.session_state.get(_K_INIT):
        return
    st.session_state[_K_CMA] = cma_demo()
    st.session_state[_K_COMPARTO] = comparto_demo()
    # proposta iniziale: equipesata sulle asset class del CMA demo
    cma = st.session_state[_K_CMA]
    nomi = [ac.nome for ac in cma.asset_class]
    peso = 1.0 / len(nomi)
    st.session_state[_K_PROPOSTE] = {
        "AAS vigente": Proposta(nome="AAS vigente", pesi={n: peso for n in nomi})
    }
    st.session_state[_K_CONFIG] = ConfigSimulazione()
    st.session_state[_K_INIT] = True


# ----------------------------- getter / setter --------------------------- #
def get_cma() -> CMASet:
    init_stato()
    return st.session_state[_K_CMA]


def set_cma(cma: CMASet) -> None:
    st.session_state[_K_CMA] = cma


def get_comparto() -> Comparto:
    init_stato()
    return st.session_state[_K_COMPARTO]


def set_comparto(comparto: Comparto) -> None:
    st.session_state[_K_COMPARTO] = comparto


def get_proposte() -> dict[str, Proposta]:
    init_stato()
    return st.session_state[_K_PROPOSTE]


def salva_proposta(proposta: Proposta) -> None:
    init_stato()
    st.session_state[_K_PROPOSTE][proposta.nome] = proposta


def elimina_proposta(nome: str) -> None:
    init_stato()
    st.session_state[_K_PROPOSTE].pop(nome, None)


def get_config() -> ConfigSimulazione:
    init_stato()
    return st.session_state[_K_CONFIG]


def set_config(config: ConfigSimulazione) -> None:
    st.session_state[_K_CONFIG] = config


# ----------------------------- helper UI ---------------------------------- #
SEMAFORO = {"OK": "🟢", "WARNING": "🟡", "VIOLATO": "🔴"}


def banner_demo() -> None:
    """Mostra l'avvertenza dati demo se il CMA e' ancora quello demo."""
    cma = get_cma()
    if "[DEMO]" in cma.nome:
        st.warning(
            "Stai usando dati DEMO (plausibili ma fittizi). Non sono assunzioni "
            "ufficiali del Fondo. Carica un file nella pagina Assunzioni per "
            "sostituirli.",
            icon="⚠️",
        )
