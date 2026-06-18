"""Pagina Comparti: configurazione del comparto previdenziale."""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import banner_demo, get_comparto, init_stato, set_comparto  # noqa: E402
from src.domain.models import (  # noqa: E402
    Comparto,
    ConfigShortfall,
    DefinizioneShortfall,
    TipoObiettivo,
)

st.set_page_config(page_title="Comparti — DPI Wizard", page_icon="🗂️", layout="wide")
init_stato()
st.title("Comparti")
banner_demo()

c = get_comparto()

st.subheader("Configurazione del comparto")
col1, col2 = st.columns(2)
with col1:
    nome = st.text_input("Nome", value=c.nome)
    patrimonio = st.number_input(
        "Patrimonio (EUR)", value=float(c.patrimonio), step=1_000_000.0, format="%.0f"
    )
    orizzonte = st.number_input(
        "Orizzonte (anni)", value=int(c.orizzonte_anni), min_value=1, step=1
    )
    tipo = st.selectbox(
        "Tipo di obiettivo", options=[t.value for t in TipoObiettivo],
        index=[t.value for t in TipoObiettivo].index(c.tipo_obiettivo.value),
    )
    obiettivo = st.number_input(
        "Obiettivo di rendimento (annuo)", value=float(c.obiettivo_rendimento),
        step=0.005, format="%.3f",
    )
with col2:
    liq_min = st.slider(
        "Liquidita minima", 0.0, 1.0, float(c.liquidita_minima), step=0.01
    )
    quota_illiq = st.slider(
        "Quota massima illiquida", 0.0, 1.0, float(c.quota_max_illiquida), step=0.01
    )
    benchmark = st.text_input("Benchmark strategico", value=c.benchmark or "")
    st.markdown("**Definizione di shortfall**")
    defs = [d.value for d in DefinizioneShortfall]
    def_label = {
        "reale_negativo": "Rendimento reale < 0 (perdita potere d'acquisto)",
        "reale_sotto_obiettivo": "Rendimento reale < obiettivo",
        "nominale_negativo": "Rendimento nominale < 0",
        "sotto_inflazione": "Rendimento nominale < inflazione",
        "montante_sotto_soglia": "Montante < soglia assoluta",
    }
    def_sel = st.selectbox(
        "Evento di shortfall", options=defs,
        index=defs.index(c.shortfall.definizione.value),
        format_func=lambda d: def_label[d],
    )
    soglia = None
    if def_sel == DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA.value:
        soglia = st.number_input(
            "Soglia montante (per 1 di capitale iniziale)",
            value=float(c.shortfall.soglia_montante or 1.0), step=0.05,
        )

if st.button("Salva comparto", type="primary"):
    try:
        nuovo = Comparto(
            nome=nome, patrimonio=patrimonio, orizzonte_anni=int(orizzonte),
            obiettivo_rendimento=obiettivo, tipo_obiettivo=TipoObiettivo(tipo),
            liquidita_minima=liq_min, quota_max_illiquida=quota_illiq,
            benchmark=benchmark or None,
            shortfall=ConfigShortfall(
                definizione=DefinizioneShortfall(def_sel), soglia_montante=soglia
            ),
        )
        set_comparto(nuovo)
        st.success("Comparto salvato.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Configurazione non valida: {exc}")
