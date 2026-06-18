# White Paper Metodologico — DPI Wizard

**Strumento di supporto quantitativo al Documento sulla Politica di Investimento**

Fondo Pensione Mario Negri · Versione 1.0 · 18 giugno 2026

---

> **Avvertenza sui dati e sui parametri.** Tutti i dati numerici di questo documento
> (asset class, rendimenti attesi, volatilità, correlazioni, comparti) sono **dati
> dimostrativi** etichettati come tali nell'applicazione. Le scelte metodologiche
> contrassegnate come provvisorie — in particolare la definizione operativa di shortfall
> (DEC-001) e i livelli di confidenza di VaR ed Expected Shortfall (DEC-002) — sono
> **valori tecnici configurabili** e **devono essere validati dalla Funzione Gestione dei
> Rischi e dagli organi competenti del Fondo** prima di qualsiasi utilizzo formale nel
> Documento sulla Politica di Investimento (DPI). Lo strumento supporta il processo
> decisionale; non lo sostituisce.

---

## Indice

1. Executive summary
2. Contesto previdenziale
3. Architettura della soluzione
4. Capital Market Assumptions
5. Rendimento di portafoglio
6. Rendimento reale
7. Rischio di portafoglio
8. Contributi al rischio
9. Simulazione Monte Carlo
10. Percorsi multi-periodali
11. Shortfall risk
12. VaR ed Expected Shortfall
13. Drawdown
14. Stress test
15. Ottimizzazione dell'AAS
16. Vincoli
17. Frontiera efficiente
18. Infeasibilità e diagnostica
19. Validazione dei dati
20. Testing e validazione
21. Rischio di modello
22. Governance del modello
23. Utilizzo nel processo DPI
24. Esempio numerico completo
25. Manuale di lettura degli output
26. Glossario
27. Appendici

---

## 1. Executive summary

DPI Wizard è un'applicazione web sviluppata in Python (Streamlit) che fornisce supporto
quantitativo alla definizione, alla verifica e alla revisione dell'Asset Allocation
Strategica (AAS) dei comparti del Fondo, nel quadro del Documento sulla Politica di
Investimento.

**Obiettivo.** Mettere a disposizione delle funzioni del Fondo uno strumento che, a
partire da un insieme di Capital Market Assumptions (CMA) e dalla struttura dei comparti,
calcoli le metriche di rendimento e rischio di un'allocazione, ne simuli l'evoluzione
prospettica, ne misuri il rischio di shortfall e di coda, ne valuti la tenuta sotto
scenari di stress e proponga allocazioni ottimizzate sotto vincoli configurabili.

**Perimetro.** Lo strumento copre: metriche deterministiche (rendimento, volatilità,
contributi al rischio); validazione delle matrici di correlazione; simulazione Monte Carlo
con distribuzione normale e t di Student multivariata; evoluzione multi-periodo dei
montanti; misure di rischio (VaR, Expected Shortfall, probabilità ed entità dello
shortfall, drawdown); stress test deterministici; ottimizzazione vincolata dell'AAS con
frontiera efficiente e diagnostica di infeasibilità.

**Principali algoritmi.** Venticinque algoritmi registrati e testati (registro ALG-01…
ALG-25), dalla covarianza di portafoglio alla t multivariata, dagli stress test
obbligazionari via duration all'ottimizzazione SLSQP vincolata.

**Modalità di utilizzo.** L'utente lavora attraverso pagine tematiche, configura i
parametri (sempre modificabili), esegue i calcoli e ne esporta i risultati. Tutte le
formule risiedono in moduli di calcolo testati; le pagine si occupano solo di interfaccia.

**Stato di validazione.** La base di codice è coperta da 114 test automatici, tutti
superati. Le validazioni numeriche indipendenti confermano la correttezza dei motori (ad
esempio la minima varianza riproduce la soluzione analitica nota; la t multivariata
riproduce la covarianza target). Il dettaglio è nel rapporto di validazione
(VALIDATION_REPORT.md).

**Limiti.** I risultati dipendono dalle CMA in ingresso (rischio di stima); la normale
sottostima le code; l'ottimizzazione media-varianza è sensibile agli input; gli stress
test sono deterministici e dipendono dagli scenari scelti. Questi limiti sono trattati
nella sezione 21. I dati dimostrativi e i parametri provvisori vanno validati prima
dell'uso reale.

---

## 2. Contesto previdenziale

**Ruolo dell'Asset Allocation Strategica.** Per un fondo pensione l'AAS è la principale
leva di rischio-rendimento di lungo periodo. Definisce la ripartizione tra le grandi
classi di attivo e quindi, in larga misura, il profilo di rischio e il rendimento atteso
dei comparti. La sua definizione e revisione è un atto di governance che il DPI deve
motivare e documentare.

