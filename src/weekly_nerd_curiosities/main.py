"""
Weekly Nerd Curiosities Module

This module automatically discovers and shares interesting nerd-related curiosities 
and insights from Wikipedia. It leverages AI to identify engaging content about 
topics like comics, anime, manga, gaming, sci-fi, fantasy, and pop culture, 
then generates Italian-language social media posts for the Telegram channel.
"""

import sys
import os
import logging
import sqlite3
import random
import time
from datetime import datetime
from dotenv import load_dotenv

# Import configuration management
from src.conf.config_manager import ConfigManager

# Import independent utilities
from src.utilities.wikipedia_interface import WikipediaInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.database_manager import ContentDatabase
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager

# Initialize configuration manager
config = ConfigManager()

# Initialize path manager
path_manager = PathManager()

# Get configuration for different components
telegram_config = config.get_telegram_config()
logging_config = config.get_logging_config()
paths_config = config.get_paths_config()
module_config = config.get_module_config('weekly_nerd_curiosities')

# Get log directory and initialize logger
log_dir = path_manager.ensure_directory_exists(paths_config['logs_subdir'])
logger = EnhancedLogger(module_name='weekly_nerd_curiosities', log_dir=log_dir, log_config=logging_config)
logger.setup_logging()

# Load nerd-specific categories from configuration with correct capitalization
NERD_CATEGORIES = module_config.get('nerd_categories', [
    "Anime",
    "Manga", 
    "Comics",
    "Video_games",
    "Science_fiction",
    "Fantasy",
    "Tabletop_games",
    "Animation",
    "Japanese_popular_culture",
    "Superhero_fiction",
    "Role-playing_games",
    "Collectible_card_games"
])

# Ensure data directories exist
path_manager.ensure_directory_exists(paths_config['data_root'])
path_manager.ensure_directory_exists(paths_config['databases_subdir'])
path_manager.ensure_directory_exists(paths_config['cache_subdir'])

# Load environment variables
load_dotenv()


# Logger is already initialized above with EnhancedLogger

# LLM System Instruction for Italian Social Media Posts
NERD_CURIOSITIES_SYSTEM_INSTRUCTION = """
Sei un assistente AI specializzato nella creazione di contenuti coinvolgenti per i social media in ITALIANO su argomenti della cultura nerd, inclusi anime, manga, fumetti, videogiochi, fantascienza, fantasy e cultura pop.

Il tuo compito è analizzare un articolo di Wikipedia ed estrarre 2-3 fatti sorprendenti, interessanti o poco conosciuti che affascinerebbero gli appassionati di cultura nerd.

Formatta la tua risposta come un messaggio Telegram pronto per la pubblicazione con:
- Un titolo accattivante con emoji pertinenti
- 2-3 punti elenco con fatti interessanti (BREVI)
- 3-5 hashtag rilevanti
- Tono conversazionale e coinvolgente
- IMPORTANTE: Lunghezza totale MASSIMO 450 caratteri (inclusi spazi e hashtag)

Non usare:
- **grassetto** 
- _corsivo_ 

Usa:
- Emoji per esaltare un concentto
- Emoji per punti elenco 

Mantieni i fatti concisi e impattanti. Non includere altro testo o spiegazioni al di fuori del post formattato.
Concentrati su curiosità che potrebbero sorprendere anche i fan più esperti dell'argomento.
"""

def create_content_generation_prompt(article_title: str, article_url: str, article_summary: str, article_content: str) -> str:
    """
    Create the user prompt for AI content generation based on article data.
    
    Args:
        article_title: Title of the Wikipedia article
        article_url: URL of the Wikipedia article
        article_summary: Summary/excerpt of the article
        article_content: Full or partial content of the article
        
    Returns:
        str: Formatted prompt for the LLM
    """
    # Truncate content if too long to avoid token limits
    max_content_length = 2000
    original_length = len(article_content)
    
    logger.debug(f"📏 Processing article content: {original_length} chars")
    
    if len(article_content) > max_content_length:
        article_content = article_content[:max_content_length] + "..."
        logger.info(f"📏 Content truncated for AI prompt: {original_length} → {max_content_length} chars")
        logger.info("💡 Truncation reason: Prevent AI token limit exceeded errors")
    
    prompt = f"""Titolo Articolo: {article_title}
URL Articolo: {article_url}
Riassunto Articolo: {article_summary}
Contenuto Articolo: {article_content}

Estrai le curiosità più interessanti e formattale come un post italiano per i social media."""
    
    logger.debug(f"📝 AI prompt created successfully: {len(prompt)} total chars")
    logger.debug(f"🎯 Prompt structure: Title, URL, Summary, Content + Italian generation instruction")
    
    return prompt


