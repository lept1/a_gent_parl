#https://doc.wikimedia.org/generated-data-platform/aqs/analytics-api/reference/page-views.html
import requests
import json
import datetime as dt
import os
from dotenv import load_dotenv
load_dotenv()
USER_WIKI = os.getenv("USER_WIKI")
GITHUB_REPO = os.getenv("GITHUB_REPO")
APP_NAME = os.getenv("APP_NAME", "a_gent_parl")
VERSION = os.getenv("VERSION", "0.0")
headers = {'User-Agent': f'{APP_NAME}/{VERSION} ({GITHUB_REPO}; {USER_WIKI})'}
base_url = "https://wikimedia.org/api/rest_v1/metrics"
today = (dt.datetime.now() - dt.timedelta(days=1)).strftime("%Y/%m/%d")

projects_list = ["en.wikipedia.org", "it.wikipedia.org", "fr.wikipedia.org", "de.wikipedia.org", "es.wikipedia.org"
                 #,"en.wikiquote.org", "it.wikiquote.org", "fr.wikiquote.org", "de.wikiquote.org", "es.wikiquote.org"
                 ]

response_list = []

pages_to_exclude =  ["Main_Page", "Special:Search", "Pagina_principale", "Speciale:Ricerca", "Wikipedia:Hauptseite", "Spezial:Suche", "Wikipedia:Portada", "Especial:Buscar", "Wikipédia:Accueil_principal","Spécial:Recherche"]

for project in projects_list:
    api_url = f"{base_url}/pageviews/top/{project}/all-access/{today}"
    response = requests.get(api_url, headers=headers)
    data = response.json()
    if 'items' in data and len(data['items']) > 0:
        response_list.append(data)
        # remove articles Main_Page and Special:Search (for each language)
        data['items'][0]['articles'] = [article for article in data['items'][0]['articles'] if article['article'] not in pages_to_exclude and article['rank'] <= 10]

        top_articles = data['items'][0]['articles']
        print(f"Top articles for {project} on {today}:")
        for article in top_articles:
            print(f"{article['article']}: {article['views']} views")
    else:
        print(f"No data available for {project} on {today}.")


