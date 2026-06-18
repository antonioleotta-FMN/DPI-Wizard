# Glossario e data dictionary — DPI Wizard

## Glossario dei termini

**Asset class.** Categoria omogenea di investimenti (es. azionario mercati sviluppati,
obbligazionario governativo) con proprie assunzioni di rendimento e rischio.

**AAS (Asset Allocation Strategica).** Ripartizione target del patrimonio tra asset
class, definita nel DPI.

**CMA (Capital Market Assumptions).** Insieme delle assunzioni di mercato: rendimenti
attesi, volatilita, costi, correlazioni per ciascuna asset class.

**Rendimento nominale.** Rendimento atteso senza tener conto dell'inflazione.

**Rendimento reale.** Rendimento al netto dell'inflazione, indicatore del potere
d'acquisto. Calcolato con la formula di Fisher esatta.

**Rendimento geometrico.** Rendimento medio composto che, applicato per ogni anno,
produce il montante atteso. Inferiore all'aritmetico in presenza di volatilita.

**Volatilita.** Deviazione standard del rendimento, misura di rischio.

**Matrice di correlazione.** Tabella delle correlazioni tra asset class. Deve essere
simmetrica, con diagonale unitaria, valori tra -1 e 1, e semi-definita positiva.

**PSD (semi-definita positiva).** Proprieta' matematica che una matrice di correlazione
deve avere per essere coerente. Se manca, l'app propone una correzione.

**Shortfall.** Evento in cui un obiettivo non viene raggiunto. La definizione e'
configurabile (default: rendimento reale negativo).

**VaR (Value at Risk).** Perdita che non viene superata con una data probabilita' su un
dato orizzonte.

**Expected Shortfall / CVaR.** Perdita media negli scenari peggiori, oltre il VaR.

**Contributo al rischio.** Quota del rischio totale del portafoglio attribuibile a
ciascuna asset class.

**Monte Carlo.** Tecnica che simula molti scenari casuali per stimare la distribuzione
dei risultati possibili.

**TER (Total Expense Ratio).** Costo annuo complessivo di gestione di un'asset class.

**Drag della volatilita.** Riduzione del rendimento composto dovuta alla variabilita':
spiega perche' il rendimento geometrico e' inferiore all'aritmetico.

## Data dictionary (modelli di dominio)

### AssetClass
| Campo | Tipo | Significato |
|-------|------|-------------|
| nome | testo | Nome dell'asset class |
| mu_nominale | decimale | Rendimento nominale atteso annuo |
| mu_reale | decimale/nullo | Rendimento reale atteso (opzionale) |
| sigma | decimale >=0 | Volatilita annua |
| costo | decimale >=0 | TER annuo |
| duration | decimale/nullo | Duration in anni (se applicabile) |
| illiquidita | vero/falso | Asset class illiquida |
| valuta | testo (3) | Valuta di denominazione |
| copertura_valutaria | 0..1 | Quota coperta dal rischio cambio |
| peso_min, peso_max | 0..1 | Bande di peso ammesse |

### Comparto
| Campo | Tipo | Significato |
|-------|------|-------------|
| nome | testo | Nome del comparto |
| patrimonio | decimale >=0 | Patrimonio in EUR |
| orizzonte_anni | intero >=1 | Orizzonte di investimento |
| obiettivo_rendimento | decimale | Obiettivo annuo |
| tipo_obiettivo | nominale/reale | Natura dell'obiettivo |
| liquidita_minima | 0..1 | Quota minima di liquidita |
| quota_max_illiquida | 0..1 | Quota massima illiquida |
| benchmark | testo/nullo | Benchmark strategico |
| shortfall | config | Definizione di shortfall attiva |

### Proposta
| Campo | Tipo | Significato |
|-------|------|-------------|
| nome | testo | Nome della proposta |
| pesi | mappa nome->0..1 | Pesi per asset class, somma 1 |

### ConfigSimulazione
| Campo | Tipo | Significato |
|-------|------|-------------|
| n_simulazioni | intero | Numero di scenari Monte Carlo |
| seed | intero | Seme per la riproducibilita |
| confidenza_var | 0.5..1 | Livello di confidenza VaR/ES |
| orizzonte_var_anni | intero | Orizzonte per VaR/ES di mercato |
| inflazione | decimale | Inflazione annua deterministica |
| ribilanciamento_annuale | vero/falso | Ribilanciamento ai pesi target |
