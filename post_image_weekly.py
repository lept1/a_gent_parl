import requests
import datetime as dt
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")


# generating list of days in the last week in fromat YYYY/MM/DD
this_month = dt.datetime.now().strftime("%B %Y")

abs_path=os.path.abspath(__file__)
images_folder='images/'
abs_path_images=abs_path.replace('post_image_weekly.py',images_folder)
scan_for_images = [f for f in os.listdir(abs_path_images) if f.endswith('.png')or f.endswith('.jpg')]
scan_for_images.sort(key=lambda x: os.path.getmtime(os.path.join(abs_path_images, x)))

#read the oldest image
with open(os.path.join(abs_path_images, scan_for_images[0]), 'rb') as f:
      image_bytes = f.read()

gemini = genai.Client(api_key=GEMINI_API_KEY)

system_instruction = """
  You are an AI assistant specialized in write caption for social media posts in ITALIAN.
  Your task is to create a short & punchy caption for the given image and to provide relevant hashtags.
  Do not include any other text or explanation.
"""

# Define the grounding tool
grounding_tool = types.Tool(
    google_search=types.GoogleSearch()
)

# Configure generation settings
chat_config = types.GenerateContentConfig(
    system_instruction=system_instruction,
    tools=[grounding_tool]
)

response = gemini.models.generate_content(
    model='gemini-2.5-flash',
    config=chat_config,
    contents=[
      types.Part.from_bytes(
        data=image_bytes,
        mime_type='image/jpeg',
      ),
      'Caption this image.'
    ]
  )

print(response.text)

message_text = response.text

# post image and its caption
def post_image_and_caption(chat_id, image_bytes, caption):
    # First, upload the image
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"
    photo_url = f"{url}/sendPhoto"
    message_url = f"{url}/sendMessage"

    payload_photo = {
        "chat_id": chat_id,
        "parse_mode": "Markdown",
    }
    files = {
        "photo": image_bytes
    }
    payload_message = {
        "chat_id": chat_id,
        "text": caption,
        "parse_mode": "Markdown",
    }
    response_photo = requests.post(photo_url, data=payload_photo, files=files)
    response_message = requests.post(message_url, json=payload_message)
    return [response_message.json(), response_photo.json()]
responses = post_image_and_caption(CHANNEL_ID, image_bytes, message_text)
print(responses)

#move the image into images/posted folder
os.makedirs(os.path.join(abs_path_images,'posted'), exist_ok=True)
os.rename(os.path.join(abs_path_images, scan_for_images[0]), os.path.join(abs_path_images,'posted', scan_for_images[0]))