**Bisogni previdenziali e orizzonti.** L'investitore previdenziale ha orizzonti lunghi e
flussi prevedibili (contributi in accumulo, prestazioni in erogazione). A differenza di un
portafoglio retail orientato al breve termine, ciò che conta non è la volatilità di un
singolo anno ma il **potere d'acquisto del montante** alla fine dell'orizzonte e la
probabilità di mancare l'obiettivo previdenziale. Per questo lo strumento ragiona in
termini reali (al netto dell'inflazione), su orizzonti pluriennali, e misura lo shortfall
rispetto a un obiettivo, non solo la dispersione.

**Liquidità e illiquidità.** Gli investimenti illiquidi (private markets, real assets)
possono offrire premi attesi più elevati ma comportano vincoli di liquidabilità e
incertezza di valorizzazione. Lo strumento tratta esplicitamente la quota illiquida come
grandezza vincolabile e ne mostra l'effetto sotto stress.

**Relazione con il DPI e con le funzioni di controllo.** Lo strumento produce evidenze
quantitative (metriche, simulazioni, stress, proposte ottimizzate) che alimentano il
processo di redazione e revisione del DPI. Le decisioni restano in capo agli organi del
Fondo; la Funzione Gestione dei Rischi valida i parametri e interpreta gli output. Lo
strumento rende il processo più tracciabile e ripetibile, non automatico.

---

## 3. Architettura della soluzione

**Architettura funzionale.** L'applicazione è organizzata in pagine tematiche che
accompagnano il flusso di lavoro: definizione dei comparti, inserimento delle CMA,
gestione della matrice di correlazione, laboratorio di asset allocation, simulazioni,
confronto tra proposte, controllo dei vincoli, reportistica, simulazione CMA con stress
test, ottimizzazione dell'AAS.

**Architettura tecnica.** Il principio inviolabile è la **separazione tra motori
quantitativi e interfaccia**: nessuna formula finanziaria rilevante è implementata nelle
pagine Streamlit. Le pagine si occupano di input, validazione dell'input utente, chiamata
ai servizi, visualizzazione, salvataggio ed esportazione. I calcoli risiedono in moduli
dedicati:

- `src/domain/` — modelli di dominio (Pydantic): asset class, CMA, comparto, proposta,
  configurazioni.
- `src/calculations/` — metriche deterministiche e metriche di rischio.
- `src/data/` — validazione (PSD, nearest correlation), dati demo, import/export Excel.
- `src/simulations/` — distribuzioni, Monte Carlo, motore dei percorsi.
- `src/stress_testing/` — scenari, motore di stress, shock obbligazionari.
- `src/optimization/` — funzioni obiettivo, vincoli, solver, frontiera, diagnostica.
- `src/services/` — facade che orchestrano i motori per le pagine (portfolio,
  simulation, optimization).
- `src/reporting/` — generazione del report Excel.

**Modello dati.** I dati sono validati alla costruzione tramite Pydantic: i pesi delle
proposte sommano a uno entro tolleranza, le matrici di correlazione sono simmetriche con
diagonale unitaria e valori in [-1, 1], le asset class hanno parametri coerenti. La
coerenza tra una proposta e il set CMA (stesse asset class) è verificata prima di ogni
calcolo.

**Gestione degli scenari e stato.** Lo stato condiviso tra le pagine
(`pages/_state.py`) mantiene CMA, comparto e proposte della sessione. Gli scenari di
stress sono definiti come oggetti modificabili e versionabili.

**Import/export, logging, versionamento.** Le CMA si importano ed esportano in Excel; i
risultati si esportano in report Excel. Il versionamento del codice avviene su Git con
tag per le versioni stabili (DEC-010). La tracciabilità delle elaborazioni è descritta in
appendice.

**Compatibilità di deployment.** Lo stack è interamente PyData standard (numpy, scipy,
pandas, plotly, openpyxl, pydantic, streamlit); non vi sono dipendenze native aggiuntive
né solver esterni. L'applicazione è verificata su Streamlit Community Cloud (Python 3.12).

---

## 4. Capital Market Assumptions

**Definizione e finalità.** Le Capital Market Assumptions sono le ipotesi prospettiche
sul comportamento delle asset class: rendimento atteso, volatilità, correlazioni, costi,
oltre a inflazione e orizzonte. Costituiscono l'input primario di tutte le elaborazioni:
le metriche, le simulazioni e l'ottimizzazione sono **condizionate** alle CMA.

**Componenti.**

- *Rendimento atteso* (μ): rendimento medio annuo atteso, in termini nominali, per ciascuna
  asset class.
- *Volatilità* (σ): deviazione standard annua dei rendimenti.
- *Correlazione* (C): matrice delle correlazioni tra asset class, simmetrica, con
  diagonale unitaria.
- *Covarianza* (Σ): ottenuta da volatilità e correlazioni (sezione 7).
- *Costi*: TER annuo per asset class, sottratto al rendimento.
- *Inflazione* (π): deterministica, editabile, usata per il passaggio al reale.
- *Orizzonte*: durata della proiezione, coerente con il comparto.

**Fonti e versionamento.** Nello strumento le CMA sono fornite come dati dimostrativi
etichettati e modificabili; nell'uso reale vanno sostituite con le CMA ufficiali del
Fondo, soggette a versionamento e validazione. Le CMA si importano da Excel.

**Rischio di stima e sensitivity.** Le CMA sono stime, non certezze: il rendimento atteso
in particolare è difficile da stimare e ha forte impatto sull'ottimizzazione. È quindi
metodologicamente importante distinguere due fonti di incertezza:

- la **variabilità dei rendimenti futuri** attorno alle CMA (catturata dal Monte Carlo);
- l'**incertezza nella stima delle CMA** stesse (analisi di sensitività, che modifica gli
  input e osserva l'effetto sugli output).

Confondere le due porterebbe a sottostimare il rischio complessivo. L'applicazione tiene
distinte le due nozioni: la simulazione condizionata alle CMA e l'analisi di sensitività
sono concettualmente separate.

**Differenza tra CMA e dati storici.** Le CMA sono ipotesi forward-looking; i dati storici
sono realizzazioni passate. Le CMA possono incorporare giudizi e correzioni rispetto alla
storia (regimi, valutazioni correnti). Lo strumento usa le CMA come input, non stima i
parametri dalla serie storica.

---

## 5. Rendimento di portafoglio

**Formula.**

$$E(R_p) = \mathbf{w}^{\top}\boldsymbol{\mu}$$

dove **w** è il vettore dei pesi (che somma a 1) e **μ** il vettore dei rendimenti attesi
delle asset class.

**Simboli e unità.** I pesi sono adimensionali e sommano a uno; i rendimenti sono decimali
annui. Il risultato è un rendimento atteso decimale annuo.

**Varianti.** Lo strumento distingue:

- *lordo* vs *netto dei costi*: il rendimento netto sottrae il TER, $R_{\text{netto}} =
  \mathbf{w}^{\top}(\boldsymbol{\mu} - \mathbf{c})$;
- *nominale* vs *reale*: il reale deflaziona per l'inflazione (sezione 6);
- *aritmetico* vs *geometrico*: l'aritmetico è la media; il geometrico tiene conto del
  drag di volatilità nel lungo periodo (sezione 9 e 10).

**Implementazione e test.** Funzione `rendimento_atteso` in `calculations/metrics.py`
(ALG-01); rendimento netto costi in `rendimento_netto_costi` (ALG-05). Test in
`tests/test_calculations.py` con valori calcolati indipendentemente a mano.

---

## 6. Rendimento reale

**Formula (Fisher esatta).**

$$R_{\text{reale}} = \frac{1 + R_{\text{nominale}}}{1 + \pi} - 1$$

**Derivazione e interpretazione.** Il rendimento reale misura la crescita del **potere
d'acquisto**. Si ottiene rapportando il montante nominale al livello dei prezzi: un euro
investito diventa $(1+R_{\text{nom}})$ nominale, ma in termini di beni vale
$(1+R_{\text{nom}})/(1+\pi)$.

**Confronto con la sottrazione semplice.** L'approssimazione $R_{\text{reale}} \approx
R_{\text{nom}} - \pi$ è accettabile per valori piccoli ma introduce un errore crescente.
Lo strumento usa la formula esatta (DEC-004). Esempio: con $R_{\text{nom}} = 5{,}38\%$ e
$\pi = 2\%$, la formula esatta dà $2{,}92\%$, la sottrazione $3{,}38\%$: una differenza non
trascurabile su orizzonti lunghi.

**Implementazione e test.** Funzione `rendimento_reale` in `calculations/metrics.py`
(ALG-04), con vincolo $\pi > -1$. Test dedicato in `tests/test_calculations.py`.

---

## 7. Rischio di portafoglio

**Formule.**

$$\sigma_p^2 = \mathbf{w}^{\top}\boldsymbol{\Sigma}\mathbf{w}, \qquad
\sigma_p = \sqrt{\mathbf{w}^{\top}\boldsymbol{\Sigma}\mathbf{w}}$$

**Costruzione della covarianza.** La matrice di covarianza si ottiene da volatilità e
correlazioni:

$$\boldsymbol{\Sigma} = D_{\sigma}\, C\, D_{\sigma}$$

dove $D_{\sigma}$ è la matrice diagonale delle volatilità e $C$ la matrice di correlazione.

**Diversificazione.** Poiché le correlazioni sono in generale inferiori a uno, la
volatilità di portafoglio è inferiore alla media pesata delle volatilità: è l'effetto di
diversificazione. La covarianza ne è la rappresentazione formale.

**Annualizzazione e limiti.** Le grandezze sono annue. La volatilità è una misura
simmetrica: tratta allo stesso modo gli scostamenti positivi e negativi e non cattura la
forma delle code. Per questo lo strumento affianca misure di rischio di coda (VaR, ES) e
di shortfall, e una distribuzione t a code spesse.

**Implementazione e test.** Funzioni `matrice_covarianza` (ALG-03) e `volatilita`
(ALG-02) in `calculations/metrics.py`. Test con matrici note in
`tests/test_calculations.py`.

---

## 8. Contributi al rischio

**Formule.** Il contributo marginale, assoluto e percentuale di ciascuna asset class al
rischio di portafoglio:

$$MCR_i = \frac{(\boldsymbol{\Sigma}\mathbf{w})_i}{\sigma_p}, \qquad
CR_i = w_i\, MCR_i, \qquad
PCR_i = \frac{CR_i}{\sigma_p}$$

**Interpretazione.** Il contributo percentuale $PCR_i$ scompone il rischio totale: la
somma dei $CR_i$ è pari a $\sigma_p$, e la somma dei $PCR_i$ è 1. Permette di vedere quali
asset class concentrano il rischio, informazione spesso più utile del solo peso: una
classe con peso modesto ma alta volatilità e correlazione può contribuire al rischio molto
più di quanto il suo peso suggerisca.

**Uso previdenziale.** Nei comparti azionari il contributo al rischio è dominato dalle
componenti equity anche quando il loro peso non è maggioritario; renderlo esplicito aiuta
a motivare le scelte di de-risking nel DPI.

**Implementazione e test.** Funzione `risk_contribution` in `calculations/metrics.py`
(ALG-06). Test in `tests/test_calculations.py` che verificano l'identità di scomposizione
(somma dei contributi = volatilità di portafoglio).

---

## 9. Simulazione Monte Carlo

La simulazione genera molti scenari di rendimento futuri coerenti con le CMA, per stimare
la distribuzione dei risultati di portafoglio. Sono implementate due distribuzioni.

**Normale multivariata.**

$$\mathbf{r} = \boldsymbol{\mu} + L\mathbf{z}, \qquad LL^{\top} = \boldsymbol{\Sigma},
\qquad \mathbf{z} \sim \mathcal{N}(\mathbf{0}, I)$$

La fattorizzazione $L$ si ottiene per decomposizione di Cholesky; in caso di matrice non
fattorizzabile per arrotondamenti si ricorre alla radice simmetrica via decomposizione
spettrale con floor sugli autovalori (robustezza numerica del campionamento, non
correzione silenziosa dei dati: la validazione della matrice avviene a monte).

**t di Student multivariata.** Per rappresentare code più spesse della normale:

$$\mathbf{r} = \boldsymbol{\mu} + \frac{\mathbf{z}}{\sqrt{g/\nu}}, \qquad
\mathbf{z} \sim \mathcal{N}(\mathbf{0}, S), \qquad g \sim \chi^2_{\nu}$$

con **parametrizzazione esplicita** della matrice di scala affinché la covarianza dei
rendimenti sia esattamente Σ. Poiché per una t multivariata $\operatorname{Cov}(\mathbf{r})
= \frac{\nu}{\nu-2} S$, si impone:

$$S = \frac{\nu - 2}{\nu}\,\boldsymbol{\Sigma}$$

così che $\operatorname{Cov}(\mathbf{r}) = \boldsymbol{\Sigma}$ per $\nu > 2$. I gradi di
libertà ν sono configurabili (default tecnico 5, vincolo $\nu > 2$ per avere varianza
finita). Questa distinzione tra matrice di scala e covarianza è essenziale: senza la
correzione, la t produrrebbe una covarianza gonfiata di un fattore $\nu/(\nu-2)$.

**Parametri configurabili.** Distribuzione, gradi di libertà, orizzonte, frequenza, numero
di simulazioni, seed, inflazione, ribilanciamento, livello di confidenza.

**Riproducibilità ed errore Monte Carlo.** Le simulazioni sono riproducibili: a parità di
seed producono risultati identici (verificato da test). L'errore Monte Carlo decresce con
la radice del numero di simulazioni; i test di convergenza verificano che media e
covarianza campionarie tendano ai valori teorici.

**Implementazione e test.** `simulations/distributions.py`: `campiona_normale` (ALG-10),
`campiona_t_student` (ALG-11), dispatcher `campiona_rendimenti`. Test in
`tests/test_distributions.py`: la covarianza empirica della t converge a Σ (non a S); la
curtosi della t supera quella della normale; riproducibilità del seed.

---

## 10. Percorsi multi-periodali

**Capitalizzazione.** Il montante a fine orizzonte lungo un percorso è il prodotto dei
rendimenti periodali:

$$V_T = V_0 \prod_{t=1}^{T}(1 + R_{p,t})$$

**Flussi opzionali.** In presenza di contributi $C_t$ e uscite $W_t$:

$$V_t = (V_{t-1} + C_t - W_t)(1 + R_{p,t})$$

**Compounding e drag di volatilità.** La capitalizzazione composta implica che il
rendimento geometrico di lungo periodo sia inferiore a quello aritmetico; la differenza
cresce con la volatilità. Questo è il motivo per cui un comparto a più alta volatilità non
domina automaticamente in termini di montante mediano.

**Sequence-of-returns risk.** L'ordine dei rendimenti conta quando vi sono flussi o
ribilanciamenti: una grave perdita in prossimità del pensionamento ha un impatto sul
montante molto maggiore della stessa perdita lontana dall'orizzonte. È precisamente questo
rischio — non la volatilità media — a giustificare il de-risking life cycle. La simulazione
multi-periodo con percorsi completi (non solo il rendimento terminale) consente di
osservarlo, attraverso il drawdown lungo il percorso.

**Frequenza e ribilanciamento.** Sono supportate frequenza annuale e mensile e due regimi:
ribilanciamento periodico ai pesi target, oppure buy-and-hold (i pesi driftano col valore
relativo degli asset). I rendimenti attesi annui si convertono alla frequenza in modo
geometrico, $(1+\mu)^{1/p}-1$; la covarianza si scala linearmente nel tempo, $\Sigma/p$.

**Implementazione e test.** `simulations/path_engine.py`: `evolvi_percorsi` (ALG-12),
con drawdown lungo i percorsi (ALG-13). Test in `tests/test_path_engine.py`: montante
composto su rendimento costante, differenza ribilanciamento vs buy-and-hold, drawdown su
serie nota, effetto dei contributi, conversione di frequenza.

---

## 11. Shortfall risk

Lo shortfall previdenziale misura il rischio di mancare un obiettivo. Si distinguono due
grandezze.

**Probabilità di shortfall:**

$$P(R_T < R^{*})$$

**Entità media dello shortfall (deficit medio condizionato):**

$$E\left[R^{*} - R_T \mid R_T < R^{*}\right]$$

La prima dice **quanto spesso** si manca l'obiettivo; la seconda **di quanto** in media
quando lo si manca. Sono complementari: due allocazioni possono avere la stessa
probabilità di shortfall ma entità molto diverse.

**Definizione operativa della soglia (DEC-001, provvisoria).** La soglia $R^{*}$ dipende
dalla definizione di shortfall adottata, che è **configurabile**. Le definizioni
disponibili comprendono: rendimento reale negativo; rendimento reale sotto l'obiettivo del
comparto; rendimento nominale negativo; rendimento sotto l'inflazione; montante sotto una
soglia. Il valore tecnico iniziale è lo shortfall rispetto all'obiettivo del comparto.
**Questa scelta è provvisoria e va validata** dalla Funzione Gestione dei Rischi e dagli
organi del Fondo.

**Uso previdenziale.** Per un fondo pensione la probabilità di non preservare il potere
d'acquisto (rendimento reale negativo) o di non raggiungere l'obiettivo è più informativa
della sola volatilità: parla la lingua degli obiettivi del comparto.

**Implementazione e test.** `calculations/risk_metrics.py`: `prob_shortfall` e
`shortfall_medio_condizionato` (ALG-16). La selezione della soglia secondo la definizione
attiva avviene nel servizio `simulation_service.py`. Test in `tests/test_simulations.py`.

---

## 12. VaR ed Expected Shortfall

**Definizione di VaR.** Il Value at Risk a livello di confidenza α è il quantile della
distribuzione di perdita:

$$VaR_{\alpha}(L) = \inf\{l : P(L \le l) \ge \alpha\}$$

**Expected Shortfall.** L'ES (o CVaR) è la **perdita media oltre il VaR**: la media delle
perdite nei casi peggiori, quelli che eccedono il VaR al livello α. A differenza del VaR,
l'ES informa sulla gravità della coda, non solo sulla sua soglia.

**Convenzioni adottate.** Nello strumento la perdita è definita come $1 - \text{montante
reale}$ a fine orizzonte (perdita positiva = riduzione del potere d'acquisto). Il livello
di confidenza è configurabile: valore tecnico 95% (default), 99% alternativo (DEC-002,
**provvisorio, da validare**).

**Differenza rispetto allo shortfall previdenziale.** VaR ed ES sono misure di **rischio di
mercato** sulla distribuzione di perdita; lo shortfall previdenziale (sezione 11) misura il
rischio rispetto a un **obiettivo**. Sono concetti distinti e lo strumento usa
denominazioni diverse per non confonderli.

**Limiti.** Il VaR non è subadditivo e ignora la forma della coda oltre la soglia; l'ES la
cattura ma resta sensibile al modello distributivo. La differenza tra normale e t è
istruttiva: a parità di scenari l'ES sotto la t è sistematicamente più alto (vedi sezione
24), segnale che la normale sottostima la coda.

**Implementazione e test.** `calculations/risk_metrics.py`: `var_perdita` (ALG-14),
`expected_shortfall_mercato` (ALG-15). Test in `tests/test_simulations.py`.

---

## 13. Drawdown

**Formule.** Il drawdown a ogni istante misura la caduta dal massimo precedente; il massimo
drawdown è il più severo lungo il percorso:

$$DD_t = \frac{V_t - \max_{s \le t} V_s}{\max_{s \le t} V_s}, \qquad
MDD = \min_t DD_t$$

**Interpretazione e uso.** Il drawdown cattura la perdita peggiore vissuta lungo il
percorso, non solo il risultato finale. È particolarmente rilevante in ottica
previdenziale per il sequence-of-returns risk: un drawdown profondo in prossimità
dell'orizzonte è difficilmente recuperabile. Lo strumento riporta il massimo drawdown
mediano sugli scenari simulati.

**Implementazione e test.** `calculations/risk_metrics.py` (`drawdown_da_serie`,
`max_drawdown_da_serie`) e `path_engine.py` (drawdown lungo i percorsi simulati), ALG-13.
Test in `tests/test_path_engine.py` su serie con drawdown noto.

---

## 14. Stress test

Gli stress test sono **scenari deterministici** di shock applicati al portafoglio. Non
sono probabilità: rappresentano l'impatto istantaneo di un dato scenario. Sono implementati
in un motore separato dal Monte Carlo (DEC-013).

**Shock obbligazionari (duration/convexity).** Per le asset class con duration, uno shock
di tasso si traduce in variazione di prezzo:

$$\frac{\Delta P}{P} \approx -D_{\text{mod}}\,\Delta y + \frac{1}{2}\,C\,(\Delta y)^2$$

In assenza di convexity si usa la sola duration, $\frac{\Delta P}{P} \approx
-D_{\text{mod}}\,\Delta y$, segnalando l'approssimazione.

**Tipologie di scenario implementate.** Shock azionari (ribassi percentuali diretti); shock
di tasso (rialzi/ribassi paralleli tradotti via duration); shock sugli illiquidi
(svalutazioni di real assets e private markets); scenario combinato (azioni in calo, tassi
e spread in aumento, illiquidi in calo). Gli scenari demo sono etichettati e modificabili.

**Aggregazione e output.** La perdita di portafoglio è la somma pesata degli shock per
asset class; lo strumento riporta perdita complessiva, nuovo valore, contributo alla
perdita per asset class ed effetto sulle quote di liquidità e illiquidità (i pesi relativi
cambiano dopo lo shock).

**Limiti.** Gli stress test dipendono dagli scenari scelti e non hanno associata una
probabilità; gli shock di tasso richiedono la duration tra i dati. Vanno letti come
"what-if" di robustezza, complementari al Monte Carlo.

**Implementazione e test.** `stress_testing/fixed_income_shocks.py` (`shock_tasso`,
ALG-17), `stress_engine.py` (`applica_stress`, ALG-18; `effetto_su_quote`),
`scenarios.py`. Test in `tests/test_stress.py`: perdita azionaria attesa, shock di tasso
via duration, somma dei contributi pari alla perdita, effetto sulle quote.

---

## 15. Ottimizzazione dell'AAS

Il motore propone allocazioni ottimali sotto vincoli. Sono implementate tre funzioni
obiettivo dirette, più il minimo rischio a rendimento target ottenibile via vincolo.

**Minima varianza.**
$$\min_{\mathbf{w}} \ \mathbf{w}^{\top}\boldsymbol{\Sigma}\mathbf{w}$$

**Massimo rendimento (con vincoli di rischio/allocazione).**
$$\max_{\mathbf{w}} \ \mathbf{w}^{\top}\boldsymbol{\mu}$$

**Massimo Sharpe ratio.**
$$\max_{\mathbf{w}} \ \frac{\mathbf{w}^{\top}\boldsymbol{\mu} - r_f}
{\sqrt{\mathbf{w}^{\top}\boldsymbol{\Sigma}\mathbf{w}}}$$

con risk free $r_f$ configurabile (default 0).

**Minimo rischio a rendimento target.** Si ottiene minimizzando la varianza con il vincolo
$\mathbf{w}^{\top}\boldsymbol{\mu} \ge R_{\text{target}}$ (sezione 16). È il meccanismo che
genera la frontiera efficiente (sezione 17).

**Solver.** `scipy.optimize.minimize` con metodo SLSQP (DEC-015): gestisce vincoli non
lineari (volatilità massima, Sharpe), è già nello stack scipy e compatibile con il
deployment, senza solver esterni. Tolleranza e numero massimo di iterazioni configurabili.
Punto iniziale: l'AAS vigente se disponibile, altrimenti equipesato.

**Arrotondamento.** I pesi possono essere arrotondati (0,1% / 0,5% / 1%) per evitare falsa
precisione, con **ri-verifica dei vincoli** dopo l'arrotondamento.

**Funzione prevista, non implementata.** La minimizzazione della probabilità di shortfall
come obiettivo (obiettivo non lineare che richiederebbe Monte Carlo nel ciclo di
ottimizzazione) **non è implementata** nel perimetro attuale, per ragioni di stabilità e
costo computazionale; è prevista come estensione (DEC-017). Documentarla come disponibile
sarebbe scorretto.

**Implementazione e test.** `optimization/objectives.py` (ALG-19/20/21),
`optimizer.py` (`ottimizza`). Validazione: la minima varianza riproduce la soluzione
analitica $\mathbf{w} = \Sigma^{-1}\mathbf{1}/(\mathbf{1}^{\top}\Sigma^{-1}\mathbf{1})$
entro tolleranza stretta. Test in `tests/test_optimization.py`.

---

## 16. Vincoli

Tutti i vincoli sono configurabili e passati al solver nel formato richiesto da SLSQP.

**Pieno investimento.** $\sum_i w_i = 1$

**Limiti individuali (e divieto di posizioni corte).** $l_i \le w_i \le u_i$, con $w_i \ge
0$ come caso particolare.

**Vincoli di gruppo.** $L_g \le \sum_{i \in g} w_i \le U_g$

**Liquidità minima.** $\sum_{i \in \mathcal{L}} w_i \ge L_{\min}$

**Illiquidità massima.** $\sum_{i \in \mathcal{I}} w_i \le I_{\max}$

**Rendimento minimo.** $\mathbf{w}^{\top}\boldsymbol{\mu} \ge R_{\min}$

**Volatilità massima.** $\sqrt{\mathbf{w}^{\top}\boldsymbol{\Sigma}\mathbf{w}} \le
\sigma_{\max}$

**Duration.** $D_{\min} \le \sum_i w_i D_i \le D_{\max}$

**Esposizione valutaria.** $FX_{\min} \le \sum_i w_i FX_i \le FX_{\max}$

**Turnover rispetto alla AAS vigente.** $\sum_i |w_i - w_i^0| \le T_{\max}$

Quest'ultimo vincolo, basato sul valore assoluto, non è differenziabile e crea difficoltà
ai solver a gradiente. È implementato tramite **riformulazione a variabili ausiliarie**
(DEC-016): si introducono $u_i \ge |w_i - w_i^0|$ (due vincoli lineari per asset) e $\sum_i
u_i \le T_{\max}$, rendendo il problema liscio. È l'approccio standard per i vincoli L1.

**Implementazione e test.** `optimization/constraints.py` (`costruisci_vincoli`, ALG-22),
riformulazione turnover in `optimizer.py` (`_ottimizza_con_turnover`, ALG-23). Test per
ciascun vincolo in `tests/test_optimization.py`.

---

## 17. Frontiera efficiente

**Metodo di generazione.** La frontiera si costruisce minimizzando la varianza a rendimenti
target crescenti, dal minimo al massimo rendimento atteso delle asset class. Ogni punto è
un'ottimizzazione vincolata; i target non fattibili sotto i vincoli sono semplicemente
esclusi.

**Informazioni per punto.** Per ciascun punto efficiente lo strumento espone rendimento,
volatilità, pesi, e — nel contesto della pagina — il confronto con la AAS vigente. Il punto
ottimizzato selezionato è evidenziato sulla curva.

**Interpretazione.** La frontiera mostra il miglior rendimento atteso per ogni livello di
rischio sotto i vincoli correnti. La presenza di vincoli (liquidità, illiquidità, bande)
sposta e accorcia la frontiera rispetto al caso non vincolato: è corretto che alcuni target
risultino irraggiungibili.

**Implementazione e test.** `optimization/efficient_frontier.py`
(`frontiera_efficiente`, ALG-24). Test in `tests/test_optimization.py`: monotonìa della
volatilità rispetto al rendimento sui punti efficienti.

---

## 18. Infeasibilità e diagnostica

**Principio.** Quando i vincoli sono incompatibili, lo strumento **non restituisce pesi
apparentemente validi**: segnala il fallimento e ne diagnostica le cause (DEC, sezione
5.7 del piano).

**Comportamento del solver.** Se SLSQP non converge a una soluzione fattibile, il risultato
è marcato come non riuscito, con messaggio. Nessun peso viene proposto in questo caso.

**Diagnostica.** La funzione di diagnostica risolve prima il problema con i soli vincoli di
base (budget e bounds): se già questo fallisce, il problema è strutturalmente infeasible
(ad esempio i bounds non permettono pesi che sommino a uno). Altrimenti aggiunge i vincoli
uno alla volta e identifica quelli che, isolatamente, rendono il problema infeasible. Se
ogni vincolo è singolarmente fattibile, segnala che l'infeasibilità nasce dalla loro
combinazione e suggerisce di allentare i più stringenti.

**Implementazione e test.** `optimization/efficient_frontier.py`
(`diagnostica_infeasibilita`, ALG-25). Test in `tests/test_optimization.py`: un rendimento
minimo superiore al massimo μ è correttamente diagnosticato come infeasible e non produce
pesi.

---

## 19. Validazione dei dati

Lo strumento valida gli input e **non corregge silenziosamente** dati invalidi.

- *Pesi*: devono sommare a uno entro tolleranza (1e-6); verificato alla costruzione della
  proposta.
- *Matrici di correlazione*: simmetria, diagonale unitaria, valori in $[-1, 1]$,
  semi-definitezza positiva. La PSD è verificata tramite l'autovalore minimo con tolleranza
  (DEC-011).
- *Nearest correlation (Higham)*: se una matrice non è PSD, lo strumento può **proporre**
  la matrice valida più vicina, ma non la applica mai in automatico (DEC-006): la scelta
  resta all'utente.
- *Rendimenti*: non inferiori a -100% (un rendimento $\le -1$ azzererebbe il capitale).
- *Coerenza di unità e frequenza*: tutti gli input nella stessa unità (decimali annui); le
  conversioni di frequenza sono esplicite.
- *Valori mancanti e coerenza proposta/CMA*: la proposta deve riferirsi alle stesse asset
  class del set CMA.

**Implementazione e test.** `data/validation.py` (`valida_psd` ALG-08,
`nearest_correlation_higham` ALG-09); validazioni Pydantic in `domain/models.py`. Test in
`tests/test_data.py` e `tests/test_domain.py`.

---

## 20. Testing e validazione

**Strategia.** Ogni algoritmo ha test con valori calcolati indipendentemente (a mano o per
via analitica), oltre a test di convergenza, riproducibilità e casi limite. Le pagine sono
coperte da smoke test che ne verificano il caricamento senza eccezioni. Un test
architetturale verifica che nessuna formula quantitativa compaia nelle pagine.

**Esiti.** Suite di **114 test, tutti superati**. Distribuzione: dominio (19), calcoli
(18), dati (10), simulazioni (12), distribuzioni (7), percorsi (6), stress (8),
ottimizzazione (14), reporting (3), pagine (2), integrazione (5).

**Validazioni indipendenti principali.** Minima varianza = soluzione analitica; covarianza
della t = Σ; perdita di stress = somma pesata degli shock; drawdown su serie nota; coerenza
tra montante deterministico geometrico e mediana simulata.

**Casi limite gestiti.** Matrice non fattorizzabile (fallback spettrale); montante non
positivo nel rendimento geometrico (floor positivo, scenario classificato come shortfall);
turnover non differenziabile (riformulazione a variabili ausiliarie); infeasibilità
(nessun peso fittizio).

**Tolleranze.** Confronti analitici 1e-4…1e-6; convergenza Monte Carlo 2e-3…5e-3 su
0,5–1 M campioni; SLSQP ftol 1e-9. Dettaglio in `VALIDATION_REPORT.md`.

---

## 21. Rischio di modello

Lo strumento è un modello, e come ogni modello ha limiti che è doveroso esplicitare.

- *Rischio di stima e dipendenza dalle CMA*: gli output sono condizionati alle CMA; errori
  nelle stime, soprattutto dei rendimenti attesi, si propagano. L'ottimizzazione
  media-varianza è notoriamente sensibile a μ.
- *Instabilità delle correlazioni e rischio di regime*: le correlazioni non sono stabili e
  tendono ad aumentare nelle crisi; un singolo set di CMA non cattura i cambi di regime.
- *Non-normalità*: la normale sottostima le code. La t mitiga ma resta un modello
  parametrico simmetrico.
- *Rischio di liquidità e valorizzazione degli illiquidi*: i private markets hanno
  valorizzazioni ritardate e lisciate; la loro volatilità "vera" è verosimilmente
  sottostimata dalle CMA.
- *Falsa precisione e instabilità dell'ottimizzazione*: piccole variazioni negli input
  possono spostare molto i pesi ottimi; l'arrotondamento e i vincoli mitigano, non
  eliminano.
- *Dipendenza dai vincoli*: i risultati riflettono i vincoli imposti; vincoli mal calibrati
  producono soluzioni mal calibrate.
- *Rischio di interpretazione*: gli output sono supporti decisionali, non prescrizioni.
- *Rischio operativo*: dati demo da sostituire, parametri provvisori da validare.

Le mitigazioni adottate (vincoli, t a code spesse, stress test, frontiera, diagnostica di
infeasibilità, arrotondamento, separazione calcolo/decisione) riducono questi rischi ma non
li annullano.

---

## 22. Governance del modello

**Responsabilità e uso.** Lo strumento è un supporto tecnico; le decisioni di asset
allocation competono agli organi del Fondo. La Funzione Gestione dei Rischi valida i
parametri (in particolare DEC-001 e DEC-002), interpreta gli output e ne presidia i limiti.

**Approvazione e versionamento.** Il codice è versionato su Git con tag per le versioni
stabili (DEC-010). Le decisioni metodologiche sono registrate in `DECISIONS.md`; gli
algoritmi in `ALGORITHM_REGISTER.md`; la validazione in `VALIDATION_REPORT.md`.

**Revisione periodica e gestione delle modifiche.** CMA, parametri e scenari vanno rivisti
periodicamente. Ogni modifica metodologica dovrebbe passare per il registro delle decisioni
e per i test.

**Separazione tra calcolo e decisione.** L'architettura separa i motori di calcolo
dall'interfaccia e, concettualmente, il calcolo dalla decisione: lo strumento fornisce
evidenze, gli organi decidono.

---

## 23. Utilizzo nel processo DPI

Lo strumento supporta il processo del DPI in più punti:

- *Definizione degli obiettivi*: traduce gli obiettivi di comparto in metriche verificabili
  (rendimento reale atteso, probabilità di shortfall).
- *Verifica della AAS*: calcola metriche e simula l'AAS vigente, evidenziando contributi al
  rischio e tenuta sotto stress.
- *Confronto tra proposte*: mette a confronto allocazioni alternative su rendimento,
  rischio, shortfall, turnover.
- *Analisi di shortfall e stress*: quantifica il rischio di mancare l'obiettivo e l'impatto
  di scenari avversi.
- *Motivazione delle modifiche e allegati tecnici*: produce evidenze esportabili a supporto
  della documentazione.
- *Tracciabilità*: rende le elaborazioni ripetibili (seed, parametri, versione del codice).

Lo strumento **supporta** il processo; **non sostituisce** le decisioni degli organi, la
validazione normativa né il giudizio professionale.

---

## 24. Esempio numerico completo

Esempio interamente riproducibile con i dati demo e seed fissato (seed 42, 10.000
simulazioni, orizzonte 15 anni, inflazione 2%). I valori provengono dall'esecuzione del
codice definitivo.

**Asset class (demo).**

| Asset class | μ (nom.) | σ | costo | illiquida |
|---|---|---|---|---|
| Liquidità | 2,0% | 1,0% | 0,10% | no |
| Govt EUR | 3,0% | 5,0% | 0,15% | no |
| Corporate | 4,0% | 7,0% | 0,25% | no |
| Equity DM | 7,0% | 16,0% | 0,30% | no |
| Equity EM | 8,5% | 22,0% | 0,50% | no |
| Real assets | 5,5% | 12,0% | 0,60% | no |
| Private markets | 9,0% | 18,0% | 1,50% | sì |

**AAS vigente (demo):** Liquidità 5%, Govt EUR 30%, Corporate 15%, Equity DM 25%,
Equity EM 10%, Real assets 5%, Private markets 10%.

**Metriche deterministiche (orizzonte 15 anni, inflazione 2%).**

| Metrica | Valore |
|---|---|
| Rendimento nominale atteso | 5,38% |
| Rendimento reale | 2,92% |
| Rendimento reale geometrico | 2,58% |
| Volatilità | 8,34% |
| Montante reale atteso | 1,4645 |
| Quota illiquida | 10,0% |

**Simulazione (seed 42, 10.000 scenari, 15 anni).**

| Distribuzione | P(shortfall) | VaR (95%) | Expected Shortfall | Max DD mediano | Mediana montante reale |
|---|---|---|---|---|---|
| Normale | 10,85% | 12,31% | 22,95% | -10,98% | 1,4689 |
| t di Student (ν=5) | 10,46% | 12,55% | 25,69% | -9,90% | 1,4713 |

Due osservazioni metodologiche. Primo: la **mediana del montante reale simulato** (1,4689
normale; 1,4713 t) coincide quasi esattamente con il **montante deterministico geometrico**
(1,4645), conferma della coerenza interna tra il calcolo deterministico e la simulazione.
Secondo: a parità di probabilità di shortfall simili, l'**Expected Shortfall sotto la t è
più alto** (25,69% contro 22,95%): è la coda, non il centro della distribuzione, a
cambiare. È la dimostrazione quantitativa del fatto che la normale sottostima il rischio di
eventi estremi — il rischio che più conta in ottica previdenziale.

**Stress test (scenario combinato).** Perdita complessiva -14,72%; nuovo valore 0,8528;
quota illiquida post-shock 9,38% (scende perché gli illiquidi sono colpiti più del resto).

**Ottimizzazione (vincoli del comparto demo, confronto con AAS vigente).**

| Obiettivo | Rendimento | Volatilità | Turnover vs vigente |
|---|---|---|---|
| Minima varianza | 2,98% | 3,44% | 1,08 |
| Massimo rendimento | 7,35% | 14,91% | 0,90 |
| Massimo Sharpe | 3,46% | 3,71% | 0,82 |

Il portafoglio a minima varianza riduce drasticamente la volatilità (dal 8,34% al 3,44%)
ma con un turnover elevato rispetto alla vigente: un esempio del trade-off che il DPI deve
valutare, non un'indicazione operativa.

> I numeri sopra derivano da **dati dimostrativi** e da **parametri provvisori**. Servono a
> illustrare il funzionamento dello strumento, non a orientare scelte reali.

---

## 25. Manuale di lettura degli output

- *Rendimenti*: salvo diversa indicazione, i risultati di simulazione sono in termini
  **reali** (potere d'acquisto) e **geometrici** su orizzonte pluriennale; le metriche
  deterministiche distinguono nominale e reale.
- *Probabilità di shortfall*: dipende dalla **definizione** di shortfall selezionata
  (provvisoria); va letta insieme all'entità media, non da sola.
- *VaR ed Expected Shortfall*: misure di rischio di mercato sulla perdita, al livello di
  confidenza scelto; non vanno confuse con lo shortfall previdenziale.
- *Stress test*: scenari "what-if" deterministici, **non probabilità**.
- *Ottimizzazione*: i pesi proposti riflettono obiettivo e vincoli impostati; vanno
  confrontati con la AAS vigente e valutati per turnover e robustezza, evitando di
  interpretare cifre decimali come precise.
- *Errori interpretativi da evitare*: leggere la volatilità come unica misura di rischio;
  trattare le CMA come certezze; considerare l'output dell'ottimizzatore come una
  prescrizione; ignorare il rischio di coda perché "la media va bene".

---

## 26. Glossario

- **AAS** — Asset Allocation Strategica: ripartizione di lungo periodo tra classi di
  attivo.
- **CMA** — Capital Market Assumptions: ipotesi prospettiche su rendimenti, volatilità,
  correlazioni.
- **Covarianza** — misura congiunta di variabilità di due asset; in forma matriciale Σ.
- **Correlazione** — covarianza normalizzata, in $[-1, 1]$.
- **VaR** — Value at Risk: quantile della perdita a un livello di confidenza.
- **Expected Shortfall** — perdita media oltre il VaR (rischio di coda).
- **Shortfall previdenziale** — rischio di mancare un obiettivo (probabilità ed entità).
- **Drawdown** — caduta dal massimo precedente lungo un percorso.
- **Duration** — sensibilità del prezzo obbligazionario al tasso.
- **Convexity** — correzione del secondo ordine alla duration.
- **Frontiera efficiente** — migliori combinazioni rischio-rendimento sotto i vincoli.
- **Infeasibilità** — assenza di soluzioni che soddisfino tutti i vincoli.
- **Turnover** — entità della modifica rispetto alla AAS vigente, $\sum_i|w_i-w_i^0|$.
- **Liquidità / Illiquidità** — quota investita in asset facilmente / difficilmente
  liquidabili.
- **Seed** — inizializzazione del generatore casuale, garante della riproducibilità.
- **Percentile** — valore sotto cui cade una data percentuale degli scenari.
- **Ribilanciamento** — riporto periodico dei pesi ai valori target.

---

## 27. Appendici

**A. Notazione.** **w** pesi; **μ** rendimenti attesi; Σ covarianza; $C$ correlazioni;
$D_\sigma$ diagonale delle volatilità; π inflazione; $L$ fattore di Cholesky; ν gradi di
libertà; $r_f$ risk free; $w^0$ AAS vigente.

**B. Mapping formula–funzione–test.** Il collegamento completo tra requisiti, formule,
moduli, funzioni, parametri, test e documentazione è nella **matrice di tracciabilità**
(`TRACEABILITY_MATRIX.md`). Il registro degli algoritmi (`ALGORITHM_REGISTER.md`) elenca i
25 algoritmi ALG-01…ALG-25 con formula, modulo, funzione, test e stato di validazione.

**C. Stato delle metodologie.**

- *Implementate e validate*: metriche deterministiche; validazione PSD/Higham; Monte Carlo
  normale e t multivariata; percorsi multi-periodo; VaR, ES, shortfall, drawdown; stress
  test (azionario, tassi, illiquidi, combinato); ottimizzazione (minima varianza, massimo
  rendimento, massimo Sharpe, minimo rischio a target); vincoli; frontiera; diagnostica.
- *Previste, non implementate*: shortfall optimization come obiettivo (DEC-017); shock di
  credito/spread espliciti e ribilanciamento infrannuale a bande (previsti
  nell'architettura).
- *Escluse dal perimetro*: solver esterni (cvxpy); autenticazione; persistenza su
  database; stima delle CMA da serie storiche.

**D. Configurazioni demo.** Sette asset class etichettate [DEMO], un comparto demo, una
matrice di correlazione demo. Da sostituire con i dati ufficiali validati.

**E. Parametri configurabili.** Distribuzione, gradi di libertà, orizzonte, frequenza,
numero di simulazioni, seed, inflazione, ribilanciamento, livello di confidenza VaR/ES,
definizione di shortfall, shock di stress, obiettivo, vincoli (bounds, gruppi, liquidità,
illiquidità, rendimento, volatilità, duration, valuta, turnover), tolleranze del solver.

**F. Riferimenti documentali.** `PROJECT_STATE.md`, `DECISIONS.md`,
`TRACEABILITY_MATRIX.md`, `ALGORITHM_REGISTER.md`, `VALIDATION_REPORT.md`,
`NOTE_METODOLOGICHE.md`, `MANUALE_UTENTE.md`, `MANUALE_METODOLOGICO.md`, `GLOSSARIO.md`,
`CHANGELOG.md`.

---

*Documento generato come sintesi metodologica del progetto DPI Wizard. Le metodologie qui
descritte corrispondono al codice definitivo e ai relativi test. In caso di difformità tra
questo documento e il codice, fa fede il comportamento del codice e la difformità va
segnalata e corretta.*
