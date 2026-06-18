"""Pagina Asset Allocation Lab: modifica dei pesi e metriche in tempo reale."""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import (  # noqa: E402
    SEMAFORO,
    banner_demo,
    get_cma,
    get_comparto,
    get_config,
    get_proposte,
    init_stato,
    salva_proposta,
)
from src.domain.models import Proposta  # noqa: E402
from src.services import calcola_metriche, verifica  # noqa: E402

st.set_page_config(page_title="AA Lab — DPI Wizard", page_icon="🧪", layout="wide")
init_stato()
st.title("Asset Allocation Lab")
banner_demo()

cma = get_cma()
comparto = get_comparto()
proposte = get_proposte()
nomi = [ac.nome for ac in cma.asset_class]

# ----------------------------- punto di partenza ------------------------- #
base = st.selectbox("Parti da una proposta esistente", options=list(proposte.keys()))
pesi_base = proposte[base].pesi

st.subheader("Pesi (%)")
st.caption("I pesi vengono normalizzati a 100% per il calcolo.")

cols = st.columns(min(len(nomi), 4))
pesi_pct = {}
for i, n in enumerate(nomi):
    with cols[i % len(cols)]:
        pesi_pct[n] = st.slider(
            n, 0.0, 100.0, round(pesi_base.get(n, 0.0) * 100, 1), step=0.5
        )

totale = sum(pesi_pct.values())
if totale <= 0:
    st.error("Imposta almeno un peso maggiore di zero.")
    st.stop()

pesi_norm = {n: v / totale for n, v in pesi_pct.items()}
proposta = Proposta(nome="lab", pesi=pesi_norm)

config = get_config()
metriche = calcola_metriche(cma, proposta, config.inflazione, comparto.orizzonte_anni)

# ----------------------------- metriche live ----------------------------- #
st.subheader("Metriche")
c1, c2, c3, c4 = st.columns(4)
c1.metric("Rendimento nominale", f"{metriche.rendimento_nominale:.2%}")
c2.metric("Rendimento netto costi", f"{metriche.rendimento_netto_costi:.2%}")
c3.metric("Rendimento reale", f"{metriche.rendimento_reale:.2%}")
c4.metric("Volatilita", f"{metriche.volatilita:.2%}")

c5, c6, c7 = st.columns(3)
c5.metric("Quota illiquida", f"{metriche.quota_illiquida:.1%}")
c6.metric("Esp. valutaria non coperta", f"{metriche.esposizione_valutaria_non_coperta:.1%}")
c7.metric("Duration media", f"{metriche.duration_media:.1f}")

c8, c9 = st.columns(2)
c8.metric(
    "Rend. reale geometrico", f"{metriche.rendimento_geometrico_reale:.2%}",
    help="Convenzione geometrica (DEC-003): tiene conto del drag della volatilita.",
)
c9.metric(
    f"Montante reale atteso ({comparto.orizzonte_anni}a)",
    f"{metriche.montante_reale_atteso:.2f}",
    help="Per 1 di capitale iniziale, capitalizzazione composta del rendimento "
    "geometrico reale.",
)

# ----------------------------- vincoli ----------------------------------- #
esiti, stato = verifica(proposta, comparto, cma)
st.markdown(f"**Vincoli:** {SEMAFORO[stato.value]} {stato.value}")
violati = [e for e in esiti if e.stato.value != "OK"]
if violati:
    for e in violati:
        st.write(f"{SEMAFORO[e.stato.value]} {e.messaggio}")

# ----------------------------- grafici ----------------------------------- #
col_a, col_b = st.columns(2)
with col_a:
    st.markdown("**Composizione**")
    fig_pie = go.Figure(go.Pie(labels=nomi, values=[pesi_norm[n] for n in nomi], hole=0.4))
    fig_pie.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_pie, width='stretch')
with col_b:
    st.markdown("**Contributo al rischio (%)**")
    contrib = metriche.contributi_rischio_pct
    fig_bar = go.Figure(go.Bar(
        x=[contrib[n] * 100 for n in nomi], y=nomi, orientation="h"
    ))
    fig_bar.update_layout(height=320, margin=dict(l=10, r=10, t=10, b=10))
    st.plotly_chart(fig_bar, width='stretch')

# ----------------------------- salvataggio ------------------------------- #
st.divider()
st.subheader("Salva come proposta")
col_n, col_s = st.columns([3, 1])
with col_n:
    nome_nuovo = st.text_input("Nome della proposta", value="Proposta base")
with col_s:
    st.write("")
    st.write("")
    if st.button("Salva", type="primary"):
        salva_proposta(Proposta(nome=nome_nuovo, pesi=pesi_norm))
        st.success(f"Proposta '{nome_nuovo}' salvata.")
