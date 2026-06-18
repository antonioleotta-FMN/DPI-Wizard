"""Pagina Ottimizzazione AAS (M7).

Configura obiettivo e vincoli, esegue l'ottimizzazione, confronta con la AAS vigente,
mostra la frontiera efficiente e diagnostica l'infeasibilita'. Salva la proposta
ottimizzata tra le proposte della sessione.

La pagina non contiene formule: usa esclusivamente i servizi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import (  # noqa: E402
    banner_demo,
    get_cma,
    get_comparto,
    get_proposte,
    init_stato,
    salva_proposta,
)
from src.services.optimization_service import (  # noqa: E402
    calcola_frontiera,
    costruisci_config_da_comparto,
    ottimizza_aas,
)

st.set_page_config(page_title="Ottimizzazione AAS", page_icon="🎯", layout="wide")
init_stato()
st.title("Ottimizzazione AAS")
banner_demo()

st.warning(
    "I parametri visualizzati sono configurabili. I valori predefiniti sono tecnici e "
    "provvisori e devono essere validati dalla Funzione Gestione dei Rischi e dagli "
    "organi competenti del Fondo prima dell'utilizzo formale nel Documento sulla "
    "Politica di Investimento.",
    icon="⚠️",
)

cma = get_cma()
comparto = get_comparto()
proposte = get_proposte()

c1, c2 = st.columns(2)
with c1:
    vigente = st.selectbox("AAS vigente (riferimento)", options=list(proposte.keys()))
    obiettivo = st.selectbox(
        "Funzione obiettivo",
        options=["min_varianza", "max_rendimento", "max_sharpe"],
        format_func=lambda o: {
            "min_varianza": "Minima varianza",
            "max_rendimento": "Massimo rendimento (con vincoli)",
            "max_sharpe": "Massimo Sharpe ratio",
        }[o],
    )
with c2:
    passo = st.select_slider("Arrotondamento pesi", options=[0.0, 0.001, 0.005, 0.01],
                             value=0.005,
                             format_func=lambda p: "Nessuno" if p == 0 else f"{p:.1%}")

with st.expander("Vincoli aggiuntivi (oltre a bande, liquidita, illiquidita del comparto)"):
    v1, v2, v3 = st.columns(3)
    usa_rend = v1.checkbox("Rendimento minimo")
    rend_min = v1.number_input("Valore", value=0.04, step=0.005, format="%.3f",
                               disabled=not usa_rend, key="rmin")
    usa_vol = v2.checkbox("Volatilita massima")
    vol_max = v2.number_input("Valore ", value=0.10, step=0.005, format="%.3f",
                              disabled=not usa_vol, key="vmax")
    usa_tov = v3.checkbox("Turnover massimo vs vigente")
    tov_max = v3.number_input("Valore  ", value=0.30, step=0.05, format="%.2f",
                              disabled=not usa_tov, key="tmax")

if st.button("Esegui ottimizzazione", type="primary"):
    cfg = costruisci_config_da_comparto(
        cma, comparto, proposte[vigente],
        rendimento_min=rend_min if usa_rend else None,
        volatilita_max=vol_max if usa_vol else None,
        turnover_max=tov_max if usa_tov else None,
    )
    esito = ottimizza_aas(cma, comparto, obiettivo, cfg,
                          passo_arrotondamento=passo if passo > 0 else None)
    st.session_state["_opt"] = esito
    st.session_state["_opt_cfg"] = cfg
    st.session_state["_opt_vigente"] = vigente

esito = st.session_state.get("_opt")
if esito is not None:
    if not esito.successo:
        st.error(esito.messaggio)
        if esito.diagnostica is not None:
            st.subheader("Diagnostica infeasibilita")
            st.write(esito.diagnostica.messaggio)
            if esito.diagnostica.vincoli_problematici:
                st.write("Vincoli problematici: " +
                         ", ".join(esito.diagnostica.vincoli_problematici))
    else:
        prop = esito.proposta
        st.subheader("Portafoglio ottimizzato")
        m1, m2, m3 = st.columns(3)
        m1.metric("Rendimento atteso", f"{esito.rendimento:.2%}")
        m2.metric("Volatilita", f"{esito.volatilita:.2%}")
        if esito.turnover_vs_vigente is not None:
            m3.metric("Turnover vs vigente", f"{esito.turnover_vs_vigente:.2f}")

        # confronto pesi con la vigente
        vig = proposte[st.session_state["_opt_vigente"]]
        nomi = [ac.nome for ac in cma.asset_class]
        fig = go.Figure()
        fig.add_trace(go.Bar(name="Vigente", x=nomi, y=[vig.pesi.get(n, 0) * 100 for n in nomi]))
        fig.add_trace(go.Bar(name="Ottimizzata", x=nomi, y=[prop.pesi.get(n, 0) * 100 for n in nomi]))
        fig.update_layout(barmode="group", yaxis_title="Peso (%)", height=360,
                          margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")

        nome_salva = st.text_input("Nome con cui salvare la proposta", value=prop.nome)
        if st.button("Salva proposta ottimizzata"):
            salva_proposta(type(prop)(nome=nome_salva, pesi=prop.pesi))
            st.success(f"Proposta '{nome_salva}' salvata.")

    # frontiera efficiente
    cfg = st.session_state.get("_opt_cfg")
    if cfg is not None:
        st.subheader("Frontiera efficiente")
        punti = calcola_frontiera(cma, cfg, n_punti=20)
        if punti:
            fig_f = go.Figure(go.Scatter(
                x=[p.volatilita * 100 for p in punti],
                y=[p.rendimento * 100 for p in punti],
                mode="lines+markers", name="Frontiera",
            ))
            if esito.successo:
                fig_f.add_trace(go.Scatter(
                    x=[esito.volatilita * 100], y=[esito.rendimento * 100],
                    mode="markers", marker=dict(size=14, symbol="star"),
                    name="Ottimizzata",
                ))
            fig_f.update_layout(xaxis_title="Volatilita (%)", yaxis_title="Rendimento (%)",
                                height=400, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fig_f, width="stretch")
        else:
            st.info("Nessun punto fattibile sulla frontiera con i vincoli correnti.")
