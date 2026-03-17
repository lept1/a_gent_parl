from src.conf.config_manager import ConfigManager
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.database_manager import NewsDatabase
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
import sqlite3
import os


SYSTEM_INSTRUCTION = """
  You are an AI assistant and your task is to create a concise and engaging Telegram post that summarizes the most relevant news items from the provided list.
  The format of the news items MUST BE as follows:

    #TechNews #LatestUpdates #TechTrends

    1. [TITLE]([URL])
       [HASHTAGS RELATED TO THE NEWS ITEM]
       [PUBLISHED DATE OF THE NEWS]
       [SHORT DESCRIPTION IN ITALIAN OF THE NEWS AND WHY IT'S IMPORTANT]

... (repeat for each news item)


IMPORTANT : Do not include any other text or explanation.
"""

def main():
    module_name = 'tech_news'
    
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
    hashtag_count = module_config.get('hashtag_count', 5)
    top_news_count = module_config.get('top_news_count', 5)
    
    # Module startup logging with configuration summary
    logger.logger.info("Starting tech_news module")
    
    try:
        # Phase 1: Setup and Database Connection
        logger.logger.info("Initializing module components")
        db_name = database_config['default_news_db']
        db_path = path_manager.get_database_path(db_name, paths_config.get('databases_subdir'))
        logger.logger.info(f"Database path: {db_path}")
        
        news_db = NewsDatabase(db_path)
        
        # Test database connection with detailed context
        try:
            cursor = news_db.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM News')
            total_news = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM News WHERE posted = 0')
            unposted_news = cursor.fetchone()[0]
            logger.logger.info(f"Database connected successfully: {total_news} total news, {unposted_news} unposted")
        except sqlite3.Error as e:
            logger.logger.error(f"Database connection failed: {str(e)}")
            logger.logger.error(f"Context: Attempting to connect to {db_path}")
            logger.logger.error(f"Suggestion: Verify database file exists and has correct permissions")
            raise
        
        logger.logger.info("Module initialization completed")
        
        # Phase 2: Select unposted news
        logger.logger.info("Selecting unposted news from database")
        news_data = news_db.get_unposted_content(category='tech')  # Pass category filter to select only tech news
        
        if not news_data:
            logger.logger.warning("No unposted news found matching criteria")
            logger.logger.info("Suggestion: Check if all news have been posted or add new news to database")
            return
        
        # Pass all news data to the content generation phase 
        try:
            # Initialize LLM interface (uses environment variables by default)
            gemini = LLMInterface()
            query=f"Select the {top_news_count} most relevant news items, add {hashtag_count} hashtags and generate a short, engaging Telegram post summarizing them:\n\n"
            for news_item in news_data:
                query += f" - Title: {news_item['title']} URL: {news_item['url']} Published Date: {news_item['published_date']}\n\n"
            
            telegram_post = gemini.generate_text(SYSTEM_INSTRUCTION, query)
            
            logger.logger.info(f"Content generated successfully: {len(telegram_post)} characters")
            
        except Exception as e:
            logger.logger.error(f"Content generation failed: {str(e)}")
            raise
        
        # Phase 4: Publication
        logger.logger.info("Starting content publication phase")
        
        try:
            # Initialize Telegram interface with configuration
            telegram_bot = TelegramInterface(
                retry_attempts=telegram_config['retry_attempts'],
                retry_delay=telegram_config['retry_delay']
            )
            telegram_bot.send_message(telegram_post)
            logger.logger.info("Content published to Telegram successfully")
            
        except Exception as e:
            logger.logger.error(f"Telegram publication failed: {str(e)}")
            raise
        
        # Phase 5: Database Update
        logger.logger.info("Updating database status")
        
        news_ids = [item['id'] for item in news_data]
        success, message = news_db.mark_news_posted(news_ids)  # Mark all news items as posted
        if success:
            logger.logger.info(f"News items with IDs {news_ids} marked as posted successfully")
        else:
            logger.logger.error(f"Failed to mark news items with IDs {news_ids} as posted: {message}")
                
        # Module completion
        logger.logger.info("News posting completed successfully")
        
    except Exception as e:
        logger.logger.error(f"News posting module failed: {str(e)}")
        raise
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
