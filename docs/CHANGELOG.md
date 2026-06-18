# Changelog — DPI Wizard

Tutte le modifiche rilevanti, per milestone. Le versioni stabili sono marcate con tag
Git (DEC-010).

## [0.4.0] — M8 — Integrazione, validazione e rilascio

- Matrice di tracciabilità (docs/TRACEABILITY_MATRIX.md): requisito → pagina → modulo →
  funzione → formula → parametri → test → doc.
- Registro algoritmi completo (docs/ALGORITHM_REGISTER.md, ALG-01..ALG-25).
- Rapporto di validazione (docs/VALIDATION_REPORT.md): perimetro, ambiente, test,
  tolleranze, performance, controlli finali, anomalie risolte, limiti.
- Controllo architetturale "nessuna formula nelle pagine": corretto il fan chart della
  pagina 10 (np.percentile spostato in calculations/risk_metrics.bande_percentili).
- Gestione del caso limite "montante non positivo" nel rendimento geometrico.
- Test di integrazione end-to-end (tests/test_integration.py).
- 114 test complessivi, tutti verdi. Deploy verificato.

## [0.3.0] — M7 — Ottimizzazione vincolata dell'AAS

- Funzioni obiettivo: minima varianza, massimo rendimento, massimo Sharpe
  (src/optimization/objectives.py).
- Vincoli configurabili: budget, bounds, gruppi, liquidità, illiquidità, rendimento,
  volatilità, duration, valuta, turnover (src/optimization/constraints.py).
- Solver SLSQP (DEC-015); turnover riformulato a variabili ausiliarie (DEC-016).
- Frontiera efficiente e diagnostica di infeasibilità (efficient_frontier.py).
- Pagina "Ottimizzazione AAS" (pagina 11). Validazione: minima varianza = soluzione
  analitica. 109 test.

## [0.2.0] — M6 — Simulazione CMA e stress test

- Distribuzioni normale e t di Student multivariata, df configurabile (DEC-012).
- Percorsi multi-periodo: frequenza, ribilanciamento, flussi, drawdown (DEC-014).
- Metriche di rischio: VaR, ES, shortfall, shortfall medio condizionato.
- Stress test deterministici separati dal Monte Carlo (DEC-013): scenari demo, shock di
  tasso via duration/convexity.
- Pagina "Simulazione CMA e Stress Test" (pagina 10). 94 test.

## [0.1.0] — MVP (M0 -> M5)

### M5 — Rifinitura e documentazione
- Allineamento delle proiezioni deterministiche alla convenzione geometrica (DEC-003):
  nuove funzioni rendimento_geometrico e montante_atteso; Asset Allocation Lab mostra
  rendimento reale geometrico e montante reale atteso sull'orizzonte del comparto.
- Documentazione: manuale utente, manuale metodologico, glossario e data dictionary,
  changelog.
- 72 test complessivi.

### M4 — MVP UI multipage
- Nove pagine Streamlit: Home, Comparti, Assunzioni, Correlazioni, Asset Allocation
  Lab, Simulazioni, Confronto, Controlli, Report.
- Stato condiviso centralizzato (session_state) in pages/_state.py.
- Reporting Excel completo (src/reporting).
- Smoke test di tutte le pagine via AppTest.
- Compatibilita cloud: sostituito use_container_width (deprecato) con width='stretch';
  pin Streamlit >= 1.49.

### M3 — Monte Carlo, vincoli, service layer
- Simulazione Monte Carlo normale multivariata: orizzonti, costi, inflazione,
  ribilanciamento annuale, seed, percentili, P(shortfall), VaR, ES.
- Motore vincoli con esito a semaforo (interni, strategici, normativi).
- Service layer facade tra dominio e moduli numerici.
- Pagina diagnostica deployabile.

### M2 — Data layer
- Validazione PSD e proposta di correzione Higham (mai applicata silenziosamente).
- Dataset demo etichettato con sette asset class.
- Import/export Excel dei set CMA.

### M1 — Metriche deterministiche
- Rendimento atteso, volatilita, rendimento reale (Fisher), netto costi, contributo
  al rischio. Schede metodologiche e test numerici indipendenti.

### M0 — Scaffold
- Struttura del repository, modelli di dominio Pydantic, file di stato e decisioni.

## Fuori dall'MVP (previsto, non implementato)
- Distribuzione t di Student, bootstrap storico, regimi di mercato, correlazioni
  stressate.
- Ottimizzatore vincolato, database esterno, autenticazione.
