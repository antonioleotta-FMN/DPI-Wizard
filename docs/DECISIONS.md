# Registro delle decisioni

Formato per ogni voce: ID, data, stato, decisione, motivazione, alternative, impatto,
file interessati. Le decisioni approvate non si modificano retroattivamente: se
superate, si registra una nuova decisione che sostituisce la precedente.

---

## DEC-001 — Definizione di shortfall
Data: 2026-06-17
Stato: approvata (tecnica) / da validare dagli organi del Fondo per uso reale
Decisione: definizione di default = rendimento reale negativo (perdita di potere
d'acquisto a fine orizzonte). La definizione è PARAMETRIZZABILE: l'utente può
selezionare tra reale<0, reale<obiettivo, nominale<0, nominale<inflazione,
montante<soglia.
Motivazione: coerente con l'ottica previdenziale (protezione del potere d'acquisto);
l'utente ha richiesto esplicitamente la modificabilità.
Alternative considerate: soglia fissa montante<obiettivo (proposta iniziale, scartata
come default ma mantenuta come opzione).
Impatto: introduce ConfigShortfall nel dominio; la metrica P(shortfall) legge la
definizione attiva dalla configurazione.
File interessati: src/domain/models.py, src/calculations (M1), src/simulations.

## DEC-002 — Livello di confidenza e orizzonte VaR/ES
Data: 2026-06-17
Stato: approvata (tecnica) / da validare dagli organi del Fondo per uso reale
Decisione: VaR ed Expected Shortfall di mercato a confidenza 95%, orizzonte 1 anno.
Lo shortfall previdenziale usa invece l'orizzonte del comparto.
Motivazione: prassi comune; separa rischio di mercato annuale da rischio previdenziale
di lungo periodo.
Alternative considerate: 99%.
Impatto: parametri di default in ConfigSimulazione.
File interessati: src/domain/models.py, src/simulations.

## DEC-003 — Convenzione di rendimento su orizzonti pluriennali
Data: 2026-06-17
Stato: approvata
Decisione: rendimento geometrico per proiezioni pluriennali del montante.
Motivazione: corretto per la capitalizzazione composta del montante.
Alternative considerate: aritmetico.
Impatto: calcoli di proiezione e Monte Carlo.
File interessati: src/calculations, src/simulations.

## DEC-004 — Inflazione
Data: 2026-06-17
Stato: approvata
Decisione: inflazione deterministica nell'MVP, valore modificabile nelle ipotesi.
Motivazione: semplicità e trasparenza nell'MVP; inflazione stocastica rimandata.
Alternative considerate: inflazione stocastica.
Impatto: campo editabile in ConfigSimulazione/Comparto.
File interessati: src/domain/models.py, src/simulations.

## DEC-005 — Asset class del dataset demo
Data: 2026-06-17
Stato: approvata
Decisione: 7 macro-classi demo (Liquidità, Govt EUR, Corporate, Equity DM, Equity EM,
Real assets, Private markets), modificabili dall'utente (aggiunta/rimozione/rinomina).
Motivazione: copertura rappresentativa di un fondo previdenziale; flessibilità
richiesta dall'utente.
Alternative considerate: set fisso.
Impatto: il CMASet è una collezione dinamica di AssetClass.
File interessati: src/domain/models.py, src/data/demo (M2).

## DEC-006 — Correzione matrice di correlazione non-PSD
Data: 2026-06-17
Stato: approvata
Decisione: in caso di matrice non semi-definita positiva, proporre la nearest
correlation matrix (algoritmo di Higham). Mai applicata silenziosamente: solo
suggerita, da confermare manualmente.
Motivazione: requisito di precisione del prompt (nessuna modifica silenziosa).
Alternative considerate: clipping autovalori (meno corretto).
Impatto: validazione matrice produce esito + proposta; l'utente conferma.
File interessati: src/data (M2), src/domain/models.py.

## DEC-007 — Modello dei costi
Data: 2026-06-17
Stato: approvata
Decisione: costi come TER annuo costante per asset class.
Motivazione: sufficiente per l'MVP.
Alternative considerate: costi per orizzonte/turnover.
Impatto: campo costo in AssetClass; rendimento netto = nominale - somma pesata costi.
File interessati: src/domain/models.py, src/calculations.

## DEC-008 — Ribilanciamento
Data: 2026-06-17
Stato: approvata
Decisione: ribilanciamento annuale fisso nell'MVP. Buy & hold rimandato.
Motivazione: semplicità; coerente con orizzonti annuali.
Alternative considerate: buy & hold.
Impatto: logica Monte Carlo.
File interessati: src/simulations.

## DEC-009 — Lingua
Data: 2026-06-17
Stato: approvata
Decisione: interfaccia e report in italiano nell'MVP.
Motivazione: ambiente di lavoro italiano.
Alternative considerate: multilingua.
Impatto: etichette UI e reportistica.
File interessati: config, pages, src/reporting.

## DEC-011 — Tolleranza numerica PSD e floor autovalori
Data: 2026-06-17
Stato: approvata (tecnica)
Decisione: la verifica di semi-definitezza positiva usa tolleranza 1e-8 sull'autovalore
minimo; l'algoritmo di Higham applica un floor di 1e-8 sugli autovalori in proiezione.
Motivazione: una matrice corretta che cade sul bordo del cono PSD puo' presentare un
autovalore minimo marginalmente negativo (~ -1e-9) per puro arrotondamento della
decomposizione spettrale; tolleranza e floor evitano falsi negativi senza ammettere
matrici realmente non valide.
Alternative considerate: tolleranza 0/1e-10 (genera falsi negativi numerici).
Impatto: src/data/validation.py.
File interessati: src/data/validation.py, tests/test_data.py.