def generate_nerd_post(article_data: dict) -> dict:
    """
    Generate Italian social media post from article data using AI.
    
    Args:
        article_data: Dictionary containing article information
                     (title, url, summary, content, category, length)
    
    Returns:
        dict: Generated post data with content and metadata
        None: If generation fails after all retries
    """
    start_time = time.time()
    logger.info(f"🤖 Starting content generation for article: '{article_data['title']}'")
    logger.info(f"📊 Article metadata - Category: {article_data['category']}, Length: {article_data['length']} chars")
    
    # Initialize LLM interface using environment variables by default
    try:
        llm_interface = LLMInterface()
        logger.info("✅ LLM interface initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize LLM interface: {str(e)}")
        logger.error("💡 Primary suggestion: Check GEMINI_API_KEY in environment variables")
        logger.error("🔧 Troubleshooting steps:")
        logger.error("  1. Verify GEMINI_API_KEY is set in .env file")
        logger.error("  2. Check API key validity at ai.google.dev")
        logger.error("  3. Ensure API key has Gemini API access enabled")
        return None
    
    # Create the prompt
    user_prompt = create_content_generation_prompt(
        article_data['title'],
        article_data['url'],
        article_data['summary'],
        article_data['content']
    )
    logger.info(f"📝 Generated prompt for AI (length: {len(user_prompt)} chars)")
    
    # Retry logic for AI generation using configuration
    retry_attempts = telegram_config['retry_attempts']
    logger.info(f"🔄 Starting content generation with {retry_attempts} max attempts")
    
    for attempt in range(retry_attempts):
        attempt_start = time.time()
        logger.info(f"🎯 Content generation attempt {attempt + 1}/{retry_attempts}")
        
        try:
            # Generate content using LLM
            generated_content = llm_interface.generate_text(
                system_instruction=NERD_CURIOSITIES_SYSTEM_INSTRUCTION,
                user_query=user_prompt
            )
            
            attempt_duration = time.time() - attempt_start
            logger.info(f"⏱️ AI generation completed in {attempt_duration:.2f}s")
            
            if not generated_content or generated_content.startswith("An error occurred"):
                logger.warning(f"❌ AI generation returned empty/error response on attempt {attempt + 1}")
                logger.warning("💡 Primary suggestion: Check API quota and network connectivity")
                logger.warning("🔧 Possible causes: Rate limit, quota exceeded, or service unavailable")
                continue
            
            logger.info(f"📊 Generated content length: {len(generated_content)} chars")
            
            # Validate generated content
            validation_result = validate_generated_post(generated_content)
            
            if validation_result['is_valid']:
                total_duration = time.time() - start_time
                logger.info(f"✅ Generated content passed validation in {total_duration:.2f}s total")
                
                hashtags = extract_hashtags(generated_content)
                logger.info(f"🏷️ Extracted {len(hashtags)} hashtags: {hashtags}")
                
                return {
                    'content': generated_content.strip(),
                    'article_title': article_data['title'],
                    'article_url': article_data['url'],
                    'category': article_data['category'],
                    'length': len(generated_content.strip()),
                    'hashtags': hashtags,
                    'generated_at': datetime.now()
                }
            else:
                logger.warning(f"❌ Generated content failed validation: {validation_result['reason']}")
                logger.warning(f"💡 Suggestion: Content issue - {validation_result['reason']}")
                logger.debug(f"📄 Generated content preview: {generated_content[:100]}...")
                continue
                
        except Exception as e:
            attempt_duration = time.time() - attempt_start
            logger.error(f"❌ Error in content generation attempt {attempt + 1} after {attempt_duration:.2f}s: {str(e)}")
            logger.error("💡 Suggestion: Check API connectivity and rate limits")
            continue
    
    total_duration = time.time() - start_time
    logger.error(f"❌ Failed to generate valid content after {retry_attempts} attempts in {total_duration:.2f}s")
    logger.error("💡 Suggestion: Try again later or check article content quality")
    return None


