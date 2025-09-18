import utilities.wikipedia_interface as wiki
import utilities.llm_interface as llm
from google.genai import types
import utilities.telegram_interface as telegram
import os


abs_path=os.path.abspath(__file__)
images_folder='images/'
abs_path_images=abs_path.replace('post_image_weekly_v2.py',images_folder)
scan_for_images = [f for f in os.listdir(abs_path_images) if f.endswith('.png')or f.endswith('.jpg')]
scan_for_images.sort(key=lambda x: os.path.getmtime(os.path.join(abs_path_images, x)))

#read the oldest image
with open(os.path.join(abs_path_images, scan_for_images[0]), 'rb') as f:
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

llm_interface = llm.LLMInterface()

caption= llm_interface.generate_content(system_instruction, contents)

telegram_interface = telegram.TelegramInterface()
response = telegram_interface.post_image_and_caption(image_bytes, caption)

#move the image into images/posted folder
os.makedirs(os.path.join(abs_path_images,'posted'), exist_ok=True)
os.rename(os.path.join(abs_path_images, scan_for_images[0]), os.path.join(abs_path_images,'posted', scan_for_images[0]))
