import src.utilities.telegram_interface as telegram
import src.utilities.llm_interface as llm
from src.utilities.config_manager import ConfigManager
from src.utilities.database_manager import QuoteDatabase
import sqlite3
import os

# Initialize ConfigManager for weekly_quote module
config = ConfigManager('weekly_quote')
config.ensure_data_directories()

# Configure quote-specific settings
config.set_validation_constants(
    excluded_categories=['anime', 'comics', 'cartoon', 'manga'],
    min_quote_length=10,
    max_quote_length=500
)

# Use ConfigManager for database path
db_name = 'quote_db.sqlite3'
db_path = config.get_database_path(db_name)
# Database Integration Options:
# Option 1: Use QuoteDatabase class (recommended for new functionality)
# - Provides structured interface with error handling
# - Supports advanced filtering and statistics
# - Better integration with other modules
# Option 2: Legacy direct SQLite approach (backward compatibility)
# - Direct database queries as before
# - Maintains existing behavior exactly
USE_QUOTE_DATABASE = False  # Set to False to use legacy direct SQLite approach

if USE_QUOTE_DATABASE:
    # Using the generic QuoteDatabase utility
    quote_db = QuoteDatabase(db_name)
    excluded_categories = config.get_validation_constant('excluded_categories')
    
    # Get random unposted quote excluding specified categories
    quote_data = quote_db.get_random_unposted_quote(excluded_categories=excluded_categories)
    
    if not quote_data:
        print("No unposted quotes found matching criteria.")
        exit(1)
    
    # Extract quote information (QuoteDatabase returns dict format)
    quote_id = quote_data['id']
    author = quote_data['author']
    quote_text = quote_data['quote_text']
    category = quote_data['category']
    
else:
    # Option 2: Legacy direct SQLite approach (backward compatibility)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # Use configured excluded categories for filtering
    excluded_categories = config.get_validation_constant('excluded_categories')
    category_conditions = ' OR '.join(['category LIKE ?' for _ in excluded_categories])
    query_text = f'SELECT * FROM Quote WHERE posted=0 AND ({category_conditions}) ORDER BY RANDOM() LIMIT 1'
    category_params = [f'%{cat}%' for cat in excluded_categories]
    records = cursor.execute(query_text, category_params).fetchall()
    
    if not records:
        print("No unposted quotes found matching criteria.")
        conn.close()
        exit(1)
    
    # Extract quote information (legacy tuple format)
    quote_id = records[0][0]
    author = records[0][1]
    quote_text = records[0][3]
    category = records[0][2]

gemini = llm.LLMInterface(env_path=config.get_env_path())
system_instruction = """
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

query = f"quote: {quote_text}\nauthor: {author}"

telegram_post = gemini.generate_text(system_instruction, query)

telegram_bot = telegram.TelegramInterface(env_path=config.get_env_path())
telegram_bot.send_message(telegram_post)

print(telegram_post)

# Mark as posted
if USE_QUOTE_DATABASE:
    # Using QuoteDatabase utility
    success = quote_db.mark_quote_posted(quote_id)
    if success:
        print(f"Marked quote id {quote_id} as posted using QuoteDatabase.")
    else:
        print(f"Failed to mark quote id {quote_id} as posted.")
    quote_db.close()
else:
    # Legacy approach
    query_text = 'UPDATE Quote SET posted=1 WHERE id=?'
    cursor.execute(query_text, (quote_id,))
    conn.commit()
    conn.close()
    print(f"Marked quote id {quote_id} as posted using legacy method.")