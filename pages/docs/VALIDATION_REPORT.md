# Rapporto di validazione — DPI Wizard (M8)

Data: 2026-06-18 · Milestone: M8 (integrazione, validazione, rilascio)

## 1. Perimetro validato

Sono validate le funzionalità delle milestone M0–M7:
- metriche deterministiche di rendimento e rischio (M1);
- data layer: validazione PSD, nearest correlation, import/export CMA (M2);
- Monte Carlo normale + motore vincoli a semaforo (M3);
- interfaccia multipagina e reporting Excel (M4–M5);
- simulazione CMA avanzata (normale e t multivariata), percorsi multi-periodo,
  metriche di rischio (VaR, ES, shortfall, drawdown), stress test deterministici (M6);
- ottimizzazione vincolata dell'AAS (minima varianza, massimo rendimento, massimo
  Sharpe), vincoli configurabili, frontiera efficiente, diagnostica infeasibilità (M7).

Funzionalità prevista NON implementata (dichiarata): shortfall optimization (minima
probabilità di shortfall come obiettivo) — vedi DEC-017.

## 2. Ambiente

- Python 3.12.3 (runtime.txt: python-3.12).
- numpy 2.4.4, scipy 1.17.1, pandas 3.0.2, streamlit 1.58.0, plotly, pydantic 2.13.4,
  openpyxl. Pin a fasce in requirements.txt, compatibili con Streamlit Community Cloud.
- Nessuna dipendenza esterna al di fuori dello stack PyData standard (niente cvxpy né
  solver esterni): deployment senza compilazioni native aggiuntive.

## 3. Test eseguiti

Suite automatica: **114 test, tutti superati** (tempo ~3,6 s).

Distribuzione per area:
- test_domain (19): modelli Pydantic, vincoli, coerenza proposta/CMA.
- test_calculations (18): metriche deterministiche, valori calcolati a mano.
- test_data (10): PSD, Higham, IO Excel.
- test_simulations (12): Monte Carlo, convergenza, riproducibilità, VaR/ES.
- test_distributions (7): normale e t multivariata, covarianza target, code spesse.
- test_path_engine (6): compounding, drawdown, flussi, conversione frequenza.
- test_stress (8): shock tasso, perdita attesa, contributi, quote.
- test_optimization (14): obiettivi, vincoli, infeasibilità, turnover, frontiera.
- test_reporting (3): report Excel.
- test_pages (2): smoke test caricamento pagine.
- test_integration (5): flusso end-to-end, riproducibilità, controllo architetturale.

## 4. Validazioni numeriche indipendenti

- **Minima varianza** riproduce la soluzione analitica w = Σ⁻¹1 / (1ᵀΣ⁻¹1) entro 1e-4.
- **t di Student multivariata**: covarianza empirica converge alla covarianza target Σ
  (non alla matrice di scala), curtosi superiore alla normale.
- **Stress azionario**: perdita = somma pesata degli shock, verificata a mano.
- **Shock di tasso**: dP/P = −D·Δy (e −D·Δy + ½C·Δy² con convexity), verificata a mano.
- **Drawdown**: serie nota [1.0, 1.2, 0.9] → max DD = −25%, esatto.
- **Coerenza MVP**: la mediana del montante reale simulato resta in linea con la
  proiezione deterministica geometrica.

## 5. Tolleranze

- Confronti analitici: atol 1e-4..1e-6.
- Convergenza Monte Carlo (media/covarianza campionaria): atol 2e-3..5e-3 a 0,5–1 M
  campioni; rtol 5% sulla covarianza della t (stima più rumorosa per code spesse).
- Solver SLSQP: ftol 1e-9, maxiter 500.

## 6. Performance (indicative, ambiente di sviluppo)

- Simulazione 25.000 scenari × 20 anni × frequenza mensile (t di Student): ~7,5 s.
  È il limite superiore d'uso; per esperienza interattiva fluida si consigliano
  10.000 scenari e frequenza annuale.
- Frontiera efficiente (20 punti, ciascuno un'ottimizzazione): ~1 s.

## 7. Controlli finali (sezione 6.6 del piano)

| Controllo | Esito |
|-----------|-------|
| Formule rilevanti fuori dalle pagine Streamlit | OK (test automatico; corretto un caso di np.percentile nel fan chart, spostato in calculations) |
| Tutti gli algoritmi hanno test | OK (registro ALG-01..ALG-25, tutti con test) |
| Simulazioni riproducibili (seed) | OK (test_integration) |
| Input validati | OK (PSD non corretta silenziosamente; coerenza proposta/CMA) |
| Output con unità e frequenza | OK (etichette nei grafici e nelle metriche) |
| Solver non nasconde errori | OK (infeasibilità segnalata, nessun peso fittizio) |
| Matrici non corrette silenziosamente | OK (DEC-006: Higham proposto, mai applicato in automatico) |
| Nessun dato riservato | OK (solo dati demo etichettati; nessun nome/IBAN/importo reale) |
| Deploy funzionante | OK (import completi, app.py carica senza eccezioni) |

## 8. Anomalie rilevate e risolte in M8

1. **Formula nella pagina 10**: il fan chart calcolava i percentili con np.percentile
   nella pagina. Spostato in calculations/risk_metrics.py (bande_percentili), esposto
   via service. Principio "nessuna formula nelle pagine" ora rispettato e blindato da
   test automatico.
2. **Montante non positivo**: percorsi con perdita cumulata ≥ 100% generavano
   RuntimeWarning nel rendimento geometrico (potenza di base negativa). Aggiunto un
   floor positivo prima del calcolo; gli scenari restano classificati come shortfall.

## 9. Problemi aperti e assunzioni provvisorie

- **DEC-001** (definizione di shortfall) e **DEC-002** (confidenza VaR/ES): valori
  tecnici provvisori e configurabili, **da validare dalla Funzione Gestione dei Rischi
  e dagli organi del Fondo** prima dell'uso istituzionale. Avvertenza presente in app.
- **Shortfall optimization**: prevista, non implementata (DEC-017).
- I dati CMA, le matrici e i comparti sono **demo**: vanno sostituiti con i dati
  ufficiali validati prima di qualsiasi uso nel DPI reale.

## 10. Esito complessivo

La suite è interamente verde (114/114), i controlli architetturali e di deployment sono
superati, le validazioni numeriche indipendenti confermano la correttezza dei motori. Il
sistema è **idoneo a procedere alla documentazione metodologica finale (M9)**, fermo
restando che i parametri provvisori e i dati demo devono essere validati e sostituiti
prima dell'utilizzo formale nel Documento sulla Politica di Investimento.
