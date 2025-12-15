from src.utilities.wikipedia_interface import WikipediaInterface
from src.utilities.llm_interface import LLMInterface
from src.utilities.telegram_interface import TelegramInterface
from src.utilities.config_manager import ConfigManager
from google.genai import types
import os

# Initialize configuration manager
config = ConfigManager('weekly_posting_image')
config.ensure_data_directories()

# Use the new data directory structure for images
images_folder = config.get_images_directory('pending')
if not os.path.exists(images_folder):
    # Fallback to main images directory if pending doesn't exist
    images_folder = config.get_images_directory()

scan_for_images = [f for f in os.listdir(images_folder) if f.endswith('.png') or f.endswith('.jpg')]
scan_for_images.sort(key=lambda x: os.path.getmtime(os.path.join(images_folder, x)))

#read the oldest image
with open(os.path.join(images_folder, scan_for_images[0]), 'rb') as f:
      image_bytes = f.read()

system_instruction = """
  You are an AI assistant specialized in write caption for social media posts in ITALIAN.
  Your task is to create a short & punchy caption for the given image and to provide relevant hashtags.
  Do not include any other text or explanation.
"""
query="Caption this image."
contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      query
    ]

llm_interface = LLMInterface(env_path=config.get_env_path())

caption= llm_interface.generate_content(system_instruction, contents)

telegram_interface = TelegramInterface(env_path=config.get_env_path())
response = telegram_interface.post_image_and_caption(image_bytes, caption)

#move the image into images/posted folder using the new data structure
posted_folder = config.get_images_directory('posted')
os.makedirs(posted_folder, exist_ok=True)
os.rename(os.path.join(images_folder, scan_for_images[0]), os.path.join(posted_folder, scan_for_images[0]))
