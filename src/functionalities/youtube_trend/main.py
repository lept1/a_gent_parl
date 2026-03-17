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
    country_list = module_config.get('country_code', 'IT')
    top_videos_count = module_config.get('top_videos_count', 10)
    

    try:
        logger.info(f"🔍 Fetching top {top_videos_count} videos for countries: {country_list}")
        #logger.info(f"📊 Configuration loaded - Countries: {country_list}")
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
        top_videos = dict()  # Initialize top_videos to ensure it's defined in case of early failure
        for country_code in country_list:
            video_country= youtube_interface.get_top_videos_by_country(country_code, max_results=top_videos_count)
            if video_country and 'items' in video_country:
                top_videos[country_code] = video_country
                logger.info(f"Fetched top videos for {country_code} - {[x['snippet']['title'] for x in top_videos[country_code]['items']]}")


        fetch_duration = time.time() - start_time
        logger.info(f"Video fetching completed in {fetch_duration:.2f}s")
        logger.info(f"Performance: {len(top_videos)} videos retrieved, avg {fetch_duration/len(top_videos) if top_videos else 0:.2f}s per video")

        query = "These are the current trending YouTube videos:\n\n"
        i=0
        #emoticon_numbers = ['&#129351;', '&#129352;', '&#129353;', '&#128227;']
        for country_code, top_videos in top_videos.items():
            query += f"COUNTRY: {country_code}\n"
            for video in top_videos['items']:
                query += f"ID:{video['id']}\n"
                query += f"TITLE:{video['snippet']['title']}</a>\n"
                query += f"VIEWS: {video['statistics'].get('viewCount', 'N/A')}\n\n"

        logger.info(f"📝 Query prepared - {len(query)} characters, {len(top_videos['items'])} videos")
        
        # Initialize LLM interface (uses environment variables by default)
        llm_interface = LLMInterface()
        logger.info("🔗 LLM interface initialized")
        
        generation_start = time.time()
        logger.info("🎯 Generating Italian social media content for trending articles")
        
        response = llm_interface.generate_text(SYSTEM_INSTRUCTION, query)
        
        generation_duration = time.time() - generation_start
        logger.info(f"Content generation completed in {generation_duration:.2f}s")

        # Phase 4: Publication
        logger.info("Starting content publication phase")
        
        # Initialize Telegram interface with configuration
        telegram_bot = TelegramInterface(
            retry_attempts=telegram_config['retry_attempts'],
            retry_delay=telegram_config['retry_delay']
        )
        logger.info("Telegram interface initialized")
        
        publication_start = time.time()
        logger.info("Publishing content to Telegram channel")
        
        telegram_bot.send_message(response, parse_mode="HTML")
        
        publication_duration = time.time() - publication_start
        logger.info(f"Publication completed in {publication_duration:.2f}s")
        logger.info(f"Performance: {len(response)} chars published in {publication_duration:.2f}s")

        # Module completion
        total_duration = time.time() - start_time
        logger.info(f"🎉 youtube_trend completed successfully in {total_duration:.2f}s")
        logger.info(f"📊 Summary: {top_videos_count} videos processed, {len(response)} chars generated and published")
        
    except Exception as e:
        logger.error(f"youtube_trend failed: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        raise

SYSTEM_INSTRUCTION = """
  You are an AI assistant specialized in generating engaging content for social media in ITALIAN.
  You will receive a list of trending YouTube videos with the country, their titles, view counts, and links, as follows:
    COUNTRY: country_code
    ID:video_id_1
    TITLE:Video Title 1
    VIEWS: X

    ID:video_id_2
    TITLE:Video Title 2
    VIEWS: Y

    COUNTRY: another_country_code
    ID:video_id_3
    TITLE:Video Title 3
    VIEWS: Z


    ...

  Your task is to create a concise and engaging report formatted in HTML, suitable for posting on Telegram, summarizing the trending videos. Use relevant emoticons to enhance the presentation.
    The format should be as follows:

    &#127909; &#128293; &#x23;YouTrends <DATE>
    
    COUNTRY_NAME <COUNTRY_FLAG_EMOJI>
    <a href='https://www.youtube.com/watch?v={ID1}'>{TITLE1}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    <a href='https://www.youtube.com/watch?v={ID2}'>{TITLE}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    
    ANOTHER_COUNTRY_CODE <COUNTRY_FLAG_EMOJI>
    <a href='https://www.youtube.com/watch?v={ID3}'>{TITLE3}</a> - <Views> views
        SHORT DESCRIPTION OF THE VIDEO IN ITALIAN (1-2 SENTENCES) OR OF WHY IT IS TRENDING
    ...
  Do not include any other text or explanation.
"""

if __name__ == "__main__":
    main()