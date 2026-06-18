# Registro degli algoritmi — DPI Wizard

Registro delle metodologie implementate, fonte per il white paper (M9). Aggiornato a
fine di ogni milestone tecnica. Stato: "validato" (test indipendenti superati),
"sperimentale" (implementato, validazione parziale), "previsto" (non implementato).

| ID | Nome | Finalita | Modulo | Funzione | Test | Stato |
|----|------|----------|--------|----------|------|-------|
| ALG-01 | Rendimento atteso | w'mu | calculations/metrics.py | rendimento_atteso | test_calculations | validato |
| ALG-02 | Volatilita | sqrt(w'Sigma w) | calculations/metrics.py | volatilita | test_calculations | validato |
| ALG-03 | Covarianza | D C D | calculations/metrics.py | matrice_covarianza | test_calculations | validato |
| ALG-04 | Rendimento reale (Fisher) | (1+r)/(1+pi)-1 | calculations/metrics.py | rendimento_reale | test_calculations | validato |
| ALG-05 | Rendimento netto costi | w'(mu-c) | calculations/metrics.py | rendimento_netto_costi | test_calculations | validato |
| ALG-06 | Risk contribution | MCTR/CCTR/PCTR | calculations/metrics.py | risk_contribution | test_calculations | validato |
| ALG-07 | Rendimento geometrico | mu - sigma^2/2 | calculations/metrics.py | rendimento_geometrico | test_calculations | validato |
| ALG-08 | Validazione PSD | autovalore minimo | data/validation.py | valida_psd | test_data | validato |
| ALG-09 | Nearest correlation (Higham) | proiezioni alternate | data/validation.py | nearest_correlation_higham | test_data | validato |
| ALG-10 | Monte Carlo normale | r=mu+Lz | simulations/montecarlo.py, distributions.py | simula_montecarlo, campiona_normale | test_simulations, test_distributions | validato |
| ALG-11 | t di Student multivariata | S=(df-2)/df Sigma | simulations/distributions.py | campiona_t_student | test_distributions | validato |
| ALG-12 | Percorsi multi-periodo | V_T=V0 prod(1+R) | simulations/path_engine.py | evolvi_percorsi | test_path_engine | validato |
| ALG-13 | Drawdown / max drawdown | (V-max)/max | calculations/risk_metrics.py | drawdown_da_serie | test_path_engine | validato |
| ALG-14 | VaR | percentile perdita | calculations/risk_metrics.py | var_perdita | test_simulations | validato |
| ALG-15 | Expected Shortfall (mercato) | media oltre VaR | calculations/risk_metrics.py | expected_shortfall_mercato | test_simulations | validato |
| ALG-16 | Shortfall medio condizionato | E[soglia-X\|X<soglia] | calculations/risk_metrics.py | shortfall_medio_condizionato | test_simulations | validato |
| ALG-17 | Stress shock tasso | -D dy + 0.5 C dy^2 | stress_testing/fixed_income_shocks.py | shock_tasso | test_stress | validato |
| ALG-18 | Stress deterministico | shock pesati | stress_testing/stress_engine.py | applica_stress | test_stress | validato |
| ALG-19 | Ottimizzazione min varianza | min w'Sigma w | optimization/optimizer.py + objectives.py | ottimizza | test_optimization | validato |
| ALG-20 | Ottimizzazione max rendimento | max w'mu | optimization/optimizer.py | ottimizza | test_optimization | validato |
| ALG-21 | Ottimizzazione max Sharpe | max (w'mu-rf)/sigma | optimization/optimizer.py | ottimizza | test_optimization | validato |
| ALG-22 | Vincoli ottimizzazione | budget, bounds, gruppi, liquidita, illiquidita, rendimento, volatilita, duration, fx, turnover | optimization/constraints.py | costruisci_vincoli | test_optimization | validato |
| ALG-23 | Turnover riformulato | u>=\|w-w0\|, sum u<=T | optimization/optimizer.py | _ottimizza_con_turnover | test_optimization | validato |
| ALG-24 | Frontiera efficiente | min varianza a target | optimization/efficient_frontier.py | frontiera_efficiente | test_optimization | validato |
| ALG-25 | Diagnostica infeasibilita | test vincoli isolati | optimization/efficient_frontier.py | diagnostica_infeasibilita | test_optimization | validato |

## Note
- ALG-21 (max Sharpe) usa risk free rf configurabile (default 0).
- ALG-23: il vincolo di turnover L1 e' riformulato con variabili ausiliarie per
  compatibilita' con SLSQP (il modulo gradiente non gestisce bene il valore assoluto).
- Shortfall optimization (minima probabilita di shortfall) NON implementata nell'MVP
  post: prevista, richiede Monte Carlo nel loop di ottimizzazione (costo computazionale
  e stabilita' da valutare). Stato: previsto.
