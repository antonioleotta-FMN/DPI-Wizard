# Manuale metodologico — DPI Wizard

Questo documento descrive le metodologie quantitative implementate in DPI Wizard, le
loro ipotesi e i loro limiti. E' rivolto a chi deve comprendere, validare o
documentare i risultati nel Documento sulla Politica di Investimento.

> Avvertenza. DPI Wizard e' uno strumento di supporto alle decisioni. I risultati sono
> output di modello e non costituiscono testo deliberativo ne valutazione legale.
> Le scelte metodologiche che confluiscono nel DPI (in particolare la definizione di
> shortfall e i livelli di confidenza di VaR/ES) vanno validate dagli organi del Fondo
> e dalla Funzione Gestione dei rischi.

## 1. Convenzioni generali

Tutte le grandezze sono annue e in forma decimale (0.05 = 5%). I pesi di portafoglio
sommano a 1. L'ordinamento di pesi, rendimenti, volatilita e correlazioni e' sempre
quello delle asset class nel set CMA attivo.

## 2. Rendimento atteso

Rendimento atteso aritmetico di portafoglio: media dei rendimenti attesi delle asset
class, pesata per i pesi di portafoglio. E' la base per la maggior parte delle altre
metriche. Su orizzonti pluriennali non si usa direttamente per il montante (vedi 7).

## 3. Volatilita

Deviazione standard del portafoglio, calcolata dalla matrice di covarianza ottenuta
combinando le volatilita delle asset class con la matrice di correlazione. La
covarianza e' costruita come prodotto della matrice diagonale delle volatilita per la
matrice di correlazione per la stessa matrice diagonale.

## 4. Rendimento reale

Calcolato con la formula di Fisher esatta: il rapporto tra uno piu' il rendimento
nominale e uno piu' l'inflazione, meno uno. Non si usa l'approssimazione "rendimento
meno inflazione", che sovrastima leggermente il rendimento reale (DEC-004).

## 5. Rendimento netto costi

Rendimento atteso al netto dei costi: dal rendimento lordo si sottrae la media pesata
dei costi (TER annui) delle asset class (DEC-007). Non sono modellati turnover o costi
di transazione.

## 6. Contributo al rischio

Il rischio totale del portafoglio viene scomposto per asset class in:
- contributo marginale al rischio (di quanto cresce la volatilita per una variazione
  infinitesima del peso);
- contributo assoluto (il marginale moltiplicato per il peso);
- contributo percentuale (la quota del rischio totale attribuibile all'asset class).
I contributi percentuali sommano al 100%. Serve a capire da dove proviene davvero il
rischio, che spesso e' concentrato in poche asset class anche quando i pesi sono
distribuiti.

## 7. Convenzione geometrica per le proiezioni (DEC-003)

Per proiettare il montante su piu' anni non si usa il rendimento aritmetico, che
ignora il "drag" della volatilita, ma il rendimento geometrico atteso, approssimato
come rendimento aritmetico meno meta' della varianza. Il montante atteso e' poi la
capitalizzazione composta del rendimento geometrico reale sull'orizzonte del comparto.
La stima geometrica piu' accurata emerge comunque dalla mediana dei montanti del
Monte Carlo (vedi 8).

## 8. Simulazione Monte Carlo

I rendimenti annui delle asset class sono campionati da una distribuzione normale
multivariata con i rendimenti attesi e la matrice di covarianza del set CMA. Per ogni
scenario il montante si capitalizza anno per anno, con ribilanciamento annuale ai pesi
target (DEC-008), al netto dei costi, e a fine orizzonte si deflaziona per l'inflazione
composta (DEC-004). Il seed rende i risultati riproducibili.

Limite metodologico dichiarato (rischio di modello): la distribuzione normale
sottostima la probabilita di eventi estremi (code sottili). I valori di coda (VaR ed
ES a confidenza elevata) vanno letti con cautela. Le metodologie che attenuano questo
limite (distribuzione t di Student, bootstrap storico, regimi di mercato, correlazioni
stressate) sono previste dall'architettura ma non implementate nell'MVP.

## 9. Probabilita di shortfall (DEC-001)

La probabilita di shortfall e' la frequenza degli scenari in cui si verifica l'evento
di shortfall secondo la definizione attiva, scelta sul comparto. Le definizioni
disponibili sono: rendimento reale negativo (default, perdita di potere d'acquisto);
rendimento reale sotto l'obiettivo; rendimento nominale negativo; rendimento nominale
sotto l'inflazione; montante sotto una soglia assoluta.

## 10. Value at Risk ed Expected Shortfall (DEC-002)

Il Value at Risk e' la perdita corrispondente al percentile della distribuzione di
perdita al livello di confidenza scelto (default 95%) sull'orizzonte di mercato
(default 1 anno). L'Expected Shortfall di mercato (CVaR) e' la perdita media negli
scenari peggiori, oltre il VaR.

Distinto da questo e' l'Expected Shortfall come "mancato raggiungimento dell'obiettivo":
la perdita media di potere d'acquisto negli scenari in cui il montante reale finisce
sotto il capitale iniziale. I due concetti rispondono a domande diverse (rischio di
mercato di breve periodo contro rischio previdenziale di lungo periodo) e sono tenuti
esplicitamente separati, con denominazioni diverse.

## 11. Verifica dei vincoli

La proposta e' confrontata con tre famiglie di vincoli: interni (liquidita minima,
quota massima illiquida), strategici (bande min/max per asset class) e normativi/
strutturali (coerenza dei pesi). Ogni vincolo ha un esito a semaforo: rispettato,
vicino al limite, violato. I limiti normativi puntuali vanno parametrizzati e validati
dalle funzioni competenti: l'app non li cabla come verita' assolute.