def validate_generated_post(content: str) -> dict:
    """
    Validate the generated post content against requirements.
    
    Args:
        content: Generated post content to validate
        
    Returns:
        dict: Validation result with is_valid (bool) and reason (str)
    """
    logger.info("🔍 Starting comprehensive content validation")
    logger.debug(f"📊 Content to validate: {len(content) if content else 0} chars")
    
    if not content or not content.strip():
        logger.warning("❌ Validation failed: Empty or whitespace-only content")
        logger.warning("💡 Suggestion: Check AI generation parameters and system instruction")
        return {'is_valid': False, 'reason': 'Empty content'}
    
    content = content.strip()
    content_length = len(content)
    
    # Check length requirements - using reasonable defaults if not configured
    post_length_min = 50  # Minimum reasonable post length
    post_length_max = 450  # Maximum from system instruction
    
    logger.info(f"📏 Content length: {content_length} chars (valid range: {post_length_min}-{post_length_max})")
    
    if content_length < post_length_min:
        logger.warning(f"❌ Validation failed: Content too short ({content_length} < {post_length_min})")
        return {
            'is_valid': False, 
            'reason': f'Content too short: {content_length} chars (min: {post_length_min})'
        }
    
    if content_length > post_length_max:
        logger.warning(f"❌ Validation failed: Content too long ({content_length} > {post_length_max})")
        return {
            'is_valid': False, 
            'reason': f'Content too long: {content_length} chars (max: {post_length_max})'
        }
    
    # Check for basic Italian content indicators
    italian_indicators = ['è', 'à', 'ì', 'ò', 'ù', 'che', 'del', 'della', 'di', 'da', 'in', 'con', 'per']
    found_indicators = [indicator for indicator in italian_indicators if indicator in content.lower()]
    has_italian = len(found_indicators) > 0
    
    if not has_italian:
        logger.warning("❌ Validation failed: Content does not appear to be in Italian")
        logger.warning("💡 Primary suggestion: Check AI system instruction language settings")
        logger.warning("🔧 Troubleshooting: Verify NERD_CURIOSITIES_SYSTEM_INSTRUCTION specifies Italian output")
        return {'is_valid': False, 'reason': 'Content does not appear to be in Italian'}
    
    logger.info(f"✅ Italian language indicators detected: {len(found_indicators)} matches ({', '.join(found_indicators[:3])}...)")
    
    # Check for hashtags
    if '#' not in content:
        logger.warning("❌ Validation failed: No hashtags found in generated content")
        logger.warning("💡 Primary suggestion: Check AI system instruction for hashtag requirements")
        logger.warning("🔧 Troubleshooting: Verify system instruction includes '3-5 hashtag rilevanti'")
        return {'is_valid': False, 'reason': 'No hashtags found in content'}
    
    hashtag_count = content.count('#')
    logger.info(f"🏷️ Hashtags detected: {hashtag_count}")
    
    # Check for emoji (basic check)
    # Most emojis are in Unicode ranges, but this is a simple check
    emoji_chars = [char for char in content if ord(char) > 127]
    has_emoji = len(emoji_chars) > 0
    
    if not has_emoji:
        logger.warning('⚠️ No emoji detected in content, but not failing validation')
        logger.warning("💡 Suggestion: Consider updating AI prompt to encourage emoji usage for engagement")
    else:
        logger.info(f"😊 Emoji detected in content: {len(emoji_chars)} emoji characters")
    
    logger.info("✅ Content passed all critical validation checks")
    logger.info(f"📊 Final validation summary: Length OK, Italian OK, Hashtags OK, Emoji: {'Yes' if has_emoji else 'No'}")
    return {'is_valid': True, 'reason': 'Content passed all validation checks'}


def extract_hashtags(content: str) -> list:
    """
    Extract hashtags from the generated content.
    
    Args:
        content: Generated post content
        
    Returns:
        list: List of hashtags found in the content
    """
    import re
    
    logger.debug("🏷️ Extracting hashtags from content")
    
    # Find all hashtags in the content
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, content)
    
    # Log hashtag analysis for business logic tracking
    if hashtags:
        unique_hashtags = list(set(hashtags))
        logger.debug(f"🔍 Found {len(hashtags)} hashtags ({len(unique_hashtags)} unique): {hashtags}")
        if len(hashtags) != len(unique_hashtags):
            logger.debug(f"📊 Duplicate hashtags detected: {len(hashtags) - len(unique_hashtags)} duplicates")
    else:
        logger.debug("🔍 No hashtags found in content")
    
    return hashtags


