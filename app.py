"""DPI Wizard — entrypoint Streamlit con navigazione esplicita.

Usa st.navigation / st.Page per dichiarare esplicitamente le pagine, invece dello
scanning automatico della cartella pages/. Questo evita che moduli di supporto vengano
interpretati come pagine ed e' robusto rispetto alle versioni di Streamlit.

Le pagine NON contengono formule: usano esclusivamente src.services e gli helper di
src.ui_state.
"""

from __future__ import annotations

import sys
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parent))

st.set_page_config(page_title="DPI Wizard", page_icon="🧭", layout="wide")

_P = "pages"
pagine = [
    st.Page(f"{_P}/01_Home.py", title="Home", icon="🧭", default=True),
    st.Page(f"{_P}/02_Comparti.py", title="Comparti", icon="🗂️"),
    st.Page(f"{_P}/03_Assunzioni.py", title="Assunzioni (CMA)", icon="📥"),
    st.Page(f"{_P}/04_Correlazioni.py", title="Correlazioni", icon="🔗"),
    st.Page(f"{_P}/05_Asset_Allocation_Lab.py", title="Asset Allocation Lab", icon="🧪"),
    st.Page(f"{_P}/06_Simulazioni.py", title="Simulazioni", icon="🎲"),
    st.Page(f"{_P}/07_Confronto.py", title="Confronto", icon="⚖️"),
    st.Page(f"{_P}/08_Controlli.py", title="Controlli", icon="✅"),
    st.Page(f"{_P}/09_Report.py", title="Report", icon="📄"),
    st.Page(f"{_P}/10_Simulazione_CMA_Stress.py", title="Simulazione CMA e Stress Test", icon="🌐"),
    st.Page(f"{_P}/11_Ottimizzazione_AAS.py", title="Ottimizzazione AAS", icon="🎯"),
]

st.navigation(pagine).run()
