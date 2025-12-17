import src.utilities.telegram_interface as telegram
import src.utilities.llm_interface as llm
from src.utilities.config_manager import ConfigManager
from src.utilities.database_manager import QuoteDatabase
import sqlite3
import os
from src.utilities.enhanced_logger import EnhancedLogger

# Initialize configuration manager
config_manager = ConfigManager('weekly_quote')

logger = EnhancedLogger(module_name='weekly_quote',config_manager=config_manager)
logger.setup_logging()

# Set nerd-specific validation constants
config_manager.set_validation_constants(
    min_content_length=500,
    max_retries=5,
    post_length_min=200,
    post_length_max=500,
    telegram_retry_attempts=3,
    telegram_retry_delay=30
)

# Ensure data directories exist
config_manager.ensure_data_directories()

config_manager.load_environment_variables()



NERD_CATEGORIES = [
    "anime",
    "manga", 
    "comics",
    "video games",
    "science fiction",
    "fantasy",
    "tabletop games",
    "animation",
    "japanese popular culture",
    "fuperhero fiction",
    "Role-playing games",
    "collectible card games"
]

# Configure quote-specific settings
config_manager.set_validation_constants(
    categories=NERD_CATEGORIES,
    min_quote_length=10,
    max_quote_length=500
)

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
    logger.logger.info("Starting the weekly quote generation process.")
    # Use ConfigManager for database path
    logger.logger.info("Initializing Quote DB")
    db_name = 'quote_db.sqlite3'
    db_path = config_manager.get_database_path(db_name)
    quote_db = QuoteDatabase(db_path)

    #Check connnection to db
    try:
        cursor = quote_db.conn.cursor()
        cursor.execute('SELECT 1')
        logger.logger.info("Successfully connected to the database.")
    except sqlite3.Error as e:
        logger.logger.error(f"Failed to connect to the database: {e}")
        exit(1)

    categories = config_manager.get_validation_constant('categories')
    
    # Get random unposted quote excluding specified categories
    logger.logger.info("Fetching a random unposted quote.")
    quote_data = quote_db.get_random_unposted_quote(categories=categories)

    if not quote_data:
        logger.logger.info("No unposted quotes found matching criteria.")
        return

    # Extract quote information (QuoteDatabase returns dict format)
    logger.logger.info("Quote data fetched successfully.")
    logger.logger.info(f"Quote ID: {quote_data['id']}, Author: {quote_data['author']}, Category: {quote_data['category']}")
    quote_id = quote_data['id']
    author = quote_data['author']
    quote = quote_data['quote']
    category = quote_data['category']

    logger.logger.info("Generating Telegram post content using Gemini.")
    gemini = llm.LLMInterface()
    query = f"quote: {quote}\nauthor: {author}"
    telegram_post = gemini.generate_text(SYSTEM_INSTRUCTION, query)
    logger.logger.info("Telegram post content generated successfully.")
    logger.logger.info(f"Telegram post content: {telegram_post}")
    telegram_bot = telegram.TelegramInterface()
    telegram_bot.send_message(telegram_post)
    logger.logger.info("Telegram post sent successfully.")
    print(telegram_post)

    # Mark as posted
    success = quote_db.mark_quote_posted(quote_id)
    if success:
        logger.logger.info(f"Quote id {quote_id} marked as posted successfully.")
    else:
        logger.logger.error(f"Failed to mark quote id {quote_id} as posted.")
    quote_db.close()
    
if __name__ == "__main__":
    main()