def publish_to_telegram(post_content: str) -> dict:
    """
    Publish content to Telegram with retry logic.
    
    Args:
        post_content: The formatted post content to publish
        
    Returns:
        dict: Result with 'success' (bool), 'response' (dict), and 'error' (str) keys
    """
    start_time = time.time()
    logger.info("📤 Starting Telegram publishing process")
    logger.info(f"📊 Content length: {len(post_content)} chars")
    
    # Initialize Telegram interface using environment variables by default
    try:
        telegram_interface = TelegramInterface(**telegram_config)
        logger.info("✅ Telegram interface initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Telegram interface: {str(e)}")
        logger.error("💡 Primary suggestion: Check TELEGRAM_BOT_TOKEN and CHANNEL_ID in environment variables")
        logger.error("🔧 Troubleshooting steps:")
        logger.error("  1. Verify TELEGRAM_BOT_TOKEN is set and valid")
        logger.error("  2. Check CHANNEL_ID format (should start with -100 for supergroups)")
        logger.error("  3. Ensure bot is added to target channel with posting permissions")
        return {
            'success': False,
            'response': None,
            'error': f"Telegram interface initialization failed: {str(e)}"
        }
    
    # Retry logic for Telegram publishing using configuration
    retry_attempts = telegram_config['retry_attempts']
    retry_delay = telegram_config['retry_delay']
    
    logger.info(f"🔄 Starting publication with {retry_attempts} max attempts, {retry_delay}s delay")
    
    for attempt in range(retry_attempts):
        attempt_start = time.time()
        logger.info(f"📡 Telegram publish attempt {attempt + 1}/{retry_attempts}")
        
        try:
            # Send message to Telegram
            response = telegram_interface.send_message(post_content)
            
            attempt_duration = time.time() - attempt_start
            logger.info(f"⏱️ Telegram API call completed in {attempt_duration:.2f}s")
            
            # Check if the response indicates success
            if response and response.get('ok', False):
                total_duration = time.time() - start_time
                message_id = response.get('result', {}).get('message_id', 'unknown')
                logger.info(f"✅ Successfully published to Telegram in {total_duration:.2f}s")
                logger.info(f"📨 Message ID: {message_id}")
                return {
                    'success': True,
                    'response': response,
                    'error': None
                }
            else:
                error_msg = response.get('description', 'Unknown error') if response else 'No response received'
                error_code = response.get('error_code', 'unknown') if response else 'no_response'
                logger.warning(f"❌ Telegram API returned error on attempt {attempt + 1}: {error_msg} (code: {error_code})")
                
                # Provide specific suggestions based on error codes
                if error_code == 429:
                    logger.warning("💡 Suggestion: Rate limit exceeded, increase retry delay")
                elif error_code == 400:
                    logger.warning("💡 Suggestion: Check message content format and length")
                elif error_code == 401:
                    logger.warning("💡 Suggestion: Check TELEGRAM_BOT_TOKEN validity")
                elif error_code == 403:
                    logger.warning("💡 Suggestion: Check bot permissions in target channel")
                
                # If this is not the last attempt, wait before retrying
                if attempt < retry_attempts - 1:
                    logger.info(f"⏳ Waiting {retry_delay} seconds before retry...")
                    time.sleep(retry_delay)
                    continue
                else:
                    return {
                        'success': False,
                        'response': response,
                        'error': f"Telegram API error: {error_msg}"
                    }
                    
        except Exception as e:
            attempt_duration = time.time() - attempt_start
            error_msg = f"Exception during Telegram publish: {str(e)}"
            logger.error(f"❌ Error on attempt {attempt + 1} after {attempt_duration:.2f}s: {error_msg}")
            logger.error("💡 Suggestion: Check network connectivity and API endpoint availability")
            
            # If this is not the last attempt, wait before retrying
            if attempt < retry_attempts - 1:
                logger.info(f"⏳ Waiting {retry_delay} seconds before retry...")
                time.sleep(retry_delay)
                continue
            else:
                return {
                    'success': False,
                    'response': None,
                    'error': error_msg
                }
    
    # This should never be reached, but just in case
    total_duration = time.time() - start_time
    logger.error(f"❌ Failed to publish after {retry_attempts} attempts in {total_duration:.2f}s")
    return {
        'success': False,
        'response': None,
        'error': f"Failed to publish after {retry_attempts} attempts"
    }


def publish_and_update_database(post_data: dict) -> dict:
    """
    Publish content to Telegram and update database only after successful posting.
    Handles rollback scenarios for failed posts.
    
    Args:
        post_data: Dictionary containing post content and article metadata
        
    Returns:
        dict: Result with 'success' (bool), 'telegram_response' (dict), 'db_updated' (bool), and 'error' (str) keys
    """
    start_time = time.time()
    logger.info("🚀 Starting publish and database update process")
    logger.info(f"📄 Article: '{post_data['article_title']}'")
    logger.info(f"🏷️ Category: {post_data['category']}")
    
    # Step 1: Attempt to publish to Telegram
    logger.info("📤 Step 1: Publishing to Telegram")
    publish_result = publish_to_telegram(post_data['content'])
    
    if not publish_result['success']:
        logger.error(f"❌ Telegram publishing failed: {publish_result['error']}")
        logger.error("💡 Suggestion: Check network connectivity and bot configuration")
        return {
            'success': False,
            'telegram_response': publish_result['response'],
            'db_updated': False,
            'error': f"Telegram publishing failed: {publish_result['error']}"
        }
    
    logger.info("✅ Successfully published to Telegram, proceeding to database update")
    
    # Step 2: Update database only after successful Telegram publish
    logger.info("💾 Step 2: Updating database")
    try:
        # Get database path using path manager and configuration
        db_path = path_manager.get_database_path('nerd_curiosities.sqlite3', paths_config['databases_subdir'])
        logger.info(f"📂 Database path: {db_path}")
        
        with ContentDatabase(db_path, 'ArticleHistory') as db:
            db_success = db.mark_content_posted(
                content_title=post_data['article_title'],
                content_url=post_data['article_url'],
                category=post_data['category'],
                content_type='article',
                module_name='weekly_nerd_curiosities'
            )
            
            if db_success:
                total_duration = time.time() - start_time
                logger.info(f"✅ Successfully marked article '{post_data['article_title']}' as posted in database")
                logger.info(f"⏱️ Complete process finished in {total_duration:.2f}s")
                return {
                    'success': True,
                    'telegram_response': publish_result['response'],
                    'db_updated': True,
                    'error': None
                }
            else:
                # Database update failed, but Telegram post was successful
                # This is a partial failure - the post is live but not tracked
                error_msg = f"Telegram post successful but database update failed for article '{post_data['article_title']}'"
                logger.error(f"❌ {error_msg}")
                logger.error("💡 Suggestion: Manually add database entry to prevent duplicate posts")
                logger.error(f"💡 Manual entry details: Title='{post_data['article_title']}', URL='{post_data['article_url']}', Category='{post_data['category']}'")
                return {
                    'success': False,
                    'telegram_response': publish_result['response'],
                    'db_updated': False,
                    'error': error_msg
                }
                
    except Exception as e:
        # Database operation failed, but Telegram post was successful
        error_msg = f"Telegram post successful but database error occurred: {str(e)}"
        logger.error(f"❌ {error_msg}")
        logger.error("💡 Suggestion: Check database file permissions and disk space")
        logger.error(f"💡 Manual entry needed: Title='{post_data['article_title']}', URL='{post_data['article_url']}', Category='{post_data['category']}'")
        return {
            'success': False,
            'telegram_response': publish_result['response'],
            'db_updated': False,
            'error': error_msg
        }

