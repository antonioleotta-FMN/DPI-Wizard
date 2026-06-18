"""Definizione degli scenari di stress deterministici (M6).

Uno scenario applica shock a una o piu' asset class. Gli shock sono espressi come:
  - shock_rendimento_diretto: variazione percentuale di prezzo applicata direttamente
    all'asset class (es. azionario -20%);
  - shock_tasso: variazione di tasso (delta_y) applicata alle asset class con duration,
    tradotta in variazione di prezzo via duration/convexity.

Gli scenari demo sono ETICHETTATI e MODIFICABILI: sono punti di partenza plausibili,
non scenari ufficiali del Fondo. Gli stress test sono deterministici e non vanno
interpretati come probabilita.

I match sulle asset class sono per sottostringa del nome (case-insensitive), cosi' da
restare robusti a rinomine del set CMA demo.
"""

from __future__ import annotations

from dataclasses import dataclass, field

ETICHETTA_DEMO = "[DEMO]"


@dataclass
class ShockAssetClass:
    """Shock applicato alle asset class il cui nome contiene 'match' (case-insensitive)."""

    match: str
    shock_rendimento_diretto: float | None = None  # es. -0.20
    shock_tasso_delta_y: float | None = None        # es. +0.01 (=+100bp)
    descrizione: str = ""


@dataclass
class ScenarioStress:
    nome: str
    shock: list[ShockAssetClass] = field(default_factory=list)
    descrizione: str = ""


def scenari_demo() -> list[ScenarioStress]:
    """Restituisce un insieme di scenari di stress demo, modificabili dall'utente."""
    return [
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Azionario -20%",
            shock=[ShockAssetClass(match="equity", shock_rendimento_diretto=-0.20,
                                   descrizione="Azionario globale -20%")],
            descrizione="Ribasso azionario moderato.",
        ),
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Azionario -30%",
            shock=[ShockAssetClass(match="equity", shock_rendimento_diretto=-0.30,
                                   descrizione="Azionario globale -30%")],
            descrizione="Ribasso azionario severo.",
        ),
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Tassi +100bp",
            shock=[ShockAssetClass(match="govt", shock_tasso_delta_y=0.01,
                                   descrizione="Rialzo parallelo +100bp (govt)"),
                   ShockAssetClass(match="corporate", shock_tasso_delta_y=0.01,
                                   descrizione="Rialzo parallelo +100bp (corporate)")],
            descrizione="Rialzo parallelo dei tassi di 100 punti base.",
        ),
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Tassi +200bp",
            shock=[ShockAssetClass(match="govt", shock_tasso_delta_y=0.02),
                   ShockAssetClass(match="corporate", shock_tasso_delta_y=0.02)],
            descrizione="Rialzo parallelo dei tassi di 200 punti base.",
        ),
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Illiquidi sotto stress",
            shock=[ShockAssetClass(match="real", shock_rendimento_diretto=-0.15,
                                   descrizione="Real assets -15%"),
                   ShockAssetClass(match="private", shock_rendimento_diretto=-0.25,
                                   descrizione="Private markets -25%")],
            descrizione="Svalutazione degli attivi illiquidi.",
        ),
        ScenarioStress(
            nome=f"{ETICHETTA_DEMO} Scenario combinato",
            shock=[ShockAssetClass(match="equity", shock_rendimento_diretto=-0.25),
                   ShockAssetClass(match="govt", shock_tasso_delta_y=0.01),
                   ShockAssetClass(match="corporate", shock_tasso_delta_y=0.015),
                   ShockAssetClass(match="real", shock_rendimento_diretto=-0.15),
                   ShockAssetClass(match="private", shock_rendimento_diretto=-0.20)],
            descrizione="Azioni in calo, spread e tassi in aumento, illiquidi in calo.",
        ),
    ]
