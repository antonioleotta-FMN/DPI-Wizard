# Stato corrente del progetto

## Obiettivo generale
Web app Python/Streamlit "DPI Wizard" a supporto della Funzione Finanza del Fondo
Pensione Mario Negri per definizione, verifica e revisione del Documento sulla
Politica di Investimento (DPI). L'app mostra come variano rendimento (nominale, netto
costi, reale), rischio, probabilità ed entità di shortfall, Expected Shortfall,
liquidità ed esposizione valutaria al modificarsi dell'Asset Allocation Strategica
(AAS) di un comparto. Non è un ottimizzatore: è un laboratorio di analisi e confronto
con verifica dei vincoli e output riutilizzabili nel DPI.

## Milestone corrente
M5 — Rifinitura e documentazione COMPLETATA. MVP completo (M0-M5).

## Funzionalità completate
- Albero cartelle del repository (M0).
- Modelli di dominio Pydantic (M0).
- Metriche deterministiche (M1) + conversione geometrica (M5).
- Data layer (M2): PSD/Higham, demo, IO Excel.
- Monte Carlo + motore vincoli + service layer (M3).
- MVP UI multipage (M4): 9 pagine.
- Rifinitura e documentazione (M5): proiezioni geometriche (DEC-003) nel Lab e nei
  servizi; manuale utente, manuale metodologico, glossario+data dictionary, changelog.

## Decisioni approvate
Vedi docs/DECISIONS.md. Sintesi:
- DEC-001 Shortfall default = rendimento reale negativo, MA definizione parametrizzabile.
- DEC-002 VaR/ES a 95%, orizzonte 1 anno.
- DEC-003 Proiezioni pluriennali: rendimento geometrico.
- DEC-004 Inflazione deterministica, modificabile nelle ipotesi.
- DEC-005 7 asset class demo, modificabili.
- DEC-006 Correzione matrice non-PSD: Higham, solo proposta (mai silenziosa).
- DEC-007 Costi = TER annuo costante per asset class.
- DEC-008 Ribilanciamento annuale fisso (MVP).
- DEC-009 Lingua: italiano.
- DEC-010 GitHub: main + commit diretti + tag versioni.

## Architettura vigente
dpi-wizard/
  app.py (entrypoint, da creare in M2)
  pages/        -> SOLO presentazione, zero formule
  src/domain/   -> modelli Pydantic (FATTO)
  src/calculations/  -> metriche deterministiche (M1)
  src/simulations/   -> Monte Carlo (M1+)
  src/constraints/   -> motore vincoli (M1+)
  src/data/     -> IO Excel/CSV, validazione, demo, versioning CMA
  src/reporting/-> export Excel, audit trail
  src/services/ -> facade dominio<->UI (le pagine chiamano solo i servizi)
  config/ data/demo/ tests/ docs/ .streamlit/

Principio inviolabile: nessuna formula finanziaria rilevante nelle pagine Streamlit.

## Convenzioni tecniche
- Python 3.12. Pydantic v2. pandas 3.x, numpy 2.x.
- Rendimenti e volatilità in forma decimale annua (0.05 = 5%).
- Pesi sommano a 1 (tolleranza 1e-6).
- Tipizzazione esplicita; dataclass/Pydantic per le strutture dati.

## Formule e metodologie approvate
Specificate in Fase 1 (vedi conversazione). Da formalizzare in schede complete in M1:
rendimento atteso w'µ; volatilità sqrt(w'Σw) con Σ=DCD; rendimento reale (Fisher
esatto); netto costi; MCTR/CCTR/PCTR; shortfall (default reale<0, parametrizzabile);
ES di mercato (CVaR) vs mancato raggiungimento obiettivo (denominazioni distinte);
VaR percentile; Monte Carlo normale multivariata.

## File principali
- app.py — Home Streamlit (M4).
- pages/_state.py — stato condiviso (M4).
- pages/02..09_*.py — le 8 pagine funzionali (M4).
- src/domain/models.py — modelli (M0).
- src/calculations/metrics.py — metriche (M1).
- src/data/{validation,demo,excel_io}.py — data layer (M2).
- src/simulations/montecarlo.py — Monte Carlo (M3).
- src/constraints/engine.py — vincoli (M3).
- src/services/portfolio_service.py — facade (M3).
- src/reporting/excel_report.py — report Excel (M4).
- docs/{PROJECT_STATE,DECISIONS,GITHUB,STREAMLIT_DEPLOY}.md.

## Test disponibili
- test_domain (19), test_calculations (18), test_data (10), test_simulations (12),
  test_reporting (3), test_pages (10). Totale: 72 test, tutti passati.

## Problemi aperti
- DEC-001 e DEC-002 da validare dagli organi/Funzione Risk del Fondo prima dell'uso
  con dati reali (scelte metodologiche che confluiscono nel DPI).

## Decisioni richieste all'utente
Nessuna. MVP completo. Da concordare l'eventuale roadmap post-MVP.

## Prossima milestone proposta
MVP completato (M0-M5). Possibili sviluppi post-MVP, fuori dall'attuale perimetro:
metodologie avanzate (t-Student, bootstrap, regimi, correlazioni stressate);
ottimizzatore vincolato; persistenza su database; autenticazione; white paper
metodologico esteso in PDF. Da avviare solo previa nuova definizione di perimetro e
approvazione.
