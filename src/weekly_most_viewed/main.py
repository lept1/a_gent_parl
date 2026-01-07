from src.conf.config_manager import ConfigManager
from src.utilities.wikipedia_interface import WikipediaInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
import time

def main():
    module_name = 'weekly_most_viewed'
    
    # Load configuration
    config = ConfigManager()
    
    # Get global configuration for different components
    telegram_config = config.get_telegram_config()
    logging_config = config.get_logging_config()
    paths_config = config.get_paths_config()
    
    # Get module-specific configuration
    module_config = config.get_module_config(module_name)
    
    # Initialize path manager
    path_manager = PathManager()
    log_dir = path_manager.ensure_directory_exists(paths_config['logs_subdir'])
    
    # Initialize logger with new architecture
    enhanced_logger = EnhancedLogger(module_name=module_name, log_dir=log_dir, log_config=logging_config)
    enhanced_logger.setup_logging()
    logger = enhanced_logger.logger

    # Module startup logging
    logger.info("🚀 Starting weekly_most_viewed module")
    
    # Get module-specific settings from configuration
    country_code = module_config.get('country_code', 'IT')
    top_articles_count = module_config.get('top_articles_count', 5)
    exclude_articles = module_config.get('exclude_articles', 'Main Page,Wikipedia')
    
    # # Convert exclude_articles to list and add additional exclusions
    # exclude_articles_list = [article.strip() for article in exclude_articles_str.split(',')]
    # pages_to_exclude = exclude_articles_list + [
    #     "Main_Page", "Special:Search", "Pagina_principale", "Speciale:Ricerca", 
    #     "Wikipedia:Hauptseite", "Spezial:Suche", "Wikipedia:Portada", "Especial:Buscar", 
    #     "Wikipédia:Accueil_principal","Spécial:Recherche","Wikipedia:Featured_pictures"
    # ]
    
    country_list = [country_code]
    
    logger.info(f"📋 Configuration: Top {top_articles_count} trending articles from {country_code}, period=week")
    logger.info(f"📊 Configuration loaded - Countries: {country_list}, Excluded pages: {len(exclude_articles)}")

    try:
        # Phase 1: Setup and Configuration
        logger.info("🔧 Initializing module components")
        
        # Ensure data directories exist
        path_manager.ensure_directory_exists(paths_config['data_root'])
        path_manager.ensure_directory_exists(paths_config['cache_subdir'])
        logger.info("✅ Data directories verified")
        logger.info("✅ Module initialization completed")

        # Phase 2: Data Fetching
        logger.info("📥 Starting Wikipedia article fetching phase")
        start_time = time.time()
        
        # Initialize Wikipedia interface (uses environment variables by default)
        wiki_interface = WikipediaInterface()
        logger.info("🔗 Wikipedia interface initialized")
        
        logger.info(f"🔍 Fetching top {top_articles_count} articles for countries: {country_list} over period: week")
        top_articles = wiki_interface.get_top_n_articles_over_period(country_list, 'week', exclude_articles, top_n=top_articles_count)
        
        fetch_duration = time.time() - start_time
        logger.info(f"⏱️ Article fetching completed in {fetch_duration:.2f}s")
        logger.info(f"📊 Performance: {len(top_articles)} articles retrieved, avg {fetch_duration/len(top_articles) if top_articles else 0:.2f}s per article")
        
        # Log article details
        for i, (article, views) in enumerate(top_articles.items(), 1):
            logger.info(f"📄 Article {i}: '{article.replace('_', ' ')}' - {views:,} views")
        
        logger.info("✅ Data fetching phase completed")

        # Phase 3: Content Generation
        logger.info("🤖 Starting content generation phase")
        
        # Prepare query for LLM
        query = "These are the trending Wikipedia articles from last week:\n"
        for article in top_articles:
            query += f"titolo: {article.replace('_', ' ')}\n"
            query += f"views: {top_articles[article]}\n\n"
        
        logger.info(f"📝 Query prepared - {len(query)} characters, {len(top_articles)} articles")
        
        # Initialize LLM interface (uses environment variables by default)
        llm_interface = LLMInterface()
        logger.info("🔗 LLM interface initialized")
        
        generation_start = time.time()
        logger.info("🎯 Generating Italian social media content for trending articles")
        
        response = llm_interface.generate_text(SYSTEM_INSTRUCTION, query)
        
        generation_duration = time.time() - generation_start
        logger.info(f"⏱️ Content generation completed in {generation_duration:.2f}s")
        logger.info(f"📊 Performance: {len(response)} chars generated, {len(response)/generation_duration:.0f} chars/sec")
        logger.info("✅ Content generation phase completed")

        # Phase 4: Publication
        logger.info("📤 Starting content publication phase")
        
        # Initialize Telegram interface with configuration
        telegram_bot = TelegramInterface(
            retry_attempts=telegram_config['retry_attempts'],
            retry_delay=telegram_config['retry_delay']
        )
        logger.info("🔗 Telegram interface initialized")
        
        publication_start = time.time()
        logger.info("📢 Publishing content to Telegram channel")
        
        telegram_bot.send_message(response)
        
        publication_duration = time.time() - publication_start
        logger.info(f"⏱️ Publication completed in {publication_duration:.2f}s")
        logger.info(f"📊 Performance: {len(response)} chars published in {publication_duration:.2f}s")

        # Module completion
        total_duration = time.time() - start_time
        logger.info(f"🎉 weekly_most_viewed completed successfully in {total_duration:.2f}s")
        logger.info(f"📊 Summary: {len(top_articles)} articles processed, {len(response)} chars generated and published")
        
    except Exception as e:
        logger.error(f"❌ weekly_most_viewed failed: {str(e)}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        
        # Provide context-specific error suggestions
        if "wikipedia" in str(e).lower():
            logger.error("💡 Suggestion: Check Wikipedia API connectivity and rate limits")
        elif "llm" in str(e).lower() or "gemini" in str(e).lower():
            logger.error("💡 Suggestion: Verify GEMINI_API_KEY and check API quota")
        elif "telegram" in str(e).lower():
            logger.error("💡 Suggestion: Verify TELEGRAM_BOT_TOKEN and CHANNEL_ID configuration")
        else:
            logger.error("💡 Suggestion: Check environment configuration and network connectivity")
        
        raise

SYSTEM_INSTRUCTION = """
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN.
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

    #WikipediaTrends <DATE> 📅

    <EMOTICON NUMBER 1> Article Title 1 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: X
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>

    <EMOTICON NUMBER 2> Article Title 2 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: Y
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>
    ...
  Do not include any other text or explanation.
"""

if __name__ == "__main__":
    main()