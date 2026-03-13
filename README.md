# a_gent_parl

Progetto Python per l'automazione e la pubblicazione di contenuti (notizie, citazioni, curiosità) su diversi canali.

## Struttura del repository

- `articles/`: articoli statici Markdown.
- `data/`: cache, database SQLite, immagini, log.
- `legacy_code/`: script Python storici (`happened_today.py`, `most_viewed_weekly.py`, `post_image_weekly.py`).
- `src/`: codice principale del progetto.
  - `conf/`: configurazioni e gestione config.
  - `feed_store/`, `happened_today/`, `nerd_curiosities/`, `nerd_quote/`, `ps_news/`, `tech_news/`, `weekly_posting_image/`, `wiki_most_viewed/`, `youtube_trend/`: microservizi/done Python e Docker.
  - `utilities/`: helper (database, logger, LLM interface, Telegram, Wikipedia, YouTube ecc.).

## Microservizi Python

- `src/feed_store/`: gestione e aggiornamento del feed principale dell’applicazione.
- `src/happened_today/`: crea e pubblica contenuti basati su fatti storici accaduti nella data corrente.
- `src/nerd_curiosities/`: genera e pubblica curiosità nerd (scienza, cultura, tecnologia) usando fonte dati interne/esterne.
- `src/nerd_quote/`: raccoglie e invia citazioni nerd da database dedicato o API di quote.
- `src/ps_news/`: estrazione e pubblicazione di notizie (probabilmente “programmazione e software” o simili) in canale dedicato.
- `src/tech_news/`: estrazione e pubblicazione notizie tech aggiornate da RSS/API.
- `src/weekly_posting_image/`: crea il post settimanale con immagine e testuale, spinge il contenuto su canali social (Telegram/altro).
- `src/wiki_most_viewed/`: usa dati Wikipedia delle pagine più viste per generare contenuti e trend.
- `src/youtube_trend/`: raccoglie trend YouTube e posta riepiloghi.

## Requisiti

- Python 3.11+ (o versione minima usata dai singoli `requirements.txt`).
- Virtualenv (consigliato) o environment alternativo.

## Avvio rapido

1. Creare environment (dalla root):

```powershell
python -m venv .venv_agp
.venv_agp\Scripts\Activate.ps1
pip install -r src\<servizio>\requirements.txt
```

2. Eseguire il servizio desiderato:

```powershell
python src\<servizio>\main.py
```

Esempi:
- `src\nerd_curiosities\main.py`
- `src\tech_news\main.py`

## Configurazione

- File principale: `src/conf/config.ini` / `src/conf/.env`.
- Gestione config in `src/conf/config_manager.py`.

## Logging

- Log scritti in `data/logs/` (es. `weekly_nerd_curiosities`).

## Database

- Database SQLite:
  - `data/databases/nerd_curiosities.sqlite3`
  - `data/databases/news_db.sqlite3`
  - `data/databases/quote_db.sqlite3`

## Note

- Il repository include file `.github/copilot-instructions.md` per norme di sviluppo, hook pre-commit e automazioni.
- Per aggiungere nuove pipeline, copiare l’esempio dei servizi esistenti (Dockerfile + main.py + requirements).

---

## Contatti

Mantieni il repository aggiornato con file di progetto e dati rinnovati.
