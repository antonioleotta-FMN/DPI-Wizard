"""Modelli di dominio di DPI Wizard.

Questo modulo definisce SOLO le strutture dati e le loro regole di validazione.
Non contiene formule finanziarie (che vivono in src/calculations e src/simulations)
ne logica di interfaccia. E' il contratto dati condiviso tra tutti gli agenti/moduli.

Convenzioni:
- Rendimenti, volatilita, costi, inflazione: forma decimale annua (0.05 = 5%).
- Pesi di portafoglio: sommano a 1 con tolleranza TOL_PESI.
- Correlazioni: in [-1, 1], diagonale 1, matrice simmetrica.
"""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, Field, field_validator, model_validator

TOL_PESI = 1e-6


# --------------------------------------------------------------------------- #
# Enumerazioni di supporto
# --------------------------------------------------------------------------- #
class TipoObiettivo(str, Enum):
    """Natura dell'obiettivo di rendimento di un comparto."""

    NOMINALE = "nominale"
    REALE = "reale"


class DefinizioneShortfall(str, Enum):
    """Definizioni selezionabili di evento di shortfall (DEC-001).

    Il default operativo e' REALE_NEGATIVO. Tutte le definizioni sono
    parametrizzabili dall'utente.
    """

    REALE_NEGATIVO = "reale_negativo"          # rendimento reale < 0
    REALE_SOTTO_OBIETTIVO = "reale_sotto_obiettivo"   # rendimento reale < obiettivo
    NOMINALE_NEGATIVO = "nominale_negativo"    # rendimento nominale < 0
    SOTTO_INFLAZIONE = "sotto_inflazione"      # rendimento nominale < inflazione
    MONTANTE_SOTTO_SOGLIA = "montante_sotto_soglia"   # montante < soglia assoluta


# --------------------------------------------------------------------------- #
# Asset class e Capital Market Assumptions
# --------------------------------------------------------------------------- #
class AssetClass(BaseModel):
    """Assunzioni di mercato per una singola asset class (DEC-005, DEC-007)."""

    nome: str = Field(..., min_length=1)
    mu_nominale: float = Field(..., description="Rendimento nominale atteso, annuo")
    mu_reale: float | None = Field(
        None, description="Rendimento reale atteso, annuo. Se None, derivato via Fisher."
    )
    sigma: float = Field(..., ge=0.0, description="Volatilita annua")
    costo: float = Field(0.0, ge=0.0, description="TER annuo (DEC-007)")
    duration: float | None = Field(None, description="Duration in anni, se applicabile")
    illiquidita: bool = Field(False, description="True se asset class illiquida")
    valuta: str = Field("EUR", min_length=3, max_length=3)
    copertura_valutaria: float = Field(
        0.0, ge=0.0, le=1.0, description="Quota di copertura valutaria, 0..1"
    )
    peso_min: float = Field(0.0, ge=0.0, le=1.0)
    peso_max: float = Field(1.0, ge=0.0, le=1.0)

    @model_validator(mode="after")
    def _check_bande(self) -> AssetClass:
        if self.peso_min > self.peso_max:
            raise ValueError(
                f"peso_min ({self.peso_min}) > peso_max ({self.peso_max}) "
                f"per asset class '{self.nome}'"
            )
        return self


class MatriceCorrelazione(BaseModel):
    """Matrice di correlazione tra asset class.

    Conserva l'esito della validazione strutturale. La verifica di semi-definitezza
    positiva e l'eventuale proposta di correzione (Higham, DEC-006) sono delegate a
    src/data: il dominio non corregge mai silenziosamente.
    """

    etichette: list[str] = Field(..., min_length=1)
    valori: list[list[float]]

    @model_validator(mode="after")
    def _check_struttura(self) -> MatriceCorrelazione:
        n = len(self.etichette)
        if len(self.valori) != n:
            raise ValueError(
                f"La matrice ha {len(self.valori)} righe ma {n} etichette"
            )
        for i, riga in enumerate(self.valori):
            if len(riga) != n:
                raise ValueError(f"La riga {i} ha {len(riga)} elementi, attesi {n}")
            for j, v in enumerate(riga):
                if not -1.0 <= v <= 1.0:
                    raise ValueError(
                        f"Valore fuori range [-1,1] in posizione ({i},{j}): {v}"
                    )
        # diagonale = 1
        for i in range(n):
            if abs(self.valori[i][i] - 1.0) > 1e-9:
                raise ValueError(f"Diagonale non unitaria in posizione ({i},{i})")
        # simmetria
        for i in range(n):
            for j in range(i + 1, n):
                if abs(self.valori[i][j] - self.valori[j][i]) > 1e-9:
                    raise ValueError(f"Matrice non simmetrica in ({i},{j})")
        return self


