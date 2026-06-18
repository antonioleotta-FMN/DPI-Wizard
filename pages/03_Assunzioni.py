"""Pagina Assunzioni: gestione delle Capital Market Assumptions (CMA)."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pandas as pd
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.ui_state import banner_demo, get_cma, init_stato, set_cma  # noqa: E402
from src.data.excel_io import esporta_cma_excel, importa_cma_excel  # noqa: E402
from src.domain.models import AssetClass, CMASet, MatriceCorrelazione  # noqa: E402

init_stato()
st.title("Assunzioni delle asset class")
banner_demo()

cma = get_cma()

# ----------------------------- editor tabellare -------------------------- #
st.subheader("Capital Market Assumptions")
st.caption("Modifica i valori; le righe possono essere aggiunte o rimosse.")

df = pd.DataFrame([
    {
        "nome": ac.nome, "mu_nominale": ac.mu_nominale, "sigma": ac.sigma,
        "costo": ac.costo, "duration": ac.duration, "illiquidita": ac.illiquidita,
        "valuta": ac.valuta, "copertura_valutaria": ac.copertura_valutaria,
        "peso_min": ac.peso_min, "peso_max": ac.peso_max,
    }
    for ac in cma.asset_class
])

df_mod = st.data_editor(
    df, num_rows="dynamic", width='stretch',
    column_config={
        "mu_nominale": st.column_config.NumberColumn("Rend. nominale", format="%.4f"),
        "sigma": st.column_config.NumberColumn("Volatilita", format="%.4f"),
        "costo": st.column_config.NumberColumn("Costo (TER)", format="%.4f"),
        "copertura_valutaria": st.column_config.NumberColumn("Cop. valutaria", format="%.2f"),
        "peso_min": st.column_config.NumberColumn("Peso min", format="%.2f"),
        "peso_max": st.column_config.NumberColumn("Peso max", format="%.2f"),
    },
)

if st.button("Applica modifiche alle assunzioni", type="primary"):
    try:
        nuove_ac = []
        for _, r in df_mod.iterrows():
            if not r["nome"] or pd.isna(r["nome"]):
                continue
            nuove_ac.append(AssetClass(
                nome=str(r["nome"]), mu_nominale=float(r["mu_nominale"]),
                sigma=float(r["sigma"]), costo=float(r["costo"] or 0.0),
                duration=None if pd.isna(r["duration"]) else float(r["duration"]),
                illiquidita=bool(r["illiquidita"]),
                valuta=str(r["valuta"]) if r["valuta"] else "EUR",
                copertura_valutaria=float(r["copertura_valutaria"] or 0.0),
                peso_min=float(r["peso_min"] or 0.0),
                peso_max=float(r["peso_max"] or 1.0),
            ))
        nomi = [ac.nome for ac in nuove_ac]
        # ricostruisce la matrice: mantiene le correlazioni esistenti dove i nomi
        # coincidono, identita' altrove. Mai modifica silenziosa dei dati esistenti.
        vecchie = {n: i for i, n in enumerate(cma.correlazioni.etichette)}
        n = len(nomi)
        valori = [[1.0 if i == j else 0.0 for j in range(n)] for i in range(n)]
        for i, ni in enumerate(nomi):
            for j, nj in enumerate(nomi):
                if ni in vecchie and nj in vecchie:
                    valori[i][j] = cma.correlazioni.valori[vecchie[ni]][vecchie[nj]]
        nuovo_cma = CMASet(
            nome=cma.nome.replace("[DEMO] ", "") if "[DEMO]" in cma.nome else cma.nome,
            versione=cma.versione,
            asset_class=nuove_ac,
            correlazioni=MatriceCorrelazione(etichette=nomi, valori=valori),
        )
        set_cma(nuovo_cma)
        st.success(
            "Assunzioni aggiornate. Controlla la matrice di correlazione nella pagina "
            "dedicata: per le nuove asset class e' stata impostata correlazione nulla."
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Dati non validi: {exc}")

st.divider()

# ----------------------------- import / export --------------------------- #
st.subheader("Import / Export Excel")
col_imp, col_exp = st.columns(2)

with col_imp:
    st.markdown("**Importa un set CMA da Excel**")
    file = st.file_uploader("File .xlsx", type=["xlsx"], key="cma_upload")
    if file is not None and st.button("Carica file"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                tmp.write(file.getvalue())
                percorso = tmp.name
            nuovo = importa_cma_excel(percorso)
            set_cma(nuovo)
            st.success(f"Importato: {nuovo.nome} ({len(nuovo.asset_class)} asset class)")
        except Exception as exc:  # noqa: BLE001
            st.error(f"Import fallito: {exc}")

with col_exp:
    st.markdown("**Esporta il set CMA corrente**")
    if st.button("Genera Excel"):
        try:
            with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                percorso = tmp.name
            esporta_cma_excel(cma, percorso)
            with open(percorso, "rb") as fh:
                st.download_button(
                    "Scarica cma.xlsx", data=fh.read(),
                    file_name="cma.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                )
        except Exception as exc:  # noqa: BLE001
            st.error(f"Export fallito: {exc}")
