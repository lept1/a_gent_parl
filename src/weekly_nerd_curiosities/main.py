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

# Add the parent directory to the path to import utilities
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..'))

import src.utilities.wikipedia_interface as wiki
import src.utilities.llm_interface as llm
import src.utilities.telegram_interface as telegram

# Import generic utilities
from src.utilities.config_manager import ConfigManager
from src.utilities.database_manager import ContentDatabase
from src.utilities.enhanced_logger import EnhancedLogger

# Initialize configuration manager
config_manager = ConfigManager('weekly_nerd_curiosities')

logger = EnhancedLogger(module_name='weekly_nerd_curiosities',config_manager=config_manager)
logger.setup_logging()

# Load nerd-specific categories
NERD_CATEGORIES = [
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
]

config_manager.load_categories(NERD_CATEGORIES)

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


# Initialize logger (will be properly configured in main)
logger = logging.getLogger(__name__)

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
    if len(article_content) > max_content_length:
        article_content = article_content[:max_content_length] + "..."
    
    prompt = f"""Titolo Articolo: {article_title}
URL Articolo: {article_url}
Riassunto Articolo: {article_summary}
Contenuto Articolo: {article_content}

Estrai le curiosità più interessanti e formattale come un post italiano per i social media."""
    
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
    logger.info(f"Generating content for article: {article_data['title']}")
    
    # Initialize LLM interface following existing project pattern
    llm_interface = llm.LLMInterface()
    
    # Create the prompt
    user_prompt = create_content_generation_prompt(
        article_data['title'],
        article_data['url'],
        article_data['summary'],
        article_data['content']
    )
    
    # Retry logic for AI generation
    telegram_retry_attempts = config_manager.get_validation_constant('telegram_retry_attempts')
    for attempt in range(telegram_retry_attempts):
        logger.info(f"Content generation attempt {attempt + 1}/{telegram_retry_attempts}")
        
        try:
            # Generate content using LLM
            generated_content = llm_interface.generate_text(
                system_instruction=NERD_CURIOSITIES_SYSTEM_INSTRUCTION,
                user_query=user_prompt
            )
            
            if not generated_content or generated_content.startswith("An error occurred"):
                logger.warning(f"AI generation failed on attempt {attempt + 1}")
                continue
            
            # Validate generated content
            validation_result = validate_generated_post(generated_content)
            
            if validation_result['is_valid']:
                logger.info("Generated content passed validation")
                
                return {
                    'content': generated_content.strip(),
                    'article_title': article_data['title'],
                    'article_url': article_data['url'],
                    'category': article_data['category'],
                    'length': len(generated_content.strip()),
                    'hashtags': extract_hashtags(generated_content),
                    'generated_at': datetime.now()
                }
            else:
                logger.warning(f"Generated content failed validation: {validation_result['reason']}")
                logger.debug(f"Generated content: {generated_content[:100]}...")
                continue
                
        except Exception as e:
            logger.error(f"Error in content generation attempt {attempt + 1}: {str(e)}")
            continue
    
    logger.error(f"Failed to generate valid content after {telegram_retry_attempts} attempts")
    return None


def validate_generated_post(content: str) -> dict:
    """
    Validate the generated post content against requirements.
    
    Args:
        content: Generated post content to validate
        
    Returns:
        dict: Validation result with is_valid (bool) and reason (str)
    """
    if not content or not content.strip():
        return {'is_valid': False, 'reason': 'Empty content'}
    
    content = content.strip()
    content_length = len(content)
    
    # Check length requirements
    post_length_min = config_manager.get_validation_constant('post_length_min')
    post_length_max = config_manager.get_validation_constant('post_length_max')
    
    if content_length < post_length_min:
        return {
            'is_valid': False, 
            'reason': f'Content too short: {content_length} chars (min: {post_length_min})'
        }
    
    if content_length > post_length_max:
        return {
            'is_valid': False, 
            'reason': f'Content too long: {content_length} chars (max: {post_length_max})'
        }
    
    # Check for basic Italian content indicators
    italian_indicators = ['è', 'à', 'ì', 'ò', 'ù', 'che', 'del', 'della', 'di', 'da', 'in', 'con', 'per']
    has_italian = any(indicator in content.lower() for indicator in italian_indicators)
    
    if not has_italian:
        return {'is_valid': False, 'reason': 'Content does not appear to be in Italian'}
    
    # Check for hashtags
    if '#' not in content:
        return {'is_valid': False, 'reason': 'No hashtags found in content'}
    
    # Check for emoji (basic check)
    # Most emojis are in Unicode ranges, but this is a simple check
    has_emoji = any(ord(char) > 127 for char in content)
    
    if not has_emoji:
        logger.warning('No emoji detected in content, but not failing validation')
    
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
    
    # Find all hashtags in the content
    hashtag_pattern = r'#\w+'
    hashtags = re.findall(hashtag_pattern, content)
    
    return hashtags