## DEC-010 — Workflow GitHub
Data: 2026-06-17
Stato: approvata
Decisione: branch unico main con commit diretti e tag per le versioni stabili.
Motivazione: profilo utente non-sviluppatore; semplicità.
Alternative considerate: main/develop + branch funzionali.
Impatto: procedura di rilascio (M finale).
File interessati: README.md, docs.

## DEC-001 (aggiornamento M6) — Definizione di shortfall: provvisoria e configurabile
Data: 2026-06-18
Stato: provvisoria, configurabile, NON ufficiale
Aggiornamento: il valore predefinito di shortfall e' configurabile dall'utente. Valore
tecnico iniziale adottato per lo sviluppo post-MVP: shortfall rispetto all'obiettivo
del comparto (oltre alle altre definizioni gia' selezionabili). Il default resta
modificabile a livello di comparto. Questi valori NON rappresentano decisioni ufficiali
e devono essere validati dalla Funzione Gestione dei Rischi e dagli organi competenti
del Fondo prima dell'utilizzo istituzionale nel DPI. Non impediscono lo sviluppo tecnico.

## DEC-002 (aggiornamento M6) — Confidenza VaR/ES: provvisoria e configurabile
Data: 2026-06-18
Stato: provvisoria, configurabile, NON ufficiale
Aggiornamento: livello di confidenza di VaR ed Expected Shortfall configurabile.
Valori tecnici iniziali: 95% (default), 99% (alternativo selezionabile). Provvisori, da
validare internamente prima dell'uso istituzionale. Non bloccano lo sviluppo.

## DEC-012 — Distribuzione t di Student multivariata (M6)
Data: 2026-06-18
Stato: approvata (tecnica)
Decisione: oltre alla normale multivariata, e' disponibile una t di Student
multivariata con gradi di liberta' configurabili (default tecnico 5, vincolo df > 2).
Parametrizzazione esplicita: matrice di scala S = (df-2)/df * Sigma, cosi' che la
covarianza dei rendimenti sia Sigma. Motivazione: la normale sottostima le code; la t
rende esplicito il rischio di coda (sequence-of-returns risk). Test: la covarianza
empirica converge a Sigma; curtosi superiore alla normale.
File interessati: src/simulations/distributions.py, tests/test_distributions.py.

## DEC-013 — Stress test deterministici separati dal Monte Carlo (M6)
Data: 2026-06-18
Stato: approvata (tecnica)
Decisione: gli stress test sono deterministici e NON producono probabilita; motore
separato (src/stress_testing). Scenari demo etichettati e modificabili. Shock
obbligazionari via duration (+ convexity se disponibile), con segnalazione
dell'approssimazione. Motivazione: requisito esplicito del piano M6.
File interessati: src/stress_testing/*, tests/test_stress.py.

## DEC-014 — Frequenza e ribilanciamento configurabili (M6)
Data: 2026-06-18
Stato: approvata (tecnica)
Decisione: il path engine supporta frequenza annuale/mensile e ribilanciamento ai pesi
target o buy & hold, con flussi opzionali (contributi/uscite). Conversione dei
rendimenti attesi (geometrica) e della covarianza (lineare nel tempo) alla frequenza.
File interessati: src/simulations/path_engine.py, tests/test_path_engine.py.

## DEC-015 — Solver di ottimizzazione: scipy SLSQP (M7)
Data: 2026-06-18
Stato: approvata (tecnica)
Decisione: l'ottimizzazione vincolata usa scipy.optimize.minimize con metodo SLSQP, non
cvxpy. Motivazione: SLSQP gestisce vincoli non lineari (volatilita massima, Sharpe), e'
gia' tra le dipendenze (scipy), compatibile con Streamlit Cloud senza solver esterni.
Tolleranza (ftol) e numero massimo di iterazioni configurabili. Validazione: la minima
varianza coincide con la soluzione analitica w=Sigma^-1 1/(1'Sigma^-1 1).
File: src/optimization/optimizer.py, tests/test_optimization.py.

## DEC-016 — Turnover riformulato a variabili ausiliarie (M7)
Data: 2026-06-18
Stato: approvata (tecnica)
Decisione: il vincolo di turnover sum|w-w0|<=T_max e' implementato riformulando il
valore assoluto con variabili ausiliarie u_i>=|w_i-w0_i| e sum u_i<=T_max, perche' la
forma diretta (L1, non liscia) non converge con SLSQP. La riformulazione e' lineare e
robusta. File: src/optimization/optimizer.py (_ottimizza_con_turnover).

## DEC-017 — Shortfall optimization: prevista, non implementata (M7)
Data: 2026-06-18
Stato: prevista (non implementata)
Decisione: la minimizzazione della probabilita di shortfall (obiettivo non lineare che
richiede Monte Carlo o approssimazione parametrica nel loop di ottimizzazione) NON e'
implementata nel perimetro M7, per ragioni di stabilita e costo computazionale. L'
architettura la prevede come estensione futura. Documentata come "prevista" nel registro
algoritmi. Sono implementati tre obiettivi (minima varianza, massimo rendimento, massimo
Sharpe) piu' il minimo rischio con rendimento target ottenibile via vincolo
rendimento_min; il criterio M7 (>=4 obiettivi operativi) e' soddisfatto.
