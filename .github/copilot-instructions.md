# Copilot Instructions per a_gent_parl

Questa guida è pensata per aiutare GitHub Copilot e qualsiasi contributore a mantenere uno stile coerente e a rispettare le convenzioni del progetto.

## 1) Obiettivi del progetto
- Generazione automatica di contenuti (quote, curiosità, notizie) tramite LLM (Google Gemini) e pubblicazione su Telegram.
- Raccolta dati da fonti esterne: Wikipedia (SPARQL), RSS, YouTube, dataset locali sqlite.
- Log robusti e gestione errori con rotazione file.

## 2) Struttura cartelle
- `src/`: codice principale
  - `conf/`: gestione configurazione (`ConfigManager`, `.env`, `config.ini`)
  - `utilities/`: classi riutilizzabili
    - `enhanced_logger.py`, `path_manager.py`, `llm_interface.py`, `telegram_interface.py`, `wikipedia_interface.py`, `youtube_interface.py`, `database_manager.py`
  - servizi specifici / componenti:
    - `happened_today/`, `nerd_curiosities/`, `nerd_quote/`, `ps_news/`, `tech_news/`, `feed_store/`, `wiki_most_viewed/`, `youtube_trend/`, `weekly_posting_image/`
- `legacy_code/`: script precedenti (da valutare e integrare o deprecare)
- `data/`: cache, DB sqlite, immagini, logs
- `articles/`: articoli statici e piano editoriale

## 3) Convenzioni di stile (Python)
- Nomi funzione / variabili: `snake_case`
- Nomi classi: `CamelCase`
- Tipi opzionali / annotazioni: `typing.Optional`, `Dict`, `List`, `Any`.
- Docstring standard per classi e metodi in stile Google/Python (brief + args + returns)
- Evitare logica in `if __name__ == '__main__'` pesante: usare `main()` modulare.
- Eldried statements: ogni modulo ha funzione `main()` e TVA (try/catch + log + raise se necessario)

## 4) Principali librerie e framework
- Google Gemini: `from google import genai`, `from google.genai import types`
- Requests: `requests` per chiamate REST
- SQLite: `sqlite3` per DB locali (in utilities/database_manager.py)
- SPARQL: `SPARQLWrapper` usato in `wikipedia_interface.py`
- YouTube API: `googleapiclient.discovery`
- Feed parsing: `feedparser`
- Config/Env: `configparser`, `dotenv` (`python-dotenv`)
- Logging: `logging`, `logging.handlers.RotatingFileHandler`
- Standard Python: `os`, `pathlib.Path`, `time`, `datetime`, `random`, `re`

> Non ci sono micro-framework web (FastAPI/Flask) al momento; si tratta di script CLI/Docker batch.

## 5) Gestione errori e log
### EnhancedLogger
- Classe centralizzata `EnhancedLogger` in `src/utilities/enhanced_logger.py`
- Supporta:
  - log console + file (rotating)
  - configurazione livello (`INFO`, `DEBUG`, `WARNING`, `ERROR`)
  - mascheramento chiavi sensibili (`GEMINI_API_KEY`, `TELEGRAM_BOT_TOKEN`, `API_KEY`, `TOKEN`, `SECRET`, etc.)
  - log API (metodo `log_api_call`)
  - log errori con contesto (metodo `log_error_with_context`)
  - `log_module_start` / `log_module_end`

### Error handling nei moduli
- Blocchi `try/except Exception as e` nei `main` dei service module (es. `happened_today`) con:
  - logging dell’errore
  - error context info
  - suggerimenti diagnostici (`ok`, rete, chiavi API)
  - rialzo (raise) finale per fallimento non silente

### Config Manager
- `ConfigManager` solido con fallback e validazione.
- `load_environment_variables` lancia `FileNotFoundError` / `ValueError` se variabili obbligatorie mancano.
- `get_*_config` ritorna default type safe.
- `_validate_and_fix_config` aggiorna `.ini` e logga warning su chiavi mancanti.

## 6) Best practice per Copilot in questa codebase
- Mantieni il pattern: modulo -> carica config -> init logging -> servizi -> esegui su try/except -> log success/fail.
- Usa `PathManager` per percorsi file e directory.
- Centralizza i DB con `database_manager.ContentDatabase` / `QuoteDatabase`.
- Testare i flussi di fallimento prima di postare su API esterne (simula `requests` / Telegram). 
- Non salvare/selezionare credenziali nel codice; leggere da `%PROJECT%/src/conf/.env`.

## 7) Checklist per PR
- [ ] Lo script mantiene lo stile `snake_case` e docstring coerenti
- [ ] La logica principale è in `main()` e viene chiamata da `if __name__ == '__main__'`
- [ ] `EnhancedLogger` è usato e il log file è in `data/logs` (o path da config)
- [ ] Gestione errori robusta (`try/except` + `logger.error` + `raise` quando necessario)
- [ ] I segreti sono mascherati nelle stringhe di log
- [ ] `config.ini` ed `.env` ammissibili non sono inclusi in git (sotto .gitignore), ma documentati nel README
- [ ] Documentazione delle nuove feature è aggiornata (`README` o `/docs` se presente)

---

### NOTE per futuri task Copilot
- Mantieni il focus su script batch / ETL di contenuto e non su API web.
- Favorisci un design modulare con classi interface (`TelegramInterface`, `WikipediaInterface`, `LLMInterface`) per testabilità.
- Aggiorna questo file con nuove parti `src/<new_component>` quando aggiungi pipeline differenziate (es. `instagram_posting`, `discord_feed`).
