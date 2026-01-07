from src.conf.config_manager import ConfigManager
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.enhanced_logger import EnhancedLogger
from src.utilities.path_manager import PathManager
from google.genai import types
import os
import time

def main():
    module_name = 'weekly_posting_image'
    
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
    
    # Setup logging directory and initialize logger
    log_dir = path_manager.ensure_directory_exists(paths_config['logs_subdir'])
    logger = EnhancedLogger(module_name, log_dir, logging_config)
    logger.setup_logging()
    
    # Module startup logging with configuration summary
    logger.logger.info("🚀 Starting weekly_posting_image module")
    logger.logger.info("📋 Configuration: Image processing and AI caption generation for social media")
    logger.logger.info(f"📊 Module config: {module_config}")
    
    try:
        # Phase 1: Setup and Image Directory Initialization
        logger.logger.info("🔧 Initializing module components")
        
        # Use the new data directory structure for images
        data_root = paths_config['data_root']
        images_subdir = paths_config['images_subdir']
        
        # Try pending images first, fallback to main images directory
        try:
            images_folder = path_manager.get_images_path(f"{data_root}/{images_subdir}", 'pending')
            logger.logger.info(f"📁 Using pending images directory: {images_folder}")
        except:
            images_folder = path_manager.get_images_path(f"{data_root}/{images_subdir}")
            logger.logger.info(f"📁 Using fallback images directory: {images_folder}")
        
        logger.logger.info("✅ Module initialization completed")
        
        # Phase 2: Image Selection Process
        logger.logger.info("📥 Starting image selection phase")
        
        # Get supported image formats from configuration
        supported_formats = module_config.get('image_formats', ['jpg', 'png', 'jpeg'])
        if isinstance(supported_formats, str):
            supported_formats = [fmt.strip() for fmt in supported_formats.split(',')]
        
        try:
            # Scan for images with supported formats
            scan_for_images = []
            for f in os.listdir(images_folder):
                file_ext = f.lower().split('.')[-1] if '.' in f else ''
                if file_ext in supported_formats:
                    scan_for_images.append(f)
            
            logger.logger.info(f"🔍 Found {len(scan_for_images)} image files in directory")
            logger.logger.info(f"📋 Supported formats: {supported_formats}")
            
            if not scan_for_images:
                logger.logger.warning("⚠️ No image files found in directory")
                logger.logger.info(f"🔍 Context: Searched in {images_folder} for {supported_formats} files")
                logger.logger.info("💡 Suggestion: Add image files to the pending directory or check directory permissions")
                return
            
            # Sort by modification time to get oldest image
            scan_for_images.sort(key=lambda x: os.path.getmtime(os.path.join(images_folder, x)))
            selected_image = scan_for_images[0]
            image_path = os.path.join(images_folder, selected_image)
            
            # Get image file information
            image_size = os.path.getsize(image_path)
            image_mtime = os.path.getmtime(image_path)
            
            logger.logger.info(f"✅ Image selected successfully: {selected_image}")
            logger.logger.info(f"📊 Image details: Size={image_size} bytes, Modified={time.ctime(image_mtime)}")
            
        except Exception as e:
            logger.logger.error(f"❌ Image selection failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Scanning directory {images_folder}")
            logger.logger.error(f"💡 Suggestion: Check directory exists and contains valid image files")
            raise
        
        # Phase 3: Image File Operations
        logger.logger.info("📖 Starting image file reading")
        
        try:
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            logger.logger.info(f"✅ Image file read successfully: {len(image_bytes)} bytes loaded")
            
        except Exception as e:
            logger.logger.error(f"❌ Image file reading failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Reading file {image_path}")
            logger.logger.error(f"💡 Suggestion: Check file permissions and ensure file is not corrupted")
            raise
        
        # Phase 4: Caption Generation Setup
        logger.logger.info("🤖 Starting caption generation phase")
        
        # Get caption configuration
        caption_max_length = module_config.get('caption_length_max', 300)
        
        system_instruction = f"""
          You are an AI assistant specialized in write caption for social media posts in ITALIAN.
          Your task is to create a short & punchy caption for the given image and to provide relevant hashtags.
          Keep the caption under {caption_max_length} characters.
          Do not include any other text or explanation.
        """
        query = "Caption this image."
        
        contents = [
            types.Part.from_bytes(
                data=image_bytes,
                mime_type='image/jpeg',
            ),
            query
        ]
        
        logger.logger.info(f"📝 Caption generation setup: Image size={len(image_bytes)} bytes, Query='{query}', Max length={caption_max_length}")
        
        # Phase 5: AI Content Generation
        logger.logger.info("🧠 Generating AI caption")
        generation_start_time = time.time()
        
        try:
            # Initialize LLM interface with environment variable defaults
            llm_interface = LLMInterface()
            caption = llm_interface.generate_content(system_instruction, contents)
            
            generation_time = time.time() - generation_start_time
            logger.logger.info(f"⏱️ Caption generation completed in {generation_time:.2f}s")
            logger.logger.info(f"📊 Performance: {len(caption)} chars generated, {len(caption)/generation_time:.0f} chars/sec")
            logger.logger.info(f"📝 Caption preview: {caption[:100]}...")
            
        except Exception as e:
            logger.logger.error(f"❌ Caption generation failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Processing image {selected_image} with LLM")
            logger.logger.error(f"💡 Suggestion: Check Gemini API key and network connectivity")
            raise
        
        # Phase 6: Content Publication
        logger.logger.info("📤 Starting content publication phase")
        
        try:
            # Initialize Telegram interface with configuration
            telegram_interface = TelegramInterface(**telegram_config)
            response = telegram_interface.post_image_and_caption(image_bytes, caption)
            
            logger.logger.info("✅ Content published to Telegram successfully")
            logger.logger.info(f"📊 Published: Image ({len(image_bytes)} bytes) + Caption ({len(caption)} chars)")
            
        except Exception as e:
            logger.logger.error(f"❌ Telegram publication failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Publishing image {selected_image} with generated caption")
            logger.logger.error(f"💡 Suggestion: Check Telegram bot token and channel permissions")
            raise
        
        # Phase 7: File Management - Move to Posted Folder
        logger.logger.info("📁 Starting file management phase")
        
        try:
            # Use path manager to get posted directory
            posted_folder = path_manager.get_images_path(f"{data_root}/{images_subdir}", 'posted')
            
            source_path = os.path.join(images_folder, selected_image)
            destination_path = os.path.join(posted_folder, selected_image)
            
            logger.logger.info(f"📦 Moving image: {source_path} → {destination_path}")
            
            os.rename(source_path, destination_path)
            
            logger.logger.info(f"✅ Image moved to posted folder successfully")
            logger.logger.info(f"📊 File management: {selected_image} archived to posted directory")
            
        except Exception as e:
            logger.logger.error(f"❌ File management failed: {str(e)}")
            logger.logger.error(f"🔍 Context: Moving {selected_image} from {images_folder} to {posted_folder}")
            logger.logger.error(f"💡 Suggestion: Check directory permissions and ensure destination is writable")
            # Don't raise here as the post was successful
        
        # Module completion
        logger.logger.info("🎉 weekly_posting_image completed successfully")
        logger.logger.info(f"📊 Summary: Image {selected_image} processed, captioned, published, and archived")
        
    except Exception as e:
        logger.logger.error(f"❌ weekly_posting_image failed: {str(e)}")
        logger.logger.error(f"💡 Suggestion: Check logs above for specific error context and remediation steps")
        raise

if __name__ == "__main__":
    main()
