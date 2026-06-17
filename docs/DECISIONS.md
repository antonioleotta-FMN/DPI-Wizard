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