def get_random_nerd_article():
    """
    Discover a random nerd-related article with duplicate checking and retry logic.
    
    Returns:
        dict: Article information with title, url, content, and category
        None: If no suitable article found after max retries
    """
    start_time = time.time()
    logger.info("📥 Starting article discovery process")
    logger.info(f"🎯 Available categories: {len(NERD_CATEGORIES)} ({', '.join(NERD_CATEGORIES[:3])}...)")
    
    # Initialize Wikipedia interface using environment variables by default
    try:
        wiki_interface = WikipediaInterface()
        logger.info("✅ Wikipedia interface initialized successfully")
    except Exception as e:
        logger.error(f"❌ Failed to initialize Wikipedia interface: {str(e)}")
        logger.error("💡 Primary suggestion: Check network connectivity and Wikipedia API availability")
        logger.error("🔧 Troubleshooting steps:")
        logger.error("  1. Verify internet connectivity to en.wikipedia.org")
        logger.error("  2. Check if Wikipedia API is accessible (https://en.wikipedia.org/api/rest_v1/)")
        logger.error("  3. Ensure no firewall blocking Wikipedia API requests")
        return None
    
    # Initialize database
    db_path = path_manager.get_database_path('nerd_curiosities.sqlite3', paths_config['databases_subdir'])
    logger.info(f"💾 Using database: {db_path}")
    
    with ContentDatabase(db_path, 'ArticleHistory') as db:
        
        # Use reasonable defaults for retry logic
        max_retries = 10  # Reasonable number of attempts
        min_article_length = 500  # Minimum article length for good content
        
        logger.info(f"🔄 Starting discovery with {max_retries} max attempts")
        logger.info(f"📏 Minimum article length: {min_article_length} chars")
        
        # Track statistics for better logging
        categories_tried = set()
        articles_checked = 0
        duplicate_count = 0
        short_article_count = 0
        
        for attempt in range(max_retries):
            attempt_start = time.time()
            logger.info(f"🎲 Article discovery attempt {attempt + 1}/{max_retries}")
            
            try:
                # Select random category
                selected_category = random.choice(NERD_CATEGORIES)
                categories_tried.add(selected_category)
                logger.info(f"🏷️ Selected category: {selected_category} (attempt {attempt + 1})")
                logger.info(f"📊 Category selection criteria: Random from {len(NERD_CATEGORIES)} available categories")
                
                # Get random article from category
                logger.debug(f"🔍 Searching for articles in category: {selected_category}")
                article_info = wiki_interface.get_random_article_from_category(selected_category)
                
                if not article_info:
                    logger.warning(f"❌ No article found in category {selected_category}")
                    logger.warning("💡 Possible causes: Category may be empty, API issue, or network problem")
                    logger.warning("🔧 Suggestion: Verify category exists on Wikipedia and contains articles")
                    continue
                
                article_title = article_info['title']
                articles_checked += 1
                logger.info(f"📄 Found article: '{article_title}'")
                
                # Check if article already posted
                logger.debug(f"🔍 Checking if article '{article_title}' was previously posted")
                if db.is_content_posted(article_title, 'article'):
                    duplicate_count += 1
                    logger.info(f"🔄 Article '{article_title}' already posted (duplicate #{duplicate_count})")
                    logger.debug("📊 Content filtering: Skipping duplicate article")
                    continue
                
                logger.debug("✅ Article not previously posted, proceeding with content fetch")
                
                # Get full article content
                content_fetch_start = time.time()
                logger.info("📖 Fetching article content...")
                article_content = wiki_interface.get_article_content(article_title)
                
                if not article_content:
                    content_fetch_duration = time.time() - content_fetch_start
                    logger.warning(f"❌ Could not fetch content for '{article_title}' after {content_fetch_duration:.2f}s")
                    logger.warning("💡 Possible causes: Article may be redirect, disambiguation page, or API issue")
                    logger.warning("🔧 Troubleshooting steps:")
                    logger.warning("  1. Check Wikipedia API status and article URL validity")
                    logger.warning("  2. Verify article exists and is not a redirect/disambiguation")
                    logger.warning("  3. Check network connectivity to Wikipedia API")
                    continue
                
                content_fetch_duration = time.time() - content_fetch_start
                logger.debug(f"⏱️ Content fetched in {content_fetch_duration:.2f}s")
                
                # Validate content length
                content_length = article_content['length']
                logger.info(f"📊 Article length: {content_length} chars")
                logger.debug(f"📏 Content filtering: Checking length against minimum {min_article_length} chars")
                
                if content_length < min_article_length:
                    short_article_count += 1
                    logger.info(f"📏 Article '{article_title}' too short ({content_length} < {min_article_length})")
                    logger.debug("📊 Content filtering: Article rejected due to insufficient length")
                    continue
                
                logger.debug("✅ Article length validation passed")
                
                # Article is suitable
                attempt_duration = time.time() - attempt_start
                total_duration = time.time() - start_time
                logger.info(f"✅ Found suitable article: '{article_title}' in {attempt_duration:.2f}s")
                logger.info(f"📊 Discovery stats - Articles checked: {articles_checked}, Duplicates: {duplicate_count}, Too short: {short_article_count}")
                logger.info(f"🏷️ Categories tried: {len(categories_tried)} ({', '.join(list(categories_tried)[:3])}...)")
                logger.info(f"⏱️ Total discovery time: {total_duration:.2f}s")
                
                return {
                    'title': article_content['title'],
                    'url': article_content['url'],
                    'summary': article_content['summary'],
                    'content': article_content['content'],
                    'category': selected_category,
                    'length': article_content['length']
                }
                
            except Exception as e:
                attempt_duration = time.time() - attempt_start
                logger.error(f"❌ Error in attempt {attempt + 1} after {attempt_duration:.2f}s: {str(e)}")
                logger.error("💡 Suggestion: Check Wikipedia API connectivity and rate limits")
                continue
        
        total_duration = time.time() - start_time
        logger.error(f"❌ Failed to find suitable article after {max_retries} attempts in {total_duration:.2f}s")
        logger.error(f"📊 Final stats - Articles checked: {articles_checked}, Duplicates: {duplicate_count}, Too short: {short_article_count}")
        logger.error(f"🏷️ Categories tried: {len(categories_tried)} out of {len(NERD_CATEGORIES)} available")
        logger.error("💡 Suggestion: Consider expanding categories or reducing minimum length requirements")
        return None


