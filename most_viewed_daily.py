#https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html
import requests
import json
import datetime as dt
import os
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv()
USER_WIKI = os.getenv("USER_WIKI")
GITHUB_REPO = os.getenv("GITHUB_REPO")
APP_NAME = os.getenv("APP_NAME")
VERSION = os.getenv("VERSION")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")

headers = {'User-Agent': f'{APP_NAME}/{VERSION} ({GITHUB_REPO}; {USER_WIKI})'}
base_url_wiki = "https://wikimedia.org/api/rest_v1/metrics"
base_url_news = "https://newsapi.org/v2/everything"
today = (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y/%m/%d")

country_list = ["IT"]

query = "These are the trending Wikipedia articles on " + today + ":\n"

pages_to_exclude =  ["Main_Page", "Special:Search", "Pagina_principale", "Speciale:Ricerca", "Wikipedia:Hauptseite", "Spezial:Suche", "Wikipedia:Portada", "Especial:Buscar", "Wikipédia:Accueil_principal","Spécial:Recherche"]

#for project in projects_list:
for country in country_list:
    api_url = f"{base_url_wiki}/pageviews/top-per-country/{country}/all-access/{today}"
    response = requests.get(api_url, headers=headers)
    data = response.json()
    if 'items' in data and len(data['items']) > 0:
        data['items'][0]['articles'] = [article for article in data['items'][0]['articles'] if article['article'] not in pages_to_exclude]# and article['rank'] <= 10]

        top_articles = data['items'][0]['articles'][:15] 
        n_articles = 0
        i=0
        while n_articles<=3:
            article = top_articles[i]
            i+=1
            params = {'q': article['article'].replace('_', '+'),  # search query, substitute _ with +
                      'sortBy': 'publishedAt',
                      'pagesize': 3,
                      'page': 1,
                      'apiKey': NEWS_API_KEY
                      }
            news_response = requests.get(base_url_news, params=params)
            news_data = news_response.json()
            if len(news_data['articles']) > 0:
                n_articles += 1
                query += f"titolo: {article['article'].replace('_', ' ')}\n"
                query += f"views: {article['views_ceil']}\n"
                query += f"news: {[news_article['description'] for news_article in news_data['articles']]}\n"
    else:
        print(f"No data available for {country} on {today}.")



system_instruction = """
  You are an AI assistant specialized in summarizing news articles and generating content for social media in ITALIAN.
  Respond only with the final report, ready to be posted on Telegram, formatted as follows:

    #WikipediaTrends <DATE> 📅

    <EMOTICON NUMBER 1> Article Title 1 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: X
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>

    <EMOTICON NUMBER 2> Article Title 2 <EMOTICON RELEVANT TO THE ARTICLE>
    <EMOTICON EYES> Views: Y
    <EMOTICON QUESTION MARK> **<COSA or CHI ACCORDING TO THE SUBJECT> è**: <SHORT DESCRIPTION OF THE ARTICLE>
    <EMOTICON LIGHT_BULB> **Perché è in trend**: <REASON WHY THIS ARTICLE IS TRENDING>
    ...
  Do not include any other text or explanation.
"""

chat_config = types.GenerateContentConfig(
    system_instruction=system_instruction,
)

gemini = genai.Client(api_key=GEMINI_API_KEY)
chat = gemini.chats.create(model="gemini-2.5-flash",config=chat_config)

response = chat.send_message(query)

print(response.text)

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