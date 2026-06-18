"""Shock su strumenti a reddito fisso per gli stress test (M6).

Approssimazione del prezzo obbligazionario rispetto a variazioni di tasso, tramite
duration modificata e, se disponibile, convexity:

    dP/P ~= -D_mod * dy + 0.5 * C * dy^2

In assenza di convexity si usa la sola duration e si segnala l'approssimazione.

Funzioni pure: nessuna dipendenza da Streamlit.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class EsitoShockTasso:
    variazione_prezzo_pct: float   # dP/P, decimale (es. -0.07 = -7%)
    usata_convexity: bool
    nota: str


def shock_tasso(
    duration_modificata: float,
    delta_y: float,
    convexity: float | None = None,
) -> EsitoShockTasso:
    """Variazione percentuale di prezzo per uno shock di tasso delta_y.

    duration_modificata  duration modificata (anni)
    delta_y              variazione di rendimento in decimale (es. 0.01 = +100 bp)
    convexity            convexity, se disponibile
    """
    primo_ordine = -duration_modificata * delta_y
    if convexity is not None:
        secondo_ordine = 0.5 * convexity * delta_y * delta_y
        return EsitoShockTasso(
            variazione_prezzo_pct=primo_ordine + secondo_ordine,
            usata_convexity=True,
            nota="Approssimazione duration + convexity.",
        )
    return EsitoShockTasso(
        variazione_prezzo_pct=primo_ordine,
        usata_convexity=False,
        nota="Approssimazione di sola duration (convexity non disponibile).",
    )
