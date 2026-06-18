"""Pagina Simulazione CMA e Stress Test (M6).

Due sezioni distinte:
  - Simulazione condizionata alle CMA (Monte Carlo normale o t multivariata).
  - Stress test deterministici (scenari di shock, NON probabilistici).

La pagina non contiene formule: usa esclusivamente i servizi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import (  # noqa: E402
    banner_demo,
    get_cma,
    get_comparto,
    get_proposte,
    init_stato,
)
from src.services import (  # noqa: E402
    ParametriSimulazioneCMA,
    esegui_simulazione_cma,
    esegui_stress,
)
from src.stress_testing import scenari_demo  # noqa: E402

st.set_page_config(page_title="Simulazione CMA e Stress Test", page_icon="🌐", layout="wide")
init_stato()
st.title("Simulazione CMA e Stress Test")
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

tab_sim, tab_stress = st.tabs(["Simulazione condizionata alle CMA", "Stress test deterministici"])

# ============================ SIMULAZIONE ================================= #
with tab_sim:
    st.caption(
        "Le CMA (rendimenti, volatilita, correlazioni, costi, inflazione) sono gli "
        "input. Il motore genera rendimenti futuri coerenti con tali ipotesi. Questa "
        "e' la variabilita dei rendimenti futuri, distinta dall'incertezza nella stima "
        "delle CMA."
    )

    nome_prop = st.selectbox("Proposta", options=list(proposte.keys()), key="sim_prop")

    c1, c2, c3, c4 = st.columns(4)
    distrib = c1.selectbox("Distribuzione", ["normale", "t"],
                           format_func=lambda d: "Normale" if d == "normale" else "t di Student")
    df = c2.number_input("Gradi di liberta (t)", value=5, min_value=3, step=1,
                         disabled=(distrib == "normale"))
    orizzonte = c3.select_slider("Orizzonte (anni)",
                                 options=[1, 3, 5, 10, 15, 20], value=min(15, comparto.orizzonte_anni))
    freq = c4.selectbox("Frequenza", [1, 12],
                        format_func=lambda f: "Annuale" if f == 1 else "Mensile")

    c5, c6, c7, c8 = st.columns(4)
    n_sim = c5.select_slider("N. simulazioni", options=[1_000, 5_000, 10_000, 25_000], value=10_000)
    seed = c6.number_input("Seed", value=42, step=1)
    inflazione = c7.number_input("Inflazione", value=0.02, step=0.005, format="%.3f")
    conf = c8.select_slider("Confidenza VaR/ES", options=[0.95, 0.99], value=0.95)

    ribil = st.checkbox("Ribilanciamento periodico ai pesi target", value=True)

    if st.button("Esegui simulazione", type="primary", key="run_sim"):
        par = ParametriSimulazioneCMA(
            distribuzione=distrib, df=float(df), orizzonte_anni=int(orizzonte),
            periodi_per_anno=int(freq), n_simulazioni=int(n_sim), seed=int(seed),
            inflazione=float(inflazione), ribilanciamento=ribil, confidenza_var=float(conf),
        )
        res = esegui_simulazione_cma(cma, proposte[nome_prop], comparto, par)
        st.session_state["_sim_cma"] = {
            "montanti": res.montanti_reali.tolist(),
            "bande": {str(p): v.tolist() for p, v in res.bande_serie.items()},
            "perc": res.percentili_montante,
            "p_sf": res.prob_shortfall, "sf_medio": res.shortfall_medio,
            "var": res.var, "es": res.expected_shortfall,
            "maxdd": res.max_drawdown_mediano,
            "def": res.definizione_shortfall.value,
            "meta": f"{distrib} · {orizzonte}a · {'annuale' if freq==1 else 'mensile'} · "
                    f"{n_sim} sim · reale",
        }

    sim = st.session_state.get("_sim_cma")
    if sim:
        st.subheader("Risultati")
        st.caption("Metodo e parametri: " + sim["meta"])
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("P(shortfall)", f"{sim['p_sf']:.1%}", help=f"Definizione: {sim['def']}")
        m2.metric("Shortfall medio", f"{sim['sf_medio']:.2%}")
        m3.metric("VaR", f"{sim['var']:.2%}")
        m4.metric("Expected Shortfall", f"{sim['es']:.2%}")
        st.metric("Max drawdown mediano", f"{sim['maxdd']:.1%}")

        # istogramma montanti reali
        fig = go.Figure(go.Histogram(x=sim["montanti"], nbinsx=60))
        fig.add_vline(x=1.0, line_dash="dash",
                      annotation_text="Capitale iniziale (potere d'acquisto)")
        fig.update_layout(xaxis_title="Montante reale finale", yaxis_title="Frequenza",
                          height=360, margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig, width="stretch")

        # fan chart dei percorsi (bande precalcolate dal service)
        bande = sim.get("bande")
        if bande:
            p5 = np.array(bande["5"])
            p50 = np.array(bande["50"])
            p95 = np.array(bande["95"])
            anni = list(range(len(p50)))
            fan = go.Figure()
            fan.add_trace(go.Scatter(x=anni, y=p95, line=dict(width=0), showlegend=False))
            fan.add_trace(go.Scatter(x=anni, y=p5, fill="tonexty", line=dict(width=0),
                                     name="5-95 percentile", fillcolor="rgba(99,110,250,0.2)"))
            fan.add_trace(go.Scatter(x=anni, y=p50, line=dict(color="rgb(99,110,250)"),
                                     name="mediana"))
            fan.update_layout(xaxis_title="Periodo", yaxis_title="Montante reale",
                              height=360, margin=dict(l=10, r=10, t=10, b=10))
            st.plotly_chart(fan, width="stretch")

        st.caption(
            "Limite metodologico: con distribuzione normale le code sono sottostimate; "
            "la t di Student attenua il problema ma resta un modello. I valori di coda "
            "(VaR/ES) vanno letti con cautela."
        )

# ============================ STRESS TEST ================================= #
with tab_stress:
    st.caption(
        "Gli stress test sono scenari DETERMINISTICI di shock. Non sono probabilita: "
        "rappresentano l'impatto istantaneo di un dato scenario sul portafoglio."
    )

    nome_prop_s = st.selectbox("Proposta", options=list(proposte.keys()), key="stress_prop")
    scenari = scenari_demo()
    nomi_scen = [s.nome for s in scenari]
    sel = st.selectbox("Scenario di stress", options=nomi_scen)
    scenario = scenari[nomi_scen.index(sel)]
    st.caption(scenario.descrizione)

    if st.button("Applica stress test", type="primary", key="run_stress"):
        res, quote = esegui_stress(cma, proposte[nome_prop_s], scenario)
        st.session_state["_stress"] = {
            "perdita": res.perdita_pct, "nuovo": res.nuovo_valore,
            "contributi": res.contributo_perdita, "shock": res.shock_per_asset,
            "note": res.note, "quote": quote,
        }

    stress = st.session_state.get("_stress")
    if stress:
        st.subheader("Impatto")
        s1, s2, s3 = st.columns(3)
        s1.metric("Perdita complessiva", f"{stress['perdita']:.1%}")
        s2.metric("Nuovo valore", f"{stress['nuovo']:.3f}")
        s3.metric("Quota illiquida post-shock", f"{stress['quote']['illiquida']:.1%}")

        nomi = list(stress["contributi"].keys())
        fig_c = go.Figure(go.Bar(
            x=[stress["contributi"][n] * 100 for n in nomi], y=nomi, orientation="h",
        ))
        fig_c.update_layout(xaxis_title="Contributo alla perdita (%)", height=320,
                            margin=dict(l=10, r=10, t=10, b=10))
        st.plotly_chart(fig_c, width="stretch")

        if stress["note"]:
            with st.expander("Note metodologiche dello scenario"):
                for n in stress["note"]:
                    st.write("• " + n)
