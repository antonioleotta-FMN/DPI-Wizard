"""Smoke test delle pagine Streamlit (M4).

Usa AppTest (lo strumento ufficiale di Streamlit) per verificare che ogni pagina si
esegua senza sollevare eccezioni con i dati demo. Protegge da regressioni negli import
e nella catena pagina -> servizi.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from streamlit.testing.v1 import AppTest  # noqa: E402

_ROOT = Path(__file__).resolve().parents[1]

PAGINE = [
    "app.py",
    "pages/02_Comparti.py",
    "pages/03_Assunzioni.py",
    "pages/04_Correlazioni.py",
    "pages/05_Asset_Allocation_Lab.py",
    "pages/06_Simulazioni.py",
    "pages/07_Confronto.py",
    "pages/08_Controlli.py",
    "pages/09_Report.py",
]


@pytest.mark.parametrize("pagina", PAGINE)
def test_pagina_si_esegue_senza_eccezioni(pagina):
    at = AppTest.from_file(str(_ROOT / pagina), default_timeout=60).run()
    assert not at.exception, f"{pagina}: {[str(e.value) for e in at.exception]}"


def test_aa_lab_ricalcola_su_modifica_slider():
    at = AppTest.from_file(
        str(_ROOT / "pages/05_Asset_Allocation_Lab.py"), default_timeout=60
    ).run()
    assert len(at.slider) == 7
    assert len(at.metric) >= 4
    # muove uno slider e verifica che non si rompa
    at.slider[0].set_value(50.0).run()
    assert not at.exception
