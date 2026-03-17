from src.conf.config_manager import ConfigManager
from src.utilities.database_manager import NewsDatabase
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
import sqlite3
import os
import feedparser


def main():
    module_name = 'feed_store'
    
    # Load configuration
    config = ConfigManager()
    
    # Get global configuration for different components
    telegram_config = config.get_telegram_config()
    logging_config = config.get_logging_config()
    paths_config = config.get_paths_config()
    database_config = config.get_database_config()
    
    # Get module-specific configuration
    module_config = config.get_module_config(module_name)
    
    # Initialize path manager
    path_manager = PathManager()
    log_dir = path_manager.ensure_directory_exists(paths_config['logs_subdir'])
    
    # Initialize logger with configuration
    logger = EnhancedLogger(module_name, log_dir, logging_config)
    logger.setup_logging()
    
    # Extract module-specific settings
    feed_urls = module_config.get('tech_feed', [])
    if isinstance(feed_urls, str):
        feed_urls = [url.strip() for url in feed_urls.split(',')]
    
    # Module startup logging with configuration summary
    logger.logger.info("Starting feed_store module")
    logger.logger.info(f"Feed URLs: {len(feed_urls)} URLs")
    
    try:
        # Phase 1: Setup and Database Connection
        logger.logger.info("Initializing module components")
        db_name = database_config['default_news_db']
        db_path = path_manager.get_database_path(db_name, paths_config.get('databases_subdir'))
        logger.logger.info(f"Database path: {db_path}")
        
        news_db = NewsDatabase(db_path)
        
        logger.logger.info("Module initialization completed")

        # Phase 2: Fetch and Store News from Feeds
        logger.logger.info("Starting news fetching phase")
        for feed_url in feed_urls:
            logger.logger.info(f"Fetching news from feed: {feed_url}")
            try:
                feed = feedparser.parse(feed_url)
                if feed.bozo:
                    logger.logger.warning(f"Failed to parse feed {feed_url}: {feed.bozo_exception}")
                    continue
                
                for entry in feed.entries:
                    title = entry.get('title', 'No Title')
                    url = entry.get('link', '')
                    source = entry.get('base', feed_url)  # Use feed URL as source if base is not provided
                    published_date = entry.get('published', '')
                    
                    success, message = news_db.insert_news_item(title=title, url=url, source=source,category='tech', published_date=published_date)
                    if success:
                        logger.logger.info(f"Inserted news: {title} from {source}")
                    else:
                        logger.logger.warning(f"Failed to insert news: {title} from {source}. Reason: {message}")
            
            except Exception as e:
                logger.logger.error(f"Error fetching news from feed {feed_url}: {str(e)}")
    
    except Exception as e:
        logger.logger.error(f"An error occurred in the feed_store module: {str(e)}")
        
    finally:
        # Ensure database connection is closed
        try:
            if 'news_db' in locals():
                news_db.close()
                logger.logger.info("Database connection closed")
        except Exception as e:
            logger.logger.warning(f"Error closing database connection: {str(e)}")
    
if __name__ == "__main__":
    main()
