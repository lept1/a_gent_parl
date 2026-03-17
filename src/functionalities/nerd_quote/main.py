from src.conf.config_manager import ConfigManager
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.database_manager import QuoteDatabase
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
import sqlite3
import os

SYSTEM_INSTRUCTION = """
  You are an AI assistant that generates hashtags for quotes and content for social media in ITALIAN.
  Generate 3 relevant hashtags based on the quote and author provided. Use popular and trending hashtags where applicable. 
  Format the hashtags as a space-separated list, each starting with a # symbol, without any additional text or punctuation.
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

    #QuoteOfTheDay <GENERATED HASHTAGS> 

    ***<QUOTE TEXT TRANSLATED IN ITALIAN>***
    _<AUTHOR NAME>_

    <SHORT DESCRIPTION OF THE AUTHOR AND WHERE THE QUOTE IS FROM>

  Do not include any other text or explanation.
"""

def main():
    module_name = 'nerd_quote'
    
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
    
    # Get nerd categories from module configuration
    nerd_categories = module_config.get('nerd_categories', [])
    if isinstance(nerd_categories, str):
        nerd_categories = [cat.strip() for cat in nerd_categories.split(',')]
    
    # Module startup logging with configuration summary
    logger.logger.info("🚀 Starting weekly_quote module")
    logger.logger.info(f"📋 Configuration: {len(nerd_categories)} categories")
    
    try:
        # Phase 1: Setup and Database Connection
        logger.logger.info("🔧 Initializing module components")
        db_name = database_config['default_quote_db']
        db_path = path_manager.get_database_path(db_name, paths_config.get('databases_subdir'))
        logger.logger.info(f"📁 Database path: {db_path}")
        
        quote_db = QuoteDatabase(db_path)
        
        # Test database connection with detailed context
        try:
            cursor = quote_db.conn.cursor()
            cursor.execute('SELECT COUNT(*) FROM Quote')
            total_quotes = cursor.fetchone()[0]
            cursor.execute('SELECT COUNT(*) FROM Quote WHERE posted = 0')
            unposted_quotes = cursor.fetchone()[0]
            logger.logger.info(f"✅ Database connected successfully: {total_quotes} total quotes, {unposted_quotes} unposted")
        except sqlite3.Error as e:
            logger.logger.error(f"❌ Database connection failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Attempting to connect to {db_path}")
            logger.logger.error(f"💡 Suggestion: Verify database file exists and has correct permissions")
            raise
        
        logger.logger.info("✅ Module initialization completed")
        
        # Phase 2: Quote Selection
        logger.logger.info("📥 Starting quote selection phase")
        logger.logger.info(f"🚫 Nerd categories: {', '.join(nerd_categories)}")
        
        quote_data = quote_db.get_random_unposted_quote(categories=nerd_categories)
        
        if not quote_data:
            logger.logger.warning("⚠️ No unposted quotes found matching criteria")
            logger.logger.info(f"🔍 Context: Searched for quotes in {len(nerd_categories)} categories")
            logger.logger.info("💡 Suggestion: Check if all quotes have been posted or add new quotes to database")
            return
        
        # Extract and log quote information
        quote_id = quote_data['id']
        author = quote_data['author']
        quote = quote_data['quote_text']
        category = quote_data['category']
        
        logger.logger.info(f"✅ Quote selected successfully: ID={quote_id}, Author='{author}', Category='{category}'")
        logger.logger.info(f"📊 Quote length: {len(quote)} characters")
        
        # Phase 3: Content Generation
        logger.logger.info("🤖 Starting content generation phase")
        logger.logger.info(f"📝 Input: Quote by {author} ({len(quote)} chars)")
        
        try:
            # Initialize LLM interface (uses environment variables by default)
            gemini = LLMInterface()
            query = f"quote: {quote}\nauthor: {author}"
            telegram_post = gemini.generate_text(SYSTEM_INSTRUCTION, query)
            
            logger.logger.info(f"✅ Content generated successfully: {len(telegram_post)} characters")
            logger.logger.info(f"📊 Generated content preview: {telegram_post[:100]}...")
            
        except Exception as e:
            logger.logger.error(f"❌ Content generation failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Processing quote ID {quote_id} by {author}")
            logger.logger.error(f"💡 Suggestion: Check Gemini API key and network connectivity")
            raise
        
        # Phase 4: Publication
        logger.logger.info("📤 Starting content publication phase")
        
        try:
            # Initialize Telegram interface with configuration
            telegram_bot = TelegramInterface(
                retry_attempts=telegram_config['retry_attempts'],
                retry_delay=telegram_config['retry_delay']
            )
            telegram_bot.send_message(telegram_post)
            logger.logger.info("✅ Content published to Telegram successfully")
            logger.logger.info(f"📊 Published content length: {len(telegram_post)} characters")
            
        except Exception as e:
            logger.logger.error(f"❌ Telegram publication failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Attempting to publish quote ID {quote_id}")
            logger.logger.error(f"💡 Suggestion: Check Telegram bot token and channel permissions")
            raise
        
        # Phase 5: Database Update
        logger.logger.info("💾 Updating database status")
        
        try:
            success = quote_db.mark_quote_posted(quote_id)
            if success:
                logger.logger.info(f"✅ Quote ID {quote_id} marked as posted successfully")
            else:
                logger.logger.error(f"❌ Failed to mark quote ID {quote_id} as posted")
                logger.logger.error(f"💡 Suggestion: Check database write permissions and connection")
                
        except Exception as e:
            logger.logger.error(f"❌ Database update failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Marking quote ID {quote_id} as posted")
            logger.logger.error(f"💡 Suggestion: Verify database is not locked and has write permissions")
            # Don't raise here as the post was successful
        
        # Module completion
        logger.logger.info("🎉 weekly_quote completed successfully")
        logger.logger.info(f"📊 Summary: Quote ID {quote_id} by {author} published and marked as posted")
        
        print(telegram_post)
        
    except Exception as e:
        logger.logger.error(f"❌ weekly_quote failed: {str(e)}")
        logger.logger.error(f"💡 Suggestion: Check logs above for specific error context and remediation steps")
        raise
    finally:
        # Ensure database connection is closed
        try:
            if 'quote_db' in locals():
                quote_db.close()
                logger.logger.info("🔒 Database connection closed")
        except Exception as e:
            logger.logger.warning(f"⚠️ Error closing database connection: {str(e)}")
    
if __name__ == "__main__":
    main()
