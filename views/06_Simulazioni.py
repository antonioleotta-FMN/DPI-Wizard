"""Pagina Simulazioni: Monte Carlo sul comparto per una proposta selezionata."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ui_state import (  # noqa: E402
    banner_demo,
    get_cma,
    get_comparto,
    get_config,
    get_proposte,
    init_stato,
    set_config,
)
from src.domain.models import ConfigSimulazione  # noqa: E402
from src.services import esegui_simulazione  # noqa: E402

init_stato()
st.title("Simulazioni Monte Carlo")
banner_demo()

cma = get_cma()
comparto = get_comparto()
proposte = get_proposte()
config = get_config()

# ----------------------------- parametri --------------------------------- #
col1, col2 = st.columns([2, 3])
with col1:
    nome_prop = st.selectbox("Proposta da simulare", options=list(proposte.keys()))
with col2:
    st.caption(
        f"Comparto: {comparto.nome.replace('[DEMO] ', '')} · "
        f"orizzonte {comparto.orizzonte_anni} anni · "
        f"shortfall: {comparto.shortfall.definizione.value}"
    )

with st.expander("Parametri di simulazione"):
    c1, c2, c3, c4 = st.columns(4)
    n_sim = c1.select_slider(
        "N. simulazioni", options=[5_000, 10_000, 20_000, 50_000],
        value=config.n_simulazioni if config.n_simulazioni in (5_000, 10_000, 20_000, 50_000) else 20_000,
    )
    seed = c2.number_input("Seed", value=int(config.seed), step=1)
    inflazione = c3.number_input(
        "Inflazione", value=float(config.inflazione), step=0.005, format="%.3f"
    )
    conf = c4.select_slider("Confidenza VaR", options=[0.90, 0.95, 0.99], value=config.confidenza_var)

if st.button("Esegui simulazione", type="primary"):
    nuovo_config = ConfigSimulazione(
        n_simulazioni=int(n_sim), seed=int(seed), inflazione=float(inflazione),
        confidenza_var=float(conf), orizzonte_var_anni=config.orizzonte_var_anni,
    )
    set_config(nuovo_config)
    res = esegui_simulazione(cma, proposte[nome_prop], comparto, nuovo_config)
    st.session_state["_ultima_sim"] = {
        "montanti": res.montanti_finali.tolist(),
        "percentili": res.percentili,
        "prob_shortfall": res.prob_shortfall,
        "var": res.var, "es": res.expected_shortfall,
        "es_obiettivo": res.es_mancato_obiettivo,
        "definizione": res.definizione_shortfall.value,
        "conf": float(conf),
    }

# ----------------------------- risultati --------------------------------- #
sim = st.session_state.get("_ultima_sim")
if sim:
    st.subheader("Risultati")
    c1, c2, c3 = st.columns(3)
    c1.metric("P(shortfall)", f"{sim['prob_shortfall']:.1%}",
              help=f"Definizione: {sim['definizione']}")
    c2.metric(f"VaR {sim['conf']:.0%}", f"{sim['var']:.2%}")
    c3.metric("Expected Shortfall (mercato)", f"{sim['es']:.2%}")

    st.caption(
        "Percentili montante reale: " +
        " · ".join(f"P{p}={v:.2f}" for p, v in sim["percentili"].items()) +
        f"  ·  Perdita media reale negli scenari di shortfall: {sim['es_obiettivo']:.1%}"
    )

    fig = go.Figure(go.Histogram(x=sim["montanti"], nbinsx=60))
    fig.add_vline(x=1.0, line_dash="dash",
                  annotation_text="Capitale iniziale (potere d'acquisto)")
    fig.update_layout(
        xaxis_title="Montante reale finale (per 1 di capitale iniziale)",
        yaxis_title="Frequenza", height=400, margin=dict(l=10, r=10, t=10, b=10),
    )
    st.plotly_chart(fig, width='stretch')

    st.caption(
        "Limite metodologico: la distribuzione normale multivariata sottostima gli "
        "eventi estremi; i valori di coda (VaR/ES) vanno letti con cautela."
    )
else:
    st.info("Imposta i parametri e premi «Esegui simulazione».")
