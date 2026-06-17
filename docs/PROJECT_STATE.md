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
M3 — Monte Carlo + motore vincoli + pagina diagnostica COMPLETATA.

## Funzionalità completate
- Albero cartelle del repository (M0).
- Modelli di dominio Pydantic (M0).
- Metriche deterministiche (M1).
- Data layer (M2): PSD/Higham, demo, IO Excel.
- Monte Carlo normale multivariata (M3): orizzonti, costi, inflazione, ribilanciamento
  annuale, seed, percentili, P(shortfall) per definizione attiva, VaR, ES di mercato,
  ES mancato obiettivo.
- Motore vincoli (M3): bande asset class, quota illiquida, liquidita minima, somma
  pesi; esito a semaforo OK/WARNING/VIOLATO con riepilogo.
- Service layer (M3): facade dominio->calcoli/simulazioni/vincoli; conversione ad
  array ordinati.
- app.py: pagina diagnostica Streamlit deployabile (smoke test, dati demo).

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
- app.py — entrypoint Streamlit, pagina diagnostica (M3).
- src/domain/models.py — modelli di dominio (M0).
- src/calculations/metrics.py — metriche deterministiche (M1).
- src/data/{validation,demo,excel_io}.py — data layer (M2).
- src/simulations/montecarlo.py — Monte Carlo (M3).
- src/constraints/engine.py — motore vincoli (M3).
- src/services/portfolio_service.py — facade dominio<->UI (M3).
- docs/{PROJECT_STATE,DECISIONS,GITHUB,STREAMLIT_DEPLOY}.md.

## Test disponibili
- tests/test_domain.py (19), test_calculations.py (15), test_data.py (10),
  test_simulations.py (12). Totale: 56 test, tutti passati.
- App verificata in avvio headless (health check ok).

## Problemi aperti
- DEC-001 e DEC-002 da validare dagli organi/Funzione Risk del Fondo prima dell'uso
  con dati reali.

## Decisioni richieste all'utente
Nessuna in sospeso. Alla fine di M3: approvazione per passare a M4 (MVP multipage).

## Prossima milestone proposta
M4 — MVP UI multipage: trasformare la diagnostica nelle 9 pagine previste (home,
comparti, assunzioni, correlazioni, AA Lab, simulazioni, confronto, controlli, report),
con import/export Excel collegati, editing dei pesi e confronto scenari. Le pagine
useranno solo i servizi gia' pronti. Poi M5 (reporting/export completo) e rilascio.
