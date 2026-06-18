# DPI Wizard

Web app a supporto della Funzione Finanza del **Fondo Pensione Mario Negri** per la
definizione, verifica e revisione del **Documento sulla Politica di Investimento (DPI)**.

L'app permette di esplorare in modo tracciabile come variano rendimento (nominale,
netto costi, reale), rischio, probabilita ed entita di shortfall, Expected Shortfall,
liquidita ed esposizione valutaria al modificarsi dell'Asset Allocation Strategica di
un comparto. Non e' un ottimizzatore: e' un laboratorio di analisi e confronto con
verifica dei vincoli e output riutilizzabili nel DPI.

## Stato

MVP multipage funzionante (M4). Avvio locale:

```bash
pip install -r requirements.txt
streamlit run app.py
```

Le pagine: Home, Comparti, Assunzioni, Correlazioni, Asset Allocation Lab,
Simulazioni, Confronto, Controlli, Report. Stato corrente e prossimi passi in
`docs/PROJECT_STATE.md`. Decisioni di progetto in `docs/DECISIONS.md`. Deploy su
Streamlit Cloud: `docs/STREAMLIT_DEPLOY.md`. Caricamento su GitHub: `docs/GITHUB.md`.

Documentazione: `docs/MANUALE_UTENTE.md`, `docs/MANUALE_METODOLOGICO.md`,
`docs/GLOSSARIO.md` (glossario e data dictionary), `docs/CHANGELOG.md`.

> **Avvertenza.** L'app e' uno strumento di supporto alle decisioni. Non sostituisce
> la valutazione degli organi del Fondo, della Funzione Gestione dei rischi, della
> Compliance ne la valutazione legale. I dati demo sono etichettati come tali e non
> costituiscono dati ufficiali del Fondo.

## Requisiti

Python 3.12+. Dipendenze in `requirements.txt`.

```bash
pip install -r requirements.txt
```

## Test

```bash
python -m pytest -q
```

## Struttura

```
dpi-wizard/
  app.py            entrypoint Streamlit (in arrivo)
  pages/            pagine UI (solo presentazione)
  src/
    domain/         modelli dati (Pydantic)
    calculations/   metriche deterministiche
    simulations/    Monte Carlo
    constraints/    motore vincoli
    data/           IO, validazione, dataset demo
    reporting/      export Excel, audit trail
    services/       facade dominio<->UI
  config/  data/demo/  tests/  docs/  .streamlit/
```

Principio inviolabile: nessuna formula finanziaria rilevante nelle pagine Streamlit.
