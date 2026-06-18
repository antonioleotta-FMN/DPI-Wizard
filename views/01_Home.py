"""Pagina Home di DPI Wizard.

Riepilogo dello stato di sessione e guida ai passi. Non contiene formule: usa gli helper
di src.ui_state. La configurazione di pagina e la navigazione sono gestite dall'entrypoint
app.py tramite st.navigation.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ui_state import (  # noqa: E402
    banner_demo,
    get_cma,
    get_comparto,
    get_proposte,
    init_stato,
)

init_stato()

st.title("DPI Wizard")
st.caption(
    "Supporto alla definizione, verifica e revisione del Documento sulla Politica "
    "di Investimento."
)
banner_demo()

cma = get_cma()
comparto = get_comparto()
proposte = get_proposte()

st.subheader("Stato della sessione")
c1, c2, c3 = st.columns(3)
c1.metric("Set CMA attivo", cma.nome.replace("[DEMO] ", ""))
c2.metric("Asset class", len(cma.asset_class))
c3.metric("Proposte salvate", len(proposte))

c4, c5, c6 = st.columns(3)
c4.metric("Comparto", comparto.nome.replace("[DEMO] ", ""))
c5.metric("Orizzonte", f"{comparto.orizzonte_anni} anni")
obiettivo = f"{comparto.obiettivo_rendimento:.1%} {comparto.tipo_obiettivo.value}"
c6.metric("Obiettivo", obiettivo)

st.divider()
st.subheader("Come procedere")
st.markdown(
    "1. **Comparti** — configura il comparto e i suoi obiettivi e vincoli.\n"
    "2. **Assunzioni** — rivedi o carica le Capital Market Assumptions.\n"
    "3. **Correlazioni** — controlla la matrice di correlazione.\n"
    "4. **Asset Allocation Lab** — modifica i pesi e osserva le metriche in tempo reale.\n"
    "5. **Simulazioni** — esegui il Monte Carlo sul comparto.\n"
    "6. **Confronto** — confronta piu' proposte di allocazione.\n"
    "7. **Controlli** — verifica il rispetto dei vincoli.\n"
    "8. **Report** — esporta input, risultati e confronti in Excel.\n"
    "9. **Simulazione CMA e Stress Test** — distribuzioni, percorsi, stress deterministici.\n"
    "10. **Ottimizzazione AAS** — allocazioni ottimizzate sotto vincoli."
)

st.info(
    "Strumento di supporto alle decisioni. Non sostituisce la valutazione degli organi "
    "del Fondo, della Funzione Gestione dei rischi, della Compliance, ne la valutazione "
    "legale.",
    icon="ℹ️",
)
