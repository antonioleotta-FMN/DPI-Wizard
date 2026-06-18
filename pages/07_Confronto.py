"""Pagina Confronto: comparazione di piu' proposte su metriche e rischio-rendimento."""

from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ui_state import (  # noqa: E402
    SEMAFORO,
    banner_demo,
    get_cma,
    get_comparto,
    get_config,
    get_proposte,
    init_stato,
)
from src.services import calcola_metriche, esegui_simulazione, verifica  # noqa: E402

init_stato()
st.title("Confronto scenari")
banner_demo()

cma = get_cma()
comparto = get_comparto()
config = get_config()
proposte = get_proposte()

selezione = st.multiselect(
    "Proposte da confrontare", options=list(proposte.keys()),
    default=list(proposte.keys())[: min(4, len(proposte))],
)
if not selezione:
    st.info("Seleziona almeno una proposta.")
    st.stop()

simula = st.checkbox(
    "Includi Monte Carlo (P(shortfall), VaR, ES)", value=False,
    help="Piu' lento: esegue una simulazione per ogni proposta.",
)

# ----------------------------- tabella comparativa ----------------------- #
righe = []
punti = []
for nome in selezione:
    p = proposte[nome]
    m = calcola_metriche(cma, p, config.inflazione, comparto.orizzonte_anni)
    _, stato = verifica(p, comparto, cma)
    riga = {
        "Proposta": nome,
        "Rend. nominale": m.rendimento_nominale,
        "Rend. netto": m.rendimento_netto_costi,
        "Rend. reale": m.rendimento_reale,
        "Volatilita": m.volatilita,
        "Quota illiquida": m.quota_illiquida,
        "Vincoli": SEMAFORO[stato.value] + " " + stato.value,
    }
    if simula:
        res = esegui_simulazione(cma, p, comparto, config)
        riga["P(shortfall)"] = res.prob_shortfall
        riga[f"VaR {config.confidenza_var:.0%}"] = res.var
        riga["ES mercato"] = res.expected_shortfall
    righe.append(riga)
    punti.append((nome, m.volatilita, m.rendimento_reale))

df = pd.DataFrame(righe).set_index("Proposta")
fmt = {c: "{:.2%}" for c in df.columns if df[c].dtype.kind == "f"}
st.subheader("Tabella comparativa")
st.dataframe(df.style.format(fmt), width='stretch')

# ----------------------------- scatter rischio-rendimento ---------------- #
st.subheader("Rischio / Rendimento (reale)")
fig = go.Figure()
for nome, vol, rend in punti:
    fig.add_trace(go.Scatter(
        x=[vol * 100], y=[rend * 100], mode="markers+text",
        text=[nome], textposition="top center", marker=dict(size=14), name=nome,
    ))
fig.update_layout(
    xaxis_title="Volatilita (%)", yaxis_title="Rendimento reale atteso (%)",
    height=440, margin=dict(l=10, r=10, t=10, b=10), showlegend=False,
)
st.plotly_chart(fig, width='stretch')

# ----------------------------- differenze pesi --------------------------- #
st.subheader("Pesi a confronto")
nomi = [ac.nome for ac in cma.asset_class]
df_pesi = pd.DataFrame(
    {nome: [proposte[nome].pesi.get(n, 0.0) for n in nomi] for nome in selezione},
    index=nomi,
)
st.dataframe(df_pesi.style.format("{:.1%}"), width='stretch')
