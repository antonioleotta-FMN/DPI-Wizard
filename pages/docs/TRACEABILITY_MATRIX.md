# Matrice di tracciabilità — DPI Wizard

Collega ogni requisito funzionale alla pagina, al modulo, alla funzione, alla formula,
ai parametri configurabili, ai test e alla documentazione. Fonte per il white paper (M9).

Legenda colonne: Requisito · Pagina · Modulo · Funzione · Formula/ALG · Parametri · Test · Doc.

## Metriche deterministiche (M1)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Rendimento atteso | 05 Lab | calculations/metrics.py | rendimento_atteso | ALG-01 | pesi, mu | test_calculations | MANUALE_METODOLOGICO |
| Volatilità | 05 Lab | calculations/metrics.py | volatilita | ALG-02 | pesi, cov | test_calculations | MANUALE_METODOLOGICO |
| Covarianza | 04 Correlazioni | calculations/metrics.py | matrice_covarianza | ALG-03 | sigma, corr | test_calculations | MANUALE_METODOLOGICO |
| Rendimento reale | 05 Lab | calculations/metrics.py | rendimento_reale | ALG-04 | inflazione | test_calculations | DEC-004 |
| Contributi al rischio | 08 Controlli | calculations/metrics.py | risk_contribution | ALG-06 | pesi, cov | test_calculations | MANUALE_METODOLOGICO |
| Proiezione geometrica | 05 Lab | calculations/metrics.py | rendimento_geometrico, montante_atteso | ALG-07 | sigma, orizzonte | test_calculations | DEC-003 |

## Data layer (M2)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Validazione PSD | 04 Correlazioni | data/validation.py | valida_psd | ALG-08 | toll | test_data | DEC-006, DEC-011 |
| Nearest correlation | 04 Correlazioni | data/validation.py | nearest_correlation_higham | ALG-09 | — | test_data | DEC-006 |
| Import/Export CMA | 03 Assunzioni | data/excel_io.py | importa/esporta_cma_excel | — | file | test_data | MANUALE_UTENTE |
| Dati demo etichettati | tutte | data/demo.py | cma_demo, comparto_demo | — | — | test_domain | DEC-005 |

## Monte Carlo e simulazione (M3, M6)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| MC normale | 06 Simulazioni, 10 | simulations/montecarlo.py, distributions.py | simula_montecarlo, campiona_normale | ALG-10 | n_sim, seed, orizzonte | test_simulations, test_distributions | NOTE_METODOLOGICHE |
| t di Student MV | 10 Sim CMA | simulations/distributions.py | campiona_t_student | ALG-11 | df, n_sim, seed | test_distributions | DEC-012 |
| Percorsi multi-periodo | 10 Sim CMA | simulations/path_engine.py | evolvi_percorsi | ALG-12 | freq, ribilanciamento, flussi | test_path_engine | DEC-014 |
| Conversione frequenza | 10 Sim CMA | simulations/path_engine.py | converti_rendimento/covarianza_*_a_periodo | — | periodi_per_anno | test_path_engine | NOTE_METODOLOGICHE |
| Bande percentili (fan) | 10 Sim CMA | calculations/risk_metrics.py | bande_percentili | — | punti | test_integration | — |

## Metriche di rischio (M6)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| VaR | 10 Sim CMA | calculations/risk_metrics.py | var_perdita | ALG-14 | confidenza | test_simulations | DEC-002 |
| Expected Shortfall | 10 Sim CMA | calculations/risk_metrics.py | expected_shortfall_mercato | ALG-15 | confidenza | test_simulations | DEC-002 |
| Prob. shortfall | 06, 10 | calculations/risk_metrics.py | prob_shortfall | — | soglia, definizione | test_simulations | DEC-001 |
| Shortfall medio cond. | 10 Sim CMA | calculations/risk_metrics.py | shortfall_medio_condizionato | ALG-16 | soglia | test_simulations | DEC-001 |
| Drawdown / Max DD | 10 Sim CMA | calculations/risk_metrics.py, path_engine.py | drawdown_da_serie | ALG-13 | — | test_path_engine | NOTE_METODOLOGICHE |

## Stress test (M6)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Shock di tasso | 10 Sim CMA | stress_testing/fixed_income_shocks.py | shock_tasso | ALG-17 | duration, delta_y, convexity | test_stress | DEC-013 |
| Stress deterministico | 10 Sim CMA | stress_testing/stress_engine.py | applica_stress | ALG-18 | scenario, shock | test_stress | DEC-013 |
| Effetto su quote | 10 Sim CMA | stress_testing/stress_engine.py | effetto_su_quote | — | — | test_stress | DEC-013 |
| Scenari demo | 10 Sim CMA | stress_testing/scenarios.py | scenari_demo | — | shock modificabili | test_stress | DEC-013 |

## Ottimizzazione (M7)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Minima varianza | 11 Ottim. | optimization/optimizer.py, objectives.py | ottimizza | ALG-19 | — | test_optimization | DEC-015 |
| Massimo rendimento | 11 Ottim. | optimization/optimizer.py | ottimizza | ALG-20 | vincoli | test_optimization | DEC-015 |
| Massimo Sharpe | 11 Ottim. | optimization/optimizer.py | ottimizza | ALG-21 | rf | test_optimization | DEC-015 |
| Vincoli configurabili | 11 Ottim. | optimization/constraints.py | costruisci_vincoli | ALG-22 | bounds, gruppi, liquidità, illiquidità, rendimento, volatilità, duration, fx | test_optimization | — |
| Turnover | 11 Ottim. | optimization/optimizer.py | _ottimizza_con_turnover | ALG-23 | turnover_max, pesi_correnti | test_optimization | DEC-016 |
| Frontiera efficiente | 11 Ottim. | optimization/efficient_frontier.py | frontiera_efficiente | ALG-24 | n_punti | test_optimization | — |
| Diagnostica infeasib. | 11 Ottim. | optimization/efficient_frontier.py | diagnostica_infeasibilita | ALG-25 | — | test_optimization | NOTE_METODOLOGICHE |

## Vincoli a semaforo (M3)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Verifica vincoli | 08 Controlli | constraints/engine.py | verifica_vincoli | — | limiti comparto | test_simulations | MANUALE_UTENTE |

## Reporting (M4)

| Requisito | Pagina | Modulo | Funzione | ALG | Parametri | Test | Doc |
|-----------|--------|--------|----------|-----|-----------|------|-----|
| Report Excel | 09 Report | reporting/excel_report.py | genera_report_excel | — | proposta, metriche | test_reporting | MANUALE_UTENTE |

## Controlli architetturali (M8)

| Requisito | Verifica | Test |
|-----------|----------|------|
| Nessuna formula nelle pagine | scansione pattern numerici nelle pagine | test_integration::test_nessuna_formula_nelle_pagine |
| Riproducibilità simulazioni | stesso seed → stesso risultato | test_integration::test_simulazione_riproducibile |
| Flusso end-to-end | CMA→metriche→sim→stress→ottimizzazione | test_integration::test_flusso_completo |
| Deploy | import moduli + caricamento app | verifica manuale M8 (VALIDATION_REPORT) |