class CMASet(BaseModel):
    """Set versionato di Capital Market Assumptions.

    Una collezione DINAMICA di asset class (DEC-005): l'utente puo aggiungere,
    rimuovere o rinominare le classi. Include la matrice di correlazione associata.
    """

    nome: str = Field(..., min_length=1)
    versione: str = Field("1.0")
    asset_class: list[AssetClass] = Field(..., min_length=1)
    correlazioni: MatriceCorrelazione

    @model_validator(mode="after")
    def _check_coerenza(self) -> CMASet:
        nomi = [ac.nome for ac in self.asset_class]
        if len(nomi) != len(set(nomi)):
            raise ValueError("Nomi di asset class duplicati nel CMASet")
        if set(nomi) != set(self.correlazioni.etichette):
            raise ValueError(
                "Le etichette della matrice non corrispondono alle asset class"
            )
        return self


# --------------------------------------------------------------------------- #
# Comparto e configurazioni
# --------------------------------------------------------------------------- #
class ConfigShortfall(BaseModel):
    """Configurazione parametrizzabile della metrica di shortfall (DEC-001)."""

    definizione: DefinizioneShortfall = DefinizioneShortfall.REALE_NEGATIVO
    soglia_montante: float | None = Field(
        None,
        description="Soglia assoluta del montante, usata solo se definizione = "
        "MONTANTE_SOTTO_SOGLIA",
    )

    @model_validator(mode="after")
    def _check_soglia(self) -> ConfigShortfall:
        if (
            self.definizione == DefinizioneShortfall.MONTANTE_SOTTO_SOGLIA
            and self.soglia_montante is None
        ):
            raise ValueError(
                "soglia_montante obbligatoria con definizione MONTANTE_SOTTO_SOGLIA"
            )
        return self


class ConfigSimulazione(BaseModel):
    """Parametri della simulazione Monte Carlo e delle metriche di rischio.

    DEC-002 (confidenza/orizzonte VaR), DEC-003 (geometrico), DEC-004 (inflazione
    deterministica editabile), DEC-008 (ribilanciamento annuale).
    """

    n_simulazioni: int = Field(10_000, ge=100)
    seed: int = Field(42, description="Seed per riproducibilita")
    confidenza_var: float = Field(0.95, gt=0.5, lt=1.0, description="DEC-002")
    orizzonte_var_anni: int = Field(1, ge=1, description="DEC-002")
    inflazione: float = Field(0.02, description="Inflazione annua deterministica, DEC-004")
    ribilanciamento_annuale: bool = Field(True, description="DEC-008")


class Comparto(BaseModel):
    """Configurazione di un comparto previdenziale."""

    nome: str = Field(..., min_length=1)
    patrimonio: float = Field(..., ge=0.0)
    orizzonte_anni: int = Field(..., ge=1)
    obiettivo_rendimento: float = Field(..., description="Obiettivo annuo")
    tipo_obiettivo: TipoObiettivo = TipoObiettivo.REALE
    liquidita_minima: float = Field(0.0, ge=0.0, le=1.0)
    quota_max_illiquida: float = Field(1.0, ge=0.0, le=1.0)
    benchmark: str | None = None
    shortfall: ConfigShortfall = Field(default_factory=ConfigShortfall)


# --------------------------------------------------------------------------- #
# Proposta di Asset Allocation
# --------------------------------------------------------------------------- #
class Proposta(BaseModel):
    """Proposta di Asset Allocation Strategica: pesi per asset class."""

    nome: str = Field(..., min_length=1)
    pesi: dict[str, float]

    @field_validator("pesi")
    @classmethod
    def _check_pesi_non_negativi(cls, v: dict[str, float]) -> dict[str, float]:
        for nome, peso in v.items():
            if peso < 0.0:
                raise ValueError(f"Peso negativo per '{nome}': {peso}")
        return v

    @model_validator(mode="after")
    def _check_somma(self) -> Proposta:
        somma = sum(self.pesi.values())
        if abs(somma - 1.0) > TOL_PESI:
            raise ValueError(
                f"I pesi della proposta '{self.nome}' sommano a {somma}, atteso 1.0"
            )
        return self

    def coerente_con(self, cma: CMASet) -> bool:
        """True se le chiavi dei pesi coincidono con le asset class del CMASet."""
        return set(self.pesi) == {ac.nome for ac in cma.asset_class}
