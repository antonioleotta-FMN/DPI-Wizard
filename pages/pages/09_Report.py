"""Pagina Report: esportazione Excel di input, assunzioni, proposte e risultati."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import (  # noqa: E402
    banner_demo,
    get_cma,
    get_comparto,
    get_config,
    get_proposte,
    init_stato,
)
from src.reporting import genera_report_excel  # noqa: E402

st.set_page_config(page_title="Report — DPI Wizard", page_icon="📄", layout="wide")
init_stato()
st.title("Report")
banner_demo()

cma = get_cma()
comparto = get_comparto()
config = get_config()
proposte = get_proposte()

st.caption(
    "Esporta un file Excel strutturato con metadati, comparto, assunzioni, matrice, "
    "pesi delle proposte e risultati a confronto. Contiene risultati di modello, non "
    "testo deliberativo."
)

includi_sim = st.checkbox(
    "Includi risultati Monte Carlo (P(shortfall), VaR, ES)", value=True
)

st.write(f"Proposte incluse: {', '.join(proposte.keys())}")

if st.button("Genera report Excel", type="primary"):
    try:
        with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
            percorso = tmp.name
        genera_report_excel(
            percorso, cma, comparto, proposte, config,
            includi_simulazione=includi_sim,
        )
        with open(percorso, "rb") as fh:
            st.download_button(
                "Scarica report_dpi.xlsx", data=fh.read(),
                file_name="report_dpi.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        st.success("Report generato.")
    except Exception as exc:  # noqa: BLE001
        st.error(f"Generazione fallita: {exc}")
