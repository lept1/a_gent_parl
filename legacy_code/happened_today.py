import sys
import os
import io
from SPARQLWrapper import SPARQLWrapper, JSON
from dotenv import load_dotenv
from google import genai
from google.genai import types
import random
import requests

load_dotenv()
USER_WIKI = os.getenv("USER_WIKI")
GITHUB_REPO = os.getenv("GITHUB_REPO")
APP_NAME = os.getenv("APP_NAME")
VERSION = os.getenv("VERSION")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
CHANNEL_ID = os.getenv("CHANNEL_ID")

endpoint_url = "https://query.wikidata.org/sparql"

#Occupation: comics artist

query_comics_artists = """
SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q715301.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))
}
ORDER BY DESC (?date_of_death)"""

query_cartoonist = """
SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q1114448.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))
}
ORDER BY DESC (?date_of_death)"""

query_mangaka = """
SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q191633.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))
}
ORDER BY DESC (?date_of_death)"""

query_fantasy_writer = """
SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q5434338.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))
}
ORDER BY DESC (?date_of_death)"""

query_animator = """
SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE {
  ?comicArtist wdt:P31 wd:Q5;
    wdt:P106 wd:Q266569.
  SERVICE wikibase:label { bd:serviceParam wikibase:language "[AUTO_LANGUAGE],mul,en". }
  OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. }
  OPTIONAL { ?comicArtist wdt:P166 ?award_received. }
  FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))
}
ORDER BY DESC (?date_of_death)"""


def get_results(endpoint_url, query):
    user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])
    # TODO adjust user agent; see https://w.wiki/CX6
    sparql = SPARQLWrapper(endpoint_url, agent=user_agent)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    return sparql.query().convert()

total_dict = {}
query = query_comics_artists
results = get_results(endpoint_url, query)
for result in results["results"]["bindings"]:
    total_dict[result["comicArtistLabel"]["value"]] = {
        "description": result.get("comicArtistDescription", {}).get("value", "No description"),
        "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
        "date_of_death": result.get('date_of_death', {}).get("value", "No date")
    }

query = query_cartoonist
results = get_results(endpoint_url, query)
for result in results["results"]["bindings"]:
    total_dict[result["comicArtistLabel"]["value"]] = {
        "description": result.get("comicArtistDescription", {}).get("value", "No description"),
        "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
        "date_of_death": result.get('date_of_death', {}).get("value", "No date")
    }

query = query_mangaka
results = get_results(endpoint_url, query)
for result in results["results"]["bindings"]:
    total_dict[result["comicArtistLabel"]["value"]] = {
        "description": result.get("comicArtistDescription", {}).get("value", "No description"),
        "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
        "date_of_death": result.get('date_of_death', {}).get("value", "No date")
    }

query = query_fantasy_writer
results = get_results(endpoint_url, query)
for result in results["results"]["bindings"]:
    total_dict[result["comicArtistLabel"]["value"]] = {
        "description": result.get("comicArtistDescription", {}).get("value", "No description"),
        "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
        "date_of_death": result.get('date_of_death', {}).get("value", "No date")
    }

query = query_animator
results = get_results(endpoint_url, query)
for result in results["results"]["bindings"]:
    total_dict[result["comicArtistLabel"]["value"]] = {
        "description": result.get("comicArtistDescription", {}).get("value", "No description"),
        "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
        "date_of_death": result.get('date_of_death', {}).get("value", "No date")
    }

prompt=f"This is a list of famous comics artists, cartoonists, mangaka, fantasy writers and animators who died today in history:\n"
for name, info in total_dict.items():
    prompt+=f"- {name} ({info['date_of_death']}): {info['description']}. Award received: {info['award_received']}\n"
# Now, use Gemini to create a Telegram post
prompt+=f"\n\n Choose the most relevant artist and generate a long and detailed description for him.\n"
#print(prompt)
system_instruction = """
  You are an AI assistant specialized generating content for social media in ITALIAN.
  Respond in a formatted way as follows:

    #AccaddeOggi <DD MMM> 📅

    <EMOTICON RELEVANT TO THE PERSON> <NAME> <EMOTICON RELEVANT TO THE PERSON>
    <EMOTICON > Nato il: <DATE OF BIRTH if available> - Morto il: <DATE OF DEATH if available>
    <IF AWARD RECEIVED EMOTICON AWARD> Premi Ricevuti: <AWARD RECEIVED>
    <LONG DESCRIPTION>

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

telegram_post = chat.send_message(prompt).text

name = chat.send_message('Extract the name of the artist from the previous response. Respond only with the name.').text


import requests

base_url_wiki = "https://en.wikipedia.org/w/api.php"
params = {
    "action": "query",
    "format": "json",
    "titles": name,
    "prop": "images"
}
headers = {'User-Agent': f'{APP_NAME}/{VERSION} ({GITHUB_REPO}; {USER_WIKI})'}
response = requests.get(url=base_url_wiki, params=params, headers=headers)
data = response.json()

pages = data['query']['pages']

#exclude images with these extensions
valid_extensions = ('jpg', 'jpeg', 'png')
img_title = random.choice([img for img in random.choice(list(pages.values()))['images'] if img['title'].lower().endswith(valid_extensions)])['title']
url_image = f"https://api.wikimedia.org/core/v1/commons/file/{img_title.replace(' ', '_')}"
response = requests.get(url_image, headers=headers)
data = response.json()
image_bytes = io.BytesIO(requests.get(data['original']['url'],headers=headers).content)


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


responses = post_image_and_caption(CHANNEL_ID, image_bytes, telegram_post)
print(responses)

#response = send_message(CHANNEL_ID, telegram_post)
print(response)