def main():
    """
    Main entry point for the weekly nerd curiosities module.
    Initializes all interfaces and database connection, orchestrates the complete 
    article discovery to posting workflow with comprehensive error handling and logging.
    """
    start_time = time.time()
    
    logger.info("🚀 Starting weekly_nerd_curiosities module")
    logger.info(f"📋 Module purpose: Nerd culture content discovery and generation for Italian Telegram channel")
    logger.info(f"🕐 Module started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"🎯 Target: Discover, generate, and publish nerd culture curiosities")
    
    try:
        # Phase 1: Configuration and Setup
        logger.info("🔧 Phase 1: Configuration and Setup")
        
        # Validate configuration
        logger.info("🔍 Validating module configuration...")
        config_valid = config.validate_configuration()
        logger.info(f"📋 Configuration validation: {'✅ Valid' if config_valid else '❌ Invalid'}")
        
        if not config_valid:
            logger.warning("⚠️ Configuration validation failed, but continuing with defaults")
            logger.warning("💡 Suggestion: Check .env file for missing environment variables")
            logger.warning("🔧 Required variables: GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, CHANNEL_ID")
        
        # Log configuration info with performance context
        db_path = path_manager.get_database_path('nerd_curiosities.sqlite3', paths_config['databases_subdir'])
        logger.info(f"💾 Database path: {db_path}")
        logger.info(f"📁 Project root: {path_manager.get_project_root()}")
        logger.info(f"📝 Log directory: {log_dir}")
        logger.info(f"🏷️ Available categories: {len(NERD_CATEGORIES)} ({', '.join(NERD_CATEGORIES[:3])}...)")
        logger.info(f"📊 Content selection strategy: Random article from random category with duplicate filtering")
        logger.info(f"🌐 Target language: Italian (sistema di istruzioni AI configurato per contenuti italiani)")
        
        # Log operational parameters
        retry_attempts = telegram_config['retry_attempts']
        retry_delay = telegram_config['retry_delay']
        
        logger.info(f"🔄 Max retries for article discovery: 10")  # Using hardcoded reasonable default
        logger.info(f"📡 Telegram retry attempts: {retry_attempts}")
        logger.info(f"⏳ Telegram retry delay: {retry_delay}s")
        logger.info(f"📏 Post length constraints: 50-450 chars")  # Using hardcoded reasonable defaults
        logger.info(f"📖 Minimum article length: 500 chars")  # Using hardcoded reasonable default
        
        # Initialize database connection and verify schema
        logger.info("💾 Initializing database connection and verifying schema...")
        db_init_start = time.time()
        
        with ContentDatabase(db_path, 'ArticleHistory') as db:
            # Test database connection and gather metrics
            recent_posts = db.get_recent_posts(7, 'article')  # Last 7 days
            db_init_duration = time.time() - db_init_start
            logger.info(f"✅ Database connected successfully in {db_init_duration:.2f}s")
            logger.info(f"📊 Recent posts in last 7 days: {len(recent_posts)}")
            logger.info(f"🗃️ Database table: ArticleHistory (tracks posted content to prevent duplicates)")
            
            # Log recent activity for business logic context
            if recent_posts:
                logger.info("📋 Recent posting activity:")
                for post in recent_posts[:3]:  # Show last 3 posts
                    logger.info(f"  📄 {post.get('content_title', 'Unknown')} ({post.get('category', 'Unknown')})")
            
            # Log category statistics with performance context
            category_stats = db.get_category_stats('article')
            if category_stats:
                total_posts = sum(category_stats.values())
                logger.info(f"📈 Total historical posts: {total_posts}")
                logger.info("🏷️ Category distribution in database:")
                for category, count in sorted(category_stats.items(), key=lambda x: x[1], reverse=True)[:5]:  # Top 5
                    percentage = (count / total_posts) * 100 if total_posts > 0 else 0
                    logger.info(f"  📊 {category}: {count} posts ({percentage:.1f}%)")
                
                # Log category balance for content strategy
                if len(category_stats) > 5:
                    logger.info(f"  📊 ... and {len(category_stats) - 5} more categories")
                
                # Identify underrepresented categories
                avg_posts_per_category = total_posts / len(NERD_CATEGORIES)
                underrepresented = [cat for cat in NERD_CATEGORIES if category_stats.get(cat, 0) < avg_posts_per_category * 0.5]
                if underrepresented:
                    logger.info(f"📊 Underrepresented categories ({len(underrepresented)}): {', '.join(underrepresented[:3])}...")
            else:
                logger.info("📊 No previous posts found in database (fresh start)")
                logger.info("💡 All categories are equally available for first post")
        
        setup_duration = time.time() - start_time
        logger.info(f"✅ Phase 1 completed in {setup_duration:.2f}s")
        
    except Exception as e:
        setup_duration = time.time() - start_time
        logger.error(f"❌ weekly_nerd_curiosities initialization failed after {setup_duration:.2f}s: {str(e)}")
        logger.error("💡 Primary suggestion: Check environment variables (.env file) and database permissions")
        logger.error("🔧 Detailed troubleshooting steps:")
        logger.error("  1. Verify .env file exists and contains: GEMINI_API_KEY, TELEGRAM_BOT_TOKEN, CHANNEL_ID")
        logger.error("  2. Check database file permissions and available disk space")
        logger.error("  3. Ensure log directory is writable by current user")
        logger.error("  4. Verify network connectivity for API access")
        logger.error("🚫 Critical initialization failure - module cannot continue")
        logger.exception("🔍 Full initialization error traceback:")
        return
    
    try:
        # Phase 2: Article Discovery
        logger.info("📥 Phase 2: Article Discovery")
        phase2_start = time.time()
        
        article = get_random_nerd_article()
        
        if not article:
            phase2_duration = time.time() - phase2_start
            logger.error(f"❌ Failed to discover suitable article after {phase2_duration:.2f}s")
            logger.error("💡 Primary suggestion: Try running again or check Wikipedia API availability")
            logger.error("🔧 Systematic troubleshooting steps:")
            logger.error("  1. Check internet connectivity and Wikipedia API status (https://en.wikipedia.org/api/rest_v1/)")
            logger.error("  2. Verify categories contain sufficient unposted articles")
            logger.error("  3. Consider reducing minimum article length requirement (current: 500 chars)")
            logger.error("  4. Check if too many articles are already posted (database cleanup may be needed)")
            logger.error("  5. Verify category names are valid Wikipedia categories")
            logger.error("🚫 Article discovery failure - cannot proceed without content")
            return
        
        phase2_duration = time.time() - phase2_start
        logger.info(f"✅ Phase 2 completed in {phase2_duration:.2f}s")
        logger.info(f"📄 Successfully discovered article: '{article['title']}'")
        logger.info(f"🏷️ Category: {article['category']}")
        logger.info(f"📊 Content length: {article['length']} characters")
        logger.info(f"🔗 URL: {article['url']}")
        
        # Phase 3: Content Generation
        logger.info("🤖 Phase 3: Content Generation")
        phase3_start = time.time()
        
        post_data = generate_nerd_post(article)
        
        if not post_data:
            phase3_duration = time.time() - phase3_start
            logger.error(f"❌ Failed to generate valid content after {phase3_duration:.2f}s")
            logger.error("💡 Primary suggestion: Check AI API quota and article content quality")
            logger.error("🔧 Systematic troubleshooting steps:")
            logger.error("  1. Verify GEMINI_API_KEY is valid and has quota remaining")
            logger.error("  2. Check network connectivity to Google AI services (ai.google.dev)")
            logger.error("  3. Review article content quality (may be too technical/sparse for AI processing)")
            logger.error("  4. Consider adjusting AI system instruction for better Italian content generation")
            logger.error("  5. Check if article content contains sufficient nerd culture elements")
            logger.error("🚫 Content generation failure - cannot proceed without valid post content")
            return
        
        phase3_duration = time.time() - phase3_start
        logger.info(f"✅ Phase 3 completed in {phase3_duration:.2f}s")
        logger.info(f"📝 Successfully generated post content ({post_data['length']} chars)")
        logger.info(f"🏷️ Hashtags found: {len(post_data['hashtags'])} - {post_data['hashtags']}")
        logger.debug(f"📄 Generated content preview: {post_data['content'][:100]}...")
        
        # Phase 4: Publication and Database Update
        logger.info("📤 Phase 4: Publication and Database Update")
        phase4_start = time.time()
        
        publish_result = publish_and_update_database(post_data)
        
        phase4_duration = time.time() - phase4_start
        
        if publish_result['success']:
            logger.info(f"✅ Phase 4 completed in {phase4_duration:.2f}s")
            logger.info("🎉 Successfully published to Telegram and updated database")
            logger.info(f"💾 Article '{post_data['article_title']}' marked as posted")
        else:
            logger.error(f"❌ Phase 4 failed after {phase4_duration:.2f}s: {publish_result['error']}")
            
            # If Telegram was successful but database failed, log the specific issue
            if publish_result['telegram_response'] and not publish_result['db_updated']:
                logger.warning("⚠️ CRITICAL: Post was published to Telegram but not tracked in database!")
                logger.warning(f"🔧 Manual database entry required for: {post_data['article_title']}")
                logger.warning("💡 Immediate action needed: Run database repair script or manually add entry")
                logger.warning("📋 Manual entry details for database repair:")
                logger.warning(f"  Title: {post_data['article_title']}")
                logger.warning(f"  URL: {post_data['article_url']}")
                logger.warning(f"  Category: {post_data['category']}")
                logger.warning(f"  Content Type: article")
                logger.warning(f"  Module: weekly_nerd_curiosities")
                logger.warning("⚠️ Risk: Article may be reposted if database not updated")
            else:
                logger.error("🔧 Complete failure troubleshooting steps:")
                logger.error("  1. Check Telegram bot token validity and channel permissions")
                logger.error("  2. Verify network connectivity to api.telegram.org")
                logger.error("  3. Check database file permissions and available disk space")
                logger.error("  4. Ensure bot is added to target channel with posting permissions")
                logger.error("  5. Verify CHANNEL_ID format (should start with -100 for supergroups)")
            
            return
        
        # Module completion summary with comprehensive metrics
        total_duration = time.time() - start_time
        logger.info("🎉 weekly_nerd_curiosities completed successfully")
        logger.info(f"⏱️ Total execution time: {total_duration:.2f}s")
        logger.info(f"🕐 Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"📊 Performance breakdown:")
        logger.info(f"  🔧 Setup & Config: {setup_duration:.2f}s ({(setup_duration/total_duration)*100:.1f}%)")
        logger.info(f"  📥 Article Discovery: {phase2_duration:.2f}s ({(phase2_duration/total_duration)*100:.1f}%)")
        logger.info(f"  🤖 Content Generation: {phase3_duration:.2f}s ({(phase3_duration/total_duration)*100:.1f}%)")
        logger.info(f"  📤 Publication & DB Update: {phase4_duration:.2f}s ({(phase4_duration/total_duration)*100:.1f}%)")
        logger.info(f"📈 Success metrics: Article '{post_data['article_title']}' from {post_data['category']} category")
        logger.info(f"📝 Content metrics: {post_data['length']} chars, {len(post_data['hashtags'])} hashtags")
        
    except Exception as e:
        total_duration = time.time() - start_time
        logger.error(f"❌ CRITICAL ERROR in Weekly Nerd Curiosities module after {total_duration:.2f}s: {str(e)}")
        logger.error(f"🕐 Error occurred at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        logger.error("💡 Primary suggestion: Check logs above for specific error context and retry")
        logger.error("🔧 General recovery steps:")
        logger.error("  1. Wait 5-10 minutes and retry (may be temporary API issue)")
        logger.error("  2. Check all environment variables are properly set")
        logger.error("  3. Verify network connectivity and API service status")
        logger.error("  4. Ensure sufficient disk space and file permissions")
        logger.error("  5. Check if error is reproducible or intermittent")
        logger.exception("🔍 Full error traceback for debugging:")
        raise

if __name__ == "__main__":
    main()