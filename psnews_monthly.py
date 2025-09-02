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


query = "What are the monthly games on PS Plus Essential for " + this_month + "?"

system_instruction = """
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN. 
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

#PSPlus <MONTH> <YEAR> <EMOTICON VIDEOGAME>

<EMOTICON RELEVANT TO THE GAME 1> Game 1 <EMOTICON RELEVANT TO THE GAME 1>
<SHORT DESCRIPTION OF THE GAME 1, SHORT SUMMARY OF THE CRITICS OF THE GAME 1, DESCRIBE HOW MUCH POPULAR THE GAME IS>

<EMOTICON RELEVANT TO THE GAME 2> Game 2 <EMOTICON RELEVANT TO THE GAME 2>
<SHORT DESCRIPTION OF THE GAME 2, SHORT SUMMARY OF THE CRITICS OF THE GAME 2, DESCRIBE HOW MUCH POPULAR THE GAME 2 IS>

...

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

gemini = genai.Client(api_key=GEMINI_API_KEY)
chat = gemini.chats.create(model="gemini-2.5-flash",config=chat_config)

response = chat.send_message(query)

print(response.text)

# system_instruction_image = """
#   You are an AI artist and an expert of videogames specialized in generating content for social media in ITALIAN.
#   You will receive a description of three videogames and you have to create an image for the most popular one, in the graphic style of the game.
#   The image should capture the essence of the game and be visually appealing to the audience.
# """

# # Configure generation settings
# image_config = types.GenerateContentConfig(
#     system_instruction=system_instruction_image,
#     tools=[grounding_tool]
# )

# image = gemini.models.generate_content(
#     model="gemini-2.5-flash-image-preview",
#     contents=[response.text],
#     config=image_config
# )

message_text = response.text

def send_message(chat_id, text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": "Markdown",
    }
    response = requests.post(url, json=payload)
    return response.json()

response = send_message(CHANNEL_ID, message_text)
print(response)