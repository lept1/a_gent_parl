from src.conf.config_manager import ConfigManager
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager

import datetime as dt
import time

def main():
    module_name = 'monthly_psnews'
    
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
    
    # Initialize utilities with configuration
    enhanced_logger = EnhancedLogger(module_name, log_dir, logging_config)
    logger = enhanced_logger.setup_logging()
    
    # Module startup logging
    logger.info("🚀 Starting monthly_psnews module")
    logger.info("📋 Configuration: PS Plus monthly games summary generation")
    
    start_time = time.time()
    current_phase = "initialization"
    
    try:
        # Phase 1: Setup and Configuration
        logger.info("🔧 Initializing module components")
        current_phase = "setup"
        
        # Ensure data directories exist
        path_manager.ensure_directory_exists(paths_config['data_root'])
        
        # Get module-specific configuration values
        content_length_min = module_config.get('content_length_min', 800)
        content_length_max = module_config.get('content_length_max', 1200)
        include_free_games = module_config.get('include_free_games', True)
        
        logger.info(f"📊 Module config - Content length: {content_length_min}-{content_length_max} chars, Include free games: {include_free_games}")
        
        # Generate current month context
        this_month = dt.datetime.now().strftime("%B %Y")
        logger.info(f"📅 Target month for PS Plus games: {this_month}")
        
        logger.info("✅ Module initialization completed")
        
        # Phase 2: Content Query Preparation
        logger.info("📝 Preparing content query for PS Plus games")
        current_phase = "query_preparation"
        
        query = "What are the monthly games on PS Plus Essential for " + this_month + "?"
        logger.info(f"🔍 Query prepared: '{query[:50]}...' (length: {len(query)} chars)")
        
        system_instruction = f"""
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN. 
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

#PSPlus <MONTH> <YEAR> <EMOTICON VIDEOGAME>

<EMOTICON RELEVANT TO THE GAME 1> Game 1 <EMOTICON RELEVANT TO THE GAME 1>
<SHORT DESCRIPTION OF THE GAME 1, SHORT SUMMARY OF THE CRITICS OF THE GAME 1, DESCRIBE HOW MUCH POPULAR THE GAME IS>

<EMOTICON RELEVANT TO THE GAME 2> Game 2 <EMOTICON RELEVANT TO THE GAME 2>
<SHORT DESCRIPTION OF THE GAME 2, SHORT SUMMARY OF THE CRITICS OF THE GAME 2, DESCRIBE HOW MUCH POPULAR THE GAME 2 IS>

...

{"Include information about free games if available." if include_free_games else "Focus only on main PS Plus Essential games."}
Keep the content between {content_length_min} and {content_length_max} characters.
Do not include any other text or explanation.
"""
        logger.info(f"📋 System instruction configured (length: {len(system_instruction)} chars)")
        logger.info("✅ Content query preparation completed")
        
        # Phase 3: Content Generation
        logger.info("🤖 Starting AI content generation for PS Plus monthly summary")
        current_phase = "content_generation"
        
        generation_start = time.time()
        llm_interface = LLMInterface()  # Uses environment variables by default
        logger.info("🔗 LLM interface initialized successfully")
        
        logger.info("📡 Sending query to AI service for content generation")
        response = llm_interface.generate_text(system_instruction, query)
        generation_time = time.time() - generation_start
        
        # Content validation logging
        if response and len(response.strip()) > 0:
            logger.info(f"⏱️ Content generation completed in {generation_time:.2f}s")
            logger.info(f"📊 Performance: {len(response)} chars generated, {len(response)/generation_time:.0f} chars/sec")
            logger.info(f"📝 Content preview: '{response[:100]}...'")
            
            # Validate content structure
            if "#PSPlus" in response and this_month.split()[0] in response:
                logger.info("✅ Content validation passed: Contains required PS Plus header and month")
            else:
                logger.warning("⚠️ Content validation warning: Missing expected PS Plus format elements")
                
            # Validate content length against module configuration
            content_length = len(response)
            if content_length_min <= content_length <= content_length_max:
                logger.info(f"✅ Content length validation passed: {content_length} chars (target: {content_length_min}-{content_length_max})")
            else:
                logger.warning(f"⚠️ Content length validation warning: {content_length} chars (target: {content_length_min}-{content_length_max})")
                
            # Count game entries (rough estimation)
            game_count = response.count('🎮') + response.count('🕹️') + response.count('🎯')
            if game_count > 0:
                logger.info(f"📊 Estimated games in summary: {game_count}")
            else:
                logger.warning("⚠️ Content validation warning: No game emojis detected in content")
        else:
            logger.error("❌ Content generation failed: Empty or null response received")
            logger.error("💡 Suggestion: Check AI service availability and API key configuration")
            raise ValueError("Empty response from AI service")
            
        logger.info("✅ Content generation phase completed")
        
        # Phase 4: Publication
        logger.info("📤 Starting content publication to Telegram")
        current_phase = "publication"
        
        publication_start = time.time()
        telegram_bot = TelegramInterface(**telegram_config)  # Uses configuration with env var fallbacks
        logger.info("📱 Telegram interface initialized successfully")
        
        logger.info("📡 Sending PS Plus monthly summary to Telegram channel")
        telegram_bot.send_message(response)
        publication_time = time.time() - publication_start
        
        logger.info(f"⏱️ Publication completed in {publication_time:.2f}s")
        logger.info(f"📊 Performance: {len(response)} chars published in {publication_time:.2f}s")
        
        # Module completion
        total_time = time.time() - start_time
        logger.info(f"🎉 monthly_psnews completed successfully in {total_time:.2f}s")
        logger.info(f"📊 Summary: {this_month} games processed, {len(response)} chars generated and published")
        logger.info(f"⏱️ Performance breakdown: Generation={generation_time:.2f}s, Publication={publication_time:.2f}s")
        
    except Exception as e:
        error_time = time.time() - start_time
        logger.error(f"❌ monthly_psnews failed during {current_phase} phase after {error_time:.2f}s: {str(e)}")
        
        # Provide context-specific error suggestions
        if current_phase == "setup":
            logger.error("💡 Suggestion: Check configuration and data directory permissions")
        elif current_phase == "query_preparation":
            logger.error("💡 Suggestion: Verify date/time system configuration and query formatting")
        elif current_phase == "content_generation":
            logger.error("💡 Suggestion: Check AI service availability, API key, and network connectivity")
        elif current_phase == "publication":
            logger.error("💡 Suggestion: Verify Telegram bot token, channel permissions, and network connectivity")
        else:
            logger.error("💡 Suggestion: Check system logs and configuration files for detailed error information")
            
        logger.error(f"🔍 Error context: Processing PS Plus games for {this_month if 'this_month' in locals() else 'unknown month'}")
        raise

if __name__ == "__main__":
    main()