from src.conf.config_manager import ConfigManager
from src.utilities.wikipedia_interface import WikipediaInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
from dotenv import load_dotenv
import os


def main():
  module_name = 'weekly_happened_today'
  
  # Load environment variables from utilities/.env file
  utilities_env_path = os.path.join(os.path.dirname(__file__), '..', 'utilities', '.env')
  if os.path.exists(utilities_env_path):
    load_dotenv(utilities_env_path, verbose=True)
  
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
  
  # Initialize logger with configuration
  enhanced_logger = EnhancedLogger(module_name, log_dir, logging_config)
  logger = enhanced_logger.setup_logging()
  
  # Initialize utilities - they will use environment variables by default
  # but can be overridden with configuration if needed
  telegram = TelegramInterface(**telegram_config)
  llm = LLMInterface()
  wiki = WikipediaInterface()
  
  # Get module-specific configuration values
  professions_list = module_config.get('professions', ['comics artist', 'cartoonist', 'mangaka', 'fantasy writer', 'animator'])
  historical_period_days = module_config.get('historical_period_days', 7)
  
  logger.info("🚀 Starting weekly_happened_today module")
  logger.info(f"📋 Configuration: Historical posts for notable figures ({', '.join(professions_list)})")
  logger.info(f"📅 Historical period: {historical_period_days} days")
  
  try:
    # Phase 1: Initialize interfaces
    logger.info("🔧 Module components initialized successfully")
    
    # Phase 2: Fetch historical data via SPARQL
    logger.info("📥 Starting historical data fetching phase")
    # Map profession names to Wikidata entity IDs
    profession_mapping = {
        'comics artist': 'wd:Q266569',
        'cartoonist': 'wd:Q5434338', 
        'mangaka': 'wd:Q191633',
        'fantasy writer': 'wd:Q1114448',
        'animator': 'wd:Q715301'
    }
    
    # Convert configured professions to Wikidata IDs
    professions = [profession_mapping.get(prof, prof) for prof in professions_list if prof in profession_mapping]
    logger.info(f"🔍 SPARQL query parameters: Professions={professions_list}")
    
    import time
    query_start = time.time()
    logger.info("⏱️ Executing SPARQL query against Wikidata endpoint...")
    
    total_dict = wiki.get_dead_on_date(professions)
    query_duration = time.time() - query_start
    
    if not total_dict:
      logger.warning("⚠️ No historical data found for today's date")
      logger.info("💡 Suggestion: Check Wikidata availability or try different profession categories")
      return
    
    logger.info(f"✅ Historical data fetching completed in {query_duration:.2f}s")
    logger.info(f"📊 Performance: {len(total_dict)} figures retrieved, {len(total_dict)/query_duration:.1f} results/sec")
    logger.info(f"📋 Retrieved figures: {', '.join(list(total_dict.keys())[:5])}{'...' if len(total_dict) > 5 else ''}")


    # Phase 3: Prepare content generation context
    logger.info("🤖 Starting content generation phase")
    logger.info(f"📝 Building prompt with {len(total_dict)} historical figures")
    
    prompt=f"This is a list of famous comics artists, cartoonists, mangaka, fantasy writers and animators who died today in history:\n"
    for name, info in total_dict.items():
        prompt+=f"- {name} ({info['date_of_death']}): {info['description']}. Award received: {info['award_received']}\n"
    # Now, use Gemini to create a Telegram post
    prompt+=f"\n\n Choose the most relevant artist and generate a long and detailed description for him.\n"
    
    logger.info(f"📊 Content generation context: Prompt length={len(prompt)} characters")
    logger.info("🎯 Content generation goal: Select most relevant artist and create detailed Italian description")
    
    system_instruction = """
      You are an AI assistant specialized generating content for social media in ITALIAN.
      Respond in a formatted way as follows:

        #AccaddeOggi <DD MMM> 📅

        <EMOTICON RELEVANT TO THE PERSON> **<Name>** <EMOTICON RELEVANT TO THE PERSON>
        <EMOTICON > Nato il: <DATE OF BIRTH if available> - Morto il: <DATE OF DEATH if available>
        <IF AWARD RECEIVED EMOTICON AWARD> Premi Ricevuti: <AWARD RECEIVED>
        <LONG DESCRIPTION>

      Do not include any other text or explanation.
    """

    generation_start = time.time()
    logger.info("⏱️ Generating content via Gemini API...")
    # LLM interface already initialized above
    telegram_post = llm.generate_text(system_instruction, prompt)
    generation_duration = time.time() - generation_start
    
    if not telegram_post or len(telegram_post.strip()) < 50:
      logger.error("❌ Content generation failed: Empty or too short response")
      logger.error("💡 Suggestion: Check Gemini API key and rate limits")
      return
    
    logger.info(f"✅ Content generation completed in {generation_duration:.2f}s")
    logger.info(f"📊 Performance: {len(telegram_post)} chars generated, {len(telegram_post)/generation_duration:.0f} chars/sec")
    logger.info(f"📝 Content preview: {telegram_post[:100]}...")
    # Phase 4: Extract selected figure and fetch image
    logger.info("🖼️ Starting image fetching phase")
    try:
      name = telegram_post.split("**")[1].strip()
      logger.info(f"🎯 Selected figure for image search: {name}")
    except (IndexError, AttributeError) as e:
      logger.error(f"❌ Failed to extract figure name from generated content: {str(e)}")
      logger.error("💡 Suggestion: Check content generation format or adjust parsing logic")
      name = "default"
    
    logger.info(f"🔍 Searching Wikipedia for image of: {name}")
    image_bytes = wiki.get_random_wiki_image(name)
    
    # Phase 5: Publication
    logger.info("📤 Starting content publication phase")
    
    if image_bytes is None:
        logger.warning(f"⚠️ No image found for {name}, posting text-only message")
        logger.info("📝 Publishing text-only post to Telegram")
        telegram.send_message(telegram_post)
        logger.info("✅ Text-only post published successfully")
    else:
        logger.info(f"🖼️ Image found for {name}, posting with image and caption")
        # Handle BytesIO object by getting its value
        if hasattr(image_bytes, 'getvalue'):
            image_data = image_bytes.getvalue()
            logger.info(f"📊 Image size: {len(image_data)} bytes")
            telegram.post_image_and_caption(image_data, telegram_post)
        else:
            logger.info(f"📊 Image size: {len(image_bytes)} bytes")
            telegram.post_image_and_caption(image_bytes, telegram_post)
        logger.info("✅ Image post with caption published successfully")
    
    logger.info("🎉 weekly_happened_today completed successfully")
    
  except Exception as e:
    logger.error(f"❌ weekly_happened_today failed: {str(e)}")
    logger.error(f"🔍 Error context: Module was processing historical figures for today's date")
    logger.error("💡 Suggestion: Check internet connectivity, API keys, and service availability")
    logger.error("🔍 Details: Verify Wikidata/Wikipedia access, Gemini API key, and Telegram bot permissions")
    raise
  
  
if __name__ == "__main__":
    main()