def publish_to_telegram(post_content: str) -> dict:
    """
    Publish content to Telegram with retry logic.
    
    Args:
        post_content: The formatted post content to publish
        
    Returns:
        dict: Result with 'success' (bool), 'response' (dict), and 'error' (str) keys
    """
    logger.info("Starting Telegram publishing process")
    
    # Initialize Telegram interface following existing project pattern
    telegram_interface = telegram.TelegramInterface()
    
    # Retry logic for Telegram publishing
    telegram_retry_attempts = config_manager.get_validation_constant('telegram_retry_attempts')
    telegram_retry_delay = config_manager.get_validation_constant('telegram_retry_delay')
    
    for attempt in range(telegram_retry_attempts):
        logger.info(f"Telegram publish attempt {attempt + 1}/{telegram_retry_attempts}")
        
        try:
            # Send message to Telegram
            response = telegram_interface.send_message(post_content)
            
            # Check if the response indicates success
            if response and response.get('ok', False):
                logger.info("Successfully published to Telegram")
                return {
                    'success': True,
                    'response': response,
                    'error': None
                }
            else:
                error_msg = response.get('description', 'Unknown error') if response else 'No response received'
                logger.warning(f"Telegram API returned error on attempt {attempt + 1}: {error_msg}")
                
                # If this is not the last attempt, wait before retrying
                if attempt < telegram_retry_attempts - 1:
                    logger.info(f"Waiting {telegram_retry_delay} seconds before retry...")
                    time.sleep(telegram_retry_delay)
                    continue
                else:
                    return {
                        'success': False,
                        'response': response,
                        'error': f"Telegram API error: {error_msg}"
                    }
                    
        except Exception as e:
            error_msg = f"Exception during Telegram publish: {str(e)}"
            logger.error(f"Error on attempt {attempt + 1}: {error_msg}")
            
            # If this is not the last attempt, wait before retrying
            if attempt < telegram_retry_attempts - 1:
                logger.info(f"Waiting {telegram_retry_delay} seconds before retry...")
                time.sleep(telegram_retry_delay)
                continue
            else:
                return {
                    'success': False,
                    'response': None,
                    'error': error_msg
                }
    
    # This should never be reached, but just in case
    return {
        'success': False,
        'response': None,
        'error': f"Failed to publish after {telegram_retry_attempts} attempts"
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
    logger.info("Starting publish and database update process")
    
    # Step 1: Attempt to publish to Telegram
    publish_result = publish_to_telegram(post_data['content'])
    
    if not publish_result['success']:
        logger.error(f"Failed to publish to Telegram: {publish_result['error']}")
        return {
            'success': False,
            'telegram_response': publish_result['response'],
            'db_updated': False,
            'error': f"Telegram publishing failed: {publish_result['error']}"
        }
    
    logger.info("Successfully published to Telegram, now updating database")
    
    # Step 2: Update database only after successful Telegram publish
    try:
        db_path = config_manager.get_module_database_path('nerd_curiosities.sqlite3')
        with ContentDatabase(db_path, 'ArticleHistory') as db:
            db_success = db.mark_content_posted(
                content_title=post_data['article_title'],
                content_url=post_data['article_url'],
                category=post_data['category'],
                content_type='article',
                module_name='weekly_nerd_curiosities'
            )
            
            if db_success:
                logger.info(f"Successfully marked article '{post_data['article_title']}' as posted in database")
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
                logger.error(error_msg)
                return {
                    'success': False,
                    'telegram_response': publish_result['response'],
                    'db_updated': False,
                    'error': error_msg
                }
                
    except Exception as e:
        # Database operation failed, but Telegram post was successful
        error_msg = f"Telegram post successful but database error occurred: {str(e)}"
        logger.error(error_msg)
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
    logger.info("Starting article discovery process")
    
    # Initialize Wikipedia interface following existing project pattern
    wiki_interface = wiki.WikipediaInterface()
    
    # Initialize database
    db_path = config_manager.get_module_database_path('nerd_curiosities.sqlite3')
    with ContentDatabase(db_path, 'ArticleHistory') as db:
        
        max_retries = config_manager.get_validation_constant('max_retries')
        min_article_length = config_manager.get_validation_constant('min_content_length')
        
        for attempt in range(max_retries):
            logger.info(f"Article discovery attempt {attempt + 1}/{max_retries}")
            
            try:
                # Select random category
                selected_category = config_manager.select_random_category()
                logger.info(f"Selected category: {selected_category}")
                
                # Get random article from category
                article_info = wiki_interface.get_random_article_from_category(selected_category)
                
                if not article_info:
                    logger.warning(f"No article found in category {selected_category}, retrying...")
                    continue
                
                article_title = article_info['title']
                logger.info(f"Found article: {article_title}")
                
                # Check if article already posted
                if db.is_content_posted(article_title, 'article'):
                    logger.info(f"Article '{article_title}' already posted, retrying...")
                    continue
                
                # Get full article content
                article_content = wiki_interface.get_article_content(article_title)
                
                if not article_content:
                    logger.warning(f"Could not fetch content for '{article_title}', retrying...")
                    continue
                
                # Validate content length
                if article_content['length'] < min_article_length:
                    logger.info(f"Article '{article_title}' too short ({article_content['length']} chars), retrying...")
                    continue
                
                # Article is suitable
                logger.info(f"Found suitable article: '{article_title}' ({article_content['length']} chars)")
                
                return {
                    'title': article_content['title'],
                    'url': article_content['url'],
                    'summary': article_content['summary'],
                    'content': article_content['content'],
                    'category': selected_category,
                    'length': article_content['length']
                }
                
            except Exception as e:
                logger.error(f"Error in attempt {attempt + 1}: {str(e)}")
                continue
        
        logger.error(f"Failed to find suitable article after {max_retries} attempts")
        return None


def main():
    """
    Main entry point for the weekly nerd curiosities module.
    Initializes all interfaces and database connection, orchestrates the complete 
    article discovery to posting workflow with comprehensive error handling and logging.
    """
    
    logger.info("=" * 60)
    logger.info("Starting Weekly Nerd Curiosities module")
    logger.info("=" * 60)
    
    try:
        
        # Validate configuration
        config_validation = config_manager.validate_configuration()
        logger.info("Configuration validation results:")
        for key, value in config_validation.items():
            logger.info(f"  {key}: {value}")
        
        # Log configuration info
        db_path = config_manager.get_module_database_path('nerd_curiosities.sqlite3')
        logger.info(f"Database path: {db_path}")
        logger.info(f"Environment file: {config_manager.get_env_path()}")
        logger.info(f"Log directory: {config_manager.get_log_directory()}")
        logger.info(f"Available categories: {len(config_manager.get_all_categories())}")
        logger.info(f"Max retries for article discovery: {config_manager.get_validation_constant('max_retries')}")
        logger.info(f"Telegram retry attempts: {config_manager.get_validation_constant('telegram_retry_attempts')}")
        logger.info(f"Post length constraints: {config_manager.get_validation_constant('post_length_min')}-{config_manager.get_validation_constant('post_length_max')} chars")
        logger.info(f"Minimum article length: {config_manager.get_validation_constant('min_content_length')} chars")
        
        # Initialize database connection and verify schema
        logger.info("Initializing database connection...")
        db_path = config_manager.get_module_database_path('nerd_curiosities.sqlite3')
        with ContentDatabase(db_path, 'ArticleHistory') as db:
            # Test database connection
            recent_posts = db.get_recent_posts(7, 'article')  # Last 7 days
            logger.info(f"Database connected successfully. Recent posts in last 7 days: {len(recent_posts)}")
            
            # Log category statistics
            category_stats = db.get_category_stats('article')
            if category_stats:
                logger.info("Category distribution in database:")
                for category, count in category_stats.items():
                    logger.info(f"  {category}: {count} posts")
            else:
                logger.info("No previous posts found in database")
        
        logger.info("Database initialization completed successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Weekly Nerd Curiosities module: {str(e)}")
        logger.error("Initialization failed, exiting...")
        return
    
    try:
        # Step 1: Discover suitable article
        article = get_random_nerd_article()
        
        if not article:
            logger.error("Failed to discover suitable article")
            return
        
        logger.info(f"Successfully discovered article: {article['title']}")
        logger.info(f"Category: {article['category']}")
        logger.info(f"Content length: {article['length']} characters")
        logger.info(f"URL: {article['url']}")
        
        # Step 2: Generate AI content
        post_data = generate_nerd_post(article)
        
        if not post_data:
            logger.error("Failed to generate valid content")
            return
        
        logger.info(f"Successfully generated post content ({post_data['length']} chars)")
        logger.info(f"Hashtags found: {post_data['hashtags']}")
        logger.debug(f"Generated content preview: {post_data['content'][:100]}...")
        
        # Step 3: Publish to Telegram and update database
        publish_result = publish_and_update_database(post_data)
        
        if publish_result['success']:
            logger.info("Successfully published to Telegram and updated database")
            logger.info(f"Article '{post_data['article_title']}' marked as posted")
        else:
            logger.error(f"Publishing process failed: {publish_result['error']}")
            
            # If Telegram was successful but database failed, log the specific issue
            if publish_result['telegram_response'] and not publish_result['db_updated']:
                logger.warning("IMPORTANT: Post was published to Telegram but not tracked in database!")
                logger.warning(f"Manual database entry may be needed for: {post_data['article_title']}")
            
            return
        
        logger.info("=" * 60)
        logger.info("Weekly Nerd Curiosities module completed successfully")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"CRITICAL ERROR in Weekly Nerd Curiosities module: {str(e)}")
        logger.error("=" * 60)
        logger.exception("Full error traceback:")
        raise

if __name__ == "__main__":
    main()