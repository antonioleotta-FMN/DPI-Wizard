# Note metodologiche provvisorie (M6-M8)

Documento di lavoro per la futura redazione del white paper (M9). Raccoglie formule,
funzioni Python, parametri, algoritmi, test e limiti delle funzionalita' post-MVP, man
mano che vengono implementate. NON e' il white paper: e' la fonte di evidenze.

## M6 — Simulazione CMA e stress test

### Distribuzioni (src/simulations/distributions.py)

Normale multivariata: r = mu + L z, con L L^T = Sigma (Cholesky; fallback spettrale con
floor sugli autovalori per stabilita'). Funzione: campiona_normale. Test:
test_normale_media_e_covarianza.

t di Student multivariata: r = mu + z / sqrt(g/df), z ~ N(0, S), g ~ chi2(df), con
S = (df-2)/df * Sigma. Per df > 2 la covarianza dei rendimenti e' Sigma. Funzione:
campiona_t_student. Parametro: df (default tecnico 5, vincolo df > 2). Test:
test_t_student_riproduce_covarianza_target, test_t_student_code_piu_spesse_della_normale.
Limite: df <= 2 non ammesso (varianza infinita).

### Percorsi multi-periodo (src/simulations/path_engine.py)

Montante composto: V_T = V_0 * prod_t (1 + R_{p,t}). Con flussi:
V_t = (V_{t-1} + C_t - W_t) * (1 + R_{p,t}). Frequenza annuale/mensile; ribilanciamento
ai pesi target oppure buy & hold (pesi che driftano). Conversione rendimenti annua->
periodo: (1+mu)^(1/p) - 1; covarianza annua->periodo: /p. Funzione: evolvi_percorsi.
Test: test_montante_composto_senza_costi, test_drawdown_su_serie_nota,
test_flussi_contributi_aumentano_montante, test_conversione_frequenza.

### Metriche di rischio (src/calculations/risk_metrics.py)

Percentili; VaR = percentile alpha della perdita; ES di mercato = media della perdita
oltre il VaR; P(shortfall) = P(X < soglia); shortfall medio condizionato =
E[soglia - X | X < soglia] (concetto distinto dall'ES di mercato); drawdown
DD_t = (V_t - max_{s<=t} V_s)/max_{s<=t} V_s; max drawdown = min_t DD_t.

### Stress test (src/stress_testing/)

Deterministici, separati dal Monte Carlo, non probabilistici. Scenario = insieme di
shock per asset class (match per sottostringa del nome). Shock diretto sul prezzo, o
shock di tasso tradotto via duration: dP/P ~= -D_mod * dy (+ 0.5 * C * dy^2 se
convexity disponibile; altrimenti sola duration, segnalata). Perdita di portafoglio =
somma pesata degli shock; contributi per asset class; effetto sulle quote di liquidita/
illiquidita dopo il riscalamento dei pesi. Funzioni: applica_stress, shock_tasso,
effetto_su_quote. Test: test_stress_azionario_perdita_attesa, test_shock_tasso_*,
test_stress_contributi_sommano_a_perdita.

### Parametri configurabili introdotti
distribuzione, df, orizzonte, frequenza (periodi_per_anno), n_simulazioni, seed,
inflazione, ribilanciamento, confidenza VaR/ES, scenari di stress (shock modificabili).

### Limiti dichiarati
Normale: code sottili. t: resta un modello parametrico simmetrico. Stress: deterministici,
dipendono dagli shock scelti; gli shock di tasso richiedono duration nei dati.

## M7 — Ottimizzazione vincolata dell'AAS

### Funzioni obiettivo (src/optimization/objectives.py)
Minima varianza: min w'Sigma w. Massimo rendimento: max w'mu (= min -w'mu). Massimo
Sharpe: max (w'mu - rf)/sqrt(w'Sigma w), rf configurabile (default 0). Tutte da
minimizzare (i max restituiscono il negativo). Test: test_min_varianza_vs_analitica
(coincide con w=Sigma^-1 1/(1'Sigma^-1 1)), test_max_rendimento_concentra_su_asset_migliore.

### Vincoli (src/optimization/constraints.py)
Budget (sum w=1, eq), bounds l_i<=w_i<=u_i, gruppi Lg<=sum<=Ug, liquidita minima,
illiquidita massima, rendimento minimo w'mu>=R, volatilita massima sqrt(w'Sigma w)<=S,
duration, esposizione valutaria, turnover sum|w-w0|<=T. Formato scipy SLSQP (dict
type/fun). Test: test_vincolo_rendimento_minimo, test_vincolo_volatilita_massima,
test_vincolo_turnover.

### Solver (src/optimization/optimizer.py)
scipy.optimize.minimize, metodo SLSQP, ftol e maxiter configurabili. Punto iniziale:
AAS vigente se disponibile, altrimenti equipesato. Pulizia numerica e rinormalizzazione.
Arrotondamento pesi (0.1%/0.5%/1%) con ri-verifica bounds.

Turnover: il vincolo L1 sum|w-w0|<=T non e' liscio e SLSQP non converge in forma
diretta. Riformulazione a variabili ausiliarie: u_i>=|w_i-w0_i| (due vincoli lineari per
asset), sum u_i<=T, variabili decisionali [w, u]. Funzione: _ottimizza_con_turnover.
Test: test_vincolo_turnover (ora converge).

### Frontiera e diagnostica (src/optimization/efficient_frontier.py)
Frontiera: minimizza la varianza a rendimenti target crescenti da min(mu) a max(mu); i
punti infeasible sono esclusi. Diagnostica infeasibilita: risolve i soli vincoli base,
poi aggiunge i vincoli uno alla volta per identificare i problematici; se i vincoli sono
singolarmente fattibili segnala che l'infeasibilita' deriva dalla combinazione. Principio:
mai restituire pesi apparentemente validi in caso di fallimento. Test:
test_infeasible_rendimento_irraggiungibile, test_infeasible_non_restituisce_pesi.

### Limiti
Markowitz e' sensibile agli input (mu soprattutto): piccole variazioni nei rendimenti
attesi possono spostare molto i pesi. Mitigazioni: vincoli, bounds, arrotondamento,
confronto con AAS vigente, turnover. Shortfall optimization non implementata (prevista).
