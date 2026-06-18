# Manuale utente — DPI Wizard

Guida pratica all'uso dell'applicazione. Per le metodologie quantitative vedi
MANUALE_METODOLOGICO.md; per il significato dei termini vedi GLOSSARIO.md.

## Avvio

In locale:
```bash
pip install -r requirements.txt
streamlit run app.py
```
Online: l'app e' pubblicata su Streamlit Community Cloud (vedi STREAMLIT_DEPLOY.md).

All'avvio l'app carica un set di dati DEMO, plausibili ma fittizi, segnalati da un
avviso. Servono a esplorare le funzioni; non sono dati ufficiali del Fondo.

## Le pagine

**Home.** Riepilogo della sessione: set CMA attivo, comparto, numero di proposte
salvate. Da qui si naviga alle altre pagine dal menu laterale.

**Comparti.** Si configura il comparto: nome, patrimonio, orizzonte, obiettivo
(nominale o reale), liquidita minima, quota massima illiquida, benchmark e soprattutto
la definizione di shortfall da usare. Premere "Salva comparto" per applicare.

**Assunzioni.** Si rivedono le Capital Market Assumptions in una tabella modificabile
(rendimenti, volatilita, costi, duration, valuta, bande). Si possono aggiungere o
togliere asset class. Premere "Applica modifiche" per salvarle. In fondo: importazione
da Excel ed esportazione del set corrente.

**Correlazioni.** Si modifica la matrice di correlazione e se ne vede la heatmap.
Premendo "Valida e salva" l'app verifica che la matrice sia valida (semi-definita
positiva). Se non lo e', propone una matrice valida vicina, che va accettata
esplicitamente: l'app non corregge mai i dati di nascosto.

**Asset Allocation Lab.** Il cuore dell'app. Si scelgono i pesi con gli slider e tutte
le metriche si aggiornano: rendimenti (nominale, netto, reale, geometrico), volatilita,
montante atteso, quota illiquida, esposizione valutaria, duration, contributo al
rischio per asset class, e lo stato dei vincoli a semaforo. La composizione si salva
come proposta con un nome, per riusarla nelle altre pagine.

**Simulazioni.** Si sceglie una proposta e si lancia il Monte Carlo sull'orizzonte del
comparto. Si ottengono probabilita di shortfall, VaR, Expected Shortfall, i percentili
del montante e l'istogramma della distribuzione. I parametri (numero di simulazioni,
seed, inflazione, confidenza) sono regolabili.

**Confronto.** Si selezionano piu' proposte e si confrontano in tabella e in un grafico
rischio-rendimento. Opzionalmente si includono i risultati Monte Carlo. In fondo, i
pesi delle proposte affiancati.

**Controlli.** Vista dettagliata dei vincoli per una proposta, con stato complessivo e
nota per ciascun vincolo.

**Report.** Genera un file Excel con metadati, comparto, assunzioni, matrice, pesi e
risultati di tutte le proposte, da scaricare e riusare nella documentazione del DPI.

## Flusso tipico

1. Configura il comparto.
2. Rivedi o carica le assunzioni e la matrice.
3. Nel Lab costruisci una o piu' proposte e salvale.
4. Simula le proposte piu' promettenti.
5. Confrontale e controlla i vincoli.
6. Esporta il report.

## Dati reali

Quando sostituirai i dati demo con quelli del Fondo (dalla pagina Assunzioni), ricorda
di non committare file con dati reali nel repository pubblico e di valutare un'app
privata. Vedi le note di privacy in STREAMLIT_DEPLOY.md e GITHUB.md.

## Simulazione CMA e Stress Test (pagina 10)

Due schede distinte.

**Simulazione condizionata alle CMA.** Le Capital Market Assumptions (rendimenti,
volatilità, correlazioni, costi, inflazione) sono gli input; il motore genera rendimenti
futuri coerenti con tali ipotesi. Si scelgono: distribuzione (Normale o t di Student),
gradi di libertà della t, orizzonte, frequenza (annuale/mensile), numero di simulazioni,
seed, inflazione, livello di confidenza VaR/ES, ribilanciamento. Output: probabilità ed
entità dello shortfall, VaR, Expected Shortfall, massimo drawdown mediano, istogramma dei
montanti reali e fan chart dei percorsi. La distribuzione t mostra code più spesse: tende
a produrre un Expected Shortfall più alto della Normale, evidenziando il rischio di coda.

**Stress test deterministici.** Scenari di shock (azionario, tassi, illiquidi, combinato)
applicati al portafoglio. Non sono probabilità: rappresentano l'impatto istantaneo di uno
scenario. Output: perdita complessiva, nuovo valore, contributo alla perdita per asset
class, quota illiquida post-shock. Gli scenari demo sono modificabili.

## Ottimizzazione AAS (pagina 11)

Si seleziona una AAS vigente di riferimento e una funzione obiettivo (minima varianza,
massimo rendimento, massimo Sharpe). Si configurano vincoli aggiuntivi (rendimento
minimo, volatilità massima, turnover massimo) oltre alle bande, liquidità e illiquidità
del comparto. L'ottimizzatore propone un portafoglio, lo confronta con la AAS vigente
(grafico dei pesi e turnover) e mostra la frontiera efficiente con il punto ottimizzato
evidenziato. Se i vincoli sono incompatibili, l'app non restituisce pesi fittizi: segnala
l'infeasibilità e indica i vincoli problematici. La proposta può essere salvata tra le
proposte della sessione.

> Avvertenza: i parametri predefiniti sono tecnici e provvisori e devono essere validati
> dalla Funzione Gestione dei Rischi e dagli organi competenti del Fondo prima
> dell'utilizzo formale nel DPI. I dati CMA, le matrici e i comparti sono demo.
