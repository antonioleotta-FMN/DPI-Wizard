"""DPI Wizard — entrypoint Streamlit (Home).

Con la cartella pages/, Streamlit costruisce automaticamente la navigazione multipage.
Questo file e' la pagina iniziale (Home). Le pagine NON contengono formule: usano
esclusivamente src.services tramite gli helper di pages/_state.py.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pages._state import banner_demo, get_cma, get_comparto, get_proposte, init_stato  # noqa: E402

st.set_page_config(page_title="DPI Wizard", page_icon="🧭", layout="wide")
init_stato()

st.title("DPI Wizard")
st.caption(
    "Supporto alla definizione, verifica e revisione del Documento sulla Politica "
    "di Investimento del Fondo Pensione Mario Negri."
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
    "8. **Report** — esporta input, risultati e confronti in Excel."
)

st.info(
    "Strumento di supporto alle decisioni. Non sostituisce la valutazione degli organi "
    "del Fondo, della Funzione Gestione dei rischi, della Compliance, ne la valutazione "
    "legale.",
    icon="ℹ️",
)
