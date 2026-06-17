"""Dataset demo di DPI Wizard (M2, DEC-005).

Fornisce un CMASet e un Comparto demo con le 7 macro asset class approvate. I valori
sono PLAUSIBILI MA FITTIZI, a solo scopo dimostrativo: NON sono Capital Market
Assumptions ufficiali del Fondo e non devono essere usati per decisioni reali.

Il marcatore ETICHETTA_DEMO viene propagato nei nomi dei set in modo che l'origine
demo resti visibile in UI e nei report (requisito di non confondere demo e dato
ufficiale, sezione 14 del prompt).
"""

from __future__ import annotations

from src.domain.models import (
    AssetClass,
    CMASet,
    Comparto,
    ConfigShortfall,
    DefinizioneShortfall,
    MatriceCorrelazione,
    TipoObiettivo,
)

ETICHETTA_DEMO = "[DEMO]"

# Ordine canonico delle asset class demo. Usato anche per le righe/colonne della
# matrice di correlazione: l'ordine DEVE coincidere.
_NOMI = [
    "Liquidita",
    "Govt EUR",
    "Corporate",
    "Equity DM",
    "Equity EM",
    "Real assets",
    "Private markets",
]


def _asset_class_demo() -> list[AssetClass]:
    # (nome, mu_nom, sigma, costo, duration, illiquida, valuta, cop_val, pmin, pmax)
    righe = [
        ("Liquidita",       0.020, 0.010, 0.0010, 0.3,  False, "EUR", 0.0, 0.00, 0.30),
        ("Govt EUR",        0.030, 0.050, 0.0015, 7.0,  False, "EUR", 0.0, 0.00, 0.60),
        ("Corporate",       0.040, 0.070, 0.0025, 5.0,  False, "EUR", 0.0, 0.00, 0.40),
        ("Equity DM",       0.070, 0.160, 0.0030, None, False, "USD", 0.5, 0.00, 0.50),
        ("Equity EM",       0.085, 0.220, 0.0050, None, False, "USD", 0.3, 0.00, 0.25),
        ("Real assets",     0.055, 0.120, 0.0060, None, False, "EUR", 0.0, 0.00, 0.20),
        ("Private markets", 0.090, 0.180, 0.0150, None, True,  "EUR", 0.0, 0.00, 0.15),
    ]
    return [
        AssetClass(
            nome=n, mu_nominale=mu, sigma=s, costo=c, duration=d,
            illiquidita=ill, valuta=val, copertura_valutaria=cop,
            peso_min=pmin, peso_max=pmax,
        )
        for (n, mu, s, c, d, ill, val, cop, pmin, pmax) in righe
    ]


def _matrice_correlazione_demo() -> MatriceCorrelazione:
    # Matrice simmetrica plausibile (diagonale 1). Ordine = _NOMI.
    v = [
        [1.00, 0.10, 0.05, -0.05, -0.05, 0.00, 0.00],  # Liquidita
        [0.10, 1.00, 0.60,  0.10,  0.05, 0.20, 0.10],  # Govt EUR
        [0.05, 0.60, 1.00,  0.35,  0.30, 0.30, 0.25],  # Corporate
        [-0.05, 0.10, 0.35, 1.00,  0.75, 0.55, 0.65],  # Equity DM
        [-0.05, 0.05, 0.30, 0.75,  1.00, 0.50, 0.55],  # Equity EM
        [0.00, 0.20, 0.30,  0.55,  0.50, 1.00, 0.45],  # Real assets
        [0.00, 0.10, 0.25,  0.65,  0.55, 0.45, 1.00],  # Private markets
    ]
    return MatriceCorrelazione(etichette=list(_NOMI), valori=v)


def cma_demo() -> CMASet:
    """Restituisce il CMASet demo (etichettato)."""
    return CMASet(
        nome=f"{ETICHETTA_DEMO} CMA base",
        versione="1.0",
        asset_class=_asset_class_demo(),
        correlazioni=_matrice_correlazione_demo(),
    )


def comparto_demo() -> Comparto:
    """Restituisce un comparto demo (orizzonte lungo, obiettivo reale)."""
    return Comparto(
        nome=f"{ETICHETTA_DEMO} Comparto Bilanciato",
        patrimonio=100_000_000.0,
        orizzonte_anni=15,
        obiettivo_rendimento=0.02,  # 2% reale annuo
        tipo_obiettivo=TipoObiettivo.REALE,
        liquidita_minima=0.05,
        quota_max_illiquida=0.15,
        benchmark=f"{ETICHETTA_DEMO} 50/50 Govt-Equity",
        shortfall=ConfigShortfall(definizione=DefinizioneShortfall.REALE_NEGATIVO),
    )


def nomi_asset_class_demo() -> list[str]:
    """Ordine canonico delle asset class demo."""
    return list(_NOMI)
