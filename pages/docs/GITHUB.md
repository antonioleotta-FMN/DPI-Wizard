# Come caricare DPI Wizard su GitHub

Workflow approvato (DEC-010): un solo branch `main`, commit diretti, tag per le
versioni stabili. Pensato per un utilizzo semplice, senza pull request.

## Prerequisiti (una volta sola)
1. Crea un account su https://github.com
2. Installa Git: https://git-scm.com/downloads
3. Configura nome ed email (sostituisci con i tuoi):
   ```bash
   git config --global user.name "Antonio"
   git config --global user.email "tua@email.it"
   ```

## Primo caricamento
1. Su GitHub: "New repository", nome es. `dpi-wizard`, **Private** (consigliato),
   senza inizializzare README/gitignore (li abbiamo gia').
2. Nella cartella del progetto, da terminale:
   ```bash
   cd dpi-wizard
   git init
   git add .
   git commit -m "M2: dominio, metriche deterministiche, data layer"
   git branch -M main
   git remote add origin https://github.com/TUO_UTENTE/dpi-wizard.git
   git push -u origin main
   ```

## Aggiornamenti successivi (a ogni milestone)
```bash
git add .
git commit -m "M3: motore Monte Carlo e vincoli"
git push
```

## Tag per le versioni stabili
Quando una versione e' stabile (es. dopo l'MVP):
```bash
git tag -a v0.1.0 -m "MVP funzionante in locale"
git push origin v0.1.0
```

## Cosa NON deve mai finire nel repository
Gia' escluso da .gitignore, ma da tenere a mente (requisito Privacy del progetto):
- dati personali o riservati del Fondo;
- credenziali, password, chiavi API (`.streamlit/secrets.toml` e' escluso);
- file Excel con dati reali (la cartella data/ e' esclusa, tranne data/demo/).

## Verifica veloce prima di ogni push
```bash
python -m pytest -q     # tutti i test devono passare
git status              # controlla che non ci siano file riservati tra i "to be committed"
```
