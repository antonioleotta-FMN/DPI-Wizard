"""Pagina Controlli: vista dettagliata dei vincoli per una proposta."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import (  # noqa: E402
    SEMAFORO,
    banner_demo,
    get_cma,
    get_comparto,
    get_proposte,
    init_stato,
)
from src.services import verifica  # noqa: E402

st.set_page_config(page_title="Controlli — DPI Wizard", page_icon="✅", layout="wide")
init_stato()
st.title("Controlli sui vincoli")
banner_demo()

cma = get_cma()
comparto = get_comparto()
proposte = get_proposte()

nome = st.selectbox("Proposta da controllare", options=list(proposte.keys()))
esiti, stato = verifica(proposte[nome], comparto, cma)

st.markdown(f"## Stato complessivo: {SEMAFORO[stato.value]} {stato.value}")

df = pd.DataFrame([
    {
        "Vincolo": e.nome,
        "Tipo": e.tipo.value,
        "Stato": SEMAFORO[e.stato.value] + " " + e.stato.value,
        "Valore": f"{e.valore:.3f}",
        "Limite": f"{e.limite:.3f}",
        "Nota": e.messaggio,
    }
    for e in esiti
])
st.dataframe(df, width='stretch', hide_index=True)

st.info(
    "I controlli automatici coprono bande, liquidita, quota illiquida e coerenza dei "
    "pesi. I limiti normativi puntuali vanno parametrizzati e validati dalle funzioni "
    "competenti del Fondo: l'app non sostituisce la valutazione legale o degli organi.",
    icon="ℹ️",
)
