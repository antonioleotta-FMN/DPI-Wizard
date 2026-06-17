"""DPI Wizard — entrypoint Streamlit.

Pagina DIAGNOSTICA (smoke test, M3). Non e' ancora l'MVP: serve a verificare che il
deploy su Streamlit Cloud funzioni e che la catena dominio -> servizi -> calcoli ->
simulazioni -> vincoli produca risultati coerenti con dati demo.

Le pagine NON contengono formule: chiamano esclusivamente src.services.
La UI definitiva (Asset Allocation Lab e pagine multipage) arriva con l'MVP (M4+).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# Rende importabile il pacchetto src quando l'app gira dalla root del repo
sys.path.insert(0, str(Path(__file__).resolve().parent))

from src.data.demo import cma_demo, comparto_demo  # noqa: E402
from src.domain.models import ConfigSimulazione, Proposta  # noqa: E402
from src.services import (  # noqa: E402
    calcola_metriche,
    esegui_simulazione,
    verifica,
)

st.set_page_config(page_title="DPI Wizard — Diagnostica", layout="wide")

st.title("DPI Wizard")
st.caption(
    "Pagina diagnostica (smoke test). Verifica il funzionamento della catena di "
    "calcolo con dati DEMO. Non e' l'applicazione definitiva."
)
st.warning(
    "I dati mostrati sono DEMO, plausibili ma fittizi. Non sono Capital Market "
    "Assumptions ufficiali del Fondo e non devono essere usati per decisioni reali.",
    icon="⚠️",
)

cma = cma_demo()
comparto = comparto_demo()
nomi = [ac.nome for ac in cma.asset_class]

# ----------------------------- Sidebar: pesi ------------------------------ #
st.sidebar.header("Proposta di allocazione")
st.sidebar.caption("Modifica i pesi (verranno normalizzati a 100%).")

pesi_default = {
    "Liquidita": 5, "Govt EUR": 30, "Corporate": 15, "Equity DM": 25,
    "Equity EM": 10, "Real assets": 5, "Private markets": 10,
}
pesi_grezzi = {}
for n in nomi:
    pesi_grezzi[n] = st.sidebar.slider(n, 0, 100, pesi_default.get(n, 0), step=1)

totale = sum(pesi_grezzi.values())
if totale == 0:
    st.error("Imposta almeno un peso maggiore di zero.")
    st.stop()

pesi_norm = {n: v / totale for n, v in pesi_grezzi.items()}
proposta = Proposta(nome="Diagnostica", pesi=pesi_norm)

st.sidebar.divider()
inflazione = st.sidebar.number_input(
    "Inflazione attesa (annua)", value=0.02, step=0.005, format="%.3f"
)
n_sim = st.sidebar.select_slider(
    "Numero simulazioni", options=[5_000, 10_000, 20_000, 50_000], value=20_000
)
seed = st.sidebar.number_input("Seed", value=42, step=1)

config = ConfigSimulazione(
    n_simulazioni=int(n_sim), seed=int(seed), inflazione=float(inflazione)
)

# ----------------------------- Metriche ----------------------------------- #
metriche = calcola_metriche(cma, proposta, float(inflazione))

st.subheader("Metriche deterministiche")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rendimento nominale", f"{metriche.rendimento_nominale:.2%}")
c2.metric("Rendimento netto costi", f"{metriche.rendimento_netto_costi:.2%}")
c3.metric("Rendimento reale", f"{metriche.rendimento_reale:.2%}")
c4.metric("Volatilita", f"{metriche.volatilita:.2%}")

c5, c6, c7 = st.columns(3)
c5.metric("Quota illiquida", f"{metriche.quota_illiquida:.1%}")
c6.metric("Esposiz. valutaria non coperta", f"{metriche.esposizione_valutaria_non_coperta:.1%}")
c7.metric("Duration media", f"{metriche.duration_media:.1f}")

# ----------------------------- Vincoli ------------------------------------ #
st.subheader("Verifica vincoli")
esiti, stato = verifica(proposta, comparto, cma)
colore = {"OK": "🟢", "WARNING": "🟡", "VIOLATO": "🔴"}
st.markdown(f"**Stato complessivo:** {colore[stato.value]} {stato.value}")
df_vincoli = pd.DataFrame([
    {"Vincolo": e.nome, "Tipo": e.tipo.value, "Stato": colore[e.stato.value] + " " + e.stato.value,
     "Valore": f"{e.valore:.3f}", "Limite": f"{e.limite:.3f}", "Nota": e.messaggio}
    for e in esiti
])
st.dataframe(df_vincoli, use_container_width=True, hide_index=True)

# ----------------------------- Contributi al rischio ---------------------- #
st.subheader("Contributo al rischio per asset class")
contrib = metriche.contributi_rischio_pct
fig_c = go.Figure(go.Bar(
    x=[contrib[n] * 100 for n in nomi], y=nomi, orientation="h",
))
fig_c.update_layout(
    xaxis_title="Contributo al rischio (%)", height=320,
    margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_c, use_container_width=True)

# ----------------------------- Simulazione -------------------------------- #
st.subheader(f"Simulazione Monte Carlo — orizzonte {comparto.orizzonte_anni} anni")
res = esegui_simulazione(cma, proposta, comparto, config)

c8, c9, c10 = st.columns(3)
c8.metric("P(shortfall)", f"{res.prob_shortfall:.1%}",
          help=f"Definizione: {res.definizione_shortfall.value}")
c9.metric(f"VaR {config.confidenza_var:.0%} ({config.orizzonte_var_anni}a)",
          f"{res.var:.2%}")
c10.metric("Expected Shortfall (mercato)", f"{res.expected_shortfall:.2%}")

# Distribuzione dei montanti reali finali
fig_h = go.Figure(go.Histogram(x=res.montanti_finali, nbinsx=60))
fig_h.add_vline(x=1.0, line_dash="dash",
                annotation_text="Capitale iniziale (potere d'acquisto)")
for p, v in res.percentili.items():
    fig_h.add_vline(x=v, line_dash="dot", opacity=0.3)
fig_h.update_layout(
    xaxis_title="Montante reale finale (per 1 di capitale iniziale)",
    yaxis_title="Frequenza", height=380, margin=dict(l=10, r=10, t=10, b=10),
)
st.plotly_chart(fig_h, use_container_width=True)

st.caption(
    "Percentili del montante reale: " +
    " · ".join(f"P{p}={v:.2f}" for p, v in res.percentili.items())
)

st.divider()
st.caption(
    "Limite metodologico: la distribuzione normale multivariata sottostima gli eventi "
    "estremi. I valori di coda (VaR/ES) vanno letti con cautela. Metodologie avanzate "
    "previste per le fasi successive."
)
