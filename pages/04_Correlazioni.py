"""Pagina Correlazioni: matrice, validazione PSD e proposta di correzione (DEC-006)."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pages._state import banner_demo, get_cma, init_stato, set_cma  # noqa: E402
from src.data.validation import valida_psd  # noqa: E402
from src.domain.models import CMASet, MatriceCorrelazione  # noqa: E402

st.set_page_config(page_title="Correlazioni — DPI Wizard", page_icon="🔗", layout="wide")
init_stato()
st.title("Matrice di correlazione")
banner_demo()

cma = get_cma()
etich = cma.correlazioni.etichette

st.subheader("Modifica la matrice")
st.caption(
    "La matrice deve essere simmetrica, con diagonale 1 e valori in [-1, 1]. "
    "Modifica il triangolo superiore: la simmetria viene applicata al salvataggio."
)

df = pd.DataFrame(cma.correlazioni.valori, index=etich, columns=etich)
df_mod = st.data_editor(df, width='stretch')

# ----------------------------- heatmap ----------------------------------- #
st.subheader("Heatmap")
fig = go.Figure(go.Heatmap(
    z=df_mod.values, x=etich, y=etich, zmin=-1, zmax=1,
    colorscale="RdBu", reversescale=True, zmid=0,
    text=np.round(df_mod.values, 2), texttemplate="%{text}",
))
fig.update_layout(height=460, margin=dict(l=10, r=10, t=10, b=10))
fig.update_yaxes(autorange="reversed")  # diagonale top-left -> bottom-right
st.plotly_chart(fig, width='stretch')

# ----------------------------- validazione ------------------------------- #
if st.button("Valida e salva", type="primary"):
    m = df_mod.values.astype(float)
    # simmetrizza usando il triangolo superiore, forza diagonale 1
    m_sym = np.triu(m) + np.triu(m, 1).T
    np.fill_diagonal(m_sym, 1.0)
    try:
        matrice = MatriceCorrelazione(
            etichette=list(etich), valori=m_sym.tolist()
        )
    except Exception as exc:  # noqa: BLE001
        st.error(f"Matrice strutturalmente non valida: {exc}")
        st.stop()

    esito = valida_psd(m_sym)
    for msg in esito.messaggi:
        st.write("• " + msg)

    if esito.is_psd:
        nuovo = CMASet(
            nome=cma.nome, versione=cma.versione,
            asset_class=cma.asset_class, correlazioni=matrice,
        )
        set_cma(nuovo)
        st.success("Matrice valida e salvata.")
    else:
        # DEC-006: la correzione e' una PROPOSTA, mai applicata in automatico
        st.warning(
            "La matrice non e' semi-definita positiva. Puoi accettare la correzione "
            "proposta (matrice valida piu' vicina) oppure modificare i valori a mano."
        )
        st.session_state["_proposta_psd"] = esito.matrice_proposta.tolist()

if st.session_state.get("_proposta_psd") is not None:
    if st.button("Accetta la correzione proposta"):
        prop = np.array(st.session_state["_proposta_psd"])
        matrice = MatriceCorrelazione(etichette=list(etich), valori=prop.tolist())
        set_cma(CMASet(
            nome=cma.nome, versione=cma.versione,
            asset_class=cma.asset_class, correlazioni=matrice,
        ))
        st.session_state["_proposta_psd"] = None
        st.success("Correzione applicata e salvata.")
        st.rerun()
