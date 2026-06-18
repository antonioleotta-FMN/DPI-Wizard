# Come pubblicare DPI Wizard su Streamlit Community Cloud

Da fare DOPO aver caricato il codice su GitHub (vedi GITHUB.md).

## Passi
1. Vai su https://share.streamlit.io e accedi con il tuo account GitHub.
2. Clicca "New app" / "Deploy a public app from GitHub".
3. Compila:
   - **Repository**: `TUO_UTENTE/dpi-wizard`
   - **Branch**: `main`
   - **Main file path**: `app.py`
4. Clicca "Deploy". La prima build richiede qualche minuto (installa le dipendenze
   da requirements.txt).

## Cosa vedrai
La pagina diagnostica: metriche deterministiche, verifica vincoli a semaforo,
contributo al rischio per asset class e una simulazione Monte Carlo con istogramma
dei montanti reali. Tutto con dati DEMO etichettati.

## Note di compatibilita'
- `requirements.txt` usa pin a FASCE di versione, non versioni esatte: e' la scelta
  piu' robusta sul cloud, dove l'immagine puo' avere versioni leggermente diverse.
- `runtime.txt` fissa Python 3.12.
- Se la build fallisse per una libreria, il primo posto da guardare e' il log di
  Streamlit Cloud ("Manage app" -> log): di solito segnala il pacchetto in conflitto.

## Privacy
La pagina diagnostica usa solo dati demo: nessun dato del Fondo viene pubblicato.
Quando in futuro l'app gestira' dati reali, valutare un'app PRIVATA o un ambiente
Streamlit non pubblico, e non committare mai dati reali nel repository.
