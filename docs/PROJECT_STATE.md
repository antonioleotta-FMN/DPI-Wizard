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
M8 — Integrazione, validazione complessiva e rilascio COMPLETATA. Integrazione pagine,
controlli architetturali, matrice di tracciabilita, registro algoritmi, rapporto di
validazione, verifica deploy. Suite 114 test verde.

Programma post-MVP approvato: M6 (fatta), M7 (ottimizzazione vincolata), M8
(integrazione e validazione), M9 (white paper finale).

## Funzionalità completate
- MVP completo M0-M5 (vedi changelog).
- M6: src/simulations/distributions.py (normale + t multivariata, df configurabile);
  src/simulations/path_engine.py (multi-periodo, frequenza, ribilanciamento, flussi,
  drawdown); src/calculations/risk_metrics.py (VaR, ES, shortfall condizionato,
  drawdown); src/stress_testing/* (scenari demo, motore deterministico, shock fixed
  income); src/services/simulation_service.py (facade); pagina 10.
- M7: ottimizzazione vincolata (src/optimization/*), service e pagina 11.

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
  test_reporting (3), test_pages (11), test_distributions (7), test_path_engine (6),
  test_stress (8), test_optimization (14), test_integration (5). Totale: 114 test, tutti passati.

## Problemi aperti
- DEC-001 e DEC-002 provvisori/configurabili: da validare dagli organi/Funzione Risk
  del Fondo prima dell'uso istituzionale (vedi avvertenza in pagina 10).

## Decisioni richieste all'utente
Nessuna. Programma M6-M9 approvato: si prosegue senza nuova scelta.

## Prossima milestone proposta
M9 — White paper metodologico finale. Redazione di docs/WHITE_PAPER.md (fonte primaria)
e, se possibile, versioni .docx/.pdf coerenti. Documenta solo le metodologie realmente
implementate, collegando formula-codice-test, distinguendo validato/sperimentale/
previsto/escluso. Fonti: codice definitivo, PROJECT_STATE, DECISIONS, TRACEABILITY_MATRIX,
ALGORITHM_REGISTER, VALIDATION_REPORT, test, manuali, changelog.