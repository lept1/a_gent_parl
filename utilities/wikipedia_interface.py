import requests
import sys
import os
import io
from dotenv import load_dotenv
from SPARQLWrapper import SPARQLWrapper, JSON
import random
load_dotenv()

class WikipediaInterface:
    def __init__(self, env_path='.env'):
        self.env_path = env_path
        load_dotenv(self.env_path)
        self.USER_WIKI = os.getenv("USER_WIKI")
        if not self.USER_WIKI:
            raise ValueError("USER_WIKI not found in environment variables.")
        self.GITHUB_REPO = os.getenv("GITHUB_REPO")
        if not self.GITHUB_REPO:
            raise ValueError("GITHUB_REPO not found in environment variables.")
        self.APP_NAME = os.getenv("APP_NAME")
        if not self.APP_NAME:
            raise ValueError("APP_NAME not found in environment variables.")
        self.VERSION = os.getenv("VERSION")
        if not self.VERSION:
            raise ValueError("VERSION not found in environment variables.")
        self.headers = {'User-Agent': f'{self.APP_NAME}/{self.VERSION} ({self.GITHUB_REPO}; {self.USER_WIKI})'}
        self.WIKI_API_URL_METRICS = "https://wikimedia.org/api/rest_v1/metrics"
        self.WIKI_API_URL_SPARQL = "https://query.wikidata.org/sparql"
        self.WIKI_API_URL = ["https://en.wikipedia.org/w/api.php", "https://de.wikipedia.org/w/api.php", "https://fr.wikipedia.org/w/api.php",
                             "https://it.wikipedia.org/w/api.php", "https://es.wikipedia.org/w/api.php", "https://nl.wikipedia.org/w/api.php"]
        self.WIKI_API_FILE_URL = "https://api.wikimedia.org/core/v1/commons/file"
        self.user_agent = "WDQS-example Python/%s.%s" % (sys.version_info[0], sys.version_info[1])

    def get_top_articles_by_country(self, country_code, date):
        api_url = f"{self.WIKI_API_URL_METRICS}/pageviews/top-per-country/{country_code}/all-access/{date}"
        response = requests.get(api_url, headers=self.headers)
        if response.status_code != 200:
            raise Exception(f"Error fetching data from Wikipedia API: {response.status_code}")
        return response.json()

    def dates_between_two_dates(self, start_date, end_date):
        import datetime as dt
        start = dt.datetime.strptime(start_date, "%Y/%m/%d")
        end = dt.datetime.strptime(end_date, "%Y/%m/%d")
        return [(start + dt.timedelta(days=i)).strftime("%Y/%m/%d") for i in range((end - start).days + 1)]

    def get_start_and_end_dates_by_period(self, period='week'):
        import datetime as dt
        today = dt.datetime.now()
        if period == 'week':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(days=7)
        elif period == 'month':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(months=1)
        elif period == 'year':
            end = today - dt.timedelta(days=1)
            start = today - dt.timedelta(years=1)
        return start.strftime("%Y/%m/%d"), end.strftime("%Y/%m/%d")
    
    def get_top_articles_excluding(self, articles, exclude_list):
        return [article for article in articles if article['article'] not in exclude_list]

    def get_top_n_articles(self, articles_dict, n=5):
        return {k: v for k, v in sorted(articles_dict.items(), key=lambda item: item[1], reverse=True)[:n]}
    
    def get_top_n_articles_over_period(self, country_code, period='week', exclude_list=None, top_n=5):
        if exclude_list is None:
            exclude_list = []
        start_date, end_date = self.get_start_and_end_dates_by_period(period)
        date_list = self.dates_between_two_dates(start_date, end_date)
        top_articles = {}
        for date in date_list:
            for country in country_code:
                data = self.get_top_articles_by_country(country, date)
                if 'items' in data and len(data['items']) > 0:
                    articles = self.get_top_articles_excluding(data['items'][0]['articles'], exclude_list)
                    for art in articles:
                        if art['article'] not in top_articles:
                            top_articles[art['article']] = art['views_ceil']
                        else:
                            top_articles[art['article']] += art['views_ceil']
                else: 
                    raise ValueError(f"No data available for {country} on {date}.")
        sorted_top_articles = self.get_top_n_articles(top_articles, top_n)
        return sorted_top_articles

    
    def sparql_get_results(self, query):
        
        # TODO adjust user agent; see https://w.wiki/CX6
        sparql = SPARQLWrapper(self.WIKI_API_URL_SPARQL, agent=self.user_agent)
        sparql.setQuery(query)
        sparql.setReturnFormat(JSON)
        return sparql.query().convert()

    def get_dead_on_date(self, professions):
        queries = []
        for p in professions:
            queries.append((r"SELECT ?comicArtistLabel ?comicArtistDescription ?award_receivedLabel ?date_of_death WHERE { "
                    r"?comicArtist wdt:P31 wd:Q5; "
                    f"wdt:P106 {p}. "
                    r"SERVICE wikibase:label { bd:serviceParam wikibase:language '[AUTO_LANGUAGE],mul,en'. } "
                    r"OPTIONAL { ?comicArtist wdt:P570 ?date_of_death. } "
                    r"OPTIONAL { ?comicArtist wdt:P166 ?award_received. } "
                    r"FILTER((((DAY(?date_of_death)) = (DAY(NOW()))) && ((MONTH(?date_of_death)) = (MONTH(NOW())))))} "
                    r"ORDER BY DESC (?date_of_death)"))
        total_dict = {}
        for query in queries:
            results = self.sparql_get_results(query)
            for result in results["results"]["bindings"]:
                total_dict[result["comicArtistLabel"]["value"]] = {
                    "description": result.get("comicArtistDescription", {}).get("value", "No description"),
                    "award_received": result.get('award_receivedLabel', {}).get("value", "No award"),
                    "date_of_death": result.get('date_of_death', {}).get("value", "No date")
                }
        return total_dict
    
    def get_random_wiki_image(self, title):
        for base_url_wiki in self.WIKI_API_URL:
            params = {
                "action": "query",
                "format": "json",
                "titles": title,
                "prop": "images"
            }
            response = requests.get(url=base_url_wiki, params=params, headers=self.headers)
            data = response.json()
            pages = data['query']['pages']
            valid_extensions = ('jpg', 'jpeg', 'png')
            if 'images' not in list(random.choice(list(pages.values())).keys()):
                print(f"No images found for {title} in {base_url_wiki}")
                continue
            img_title = random.choice([img for img in random.choice(list(pages.values()))['images'] if img['title'].lower().endswith(valid_extensions)])
            if not img_title:
                print(f"No valid image found for {title} in {base_url_wiki}")
                continue
            #remove any word before ":" from the title in any language
            img_title_clean = img_title['title'].split(":")[-1].strip()
            url_image = f"{self.WIKI_API_FILE_URL}/File:{img_title_clean.replace(' ', '_')}"
            response = requests.get(url_image, headers=self.headers)
            data = response.json()
            return io.BytesIO(requests.get(data['original']['url'],headers=self.headers).content)
