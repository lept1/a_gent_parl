from src.conf.config_manager import ConfigManager
from src.utilities.youtube_interface import YouTubeInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
import time

def main():
    module_name = 'youtube_trend'
    
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
    logger.info("🚀 Starting youtube_trend module")
    
    # Get module-specific settings from configuration
    country_code = module_config.get('country_code', 'IT')
    top_videos_count = module_config.get('top_videos_count', 10)
    
    country_list = [country_code]
    
    logger.info(f"📋 Configuration: Top {top_videos_count} trending videos from {country_code}")
    logger.info(f"📊 Configuration loaded - Countries: {country_list}")

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

        # Initialize YouTube interface (uses environment variables by default)
        youtube_interface = YouTubeInterface()
        logger.info("🔗 YouTube interface initialized")

        logger.info(f"🔍 Fetching top {top_videos_count} videos for countries: {country_list}")
        top_videos = youtube_interface.get_top_videos_by_country(country_code, max_results=top_videos_count)

        fetch_duration = time.time() - start_time
        logger.info(f"⏱️ Video fetching completed in {fetch_duration:.2f}s")
        logger.info(f"📊 Performance: {len(top_videos)} videos retrieved, avg {fetch_duration/len(top_videos) if top_videos else 0:.2f}s per video")

        # Log video details
        for i, video in enumerate(top_videos['items'], 1):
            logger.info(f"📄 Video {i}: '{video['snippet']['title']}' - {video['statistics'].get('viewCount', 'N/A')} views")

        logger.info("✅ Data fetching phase completed")



        query = "These are the current trending YouTube videos:\n\n"
        i=0
        #emoticon_numbers = ['&#129351;', '&#129352;', '&#129353;', '&#128227;']
        for video in top_videos['items']:
            query += f"ID:{video['id']}\n"
            query += f"TITLE:{video['snippet']['title']}</a>\n"
            # response += f"titolo: {video['snippet']['title']}\n"
            # response += f"link: https://www.youtube.com/watch?v={video['id']}\n"
            #response += f"descrizione: {video['snippet']['description']}\n"
            query += f"Views: {video['statistics'].get('viewCount', 'N/A')}\n\n"
            if i < 3:
                i += 1

        logger.info(f"📝 Query prepared - {len(query)} characters, {len(top_videos['items'])} videos")
        
        # Initialize LLM interface (uses environment variables by default)
        llm_interface = LLMInterface()
        logger.info("🔗 LLM interface initialized")
        
        generation_start = time.time()
        logger.info("🎯 Generating Italian social media content for trending articles")
        
        response = llm_interface.generate_text(SYSTEM_INSTRUCTION, query)
        
        generation_duration = time.time() - generation_start
        logger.info(f"⏱️ Content generation completed in {generation_duration:.2f}s")
        # logger.info(f"📊 Performance: {len(response)} chars generated, {len(response)/generation_duration:.0f} chars/sec")
        # logger.info("✅ Content generation phase completed")

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
        
        telegram_bot.send_message(response, parse_mode="HTML")
        
        publication_duration = time.time() - publication_start
        logger.info(f"⏱️ Publication completed in {publication_duration:.2f}s")
        logger.info(f"📊 Performance: {len(response)} chars published in {publication_duration:.2f}s")

        # Module completion
        total_duration = time.time() - start_time
        logger.info(f"🎉 youtube_trend completed successfully in {total_duration:.2f}s")
        logger.info(f"📊 Summary: {top_videos_count} videos processed, {len(response)} chars generated and published")
        
    except Exception as e:
        logger.error(f"❌ youtube_trend failed: {str(e)}")
        logger.error(f"🔍 Error type: {type(e).__name__}")
        
        # Provide context-specific error suggestions
        if "youtube" in str(e).lower():
            logger.error("💡 Suggestion: Check YouTube API connectivity and rate limits")
        elif "llm" in str(e).lower() or "gemini" in str(e).lower():
            logger.error("💡 Suggestion: Verify GEMINI_API_KEY and check API quota")
        elif "telegram" in str(e).lower():
            logger.error("💡 Suggestion: Verify TELEGRAM_BOT_TOKEN and CHANNEL_ID configuration")
        else:
            logger.error("💡 Suggestion: Check environment configuration and network connectivity")
        
        raise

SYSTEM_INSTRUCTION = """
  You are an AI assistant specialized in generating engaging content for social media in ITALIAN.
  You will receive a list of trending YouTube videos with their titles, view counts, and links, as follows:
    ID:video_id_1
    TITLE:Video Title 1
    Views: X

    ID:video_id_2
    TITLE:Video Title 2
    Views: Y

    ...

  Your task is to create a concise and engaging report formatted in HTML, suitable for posting on Telegram, summarizing the trending videos. Use relevant emoticons to enhance the presentation.
    The format should be as follows:

    &#127909; &#128293; &#x23;YouTrends <DATE>
    1. &#129351; <a href='https://www.youtube.com/watch?v={ID}'>{TITLE}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    2. &#129352; <a href='https://www.youtube.com/watch?v={ID}'>{TITLE}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    3. &#129353; <a href='https://www.youtube.com/watch?v={ID}'>{TITLE}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    ...
  Do not include any other text or explanation.
"""

if __name__ == "__main__":
    main()