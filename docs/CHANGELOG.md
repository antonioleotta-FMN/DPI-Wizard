# Changelog — DPI Wizard

Tutte le modifiche rilevanti, per milestone. Le versioni stabili sono marcate con tag
Git (DEC-010).

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
